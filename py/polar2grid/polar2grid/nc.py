#!/usr/bin/env python
# encoding: utf-8
"""
NetCDF utilities.

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         June 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
from xml.etree import cElementTree
from netCDF4 import Dataset

log = logging.getLogger(__name__)

_types = {
        "float" : float,
        "int" : int,
        None : str
        }

_type_str = {
        "float" : "f4",
        "int" : "i4",
        "double" : "f8",
        "byte" : "i1"
        }

def ncml_tag(t):
    return "{http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2}%s" % t

def _process_dimension(xml_parser, nc, elem, event="start", parent=None):
    new_dim = nc.createDimension(elem.get("name"), elem.get("length") and int(elem.get("length")))

    next_event,next_elem = xml_parser.next()
    while not (next_event == "end" and \
        next_elem.tag == ncml_tag("dimension") and \
        next_elem.get("name") == elem.get("name")):
        _process_element(xml_parser, nc, next_elem, event=next_event, parent=new_dim)
        next_event,next_elem = xml_parser.next()

    return

def _process_attribute(xml_parser, nc, elem, event="start", parent=None):
    # Handle attribute type and value
    setattr(parent, elem.get("name"), _types[elem.get("type")](elem.get("value")))

    next_event,next_elem = xml_parser.next()
    while not (next_event == "end" and \
        next_elem.tag == ncml_tag("attribute") and \
        next_elem.get("name") == elem.get("name")):
        # FIXME: I don't know if parent=nc would be correct here
        _process_element(xml_parser, nc, next_elem, event=next_event, parent=nc)
        next_event,next_elem = xml_parser.next()

    return

def _process_variable(xml_parser, nc, elem, event="start", parent=None):
    if elem.get("shape"):
        dims = tuple(elem.get("shape").split(" "))
        new_var = nc.createVariable(elem.get("name"), _type_str[elem.get("type")], dims)
    else:
        new_var = nc.createVariable(elem.get("name"), _type_str[elem.get("type")])
    new_var.set_auto_maskandscale(False)
    new_var[:] = 0

    next_event,next_elem = xml_parser.next()
    while not (next_event == "end" and \
        next_elem.tag == ncml_tag("variable") and \
        next_elem.get("name") == elem.get("name")):
        _process_element(xml_parser, nc, next_elem, event=next_event, parent=new_var)
        next_event,next_elem = xml_parser.next()

    return None

def _process_element(xml_parser, nc, elem, event="start", parent=None):
    if elem.tag == "end":
        log.warning("Something went wrong, we shouldn't be parsing an 'end' tag")
        return
    if elem.tag == ncml_tag("dimension"):
        _process_dimension(xml_parser, nc, elem, event=event, parent=parent)
    elif elem.tag == ncml_tag("attribute"):
        _process_attribute(xml_parser, nc, elem, event=event, parent=parent)
    elif elem.tag == ncml_tag("variable"):
        _process_variable(xml_parser, nc, elem, event=event, parent=parent)
    elif elem.tag == ncml_tag("netcdf"):
        pass
    else:
        log.error("Unknown NCML element found (%r)" % (elem))
        raise ValueError("Unknown NCML element found (%r)" % (elem))

def create_nc_from_ncml(nc_filename, ncml_filename, format="NETCDF3_CLASSIC"):
    """Take a NCML file and create a NetCDF file filled with the attributes
    and variables listed in the NCML file.

    """
    if os.path.exists(nc_filename):
        log.warning("Overwriting NC file %s" % nc_filename)

    xml_parser = cElementTree.iterparse(ncml_filename, events=("start", "end"))
    nc = Dataset(nc_filename, "w", format=format)
    for event,elem in xml_parser:
        _process_element(xml_parser, nc, elem, event=event, parent=nc)

    return nc

def main():
    #import doctest
    #return doctest.testmod()
    logging.basicConfig(level=logging.DEBUG)
    return create_nc_from_ncml(sys.argv[2], sys.argv[1])

if __name__ == "__main__":
    sys.exit(main())

