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
flexibility is the design of the scripts tying a frontend to a backend.  In
future versions of polar2grid, it may be possible to have one unified script
where a frontend and a backend are selected via command line arguments.
Currently however there are not enough use cases to define a generic 'master'
script.  So the current design is to have separate connecting scripts that
can have as much freedom as they need to connect the frontend to the backend
and produce the proper output.

Prerequisites
-------------

These topics should be understood to get the most out of this guide:

 - The overall 'flow' of the :doc:`Chain <chain>`

A developer should be familiar with these concepts to develop a new component
for polar2grid:

 - python and numpy programming
 - memory management in terms of how arrays are created/manipulated/copied
 - flat binary files and how data is stored and arranged
   (`FBF Description <https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/flat-binary-format-fbf-files-and-utilities/FBF-file-format.pdf/view?searchterm=FBF>`_)
 - remapping/regridding satellite imagery swaths
 - python packaging, specifically `distribute <http://packages.python.org/distribute/>`_ (setuptools)
 - git source code management system and the 'forking' and 'pull request'
   features of http://github.com

Definitions
-----------

Pseudoband
    Band created by processing 'raw' data from satellite files.  For example,
    ``viirs2awips`` creates a Fog product from 'raw' data in the file.

.. _formats_section:

File Formats
------------

polar2grid uses flat binary files (FBF) for all of its intermediate file
storage.  Data is primary stored as files due its large size and the
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
develop new features or fix bugs.

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
structures or file renamings.

To run polar2grid from your new development environment run the following
command. This command uses viirs2awips, but any other connecting script
should follow the same basic calling sequence::

    python -m polar2grid.viirs2awips -vvv -g 211e -f /path/to/test/data/files/SVI01*
    # for more options run
    python -m polar2grid.viirs2awips -h

Frontend to Backend Scripts
---------------------------

As mentioned above, the scripts that connect frontend to backend have a lot
of freedom and should be considered the dumping ground for any special case
code.  They also follow the convention of placing all intermediate and product
files in the current directory, the directory that the script was executed
from.

TODO

Connecting scripts may use the metadata dictionary returned from the frontend
as storage for additional metadata.  This makes it easier to manage information
since the metadata dictionary already contains a 'per band' data structure.
This is optional, but may be helpful for implementing the script.  Some
examples of information that may be added by a connecting script:

 - ``fbf_swath`` (str): Filename of the binary swath file to be passed
   to the remapping utilities.  This is different from ``fbf_img`` when
   prescaling has to be done, otherwise it is the same.  This should be
   added to the band metadata dictionary since there is a different
   swath file for each band being processed.
 - ``img_lat`` (str): Filename of the latitude binary file.  This is only used
   as an alias for ``fbf_lat`` (a symbolic link).  This is added to the
   metadata dictionary.
 - ``img_lon`` (str): Filename of the longitude binary file to be passed to
   the remapping utilities.  This is only used as an alias for ``fbf_lon``
   (a symbolic link).  This is added to the metadata dictionary.
 - ``img_swath`` (str): Filename of the binary swath file to be passed to
   the remapping utilities.  This is only used as an alias for ``fbf_swath``
   (a symbolic link).  This is added to the band job metadata dictionary that
   is passed to the regridding utility, fornav.

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

The required pieces of information in the metadata dictionary are listed below.
Additional information can be stored:

 - ``sat`` (str): Satellite name or identifier, lowercase (ex. npp, aqua, terra)
 - ``instrument`` (str): Instrument name on the satellite, lowercase (ex. viirs, modis, etc)
 - ``kind`` (str): The kind of the band of data, lowercase.  For example, VIIRS has 'i' bands, 'm' bands,
    and 'dnb'.
 - ``start_dt`` (datetime object): First scanline measurement time for the entire swath
 - ``fbf_lat`` (str): Filename of the binary latitude file
 - ``fbf_lon`` (str): Filename of the binary longitude file
 - ``swath_rows`` (int): Number of rows in the entire swath
 - ``swath_cols`` (int): Number of columns in the entire swath
 - ``swath_scans`` (int): Number of scans in the entire swath.  ``swath_scans`` = ``swath_rows`` / ``rows_per_scan``
 - ``rows_per_scan`` (int): Number of rows per scan for the satellite.  This
   is usually constant for each satellite sensor type.
 - ``bands`` (dict of dicts): One python dictionary for each band
   (I01,I02,DNB,etc).  The key of the dictionary
   is the band as a string ('01' for I01, '02' for I02, '00' for DNB). Each
   of the band dictionaries must contain the following items:

    - ``data_kind`` (int constant): Constant describing what the data for
      this band is. Common cases are brightness temperatures, radiances, or
      reflectances.  For psuedobands created later in processing this value
      will represent what that psuedoband means (ex. Fog products).
    - ``src_kind`` (int constant): Same as ``data_kind`` for 'raw'
      data from the files.  During psuedoband creation this value is copied
      so that filtering by data source can be done, mainly used in remapping.
    - ``band`` (str) : Same as the key value for this dictionary
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

    Frontends are to used via one function named ``make_swaths``. This function
    takes 1 positional argument that is a list of the paths to the raw satellite
    data files (not including any navigation data files).  Past versions of the
    remapping utilities did not accept scan line navigation data with invalid/fill values
    (ex. -999).  A ``cut_bad`` keyword was added to frontends to tell the frontend
    to "cut out" these bad scanlines from the latitude, longitude, and all image
    data arrays.  This was done in the frontend to save on memory usage and processing
    time as the frontends were already reading in all of the data.

        make_swaths(filepaths, cut_bad=False, \*\*kwargs)


Product Backends
----------------

TODO

Rescaling
---------

TODO



