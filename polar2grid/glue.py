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
import logging
import importlib
from glob import glob
import dask

from polar2grid.writers import geotiff, scmi

LOG = logging.getLogger(__name__)

WRITER_PARSER_FUNCTIONS = {
    'geotiff': geotiff.add_writer_argument_groups,
    'scmi': scmi.add_writer_argument_groups,
}

OUTPUT_FILENAMES = {
    'geotiff': geotiff.DEFAULT_OUTPUT_FILENAME,
}


def get_default_output_filename(reader, writer):
    """Get a default output filename based on what reader we are reading."""
    ofile_map = OUTPUT_FILENAMES.get(writer, {})
    if reader not in ofile_map:
        reader = None
    return ofile_map[reader]


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

    for writer_name in writers:
        wargs = writer_args[writer_name]

        res = scn.save_datasets(writer=writer_name, compute=False, datasets=datasets, **wargs)
        if isinstance(res, (tuple, list)):
            to_save.extend(zip(*res))
        else:
            to_save.append(res)
    return to_save


def add_scene_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Scene Initialization')
    group_1.add_argument('-r', '--reader',
                         help='Name of reader used to read provided files')
    group_1.add_argument('-f', '--filenames', nargs='+', default=[],
                         help='Input files to read')
    group_2 = parser.add_argument_group(title='Scene Load')
    group_2.add_argument('-p', '--products', nargs='+',
                         help='Names of products to load from input files')
    return group_1, group_2


def add_resample_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Resampling')
    group_1.add_argument('--method', dest='resampler',
                         default=None, choices=['native', 'nearest'],
                         help='resampling algorithm to use (default: native)')
    group_1.add_argument('--cache-dir',
                         help='Directory to store resampling intermediate '
                              'results between executions')
    group_1.add_argument('-g', '--grids', default=None, nargs="*",
                         help='Area definition to resample to. Empty means '
                              'no resampling (default: MAX)')
    group_1.add_argument('--grid-configs', dest='grid_configs', nargs="+", default=tuple(),
                         help="Specify additional grid configuration files. "
                              "(.conf for P2G-style grids, .yaml for "
                              "SatPy-style areas)")
    group_1.add_argument('--ll-bbox', nargs=4, type=float,
                         help='Crop data to region specified by lon/lat '
                              'bounds (lon_min lat_min lon_max lat_max).'
                              'Coordinates must be valid in the source data '
                              'projection. For negative numbers use quotes '
                              'preceeded by a space: " -95.5"')
    return tuple([group_1])


def main(argv=sys.argv[1:]):
    global LOG
    from satpy import Scene
    from satpy.resample import get_area_def
    from satpy.writers import compute_writer_results
    from dask.diagnostics import ProgressBar
    from polar2grid.core.script_utils import (
        setup_logging, rename_log_file, create_exc_handler)
    import argparse
    parser = argparse.ArgumentParser(description="Load, composite, resample, and save datasets")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-l', '--log', dest="log_fn", default=None,
                        help="specify the log filename")
    parser.add_argument('--progress', action='store_true',
                        help="show processing progress bar (not recommended for logged output)")
    parser.add_argument('--num-workers', type=int, default=4,
                        help="specify number of worker threads to use (default: 4)")
    parser.add_argument('--match-resolution', dest='preserve_resolution', action='store_false',
                        help="When using the 'native' resampler for composites, don't save data "
                             "at its native resolution, use the resolution used to create the "
                             "composite.")
    parser.add_argument('-w', '--writers', nargs='+', default=['geotiff'],
                        help='writers to save datasets with')
    parser.add_argument("--list-products", dest="list_products", action="store_true",
                        help="List available reader products and exit")
    subgroups = add_scene_argument_groups(parser)
    subgroups += add_resample_argument_groups(parser)

    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]
    args, remaining_args = parser.parse_known_args(argv_without_help)

    if args.reader is None:
        parser.print_usage()
        parser.exit(1, "ERROR: Reader must be provided (-r flag)\n")

    glue_name = args.reader + "_" + "-".join(args.writers)
    LOG = logging.getLogger(glue_name)
    for writer in args.writers:
        parser_func = WRITER_PARSER_FUNCTIONS.get(writer)
        if parser_func is None:
            continue
        subgroups += parser_func(parser)
    args = parser.parse_args(argv)

    def _args_to_dict(group_actions):
        return {ga.dest: getattr(args, ga.dest) for ga in group_actions}
    scene_args = _args_to_dict(subgroups[0]._group_actions)
    load_args = _args_to_dict(subgroups[1]._group_actions)
    resample_args = _args_to_dict(subgroups[2]._group_actions)
    writer_args = {}
    for idx, writer in enumerate(args.writers):
        sgrp1, sgrp2 = subgroups[3 + idx * 2: 5 + idx * 2]
        wargs = _args_to_dict(sgrp1._group_actions)
        if sgrp2 is not None:
            wargs.update(_args_to_dict(sgrp2._group_actions))
        writer_args[writer] = wargs
        # get default output filename
        if 'filename' in wargs and wargs['filename'] is None:
            wargs['filename'] = get_default_output_filename(args.reader, writer)

    if not args.filenames:
        parser.print_usage()
        parser.exit(1, "ERROR: No data files provided (-f flag)\n")

    # Prepare logging
    rename_log = False
    if args.log_fn is None:
        rename_log = True
        args.log_fn = glue_name + "_fail.log"
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    logging.getLogger('rasterio').setLevel(levels[min(2, args.verbosity)])
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))

    # Set up dask and the number of workers
    if args.num_workers:
        from multiprocessing.pool import ThreadPool
        dask.config.set(pool=ThreadPool(args.num_workers))

    # Parse provided files and search for files if provided directories
    scene_args['filenames'] = get_input_files(scene_args['filenames'])
    # Create a Scene, analyze the provided files
    scn = Scene(**scene_args)

    if args.list_products:
        print("\n".join(sorted(scn.available_dataset_names(composites=True))))
        return 0

    # Rename the log file
    if rename_log:
        rename_log_file(glue_name + scn.attrs['start_time'].strftime("_%Y%m%d_%H%M%S.log"))

    # Load the actual data arrays and metadata (lazy loaded as dask arrays)
    LOG.info("Loading product metadata from files...")
    if load_args['products'] is None:
        try:
            reader_mod = importlib.import_module('polar2grid.readers.' + scene_args['reader'])
            load_args['products'] = reader_mod.DEFAULT_PRODUCTS
            LOG.info("Using default product list: {}".format(load_args['products']))
        except (ImportError, AttributeError):
            LOG.error("No default products list set, please specify with `--products`.")
            return -1

    scn.load(load_args['products'])

    resample_kwargs = resample_args.copy()
    areas_to_resample = resample_kwargs.pop('grids')
    grid_configs = resample_kwargs.pop('grid_configs')
    if not areas_to_resample:
        areas_to_resample = [None]
    has_custom_grid = any(g not in ['MIN', 'MAX', None] for g in areas_to_resample)
    resampler = resample_kwargs.pop('resampler')
    if has_custom_grid and resampler == 'native':
        LOG.error("Resampling method 'native' can only be used with 'MIN' or 'MAX' grids (use 'nearest' instead).")
        return -1

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
        preserved_products = set(wishlist) & set(scn.datasets.keys())
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
            from pyresample.geometry import DynamicAreaDefinition
            p2g_def = grid_manager[area_name]
            area_def = p2g_def.to_satpy_area()
            if isinstance(area_def, DynamicAreaDefinition) and p2g_def['cell_width'] is not None:
                area_def = area_def.freeze(scn.max_area(),
                                           resolution=(abs(p2g_def['cell_width']), abs(p2g_def['cell_height'])))
        else:
            area_def = get_area_def(area_name)

        if resampler is None and area_def is not None:
            rs = 'native' if area_name in ['MIN', 'MAX'] else 'nearest'
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

        to_save = write_scene(new_scn, args.writers, writer_args, resampled_products, to_save=to_save)

    if args.progress:
        pbar = ProgressBar()
        pbar.register()

    LOG.info("Saving data to writers...")
    compute_writer_results(to_save)
    return 0


if __name__ == "__main__":
    sys.exit(main())
