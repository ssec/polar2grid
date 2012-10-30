Developer's Guide
=================

This guide is intended to ease the development of additional frontends,
backends, or other components to the polar2grid package. It provides the
general interface for each "chain link" as well as a minimal description
of the responibilites of that link.  To avoid being tied down to a specific
implementation, the polar2grid package
is very flexible in terms of where certain pieces of logic can go.  As the
package matures this flexibility will slowly disappear.

An example of this
flexibility is the design of the scripts tying a frontend to a backend
(glue scripts).  In
future versions of polar2grid, it may be possible to have one unified script
where a frontend and a backend are selected via command line arguments.
Currently however there are not enough use cases to define a generic 'master'
script.  So the current design has separate glue scripts that
can have as much freedom as they need to connect the frontend to the backend
and produce the proper output.  Although, there shouldn't need to be much
work outside of what has already been done to accomplish any gluing.  That is,
assuming any new frontends or backends were developed properly.

If you are trying to decide whether or not your backend idea should be
implemented in polar2grid here are a few things to think about.  Polar2grid
should not be used for anything that doesn't want remapped data.  If you want
raw scanline data, polar2grid is not the package for you.  Also, if your
backend output is not a file, polar2grid is not for you.  Non-file output may
be something like a server that provides remapped data to a client.  Although
polar2grid could provide this data to a server for storage, a polar2grid
backend should not be doing the serving.

Polar2grid is intended for polar-orbitting satellite data.  Geo-stationary
data may work with the current tool-set, but is not guaranteed to always
work.

Prerequisites
-------------

These polar2grid topics should be understood to get the most out of this
guide:

 - The overall 'flow' of the :doc:`Chain <chain>`
 - The responsibilities of a frontend
 - The responsibilities of a backend
 - Package hierarchy and dependencies

A developer should be familiar with these concepts to develop a new component
for polar2grid:

 - python and numpy programming
 - memory management in terms of how arrays are created/manipulated/copied
 - flat binary files and how data is stored and arranged
   (`FBF Description <https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/flat-binary-format-fbf-files-and-utilities/FBF-file-format.pdf/view?searchterm=FBF>`_)
 - remapping/regridding satellite imagery swaths (including types of projections)
 - python packaging, specifically `distribute <http://packages.python.org/distribute/>`_ (setuptools)
 - git source code management system and the 'forking' and 'pull request'
   features of http://github.com

Definitions
-----------

Pseudoband
    Band created by processing 'raw' data from satellite files.  For example,
    ``polar2grid.viirs`` can create a Fog product from 'raw' .h5 data.
Glue Script
    The script connecting every component together.  A glue script connects
    the frontend, grid determiner, remapper, and backend.  There is one
    glue script per task, so one for every frontend to backend connection.

.. _formats_section:

File Formats
------------

polar2grid uses flat binary files (FBF) for all of its intermediate file
storage.  Data is primarily stored as files due its large size and the
requirement for the current remapping utilities to have file input.

FBF conventions specific to polar2grid are that there is only one
invalid/missing value, -999.0, and that all image and navigation
data is stored as 32-bit floats (real4 in FBF terms).

polar2grid does not require any other data format except for those required
by a frontend or backend.

Setting up a development environment
------------------------------------

Before adding components to polar2grid you will need to set up a polar2grid
development environment.  This will allow for easy access to the newest code
updates from other developers and make it easier for you to get your code
additions added to the master polar2grid package.  As described in other
parts of the documentation, the primary installation of polar2grid is the
software bundle.  The software bundle consists of a lot of wrapper scripts
to make it easier to install and use, but it does not make it easy to
develop new features or fix bugs as it hides the command line arguments from
the user.

The main code repository for polar2grid is on github at
https://github.com/davidh-ssec/polar2grid.
If you plan to make a lot of changes over a long period of time it may
be beneficial to "fork" the main repository and then make a "pull request"
when you believe your code is ready to be added to the master branch.

The following instructions will go through a common development installation
case.  It will install everything into 1 directory in your home directory.
polar2grid development does not require this directory structure, so if you
understand every step of these instructions feel free to change the locations
where components are installed.

1. Get a copy of the main code repository:
   
    ::

        mkdir ~/polar2grid
        cd ~/polar2grid
        git clone https://github.com/davidh-ssec/polar2grid.git polar2grid
        cd polar2grid

    If you are working on a specific branch, like 'ninjo' for example,
    you should do the following in addition to the above:

    ::

        git checkout -b ninjo origin/ninjo

2. Compile ms2gt:
   
    ::

        cd polar2grid/ms2gt
        make clean
        make

3. Download and unpack ShellB3:
 
    ::

        cd ~/polar2grid
        # Download the newest version of ShellB3 from ftp://ftp.ssec.wisc.edu/pub/shellb3/
        wget ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3-Linux-x86_64-YYYYMMDD-rXXX-core-cspp.tar.gz
        tar -xzf ShellB3-Linux-x86_64-YYYYMMDD-rXXX-core-cspp.tar.gz

    .. note::

           This step is optional. You could install python 2.7
           and the necessary python packages and libraries yourself, but ShellB3 is a
           pre-compiled binary package with all requirements included.
           Libraries required by polar2grid depend on
           the frontend and backend used, but the most common are 'netcdf4-python',
           'h5py', 'pyhdf', 'GDAL'.
 
4. Create a location to install the polar2grid python packages
   (don't install them just yet):
   
    ::

        cd ~/polar2grid
        mkdir python

4. Add the newly installed software to your PATH environment variable and
   add the new python package location to your PYTHONPATH:
   
    ::

        # Edit your ~/.bash_profile or equivalent file
        # Add this to the bottom
        export PATH=$HOME/polar2grid/ShellB3/bin:$PATH
        export PATH=$HOME/polar2grid/polar2grid/ms2gt/bin:$PATH
        export PYTHONPATH=$HOME/polar2grid/python:$PYTHONPATH
        # Log out and log back in or run 'source ~/.bash_profile' for these to take effect

5. Verify you are using the correct python:
   
    ::

        which python
        # result should be '/home/<username>/polar2grid/ShellB3/bin/python'
        python -V
        # result should be 'Python 2.7.x'

6. Install the python packages in a development mode:
   
    ::

        cd ~/polar2grid/polar2grid/py/
        cd polar2grid_core
        python setup.py develop -d ~/polar2grid/python
        cd ../polar2grid_viirs
        python setup.py develop -d ~/polar2grid/python
        cd ../polar2grid
        python setup.py develop -d ~/polar2grid/python
        cd ~

7. Verify that you can import all of the polar2grid python packages:
   
    ::

        python -c "from polar2grid import viirs2awips"
        # should result in nothing

You now have a polar2grid development environment. If you are not familiar
with python packaging (distribute/setuptools), when updating your git
repository via a "git pull" or adding files, you may have to redo step 6.
This will make the development install understand any new directory
structures or file renamings.  If a "git pull" shows that ms2gt files
were changed, you will need to recompile ms2gt by running step 2 again.

To run polar2grid from your new development environment run the following
command. This command uses viirs2awips, but any other glue script
should follow the same basic calling sequence::

    python -m polar2grid.viirs2awips -vvv -g 211e -f /path/to/test/data/files/SVI01*
    # for more options run
    python -m polar2grid.viirs2awips -h

Frontend to Backend Scripts (Glue Scripts)
------------------------------------------

As mentioned above, the scripts that connect frontend to backend have a lot
of freedom and should be considered the dumping ground for any special case
code.  They also follow the convention of placing all intermediate and product
files in the current directory, the directory that the script was executed
from.  Frontends, backends, remapping, and any other polar2grid component
will follow this convention so glue script should do the same.

Glue scripts are the first python script that should be called by the user.
They have command line arguments that are relevant to their specific frontends
and backends, as well as those common to all glue scripts (like remapping and
grid determination options).  The main responsibility of a glue script is to
take input data filenames from the command line, separate them by files that
share the navigation data
(usually by filename pattern), and process each set of those files separately.
Processing means calling the frontend to get the data into swaths, calling
the grid determiner to find what grids the data should be mapped to,
calling the remapper to remap/grid the data, and calling the backend to
produce the gridded data in a format useful to others.

Glue scripts may use the metadata dictionary returned from the frontend
as storage for additional metadata.  This makes it easier to manage information
since the metadata dictionary already contains a 'per band' data structure.
This is optional, but may be helpful for implementing the script. Meta-data
keys/values should never be overwritten, just add new keys. Overwriting will
make debugging more difficult and will likely result in problems.  Some
examples of information that may be added by a connecting script:

 - ``fbf_swath`` (str): Filename of the binary swath file to be passed
   to the remapping utilities.  This is different from ``fbf_img`` when
   prescaling has to be done, otherwise it is the same.  This should be
   added to the band metadata dictionary since there is a different
   swath file for each band being processed.

.. note::

    The ``fbf_swath`` example above may not be relevant if prescaling
    is done in the frontend.

Data Frontends
--------------

The main responsibility of data frontends is to take raw satellite data files
and put it into a common format that the rest of the polar2grid package can
understand.  Frontends output two types of data, flat binary files of all
necessary data and a python dictionary with metadata to be used in the rest
of processing.  All flat binary file output should follow SSEC FBF naming conventions
(`FBF Description <https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/flat-binary-format-fbf-files-and-utilities/FBF-file-format.pdf/view?searchterm=FBF>`_).
Flat binary files should also follow the convention of having one
invalid/missing value (-999.0) as described in the :ref:`formats_section` section
above.

The required flat binary files that should be created are:
 - 1 Image data file for each band to be processed
 - 1 Latitude file
 - 1 Longitude file
 - (Optional) Data that is needed for future processing of the image data (ex. day/night mask)

Data files and navigation files must have the same shape.  It is also assumed
that all data files have 1 pair of navigation files (latitude and longitude).
Frontends should be called once per set of navigation sharing files.  If it
is desired or more efficient to break these navigation sets into smaller sets
this is up to the glue script and must be made possible by the frontend.

The pieces of information in the metadata dictionary are listed below. All
the information is required unless stated otherwise. A data type of 'constant'
means the value is a constant in the ``polar2grid.core.constants`` module.
Metadata 'key (data type): description':

 - ``sat`` (constant): Satellite name or identifier (ex. SAT_NPP, SAT_AQUA, SAT_TERRA)
 - ``instrument`` (constant): Instrument name on the satellite (ex. INST_VIIRS, INST_MODIS, etc)
 - ``start_time`` (datetime object): First scanline measurement time for the entire swath
 - ``fbf_lat`` (str): Filename of the binary latitude file
 - ``fbf_lon`` (str): Filename of the binary longitude file
 - ``lat_min`` (float): Minimum valid latitude of the navigation data. This
    value is optional, but may be used to remap to PROJ4 grids. It is often
    faster for the frontend to compute this value than to have the remapper
    load the entire swath array into memory and search for the minimum.
 - ``lat_max`` (float): Maximum valid latitude of the navigation data. This
    value is optional, similar to ``lat_min``.
 - ``lon_min`` (float): Minimum valid longitude of the navigation data. This
    value is optional, similar to ``lat_min``.
 - ``lon_max`` (float): Maximum valid longitude of the navigation data. This
    value is optional, similar to ``lat_min``.
 - ``swath_rows`` (int): Number of rows in the entire swath
 - ``swath_cols`` (int): Number of columns in the entire swath
 - ``swath_scans`` (int): Number of scans in the entire swath.  ``swath_scans`` = ``swath_rows`` / ``rows_per_scan``
 - ``rows_per_scan`` (int): Number of rows per scan for the satellite.  This
   is usually constant for each satellite sensor type.
 - ``bands`` (dict of dicts): One python dictionary for each band
   (I01,I02,DNB,etc).  The key of the dictionary
   is a 2-element tuple of (kind of band, band ID), each being a constant.
   Some examples would be (BKIND_I,BID_01) for I01 or
   (BKIND_DNB,NOT_APPLICABLE) for DNB). Each
   of the band dictionaries must contain the following items:

    - ``data_kind`` (constant): Constant describing what the data for
      this band is. Common cases are brightness temperatures, radiances, or
      reflectances.  For psuedobands created later in processing this value
      will represent what that psuedoband means (ex. Fog products)
    - ``remap_data_as`` (constant): Same as ``data_kind`` for 'raw'
      data from the files.  During psuedoband creation this value is copied
      from the data used to create the psuedoband to tell the remapping that
      it shares the same invalid mask as its creating bands and can be
      separated based on this type
    - ``kind`` (constant): The kind of the band of data, constant.
      For example, VIIRS has BKIND_I, BKIND_M, BKIND_DNB. Same as the key's
      first element for this dictionary
    - ``band`` (constant) : Same as the key's second element for this
      dictionary
    - ``fbf_img`` (str) : Filename of the binary swath file
    - ``swath_rows`` (int) : Copy of metadata dict entry
    - ``swath_cols`` (int) : Copy of metadata dict entry
    - ``swath_scans`` (int) : Copy of metadata dict entry
    - ``rows_per_scan`` (int) : Copy of metadata dict entry

.. note::

    Although the metadata dictionary holds required information, it can also
    be used to hold any additional information that may be needed to easily
    produce the flat binary file output (ex. filepaths, glob patterns, etc).

Interface:

    Frontends are to used via one class named ``Frontend``.  The ``__init__``
    function does not require any arguments.  The key function is named
    ``make_swaths`` and performs all of the functionality of the frontend.
    This function takes 1 positional
    argument that is a list of the paths to the raw satellite data files
    (not including any navigation data files).  Past versions of the
    remapping utilities did not accept scan line navigation data with
    invalid/fill values (ex. -999).  A ``cut_bad`` keyword was added to
    frontends to tell the frontend to "cut out" these bad scanlines from the
    latitude, longitude, and all image data arrays.  This was done in the
    frontend to save on memory usage and processing time as the frontends
    were already reading in all of the data.  Other keywords may be added
    for any frontend specific functionality.  For example, the VIIRS frontend
    can make a temperature difference 'fog' pseudoband or it can do histogram
    equilization on the VIIRS Day/Night Band; there are keywords for each.

    ::

        frontend.make_swaths(filepaths, cut_bad=False, **kwargs)

Grid Jobs
---------

.. warning::

    This API may change to be object oriented and/or return different
    dictionaries.

TODO

Remapping
---------

Remapping is the process of mapping polar-orbitting satellite data pixels to
an evenly spaced grid.  This grid is either equal-area or equal-angle
depending on the projection provided.
Polar2grid's remapping step is actually 2 separate steps. The first step
known as ll2cr (lat/lon to col/row) calculates each pixels location in the
newly projected grid. It takes a longitude/latitude location and maps it to
a column/row location in the grid being mapped to.  This grid location is a
decimal value (fractional pixel locations) used in the second remapping step.
The second step known as fornav (forward navigation) takes the output of the
first remapping step and weights each input image pixel to calculate the
output grid pixel.

Grid specifications are provided to remapping via grid names and the first
step of remapping will pull the information from the `grids.conf` file (see
the :ref:`grids_section` section below).  There are 2 methods of accessing
the remapping process.  The first is calling the 2 steps of remapping
separately using the following::

    from polar2grid.remap import run_ll2cr,run_fornav
    ll2cr_output = run_ll2cr(sat, instrument, kind, lon_fbf, lat_fbf,
                        grid_jobs, **kwargs)
    fornav_output = run_fornav(sat, instrument, kind, grid_jobs, ll2cr_output,
                        **kwargs)

See the API documentation for more information on possible keyword arguments.

TODO API Link

The second method is by calling::

    from polar2grid.remap import remap_bands
    fornav_output = remap_bands(sat, instrument, kind, lon_fbf, lat_fbf,
                        grid_jobs, **kwargs)

This function simply calls ``run_ll2cr`` and ``run_fornav``.
See the API documentation for more information on possible keyword arguments.

TODO API Link

Product Backends
----------------

TODO

Rescaling
---------

Rescaling is a component that takes grids of data and scales them to a proper
range, usable by a product backend.  Rescaling should only be called by
backends.  Although it is possible, there shouldn't be any need to subclass
the default ``Rescaler`` in ``polar2grid.rescale``.

TODO

.. _grids_section:

Grids
-----

TODO

