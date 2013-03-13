Data Frontends
==============

The main responsibility of data frontends is to take raw satellite data files
and put it into a common format that the rest of the polar2grid package can
understand. Frontends output two types of data, flat binary files of all
necessary data and a python dictionary with metadata to be used in the rest
of processing. All flat binary file output should follow SSEC FBF naming conventions
(`FBF Description <https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/flat-binary-format-fbf-files-and-utilities/FBF-file-format.pdf>`_).
Flat binary files should also follow the convention of having one
invalid/missing value (-999.0) as described in the :ref:`formats_section` section.

The required flat binary files that should be created for each call to the
frontend are:

 - 1 Image data file for each band to be processed
 - 1 Latitude file
 - 1 Longitude file

Data files and navigation files must have the same shape. It is also assumed
that all data files have 1 pair of navigation files (latitude and longitude).
Frontends should be called once per set of navigation sharing files. If it
is desired or more efficient to break these
:term:`navigation sets <navigation set>` into smaller sets
this is up to the glue script and must be made possible by the frontend.

The pieces of information in the metadata dictionary are listed below. All
the information is required unless stated otherwise. A data type of 'constant'
means the value is a constant in the :doc:`polar2grid.core.constants <../constants>` module.
Metadata 'key (data type): description':

 - ``sat`` (constant): Satellite name or identifier (ex. SAT_NPP, SAT_AQUA, SAT_TERRA)
 - ``instrument`` (constant): Instrument name on the satellite (ex. INST_VIIRS, INST_MODIS, etc)
 - ``start_time`` (datetime object): First scanline measurement time for the entire swath
 - ``fbf_lat`` (str): Filename of the binary latitude file. Flat binary files
   should be stored in the current working directory and referred to by their
   filename, not filepath.
 - ``fbf_lon`` (str): Filename of the binary longitude file. Flat binary files
   should be stored in the current working directory and referred to by their
   filename, not filepath.
 - ``nav_set_uid`` (str): Unique identifier for a :term:`navigation set`.
 - ``lat_south`` (float): Southern most valid latitude of the navigation
    data. This
    value is optional, but may be used to remap to PROJ.4 grids. It is often
    faster for the frontend to compute this value than to have the remapper
    load the entire swath array into memory and search for the minimum.
 - ``lat_north`` (float): Northern most valid latitude of the navigation data.
    This
    value is optional, similar to ``lat_south``.
 - ``lon_west`` (float): Western most valid longitude of the navigation data.
    This
    value is optional, similar to ``lat_south``.
 - ``lon_east`` (float): Eastern most valid longitude of the navigation data.
    This
    value is optional, similar to ``lat_south``.
 - ``lon_fill_value`` (float): Fill value for the longitude data. Glue scripts
    assume -999.0 if not specified. This parameter is optional.
 - ``lat_fill_value`` (float): Fill value for the latitude data. Glue scripts
    assume -999.0 if not specified. This parameter is optional.
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
    - ``fbf_img`` (str) : Filename of the binary swath file. Flat binary
      files should be stored in the current working directory and referred
      to by their filename, not filepath.
    - ``fill_value`` (float) : Data fill value. Glue scripts assume -999.0
        if not specified. This parameter is optional.
    - ``swath_rows`` (int) : Copy of metadata dict entry
    - ``swath_cols`` (int) : Copy of metadata dict entry
    - ``swath_scans`` (int) : Copy of metadata dict entry
    - ``rows_per_scan`` (int) : Copy of metadata dict entry

.. note::

    Although the metadata dictionary holds required information, it can also
    be used to hold any additional information that may be needed to easily
    produce the flat binary file output (ex. filepaths, glob patterns, etc).

Interface:

    Frontends are to be used via one class named ``Frontend``. This class
    must be derived from the :py:class:`polar2grid.core.roles.FrontendRole`
    class, see the roles documentation for additional information on methods.

    Past versions of the
    remapping utilities did not accept scan line navigation data with
    invalid/fill values (ex. -999).  A ``cut_bad`` keyword was added to
    frontends to tell the frontend to "cut out" these bad scanlines from the
    latitude, longitude, and all image data arrays.  This was done in the
    frontend to save on memory usage and processing time as the frontends
    were already reading in all of the data.  Other keywords may be added
    for any frontend specific functionality.  For example, the VIIRS frontend
    can make a temperature difference 'fog' pseudoband or it can do histogram
    equilization on the VIIRS Day/Night Band; there are keywords for each.

