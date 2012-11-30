"""Module to store all constants.  Any constant needed in more than one
component, or potentially more than one part, of polar2grid should be
defined here.

Rules/Preferences:
    - All values lowercase
    - strings
    - user-legible (assume that they may be printed in log messages)
    - use == for comparison (not 'is' or 'not' or other)

Possible confusions:
    The VIIRS fog product created by polar2grid is a temperature difference of
    2 I bands.  It is classified as an I band for this reason, meaning the
    band is "fog", not the usual number.

Exceptions:
    - Return status constants are not strings so that they can be or'ed and
    can be interpreted by a command line shell.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

NOT_APPLICABLE = None

# default fill value
DEFAULT_FILL_VALUE = -999.0

# Satellites
SAT_NPP   = "npp"
SAT_TERRA = "terra"
SAT_AQUA  = "aqua"

# Instruments
INST_VIIRS = "viirs"
INST_MODIS = "modis"

# Band Kinds
BKIND_I     = "i"
BKIND_M     = "m"
BKIND_DNB   = "dnb"
BKIND_VIS   = "visible"
BKIND_IR    = "infrared"
BKIND_CMASK = "cloud_mask"
BKIND_SST   = "sea_surface_temp"
BKIND_LST   = "land_surface_temp"
BKIND_SLST  = "summer_land_surface_temp"
BKIND_SZA   = "solar_zenith_angle"
BKIND_CTT   = "cloud_top_temperature"
BKIND_IST   = "ice_surface_temperature"
BKIND_INV   = "inversion_strength"
BKIND_IND   = "inversion_depth"
BKIND_ICON  = "ice_concentration"
BKIND_NDVI  = "ndvi"
BKIND_TPW   = "total_precipitable_water"

# Band Identifier
BID_01 = "01"
BID_02 = "02"
BID_03 = "03"
BID_04 = "04"
BID_05 = "05"
BID_06 = "06"
BID_07 = "07"
BID_08 = "08"
BID_09 = "09"
BID_10 = "10"
BID_11 = "11"
BID_12 = "12"
BID_13 = "13"
BID_14 = "14"
BID_15 = "15"
BID_16 = "16"
BID_FOG = "fog"
BID_20 = "20"
BID_26 = "26"
BID_27 = "27"
BID_31 = "31"

# Data kinds
DKIND_LATITUDE    = "latitude"
DKIND_LONGITUDE   = "longitude"
DKIND_RADIANCE    = "radiance"
DKIND_REFLECTANCE = "reflectance"
DKIND_BTEMP       = "btemp"
DKIND_FOG         = "fog"
DKIND_CATEGORY    = "category"
DKIND_ANGLE       = "angle"
DKIND_DISTANCE    = "distance" # this is meant to be a distance in the sense of mm, cm, meters, km, or miles
DKIND_PERCENT     = "percent"
DKIND_C_INDEX     = "contiguous_index" # this represents some abstract ranging index with meaningfully contiguous values (not discrete categories)

# Grid Constants
GRIDS_ANY = "any_grid"
GRIDS_ANY_GPD = "any_gpd_grid"
GRIDS_ANY_PROJ4 = "any_proj4_grid"
GRID_KIND_GPD = "gpd"
GRID_KIND_PROJ4 = "proj4"

### Return Status Values ###
STATUS_SUCCESS       = 0
# the frontend failed
STATUS_FRONTEND_FAIL = 1
# the backend failed
STATUS_BACKEND_FAIL  = 2
# either ll2cr or fornav failed (4 + 8)
STATUS_REMAP_FAIL    = 12
# ll2cr failed
STATUS_LL2CR_FAIL    = 4
# fornav failed
STATUS_FORNAV_FAIL   = 8
# grid determination or grid jobs creation failed
STATUS_GDETER_FAIL   = 16
# not sure why we failed, not an expected failure
STATUS_UNKNOWN_FAIL  = -1


