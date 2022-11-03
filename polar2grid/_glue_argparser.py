#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2022 Space Science and Engineering Center (SSEC),
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
"""Argument parsing and script setup for the main glue.py script."""
from __future__ import annotations

import argparse
import os
import sys
from glob import glob
from typing import Callable, Optional

from polar2grid.core.script_utils import ExtendAction
from polar2grid.utils.dynamic_imports import get_reader_attr, get_writer_attr

# type aliases
ComponentParserFunc = Callable[[argparse.ArgumentParser], tuple]


def get_reader_parser_function(reader_name: str) -> Optional[ComponentParserFunc]:
    return get_reader_attr(reader_name, "add_reader_argument_groups")


def get_writer_parser_function(writer_name: str) -> Optional[ComponentParserFunc]:
    return get_writer_attr(writer_name, "add_writer_argument_groups")


READER_ALIASES = {
    "modis": "modis_l1b",
    "avhrr": "avhrr_l1b_aapp",
}
WRITER_ALIASES = {
    "scmi": "awips_tiled",
}


def get_default_output_filename(reader: str, writer: str, is_polar2grid: bool):
    """Get a default output filename based on what reader we are reading."""
    ofile_map = get_writer_attr(writer, "DEFAULT_OUTPUT_FILENAMES", {})
    pkg_name = "polar2grid" if is_polar2grid else "geo2grid"
    package_filenames = ofile_map[pkg_name]
    if reader not in package_filenames:
        reader = None
    return package_filenames.get(reader)


def _fsfiles_for_s3(input_filenames):
    """Convert S3 URLs to something Satpy can understand and use.

    Examples:
        Example S3 URLs (no caching):

        .. code-block:: bash

            polar2grid.sh ... -f s3://noaa-goes16/ABI-L1b-RadC/2019/001/17/*_G16_s20190011702186*

        Example S3 URLs using fsspec caching:

        .. code-block:: bash

            polar2grid.sh ... -f simplecache::s3://noaa-goes16/ABI-L1b-RadC/2019/001/17/*_G16_s20190011702186*

    """
    import fsspec
    from satpy.readers import FSFile

    kwargs = {"anon": True}
    if "simplecache::" in input_filenames[0]:
        kwargs = {"s3": kwargs}
    for open_file in fsspec.open_files(input_filenames, **kwargs):
        yield FSFile(open_file)


def _filenames_from_local(input_filenames):
    for fn in input_filenames:
        if os.path.isdir(fn):
            yield from glob(os.path.join(fn, "*"))
        else:
            yield fn


def get_input_files(input_filenames):
    """Convert directories to list of files."""
    if input_filenames and "s3://" in input_filenames[0]:
        yield from _fsfiles_for_s3(input_filenames)
    else:
        yield from _filenames_from_local(input_filenames)


def get_p2g_defaults_env_var():
    return bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))


class GlueArgumentParser:
    """Helper class for parsing and grouping command line arguments."""

    def __init__(self, argv: list[str], is_polar2grid: bool):
        self._is_polar2grid = is_polar2grid
        parser, known_args, reader_group, resampling_group, writer_group = _main_args(argv, self._is_polar2grid)
        # env used by some writers for default number of threads (ex. geotiff)
        # must be done before writer args are parsed
        os.environ["DASK_NUM_WORKERS"] = str(known_args.num_workers)

        reader_subgroups = _add_component_parser_args(parser, "readers", known_args.readers or [])
        writer_subgroups = _add_component_parser_args(parser, "writers", known_args.writers or [])
        self.argv = argv
        self._args = parser.parse_args(argv)
        _validate_reader_writer_args(parser, self._args, self._is_polar2grid)

        self._reader_args = _args_to_dict(self._args, reader_group._group_actions)
        self._reader_names = self._reader_args.pop("readers")
        self._separate_scene_init_load_args(reader_subgroups)
        self._resample_args = _args_to_dict(self._args, resampling_group._group_actions)
        self._writer_args = _args_to_dict(self._args, writer_group._group_actions)
        writer_specific_args = self._parse_one_writer_args(writer_subgroups)
        self._writer_args.update(writer_specific_args)

        if not self._args.filenames:
            parser.print_usage()
            parser.exit(1, "\nERROR: No data files provided (-f flag)\n")

    def _separate_scene_init_load_args(self, reader_subgroups) -> None:
        products = self._reader_args.pop("products") or []
        filenames = self._reader_args.pop("filenames") or []
        filenames = list(get_input_files(filenames))

        reader_specific_args, reader_specific_load_args = self._parse_reader_args(reader_subgroups)
        # argparse will combine "extended" arguments like `products` automatically
        # and products should only be provided to the load arguments, not reader creation
        for _reader_name, _reader_args in reader_specific_args.items():
            _reader_args.pop("products", None)

        # Parse provided files and search for files if provided directories
        self._scene_creation = {
            "filenames": filenames,
            "reader": self._reader_names[0],
            "reader_kwargs": reader_specific_args.get(self._reader_names[0], {}),
        }
        self._load_args = {
            "products": products,
        }
        self._load_args.update(reader_specific_load_args)

    def _parse_reader_args(self, reader_subgroups: list) -> tuple[dict, dict]:
        reader_args = {}
        load_args = {}
        for reader_name, (sgrp1, sgrp2) in zip(self._reader_names, reader_subgroups):
            if sgrp1 is None:
                continue
            rargs = _args_to_dict(self._args, sgrp1._group_actions)
            reader_args[reader_name] = rargs
            if sgrp2 is not None:
                load_args.update(_args_to_dict(self._args, sgrp2._group_actions))
        return reader_args, load_args

    def _parse_one_writer_args(self, writer_subgroups: list) -> dict:
        writer_names: list[str] = self._writer_args["writers"]
        writer_specific_args = {}
        for writer_name, (sgrp1, sgrp2) in zip(writer_names, writer_subgroups):
            wargs = _args_to_dict(self._args, sgrp1._group_actions)
            if sgrp2 is not None:
                wargs.update(_args_to_dict(self._args, sgrp2._group_actions))
            writer_specific_args[writer_name] = wargs
            # get default output filename
            if "filename" in wargs and wargs["filename"] is None:
                wargs["filename"] = get_default_output_filename(self._reader_names[0], writer_name, self._is_polar2grid)
        return writer_specific_args


def _main_args(argv, use_polar2grid_defaults):
    binary_name = "polar2grid" if use_polar2grid_defaults else "geo2grid"
    prog = os.getenv("PROG_NAME", sys.argv[0])
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
    parser = argparse.ArgumentParser(
        prog=prog,
        usage=usage,
        fromfile_prefix_chars="@",
        description="Load, composite, resample, and save datasets.",
    )
    _add_common_arguments(parser, binary_name)
    reader_group = add_scene_argument_groups(parser, is_polar2grid=use_polar2grid_defaults)[0]
    resampling_group = add_resample_argument_groups(parser, is_polar2grid=use_polar2grid_defaults)[0]
    writer_group = add_writer_argument_groups(parser, is_polar2grid=use_polar2grid_defaults)[0]
    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]

    _retitle_optional_arguments(parser)
    args, _ = parser.parse_known_args(argv_without_help)
    return parser, args, reader_group, resampling_group, writer_group


def _add_common_arguments(parser: argparse.ArgumentParser, binary_name: str) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=0,
        help="each occurrence increases verbosity 1 level through " "ERROR-WARNING-INFO-DEBUG (default INFO)",
    )
    parser.add_argument("-l", "--log", dest="log_fn", default=None, help="specify the log filename")
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show processing progress bar (Not recommended for logged output)",
    )
    parser.add_argument(
        "--create-profile",
        nargs="?",
        default=False,
        help=argparse.SUPPRESS,
        # help="Create an HTML document profiling the execution of the script "
        #      "using dask diagnostic tools.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=os.getenv("DASK_NUM_WORKERS", 4),
        help="Specify number of worker threads to use (Default: 4)",
    )
    parser.add_argument(
        "--extra-config-path",
        action="append",
        help="Specify the base directory of additional Satpy configuration "
        "files. For example, to use custom enhancement YAML file named "
        "'generic.yaml' place it in a directory called 'enhancements' "
        "like '/path/to/my_configs/enhancements/generic.yaml' and then "
        "set this flag to '/path/to/my_configs'. For backwards compatibility, "
        "with older versions, this flag can also be given a single enhancement "
        "YAML configuration file.",
    )
    parser.add_argument(
        "--match-resolution",
        dest="preserve_resolution",
        action="store_false",
        help="When using the 'native' resampler for composites, don't save data "
        "at its native resolution, use the resolution used to create the "
        "composite.",
    )
    parser.add_argument(
        "--list-products",
        dest="list_products",
        action="store_true",
        help="List available {} products and exit".format(binary_name),
    )
    parser.add_argument(
        "--list-products-all",
        dest="list_products_all",
        action="store_true",
        help="List available {} products and custom/Satpy products and exit".format(binary_name),
    )


def _validate_reader_writer_args(parser, args, use_polar2grid_defaults):
    if args.readers is None:
        parser.print_usage()
        parser.exit(
            1,
            "\nERROR: Reader must be provided (-r flag).\n"
            "Supported readers:\n\t{}\n".format("\n\t".join(_supported_readers(use_polar2grid_defaults))),
        )
    elif len(args.readers) > 1:
        parser.print_usage()
        parser.exit(
            1,
            "\nMultiple readers is not currently supported. Got:\n\t" "{}\n".format("\n\t".join(args.readers)),
        )
        return -1
    if args.writers is None:
        parser.print_usage()
        parser.exit(
            1,
            "\nERROR: Writer must be provided (-w flag) with one or more writer.\n"
            "Supported writers:\n\t{}\n".format("\n\t".join(_supported_writers(use_polar2grid_defaults))),
        )


def _add_component_parser_args(
    parser: argparse.ArgumentParser, component_type: str, component_names: list[str]
) -> list:
    _get_args_func = get_writer_parser_function if component_type == "writers" else get_reader_parser_function
    subgroups = []
    for component_name in component_names:
        parser_func = _get_args_func(component_name)
        if parser_func is None:
            # two items in each tuple
            subgroups += [(None, None)]
            continue
        subgroups += [parser_func(parser)]
    return subgroups


def _args_to_dict(args, group_actions, exclude=None):
    if exclude is None:
        exclude = []
    return {
        ga.dest: getattr(args, ga.dest) for ga in group_actions if hasattr(args, ga.dest) and ga.dest not in exclude
    }


def _convert_reader_name(reader_name: str) -> str:
    return READER_ALIASES.get(reader_name, reader_name)


def _convert_writer_name(writer_name: str) -> str:
    return WRITER_ALIASES.get(writer_name, writer_name)


def _supported_readers(is_polar2grid: bool = False) -> list[str]:
    if is_polar2grid:
        readers = [
            "acspo",
            "amsr2_l1b",
            "amsr_l2_gaasp",
            "avhrr_l1b_aapp",
            "clavrx",
            "mersi2_l1b",
            "mirs",
            "modis_l1b",
            "modis_l2",
            "nucaps",
            "viirs_edr_active_fires",
            "viirs_edr_flood",
            "viirs_l1b",
            "viirs_sdr",
            "virr_l1b",
        ]
    else:
        readers = [
            "abi_l1b",
            "abi_l2_nc",
            "agri_l1",
            "ahi_hrit",
            "ahi_hsd",
            "ami_l1b",
            "glm_l2",
        ]
    return sorted(readers)


def add_scene_argument_groups(parser, is_polar2grid=False):
    if is_polar2grid:
        filter_dn_products = 0.1
        filter_doc = " and is enabled by default."
    else:
        filter_dn_products = False
        filter_doc = ", but is disabled by default."
    readers = _supported_readers(is_polar2grid)

    group_1 = parser.add_argument_group(title="Reading")
    group_1.add_argument(
        "-r",
        "--reader",
        action="append",
        dest="readers",
        metavar="READER",
        type=_convert_reader_name,
        help="Name of reader used to read provided files. " "Supported readers: " + ", ".join(readers),
    )
    group_1.add_argument(
        "-f",
        "--filenames",
        nargs="+",
        default=[],
        help="Input files to read. For a long list of "
        "files, use '-f @my_files.txt' "
        "to provide a list of filenames from another "
        "file (one filename per line). Files can also "
        "be passed at the end of the command line by "
        "using two hyphens (--) to separate the list "
        "of files from the other arguments. "
        "arguments (ex. '%(prog)s ... -- /path/to/files*')",
    )
    group_1.add_argument("filenames", nargs="*", action="extend", help=argparse.SUPPRESS)
    # help="Alternative to '-f' flag. Use two hyphens (--) "
    #      "to separate these files from other command line "
    #      "arguments (ex. '%(prog)s ... -- /path/to/files*')")
    group_1.add_argument(
        "-p",
        "--products",
        nargs="+",
        default=None,
        action=ExtendAction,
        help="Names of products to create from input files",
    )
    group_1.add_argument(
        "--filter-day-products",
        nargs="?",
        type=float_or_false,
        default=filter_dn_products,
        metavar="fraction_of_day",
        help="Don't produce products that require "
        "daytime data when most of the image "
        "is nighttime (ex. reflectances). The "
        "list of products checked is currently limited "
        "to reflectance bands and true and false color "
        "composites. Default is 0.1 (at least 10%% "
        "day)" + filter_doc,
    )
    group_1.add_argument(
        "--filter-night-products",
        nargs="?",
        type=float_or_false,
        default=filter_dn_products,
        metavar="fraction_of_night",
        help="Don't produce products that require "
        "nighttime data when most of the image "
        "is daytime. The "
        "list of products checked is currently limited "
        "to temperature difference fog "
        "composites. Default is 0.1 (at least 10%% "
        "night)" + filter_doc,
    )
    group_1.add_argument(
        "--sza-threshold",
        type=float,
        default=100,
        help="When making filter decisions based on amount "
        "of day or amount of night, use this solar "
        "zenith angle value as the transition point. "
        "Less than this is day, greater than or equal to "
        "this value is night.",
    )
    group_1.add_argument(
        "--no-persist-geolocation",
        action="store_true",
        # help="After data is loaded, compute all geolocation arrays and hold "
        #      "them in memory. This should allow processing to perform faster "
        #      "in most cases at the cost of higher memory usage. This will "
        #      "have the biggest impact on readers whose lon/lat arrays are "
        #      "expensive to load (ex. modis_l1b). This currently only works "
        #      "on swath-based geolocation data and has no effect otherwise.",
        help=argparse.SUPPRESS,
    )
    return (group_1,)


def float_or_false(val):
    if isinstance(val, str) and val.lower() == "false":
        return False
    return float(val)


def _supported_writers(is_polar2grid: bool = False) -> list[str]:
    if is_polar2grid:
        writers = [
            "geotiff",
            "awips_tiled",
            "binary",
            "hdf5",
        ]
    else:
        writers = [
            "geotiff",
            "awips_tiled",
        ]
    return writers


def add_writer_argument_groups(parser, is_polar2grid=False):
    writers = _supported_writers(is_polar2grid)
    group_1 = parser.add_argument_group(title="Writing")
    group_1.add_argument(
        "-w",
        "--writer",
        action="append",
        dest="writers",
        type=_convert_writer_name,
        metavar="WRITER",
        help="Writer used to save datasets. " "Supported writers: " + ", ".join(writers),
        # help="Writers to save datasets with. Multiple writers "
        #      "can be provided by specifying '-w' multiple "
        #      "times (ex. '-w geotiff -w awips_tiled'). "
        #      "Supported writers: " + ", ".join(writers),
    )
    return (group_1,)


def add_resample_argument_groups(parser, is_polar2grid=None):
    if is_polar2grid is None:
        # if we are being loaded from documentation then this won't be
        # specified so we need to load it directly from the environment variable
        is_polar2grid = get_p2g_defaults_env_var()

    group_1 = parser.add_argument_group(title="Resampling")
    if is_polar2grid:
        DEBUG_EWA = bool(int(os.getenv("P2G_EWA_LEGACY", "0")))
        methods = ["ewa", "native", "nearest"]
        if DEBUG_EWA:
            methods.append("ewa_legacy")

        group_1.add_argument(
            "--method",
            dest="resampler",
            default=None,
            choices=methods,
            help="resampling algorithm to use (default: <sensor specific>)",
        )
        group_1.add_argument(
            "-g",
            "--grids",
            default=None,
            nargs="*",
            help="Area definition to resample to. Empty means "
            'no resampling (default: "wgs84_fit" for '
            "non-native resampling)",
        )

        # EWA options
        group_1.add_argument(
            "--weight-delta-max",
            default=argparse.SUPPRESS,
            type=float,
            help="Maximum distance in grid cells over which "
            'to distribute an input swath pixel (--method "ewa"). '
            'This is equivalent to the old "--fornav-D" flag.'
            "Default is 10.0.",
        )
        group_1.add_argument(
            "--weight-distance-max",
            default=argparse.SUPPRESS,
            type=float,
            help="Distance in grid cell units at which to "
            'apply a minimum weight. (--method "ewa"). '
            'This is equivalent to the old "--fornav-d" flag.'
            "Default is 1.0.",
        )
        group_1.add_argument(
            "--maximum-weight-mode",
            dest="maximum_weight_mode",
            default=argparse.SUPPRESS,
            action="store_true",
            help='Use maximum weight mode (--method "ewa"). Default is off.',
        )
        group_1.add_argument(
            "--rows-per-scan",
            dest="rows_per_scan",
            default=argparse.SUPPRESS,
            type=int,
            help="Number of data rows making up one instrument scan. "
            '(--method "ewa"). Defaults to value extracted from '
            "reader.",
        )
        group_1.add_argument(
            "--ewa-persist",
            action="store_true",
            help=argparse.SUPPRESS,
            # help="Pre-compute geolocation to determine what "
            # "chunks of data should be resampled "
            # '(--method "ewa"). This can reduce the '
            # "overall work required by the algorithm, "
            # "but only if a small amount of swath data "
            # "lies on the target area.",
        )
    else:
        group_1.add_argument(
            "--method",
            dest="resampler",
            default=None,
            choices=["native", "nearest"],
            help="resampling algorithm to use (default: native)",
        )
        group_1.add_argument(
            "-g",
            "--grids",
            default=None,
            nargs="*",
            help='Area definition to resample to. Empty means no resampling (default: "MAX")',
        )

    # shared options
    group_1.add_argument(
        "--grid-coverage",
        default=0.1,
        type=float,
        help="Fraction of target grid that must contain " "data to continue processing product.",
    )
    group_1.add_argument(
        "--cache-dir",
        help="Directory to store resampling intermediate "
        "results between executions. Not used with native "
        "resampling or resampling of ungridded or swath data.",
    )
    group_1.add_argument(
        "--grid-configs",
        nargs="+",
        default=tuple(),
        help="Specify additional grid configuration files. "
        "(.conf for legacy CSV grids, .yaml for "
        "SatPy-style areas)",
    )
    group_1.add_argument(
        "--ll-bbox",
        nargs=4,
        type=float,
        metavar=("lon_min", "lat_min", "lon_max", "lat_max"),
        help=argparse.SUPPRESS
        if is_polar2grid
        else "Crop data to region specified by lon/lat "
        "bounds (lon_min lat_min lon_max lat_max). "
        "Coordinates must be valid in the source data "
        "projection. Can only be used with gridded "
        "input data.",
    )
    group_1.add_argument(
        "--antimeridian-mode",
        default="modify_crs",
        choices=("modify_extents", "modify_crs", "global_extents"),
        help="Behavior when dynamic grids are converted to 'frozen' grids and "
        "data crosses the anti-meridian. Defaults to 'modify_crs' where "
        "the prime meridian is shifted 180 degrees to make the result one "
        "contiguous coordinate space. 'modify_extents' will attempt to "
        "surround the data but will often cause artifacts over the "
        "antimeridian. 'global_extents' will force the X extents to -180 "
        "and 180 to create one large grid. This currently only affects "
        "lon/lat projections.",
    )

    # nearest neighbor resampling
    group_1.add_argument(
        "--radius-of-influence",
        default=argparse.SUPPRESS,
        type=float,
        help="Specify radius to search for valid input "
        'pixels for nearest neighbor resampling (--method "nearest"). '
        "Value is in geocentric meters regardless of input or output projection. "
        "By default this will be estimated based on input and output projection and pixel size.",
    )
    return tuple([group_1])


def _retitle_optional_arguments(parser):
    """Hack to make the optional arguments say what we want."""
    opt_args = [x for x in parser._action_groups if x.title == "optional arguments"]
    if len(opt_args) == 1:
        opt_args = opt_args[0]
        opt_args.title = "Global Options"
