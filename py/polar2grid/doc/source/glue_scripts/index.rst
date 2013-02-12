Glue Scripts
============

Polar2grid uses specialized scripts to handle the high level processing of
polar-orbiting satellite data to product generation.  These scripts are
programmed in python and called glue scripts.  Each glue script has
a "bundle" script that is located in the polar2grid software bundle's
``/bin`` directory.  These "bundle" scripts are used to setup the
environment needed by the python scripts, enter defaults into the python
scripts, and ease the installation/use process for the user.  The "bundle"
scripts are callable (once proper installation steps have been taken) by the
name of the script.

.. important::

    Glue scripts do not delete files created by previous glue script
    calls and may fail if those files exist during processing. The two common
    methods for dealing with this are the ``-R`` command line option
    described below or creating a working directory for each new call to a
    glue script and removing the working directory after copying/using
    the product files.

.. note::

    If you are using the basic software bundle method of installation, you MUST use
    the bundle script to properly run polar2grid processing.

There are 2 common use cases for glue scripts. First is creating a
working directory for each run of the glue script::

    $POLAR2GRID_HOME/bin/viirs2awips.sh -g 211e -d /path/to/data/

This example forces the grid to ``211e`` and tells the script to process
all accepted files in the directory ``/path/to/data/``. Since the working
directory is not reused the :option:`-R` flag does not have to be used.

The second common case is running a glue script multiple times in the same
working directory. This is usually done for testing or running with a specific
set of files::

    $POLAR2GRID_HOME/bin/viirs2awips.sh -vv -R
    $POLAR2GRID_HOME/bin/viirs2awips.sh -g 203 -f /path/to/files*.h5

This example forces the grid to ``203`` and lists a specific set of input
files. The glue script will only operate on the files that exist and that
it knows how to handle. Since this use case is run in the same working
directory multiple times, the :option:`-R` option is needed to remove files
from previous runs that may conflict with the next invocation. The
:option:`-v` flags tell the script to print ``INFO`` level log messages
which will print what files are removed. See specific glue script
documentation for more information on available command line options.

The following glue scripts are included with polar2grid:

.. toctree::
    :maxdepth: 1

    viirs2awips
    viirs2gtiff
    viirs2binary
    modis2awips



