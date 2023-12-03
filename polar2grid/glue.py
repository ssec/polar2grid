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

import contextlib
import logging
import os
import shutil
import sys
import tempfile
from collections.abc import Iterable
from datetime import datetime
from typing import Optional, Union

# isort: off
# hdf5plugin must be imported before h5py and xarray or it won't be available
# Used by the FCI reader
try:
    import hdf5plugin
except ImportError:
    hdf5plugin = None  # type: ignore
# isort: on

import dask
import satpy
from dask.diagnostics import ProgressBar
from pyresample import SwathDefinition
from satpy import DataID, Scene
from satpy.writers import compute_writer_results

from polar2grid._glue_argparser import GlueArgumentParser, get_p2g_defaults_env_var
from polar2grid.core.script_utils import create_exc_handler, rename_log_file, setup_logging
from polar2grid.filters import filter_scene
from polar2grid.readers._base import ReaderProxyBase
from polar2grid.resample import resample_scene
from polar2grid.utils.config import add_polar2grid_config_paths
from polar2grid.utils.dynamic_imports import get_reader_attr
from polar2grid.utils.legacy_compat import get_sensor_alias

LOG = logging.getLogger(__name__)

_PLATFORM_ALIASES = {
    "suominpp": "npp",
    "npp": "npp",
    "snpp": "npp",
    "n20": "noaa20",
    "n21": "noaa21",
    "n22": "noaa22",
    "n23": "noaa23",
    "noaa18": "noaa18",
    "noaa19": "noaa19",
    "noaa20": "noaa20",
    "noaa21": "noaa21",
    "noaa22": "noaa22",
    "noaa23": "noaa23",
    "jpss1": "noaa20",
    "jpss2": "noaa21",
    "jpss3": "noaa22",
    "jpss4": "noaa23",
    "j1": "noaa20",
    "j2": "noaa21",
    "j3": "noaa22",
    "j4": "noaa23",
    "fy3b": "fy3b",
    "fy3c": "fy3c",
    "fy3d": "fy3d",
    "eosaqua": "aqua",
    "eosterra": "terra",
    "aqua": "aqua",
    "terra": "terra",
    "gcomw1": "gcom-w1",
    "metopa": "metopa",
    "metopb": "metopb",
    "metopc": "metopc",
}


def _get_platform_name_alias(satpy_platform_name):
    return _PLATFORM_ALIASES.get(satpy_platform_name.lower().replace("-", ""), satpy_platform_name)


def _overwrite_platform_name_with_aliases(scn):
    """Change 'platform_name' for every DataArray to Polar2Grid expectations."""
    for data_arr in scn:
        if "platform_name" not in data_arr.attrs:
            continue
        pname = _get_platform_name_alias(data_arr.attrs["platform_name"])
        data_arr.attrs["platform_name"] = pname


def _overwrite_sensor_with_aliases(scn):
    """Change 'sensor' for every DataArray to Polar2Grid expectations."""
    for data_arr in scn:
        if "sensor" not in data_arr.attrs:
            continue
        pname = get_sensor_alias(data_arr.attrs["sensor"])
        data_arr.attrs["sensor"] = pname


def _write_scene(
    scn: Scene, writers: list[str], writer_args: dict[str, dict], data_ids: list[DataID], to_save: Optional[list] = None
):
    if to_save is None:
        to_save = []
    if not data_ids:
        # no datasets to save
        return to_save

    _assign_default_native_area_id(scn, data_ids)
    for writer_name in writers:
        wargs = writer_args[writer_name]
        _write_scene_with_writer(scn, writer_name, data_ids, wargs, to_save)
    return to_save


def _assign_default_native_area_id(scn: Scene, data_ids: list[DataID]) -> None:
    for data_id in data_ids:
        area_def = scn[data_id].attrs.get("area")
        if area_def is None or hasattr(area_def, "area_id"):
            continue
        scn[data_id].attrs["area"].area_id = "native"


def _write_scene_with_writer(scn: Scene, writer_name: str, data_ids: list[DataID], wargs: dict, to_save: list) -> None:
    res = scn.save_datasets(writer=writer_name, compute=False, datasets=data_ids, **wargs)
    if res and isinstance(res[0], (tuple, list)):
        # list of (dask-array, file-obj) tuples
        to_save.extend(zip(*res, strict=True))
    else:
        # list of delayed objects
        to_save.extend(res)


def _print_list_products(reader_info, is_polar2grid: bool, p2g_only: bool):
    available_p2g_names, available_custom_names, available_satpy_names = reader_info.get_available_products()
    available_satpy_names = ["*" + _sname for _sname in available_satpy_names]
    available_custom_names = ["*" + _sname for _sname in available_custom_names]
    project_name = "Polar2Grid" if is_polar2grid else "Geo2Grid"

    print("### Custom User Products")
    print("\n".join(sorted(available_custom_names)) if available_custom_names else "<None>")
    print()

    if not p2g_only:
        print("### Non-standard Satpy Products")
        print("\n".join(sorted(available_satpy_names)) if available_satpy_names else "<None>")
        print()

    print(f"### Standard Available {project_name} Products")
    print("\n".join(sorted(available_p2g_names)) if available_p2g_names else "<None>")


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
    antimeridian_mode = resample_args.pop("antimeridian_mode")
    if "ewa_persist" in resample_args:
        resample_args["persist"] = resample_args.pop("ewa_persist")
    scenes_to_save = resample_scene(
        scn,
        areas_to_resample,
        antimeridian_mode=antimeridian_mode,
        preserve_resolution=preserve_resolution,
        is_polar2grid=use_polar2grid_defaults,
        **resample_args,
    )
    return scenes_to_save


def _save_scenes(scenes_to_save: list[tuple], reader_info, writer_args) -> list:
    to_save = []
    for scene_to_save, products_to_save in scenes_to_save:
        _overwrite_platform_name_with_aliases(scene_to_save)
        _overwrite_sensor_with_aliases(scene_to_save)
        reader_info.apply_p2g_name_to_scene(scene_to_save)
        to_save = _write_scene(
            scene_to_save,
            writer_args["writers"],
            writer_args,
            products_to_save,
            to_save=to_save,
        )
    return to_save


def _get_glue_name(args):
    reader_name = "NONE" if args.readers is None else args.readers[0]
    writer_names = "-".join(args.writers or [])
    return f"{reader_name}_{writer_names}"


@contextlib.contextmanager
def _create_profile_html_if(create_profile: Union[False, None, str], project_name: str, glue_name: str):
    from dask.diagnostics import CacheProfiler, Profiler, ResourceProfiler, visualize

    if create_profile is False:
        yield
        return
    if create_profile is None:
        profile_filename = "{project_name}_{glue_name}_{start_time:%Y%m%d_%H%M%S}.html"
    else:
        profile_filename = create_profile

    start_time = datetime.now()
    with CacheProfiler() as cprof, ResourceProfiler() as rprof, Profiler() as prof:
        yield
    end_time = datetime.now()

    profile_filename = profile_filename.format(
        project_name=project_name,
        glue_name=glue_name,
        start_time=start_time,
        end_time=end_time,
    )
    profile_filename = os.path.abspath(profile_filename)
    visualize([prof, rprof, cprof], file_path=profile_filename, show=False)
    print(f"Profile HTML: file://{profile_filename}")


def main(argv=sys.argv[1:]):
    ret = -1
    try:
        processor = _GlueProcessor(argv)
    except FileNotFoundError:
        return ret

    try:
        ret = processor()
    finally:
        processor.cleanup()
    return ret


class _GlueProcessor:
    """Helper class to make calling processing steps easier."""

    def __init__(self, argv):
        add_polar2grid_config_paths()
        self.is_polar2grid = get_p2g_defaults_env_var()
        self.arg_parser = GlueArgumentParser(argv, self.is_polar2grid)
        self.glue_name = _get_glue_name(self.arg_parser._args)
        self.rename_log = _prepare_initial_logging(self.arg_parser, self.glue_name)
        self.tmp_config_paths = []
        self._handle_extra_config_paths(self.arg_parser._args)
        self._clean = False

    def _handle_extra_config_paths(self, args):
        if not args.extra_config_path:
            return
        _check_valid_config_paths(args.extra_config_path)

        new_config_paths = []
        # Preserve user's specified order to handle inheritance/overrides
        for extra_config_path in args.extra_config_path:
            if os.path.isdir(extra_config_path):
                new_config_paths.append(extra_config_path)
                continue

            tmp_config_path = _create_tmp_enhancement_config_dir(extra_config_path)
            new_config_paths.append(tmp_config_path)
            self.tmp_config_paths.append(tmp_config_path)
        _add_extra_config_paths(new_config_paths)
        LOG.debug(f"Satpy config path is: {satpy.config.get('config_path')}")

    def cleanup(self):
        self._clean = True
        for tmp_config_path in self.tmp_config_paths:
            LOG.debug(f"Deleting temporary config directory: {tmp_config_path}")
            shutil.rmtree(tmp_config_path, ignore_errors=True)

    def __call__(self):
        # Set up dask and the number of workers
        common_args = self.arg_parser._args
        if common_args.num_workers:
            dask.config.set(num_workers=common_args.num_workers)

        with _create_profile_html_if(
            common_args.create_profile,
            "polar2grid" if self.is_polar2grid else "geo2grid",
            self.glue_name,
        ):
            return self._run_processing()

    def _run_processing(self):
        LOG.info("Sorting and reading input files...")
        arg_parser = self.arg_parser
        preferred_chunk_size = get_reader_attr(arg_parser._scene_creation["reader"], "PREFERRED_CHUNK_SIZE", 1024)
        _set_preferred_chunk_size(preferred_chunk_size)
        scn = _create_scene(arg_parser._scene_creation)
        if scn is None:
            return -1

        if self.rename_log:
            stime = getattr(scn, "start_time", scn.attrs.get("start_time"))
            rename_log_file(self.glue_name + stime.strftime("_%Y%m%d_%H%M%S.log"))

        # Load the actual data arrays and metadata (lazy loaded as dask arrays)
        LOG.info("Loading product metadata from files...")
        load_args = arg_parser._load_args.copy()
        user_products = load_args.pop("products")
        reader_info = ReaderProxyBase.from_reader_name(arg_parser._scene_creation["reader"], scn, user_products)
        if arg_parser._args.list_products or arg_parser._args.list_products_all:
            _print_list_products(reader_info, self.is_polar2grid, not arg_parser._args.list_products_all)
            return 0

        products = reader_info.get_satpy_products_to_load()
        persist_geolocation = not arg_parser._reader_args.pop("no_persist_geolocation", False)
        if not products:
            return -1
        scn.load(products, **load_args, generate=False)
        if persist_geolocation:
            scn = _persist_swath_definition_in_scene(scn)
        scn.generate_possible_composites(True)

        reader_args = arg_parser._reader_args
        filter_kwargs = {
            "sza_threshold": reader_args["sza_threshold"],
            "day_fraction": reader_args["filter_day_products"],
            "night_fraction": reader_args["filter_night_products"],
        }
        scenes_to_save = _resample_scene_to_grids(
            scn,
            arg_parser._reader_names,
            arg_parser._resample_args,
            filter_kwargs,
            arg_parser._args.preserve_resolution,
            self.is_polar2grid,
        )
        to_save = _save_scenes(scenes_to_save, reader_info, arg_parser._writer_args)

        if arg_parser._args.progress:
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


def _prepare_initial_logging(arg_parser, glue_name: str) -> bool:
    global LOG
    LOG = logging.getLogger(glue_name)

    # Prepare logging
    args = arg_parser._args
    rename_log = False
    if args.log_fn is None:
        rename_log = True
        args.log_fn = glue_name + "_fail.log"
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    logging.getLogger("rasterio").setLevel(levels[min(1, args.verbosity)])
    logging.getLogger("fsspec").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("s3fs").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("aiobotocore").setLevel(levels[min(2, args.verbosity)])
    logging.getLogger("botocore").setLevel(levels[min(2, args.verbosity)])
    sys.excepthook = create_exc_handler(LOG.name)
    if levels[min(3, args.verbosity)] > logging.DEBUG:
        import warnings

        warnings.filterwarnings("ignore")
    LOG.debug("Starting script with arguments: %s", " ".join(arg_parser.argv))
    return rename_log


def _add_extra_config_paths(extra_paths: list[str]):
    config_path = satpy.config.get("config_path")
    LOG.info(f"Adding additional configuration paths: {extra_paths}")
    satpy.config.set(config_path=config_path + extra_paths)


def _check_valid_config_paths(extra_config_paths: Iterable):
    single_file_configs = [config_path for config_path in extra_config_paths if os.path.isfile(config_path)]
    config_paths = [config_path for config_path in extra_config_paths if os.path.isdir(config_path)]
    invalid_paths = set(extra_config_paths) - (set(single_file_configs) | set(config_paths))
    if invalid_paths:
        str_paths = "\n\t".join(sorted(invalid_paths))
        msg = f"Specified extra config paths don't exist:\n\t{str_paths}"
        LOG.error(msg)
        raise FileNotFoundError(msg)


def _create_tmp_enhancement_config_dir(enh_yaml_file: str) -> str:
    config_dir = tempfile.mkdtemp(prefix="p2g_tmp_config")
    enh_dir = os.path.join(config_dir, "enhancements")
    LOG.debug(f"Creating temporary config directory for enhancement file {enh_yaml_file!r}: {enh_dir}")
    os.makedirs(enh_dir)

    new_enh_file = os.path.join(enh_dir, "generic.yaml")
    shutil.copy(enh_yaml_file, new_enh_file)
    return config_dir


def _set_preferred_chunk_size(preferred_chunk_size: int) -> None:
    pcs_in_mb = (preferred_chunk_size * preferred_chunk_size) * 8 // (1024 * 1024)
    if "PYTROLL_CHUNK_SIZE" not in os.environ:
        LOG.debug(f"Setting preferred chunk size to {preferred_chunk_size} pixels or {pcs_in_mb:d}MiB")
        os.environ["PYTROLL_CHUNK_SIZE"] = f"{preferred_chunk_size:d}"
        dask.config.set({"array.chunk-size": f"{pcs_in_mb:d}MiB"})
    else:
        LOG.debug(f"Using environment variable chunk size: {os.environ['PYTROLL_CHUNK_SIZE']}")


def _persist_swath_definition_in_scene(scn: Scene) -> None:
    to_persist_swath_defs = _swaths_to_persist(scn)
    if not to_persist_swath_defs:
        return scn

    to_update_data_arrays, to_persist_lonlats = zip(*to_persist_swath_defs.values(), strict=True)
    LOG.info("Loading swath geolocation into memory...")
    persisted_lonlats = dask.persist(*to_persist_lonlats)
    persisted_swath_defs = [SwathDefinition(plons, plats) for plons, plats in persisted_lonlats]
    new_scn = scn.copy()
    for arrays_to_update, persisted_swath_def in zip(to_update_data_arrays, persisted_swath_defs, strict=True):
        for array_to_update in arrays_to_update:
            array_to_update.attrs["area"] = persisted_swath_def
            new_scn._datasets[array_to_update.attrs["_satpy_id"]] = array_to_update
    LOG.debug(f"{len(to_persist_swath_defs)} unique swath definitions persisted")
    return new_scn


def _swaths_to_persist(scn: Scene) -> dict:
    to_persist_swath_defs = {}
    for data_arr in scn.values():
        swath_def = data_arr.attrs.get("area")
        if not isinstance(swath_def, SwathDefinition):
            continue
        this_swath_data_array_copies, _ = to_persist_swath_defs.setdefault(
            swath_def, ([], (swath_def.lons, swath_def.lats))
        )
        this_swath_data_array_copies.append(data_arr.copy())
    return to_persist_swath_defs


if __name__ == "__main__":
    sys.exit(main())
