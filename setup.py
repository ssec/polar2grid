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
"""Script for installing the polar2grid package. See the documentation site for more information:

http://www.ssec.wisc.edu/software/polar2grid/

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Nov 2014
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"
import os
from setuptools import setup, find_packages, Command
from distutils.extension import Extension
import numpy

extensions = [
    Extension("polar2grid.remap._ll2cr", sources=["polar2grid/remap/_ll2cr.pyx"], extra_compile_args=["-O3", "-Wno-unused-function"]),
    Extension("polar2grid.remap._fornav", sources=["polar2grid/remap/_fornav.pyx", "polar2grid/remap/_fornav_templates.cpp"], language="c++", extra_compile_args=["-O3", "-Wno-unused-function"])
]

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

if not os.getenv("USE_CYTHON", False) or cythonize is None:
    print("Cython will not be used. Use environment variable 'USE_CYTHON=True' to use it")
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

version = '2.3.0a3'


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


def readme():
    with open("README.rst", "r") as f:
        return f.read()


classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: POSIX :: Linux",  # Not sure if it works on Windows, since we don't normally support it, needs testing
    "Operating System :: MacOS :: MacOS X",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
    "Topic :: Scientific/Engineering :: GIS",
]

extras_require = {
    # Backends:
    "awips": ["netCDF4"],
    "gtiff": ["gdal"],
    "ninjo": [],
    "hdf5": ["h5py"],
    # Other:
    "remap": ["pyproj>=2.0", "scipy"],
    "utils": ["matplotlib"],
    "docs": ["sphinx", "rst2pdf"],
    "coastlines": ["pycoast", "pydecorate"],
    # Frontends (included separately):
    "viirs_sdr": ['h5py'],
    'modis_l1b': ['pyhdf'],
    'mirs': ['netCDF4'],
    "drrtv": ['h5py'],
    'acspo': ['netCDF4'],
}
extras_require["all"] = list(set([x for y in extras_require.values() for x in y]))

entry_points = {
    'console_scripts': [],
    'polar2grid.backend_class': [
        'gtiff=polar2grid.gtiff_backend:Backend',
        'awips=polar2grid.awips.awips_netcdf:Backend',
        'binary=polar2grid.binary:Backend',
        'ninjo=polar2grid.ninjo:Backend',
        'hdf5=polar2grid.hdf5_backend:Backend',
        'scmi=polar2grid.awips.scmi_backend:Backend',
        ],
    'polar2grid.backend_arguments': [
        'gtiff=polar2grid.gtiff_backend:add_backend_argument_groups',
        'awips=polar2grid.awips.awips_netcdf:add_backend_argument_groups',
        'binary=polar2grid.binary:add_backend_argument_groups',
        'ninjo=polar2grid.ninjo:add_backend_argument_groups',
        'hdf5=polar2grid.hdf5_backend:add_backend_argument_groups',
        'scmi=polar2grid.awips.scmi_backend:add_backend_argument_groups',
        ],
    'polar2grid.compositor_class': [
        'rgb=polar2grid.compositors.rgb:RGBCompositor',
        'true_color=polar2grid.compositors.rgb:TrueColorCompositor',
        'false_color=polar2grid.compositors.rgb:FalseColorCompositor',
        'crefl_sharpen=polar2grid.compositors.rgb:CreflRGBSharpenCompositor',
        'crefl_sharpen_awips=polar2grid.compositors.rgb:CreflRGBSharpenCompositor',
        ],
    'polar2grid.frontend_class': [
        'viirs_edr_flood=polar2grid.readers.viirs_edr_flood:Frontend',
        'viirs_edr_active_fires=polar2grid.readers.viirs_edr_active_fires:Frontend',
        'mersi2_l1b=polar2grid.readers.mersi2_l1b:Frontend',
        'virr_l1b=polar2grid.readers.virr_l1b:Frontend',
        'viirs_l1b=polar2grid.readers.viirs_l1b:Frontend',
        'nucaps=polar2grid.readers.nucaps:Frontend',
        'amsr2_l1b=polar2grid.readers.amsr2_l1b:Frontend',
        'acspo=polar2grid.readers.acspo:Frontend',
        'viirs=polar2grid.viirs:Frontend',
        'viirs_sdr=polar2grid.viirs:Frontend',
        'viirsedr=polar2grid.viirs:EDRFrontend',
        'modis=polar2grid.modis:Frontend',
        'mirs=polar2grid.mirs:Frontend',
        'drrtv=polar2grid.drrtv:Frontend',
        'avhrr=polar2grid.avhrr:Frontend',
        'crefl=polar2grid.crefl:Frontend',
        'clavrx=polar2grid.readers.clavrx:Frontend',
        ],
    'polar2grid.frontend_arguments': [
        'viirs_edr_flood=polar2grid.readers.viirs_edr_flood:add_frontend_argument_groups',
        'viirs_edr_active_fires=polar2grid.readers.viirs_edr_active_fires:add_frontend_argument_groups',
        'mersi2_l1b=polar2grid.readers.mersi2_l1b:add_frontend_argument_groups',
        'virr_l1b=polar2grid.readers.virr_l1b:add_frontend_argument_groups',
        'viirs_l1b=polar2grid.readers.viirs_l1b:add_frontend_argument_groups',
        'nucaps=polar2grid.readers.nucaps:add_frontend_argument_groups',
        'amsr2_l1b=polar2grid.readers.amsr2_l1b:add_frontend_argument_groups',
        'acspo=polar2grid.readers.acspo:add_frontend_argument_groups',
        'viirs=polar2grid.viirs:add_frontend_argument_groups',
        'viirs_sdr=polar2grid.viirs:add_frontend_argument_groups',
        'viirsedr=polar2grid.viirs:add_frontend_argument_groups_edr',
        'modis=polar2grid.modis:add_frontend_argument_groups',
        'mirs=polar2grid.mirs:add_frontend_argument_groups',
        'drrtv=polar2grid.drrtv:add_frontend_argument_groups',
        'avhrr=polar2grid.avhrr:add_frontend_argument_groups',
        'crefl=polar2grid.crefl:add_frontend_argument_groups',
        'clavrx=polar2grid.readers.clavrx:add_frontend_argument_groups',
        ],
    }

setup(
    name='polar2grid',
    version=version,
    author='David Hoese, SSEC',
    author_email='david.hoese@ssec.wisc.edu',
    license='GPLv3',
    description="Library and scripts to remap satellite data to a grid",
    long_description=readme(),
    classifiers=classifiers,
    keywords='',
    url="http://www.ssec.wisc.edu/software/polar2grid/",
    download_url="http://larch.ssec.wisc.edu/simple/polar2grid",
    ext_modules=cythonize(extensions),
    include_dirs=[numpy.get_include()],
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    package_data={'polar2grid': ["compositors/*.ini", "awips/*.ini", "awips/*.yaml",
                                 "grids/*.conf", "ninjo/*.ini", "core/rescale_configs/*.ini"]},
    zip_safe=True,
    tests_require=['py.test'],
    cmdclass={'test': PyTest},
    install_requires=[
        'setuptools',       # reading configuration files
        'numpy',
        ],
    python_requires='>=3.6',
    extras_require=extras_require,
    entry_points=entry_points
)

