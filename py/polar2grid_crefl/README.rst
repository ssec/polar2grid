Polar2Grid Project
==================

Polar2Grid is a set of tools for extracting swath data from earth-observing satellite instruments,
remapping it to uniform grids, and finally writing that gridded data to a new file format. Polar2Grid uses
a modular design to reduce code duplication. As such, there are multiple python packages that make up all of the
functionality possible.

Polar2Grid is created and distributed by scientists and programmers at the Space Science and Engineering Center (SSEC).
It is available as an all-in-one software bundle by the maintainers of the Community Satellite Processing
Package (CSPP). This is the preferred method of use for scientists and direct broadcast users not needing custom
operations.

Further details about the Polar2Grid project and about the software bundle
can be found on the `documentation site <http://www.ssec.wisc.edu/software/polar2grid/>`_.

Source code can be found on GitHub: https://github.com/davidh-ssec/polar2grid

Polar2Grid CREFL Package
------------------------

The `polar2grid.crefl` package contains objects and tools for reading the output files from VIIRS and MODIS corrected
reflectance (CREFL) processing software. These files are typically HDF4 files. Data files are
typically read via the `Frontend` object (`polar2grid.crefl.Frontend`). The frontend can also be accessed via the
command line by calling `python -m polar2grid.crefl -h`.

CREFL output typically does not contain the geolocation information (Longitude/Latitude) in its output files. For this,
the CREFL frontend requires that the original SDR geolocation be provided. For VIIRS, the frontend can handle both
terrain-corrected and non-terrain-corrected files. The CREFL frontend can also accept the original reflectance SDRs
from either instrument and will run the proper crefl binary to process the files. This assumes that these binaries
are available on the PATH (`crefl` for MODIS, `cviirs` for VIIRS). VIIRS processing also requires the
`h5SDS_transfer_rename` binary. These are automatically provided in the software bundle mentioned above. They can
also be compiled from source available in the git repository in the `/modis_crefl` and `/viirs_crefl` directories.

The CREFL binaries require an ancillary files to base their output on (`tbase.hdf` for MODIS, `CMGDEM.hdf` for VIIRS).
The locations of these files and the binaries can be overridden with the `P2G_CREFL_NAME`, `P2G_CVIIRS_NAME`,
`P2G_CVIIRS_ANCPATH`, and `P2G_CMODIS_ANCPATH` environment variables.

Installation
------------

As mentioned above, the entire Polar2Grid project is available as an all-in-one tarball from the CSPP team. See the
main documentation site for more information. Otherwise, the following steps can be used to install individual packages.

The python package itself can be installed via pip::

    pip install -i http://larch.ssec.wisc.edu/simple polar2grid.crefl

Or from source::

    python setup.py install

There is also a method for creating a development environment with steps for compiling all extra polar2grid features
described on the main documentation site.

Copyright and License
---------------------

::

    Copyright (C) 2012-2015 Space Science and Engineering Center (SSEC), University of Wisconsin-Madison.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

