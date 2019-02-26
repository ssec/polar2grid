#!/usr/bin/env python3
# encoding: utf-8
"""
Extract IASI data to flat binary files in a similar form to AIRS ROK MATLAB script.

spectralFreq.real4.WWWW # wavenumbers
radiances.real4.WWWW # radiance data
time.real4       # time of day in decimal hours?
latitude.real4   # latitude in northward degrees
longitude.real4  # longitude in eastward degrees
scanAng.real4
landFrac.real4
elevation.real4  # -optional elevation (units?)
solar_zenith_angle # degrees
satellite_zenith_angle # degrees
solar_azimuth_angle # degrees
satellite_azimuth_angle # degrees
quality_flag # 0 for good, nonzero bad, integer


:author:       Ray Garcia (rayg)
:contact:      rayg@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Mar 2013
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
"""

__docformat__ = "restructuredtext en"

import logging, os, sys
from .swath import extract_sounding, extract_retrieval

LOG = logging.getLogger(__name__)

#
#
# iasi2fbf support
#
#


def main():
    import optparse
    usage = """usage: %prog [options] list-of-input-files
$Id: fbf.py 51 2011-05-27 20:06:46Z rayg $
This program extracts IASI data to flat binary files using the EUGENE toolkit.
It can output in two main geometries: record-by-record or scan-lines (-L option)
In scan-line mode, data is presented geographically contiguously.
If all detectors are requested, the detectors are geographically deinterleaved
to create 'pseudo-scan-lines', each containing two of the four detectors.
UNIX epoch time is included in the output, as well as detector number and scan number.
Unless otherwise specified, output is zero-based instead of one-based.
"""
    logging.basicConfig()

    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-d', '--detector', dest="detector", type="int", default=None,
                    help="optional: detector number, 0..3; default is all detectors")
    parser.add_option('-L', '--lines', dest='lines', default=False, action='store_true',
                    help="optional: enable extraction of a scan line at a time (three dimensional output)")
    parser.add_option('-R', '--no-radiances', dest='no_radiances', default=False, action='store_true',
                    help="optional: disable output of radiance data")
    parser.add_option('-S', '--scans', dest='scans', default=None,
                    help="optional: range of scan lines to export, starting from 0 e.g. -S 0-13")
    parser.add_option('-T', '--retrieval', dest='retrieval', default=False, action='store_true',
                    help='extract from a SND format retrieval file')
    parser.add_option("-C", "--cloud", dest="read_cloud_mask_files", default=False, action='store_true',
                    help="look for mask_*.pickle files with cloud mask data (see iasi_cloud_extract)")
    parser.add_option("-M", "--iasimask", dest="cloud_mask_filename",
                    help="cloud mask file to load e.g. iasimask_*.txt")
    parser.add_option("-I", "--iis", dest="iis_tiles", default=False, action='store_true',
                    help="include IIS 64x64 image tiles in output dimensioned as [scanline,field,x,y]")
    parser.add_option("-o", "--output", dest="output",
                    help="required: output directory name (will be created)")
    parser.add_option('-v', '--verbose', dest="verbose",
                    action="store_true", default=False, help="enable debug output")
    parser.add_option('-q', '--quiet', dest="quiet",
                    action="store_true", default=False, help="only warning and error output")
    (options, args) = parser.parse_args()

    lvl = logging.INFO
    if options.verbose: lvl = logging.DEBUG
    elif options.quiet: lvl = logging.WARNING
    LOG.setLevel(lvl)

    if options.self_test:
        import doctest
        doctest.testmod()
        sys.exit(2)

    if len(args) < 1 or not options.output:
        parser.error("incorrect arguments. try --help or -h")
    else:
        if options.scans is not None:
            lal = [int(x) for x in options.scans.split('-')]
            first,last = lal[0], lal[-1]
            scans = range(first,last+1)
        else:
            scans = None
        ignore = set()
        if options.no_radiances: ignore.add('radiances')  # prevents radiances files from being created in FBF writer

        if not options.retrieval:
            extract_sounding( options.output, options.detector, options.lines,
                                options.read_cloud_mask_files, options.cloud_mask_filename,
                                scans, options.iis_tiles, ignore, *args )
        else:
            assert( options.read_cloud_mask_files != True )
            extract_retrieval( options.output, ignore, *args )



if __name__=='__main__':
    sys.exit(main())

