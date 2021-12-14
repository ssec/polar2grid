#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2021 Space Science and Engineering Center (SSEC),
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
"""Connect various satpy components together to go from satellite data to output imagery format."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from glob import glob
from typing import Callable, Optional

import dask
import satpy
from dask.diagnostics import ProgressBar
from satpy import Scene
from satpy.writers import compute_writer_results

from polar2grid.core.script_utils import (
    ExtendAction,
    create_exc_handler,
    rename_log_file,
    setup_logging,
)
from polar2grid.filters import filter_scene
from polar2grid.readers._base import ReaderProxyBase
from polar2grid.resample import resample_scene
from polar2grid.utils.config import add_polar2grid_config_paths
from polar2grid.utils.dynamic_imports import get_reader_attr, get_writer_attr

# type aliases
ComponentParserFunc = Callable[[argparse.ArgumentParser], tuple]

LOG = logging.getLogger(__name__)


def get_reader_parser_function(reader_name: str) -> Optional[ComponentParserFunc]:
    return get_reader_attr(reader_name, "add_reader_argument_groups")


def get_writer_parser_function(writer_name: str) -> Optional[ComponentParserFunc]:
    return get_writer_attr(writer_name, "add_writer_argument_groups")


PLATFORM_ALIASES = {
    "suomi-npp": "npp",
    "snpp": "npp",
    "n20": "noaa20",
    "n21": "noaa21",
    "n22": "noaa22",
    "n23": "noaa23",
    "noaa-20": "noaa20",
    "noaa-21": "noaa21",
    "noaa-22": "noaa22",
    "noaa-23": "noaa23",
    "jpss-1": "noaa20",
    "jpss-2": "noaa21",
    "jpss-3": "noaa22",
    "jpss-4": "noaa23",
    "j1": "noaa20",
    "j2": "noaa21",
    "j3": "noaa22",
    "j4": "noaa23",
    "fy-3b": "fy3b",
    "fy-3c": "fy3c",
    "fy-3d": "fy3d",
    "eos-aqua": "aqua",
    "eos-terra": "terra",
    "aqua": "aqua",
    "terra": "terra",
    "gcom-w1": "gcom-w1",
}

READER_ALIASES = {
    "modis": "modis_l1b",
    "avhrr": "avhrr_l1b_aapp",
}

WRITER_ALIASES = {
    "scmi": "awips_tiled",
}


def get_platform_name_alias(satpy_platform_name):
    return PLATFORM_ALIASES.get(satpy_platform_name.lower(), satpy_platform_name)


def overwrite_platform_name_with_aliases(scn):
    """Change 'platform_name' for every DataArray to Polar2Grid expectations."""
    for data_arr in scn:
        if "platform_name" not in data_arr.attrs:
            continue
        pname = get_platform_name_alias(data_arr.attrs["platform_name"])
        data_arr.attrs["platform_name"] = pname


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


def write_scene(scn, writers, writer_args, datasets, to_save=None):
    if to_save is None:
        to_save = []
    if not datasets:
        # no datasets to save
        return to_save

    for data_id in datasets:
        area_def = scn[data_id].attrs.get("area")
        if area_def is None or hasattr(area_def, "area_id"):
            continue
        scn[data_id].attrs["area"].area_id = "native"

    for writer_name in writers:
        wargs = writer_args[writer_name]
        res = scn.save_datasets(writer=writer_name, compute=False, datasets=datasets, **wargs)
        if res and isinstance(res[0], (tuple, list)):
            # list of (dask-array, file-obj) tuples
            to_save.extend(zip(*res))
        else:
            # list of delayed objects
            to_save.extend(res)
    return to_save


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
            "clavrx",
            "mersi2_l1b",
            "mirs",
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
            "ahi_hrit",
            "ahi_hsd",
        ]
    return readers


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
        type=float,
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
        type=float,
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
    return (group_1,)


def _supported_writers(is_polar2grid: bool = False) -> list[str]:
    if is_polar2grid:
        writers = [
            "geotiff",
            "awips_tiled",
            "binary",
        ]
    else:
        writers = [
            "geotiff",
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
        help="Writers to save datasets with. Multiple writers "
        "can be provided by specifying '-w' multiple "
        "times (ex. '-w geotiff -w awips_tiled'). "
        "Supported writers: " + ", ".join(writers),
    )
    return (group_1,)


def add_resample_argument_groups(parser, is_polar2grid=None):
    if is_polar2grid is None:
        # if we are being loaded from documentation then this won't be
        # specified so we need to load it directly from the environment variable
        is_polar2grid = _get_p2g_defaults_env_var()

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
            default=argparse.SUPPRESS,
            help="Pre-compute geolocation to determine what "
            "chunks of data should be resampled "
            '(--method "ewa"). This can reduce the '
            "overall work required by the algorithm, "
            "but only if a small amount of swath data "
            "lies on the target area.",
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
        "(.conf for P2G-style grids, .yaml for "
        "SatPy-style areas)",
    )
    group_1.add_argument(
        "--ll-bbox",
        nargs=4,
        type=float,
        metavar=("lon_min", "lat_min", "lon_max", "lat_max"),
        help="Crop data to region specified by lon/lat "
        "bounds (lon_min lat_min lon_max lat_max). "
        "Coordinates must be valid in the source data "
        "projection. Can only be used with gridded "
        "input data.",
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


def _parse_reader_args(
    reader_names: list[str],
    reader_subgroups: list,
    args,
) -> tuple[dict, dict]:
    reader_args = {}
    load_args = {}
    for reader_name, (sgrp1, sgrp2) in zip(reader_names, reader_subgroups):
        if sgrp1 is None:
            continue
        rargs = _args_to_dict(args, sgrp1._group_actions)
        reader_args[reader_name] = rargs
        if sgrp2 is not None:
            load_args.update(_args_to_dict(args, sgrp2._group_actions))
    return reader_args, load_args


def _parse_writer_args(
    writer_names: list[str],
    writer_subgroups: list,
    reader_names: list[str],
    is_polar2grid: bool,
    args,
) -> dict:
    writer_args = {}
    for writer_name, (sgrp1, sgrp2) in zip(writer_names, writer_subgroups):
        wargs = _args_to_dict(args, sgrp1._group_actions)
        if sgrp2 is not None:
            wargs.update(_args_to_dict(args, sgrp2._group_actions))
        writer_args[writer_name] = wargs
        # get default output filename
        if "filename" in wargs and wargs["filename"] is None:
            wargs["filename"] = get_default_output_filename(reader_names[0], writer_name, is_polar2grid)
    return writer_args


def _get_scene_init_load_args(args, reader_args, reader_names, reader_subgroups):
    products = reader_args.pop("products") or []
    filenames = reader_args.pop("filenames") or []
    filenames = list(get_input_files(filenames))

    reader_specific_args, reader_specific_load_args = _parse_reader_args(reader_names, reader_subgroups, args)
    # argparse will combine "extended" arguments like `products` automatically
    # and products should only be provided to the load arguments, not reader creation
    for _reader_name, _reader_args in reader_specific_args.items():
        _reader_args.pop("products", None)

    # Parse provided files and search for files if provided directories
    scene_creation = {
        "filenames": filenames,
        "reader": reader_names[0],
        "reader_kwargs": reader_specific_args.get(reader_names[0], {}),
    }
    load_args = {
        "products": products,
    }
    load_args.update(reader_specific_load_args)
    return scene_creation, load_args


def _print_list_products(reader_info, p2g_only=True):
    available_satpy_names, available_p2g_names = reader_info.get_available_products()
    available_satpy_names = ["*" + _sname for _sname in available_satpy_names]
    if available_satpy_names and not p2g_only:
        print("### Custom/Satpy Products")
        print("\n".join(available_satpy_names) + "\n")
    if not p2g_only:
        print("### Standard Available Polar2Grid Products")
    if not available_p2g_names:
        print("<None>")
    else:
        print("\n".join(sorted(available_p2g_names)))


def add_extra_config_paths(extra_paths: list[str]):
    config_path = satpy.config.get("config_path")
    LOG.info(f"Adding additional configuration paths: {extra_paths}")
    satpy.config.set(config_path=extra_paths + config_path)


def _get_p2g_defaults_env_var():
    return bool(int(os.environ.setdefault("USE_POLAR2GRID_DEFAULTS", "1")))


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
        help="show processing progress bar (not recommended for logged output)",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=os.getenv("DASK_NUM_WORKERS", 4),
        help="specify number of worker threads to use (default: 4)",
    )
    parser.add_argument(
        "--extra-config-path",
        action="append",
        help="Specify the base directory of additional Satpy configuration "
        "files. For example, to use custom enhancement YAML file named "
        "'generic.yaml' place it in a directory called 'enhancements' "
        "like '/path/to/my_configs/enhancements/generic.yaml' and then "
        "set this flag to '/path/to/my_configs'.",
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
    reader_group = add_scene_argument_groups(parser, is_polar2grid=use_polar2grid_defaults)[0]
    resampling_group = add_resample_argument_groups(parser, is_polar2grid=use_polar2grid_defaults)[0]
    writer_group = add_writer_argument_groups(parser)[0]
    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]

    _retitle_optional_arguments(parser)
    args, _ = parser.parse_known_args(argv_without_help)
    return parser, args, reader_group, resampling_group, writer_group


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


def _prepare_initial_logging(args, glue_name):
    global LOG
    LOG = logging.getLogger(glue_name)

    # Prepare logging
    rename_log = False
    if args.log_fn is None:
        rename_log = True
        args.log_fn = glue_name + "_fail.log"
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    logging.getLogger("rasterio").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("fsspec").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("s3fs").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("aiobotocore").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("botocore").setLevel(levels[min(2, args.verbosity)])
    sys.excepthook = create_exc_handler(LOG.name)
    if levels[min(3, args.verbosity)] > logging.DEBUG:
        import warnings

        warnings.filterwarnings("ignore")
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))
    if args.extra_config_path:
        add_extra_config_paths(args.extra_config_path)
    LOG.debug(f"Satpy config path is: {satpy.config.get('config_path')}")
    return rename_log, glue_name


def _create_scene(scene_creation: dict) -> Optional[Scene]:
    try:
        scn = Scene(**scene_creation)
    except ValueError as e:
        LOG.error("{} | Enable debug message (-vvv) or see log file for details.".format(str(e)))
        LOG.debug("Further error information: ", exc_info=True)
        return
    except OSError:
        LOG.error("Could not open files. Enable debug message (-vvv) or see log file for details.")
        LOG.debug("Further error information: ", exc_info=True)
        return
    return scn


def _resample_scene_to_grids(
    scn: Scene,
    reader_names: list[str],
    resample_args: dict,
    filter_kwargs: dict,
    preserve_resolution: bool,
    use_polar2grid_defaults: bool,
) -> list[tuple]:
    ll_bbox = resample_args.pop("ll_bbox")
    if ll_bbox:
        scn = scn.crop(ll_bbox=ll_bbox)

    scn = filter_scene(
        scn,
        reader_names,
        **filter_kwargs,
    )
    if scn is None:
        LOG.info("No remaining products after filtering.")
        return []

    areas_to_resample = resample_args.pop("grids")
    if "ewa_persist" in resample_args:
        resample_args["persist"] = resample_args.pop("ewa_persist")
    scenes_to_save = resample_scene(
        scn,
        areas_to_resample,
        preserve_resolution=preserve_resolution,
        is_polar2grid=use_polar2grid_defaults,
        **resample_args,
    )
    return scenes_to_save


def _save_scenes(scenes_to_save: list[tuple], reader_info, writer_args) -> list:
    to_save = []
    for scene_to_save, products_to_save in scenes_to_save:
        overwrite_platform_name_with_aliases(scene_to_save)
        reader_info.apply_p2g_name_to_scene(scene_to_save)
        to_save = write_scene(
            scene_to_save,
            writer_args["writers"],
            writer_args,
            products_to_save,
            to_save=to_save,
        )
    return to_save


def _parse_glue_args(argv: list[str], use_polar2grid_defaults: bool):
    parser, args, reader_group, resampling_group, writer_group = _main_args(argv, use_polar2grid_defaults)
    # env used by some writers for default number of threads (ex. geotiff)
    # must be done before writer args are parsed
    os.environ["DASK_NUM_WORKERS"] = str(args.num_workers)

    reader_subgroups = _add_component_parser_args(parser, "readers", args.readers or [])
    writer_subgroups = _add_component_parser_args(parser, "writers", args.writers or [])
    args = parser.parse_args(argv)
    _validate_reader_writer_args(parser, args, use_polar2grid_defaults)

    reader_args = _args_to_dict(args, reader_group._group_actions)
    reader_names = reader_args.pop("readers")
    scene_creation, load_args = _get_scene_init_load_args(args, reader_args, reader_names, reader_subgroups)
    resample_args = _args_to_dict(args, resampling_group._group_actions)
    writer_args = _args_to_dict(args, writer_group._group_actions)
    writer_specific_args = _parse_writer_args(
        writer_args["writers"], writer_subgroups, reader_names, use_polar2grid_defaults, args
    )
    writer_args.update(writer_specific_args)

    if not args.filenames:
        parser.print_usage()
        parser.exit(1, "\nERROR: No data files provided (-f flag)\n")
    return args, reader_args, reader_names, scene_creation, load_args, resample_args, writer_args


def _get_glue_name(args):
    reader_name = "NONE" if args.readers is None else args.readers[0]
    writer_names = "-".join(args.writers or [])
    return f"{reader_name}_{writer_names}"


def main(argv=sys.argv[1:]):
    add_polar2grid_config_paths()
    USE_POLAR2GRID_DEFAULTS = _get_p2g_defaults_env_var()
    args, reader_args, reader_names, scene_creation, load_args, resample_args, writer_args = _parse_glue_args(
        argv, USE_POLAR2GRID_DEFAULTS
    )
    glue_name = _get_glue_name(args)
    rename_log = _prepare_initial_logging(args, glue_name)
    # Set up dask and the number of workers
    if args.num_workers:
        dask.config.set(num_workers=args.num_workers)

    # Create a Scene, analyze the provided files
    LOG.info("Sorting and reading input files...")
    scn = _create_scene(scene_creation)
    if scn is None:
        return -1

    # Rename the log file
    if rename_log:
        stime = getattr(scn, "start_time", scn.attrs.get("start_time"))
        rename_log_file(glue_name + stime.strftime("_%Y%m%d_%H%M%S.log"))

    # Load the actual data arrays and metadata (lazy loaded as dask arrays)
    LOG.info("Loading product metadata from files...")
    reader_info = ReaderProxyBase.from_reader_name(scene_creation["reader"], scn, load_args["products"])
    if args.list_products or args.list_products_all:
        _print_list_products(reader_info, p2g_only=not args.list_products_all)
        return 0

    load_args["products"] = reader_info.get_satpy_products_to_load()
    if not load_args["products"]:
        return -1
    products = load_args.pop("products")
    scn.load(products, **load_args)

    filter_kwargs = {
        "sza_threshold": reader_args["sza_threshold"],
        "day_fraction": reader_args["filter_day_products"],
        "night_fraction": reader_args["filter_night_products"],
    }
    scenes_to_save = _resample_scene_to_grids(
        scn, reader_names, resample_args, filter_kwargs, args.preserve_resolution, USE_POLAR2GRID_DEFAULTS
    )
    to_save = _save_scenes(scenes_to_save, reader_info, writer_args)

    if args.progress:
        pbar = ProgressBar()
        pbar.register()

    LOG.info("Computing products and saving data to writers...")
    if not to_save:
        LOG.warning(
            "No product files produced given available valid data and "
            "resampling settings. This can happen if the writer "
            "detects that no valid output will be written or the "
            "input data does not overlap with the target grid."
        )
    compute_writer_results(to_save)
    LOG.info("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
