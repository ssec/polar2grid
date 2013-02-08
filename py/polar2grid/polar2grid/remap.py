#!/usr/bin/env python
# encoding: utf-8
"""Interface to remapping polar2grid data.

Main interface function `remap_bands`.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

from polar2grid.core.constants import GRID_KIND_PROJ4,GRID_KIND_GPD,DEFAULT_FILL_VALUE
from polar2grid.core.fbf import check_stem
from . import ll2cr as gator # gridinator
from . import ms2gt

import os
import sys
import logging
import signal
import multiprocessing

log = logging.getLogger(__name__)

removable_file_patterns = [
        "ll2cr_*_*_cols_*_*_*_*.img",
        "ll2cr_*_*_rows_*_*_*_*.img",
        "ll2cr_*_*_cols.real4.*.*",
        "ll2cr_*_*_rows.real4.*.*",
        "result_*_*.real4.*.*"
        ]

def init_worker():
    """Used in multiprocessing to initialize pool workers.

    If this isn't done then the listening process will hang forever and
    will have to be killed with the "kill" command even after the outer-most
    process is Ctrl+C'd out of existence.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)

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

def run_ll2cr(sat, instrument, nav_set_uid, lon_fbf, lat_fbf,
        grid_jobs,
        num_procs=1, verbose=False, forced_gpd=None,
        lat_south=None, lat_north=None, lon_west=None, lon_east=None,
        lon_fill_value=None, lat_fill_value=None):
    """Run one of the ll2crs and return a dictionary mapping the
    `grid_name` to the cols and rows files.
    """
    proc_pool = multiprocessing.Pool(num_procs, init_worker)
    # Use the default fill value if the user didn't specify or forced None
    lon_fill_value = lon_fill_value or DEFAULT_FILL_VALUE
    lat_fill_value = lat_fill_value or DEFAULT_FILL_VALUE

    # Run ll2cr
    ll2cr_results = dict((grid_name, None) for grid_name in grid_jobs)
    ll2cr_output  = dict((grid_name, None) for grid_name in grid_jobs)
    # We use a big try block to catch a keyboard interrupt and properly
    # terminate the process pool see:
    # https://github.com/davidh-ssec/polar2grid/issues/33
    try:
        for grid_name in grid_jobs.keys():
            log.info("Running ll2cr for grid %s and bands %r" % (grid_name, grid_jobs[grid_name].keys()))
            ll2cr_tag = "ll2cr_%s_%s" % (nav_set_uid,grid_name)

            # Get information that is usually per band, but since we are already
            # separated by 'similar' data, just pick one of the bands to pull the
            # data from
            band_representative = grid_jobs[grid_name].keys()[0]
            band_rep_dict = grid_jobs[grid_name][band_representative]
            # Get grid info from the grids module
            grid_info = band_rep_dict["grid_info"]
            ll2cr_output[grid_name] = grid_info.copy()
            swath_cols = band_rep_dict["swath_cols"]
            ll2cr_output[grid_name]["swath_cols"] = swath_cols
            swath_rows = band_rep_dict["swath_rows"]
            ll2cr_output[grid_name]["swath_rows"] = swath_rows
            rows_per_scan = band_rep_dict["rows_per_scan"]
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
                        lat_fill_in=lat_fill_value,
                        lon_fill_in=lon_fill_value,
                        fill_out=-1e30,
                        prefix=ll2cr_tag,
                        swath_lat_south=lat_south,
                        swath_lat_north=lat_north,
                        swath_lon_west=lon_west,
                        swath_lon_east=lon_east,
                        pool=proc_pool
                        )
            elif grid_info["grid_kind"] == GRID_KIND_GPD:
                # C version of ll2cr can't handle different nav fill values
                if lon_fill_value != lat_fill_value:
                    msg = "Navigation files must have the same fill value when using the C ll2cr (%f vs %f)" % (lon_fill_value, lat_fill_value)
                    log.warning(msg)
                    del grid_jobs[grid_name]
                    continue

                ll2cr_results[grid_name] = run_ll2cr_c(
                        swath_cols,
                        swath_rows/rows_per_scan, # swath_scans
                        rows_per_scan,
                        lat_fbf,
                        lon_fbf,
                        forced_gpd or grid_info["gpd_filepath"],
                        verbose = verbose,
                        fill_io = (lon_fill_value, -1e30),
                        tag=ll2cr_tag,
                        pool=proc_pool
                        )

        proc_pool.close()
        proc_pool.join()
    except KeyboardInterrupt:
        # Catch keyboard interrupt during pool processing, see comment at
        # top of try block
        log.debug("Keyboard interrupt during ll2cr call")
        proc_pool.terminate()
        proc_pool.join()
        raise

    # Get the results of the ll2cr calls
    for grid_name in grid_jobs.keys():
        try:
            cr_dict = ll2cr_results[grid_name].get()
            ll2cr_output[grid_name].update(cr_dict)
            for band_dict in grid_jobs[grid_name].values():
                band_dict.update(ll2cr_output[grid_name])
        except StandardError:
            log.warning("ll2cr failed for grid %s for bands %r" % (grid_name,grid_jobs[grid_name].keys()))
            log.warning("Won't process for this grid...")
            log.debug("ll2cr error:", exc_info=1)
            for (band_kind, band_id) in grid_jobs[grid_name]:
                log.error("Removing processing for kind %s band %s because of bad ll2cr execution on grid %s" % (band_kind, band_id, grid_name))
            del grid_jobs[grid_name]
            del ll2cr_output[grid_name]

    if len(grid_jobs) == 0:
        log.error("All grids failed during ll2cr processing for %s" % (nav_set_uid,))
        raise ValueError("All grids failed during ll2cr processing for %s" % (nav_set_uid,))

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

def run_fornav(sat, instrument, nav_set_uid, grid_jobs, ll2cr_output,
        num_procs=1, verbose=False, fornav_d=None, fornav_D=None, fill_value=None):
    """Run one of the fornavs and return a dictionary mapping grid_name
    to the fornav remapped image data, among other information.
    """
    # Copy the grid_jobs dict (shallow copy)
    fornav_output = grid_jobs
    fill_value = fill_value or DEFAULT_FILL_VALUE

    proc_pool = multiprocessing.Pool(num_procs, init_worker)

    # We use a big try block to catch a keyboard interrupt and properly
    # terminate the process pool see:
    # https://github.com/davidh-ssec/polar2grid/issues/33
    try:
        # Add fornav calls to the process pool
        fornav_jobs = {} # Store the information for each job
        for grid_name in grid_jobs:
            # Collect information for each "fornav job" (sorted by `remap_data_as`)
            fornav_jobs[grid_name] = {}
            fornav_group = fornav_jobs[grid_name]
            for (band_kind, band_id),band_info in fornav_output[grid_name].items():
                if band_info["remap_data_as"] not in fornav_group:
                    fornav_group[band_info["remap_data_as"]] = {
                            "inputs" : [],
                            "outputs" : [],
                            "swath_fill_1" : [],
                            "grid_fill_1" : [],
                            "result" : None
                            }
                fornav_group[band_info["remap_data_as"]]["inputs"].append(band_info["fbf_swath"])
                stem = "result_%s%s_%s" % (band_kind,band_id,grid_name)
                check_stem(stem)
                output_name = "%s.real4.%d.%d" % (stem, band_info["grid_width"], band_info["grid_height"])
                fornav_group[band_info["remap_data_as"]]["outputs"].append(output_name)
                fornav_group[band_info["remap_data_as"]]["swath_fill_1"].append(band_info.get("fill_value", fill_value))
                fornav_group[band_info["remap_data_as"]]["grid_fill_1"].append(band_info.get("fill_value", fill_value))
                band_info["fbf_remapped"] = output_name

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
                            swath_fill_1=fornav_job["swath_fill_1"],
                            grid_fill_1=fornav_job["grid_fill_1"],
                            weight_delta_max=fornav_D,
                            weight_distance_max=fornav_d,
                            # We only specify start_scan for the 'image'/channel
                            # data because ll2cr is not 'forced' so it only writes
                            # useful data to the output cols/rows files
                            start_scan=(ll2cr_output[grid_name]["scan_first"],0),
                            pool=proc_pool
                            )

        proc_pool.close()
        proc_pool.join()
    except KeyboardInterrupt:
        # Catch keyboard interrupt during pool processing, see comment at
        # top of try block
        log.debug("Keyboard interrupt during fornav call")
        proc_pool.terminate()
        proc_pool.join()
        raise

    # Get all the results
    for grid_name,fornav_group in fornav_jobs.items():
        for remap_data_as,fornav_job in fornav_group.items():
            try:
                fornav_dict = fornav_job["result"].get()
                for (band_kind, band_id),band_dict in fornav_output[grid_name].items():
                    band_dict.update(fornav_dict)
                log.debug("Fornav successfully completed for grid %s, %s data" % (grid_name,remap_data_as))
            except StandardError:
                log.warning("fornav failed for %s band, grid %s, remapping as %s" % (nav_set_uid,grid_name,remap_data_as))
                log.debug("Exception was:", exc_info=1)
                log.warning("Cleaning up for this job...")
                for (band_kind, band_id) in fornav_output[grid_name].keys():
                    if fornav_output[grid_name][(band_kind, band_id)]["remap_data_as"] == remap_data_as:
                        log.error("Removing %s%s because of bad fornav execution" % (band_kind,band_id))
                        del fornav_output[grid_name][(band_kind, band_id)]

        if len(fornav_output[grid_name]) == 0:
            log.error("The last grid job for grid %s was removed" % (grid_name,))
            del fornav_output[grid_name]

    if len(fornav_output) == 0:
        log.error("Fornav was not able to complete any remapping for navigation set %s" % (nav_set_uid,))

    return fornav_output

def remap_bands(sat, instrument, nav_set_uid, lon_fbf, lat_fbf,
        grid_jobs, num_procs=1, fornav_d=None, fornav_D=None, forced_gpd=None,
        lat_south=None, lat_north=None, lon_west=None, lon_east=None,
        lat_fill_value=None, lon_fill_value=None, fill_value=None):
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

    # Run ll2cr
    ll2cr_output = run_ll2cr(sat, instrument, nav_set_uid, lon_fbf, lat_fbf,
            grid_jobs,
            num_procs=num_procs, verbose=log_level <= logging.DEBUG, forced_gpd=forced_gpd,
            lat_south=lat_south, lat_north=lat_north, lon_west=lon_west, lon_east=lon_east,
            lat_fill_value=lat_fill_value, lon_fill_value=lon_fill_value)

    # Run fornav
    fornav_output = run_fornav(sat, instrument, nav_set_uid, grid_jobs, ll2cr_output,
            num_procs=num_procs, verbose=log_level <= logging.DEBUG,
            fornav_d=fornav_d, fornav_D=fornav_D, fill_value=fill_value)

    return fornav_output

def main():
    pass

if __name__ == "__main__":
    sys.exit(main())

