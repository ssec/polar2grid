Polar2Grid
==========

Polar2Grid is a set of tools for extracting swath data from earth-observing satellite instruments,
remapping it to uniform grids, and finally writing that gridded data to a new file format.
Polar2Grid is created by scientists and software developers at the Space Science and Engineering Center (SSEC) at
the University of Wisconsin - Madison. It is distributed as part of the
`Community Satellite Processing Package (CSPP) <http://cimss.ssec.wisc.edu/cspp/>`_ for
processing of data received via direct broadcast antennas. Although this is why Polar2Grid was created, it can be used
on most archived (non-DB) data files. See the documentation for specific functionality.

`Documentation <http://www.ssec.wisc.edu/software/polar2grid/>`_

`GitHub Repository <https://github.com/davidh-ssec/polar2grid>`_

`Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`_

Contributing
------------

Feel free to submit issues and pull requests on Github or contact us (see above) about more involved feature requests.
We do ask that before you add features yourself or fix complex issues that you contact us in some way. Polar2Grid is
in active development and features and fixes are added all the time. Developers should see the
`Developer's Guide <http://www.ssec.wisc.edu/software/polar2grid/dev_guide/>`_ for more information on the internals
of Polar2Grid.

Directories
-----------

The majority of Polar2Grid is written in python, but some of the components may use third-party C or Fortran binaries
for various processing algorithms.
To make it easier to create our CSPP distribution (aka the software bundle) and for any pure python users we provide
the source for some of these executables in the root of the repository.

- py: Contains all of the python code. Due to the modularity of Polar2Grid there are multiple python packages to allow users to only install portions of Polar2Grid.
- swbundle: Helper scripts and other files provided in the Polar2Grid Software Bundle released by the CSPP team.
- modis_crefl: Copy of the MODIS Corrected Reflectance software (CREFL) that includes updates for building with Makefile
- viirs_crefl: Copy of the VIIRS Corrected Reflectance software (CREFL) that includes updates for building with Makefile
- ms2gt: Custom version of the `ms2gt <http://nsidc.org/data/modis/ms2gt/>`_ software package with bug fixes and optimizations. This is not used as of P2Gv2.0 and will be removed in future revisions.

Branching Model
---------------

The branching model used by the Polar2Grid team follows a basic ``feature-branch`` -> ``develop`` -> ``master``
structure.
New features still in development should get their own branches. Once these features are complete they are merged
into the ``develop`` branch. Once all features for a particular release have been tested and are considered
"release ready" they are merged into the ``master`` branch. If a master merge is for a new minor version a
maintenance branch is also created for future bug fixes. This branching model was inspired from the discussion
`here <http://nvie.com/posts/a-successful-git-branching-model/>`_.

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

    Original scripts and automation included as part of this package are
    distributed under the GNU GENERAL PUBLIC LICENSE agreement version 3.
    Binary executable files included as part of this software package are
    copyrighted and licensed by their respective organizations, and
    distributed consistent with their licensing terms.
