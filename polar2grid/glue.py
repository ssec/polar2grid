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
from polar2grid.resample import resample_scene
from polar2grid.writers import geotiff, awips_tiled
from polar2grid.filters import filter_scene


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
        if 'platform_name' not in data_arr.attrs:
            continue
        pname = get_platform_name_alias(data_arr.attrs['platform_name'])
        data_arr.attrs['platform_name'] = pname


def get_default_output_filename(reader, writer):
    """Get a default output filename based on what reader we are reading."""
    ofile_map = OUTPUT_FILENAMES.get(writer, {})
    if reader not in ofile_map:
        reader = None
    return ofile_map[reader]


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

    for data_id in datasets:
        area_def = scn[data_id].attrs.get('area')
        if area_def is None or hasattr(area_def, 'area_id'):
            continue
        scn[data_id].attrs['area'].area_id = "native"

    for writer_name in writers:
        wargs = writer_args[writer_name]
        res = scn.save_datasets(writer=writer_name, compute=False, datasets=datasets, **wargs)
        if isinstance(res[0], (tuple, list)):
            # list of (dask-array, file-obj) tuples
            to_save.extend(zip(*res))
        else:
            # list of delayed objects
            to_save.extend(res)
    return to_save


def _handle_product_names(aliases, products):
    for prod_name in products:
        product = aliases.get(prod_name, prod_name)
        if isinstance(product, (list, tuple)):
            yield from product
        else:
            yield product


def add_scene_argument_groups(parser, is_polar2grid=False):
    if is_polar2grid:
        readers = [
            'acspo',
            'amsr2_l1b',
            'amsr_l2_gaasp',
            'clavrx',
            'mersi2_l1b',
            'mirs',
            'nucaps',
            'viirs_edr_active_fires',
            'viirs_edr_flood',
            'viirs_l1b',
            'viirs_sdr',
            'virr_l1b',
        ]
    else:
        readers = [
            'abi_l1b',
            'ahi_hrit',
            'ahi_hsd',
        ]

    group_1 = parser.add_argument_group(title='Reading')
    group_1.add_argument('-r', '--reader', action='append', dest='readers',
                         metavar="READER",
                         help='Name of reader used to read provided files. '
                              'Supported readers: ' + ', '.join(readers))
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
    group_1.add_argument('--filter-day-products', nargs='?', type=float,
                         default=False, metavar="fraction_of_day",
                         help="Don't produce products that require "
                              "daytime data when most of the image "
                              "is nighttime (ex. reflectances). The "
                              "list of products checked is currently limited "
                              "to reflectance bands and true and false color "
                              "composites. Default is 0.1 (at least 10%% "
                              "day).")
    group_1.add_argument('--filter-night-products', nargs='?', type=float,
                         default=False, metavar="fraction_of_night",
                         help="Don't produce products that require "
                              "nighttime data when most of the image "
                              "is daytime. The "
                              "list of products checked is currently limited "
                              "to temperature difference fog "
                              "composites. Default is 0.1 (at least 10%% "
                              "night).")
    group_1.add_argument('--sza-threshold', type=float,
                         default=100,
                         help="When making filter decisions based on amount "
                              "of day or amount of night, use this solar "
                              "zenith angle value as the transition point. "
                              "Less than this is day, greater than or equal to "
                              "this value is night.")
    return (group_1,)


def _convert_writer_name(writer_name):
    return WRITER_ALIASES.get(writer_name, writer_name)


def add_writer_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Writing')
    group_1.add_argument('-w', '--writer', action='append', dest='writers',
                         type=_convert_writer_name,
                         metavar="WRITER",
                         help='Writers to save datasets with. Multiple writers '
                              'can be provided by specifying \'-w\' multiple '
                              'times (ex. \'-w geotiff -w awips_tiled\').')
    return (group_1,)


def add_resample_argument_groups(parser, is_polar2grid=False):
    group_1 = parser.add_argument_group(title='Resampling')
    if is_polar2grid:
        DEBUG_EWA = bool(int(os.getenv("P2G_EWA_LEGACY", "0")))
        methods = ['ewa', 'native', 'nearest']
        if DEBUG_EWA:
            methods.append('ewa_legacy')

        group_1.add_argument('--method', dest='resampler',
                             default=None, choices=methods,
                             help='resampling algorithm to use (default: <sensor specific>)')
        group_1.add_argument('-g', '--grids', default=None, nargs="*",
                             help='Area definition to resample to. Empty means '
                                  'no resampling (default: "wgs84_fit" for '
                                  'non-native resampling)')

        # EWA options
        group_1.add_argument('--weight-delta-max', default=argparse.SUPPRESS, type=float,
                             help='Maximum distance in grid cells over which '
                                  'to distribute an input swath pixel (--method "ewa"). '
                                  'Default is 10.0.')
        group_1.add_argument('--weight-distance-max', default=argparse.SUPPRESS, type=float,
                             help='Distance in grid cell units at which to '
                                  'apply a minimum weight. (--method "ewa"). '
                                  'Default is 1.0.')
        group_1.add_argument('--maximum-weight-mode', dest="maximum_weight_mode",
                             default=argparse.SUPPRESS, action="store_true",
                             help='Use maximum weight mode (--method "ewa"). '
                                  'Default is off.')
        group_1.add_argument('--ewa-persist', default=argparse.SUPPRESS,
                             help='Pre-compute geolocation to determine what '
                                  'chunks of data should be resampled '
                                  '(--method "ewa"). This can reduce the '
                                  'overall work required by the algorithm, '
                                  'but only if a small amount of swath data '
                                  'lies on the target area.')
    else:
        group_1.add_argument('--method', dest='resampler',
                             default=None, choices=['native', 'nearest'],
                             help='resampling algorithm to use (default: native)')
        group_1.add_argument('-g', '--grids', default=None, nargs="*",
                             help='Area definition to resample to. Empty means '
                                  'no resampling (default: "MAX")')
    group_1.add_argument('--cache-dir',
                         help='Directory to store resampling intermediate '
                              'results between executions. Not used with native '
                              'resampling or resampling of ungridded or swath data.')
    group_1.add_argument('--grid-configs', dest='grid_configs', nargs="+", default=tuple(),
                         help="Specify additional grid configuration files. "
                              "(.conf for P2G-style grids, .yaml for "
                              "SatPy-style areas)")
    group_1.add_argument('--ll-bbox', nargs=4, type=float, metavar=("lon_min", "lat_min", "lon_max", "lat_max"),
                         help='Crop data to region specified by lon/lat '
                              'bounds (lon_min lat_min lon_max lat_max). '
                              'Coordinates must be valid in the source data '
                              'projection. Can only be used with gridded '
                              'input data.')

    # nearest neighbor resampling
    group_1.add_argument('--radius-of-influence', default=argparse.SUPPRESS, type=float,
                         help='Specify radius to search for valid input '
                              'pixels for nearest neighbor resampling (--method "nearest"). '
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


def _user_products_that_exist(user_products, available_names):
    for user_product in user_products:
        name = user_product if isinstance(user_product, str) else user_product['name']
        if name in available_names:
            yield user_product


def _apply_default_products_and_aliases(scn, reader, user_products):
    reader_mod = importlib.import_module('polar2grid.readers.' + reader)
    default_products = getattr(reader_mod, 'DEFAULT_PRODUCTS', [])
    all_dataset_names = None
    if user_products is None and default_products:
        LOG.info("Using default product list: {}".format(default_products))
        user_products = default_products
        all_dataset_names = scn.all_dataset_names(composites=True)
    elif user_products is None:
        LOG.error("Reader does not have a default set of products to load, "
                  "please specify products to load with `--products`.")
        return None

    # only use defaults that actually exist for the provided files
    aliases = getattr(reader_mod, 'PRODUCT_ALIASES', {})
    user_products = _handle_product_names(aliases, user_products)
    if all_dataset_names is not None:
        user_products = _user_products_that_exist(user_products, all_dataset_names)
    user_products = list(user_products)

    if user_products:
        return user_products
    elif all_dataset_names:
        msg = "No default products found in available file products:\n\t{}"
        msg = msg.format("\n\t".join(all_dataset_names))
        LOG.error(msg)


def main(argv=sys.argv[1:]):
    global LOG

    import satpy
    from satpy import Scene
    from satpy.writers import compute_writer_results
    from dask.diagnostics import ProgressBar
    from polar2grid.core.script_utils import (
        setup_logging, rename_log_file, create_exc_handler)
    import argparse

    dist = pkg_resources.get_distribution('polar2grid')
    if dist_is_editable(dist):
        p2g_etc = os.path.join(dist.module_path, 'etc')
    else:
        p2g_etc = os.path.join(sys.prefix, 'etc', 'polar2grid')
    config_path = satpy.config.get('config_path')
    if p2g_etc not in config_path:
        satpy.config.set(config_path=config_path + [p2g_etc])

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
                        help='each occurrence increases verbosity 1 level through '
                             'ERROR-WARNING-INFO-DEBUG (default INFO)')
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
    reader_group = add_scene_argument_groups(
        parser, is_polar2grid=USE_POLAR2GRID_DEFAULTS)[0]
    resampling_group = add_resample_argument_groups(
        parser, is_polar2grid=USE_POLAR2GRID_DEFAULTS)[0]
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
    reader_names = reader_args.pop('readers')
    scene_creation = {
        'filenames': reader_args.pop('filenames'),
        'reader': reader_names[0],
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
        dask.config.set(num_workers=args.num_workers)

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

    ll_bbox = resample_args.pop('ll_bbox')
    if ll_bbox:
        scn = scn.crop(ll_bbox=ll_bbox)

    scn = filter_scene(scn, reader_names,
                       sza_threshold=reader_args['sza_threshold'],
                       day_fraction=reader_args['filter_day_products'],
                       night_fraction=reader_args['filter_night_products'],
                       )
    if scn is None:
        LOG.info("No remaining products after filtering.")
        return 0

    to_save = []
    areas_to_resample = resample_args.pop("grids")
    if 'ewa_persist' in resample_args:
        resample_args['persist'] = resample_args.pop('ewa_persist')
    scenes_to_save = resample_scene(scn, areas_to_resample, preserve_resolution=args.preserve_resolution,
                                    is_polar2grid=USE_POLAR2GRID_DEFAULTS,
                                    **resample_args)
    for scene_to_save, products_to_save in scenes_to_save:
        overwrite_platform_name_with_aliases(scene_to_save)
        to_save = write_scene(scene_to_save, writer_args['writers'], writer_args, products_to_save, to_save=to_save)

    if args.progress:
        pbar = ProgressBar()
        pbar.register()

    LOG.info("Computing products and saving data to writers...")
    compute_writer_results(to_save)
    LOG.info("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
