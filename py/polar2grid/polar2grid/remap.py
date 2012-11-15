"""Interface to remapping polar2grid data.

Main interface function `remap_bands`.
"""
from polar2grid.core.constants import GRID_KIND_PROJ4,GRID_KIND_GPD,DEFAULT_FILL_VALUE
from .grids.grids import get_grid_info
from . import ll2cr as gator # gridinator
from . import ms2gt

import os
import sys
import logging
import multiprocessing

log = logging.getLogger(__name__)

def run_ll2cr_c(*args, **kwargs):
    proc_pool = kwargs.pop("pool", None)
    if proc_pool is None:
        result = ms2gt.ll2cr(*args, **kwargs)
    else:
        result = proc_pool.apply_async(ms2gt.ll2cr,
                args=args, kwds=kwargs)
    return result

def run_ll2cr_py(*args, **kwargs):
    proc_pool = kwargs.pop("pool", None)
    if proc_pool is None:
        result = gator.ll2cr_fbf(*args, **kwargs)
    else:
        result = proc_pool.apply_async(gator.ll2cr_fbf,
                args=args, kwds=kwargs)
    return result

def run_ll2cr(sat, instrument, kind, lon_fbf, lat_fbf,
        grid_jobs,
        num_procs=1, verbose=False, forced_gpd=None,
        lat_min=None, lat_max=None, lon_min=None, lon_max=None,
        fill_value_in=DEFAULT_FILL_VALUE):
    """Run one of the ll2crs and return a dictionary mapping the
    `grid_name` to the cols and rows files.
    """
    proc_pool = multiprocessing.Pool(num_procs)

    # Run ll2cr
    ll2cr_results = dict((grid_name,None) for grid_name in grid_jobs)
    ll2cr_output = dict((grid_name,None) for grid_name in grid_jobs)
    for grid_name in grid_jobs.keys():
        log.info("Running ll2cr for the %s band and grid %s" % (kind,grid_name))
        # Get grid info from the grids module
        grid_info = get_grid_info(grid_name)
        ll2cr_output[grid_name] = grid_info.copy()
        ll2cr_tag = "ll2cr_%s_%s" % (kind,grid_name)

        # Get information that is usually per band, but since we are already
        # separated by 'similar' data, just pick one of the bands to pull the
        # data from
        band_representative = grid_jobs[grid_name].keys()[0]
        swath_cols = grid_jobs[grid_name][band_representative]["swath_cols"]
        ll2cr_output[grid_name]["swath_cols"] = swath_cols
        swath_rows = grid_jobs[grid_name][band_representative]["swath_rows"]
        ll2cr_output[grid_name]["swath_rows"] = swath_rows
        rows_per_scan = grid_jobs[grid_name][band_representative]["rows_per_scan"]
        ll2cr_output[grid_name]["rows_per_scan"] = rows_per_scan

        if grid_info["grid_kind"] == GRID_KIND_PROJ4:
            # Stuff that fornav needs, but the python version doesn't provide
            ll2cr_output[grid_name]["scans_out"] = swath_rows/rows_per_scan
            ll2cr_output[grid_name]["scan_first"] = 0
            ll2cr_results[grid_name] = run_ll2cr_py(
                    lon_fbf,
                    lat_fbf,
                    grid_info["proj4_str"],
                    pixel_size_x=grid_info["pixel_size_x"],
                    pixel_size_y=grid_info["pixel_size_y"],
                    grid_origin_x=grid_info["grid_origin_x"],
                    grid_origin_y=grid_info["grid_origin_y"],
                    grid_width=grid_info["grid_width"],
                    grid_height=grid_info["grid_height"],
                    fill_in=fill_value_in,
                    fill_out=-1e30,
                    prefix=ll2cr_tag,
                    swath_lat_min=lat_min,
                    swath_lat_max=lat_max,
                    swath_lon_min=lon_min,
                    swath_lon_max=lon_max,
                    pool=proc_pool
                    )
        elif grid_info["grid_kind"] == GRID_KIND_GPD:
            ll2cr_results[grid_name] = run_ll2cr_c(
                    swath_cols,
                    swath_rows/rows_per_scan, # swath_scans
                    rows_per_scan,
                    lat_fbf,
                    lon_fbf,
                    forced_gpd or grid_info["gpd_filepath"],
                    verbose = verbose,
                    fill_io = (fill_value_in, -1e30),
                    tag=ll2cr_tag,
                    pool=proc_pool
                    )

    proc_pool.close()
    proc_pool.join()

    for grid_name in grid_jobs:
        try:
            cr_dict = ll2cr_results[grid_name].get()
            ll2cr_output[grid_name].update(cr_dict)
            for band,band_dict in grid_jobs[grid_name].items():
                band_dict.update(ll2cr_output[grid_name])
        except StandardError:
            log.warning("ll2cr failed for %s band, grid %s" % (kind,grid_name))
            log.warning("Won't process for this grid...")
            log.debug("ll2cr error:", exc_info=1)
            for band in grid_jobs[grid_name]:
                log.error("Removing processing for kind %s band %s because of bad ll2cr execution on grid %s" % (kind,band,grid_name))
            del grid_jobs[grid_name]
            del ll2cr_output[grid_name]

    if len(grid_jobs) == 0:
        log.error("All grids failed during ll2cr processing for %s" % kind)
        raise ValueError("All grids failed during ll2cr processing for %s" % kind)

    return ll2cr_output

def run_fornav_c(*args, **kwargs):
    proc_pool = kwargs.pop("pool", None)
    if proc_pool is None:
        result = ms2gt.fornav(*args, **kwargs)
    else:
        result = proc_pool.apply_async(ms2gt.fornav,
                args=args,
                kwds=kwargs
                )
    return result

def run_fornav_py():
    pass

def run_fornav(sat, instrument, kind, grid_jobs, ll2cr_output,
        num_procs=1, verbose=False, fornav_d=None, fornav_D=None,
        fill_value_in=DEFAULT_FILL_VALUE):
    """Run one of the fornavs and return a dictionary mapping grid_name
    to the fornav remapped image data, among other information.
    """
    # Copy the grid_jobs dict (shallow copy)
    fornav_output = grid_jobs

    proc_pool = multiprocessing.Pool(num_procs)

    # Add fornav calls to the process pool
    fornav_jobs = {} # Store the information for each job
    for grid_name in grid_jobs:
        # Collect information for each "fornav job" (sorted by `remap_data_as`)
        fornav_jobs[grid_name] = {}
        fornav_group = fornav_jobs[grid_name]
        for band, band_info in fornav_output[grid_name].items():
            
            if band_info["remap_data_as"] not in fornav_group:
                fornav_group[band_info["remap_data_as"]] = {
                        "inputs" : [],
                        "outputs" : [],
                        "result" : None
                        }
            fbf_swath_temp = band_info["fbf_swath"] if "fbf_swath" in band_info else band_info["fbf_img"]
            fornav_group[band_info["remap_data_as"]]["inputs"].append(fbf_swath_temp)
            #stem = "result_%s%s_%s" % (kind,band,grid_name) # The format of the band key has changed!
            stem = "result_%s%s_%s" % (band[0], band[1], grid_name)
            output_name = "%s.real4.%d.%d" % (stem, band_info["grid_width"], band_info["grid_height"])
            fornav_group[band_info["remap_data_as"]]["outputs"].append(output_name)
            band_info["fbf_remapped"] = output_name
            fill_value_in = band_info["fill_value"] if "fill_value" in band_info else fill_value_in
        
        for remap_data_as,fornav_job in fornav_group.items():
            fornav_job["result"] = run_fornav_c(
                        len(fornav_job["inputs"]),
                        ll2cr_output[grid_name]["swath_cols"],
                        ll2cr_output[grid_name]["scans_out"],
                        ll2cr_output[grid_name]["rows_per_scan"],
                        ll2cr_output[grid_name]["cols_filename"],
                        ll2cr_output[grid_name]["rows_filename"],
                        fornav_job["inputs"],
                        ll2cr_output[grid_name]["grid_width"],
                        ll2cr_output[grid_name]["grid_height"],
                        fornav_job["outputs"],
                        verbose=verbose,
                        swath_data_type_1="f4",
                        swath_fill_1=fill_value_in,
                        grid_fill_1=fill_value_in,
                        weight_delta_max=fornav_D,
                        weight_distance_max=fornav_d,
                        start_scan=(ll2cr_output[grid_name]["scan_first"],0),
                        pool=proc_pool
                        )

    proc_pool.close()
    proc_pool.join()

    # Get all the results
    for grid_name,fornav_group in fornav_jobs.items():
        for remap_data_as,fornav_job in fornav_group.items():
            try:
                fornav_dict = fornav_job["result"].get()
                for band,band_dict in fornav_output[grid_name].items():
                    band_dict.update(fornav_dict)
                log.debug("Fornav successfully completed for grid %s, %s data" % (grid_name,remap_data_as))
            except StandardError:
                log.warning("fornav failed for %s band, grid %s, remapping as %s" % (kind,grid_name,remap_data_as))
                log.debug("Exception was:", exc_info=1)
                log.warning("Cleaning up for this job...")
                for band in fornav_output[grid_name].keys():
                    print fornav_output[grid_name][band]["remap_data_as"],remap_data_as
                    if fornav_output[grid_name][band]["remap_data_as"] == remap_data_as:
                        log.error("Removing %s%s because of bad fornav execution" % (kind,band))
                        del fornav_output[grid_name][band]

        if len(fornav_output[grid_name]) == 0:
            log.error("The last grid job for grid %s was removed" % (grid_name,))
            del fornav_output[grid_name]

    if len(fornav_output) == 0:
        log.error("Fornav was not able to complete any remapping for %s bands" % (kind,))

    return fornav_output

def remap_bands(sat, instrument, kind, lon_fbf, lat_fbf,
        grid_jobs, num_procs=1, fornav_d=None, fornav_D=None, forced_gpd=None,
        lat_min=None, lat_max=None, lon_min=None, lon_max=None,
        lat_fill_value=DEFAULT_FILL_VALUE, lon_fill_value=DEFAULT_FILL_VALUE):
    """Remap data using the C or python version of ll2cr and the
    C version of fornav.

    Grid information is asked for through the `polar2grid.grids.grids`
    module.
    
    note:
        Although the C version of ll2cr/fornav requires the number of scans,
        the number of rows is passed for the likely future requirement
        of software to need the size of the data being provided.
    """

    # Used to determine verbosity
    log_level = logging.getLogger('').handlers[0].level or 0
    
    # TODO, this is just a very rough check for now, in the long run handle this more gracefully
    #print("lat_fill_value: " + str(lat_fill_value))
    #print("lon_fill_value: " + str(lon_fill_value))
    assert (lat_fill_value == lon_fill_value)
    
    # Run ll2cr
    ll2cr_output = run_ll2cr(sat, instrument, kind, lon_fbf, lat_fbf,
            grid_jobs,
            num_procs=num_procs, verbose=log_level <= logging.DEBUG, forced_gpd=forced_gpd,
            lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
            fill_value_in=lat_fill_value)

    # Run fornav
    fornav_output = run_fornav(sat, instrument, kind, grid_jobs, ll2cr_output,
            num_procs=num_procs, verbose=log_level <= logging.DEBUG,
            fornav_d=fornav_d, fornav_D=fornav_D)

    return fornav_output

def main():
    pass

if __name__ == "__main__":
    sys.exit(main())

