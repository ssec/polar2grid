#!/usr/bin/env python
# encoding: utf-8
"""
Read one or more contiguous in-order HDF5 VIIRS imager granules in any aggregation
Write out Swath binary files used by ms2gt tools.

:newfield revision: Revision
:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2012
:license:      GNU GPLv3
"""
__docformat__ = "restructuredtext en"
__revision__  = " $Id$"

from polar2grid.adl_guidebook import file_info,geo_info,read_file_info,read_geo_info
import numpy

import os
import sys
import logging
from glob import glob

log = logging.getLogger(__name__)

def _glob_file(pat):
    """Globs for a single file based on the provided pattern.

    :raises ValueError: if more than one file matches pattern
    """
    tmp = glob(pat)
    if len(tmp) != 1:
        log.error("There were no files or more than one fitting the pattern %s" % pat)
        raise ValueError("There were no files or more than one fitting the pattern %s" % pat)
    return tmp[0]

def get_meta_data(ifilepaths, filter=None):
    """Get all meta data for the provided data files.

    :Parameters:
        ifilepaths : list or iterator
            Filepaths for data files to be analyzed
    :Keywords:
        filter : function pointer
            Function that expects a ``finfo`` object as its only argument
            and returns True if the finfo should be accepted, False if not.
            This can be used to specify what types of bands are desired.

    :returns:
        meta_data : dict
            - kind
                kind of band
            - bands
                dictionary per band of band info containing the following keys:
                    - kind
                    - band
                    - band_name
                    - data_kind
                    - rows_per_scan
                    - fbf_swath
        image_data : dict
            Dictionary where the key is a band ('01','00',etc.) and the
            value is a list of finfo dictionaries.

    :raises ValueError:
        if there is more than one kind of band in provided filenames
    :raises ValueError:
        if after attempting to process the provided image
        filenames there was no useful data found.
    """
    ifilepaths = sorted(ifilepaths)

    # Data structures
    meta_data = {
            "bands" : {},
            "kind"   : None
            }
    image_data = {}

    # Identify the kind of these files
    kind = None

    # Get image and geonav file info
    bad_bands = []
    for fn in ifilepaths:
        if not os.path.exists(fn):
            log.error("Data file %s does not exist, will try to continue without it..." % fn)
            continue

        try:
            finfo = file_info(fn)
        except StandardError:
            log.error("There was an error getting information from filename '%s'" % fn, exc_info=1)
            log.error("Continuing without that image file...")
            continue

        if not filter(finfo):
            log.debug("File %s was filtered out" % fn)
            continue

        # Verify some information before adding any jobs
        if finfo["band"] in bad_bands:
            log.info("Couldn't add %s because a previous file of that band was bad" % fn)
            continue

        # Geonav file exists
        geo_glob = finfo["geo_glob"]
        try:
            finfo["geo_path"] = _glob_file(geo_glob)
        except ValueError:
            log.error("Couldn't identify geonav file for %s" % fn)
            log.error("Continuing without that band...")
            bad_bands.append(finfo["band"])
            continue

        # Make sure all files are of the same kind
        if kind is None:
            kind = finfo["kind"]
        elif finfo["kind"] != kind:
            log.error("Inconsistent band kinds in the files provided")
            raise ValueError("Inconsistent band kinds in the files provided")

        # Create any locations that don't exist yet
        if finfo["band"] not in image_data:
            # Fill in data structure
            image_data[finfo["band"]] = []
            meta_data["bands"][finfo["band"]] = {
                    "kind"          : finfo["kind"],
                    "band"          : finfo["band"],
                    "band_name"     : finfo["kind"] + finfo["band"],
                    "data_kind"     : finfo["data_kind"],
                    "rows_per_scan" : finfo["rows_per_scan"],
                    "fbf_swath"     : None
                    }

        # Add it to the proper locations for future use
        image_data[finfo["band"]].append(finfo)

    # SANITY CHECK
    if len(image_data) == 0:
        log.error("There aren't any bands left to work on, quitting...")
        raise ValueError("There aren't any bands left to work on, quitting...")

    meta_data["kind"] = kind
    return meta_data,image_data

def get_geo_meta(gfilepaths):
    """Get all meta data from the geo-navigation files provided.

    :Parameters:
        gfilepaths : list
            Filepaths for geo-navigation files to be processed

    :returns:
        meta_data : dict
            Dictionary of meta data derived from the provided filepaths.
            Contains the following keys:

                - start_dt
                - swath_rows
                - swath_cols
                - rows_per_scan
                - fbf_lat
                - fbf_lon
                - fbf_mode

        geo_data : list
            List of ginfo dictionaries that can be used to read the
            associated geonav files.

    :attention:
        Just because a key if put in the meta_data dictionary
        does not necessarily mean that that data will be valid or filled
        in after this function has returned.  It will probably be filled
        in during a later step in the swath extraction process.

    :raises ValueError:
        if there is an error processing one of the geonav files.
    """
    geo_data = []
    meta_data = {
            "start_dt"  : None,
            "swath_rows"  : None,
            "swath_cols"  : None,
            "rows_per_scan" : None,
            "fbf_lat"   : None,
            "fbf_lon"   : None,
            "fbf_mode"  : None
            }

    for gname in gfilepaths:
        # Get lat/lon information
        try:
            ginfo = geo_info(gname)
        except StandardError:
            log.error("Error analyzing geonav filename %s" % gname)
            raise ValueError("Error analyzing geonav filename %s" % gname)

        # Add meta data to the meta_data dictionary
        if meta_data["rows_per_scan"] is None:
            meta_data["rows_per_scan"] = ginfo["rows_per_scan"]

        geo_data.append(ginfo)

    return meta_data,geo_data

def process_geo(meta_data, geo_data, cut_bad=False):
    """Read data from the geonav files and put them all
    into 3 concatenated swath files.  One for latitude data, one for
    longitude data, and one for mode (day/night masks) data.
    Has the option of cutting out bad data scans, see ``cut_bad`` below.

    Will add/fill in the following information into the meta_data dictionary:
        - start_dt
            Datetime object of the first middle scan time of the
            first granule
        - fbf_lat
            Filename of the flat binary file with latitude data
        - fbf_lon
            Filename of the flat binary file with longitude data
        - fbf_mode
            Filename of the flat binary file with mode data
        - swath_rows
            Number of rows in the concatenated swath
        - swath_cols
            Number of cols in the concatenated swath
        - swath_scans
            Number of scans in the concatenated swath, which is
            equal to ``swath_rows / rows_per_scan``

    :Parameters:
        meta_data : dict
            The meta data dictionary from `get_meta_data`
        geo_data : list
            The list of ``ginfo`` dictionaries from `get_geo_meta`
    :Keywords:
        cut_bad : bool
            Specify whether or not to remove entire scans of data
            when the scan is found to have bad data.  This is done
            because the ms2gt utilities don't know how to handle
            bad geonav data properly.

    :raises ValueError: if there is an error reading in the data from the file
    """
    # Write lat/lon data to fbf files
    # Create fbf files
    spid = '%d' % os.getpid()
    latname = '.lat' + spid
    lonname = '.lon' + spid
    modename = '.mode' + spid
    lafo = file(latname, 'wb')
    lofo = file(lonname, 'wb')
    modefo = file(modename, 'wb')
    lafa = file_appender(lafo, dtype=numpy.float32)
    lofa = file_appender(lofo, dtype=numpy.float32)
    modefa = file_appender(modefo, dtype=numpy.int8)

    for ginfo in geo_data:
        # Read in lat/lon data
        try:
            read_geo_info(ginfo)
            # Start datetime used in product backend for NC creation
            if meta_data["start_dt"] is None:
                meta_data["start_dt"] = ginfo["start_dt"]
        except StandardError:
            # Can't continue without lat/lon data
            log.error("Error reading data from %s for band kind %s" % (ginfo["geo_path"],meta_data["kind"]), exc_info=1)
            raise ValueError("Error reading data from %s for band kind %s" % (ginfo["geo_path"],meta_data["kind"]))

        # ll2cr/fornav hate entire scans that are bad
        scan_quality = ginfo["scan_quality"]
        if cut_bad and len(scan_quality[0]) != 0:
            ginfo["lat_data"] = numpy.delete(ginfo["lat_data"], scan_quality, axis=0)
            ginfo["lon_data"] = numpy.delete(ginfo["lon_data"], scan_quality, axis=0)
            ginfo["mode_mask"] = numpy.delete(ginfo["mode_mask"], scan_quality, axis=0)

        # Append the data to the swath
        lafa.append(ginfo["lat_data"])
        lofa.append(ginfo["lon_data"])
        modefa.append(ginfo["mode_mask"])
        del ginfo["lat_data"]
        del ginfo["lon_data"]
        del ginfo["lat_mask"]
        del ginfo["lon_mask"]
        del ginfo["mode_mask"]

    lafo.close()
    lofo.close()
    modefo.close()

    # Rename files
    suffix = '.real4.' + '.'.join(str(x) for x in reversed(lafa.shape))
    suffix2 = '.int1.' + '.'.join(str(x) for x in reversed(modefa.shape))
    fbf_lat_var = "latitude_%s" % meta_data["kind"]
    fbf_lon_var = "longitude_%s" % meta_data["kind"]
    fbf_mode_var = "mode_%s" % meta_data["kind"]
    fbf_lat = fbf_lat_var + suffix
    fbf_lon = fbf_lon_var + suffix
    fbf_mode = fbf_mode_var + suffix2
    os.rename(latname, fbf_lat)
    os.rename(lonname, fbf_lon)
    os.rename(modename, fbf_mode)

    meta_data["fbf_lat"] = fbf_lat
    meta_data["fbf_lon"] = fbf_lon
    meta_data["fbf_mode"] = fbf_mode
    swath_rows,swath_cols = lafa.shape
    meta_data["swath_rows"] = swath_rows
    meta_data["swath_cols"] = swath_cols
    meta_data["swath_scans"] = swath_rows/meta_data["rows_per_scan"]

    return meta_data,geo_data

def process_image(meta_data, image_data, geo_data, cut_bad=False):
    """Read the image data from hdf files and concatenated them
    into 1 swath file.  Has the option to cut out bad data if
    bad navigation data was found, see ``cut_bad`` below.

    :Parameters:
        meta_data : dict
            The meta data dictionary from `get_meta_data`, that's been updated
            through the entire swath extraction process.
        image_data : dict
            Per band dictionary of ``finfo`` dictionary objects from
            `get_meta_data`.
        geo_data : list
            List of ``ginfo`` dictionaries from `get_geo_meta`.
    :Keywords:
        cut_bad : bool
            Specify whether or not to remove entire scans of data
            when the geonav scan is found to have bad data.  This is done
            because the ms2gt utilities don't know how to handle
            bad geonav data properly.

    Information that is updated in the meta data per band dictionary:
        - fbf_img
            Filename of the flat binary file of image data
        - swath_rows
            Number of rows in the swath
        - swath_cols
            Number of columns in the swath
        - swath_scans
            Number of scans in the swath
        - fbf_mode
            Filename of the flat binary file of mode data from `process_geo`
    """
    # Get image data and save it to an fbf file
    for band,finfos in image_data.items():
        band_meta = meta_data["bands"][band]

        # Create fbf files and appenders
        spid = '%d' % os.getpid()
        imname = '.image' + spid
        imfo = file(imname, 'wb')
        imfa = file_appender(imfo, dtype=numpy.float32)

        # Get the data
        for finfo,ginfo in zip(finfos,geo_data):
            try:
                # XXX: May need to pass the lat/lon masks
                read_file_info(finfo)
            except StandardError:
                log.error("Error reading data from %s" % finfo["img_path"], exc_info=1)
                log.error("Removing entire job associated with this file")
                del image_data[band]
                if len(image_data) == 0:
                    # We are out of jobs
                    log.error("The last job was removed, no more to do, quitting...")
                    raise ValueError("The last job was removed, no more to do, quitting...")
                # Continue on with the next band
                break

            # Cut out bad data
            if cut_bad and len(ginfo["scan_quality"][0]) != 0:
                log.info("Removing %d bad scans from %s" % (len(ginfo["scan_quality"][0])/finfo["rows_per_scan"], finfo["img_path"]))
                finfo["image_data"] = numpy.delete(finfo["image_data"], ginfo["scan_quality"], axis=0)

            # Append the data to the file
            imfa.append(finfo["image_data"])

            # Remove pointers to data so it gets garbage collected
            del finfo["image_data"]
            del finfo["image_mask"]
            del finfo["scan_quality"]
            del finfo

        suffix = '.real4.' + '.'.join(str(x) for x in reversed(imfa.shape))
        img_base = "image_%s" % band_meta["band_name"]
        fbf_img = img_base + suffix
        os.rename(imname, fbf_img)
        band_meta["fbf_img"] = fbf_img
        rows,cols = imfa.shape
        band_meta["swath_rows"] = rows
        band_meta["swath_cols"] = cols
        band_meta["swath_scans"] = meta_data["swath_scans"]
        band_meta["fbf_mode"] = meta_data["fbf_mode"]

        if ("swath_rows" in meta_data and "swath_cols" in meta_data) and \
                (meta_data["swath_rows"] is not None and meta_data["swath_cols"] is not None) and \
                (rows != meta_data["swath_rows"] or cols != meta_data["swath_cols"]):
            log.error("Expected %d rows and %d cols, but band %s had %d rows and %d cols" % (meta_data["swath_rows"], meta_data["swath_cols"], band_meta["band_name"], rows, cols))
            log.error("Removing that band from future meta data")
            del meta_data["bands"][band]
            del image_data[band]
            if len(meta_data["bands"]) == 0:
                log.error("No more bands to process for %s bands provided" % meta_data["kind"])
                raise ValueError("No more bands to process for %s bands provided" % meta_data["kind"])

        imfo.close()
        del imfa
        del finfos

class array_appender(object):
    """wrapper for a numpy array object which gives it a binary data append usable with "catenate"
    """
    A = None
    shape = (0,0)
    def __init__(self, nparray = None):
        if nparray:
            self.A = nparray
            self.shape = nparray.shape

    def append(self, data):
        # append new rows to the data
        if self.A is None:
            self.A = numpy.array(data)
            self.shape = data.shape
        else:
            self.A = numpy.concatenate((self.A, data))
            self.shape = self.A.shape
        log.debug('array shape is now %s' % repr(self.A.shape))


class file_appender(object):
    """wrapper for a file object which gives it a binary data append usable with "catenate"
    """
    F = None
    shape = (0,0)
    def __init__(self, file_obj, dtype):
        self.F = file_obj
        self.dtype = dtype

    def append(self, data):
        # append new rows to the data
        if data is None:
            return
        inform = data.astype(self.dtype) if self.dtype != data.dtype else data
        inform.tofile(self.F)
        self.shape = (self.shape[0] + inform.shape[0], ) + data.shape[1:]
        log.debug('%d rows in output file' % self.shape[0])

def make_swaths(ifilepaths, filter=None, cut_bad=False):
    """Takes SDR hdf files and creates flat binary files for the information
    required to do further processing.

    :Parameters:
        ifilepaths : list
            List of image data filepaths ('SV*') of one kind of band that are
            to be concatenated into a swath.  For example, all of the data
            files for the I bands that are in the same time window.
    :Keywords:
        filter : function pointer
            Function that expects a file info dictionary as its only parameter
            and returns True if that file should continue to be process or
            False if not.
        cut_bad : bool
            Specify whether or not to delete/cut out entire scans of data
            when navigation data is bad.  This is done because the ms2gt
            utilities used for remapping can't handle incorrect navigation data
    """
    # Get meta information from the image data files
    log.info("Getting data file info...")
    meta_data,image_data = get_meta_data(ifilepaths, filter=filter)

    # Extract gfilepaths from the ifilepath information
    # list comprehension here is the fastest way to flatten a list of lists
    gfilepaths = sorted(set( finfo["geo_path"] for band_data in image_data.values() for finfo in band_data ))

    # SANITY CHECK
    g_len = len(gfilepaths)
    for band,finfos in image_data.items():
        f_len = len(finfos)
        if f_len != g_len:
            log.error("Expected same number of image and navigation files for every band, removing band...")
            log.error("Got (num ifiles: %d, num gfiles: %d)" % (f_len,g_len))
            del image_data[band]
            del meta_data["bands"][band]

    if len(image_data) == 0:
        log.error("There aren't any bands left to work on, quitting...")
        raise ValueError("There aren't any bands left to work on, quitting...")

    # Get nav data and put it in fbf files
    log.info("Getting geonav file info...")
    geo_meta,geo_data = get_geo_meta(gfilepaths)
    meta_data.update(geo_meta)

    log.info("Creating binary files for latitude and longitude data")
    process_geo(meta_data, geo_data, cut_bad=cut_bad)

    # Get image data and put it in fbf files
    log.info("Creating binary files for image data and day/night masks")
    process_image(meta_data, image_data, geo_data, cut_bad=cut_bad)

    return meta_data

def main():
    import optparse
    usage = """
%prog [options] filename1.h,filename2.h,filename3.h,... struct1,struct2,struct3,...

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path to append to GCCXML call")
    (options, args) = parser.parse_args()

    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options

    if options.self_test:
        import doctest
        doctest.testmod()
        sys.exit(0)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 9

    import json
    meta_data = make_swaths(args[:])
    print json.dumps(meta_data)
    return 0

if __name__=='__main__':
    sys.exit(main())
