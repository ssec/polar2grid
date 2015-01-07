#!/usr/bin/env python
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

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"
import os
from setuptools import setup, find_packages
from distutils.extension import Extension
import numpy

extensions = [
    Extension("polar2grid.remap._ll2cr", sources=["polar2grid/remap/_ll2cr.pyx"], extra_compile_args=["-Wno-unused-function"]),
    Extension("polar2grid.remap._fornav", sources=["polar2grid/remap/_fornav.pyx", "polar2grid/remap/_fornav_templates.cpp"], extra_compile_args=["-Wno-unused-function"], language="c++")
]

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

if os.getenv("NO_CYTHONIZE", False) or cythonize is None:
    def cythonize(extensions, **_ignore):
        """Fake function to compile from C/C++ files instead of compiling .pyx files with cython.
        """
        for extension in extensions:
            sources = []
            for sfile in extension.sources:
                path, ext = os.path.splitext(sfile)
                if ext in ('.pyx', '.py'):
                    if extension.language == 'c++':
                        ext = '.cpp'
                    else:
                        ext = '.c'
                    sfile = path + ext
                sources.append(sfile)
            extension.sources[:] = sources
        return extensions

classifiers = ""
version = '1.2.1'


setup(
    name='polar2grid',
    version=version,
    description="Library and scripts to remap imager data to a grid",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='David Hoese, SSEC',
    author_email='david.hoese@ssec.wisc.edu',
    license='GPLv3',
    url='http://www.ssec.wisc.edu/software/polar2grid/',

    ext_modules=cythonize(extensions),
    include_dirs=[numpy.get_include()],
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),

    namespace_packages=["polar2grid"],
    include_package_data=True,
    package_data={'polar2grid': ["awips/ncml/*.ncml", "awips/*.ini", "grids/*.conf", "ninjo/*.ini"]},
    zip_safe=False,
    install_requires=[
        'numpy',
        'matplotlib',
        'netCDF4',          # AWIPS backend
        'pyproj',           # Python ll2cr, grids
        'gdal',             # Geotiff backend
        'shapely',          # Grid determination
        'pylibtiff',
        'polar2grid.core',
        'polar2grid.viirs',
        'polar2grid.modis'
        ],
    dependency_links=['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi'],
    entry_points={
        'console_scripts': [
            'viirs2awips = polar2grid.viirs2awips:main',
            'modis2awips = polar2grid.modis2awips:main'
        ],
        'polar2grid.backend_class': [
            'gtiff=polar2grid.gtiff_backend:Backend',
            'awips=polar2grid.awips.awips_netcdf:Backend',
            'binary=polar2grid.binary:Backend',
            'ninjo=polar2grid.ninjo:Backend',
            'hdf5=polar2grid.hdf5_backend:Backend',
        ],
        'polar2grid.backend_arguments': [
            'gtiff=polar2grid.gtiff_backend:add_backend_argument_groups',
            'awips=polar2grid.awips.awips_netcdf:add_backend_argument_groups',
            'binary=polar2grid.binary:add_backend_argument_groups',
            'ninjo=polar2grid.ninjo:add_backend_argument_groups',
            'hdf5=polar2grid.hdf5_backend:add_backend_argument_groups',
        ],
        'polar2grid.compositor_class': [
            'rgb=polar2grid.compositors.rgb:RGBCompositor',
            'true_color=polar2grid.compositors.rgb:TrueColorCompositor',
            'false_color=polar2grid.compositors.rgb:FalseColorCompositor',
        ],
        'polar2grid.compositor_arguments': [
            'rgb=polar2grid.compositors.rgb:add_rgb_compositor_argument_groups',
            'true_color=polar2grid.compositors.rgb:add_true_color_compositor_argument_groups',
            'false_color=polar2grid.compositors.rgb:add_false_color_compositor_argument_groups',
        ]
    }
)

