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

Polar2Grid Main Package
-----------------------

The main `polar2grid` package contains objects and tools for remapping as well as various backends. It's main purpose
to command line users is as a glue script via the `polar2grid.glue` module. This script automates the common
operation of `Frontend -> Remapping -> [Compositors] -> Backend`.

Installation
------------

As mentioned above, the entire Polar2Grid project is available as an all-in-one tarball from the CSPP team. See the
main documentation site for more information. Otherwise, the following steps can be used to install individual packages.

The python package itself can be installed via pip::

    pip install -i http://larch.ssec.wisc.edu/simple polar2grid

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

