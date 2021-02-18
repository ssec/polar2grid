#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2018 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    April 2018
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""Connect various satpy components together to go from satellite data to output imagery format.
"""

import os
import sys
import argparse
import logging
import importlib
import pkg_resources
from glob import glob

import dask
import numpy as np
from satpy import DataQuery
from pyresample.geometry import DynamicAreaDefinition, AreaDefinition, SwathDefinition
from pyproj import Proj
from polar2grid.writers import geotiff, awips_tiled

try:
    from pyproj import CRS
except ImportError:
    CRS = None


def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False


LOG = logging.getLogger(__name__)

WRITER_PARSER_FUNCTIONS = {
    'geotiff': geotiff.add_writer_argument_groups,
    'scmi': awips_tiled.add_writer_argument_groups,
    'awips_tiled': awips_tiled.add_writer_argument_groups,
}

OUTPUT_FILENAMES = {
    'geotiff': geotiff.DEFAULT_OUTPUT_FILENAME,
}

PLATFORM_ALIASES = {
    'suomi-npp': 'npp',
}

WRITER_ALIASES = {
    'scmi': 'awips_tiled',
}


def get_platform_name_alias(satpy_platform_name):
    return PLATFORM_ALIASES.get(satpy_platform_name.lower(), satpy_platform_name)


def overwrite_platform_name_with_aliases(scn):
    """Change 'platform_name' for every DataArray to Polar2Grid expectations."""
    for data_arr in scn:
        data_dict = data_arr.attrs
        if 'platform_name' not in data_dict:
            continue
        pname = get_platform_name_alias(data_arr.attrs['platform_name'])
        data_arr.attrs['platform_name'] = pname


def get_default_output_filename(reader, writer):
    """Get a default output filename based on what reader we are reading."""
    ofile_map = OUTPUT_FILENAMES.get(writer, {})
    if reader not in ofile_map:
        reader = None
    return ofile_map[reader]


def _proj_dict_equal(a, b):
    """Compare two projection dictionaries for "close enough" equality."""
    # pyproj 2.0+
    if CRS is not None:
        crs1 = CRS(a)
        crs2 = CRS(b)
        return crs1 == crs2

    # fallback
    from osgeo import osr
    a = dict(sorted(a.items()))
    b = dict(sorted(b.items()))
    p1 = Proj(a)
    p2 = Proj(b)
    s1 = osr.SpatialReference()
    s1.ImportFromProj4(p1.srs)
    s2 = osr.SpatialReference()
    s2.ImportFromProj4(p2.srs)
    return s1.IsSame(s2)


def is_native_grid(grid, max_native_area):
    """Is the desired grid a version of the native Area?"""
    if not isinstance(max_native_area, AreaDefinition):
        return False
    if not isinstance(grid, AreaDefinition):
        return False
    if not _proj_dict_equal(max_native_area.proj_dict, grid.proj_dict):
        return False
    # if not np.allclose(np.array(max_native_area.area_extent), np.array(grid.area_extent), atol=grid.pixel_size_x):
    if not np.allclose(np.array(max_native_area.area_extent), np.array(grid.area_extent)):
        return False
    if max_native_area.width < grid.width:
        return (grid.width / max_native_area.width).is_integer()
    else:
        return (max_native_area.width / grid.width).is_integer()


def get_preserve_resolution(args, resampler, areas_to_resample):
    """Determine if we should preserve native resolution products.

    Preserving native resolution should only happen if:

    1. The 'native' resampler is used
    2. At least one of the areas provided to resampling are 'MIN' or 'MAX'
    3. The user didn't ask to *not* preserve it.

    """
    # save original native resolution if possible
    any_minmax = any(x in ['MIN', 'MAX'] for x in areas_to_resample)
    is_native = resampler == 'native'
    is_default = resampler is None
    return any_minmax and (is_native or is_default) and args.preserve_resolution


def get_input_files(input_filenames):
    """Convert directories to list of files."""
    for fn in input_filenames:
        if os.path.isdir(fn):
            yield from glob(os.path.join(fn, '*'))
        else:
            yield fn


def write_scene(scn, writers, writer_args, datasets, to_save=None):
    if to_save is None:
        to_save = []
    if not datasets:
        # no datasets to save
        return to_save

    for dataID in datasets:
        try:
            area_def = getattr(scn[dataID], 'area', None)
        except KeyError:
            msg = 'No area definition in {}'.format(dataID)
            LOG.info(msg)
            LOG.error('Information', exc_info=True)
            
        if isinstance(area_def, SwathDefinition): 
            scn[dataID].attrs['area'].area_id = "native"

    for writer_name in writers:
        wargs = writer_args[writer_name]
        res = scn.save_datasets(writer=writer_name, compute=False, datasets=datasets, **wargs)
        if isinstance(res, (tuple, list)):
            to_save.extend(zip(*res))
        else:
            to_save.append(res)
    return to_save


def _handle_product_names(aliases, products):
    for prod_name in products:
        product = aliases.get(prod_name, prod_name)
        if isinstance(product, DataQuery):
            product = product['name']
        yield product


def add_scene_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Reading')
    group_1.add_argument('-r', '--reader', action='append', dest='readers',
                         metavar="READER",
                         help='Name of reader used to read provided files. '
                              'Supported readers: ' + ', '.join(['mirs', 'abi_l1b', 'ahi_hrit', 'ahi_hsd']))
    group_1.add_argument('-f', '--filenames', nargs='+', default=[],
                         help='Input files to read. For a long list of '
                              'files, use \'-f @my_files.txt\' '
                              'to provide a list of filenames from another '
                              'file (one filename per line). Files can also '
                              'be passed at the end of the command line by '
                              'using two hyphens (--) to separate the list '
                              'of files from the other arguments. '
                              'arguments (ex. \'%(prog)s ... -- /path/to/files*\')')
    group_1.add_argument('filenames', nargs="*", action='extend', help=argparse.SUPPRESS)
                         # help="Alternative to '-f' flag. Use two hyphens (--) "
                         #      "to separate these files from other command line "
                         #      "arguments (ex. '%(prog)s ... -- /path/to/files*')")
    group_1.add_argument('-p', '--products', nargs='+',
                         help='Names of products to create from input files')
    return (group_1,)


def add_writer_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Writing')
    group_1.add_argument('-w', '--writer', action='append', dest='writers',
                         metavar="WRITER",
                         help='Writers to save datasets with. Multiple writers '
                              'can be provided by specifying \'-w\' multiple '
                              'times (ex. \'-w geotiff -w awips_tiled\').')
    return (group_1,)


def add_resample_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Resampling')
    group_1.add_argument('--method', dest='resampler',
                         default=None, choices=['native', 'nearest'],
                         help='resampling algorithm to use (default: native)')
    group_1.add_argument('--cache-dir',
                         help='Directory to store resampling intermediate '
                              'results between executions. Not used with native '
                              'resampling.')
    group_1.add_argument('-g', '--grids', default=None, nargs="*",
                         help='Area definition to resample to. Empty means '
                              'no resampling (default: MAX)')
    group_1.add_argument('--grid-configs', dest='grid_configs', nargs="+", default=tuple(),
                         help="Specify additional grid configuration files. "
                              "(.conf for P2G-style grids, .yaml for "
                              "SatPy-style areas)")
    group_1.add_argument('--ll-bbox', nargs=4, type=float, metavar=("lon_min", "lat_min", "lon_max", "lat_max"),
                         help='Crop data to region specified by lon/lat '
                              'bounds (lon_min lat_min lon_max lat_max). '
                              'Coordinates must be valid in the source data '
                              'projection.')

    # nearest neighbor resampling
    group_1.add_argument('--radius-of-influence', default=None, type=float,
                         help='Specify radius to search for valid input '
                              'pixels for nearest neighbor resampling. '
                              'Value is in projection units (typically meters). '
                              'By default this will be determined by input '
                              'pixel size.')
    return tuple([group_1])


def _retitle_optional_arguments(parser):
    """Hack to make the optional arguments say what we want."""
    opt_args = [x for x in parser._action_groups if x.title == 'optional arguments']
    if len(opt_args) == 1:
        opt_args = opt_args[0]
        opt_args.title = "Global Options"


def _apply_default_products_and_aliases(scn, reader, user_products):
    reader_mod = importlib.import_module('polar2grid.readers.' + reader)
    default_products = getattr(reader_mod, 'DEFAULT_PRODUCTS', [])
    if user_products is None and default_products:
        LOG.info("Using default product list: {}".format(default_products))
        user_products = default_products
    elif user_products is None:
        LOG.error("Reader does not have a default set of products to load, "
                  "please specify products to load with `--products`.")
        return None

    # check for valid product names
    ds_ids = scn.available_dataset_names(composites=True)
    aliases = getattr(reader_mod, 'PRODUCT_ALIASES', {})
    user_products = list(_handle_product_names(aliases, user_products))

    # only load default products which match data available
    user_products = set(ds_ids).intersection(user_products)
    if user_products:
        return list(_handle_product_names(aliases, user_products))
    else:
        msg = "No intersection between products {} and scn {}"
        msg = msg.format(user_products, ds_ids)
        LOG.error(msg)

def main(argv=sys.argv[1:]):
    global LOG
    from satpy import Scene
    from satpy.resample import get_area_def
    from satpy.writers import compute_writer_results
    from dask.diagnostics import ProgressBar
    from polar2grid.core.script_utils import (
        setup_logging, rename_log_file, create_exc_handler)
    import argparse

    dist = pkg_resources.get_distribution('polar2grid')
    if dist_is_editable(dist):
        os.environ.setdefault("PPP_CONFIG_DIR", os.path.join(dist.module_path, 'etc'))
    else:
        os.environ.setdefault("PPP_CONFIG_DIR", os.path.join(sys.prefix, 'etc', 'polar2grid'))
    USE_POLAR2GRID_DEFAULTS = bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))

    prog = os.getenv('PROG_NAME', sys.argv[0])
    # "usage: " will be printed at the top of this:
    usage = """
    %(prog)s -h
see available products:
    %(prog)s -r <reader> -w <writer> --list-products -f file1 [file2 ...]
basic processing:
    %(prog)s -r <reader> -w <writer> [options] -f file1 [file2 ...]
basic processing with limited products:
    %(prog)s -r <reader> -w <writer> [options] -p prod1 prod2 -f file1 [file2 ...]
"""
    parser = argparse.ArgumentParser(prog=prog, usage=usage,
                                     fromfile_prefix_chars="@",
                                     description="Load, composite, resample, and save datasets.")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-l', '--log', dest="log_fn", default=None,
                        help="specify the log filename")
    parser.add_argument('--progress', action='store_true',
                        help="show processing progress bar (not recommended for logged output)")
    parser.add_argument('--num-workers', type=int, default=os.getenv('DASK_NUM_WORKERS', 4),
                        help="specify number of worker threads to use (default: 4)")
    parser.add_argument('--match-resolution', dest='preserve_resolution', action='store_false',
                        help="When using the 'native' resampler for composites, don't save data "
                             "at its native resolution, use the resolution used to create the "
                             "composite.")
    parser.add_argument("--list-products", dest="list_products", action="store_true",
                        help="List available reader products and exit")
    reader_group = add_scene_argument_groups(parser)[0]
    resampling_group = add_resample_argument_groups(parser)[0]
    writer_group = add_writer_argument_groups(parser)[0]
    subgroups = [reader_group, resampling_group, writer_group]

    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]

    _retitle_optional_arguments(parser)
    args, remaining_args = parser.parse_known_args(argv_without_help)
    os.environ['DASK_NUM_WORKERS'] = str(args.num_workers)

    # get the logger if we know the readers and writers that will be used
    if args.readers is not None and args.writers is not None:
        glue_name = args.readers[0] + "_" + "-".join(args.writers or [])
        LOG = logging.getLogger(glue_name)
    # add writer arguments
    if args.writers is not None:
        args.writers = [WRITER_ALIASES.get(writer, writer) for writer in args.writers]
        for writer in (args.writers or []):
            parser_func = WRITER_PARSER_FUNCTIONS.get(writer)
            if parser_func is None:
                continue
            subgroups += parser_func(parser)
    args = parser.parse_args(argv)

    if args.readers is None:
        parser.print_usage()
        parser.exit(1, "\nERROR: Reader must be provided (-r flag).\n"
                       "Supported readers:\n\t{}\n".format('\n\t'.join(['abi_l1b', 'ahi_hsd', 'hrit_ahi'])))
    elif len(args.readers) > 1:
        parser.print_usage()
        parser.exit(1, "\nMultiple readers is not currently supported. Got:\n\t"
                  "{}\n".format('\n\t'.join(args.readers)))
        return -1
    if args.writers is None:
        parser.print_usage()
        parser.exit(1, "\nERROR: Writer must be provided (-w flag) with one or more writer.\n"
                       "Supported writers:\n\t{}\n".format('\n\t'.join(['geotiff'])))

    def _args_to_dict(group_actions, exclude=None):
        if exclude is None:
            exclude = []
        return {ga.dest: getattr(args, ga.dest) for ga in group_actions
                if hasattr(args, ga.dest) and ga.dest not in exclude}
    reader_args = _args_to_dict(reader_group._group_actions)
    scene_creation = {
        'filenames': reader_args.pop('filenames'),
        'reader': reader_args.pop('readers')[0],
    }
    load_args = {
        'products': reader_args.pop('products'),
    }
    # anything left in 'reader_args' is a reader-specific kwarg
    resample_args = _args_to_dict(resampling_group._group_actions)
    writer_args = _args_to_dict(writer_group._group_actions)
    # writer_args = {}
    subgroup_idx = 3
    for idx, writer in enumerate(writer_args['writers']):
        sgrp1, sgrp2 = subgroups[subgroup_idx + idx * 2: subgroup_idx + 2 + idx * 2]
        wargs = _args_to_dict(sgrp1._group_actions)
        if sgrp2 is not None:
            wargs.update(_args_to_dict(sgrp2._group_actions))
        writer_args[writer] = wargs
        # get default output filename
        if 'filename' in wargs and wargs['filename'] is None:
            wargs['filename'] = get_default_output_filename(args.readers[0], writer)

    if not args.filenames:
        parser.print_usage()
        parser.exit(1, "\nERROR: No data files provided (-f flag)\n")

    # Prepare logging
    rename_log = False
    if args.log_fn is None:
        rename_log = True
        args.log_fn = glue_name + "_fail.log"
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    logging.getLogger('rasterio').setLevel(levels[min(2, args.verbosity)])
    sys.excepthook = create_exc_handler(LOG.name)
    if levels[min(3, args.verbosity)] > logging.DEBUG:
        import warnings
        warnings.filterwarnings("ignore")
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    # Set up dask and the number of workers
    if args.num_workers:
        from multiprocessing.pool import ThreadPool
        dask.config.set(pool=ThreadPool(args.num_workers))

    # Parse provided files and search for files if provided directories
    scene_creation['filenames'] = get_input_files(scene_creation['filenames'])
    # Create a Scene, analyze the provided files
    LOG.info("Sorting and reading input files...")
    try:
        scn = Scene(**scene_creation)
    except ValueError as e:
        LOG.error("{} | Enable debug message (-vvv) or see log file for details.".format(str(e)))
        LOG.debug("Further error information: ", exc_info=True)
        return -1
    except OSError:
        LOG.error("Could not open files. Enable debug message (-vvv) or see log file for details.")
        LOG.debug("Further error information: ", exc_info=True)
        return -1

    if args.list_products:
        print("\n".join(sorted(scn.available_dataset_names(composites=True))))
        return 0

    # Rename the log file
    if rename_log:
        rename_log_file(glue_name + scn.attrs['start_time'].strftime("_%Y%m%d_%H%M%S.log"))

    # Load the actual data arrays and metadata (lazy loaded as dask arrays)
    LOG.info("Loading product metadata from files...")
    load_args['products'] = _apply_default_products_and_aliases(scn,
        scene_creation['reader'], load_args['products'])
    if not load_args['products']:
        return -1
    scn.load(load_args['products'])

    # from .filters.day_night import _get_sunlight_coverage
    # data_arr = scn[load_args['products'][0]]
    # sl_cov = _get_sunlight_coverage(data_arr.attrs['area'], data_arr.attrs['start_time'])
    # print("Sunlight coverage: ", sl_cov)
    # return

    resample_kwargs = resample_args.copy()
    areas_to_resample = resample_kwargs.pop('grids')
    grid_configs = resample_kwargs.pop('grid_configs')
    resampler = resample_kwargs.pop('resampler')

    if areas_to_resample is None and resampler in [None, 'native']:
        # no areas specified
        areas_to_resample = ['MAX']
    elif areas_to_resample is None:
        raise ValueError("Resampling method specified (--method) without any destination grid/area (-g flag).")
    elif not areas_to_resample:
        # they don't want any resampling (they used '-g' with no args)
        areas_to_resample = [None]

    p2g_grid_configs = [x for x in grid_configs if x.endswith('.conf')]
    pyresample_area_configs = [x for x in grid_configs if not x.endswith('.conf')]
    if not grid_configs or p2g_grid_configs:
        # if we were given p2g grid configs or we weren't given any to choose from
        from polar2grid.grids import GridManager
        grid_manager = GridManager(*p2g_grid_configs)
    else:
        grid_manager = {}

    if pyresample_area_configs:
        from pyresample.utils import parse_area_file
        custom_areas = parse_area_file(pyresample_area_configs)
        custom_areas = {x.area_id: x for x in custom_areas}
    else:
        custom_areas = {}

    ll_bbox = resample_kwargs.pop('ll_bbox')
    if ll_bbox:
        scn = scn.crop(ll_bbox=ll_bbox)

    wishlist = scn.wishlist.copy()
    preserve_resolution = get_preserve_resolution(args, resampler, areas_to_resample)
    if preserve_resolution:
        preserved_products = set(wishlist) & set(scn.keys())
        resampled_products = set(wishlist) - preserved_products

        # original native scene
        to_save = write_scene(scn, args.writers, writer_args, preserved_products)
    else:
        preserved_products = set()
        resampled_products = set(wishlist)
        to_save = []

    LOG.debug("Products to preserve resolution for: {}".format(preserved_products))
    LOG.debug("Products to use new resolution for: {}".format(resampled_products))
    for area_name in areas_to_resample:
        if area_name is None:
            # no resampling
            area_def = None
        elif area_name == 'MAX':
            area_def = scn.max_area()
        elif area_name == 'MIN':
            area_def = scn.min_area()
        elif area_name in custom_areas:
            area_def = custom_areas[area_name]
        elif area_name in grid_manager:
            p2g_def = grid_manager[area_name]
            area_def = p2g_def.to_satpy_area()
            if isinstance(area_def, DynamicAreaDefinition) and p2g_def['cell_width'] is not None:
                area_def = area_def.freeze(scn.max_area(),
                                           resolution=(abs(p2g_def['cell_width']), abs(p2g_def['cell_height'])))
        else:
            area_def = get_area_def(area_name)

        if resampler is None and area_def is not None:
            rs = 'native' if area_name in ['MIN', 'MAX'] or is_native_grid(area_def, scn.max_area()) else 'nearest'
            LOG.debug("Setting default resampling to '{}' for grid '{}'".format(rs, area_name))
        else:
            rs = resampler

        if area_def is not None:
            LOG.info("Resampling data to '%s'", area_name)
            new_scn = scn.resample(area_def, resampler=rs, **resample_kwargs)
        elif not preserve_resolution:
            # the user didn't want to resample to any areas
            # the user also requested that we don't preserve resolution
            # which means we have to save this Scene's datasets
            # because they won't be saved
            new_scn = scn

        overwrite_platform_name_with_aliases(new_scn)
        to_save = write_scene(new_scn, writer_args['writers'], writer_args, resampled_products, to_save=to_save)

    if args.progress:
        pbar = ProgressBar()
        pbar.register()

    LOG.info("Computing products and saving data to writers...")
    compute_writer_results(to_save)
    LOG.info("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
