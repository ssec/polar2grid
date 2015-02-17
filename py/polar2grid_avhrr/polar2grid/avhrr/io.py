#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2015 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    February 2015
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""File access to AVHRR files.

The majority of the AVHRR format and how it is accessed was taken from the mpop package created by the PyTroll group
and is copywritten by SMHI.
https://github.com/mraspaud/mpop

:author:       David Hoese (davidh)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2015 University of Wisconsin SSEC. All rights reserved.
:date:         Feb 2015
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

import os
import sys
import logging
import numpy as np
from datetime import datetime

from polar2grid.core.frontend_utils import BaseFileReader, BaseMultiFileReader

LOG = logging.getLogger(__name__)

FT_AAPP = "FT_AAPP"
FT_NOAA = "FT_NOAA"

AVHRR_CHANNEL_NAMES = ("1", "2", "3A", "3B", "4", "5")

# AAPP 1b header
_HEADERTYPE = np.dtype([("siteid", "S3"),
                        ("blank", "S1"),
                        ("l1bversnb", "<i2"),
                        ("l1bversyr", "<i2"),
                        ("l1bversdy", "<i2"),
                        ("reclg", "<i2"),
                        ("blksz", "<i2"),
                        ("hdrcnt", "<i2"),
                        ("filler0", "S6"),
                        ("dataname", "S42"),
                        ("prblkid", "S8"),
                        ("satid", "<i2"),
                        ("instid", "<i2"),
                        ("datatype", "<i2"),
                        ("tipsrc", "<i2"),
                        ("startdatajd", "<i4"),
                        ("startdatayr", "<i2"),
                        ("startdatady", "<i2"),
                        ("startdatatime", "<i4"),
                        ("enddatajd", "<i4"),
                        ("enddatayr", "<i2"),
                        ("enddatady", "<i2"),
                        ("enddatatime", "<i4"),
                        ("cpidsyr", "<i2"),
                        ("cpidsdy", "<i2"),
                        ("filler1", "S8"),
                        # data set quality indicators
                        ("inststat1", "<i4"),
                        ("filler2", "S2"),
                        ("statchrecnb", "<i2"),
                        ("inststat2", "<i4"),
                        ("scnlin", "<i2"),
                        ("callocscnlin", "<i2"),
                        ("misscnlin", "<i2"),
                        ("datagaps", "<i2"),
                        ("okdatafr", "<i2"),
                        ("pacsparityerr", "<i2"),
                        ("auxsyncerrsum", "<i2"),
                        ("timeseqerr", "<i2"),
                        ("timeseqerrcode", "<i2"),
                        ("socclockupind", "<i2"),
                        ("locerrind", "<i2"),
                        ("locerrcode", "<i2"),
                        ("pacsstatfield", "<i2"),
                        ("pacsdatasrc", "<i2"),
                        ("filler3", "S4"),
                        ("spare1", "S8"),
                        ("spare2", "S8"),
                        ("filler4", "S10"),
                        # Calibration
                        ("racalind", "<i2"),
                        ("solarcalyr", "<i2"),
                        ("solarcaldy", "<i2"),
                        ("pcalalgind", "<i2"),
                        ("pcalalgopt", "<i2"),
                        ("scalalgind", "<i2"),
                        ("scalalgopt", "<i2"),
                        ("irttcoef", "<i2", (4, 6)),
                        ("filler5", "<i4", (2, )),
                        # radiance to temperature conversion
                        ("albcnv", "<i4", (2, 3)),
                        ("radtempcnv", "<i4", (3, 3)),
                        ("filler6", "<i4", (3, )),
                        # Navigation
                        ("modelid", "S8"),
                        ("nadloctol", "<i2"),
                        ("locbit", "<i2"),
                        ("filler7", "S2"),
                        ("rollerr", "<i2"),
                        ("pitcherr", "<i2"),
                        ("yawerr", "<i2"),
                        ("epoyr", "<i2"),
                        ("epody", "<i2"),
                        ("epotime", "<i4"),
                        ("smaxis", "<i4"),
                        ("eccen", "<i4"),
                        ("incli", "<i4"),
                        ("argper", "<i4"),
                        ("rascnod", "<i4"),
                        ("manom", "<i4"),
                        ("xpos", "<i4"),
                        ("ypos", "<i4"),
                        ("zpos", "<i4"),
                        ("xvel", "<i4"),
                        ("yvel", "<i4"),
                        ("zvel", "<i4"),
                        ("earthsun", "<i4"),
                        ("filler8", "S16"),
                        # analog telemetry conversion
                        ("pchtemp", "<i2", (5, )),
                        ("reserved1", "<i2"),
                        ("pchtempext", "<i2", (5, )),
                        ("reserved2", "<i2"),
                        ("pchpow", "<i2", (5, )),
                        ("reserved3", "<i2"),
                        ("rdtemp", "<i2", (5, )),
                        ("reserved4", "<i2"),
                        ("bbtemp1", "<i2", (5, )),
                        ("reserved5", "<i2"),
                        ("bbtemp2", "<i2", (5, )),
                        ("reserved6", "<i2"),
                        ("bbtemp3", "<i2", (5, )),
                        ("reserved7", "<i2"),
                        ("bbtemp4", "<i2", (5, )),
                        ("reserved8", "<i2"),
                        ("eleccur", "<i2", (5, )),
                        ("reserved9", "<i2"),
                        ("motorcur", "<i2", (5, )),
                        ("reserved10", "<i2"),
                        ("earthpos", "<i2", (5, )),
                        ("reserved11", "<i2"),
                        ("electemp", "<i2", (5, )),
                        ("reserved12", "<i2"),
                        ("chtemp", "<i2", (5, )),
                        ("reserved13", "<i2"),
                        ("bptemp", "<i2", (5, )),
                        ("reserved14", "<i2"),
                        ("mhtemp", "<i2", (5, )),
                        ("reserved15", "<i2"),
                        ("adcontemp", "<i2", (5, )),
                        ("reserved16", "<i2"),
                        ("d4bvolt", "<i2", (5, )),
                        ("reserved17", "<i2"),
                        ("d5bvolt", "<i2", (5, )),
                        ("reserved18", "<i2"),
                        ("bbtempchn3B", "<i2", (5, )),
                        ("reserved19", "<i2"),
                        ("bbtempchn4", "<i2", (5, )),
                        ("reserved20", "<i2"),
                        ("bbtempchn5", "<i2", (5, )),
                        ("reserved21", "<i2"),
                        ("refvolt", "<i2", (5, )),
                        ("reserved22", "<i2"),
                        ])

# AAPP 1b scanline
_SCANTYPE = np.dtype([("scnlin", "<i2"),
                      ("scnlinyr", "<i2"),
                      ("scnlindy", "<i2"),
                      ("clockdrift", "<i2"),
                      ("scnlintime", "<i4"),
                      ("scnlinbit", "<i2"),
                      ("filler0", "S10"),
                      ("qualind", "<i4"),
                      ("scnlinqual", "<i4"),
                      ("calqual", "<i2", (3, )),
                      ("cbiterr", "<i2"),
                      ("filler1", "S8"),
                      # Calibration
                      ("calvis", "<i4", (3, 3, 5)),
                      ("calir", "<i4", (3, 2, 3)),
                      ("filler2", "<i4", (3, )),
                      # Navigation
                      ("navstat", "<i4"),
                      ("attangtime", "<i4"),
                      ("rollang", "<i2"),
                      ("pitchang", "<i2"),
                      ("yawang", "<i2"),
                      ("scalti", "<i2"),
                      ("ang", "<i2", (51, 3)),
                      ("filler3", "<i2", (3, )),
                      ("pos", "<i4", (51, 2)),
                      ("filler4", "<i4", (2, )),
                      ("telem", "<i2", (103, )),
                      ("filler5", "<i2"),
                      ("hrpt", "<i2", (2048, 5)),
                      ("filler6", "<i4", (2, )),
                      # tip minor frame header
                      ("tipmfhd", "<i2", (7, 5)),
                      # cpu telemetry
                      ("cputel", "S6", (2, 5)),
                      ("filler7", "<i2", (67, )),
                      ])


class AVHRRReader(object):
    """Basic file reader for AVHRR files.
    """
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.filepath = os.path.realpath(filename)

        with open(self.filename, "rb") as fp_:
            header = np.memmap(fp_, dtype=_HEADERTYPE, mode="r", shape=(_HEADERTYPE.itemsize,))
            data = np.memmap(fp_, dtype=_SCANTYPE, offset=22016, mode="r")


        self._header = header
        self._data = data

    def __contains__(self, key):
        return key in _SCANTYPE.names or key in _HEADERTYPE.names

    def __getitem__(self, key):
        """Get HDF5 variable, making it easier to access attributes.
        """
        try:
            return self._data[key]
        except KeyError:
            return self._header[key]


class AVHRRSingleFileReader(BaseFileReader):
    def __init__(self, file_handle, file_type_info):
        super(AVHRRSingleFileReader, self).__init__(file_handle, file_type_info)


class AVHRRMultiFileReader(BaseMultiFileReader):
    def __init__(self, file_type_info):
        super(AVHRRMultiFileReader, self).__init__(file_type_info, AVHRRSingleFileReader)
