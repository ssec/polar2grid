#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC),
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
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    January 2015
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Script for installing this polar2grid.acspo package.

See http://www.ssec.wisc.edu/software/polar2grid/ for details.

:author:       David Hoese (davidh)
:author:       Eva Schiffer (evas)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2015 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2015
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"
from setuptools import setup, find_packages


def readme():
    with open("README.rst", "r") as f:
        return f.read()


version = '2.0.0'
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 2 :: Only",  # Working on it, I swear
    "Programming Language :: Python :: Implementation :: CPython",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: POSIX :: Linux",  # Not sure if it works on Windows, since we don't normally support it, needs testing
    "Operating System :: MacOS :: MacOS X",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
    "Topic :: Scientific/Engineering :: GIS",
    ]

setup(
    name='polar2grid.modis',
    version=version,
    author='Eva Schiffer, SSEC',
    author_email='eva.schiffer@ssec.wisc.edu',
    description="Library and scripts to aggregate MODIS data and get associated metadata",
    long_description=readme(),
    classifiers=classifiers,
    keywords='',
    license='GPLv3',
    url='http://www.ssec.wisc.edu/software/polar2grid/',
    download_url="http://larch.ssec.wisc.edu/simple/polar2grid",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=["polar2grid"],
    include_package_data=True,
    zip_safe=True,
    install_requires=['numpy', 'pyhdf', 'polar2grid.core', 'python_geotiepoints'],
    entry_points={
        'console_scripts': [],
        'polar2grid.frontend_class': ['modis=polar2grid.modis:Frontend'],
        'polar2grid.frontend_arguments': ['modis=polar2grid.modis:add_frontend_argument_groups'],
    }
)
