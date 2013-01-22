POLAR2GRID
==========

Polar2grid is a software package for converting polar-orbitting satellite
data from various sources (VIIRS, MODIS, etc.) into
formats that are useable by meteorlogical visualization applications,
such as AWIPS, NINJO, WMS, etc.

The main code repository is hosted at https://github.com/davidh-ssec/polar2grid

The main documentation site is http://www.ssec.wisc.edu/software/polar2grid/

License
-------

::

    Copyright (C) 2013 Space Science and Engineering Center (SSEC),
     University of Wisconsin-Madison.

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

Directory Structure
-------------------

.. code-block::

    . git root
    ├── ms2gt
    │   └── # custom polar2grid version of ms2gt
    ├── py
    │   ├── # Python packages and scripts
    │   ├── misc
    │   │   └── # miscellaneous files
    │   ├── polar2grid
    │   │   ├── doc
    │   │   │   └── # Sphinx documentation files for main documentation site
    │   │   └── polar2grid
    │   │       ├── # 'Main' python package (highest on dependency tree)
    │   │       ├── awips
    │   │       │   ├── # AWIPS backend code
    │   │       │   └── ncml
    │   │       │       └── # NCML templates for the AWIPS backend
    │   │       └── grids
    │   │           └── # Grids subpackage, includes gpd files and grid configuration files
    │   ├── polar2grid_core
    │   │   └── polar2grid
    │   │       └── core
    │   │           ├── # 'Core' python package (lowest on dependency tree)
    │   │           └── rescale_configs
    │   │               └── # Rescaling configuration files (\*.conf)
    │   ├── polar2grid_viirs
    │   │   └── polar2grid
    │   │       └── viirs
    │   │           └── # VIIRS frontend package (middle of the dependency tree)
    │   └── util
    │       └── # Python utility scripts not necessary used directly with polar2grid
    ├── swbundle
    │   └── # Bash scripts and text files for the './bin' directory of the software bundle
    └── swbundle_tests
        └── # Bash scripts (run/verify) for the test bundles

SVN Conversion Notes
--------------------

The original repository included a "vendor" directory in the root repository
that was being used to store the vendor release of ms2gt.  The repository was
converted to git using "svn2git" which does not support this structure.
For now, the "vendor" directory is represented by the ``ms2gt`` directory in
the root of the git repository.

