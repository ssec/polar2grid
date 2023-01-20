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
"""Basic usability tests for the main glue script."""

import contextlib
import os
from glob import glob
from tempfile import gettempdir
from unittest import mock

import dask
import pytest
import yaml
from pytest_lazyfixture import lazy_fixture
from satpy.tests.utils import CustomScheduler

from polar2grid.utils.config import get_polar2grid_etc


@contextlib.contextmanager
def set_env(**environ):
    """Temporarily set the process environment variables.

    Args:
        environ (dict[str, unicode]): New environment variables to set.

    """
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


VIIRS_SDR_FILENAMES = [
    "GDNBO_npp_d20120225_t1801245_e1802487_b01708_c20120226001636568470_noaa_ops.h5",
    "GITCO_npp_d20120225_t1801245_e1802487_b01708_c20120226001734123892_noaa_ops.h5",
    "GMTCO_npp_d20120225_t1801245_e1802487_b01708_c20120226001559910679_noaa_ops.h5",
    "SVDNB_npp_d20120225_t1801245_e1802487_b01708_c20120226002239040837_noaa_ops.h5",
    "SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5",
    "SVI02_npp_d20120225_t1801245_e1802487_b01708_c20120226002313514280_noaa_ops.h5",
    "SVI03_npp_d20120225_t1801245_e1802487_b01708_c20120226002348811096_noaa_ops.h5",
    "SVI04_npp_d20120225_t1801245_e1802487_b01708_c20120226002313755405_noaa_ops.h5",
    "SVI05_npp_d20120225_t1801245_e1802487_b01708_c20120226002349115396_noaa_ops.h5",
    "SVM01_npp_d20120225_t1801245_e1802487_b01708_c20120226002049115233_noaa_ops.h5",
    "SVM02_npp_d20120225_t1801245_e1802487_b01708_c20120226002132385368_noaa_ops.h5",
    "SVM03_npp_d20120225_t1801245_e1802487_b01708_c20120226002053795183_noaa_ops.h5",
    "SVM04_npp_d20120225_t1801245_e1802487_b01708_c20120226002204554472_noaa_ops.h5",
    "SVM05_npp_d20120225_t1801245_e1802487_b01708_c20120226002048565595_noaa_ops.h5",
    "SVM06_npp_d20120225_t1801245_e1802487_b01708_c20120226002138321916_noaa_ops.h5",
    "SVM07_npp_d20120225_t1801245_e1802487_b01708_c20120226002208157737_noaa_ops.h5",
    "SVM08_npp_d20120225_t1801245_e1802487_b01708_c20120226002205860744_noaa_ops.h5",
    "SVM09_npp_d20120225_t1801245_e1802487_b01708_c20120226002205633207_noaa_ops.h5",
    "SVM10_npp_d20120225_t1801245_e1802487_b01708_c20120226002316653329_noaa_ops.h5",
    "SVM11_npp_d20120225_t1801245_e1802487_b01708_c20120226002207165715_noaa_ops.h5",
    "SVM12_npp_d20120225_t1801245_e1802487_b01708_c20120226002134281104_noaa_ops.h5",
    "SVM13_npp_d20120225_t1801245_e1802487_b01708_c20120226002316702845_noaa_ops.h5",
    "SVM14_npp_d20120225_t1801245_e1802487_b01708_c20120226002317383363_noaa_ops.h5",
    "SVM15_npp_d20120225_t1801245_e1802487_b01708_c20120226002348350715_noaa_ops.h5",
    "SVM16_npp_d20120225_t1801245_e1802487_b01708_c20120226002204855751_noaa_ops.h5",
]


@pytest.fixture(scope="session")
def extra_viirs_composite_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("extra_viirs_composite_path")
    _create_fake_comp(tmp_path)
    _create_fake_comp_enh(tmp_path)
    yield [tmp_path]


def _create_fake_comp(tmp_path):
    from satpy.composites import GenericCompositor

    comps_dict = {
        "composites": {
            "myfakecomp": {
                "compositor": GenericCompositor,
                "prerequisites": [
                    {"name": "I01"},
                    {"name": "I01"},
                    {"name": "I01"},
                ],
                "standard_name": "myfakecomp",
            },
        },
    }

    comp_path = tmp_path / "composites"
    comp_path.mkdir(parents=True)
    viirs_comp_path = comp_path / "viirs.yaml"
    with open(viirs_comp_path, "w") as comp_file:
        yaml.dump(comps_dict, comp_file)


def _create_fake_comp_enh(tmp_path):
    from satpy.enhancements import stretch

    enh_dict = {
        "enhancements": {
            "myfakecomp_default": {
                "standard_name": "myfakecomp",
                "operations": [
                    {
                        "name": "myfakecomp_stretch",
                        "method": stretch,
                        "kwargs": {"stretch": "crude", "min_stretch": 0, "max_stretch": 1},
                    },
                ],
            },
        },
    }

    enh_path = tmp_path / "enhancements"
    enh_path.mkdir(parents=True)
    viirs_enh_file = enh_path / "viirs.yaml"
    with open(viirs_enh_file, "w") as comp_file:
        yaml.dump(enh_dict, comp_file)


@pytest.fixture(scope="session")
def extra_viirs_enhancement_file(tmp_path_factory):
    import yaml
    from satpy.enhancements import stretch

    tmp_path = tmp_path_factory.mktemp("extra_viirs_enhancement_file")

    enh_dict = {
        "enhancements": {
            "myfakeenh_i01": {
                "name": "I01",
                "operations": [
                    {
                        "name": "myfakeenh_i01_stretch",
                        "method": stretch,
                        "kwargs": {"stretch": "crude", "min_stretch": 0, "max_stretch": 1},
                    },
                ],
            },
            "myfakecomp_new_default": {
                "name": "myfakecomp",
                "standard_name": "myfakecomp",
                "operations": [
                    {
                        "name": "myfakecomp_new_stretch",
                        "method": stretch,
                        "kwargs": {"stretch": "crude", "min_stretch": 0, "max_stretch": 1},
                    },
                ],
            },
        },
    }

    enh_path = tmp_path / "enhancements"
    enh_path.mkdir(parents=True)
    viirs_enh_file = enh_path / "blahblahblah.yaml"
    with open(viirs_enh_file, "w") as comp_file:
        yaml.dump(enh_dict, comp_file)
    yield [viirs_enh_file]


@pytest.fixture(scope="session")
def extra_viirs_comp_and_enh(extra_viirs_composite_path, extra_viirs_enhancement_file):
    yield extra_viirs_composite_path + extra_viirs_enhancement_file


@contextlib.contextmanager
def prepare_glue_exec(create_scene_func, max_computes=0, use_polar2grid=True):
    use_str = "1" if use_polar2grid else "0"
    with set_env(USE_POLAR2GRID_DEFAULTS=use_str), mock.patch(
        "polar2grid.glue._create_scene"
    ) as create_scene, dask.config.set(scheduler=CustomScheduler(max_computes)):
        create_scene.return_value = create_scene_func
        yield


def _create_empty_viirs_sdrs(dst_dir):
    import h5py

    for viirs_fn in VIIRS_SDR_FILENAMES:
        viirs_path = dst_dir / viirs_fn
        h5py.File(viirs_path, "w")


def test_polar2grid_help():
    from polar2grid.glue import main

    with pytest.raises(SystemExit) as e, set_env(USE_POLAR2GRID_DEFAULTS="1"):
        main(["--help"])
    assert e.value.code == 0


def test_geo2grid_help():
    from polar2grid.glue import main

    with pytest.raises(SystemExit) as e, set_env(USE_POLAR2GRID_DEFAULTS="0"):
        main(["--help"])
    assert e.value.code == 0


class TestGlueWithVIIRS:
    def setup_method(self):
        """Wrap HDF5 file handler with our own fake handler."""
        from satpy._config import config_search_paths
        from satpy.readers.viirs_sdr import VIIRSSDRFileHandler
        from satpy.tests.reader_tests.test_viirs_sdr import FakeHDF5FileHandler2

        self.reader_configs = config_search_paths(os.path.join("readers", "viirs_sdr.yaml"))
        # http://stackoverflow.com/questions/12219967/how-to-mock-a-base-class-with-python-mock-library
        self.p = mock.patch.object(VIIRSSDRFileHandler, "__bases__", (FakeHDF5FileHandler2,))
        self.fake_handler = self.p.start()
        self.p.is_local = True

    def teardown_method(self):
        """Stop wrapping the HDF5 file handler."""
        self.p.stop()

    def test_polar2grid_viirs_sdr_list_products(self, tmp_path):
        from polar2grid.glue import main

        _create_empty_viirs_sdrs(tmp_path)
        with set_env(USE_POLAR2GRID_DEFAULTS="1"):
            ret = main(["-r", "viirs_sdr", "-w", "geotiff", "-f", str(tmp_path), "--list-products"])
        assert ret == 0


class TestGlueFakeScene:
    @pytest.mark.parametrize(
        ("scene_fixture", "product_names", "num_outputs", "max_computes"),
        [
            (lazy_fixture("abi_l1b_c01_scene"), ["C01"], 1, 1),
            (lazy_fixture("abi_l1b_airmass_scene"), ["airmass"], 1, 1),
        ],
    )
    def test_abi_scene(self, scene_fixture, product_names, num_outputs, max_computes, chtmpdir):
        from polar2grid.glue import main

        with prepare_glue_exec(scene_fixture, max_computes=max_computes, use_polar2grid=False):
            ret = main(["-r", "abi_l1b", "-w", "geotiff", "-f", str(chtmpdir), "-p"] + product_names)
        output_files = glob(str(chtmpdir / "*.tif"))
        assert len(output_files) == num_outputs
        assert ret == 0

    @pytest.mark.parametrize(
        ("scene_fixture", "product_names", "num_outputs", "extra_flags", "max_computes"),
        [
            # lon/lat persist -> day/night check (I band) -> dynamic grid -> final compute
            (lazy_fixture("viirs_sdr_i01_scene"), [], 1, [], 4),
            # lon/lat persist -> day/night check (I band) -> dynamic grid -> final compute
            (lazy_fixture("viirs_sdr_i01_scene"), [], 1, ["--dnb-saturation-correction"], 4),
            # lon/lat persist -> day/night check (x2 = I band + M band) -> dynamic grid -> final compute
            (lazy_fixture("viirs_sdr_full_scene"), [], 5 + 16 + 3 + 1 + 1 + 1, ["--dnb-saturation-correction"], 5),
            # lon/lat persist -> day/night check (x2 = I band + M band) -> dynamic grid -> final compute
            (
                lazy_fixture("viirs_sdr_full_scene"),
                [],
                5,
                ["-g", "lcc_conus_1km", "--awips-true-color", "--awips-false-color"],
                5,
            ),
            # lon/lat persist -> day/night check (I band) -> final compute
            (lazy_fixture("viirs_sdr_i01_scene"), [], 1, ["--method", "native", "-g", "MAX"], 3),
        ],
    )
    def test_viirs_sdr_scene(self, scene_fixture, product_names, num_outputs, extra_flags, max_computes, chtmpdir):
        from polar2grid.glue import main

        with prepare_glue_exec(scene_fixture, max_computes=max_computes):
            args = ["-r", "viirs_sdr", "-w", "geotiff", "-vvv", "-f", str(chtmpdir)]
            if product_names:
                args.append("-p")
                args.extend(product_names)
            if extra_flags:
                args.extend(extra_flags)
            ret = main(args)
        output_files = glob(str(chtmpdir / "*.tif"))
        assert len(output_files) == num_outputs
        assert ret == 0

    @pytest.mark.parametrize(
        ("extra_config_path", "exp_comps", "exp_enh_names"),
        [
            (lazy_fixture("extra_viirs_composite_path"), ["myfakecomp"], ["myfakecomp_stretch", "gamma"]),
            (lazy_fixture("extra_viirs_enhancement_file"), [], ["myfakeenh_i01_stretch"]),
            (
                lazy_fixture("extra_viirs_comp_and_enh"),
                ["myfakecomp"],
                ["myfakeenh_i01_stretch", "myfakecomp_new_stretch"],
            ),
        ],
    )
    def test_extra_config_path(
        self, extra_config_path, exp_comps, exp_enh_names, viirs_sdr_full_scene, chtmpdir, capsys
    ):
        from polar2grid.glue import main

        args = ["-r", "viirs_sdr", "-w", "geotiff", "-vvv", "-f", str(chtmpdir)]
        for extra_path in extra_config_path:
            args += ["--extra-config-path", str(extra_path)]
        with prepare_glue_exec(viirs_sdr_full_scene):
            ret = main(args + ["--list-products-all"])
        assert ret == 0
        captured = capsys.readouterr()
        for exp_comp in exp_comps:
            assert exp_comp in captured.out

        with prepare_glue_exec(viirs_sdr_full_scene, max_computes=4):
            ret = main(args + ["-p"] + exp_comps + ["i01"])
        assert ret == 0
        captured = capsys.readouterr()
        for exp_enh_name in exp_enh_names:
            assert exp_enh_name in captured.err

        # ensure p2g builtins are processed/added before user custom configs
        p2g_etc = get_polar2grid_etc()
        builtin_path_idx = captured.err.index(f"Adding enhancement configuration from file: {p2g_etc}")  # the first one
        for extra_cpath in extra_config_path:
            if str(extra_cpath).endswith(".yaml"):
                # the YAML was copied to a temp directory, check for that
                extra_cpath = gettempdir()
            path_idx = captured.err.index(f"Adding enhancement configuration from file: {str(extra_cpath)}")
            assert builtin_path_idx < path_idx
