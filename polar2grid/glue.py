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
import sys
from datetime import datetime
from typing import Optional, Union

import dask
import satpy
from dask.diagnostics import ProgressBar
from satpy import DataID, Scene
from satpy.writers import compute_writer_results

from polar2grid._glue_argparser import GlueArgumentParser, get_p2g_defaults_env_var
from polar2grid.core.script_utils import (
    create_exc_handler,
    rename_log_file,
    setup_logging,
)
from polar2grid.filters import filter_scene
from polar2grid.readers._base import ReaderProxyBase
from polar2grid.resample import resample_scene
from polar2grid.utils.config import add_polar2grid_config_paths

LOG = logging.getLogger(__name__)

_PLATFORM_ALIASES = {
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
    "metop-a": "metopa",
    "metop-b": "metopb",
}


_SENSOR_ALIASES = {
    "avhrr-3": "avhrr",
}


def _get_platform_name_alias(satpy_platform_name):
    return _PLATFORM_ALIASES.get(satpy_platform_name.lower(), satpy_platform_name)


def _overwrite_platform_name_with_aliases(scn):
    """Change 'platform_name' for every DataArray to Polar2Grid expectations."""
    for data_arr in scn:
        if "platform_name" not in data_arr.attrs:
            continue
        pname = _get_platform_name_alias(data_arr.attrs["platform_name"])
        data_arr.attrs["platform_name"] = pname


def _get_sensor_alias(satpy_sensor):
    if not isinstance(satpy_sensor, set):
        satpy_sensor = {satpy_sensor}
    new_sensor = {_SENSOR_ALIASES.get(sname, sname) for sname in satpy_sensor}
    if len(new_sensor) == 1:
        return new_sensor.pop()
    return new_sensor


def _overwrite_sensor_with_aliases(scn):
    """Change 'sensor' for every DataArray to Polar2Grid expectations."""
    for data_arr in scn:
        if "sensor" not in data_arr.attrs:
            continue
        pname = _get_sensor_alias(data_arr.attrs["sensor"])
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
        to_save.extend(zip(*res))
    else:
        # list of delayed objects
        to_save.extend(res)


def _print_list_products(reader_info, is_polar2grid: bool, p2g_only: bool):
    available_satpy_names, available_p2g_names = reader_info.get_available_products()
    available_satpy_names = ["*" + _sname for _sname in available_satpy_names]
    project_name = "Polar2Grid" if is_polar2grid else "Geo2Grid"
    if available_satpy_names and not p2g_only:
        print("### Custom/Satpy Products")
        print("\n".join(available_satpy_names) + "\n")
    if not p2g_only:
        print(f"### Standard Available {project_name} Products")
    if not available_p2g_names:
        print("<None>")
    else:
        print("\n".join(sorted(available_p2g_names)))


def _add_extra_config_paths(extra_paths: list[str]):
    config_path = satpy.config.get("config_path")
    LOG.info(f"Adding additional configuration paths: {extra_paths}")
    satpy.config.set(config_path=extra_paths + config_path)


def _prepare_initial_logging(args, glue_name: str) -> bool:
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
        _add_extra_config_paths(args.extra_config_path)
    LOG.debug(f"Satpy config path is: {satpy.config.get('config_path')}")
    return rename_log


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
    processor = _GlueProcessor(argv)
    return processor()


class _GlueProcessor:
    """Helper class to make calling processing steps easier."""

    def __init__(self, argv):
        add_polar2grid_config_paths()
        self.is_polar2grid = get_p2g_defaults_env_var()
        self.arg_parser = GlueArgumentParser(argv, self.is_polar2grid)
        self.glue_name = _get_glue_name(self.arg_parser._args)
        self.rename_log = _prepare_initial_logging(self.arg_parser._args, self.glue_name)

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
        if not products:
            return -1
        scn.load(products, **load_args)

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


if __name__ == "__main__":
    sys.exit(main())
