POLAR2GRID
==========

Polar2grid is a software package for converting polar-orbitting satellite
data from various sources (VIIRS, MODIS, etc.) into
formats that are useable by meteorlogical visualization applications,
such as AWIPS, NINJO, WMS, etc.

The main code repository is hosted at https://github.com/davidh-ssec/polar2grid

The main documentation site is http://www.ssec.wisc.edu/software/polar2grid/

Directory Structure
-------------------

..

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

