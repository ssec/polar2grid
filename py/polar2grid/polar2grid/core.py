#!/usr/bin/env python
# encoding: utf-8
""" Core of viirs2awips that holds shared utilities and constants.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"
import numpy

import os
import logging
from glob import glob
import datetime

log = logging.getLogger(__name__)

# Constants
# Data kinds
K_LATITUDE = 'LatitudeVar'
K_LONGITUDE = 'LongitudeVar'
K_RADIANCE = 'RadianceVar'
K_REFLECTANCE = 'ReflectanceVar'
K_BTEMP = "BrightnessTemperatureVar"
K_SOLARZENITH = "SolarZenithVar"
K_FOG = "FogPseudoBand"

# Other variables
K_ALTITUDE = 'AltitudeVar'
K_RADIANCE_FACTORS = "RadianceFactorsVar"
K_REFLECTANCE_FACTORS = "ReflectanceFactorsVar"
K_BTEMP_FACTORS = "BrightnessTemperatureFactorsVar"
K_STARTTIME = "StartTimeVar"
K_MODESCAN = "ModeScanVar"
K_MODEGRAN = "ModeGranVar"
K_QF3 = "QF3Var"
K_NAVIGATION = 'NavigationFilenameGlob'  # glob to search for to find navigation file that corresponds
K_GEO_REF = 'CdfcbGeolocationFileGlob' # glob which would match the N_GEO_Ref attribute

class UTC(datetime.tzinfo):
    """Time zone class for UTC
    """
    ZERO = datetime.timedelta(0)
    def utcoffset(self, dt):
        return self.ZERO
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return self.ZERO

def utc_now():
    return datetime.datetime.utcnow().replace(tzinfo=UTC())

str_to_dtype = {
        "real4" : numpy.float32,
        "int1"  : numpy.int8,
        "uint1" : numpy.uint8
        }

class Workspace(object):
    """Wrapper object around ``numpy.fromfile()`` method to treat a directory as a
    workspace of flat binary files.

    :attention: Replaces rayg's ``keoni.fbf.Workspace``
    """
    def __init__(self, dir='.'):
        self._dir=dir

    def _parse_attr_name(self, name):
        """Take a FBF formatted filename and parse out the binary data
        details such as number of rows/cols and data type.

        :Parameters:
            name : str
                Flat binary formatted name (ex. image_I01.real4.6400.10167).
        """
        fullpath = os.path.abspath(name)
        filename = os.path.split(fullpath)[1]
        parts = filename.split(".")
        if len(parts) != 4:
            log.error("Found filename %s with incorrect format, need 4 parts" % filename)
            raise ValueError("Found filename %s with incorrect format, need 4 parts" % filename)

        attr_name,type,cols,rows = parts
        if type not in str_to_dtype:
            log.error("Don't know how to interpret data type %s from %s" % (type,filename))
            raise ValueError("Don't know how to interpret data type %s from %s" % (type,filename))
        dtype = str_to_dtype[type]

        try:
            cols = int(cols)
            rows = int(rows)
        except ValueError:
            log.error("Columns and rows must be integers not (%s,%s)" % (str(cols),str(rows)))
            raise ValueError("Columns and rows must be integers not (%s,%s)" % (str(cols),str(rows)))

        return attr_name,dtype,cols,rows

    def __getattr__(self, name, mode='r'):
        g = glob( os.path.join(self._dir,name+'.*') )
        if len(g)==1:
            attr_name,dtype,cols,rows = self._parse_attr_name(g[0])
            mmap_arr = numpy.memmap(g[0], dtype=dtype, mode=mode, shape=(rows,cols))
            setattr(self,name,mmap_arr)
            return mmap_arr
        elif len(g) > 1:
            raise AttributeError("Found too many instances for %s in workspace" % name)
        else:
            raise AttributeError("%s not in workspace" % name)
        
    def var(self,name):
        return getattr(self, name)
    
    def vars(self):
        for path in os.listdir(self._dir):
            try:
                fullpath = os.path.join(self._dir, path)
                stemname,_,_,_ = self._parse_attr_name(fullpath)
                yield stemname, self.__getattr__(stemname)
            except:
                pass
            
    def variables(self):
        return dict(self.vars())

    def __getitem__(self,name):
        return getattr(self,name)


