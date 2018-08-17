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
from glob import glob
import dask
import dask.array as da

LOG = logging.getLogger(__name__)


def compute_writer_results(results):
    sources = []
    targets = []
    delayeds = []
    for res in results:
        if isinstance(res, tuple):
            # source, target to be passed to da.store
            sources.append(res[0])
            targets.append(res[1])
        else:
            # delayed object
            delayeds.append(res)

    # one or more writers have targets that we need to close in the future
    if targets:
        delayeds.append(da.store(sources, targets, compute=False))

    if delayeds:
        da.compute(delayeds)

    if targets:
        for target in targets:
            if hasattr(target, 'close'):
                target.close()


def add_scene_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Scene Initialization')
    group_1.add_argument('reader',
                         help='Name of reader used to read provided files')
    group_1.add_argument('-f', '--filenames', nargs='+', required=True,
                         help='Input files to read')
    group_2 = parser.add_argument_group(title='Scene Load')
    group_2.add_argument('-d', '--datasets', nargs='+',
                         help='Names of datasets to load from input files')
    return group_1, group_2


def add_resample_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Resampling')
    group_1.add_argument('--method', dest='resampler',
                         default='native', choices=['native', 'nearest'],
                         help='resampling algorithm to use (default: native)')
    group_1.add_argument('--cache-dir',
                         help='Directory to store resampling intermediate '
                              'results between executions')
    group_1.add_argument('-g', '--grids', default=['MAX'], nargs="*",
                         help='Area definition to resample to. Empty means '
                              'no resampling (default: MAX)')
    group_1.add_argument('--grid-configs', dest='grid_configs', nargs="+", default=tuple(),
                         help="Specify additional grid configuration files. "
                              "(.conf for P2G-style grids, .yaml for "
                              "SatPy-style areas)")
    return tuple([group_1])


def add_geotiff_argument_groups(parser):
    group_1 = parser.add_argument_group(title='Writer Initialization')
    group_1.add_argument('--file-pattern',
                         help="custom file pattern to save dataset to")
    group_2 = parser.add_argument_group(title='Writer Save')
    return group_1, group_2


def main():
    from satpy import Scene
    from satpy.resample import get_area_def
    from dask.diagnostics import ProgressBar
    import argparse
    parser = argparse.ArgumentParser(description="Load, composite, resample, and save datasets")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    parser.add_argument('-l', '--log', dest="log_fn", default=None,
                        help="specify the log filename")
    parser.add_argument('--progress', action='store_true',
                        help="show processing progress bar (not recommended for logged output)")
    parser.add_argument('--num-workers', type=int,
                        help="specify number of worker threads to use (default: 1 per logical core)")
    parser.add_argument('-w', '--writers', nargs='+', choices=['geotiff'], default=['geotiff'],
                        help='writers to save datasets with')
    subgroups = add_scene_argument_groups(parser)
    subgroups += add_resample_argument_groups(parser)
    subgroups += add_geotiff_argument_groups(parser)
    args = parser.parse_args()

    scene_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[0]._group_actions}
    load_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[1]._group_actions}
    resample_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[2]._group_actions}
    writer_init_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[3]._group_actions}
    writer_call_args = {ga.dest: getattr(args, ga.dest) for ga in subgroups[4]._group_actions}

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)], filename=args.log_fn)

    writers = args.writers
    if len(writers) != 1:
        raise ValueError("Multiple writers is not currently supported.")

    if args.num_workers:
        from multiprocessing.pool import ThreadPool
        dask.set_options(pool=ThreadPool(args.num_workers))

    all_filenames = []
    for fn in scene_args['filenames']:
        if os.path.isdir(fn):
            all_filenames.extend(glob(os.path.join(fn, '*')))
        else:
            all_filenames.append(fn)
    scene_args['filenames'] = all_filenames

    scn = Scene(**scene_args)
    scn.load(load_args['datasets'])

    resample_kwargs = resample_args.copy()
    areas_to_resample = resample_kwargs.pop('grids')
    grid_configs = resample_kwargs.pop('grid_configs')
    if not areas_to_resample:
        areas_to_resample = [None]
    has_custom_grid = any(g not in ['MIN', 'MAX', None] for g in areas_to_resample)
    if has_custom_grid and resample_kwargs['resampler'] == 'native':
        raise ValueError("Must specify resampling method (--method) when "
                         "a target grid (-g) is specified.")

    p2g_grid_configs = [x for x in grid_configs if x.endswith('.conf')]
    pyresample_area_configs = [x for x in grid_configs if not x.endswith('.conf')]
    if p2g_grid_configs:
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

    to_save = []
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
            area_def = grid_manager[area_name].to_satpy_area()
        else:
            area_def = get_area_def(area_name)

        if area_def is not None:
            new_scn = scn.resample(area_def, **resample_kwargs)
        else:
            # the user didn't want to resample to any areas
            new_scn = scn

        for writer_name in writers:
            writer_args = {}
            writer_args.update(writer_init_args)
            writer_args.update(writer_call_args)
            res = new_scn.save_datasets(writer=writer_name, compute=False,
                                        **writer_args)
            if isinstance(res, (tuple, list)):
                to_save.extend(zip(*res))
            else:
                to_save.append(res)

    if args.progress:
        pbar = ProgressBar()
        pbar.register()

    compute_writer_results(to_save)
    return 0


if __name__ == "__main__":
    sys.exit(main())
