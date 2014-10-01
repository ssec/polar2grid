Constants
=========

Polar2grid defines various constants so that data or information can be
identified across multiple polar2grid components. This is very useful
considering polar2grid's semi-swappable frontend and backend design. The
constants are explained below, but are defined in the
``polar2grid.core.constants`` module. The source code for this module can
be found
`here <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/constants.py>`_.

The constants are listed as ``VARIABLE_NAME = "constant value"``. When used
on the command line the constant value should be used NOT the variable name.
If the value of a constant is not listed in the definition or in the
description this is because it should not be accessed by the user and the
constant value serves no purpose to a developer.

Special Constants
-----------------

Constants that don't fit any of the following categories or can be used in
place of multiple constants.

.. data:: NOT_APPLICABLE

    General constant when a required identifier has no meaning. The actual
    value is the python ``None`` value.

Satellites
----------

Constants identifying the satellite the data came from.

.. data:: SAT_NPP = "npp"

    Suomi National Polar-orbiting (NPP) satellite

.. data:: SAT_TERRA = "terra"

    NASA Earth Observing System's flagship satellite Terra (launched December 18, 1999)

.. data:: SAT_AQUA = "aqua"

    NASA Earch Science Satellite Aqua (launched May 4, 2002)

Instruments
-----------

Constants identifying the instrument that measured the data being used.

.. data:: INST_VIIRS = "viirs"

    Visible Infrared Imager Radiometer Suite

.. data:: INST_MODIS = "modis"

    Moderate-Resolution Imaging Spectroradiometer

Band Kinds
----------

Constants identifying the kind of band of the data. For some frontends this
means the type of product, such as cloud top height or sea surface temperature.
For other frontends this means the detector type used to record the data.

.. data:: BKIND_I = "i"

    NPP VIIRS imaging resolution bands

.. data:: BKIND_M = "m"

    NPP VIIRS moderate resolution bands

.. data:: BKIND_DNB = "dnb"

    NPP VIIRS Day/Night Band

.. data:: BKIND_VIS = "visible"

    Visible Band

.. data:: BKIND_IR = "infrared"

    Infrared Band

.. data:: BKIND_CMASK = "cloud_mask"

    Cloud Mask

.. data:: BKIND_LSMSK = "land_sea_mask"

    Land Sea Mask

.. data:: BKIND_SST  = "sea_surface_temp"

    Sea Surface Temperature

.. data:: BKIND_LST = "land_surface_temp"

    Land Surface Temperature

.. data:: BKIND_SLST = "summer_land_surface_temp"

    Summer Land Surface Temperature

.. data:: BKIND_SZA = "solar_zenith_angle"

    Solar Zenith Angle

.. data:: BKIND_CTT = "cloud_top_temperature"

    Cloud Top Temperature

.. data:: BKIND_IST = "ice_surface_temperature"

    Ice Surface Temperature

.. data:: BKIND_INV = "inversion_strength"

    Inversion Strength

.. data:: BKIND_IND = "inversion_depth"

    Inversion Depth

.. data:: BKIND_ICON = "ice_concentration"

    Ice Concentration

.. data:: BKIND_NDVI = "ndvi"

    Normalized Difference Vegetation Index

.. data:: BKIND_TPW = "total_precipitable_water"

    Total Precipitable Water

.. data:: BKIND_CREFL = "crefl"

    Corrected Reflectance Product

.. data:: BKIND_TCOLOR_CREFL = "true_color_crefl"

    True Color Corrected Reflectance Product (3-2D bands, RGB)

Band Identifiers
----------------

A second identifying value for a kind of band. This is primarily used when
bands have multiple detectors of the same kind. For example, their are
multiple NPP VIIRS I bands so they are numbered when provided by the frontend.
For bands that don't need a second identifying term the :data:`NOT_APPLICABLE`
constant can and should be used.

.. data:: BID_01 = "01"

.. data:: BID_01 = "02"

.. data:: BID_01 = "03"

.. data:: BID_01 = "04"

.. data:: BID_01 = "05"

.. data:: BID_01 = "06"

.. data:: BID_01 = "07"

.. data:: BID_01 = "08"

.. data:: BID_01 = "09"

.. data:: BID_01 = "10"

.. data:: BID_01 = "11"

.. data:: BID_01 = "12"

.. data:: BID_01 = "13"

.. data:: BID_01 = "14"

.. data:: BID_01 = "15"

.. data:: BID_01 = "16"

.. data:: BID_20 = "20"

.. data:: BID_26 = "26"

.. data:: BID_27 = "27"

.. data:: BID_31 = "31"

.. data:: BID_FOG = "fog"

.. data:: BID_NEW = "new"

.. _constants_data_kinds:

Data Kinds
----------

.. data:: DKIND_RADIANCE = "radiance"

    Radiance data.

.. data:: DKIND_REFLECTANCE = "reflectance"

    Reflectance data.

.. data:: DKIND_BTEMP = "btemp"

    Brightness Temperature data.

.. data:: DKIND_FOG = "fog"

    Fog data. Currently used to described the NPP VIIRS temperature
    difference (fog) product.

.. data:: DKIND_LATITUDE = "latitude"

    Latitude data. Not used often since it is not processed as image data.

.. data:: DKIND_LONGITUDE = "longitude"

    Longitude data. Not used often since it is not processed as image data.

.. data:: DKIND_CATEGORY    = "category"

    Discrete category data, where each category is represented by an integer in the data.

.. data:: DKIND_ANGLE       = "angle"

    Data represented as angles.

.. data:: DKIND_DISTANCE    = "distance"

    Distance (meters, miles, etc.)

.. data:: DKIND_PERCENT     = "percent"

    Data represented as a percentage.

.. data:: DKIND_C_INDEX     = "contiguous_index"

    Abstract ranging index with meaningful contiguous values (not discrete categories)

.. data:: DKIND_CREFL = "corrected_reflectance"

    Corrected Reflectance data.

.. data:: DKIND_TCOLOR_CREFL = "true_color_crefl"

    True Color Corrected Reflectance data (RGB - 3 bands)

Special Set:

.. data:: SET_DKINDS

    A python set object that holds all of the data kinds listed above. This
    can only be used internally in the software. It can **NOT** be used in
    configuration files or on the command line.

.. _constants_data_types:

Data Types
----------

Constants that describe the size or format of the binary representation of the
data. The values of these constants represent the flat binary format naming
scheme where the integer suffix represents the number of bytes in the format.
The constant variable name uses the ``numpy`` python package naming scheme
where the integer suffix represents the number of bits in the format.

.. data:: DTYPE_UINT8 = "uint1"

.. data:: DTYPE_UINT16 = "uint2"

.. data:: DTYPE_UINT32 = "uint4"

.. data:: DTYPE_UINT64 = "uint8"

.. data:: DTYPE_INT8 = "int1"

.. data:: DTYPE_INT16 = "int2"

.. data:: DTYPE_INT32 = "int4"

.. data:: DTYPE_INT64 = "int8"

.. data:: DTYPE_FLOAT32 = "real4"

.. data:: DTYPE_FLOAT64 = "real8"

Navigation Identifiers
----------------------

Constants that describe the type of navigation the data is using. For example,
what resolution at which the data was measured (250 meters, 750 meters, 1km, etc).
These naming of these values is determined by the frontend.

.. data:: MBAND_NAV_UID = "m_nav"

    VIIRS M band navigation group

.. data:: IBAND_NAV_UID = "i_nav"

    VIIRS I band navigation group

.. data:: DNB_NAV_UID = "dnb_nav"

    VIIRS Day/Night band navigation group

.. data:: GEO_NAV_UID = "geo_1000m_nav"

    MODIS 1000 meter navigation group

.. data:: GEO_500M_NAV_UID = "geo_500m_nav"

    MODIS 500 meter navigation navigation group

.. data:: GEO_250M_NAV_UID = "geo_250m_nav"

    MODIS 250 meter navigation group

.. data:: MOD06_NAV_UID = "mod06_nav"

    MODIS mod06 navigation group

.. data:: MOD07_NAV_UID = "mod07_nav"

    MODIS mod07 navigation group

Grid Constants
--------------

Constants that are used to describe supported grids or the type of grid. Each
constant listed below will specifically say its purpose.

.. data:: GRIDS_ANY

    Used by backends to tell grid determination that any grid can be
    used by that specific backend. Currently this includes PROJ.4 grids
    and GPD grids.

.. data:: GRIDS_ANY_GPD

    Used by backends to tell grid determination that any gpd grid can be
    used by that specific backend.

.. data:: GRIDS_ANY_PROJ4

    Used by backends to tell grid determination that any PROJ.4 grid can be
    used by that specific backend.

.. data:: GRID_KIND_GPD

    Constant used to describe the grid returned by the grids configuration
    file. This is used by grid determination and remapping so that GPD
    grids can be handled in a special manner if they need to be.

.. data:: GRID_KIND_PROJ4

    Constant used to describe the grid returned by the grids configuration
    file. This is used by grid determination and remapping so that PROJ.4
    grids can be handled in a special manner if they need to be.

Glue Script Return Codes
------------------------

    Constants that :term:`glue scripts` should return to notify the calling
    shell of the reason for failure. Note that for human-readable details the
    log messages (the ``-v`` flag) are much more descriptive of the exact
    error that occurred.

.. data:: STATUS_SUCCESS = 0

    Glue script completed successfully

.. data:: STATUS_FRONTEND_FAIL = 1

    Glue script failed while trying to get data from the frontend.

.. data:: STATUS_BACKEND_FAIL = 2

    Glue script failed while trying to create output products using the
    backend.

.. data:: STATUS_REMAP_FAIL = 12

    A bitwise OR of the following 2 constants. Glue script failed during
    some remapping operation. Since remapping may be called via one function
    that encapsulates the ll2cr and fornav operations, this constant may be
    returned since there is no easy way to determine which operation failed.

.. data:: STATUS_LL2CR_FAIL = 4

    Glue script failed when running ll2cr.

.. data:: STATUS_FORNAV_FAIL = 8

    Glue script failed when running fornav.

.. data:: STATUS_GDETER_FAIL = 16

    Glue script failed while determining the grid to remap to.

.. data:: STATUS_UNKNOWN_FAIL = -1

    An unexpected and unknown error occurred. Log messages are the best way to
    diagnose this.

Fill Values
-----------

.. _default_fill_value:

.. data:: DEFAULT_FILL_VALUE = -999.0

    Used by most, if not all, polar2grid components that deal with data to
    specify a fill value to use. Frontends are not required to use this
    fill value, but must specify otherwise (see the :doc:`dev_guide/index` for
    more details).
