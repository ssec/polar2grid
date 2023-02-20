#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    November 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Script for installing the polar2grid package.

See the documentation site for more information:

http://www.ssec.wisc.edu/software/polar2grid/

"""
from glob import glob

from setuptools import find_packages, setup

version = "3.0.1"


def readme():
    with open("README.rst", "r") as f:
        return f.read()


classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS :: MacOS X",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
    "Topic :: Scientific/Engineering :: GIS",
]

extras_require = {
    # Other:
    "utils": ["matplotlib"],
    "docs": ["sphinx", "rst2pdf", "sphinx-argparse", "sphinxcontrib-apidoc", "pytest"],
    "tests": ["pytest"],
    "coastlines": ["pycoast", "pydecorate"],
}
extras_require["all"] = list(set([x for y in extras_require.values() for x in y]))

entry_points = {
    "console_scripts": [
        "polar2grid=polar2grid.__main__:p2g_main",
        "geo2grid=polar2grid.__main__:g2g_main",
    ],
}

setup(
    name="polar2grid",
    version=version,
    author="David Hoese, SSEC",
    author_email="david.hoese@ssec.wisc.edu",
    license="GPLv3",
    description="Library and scripts to remap satellite data to a grid",
    long_description=readme(),
    classifiers=classifiers,
    keywords="",
    url="https://www.ssec.wisc.edu/software/polar2grid/",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "polar2grid": [
            "grids/*.conf",
        ]
    },
    # The location of where these are installed are important for the swbundle and glue scripts!
    # Look at env.sh, glue.py, and glue_legacy.py for where these are pointed to.
    data_files=[
        ("etc/polar2grid/colormaps", glob("etc/colormaps/*")),
        ("etc/polar2grid/composites", glob("etc/composites/*")),
        ("etc/polar2grid/enhancements", glob("etc/enhancements/*")),
        ("etc/polar2grid/readers", glob("etc/readers/*")),
        ("etc/polar2grid/writers", glob("etc/writers/*")),
        ("etc/polar2grid", ["etc/pyspectral.yaml"]),
        ("etc/polar2grid", ["etc/resampling.yaml"]),
    ],
    zip_safe=True,
    install_requires=[
        "setuptools",  # reading configuration files
        "satpy",
        "rasterio",
        "netCDF4",
        "h5py",
    ],
    python_requires=">=3.9",
    extras_require=extras_require,
    entry_points=entry_points,
    scripts=[file for file in glob("swbundle/*.sh") if file not in ["swbundle/env.sh", "swbundle/polar2grid_env.sh"]],
)
