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
from unittest import mock

import pytest
from pytest_lazyfixture import lazy_fixture


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
        ("scene_fixture", "product_names", "num_outputs"),
        [
            (lazy_fixture("abi_l1b_c01_scene"), ["C01"], 1),
            (lazy_fixture("abi_l1b_airmass_scene"), ["airmass"], 1),
        ],
    )
    def test_abi_scene(self, scene_fixture, product_names, num_outputs, chtmpdir):
        from polar2grid.glue import main

        with set_env(USE_POLAR2GRID_DEFAULTS="0"), mock.patch("polar2grid.glue._create_scene") as create_scene:
            create_scene.return_value = scene_fixture
            ret = main(["-r", "abi_l1b", "-w", "geotiff", "-f", str(chtmpdir), "-p"] + product_names)
        output_files = glob(str(chtmpdir / "*.tif"))
        assert len(output_files) == num_outputs
        assert ret == 0

    @pytest.mark.parametrize(
        ("scene_fixture", "product_names", "num_outputs", "extra_flags"),
        [
            (lazy_fixture("viirs_sdr_i01_scene"), [], 1, []),
            (lazy_fixture("viirs_sdr_i01_scene"), [], 1, ["--dnb-saturation-correction"]),
            (lazy_fixture("viirs_sdr_full_scene"), [], 5 + 16 + 3 + 1 + 1 + 1, ["--dnb-saturation-correction"]),
        ],
    )
    def test_viirs_sdr_scene(self, scene_fixture, product_names, num_outputs, extra_flags, chtmpdir):
        from polar2grid.glue import main

        with set_env(USE_POLAR2GRID_DEFAULTS="1"), mock.patch("polar2grid.glue._create_scene") as create_scene:
            create_scene.return_value = scene_fixture
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
