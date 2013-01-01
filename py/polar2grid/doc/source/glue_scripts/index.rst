Glue Scripts
============

.. include:: ../global.rst

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

The following are glue scripts are included with polar2grid:

.. toctree::
    :maxdepth: 1

    viirs2awips
    viirs2gtiff
    viirs2binary



