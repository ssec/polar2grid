Polar2Grid and Geo2Grid
=======================

.. image:: https://github.com/ssec/polar2grid/workflows/CI/badge.svg?branch=main
    :target: https://github.com/ssec/polar2grid/actions?query=workflow%3A%22CI%22

.. image:: https://coveralls.io/repos/github/ssec/polar2grid/badge.svg
    :target: https://coveralls.io/github/ssec/polar2grid

.. image:: https://codescene.io/projects/21812/status-badges/code-health
    :target: https://codescene.io/projects/21812
    :alt: CodeScene Code Health

Polar2Grid and Geo2Grid are a set of tools for extracting data from earth-observing satellite instruments,
remapping it to uniform grids, and writing that gridded data to a new file format.
As the names suggest, Polar2Grid is meant to operate on polar-orbiting satellite data and
Geo2Grid on geostationary satellite data. Due to the projects sharing a lot of internal functionality
their code bases are stored in the same code repository.
Both projects are created by scientists and software developers at the Space Science and Engineering Center (SSEC) at
the University of Wisconsin - Madison. Polar2Grid is distributed as part of the
`Community Satellite Processing Package (CSPP) <http://cimss.ssec.wisc.edu/cspp/>`_ for
processing of data received via direct broadcast antennas. Geo2Grid is distributed as part of the
`CSPP Geo <http://cimss.ssec.wisc.edu/csppgeo/>`_ project for processing of data received via direct broadcast
antennas. Although both projects were created to serve the direct
broadcast community, they can be used on most archived data files.
See the documentation for specific functionality.

`Polar2Grid Documentation <http://www.ssec.wisc.edu/software/polar2grid/>`_

`Geo2Grid Documentation <http://www.ssec.wisc.edu/software/geo2grid/>`_

`GitHub Repository <https://github.com/ssec/polar2grid>`_

`Polar2Grid Contact <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`__

`CSPP LEO Forum <https://forums.ssec.wisc.edu/viewforum.php?f=66>`_

`CSPP Geo Forum <https://forums.ssec.wisc.edu/viewforum.php?f=67>`_

Installation
------------

It is recommended that users use the official Polar2Grid/Geo2Grid release compatible
with RHEL6+ systems whenever possible. This tarball is available through the
CSPP team's website (see above). To install the Polar2Grid python package (used for Polar2Grid and Geo2Grid)
from source, run::

    pip install .

Other Installation Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^

The "polar2grid" package that powers the official CSPP Polar2Grid and CSPP Geo
Geo2Grid all-in-one tarballs is also released as a traditional python package
on PyPI and conda-forge. Installing the package in this way allows Polar2Grid
and Geo2Grid functionality to be used from non-Linux systems.
The python package can be installed into your normal Python 3.8+
environment by doing the following in a conda environment (recommended):

.. code-block:: bash

    conda install -c conda-forge polar2grid

Or with pip:

.. code-block:: bash

    pip install polar2grid

Once the package is installed the regular "geo2grid.sh" and "polar2grid.sh"
scripts are available. For systems without the bash shell available there are
also "geo2grid" and "polar2grid" wrapper scripts available. For example:

.. code-block:: bash

    polar2grid -h

Contributing
------------

Feel free to submit issues and pull requests on Github or contact us (see above) about more involved feature requests.
We do ask that before you add features yourself or fix complex issues that you contact us in some way. Both projects
are in active development and features and fixes are added all the time. Developers should see the
`Developer's Guide <http://www.ssec.wisc.edu/software/polar2grid/dev_guide/>`_ for more information on the internals
of both projects.

Directories
-----------

The majority of Polar2Grid is written in python, but some of the components may use third-party C or Fortran binaries
for various processing algorithms.
To make it easier to create our CSPP distribution (aka the software bundle) and for any pure python users we provide
the source for some of these executables in the root of the repository.

- polar2grid: The Polar2Grid python package.
- swbundle: Helper scripts and other files provided in the Polar2Grid Software Bundle released by the CSPP team.
- modis_crefl: Copy of the MODIS Corrected Reflectance software (CREFL) that includes updates for building with Makefile
- viirs_crefl: Copy of the VIIRS Corrected Reflectance software (CREFL) that includes updates for building with Makefile
- ms2gt: Custom version of the `ms2gt <http://nsidc.org/data/modis/ms2gt/>`_ software package with bug fixes and
         optimizations. This is not used as of P2Gv2.0 and will be removed in future revisions.
- etc: Configuration files used to customize the SatPy package for Polar2Grid users.

Copyright and License
---------------------

::

    Copyright (C) 2012-2021 Space Science and Engineering Center (SSEC), University of Wisconsin-Madison.

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

    Original scripts and automation included as part of this package are
    distributed under the GNU GENERAL PUBLIC LICENSE agreement version 3.
    Binary executable files included as part of this software package are
    copyrighted and licensed by their respective organizations, and
    distributed consistent with their licensing terms.
