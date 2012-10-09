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

# Projection tools
def from_proj4(proj4_str):
    proj4_elements = proj4_str.split(" ")
    proj4_dict = dict([ y.split("=") for y in [ x.strip("+") for x in proj4_elements ] ])
    return proj4_dict

def to_proj4(proj4_dict):
    """Convert a dictionary of proj4 parameters back into a proj4 string.

    >>> proj4_str = "+proj=lcc +a=123456 +b=12345"
    >>> proj4_dict = from_proj4(proj4_str)
    >>> new_proj4_str = to_proj4(proj4_dict)
    >>> assert(new_proj4_str == proj4_str)
    """
    # Make sure 'proj' is first, some proj4 parsers don't accept it otherwise
    proj4_str = "+proj=%s" % proj4_dict.pop("proj")
    proj4_str = proj4_str + " " + " ".join(["+%s=%s" % (k,str(v)) for k,v in proj4_dict.items()])
    return proj4_str

def clean_string(s):
    s = s.replace("-", "")
    s = s.replace("(", "")
    s = s.replace(")", "")
    s = s.replace(" ", "")
    s = s.upper()
    return s

def remove_comments(s, comment=";"):
    s = s.strip()
    c_idx = s.find(comment)
    if c_idx != -1:
        return s[:c_idx].strip()
    return s

gpd_conv_funcs = {
        # gpd file stuff:
        "GRIDWIDTH" : int,
        "GRIDHEIGHT" : int,
        "GRIDMAPUNITSPERCELL" : float,
        "GRIDCELLSPERMAPUNIT" : float,
        # mpp file stuff:
        "MAPPROJECTION" : clean_string,
        "MAPREFERENCELATITUDE" : float,
        "MAPSECONDREFERENCELATITUDE" : float,
        "MAPREFERENCELONGITUDE" : float,
        "MAPEQUATORIALRADIUS" : float,
        "MAPPOLARRADIUS" : float,
        "MAPORIGINLATITUDE" : float,
        "MAPORIGINLONGITUDE" : float,
        "MAPECCENTRICITY" : float,
        "MAPECCENTRICITYSQUARED" : float,
        "MAPFALSEEASTING" : float,
        "MAPSCALE" : float
        }

def _parse_gpd(gpd_file):
    gpd_dict = {}
    for line in gpd_file:
        line_parts = line.split(":")
        if len(line_parts) != 2:
            log.error("Incorrect gpd syntax: more than one ':' ('%s')" % line)
        key = clean_string(line_parts[0])
        val = remove_comments(line_parts[1])

        if key not in gpd_conv_funcs:
            log.error("Can't parse gpd file, don't know how to handle key '%s'" % key)
            raise ValueError("Can't parse gpd file, don't know how to handle key '%s'" % key)
        conv_func = gpd_conv_funcs[key]
        val = conv_func(val)
        gpd_dict[key] = val
    return gpd_dict

gpd_proj_to_proj4 = {
        "ALBERSCONICEQUALAREA" : "aea",
        "AZIMUTHALEQUALAREA" : None,
        "AZIMUTHALEQUALAREAELLIPSOID" : None,
        "CYLINDRICALEQUALAREA" : "cea",
        "CYLINDRICALEQUALAREAELLIPSOID" : None,
        "CYLINDRICALEQUIDISTANT" : "eqc",
        "INTEGERIZEDSINUSOIDAL" : None,
        "INTERRUPTEDHOMOLOSINEEQUALAREA" : "igh",
        "LAMBERTCONICCONFORMALELLIPSOID" : "lcc",
        "MERCATOR" : "merc",
        "MOLLWEIDE" : "moll",
        "ORTHOGRAPHIC" : "ortho",
        "POLARSTEREOGRAPHIC" : "ups",
        "POLARSTEREOGRAPHICELLIPSOID" : "ups",
        "SINUSOIDAL" : None,
        "TRANSVERSEMERCATOR" : "tmerc",
        "TRANSVERSEMERCATORELLIPSOID" : None,
        "UNIVERSALTRANSVERSEMERCATOR" : "utm"
        }

gpd2proj4 = {
        # gpd file stuff:
        "GRIDWIDTH" : None,
        "GRIDHEIGHT" : None,
        "GRIDMAPUNITSPERCELL" : None,
        "GRIDCELLSPERMAPUNIT" : None,
        # mpp file stuff:
        "MAPPROJECTION" : "proj",
        "MAPREFERENCELATITUDE" : ["lat_0","lat_1"],
        "MAPSECONDREFERENCELATITUDE" : "lat_ts",
        "MAPREFERENCELONGITUDE" : "lon_0",
        "MAPEQUATORIALRADIUS" : "a",
        "MAPPOLARRADIUS" : "b",
        "MAPORIGINLATITUDE" : None,
        "MAPORIGINLONGITUDE" : None,
        "MAPECCENTRICITY" : "e",
        "MAPECCENTRICITYSQUARED" : "es",
        "MAPFALSEEASTING" : "x_0",
        "MAPSCALE" : None # ?
        }

def _gpd2proj4(gpd_dict):
    proj4_dict = {}
    for k,v in gpd_dict.items():
        if k not in gpd2proj4:
            log.error("Don't know how to convert gpd %s to proj.4" % k)
            raise ValueError("Don't know how to convert gpd %s to proj.4" % k)
        if k == "MAPPROJECTION":
            # Special case
            proj4_dict[gpd2proj4[k]] = gpd_proj_to_proj4[v]
            if proj4_dict[gpd2proj4[k]] is None:
                log.warning("Could not find equivalent proj4 projection name for %s" % v)
        elif k == "MAPREFERENCELATITUDE":
            pkey = gpd2proj4[k]
            pk1,pk2 = pkey
            proj4_dict[pk1] = v
            proj4_dict[pk2] = v
        else:
            pkey = gpd2proj4[k]
            if pkey is not None:
                proj4_dict[gpd2proj4[k]] = v

    return proj4_dict


def gpd_to_proj4(gpd_fn):
    gpd_file = open(gpd_fn, "r")
    gpd_dict = _parse_gpd(gpd_file)
    proj4_dict = _gpd2proj4(gpd_dict)
    return proj4_dict,gpd_dict

