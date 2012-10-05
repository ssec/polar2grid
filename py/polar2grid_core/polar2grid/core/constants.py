"""Module to store all constants.  Any constant needed in more than one
component, or potentially more than one part, of polar2grid should be
defined here.

Rules/Preferences:
    - All values lowercase
    - strings
    - user-legible (assume that they may be printed in log messages)
    - use == for comparison (not 'is' or 'not' or other)

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"

NOT_APPLICABLE = None

# Satellites
SAT_NPP = "npp"

# Instruments
INST_VIIRS = "viirs"

# Band Kinds
BKIND_I = "i"
BKIND_M = "m"
BKIND_DNB = "dnb"

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

# Data kinds
DKIND_LATITUDE = "LatitudeVar"
DKIND_LONGITUDE = "LongitudeVar"
DKIND_RADIANCE = "RadianceVar"
DKIND_REFLECTANCE = "ReflectanceVar"
DKIND_BTEMP = "BrightnessTemperatureVar"
DKIND_FOG = "FogPseudoBand"


