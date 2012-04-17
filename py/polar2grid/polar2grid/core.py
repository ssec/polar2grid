"""Core of viirs2awips that holds shared utilities and constants.

FBF Workspace:
    Wrapper object around numpy's fromfile method to treat a directory as a
    workspace of flat binary files.
    Replaces rayg's pykeoni.fbf.Workspace.

Author: David Hoese,davidh,SSEC
"""
import numpy

import os
import logging
from glob import glob
import datetime

log = logging.getLogger(__name__)

# time zone class for UTC
class UTC(datetime.tzinfo):
    """UTC"""
    ZERO = datetime.timedelta(0)
    def utcoffset(self, dt):
        return self.ZERO
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return self.ZERO


str_to_dtype = {
        "real4" : numpy.float32,
        "int1"  : numpy.int8
        }

class Workspace(object):
    def __init__(self,dir='.'):
        self._dir=dir

    def _parse_attr_name(self, name):
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


