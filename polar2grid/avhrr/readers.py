#!/usr/bin/env python3
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

from datetime import datetime, timedelta
from numpy import arccos, sign, rad2deg, sqrt, arcsin

import logging
import numpy
import os
from collections import namedtuple
from polar2grid.core.frontend_utils import BaseFileReader, BaseMultiFileReader
from scipy.interpolate import splrep, splev

LOG = logging.getLogger(__name__)
EARTH_RADIUS = 6370997.0

FT_AAPP = "FT_AAPP"
FT_NOAA = "FT_NOAA"

AVHRR_CHANNEL_NAMES = ("1", "2", "3A", "3B", "4", "5")

# AAPP 1b header
_HEADERTYPE = numpy.dtype([("siteid", "S3"),
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
_SCANTYPE = numpy.dtype([("scnlin", "<i2"),
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

        with open(self.filepath, "rb") as fp_:
            header = numpy.memmap(fp_, dtype=_HEADERTYPE, mode="r", shape=(_HEADERTYPE.itemsize,))
            data = numpy.memmap(fp_, dtype=_SCANTYPE, offset=22016, mode="r")

        self._header = header
        self._data = data
        self.file_type = FT_AAPP

    def __contains__(self, key):
        return key in _SCANTYPE.names or key in _HEADERTYPE.names

    def __getitem__(self, key):
        """Get HDF5 variable, making it easier to access attributes.
        """
        try:
            return self._data[key]
        except (ValueError, KeyError):
            return self._header[key]


def _vis_calibrate(data_reader, chn, calib_type, pre_launch_coeffs=False):
    """Visible channel calibration only.
    *calib_type* = 0: Counts
    *calib_type* = 1: Reflectances
    *calib_type* = 2: Radiances
    """
    # Calibration count to albedo, the calibration is performed separately for
    # two value ranges.

    channel = data_reader["hrpt"][:, :, chn].astype(numpy.float)
    if calib_type == 0:
        return channel

    if calib_type == 2:
        LOG.warning("Radiances are not yet supported for the VIS/NIR channels!")

    if pre_launch_coeffs:
        coeff_idx = 2
    else:
        # check that coeffs are valid
        if numpy.all(data_reader["calvis"][:, chn, 0, 4] == 0):
            LOG.debug("No valid operational coefficients, fall back to pre-launch")
            coeff_idx = 2
        else:
            coeff_idx = 0

    intersection = data_reader["calvis"][:, chn, coeff_idx, 4]
    slope1 = numpy.expand_dims(data_reader["calvis"][:, chn, coeff_idx, 0] * 1e-10, 1)
    intercept1 = numpy.expand_dims(data_reader["calvis"][:, chn, coeff_idx, 1] * 1e-7, 1)
    slope2 = numpy.expand_dims(data_reader["calvis"][:, chn, coeff_idx, 2] * 1e-10, 1)
    intercept2 = numpy.expand_dims(data_reader["calvis"][:, chn, coeff_idx, 3] * 1e-7, 1)

    if chn == 2:
        slope2[slope2 < 0] += 0.4294967296

    mask1 = channel <= numpy.expand_dims(intersection, 1)
    mask2 = channel > numpy.expand_dims(intersection, 1)

    channel[mask1] = (channel * slope1 + intercept1)[mask1]

    channel[mask2] = (channel * slope2 + intercept2)[mask2]

    channel[channel < 0] = numpy.nan
    return numpy.ma.masked_invalid(channel)


def _ir_calibrate(data_reader, irchn, calib_type):
    """IR calibration
    *calib_type* = 0: Counts
    *calib_type* = 1: BT
    *calib_type* = 2: Radiances
    """

    count = data_reader['hrpt'][:, :, irchn + 2].astype(numpy.float)

    if calib_type == 0:
        return count

    # Mask unnaturally low values
    mask = count == 0.0

    k1_ = numpy.expand_dims(data_reader['calir'][:, irchn, 0, 0] / 1.0e9, 1)
    k2_ = numpy.expand_dims(data_reader['calir'][:, irchn, 0, 1] / 1.0e6, 1)
    k3_ = numpy.expand_dims(data_reader['calir'][:, irchn, 0, 2] / 1.0e6, 1)

    # Count to radiance conversion:
    rad = k1_ * count * count + k2_ * count + k3_

    all_zero = numpy.logical_and(numpy.logical_and(numpy.equal(k1_, 0),
                                             numpy.equal(k2_, 0)),
                              numpy.equal(k3_, 0))
    idx = numpy.indices((all_zero.shape[0],))
    suspect_line_nums = numpy.repeat(idx[0], all_zero[:, 0])
    if suspect_line_nums.any():
        LOG.debug("Suspicious scan lines: " + str(suspect_line_nums))

    if calib_type == 2:
        rad[mask | (rad <= 0.0)] = numpy.nan
        return numpy.ma.masked_array(rad, numpy.isnan(rad))

    # Central wavenumber:
    cwnum = data_reader['radtempcnv'][0, irchn, 0]
    if irchn == 0:
        cwnum = cwnum / 1.0e2
    else:
        cwnum = cwnum / 1.0e3

    bandcor_2 = data_reader['radtempcnv'][0, irchn, 1] / 1e5
    bandcor_3 = data_reader['radtempcnv'][0, irchn, 2] / 1e6

    ir_const_1 = 1.1910659e-5
    ir_const_2 = 1.438833

    t_planck = (ir_const_2 * cwnum) / \
        numpy.log(1 + ir_const_1 * cwnum * cwnum * cwnum / rad)

    # Band corrections applied to t_planck to get correct
    # brightness temperature for channel:
    if bandcor_2 < 0:  # Post AAPP-v4
        tb_ = bandcor_2 + bandcor_3 * t_planck
    else:  # AAPP 1 to 4
        tb_ = (t_planck - bandcor_2) / bandcor_3

    #tb_[tb_ <= 0] = np.nan
    # Data with count=0 are often related to erroneous (bad) lines, but in case
    # of saturation (channel 3b) count=0 can be observed and associated to a
    # real measurement. So we leave out this filtering to the user!
    # tb_[count == 0] = np.nan
    #tb_[rad == 0] = np.nan
    tb_[mask] = numpy.nan
    return numpy.ma.masked_array(tb_, numpy.isnan(tb_))


def interpolate_1km_geolocation(lons_40km, lats_40km):
    """Interpolate AVHRR 40km navigation to 1km.

    This code was extracted from the python-geotiepoints package from the PyTroll group. To avoid adding another
    dependency to this package this simple case from the geotiepoints was copied.
    """
    cols40km = numpy.arange(24, 2048, 40)
    cols1km = numpy.arange(2048)
    lines = lons_40km.shape[0]
    # row_indices = rows40km = numpy.arange(lines)
    rows1km = numpy.arange(lines)

    lons_rad = numpy.radians(lons_40km)
    lats_rad = numpy.radians(lats_40km)
    x__ = EARTH_RADIUS * numpy.cos(lats_rad) * numpy.cos(lons_rad)
    y__ = EARTH_RADIUS * numpy.cos(lats_rad) * numpy.sin(lons_rad)
    z__ = EARTH_RADIUS * numpy.sin(lats_rad)
    along_track_order = 1
    cross_track_order = 3

    lines = len(rows1km)
    newx = numpy.empty((len(rows1km), len(cols1km)), x__.dtype)
    newy = numpy.empty((len(rows1km), len(cols1km)), y__.dtype)
    newz = numpy.empty((len(rows1km), len(cols1km)), z__.dtype)
    for cnt in range(lines):
        tck = splrep(cols40km, x__[cnt, :], k=cross_track_order, s=0)
        newx[cnt, :] = splev(cols1km, tck, der=0)
        tck = splrep(cols40km, y__[cnt, :], k=cross_track_order, s=0)
        newy[cnt, :] = splev(cols1km, tck, der=0)
        tck = splrep(cols40km, z__[cnt, :], k=cross_track_order, s=0)
        newz[cnt, :] = splev(cols1km, tck, der=0)

    lons_1km = get_lons_from_cartesian(newx, newy)
    lats_1km = get_lats_from_cartesian(newx, newy, newz)
    return lons_1km, lats_1km


def get_lons_from_cartesian(x__, y__):
    """Get longitudes from cartesian coordinates.
    """
    return rad2deg(arccos(x__ / sqrt(x__ ** 2 + y__ ** 2))) * sign(y__)


def get_lats_from_cartesian(x__, y__, z__, thr=0.8):
    """Get latitudes from cartesian coordinates.
    """
    # if we are at low latitudes - small z, then get the
    # latitudes only from z. If we are at high latitudes (close to the poles)
    # then derive the latitude using x and y:
    lats = numpy.where((z__ < thr * EARTH_RADIUS) & (z__ > -thr * EARTH_RADIUS),
                       90 - rad2deg(arccos(z__/EARTH_RADIUS)),
                       sign(z__) * (90 - rad2deg(arcsin(sqrt(x__ ** 2 + y__ ** 2) / EARTH_RADIUS))))
    return lats


def geolocation_calibration(data_reader, chn, calib_type):
    """Special function to hide the fact that we need to interpolate 40km resolution geolocation to 1km.
    """
    # Hacked up cache
    if hasattr(data_reader, "lons_1km"):
        if chn == 0:
            return data_reader.lons_1km
        else:
            return data_reader.lats_1km

    lons_40km = data_reader["pos"][:, :, 1] * 1e-4
    lats_40km = data_reader["pos"][:, :, 0] * 1e-4
    LOG.debug("Interpolating 40km navigation to 1km...")
    lons_1km, lats_1km = interpolate_1km_geolocation(lons_40km, lats_40km)

    # save our results for when the other is requested (if lon-chn 0 now, then lat-chn 1 later)
    data_reader.lons_1km = lons_1km
    data_reader.lats_1km = lats_1km

    if chn == 0:
        return data_reader.lons_1km
    else:
        return data_reader.lats_1km


def get_band_3_mask(data_reader, chn, calib_type):
    """Get a boolean mask to determine if a pixel is band 3A or 3B.

    True if 3B, False if 3A.
    """
    # XXX: If NOAA files need processing this logic is opposite (True = 3A, False = 3B)
    return numpy.expand_dims((data_reader["scnlinbit"] & 1) == 1, 1)


class VarInfo(namedtuple("FileVar", ["var_name", "index", "scale_factor", "calibrate_func", "calibrate_level", "data_type"])):
    def __new__(cls, var_name, index=(0,), scale_factor=None, calibrate_func=None, calibrate_level=1, data_type=numpy.float32):
        return super(VarInfo, cls).__new__(cls, var_name, index, scale_factor, calibrate_func, calibrate_level, data_type)

# TODO: Add lat/lon interpolation (this module probably)

FT_AVHRR = "ft_avhrr"

K_LONGITUDE = "LongitudeVar"
K_LATITUDE = "LatitudeVar"
K_BAND1 = "Band1Var"
K_BAND2 = "Band2Var"
K_BAND3a = "Band3aVar"
K_BAND3b = "Band3bVar"
K_BAND4 = "Band4Var"
K_BAND5 = "Band5Var"
K_BAND3_MASK = "Band3MaskVar"
FILE_TYPES = {}
FILE_TYPES[FT_AAPP] = {
    K_LONGITUDE: VarInfo("pos", 0, None, geolocation_calibration),
    K_LATITUDE: VarInfo("pos", 1, None, geolocation_calibration),
    K_BAND1: VarInfo("hrpt", 0, None, _vis_calibrate),
    K_BAND2: VarInfo("hrpt", 1, None, _vis_calibrate),
    K_BAND3a: VarInfo("hrpt", 2, None, _vis_calibrate),
    K_BAND3b: VarInfo("hrpt", 0, None, _ir_calibrate), # + 2 to channel number in IR calibration functions
    K_BAND4: VarInfo("hrpt", 1, None, _ir_calibrate),
    K_BAND5: VarInfo("hrpt", 2, None, _ir_calibrate),
    K_BAND3_MASK: VarInfo("scnlinbit", None, None, get_band_3_mask, data_type=numpy.int32),
}


class AVHRRSingleFileReader(BaseFileReader):
    SAT_ID_MAP = {
        2: "noaa16",
        4: "noaa15",
        6: "noaa17",
        7: "noaa18",
        8: "noaa19",
        11: "metopb",
        12: "metopa",
        13: "metopc",
        14: "metopsim",
    }

    def __init__(self, file_handle, file_type_info):
        super(AVHRRSingleFileReader, self).__init__(file_handle, file_type_info)

        try:
            yr = self.file_handle["startdatayr"][0]
            jd = self.file_handle["startdatady"][0]
            us = int(self.file_handle["startdatatime"][0]) * 1000
            self.begin_time = datetime.strptime("%04d-%03d" % (yr, jd), "%Y-%j") + timedelta(microseconds=us)

            yr = self.file_handle["enddatayr"][0]
            jd = self.file_handle["enddatady"][0]
            us = int(self.file_handle["enddatatime"][0]) * 1000
            self.end_time = datetime.strptime("%04d-%03d" % (yr, jd), "%Y-%j") + timedelta(microseconds=us)

            self.satellite = self.SAT_ID_MAP[int(self.file_handle["satid"][0])]
            self.instrument = "avhrr"
        except (KeyError, ValueError):
            LOG.error("Could not parse basic information from AVHRR file: %s", self.file_handle.filepath)
            raise

    def __getitem__(self, item):
        known_item = self.file_type_info.get(item, item)
        if known_item is None:
            raise KeyError("Key 'None' was not found")

        # Normally these types of operations are handled in `get_swath_data`, but due to the way numpy dtypes work this
        # is handled here (where indexing can be properly handled)
        if not isinstance(known_item, str):
            # Using FileVar class
            if known_item.calibrate_func is not None:
                # wrap in array in case we don't get a basic numpy array back
                data = numpy.array(known_item.calibrate_func(self, known_item.index, known_item.calibrate_level))
            else:
                var_name = known_item.var_name
                LOG.debug("Loading %s from %s", var_name, self.filename)
                data = self.file_handle[var_name]
                data = data[known_item.index]
                if known_item.scale_factor is not None:
                    data *= known_item.scale_factor
        else:
            data = self.file_handle[known_item]

        return data

    def get_swath_data(self, item):
        return self[item]


class AVHRRMultiFileReader(BaseMultiFileReader):
    def __init__(self, file_type_info):
        super(AVHRRMultiFileReader, self).__init__(file_type_info, AVHRRSingleFileReader)
