#!/usr/bin/env python
# encoding: utf-8
"""
viirs_imager_to_swath.py
$Id$

Purpose:
Read one or more contiguous in-order HDF5 VIIRS imager granules in any aggregation
Write out Swath binary files used by ms2gt tools.

Created by rayg@ssec.wisc.edu, Dec 2011.
Copyright (c) 2011 University of Wisconsin SSEC. All rights reserved.
"""
from adl_guidebook import file_info,geo_info,read_file_info,read_geo_info

import logging
import sys, os
from glob import glob
import numpy

log = logging.getLogger(__name__)

def _glob_file(pat):
    tmp = glob(pat)
    if len(tmp) != 1:
        log.error("There were no files or more than one fitting the pattern %s" % pat)
        raise ValueError("There were no files or more than one fitting the pattern %s" % pat)
    return tmp[0]

def get_meta_data(ifilepaths, filter=None):
    """Create all possibly necessary binary files from concatenated
    granule data.
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
    """Return a dictionary of meta data taken from the geonav filenames.
    Also, return a list of geonav file detailed information dictionaries.
    """
    geo_data = []
    meta_data = {
            "start_dt"  : None,
            "swath_rows"  : None,
            "swath_cols"  : None,
            "rows_per_scan" : None,
            "fbf_lat"   : None,
            "fbf_lon"   : None
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
    """Read data from the geonav files and put then all
    into 2 concatenated swath files.  One for latitude data and one for
    longitude data.
    """
    #meta_data = {
    #        "start_dt"  : None,
    #        "swath_rows"  : None,
    #        "swath_cols"  : None,
    #        "fbf_lat"   : None,
    #        "fbf_lon"   : None
    #        }

    # Write lat/lon data to fbf files
    # Create fbf files
    spid = '%d' % os.getpid()
    latname = '.lat' + spid
    lonname = '.lon' + spid
    lafo = file(latname, 'wb')
    lofo = file(lonname, 'wb')
    lafa = file_appender(lafo, dtype=numpy.float32)
    lofa = file_appender(lofo, dtype=numpy.float32)


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

        # Append the data to the swath
        lafa.append(ginfo["lat_data"])
        lofa.append(ginfo["lon_data"])
        del ginfo["lat_data"]
        del ginfo["lon_data"]
        del ginfo["lat_mask"]
        del ginfo["lon_mask"]

    lafo.close()
    lofo.close()

    # Rename files
    suffix = '.real4.' + '.'.join(str(x) for x in reversed(lafa.shape))
    fbf_lat_var = "latitude_%s" % meta_data["kind"]
    fbf_lon_var = "longitude_%s" % meta_data["kind"]
    fbf_lat = fbf_lat_var + suffix
    fbf_lon = fbf_lon_var + suffix
    os.rename(latname, fbf_lat)
    os.rename(lonname, fbf_lon)
    meta_data["fbf_lat"] = fbf_lat
    meta_data["fbf_lon"] = fbf_lon
    swath_rows,swath_cols = lafa.shape
    meta_data["swath_rows"] = swath_rows
    meta_data["swath_cols"] = swath_cols
    meta_data["swath_scans"] = swath_rows/meta_data["rows_per_scan"]

    return meta_data,geo_data

def process_image(meta_data, image_data, geo_data, cut_bad=False):
    # Get image data and save it to an fbf file
    for band,finfos in image_data.items():
        band_meta = meta_data["bands"][band]

        # Create fbf files and appenders
        spid = '%d' % os.getpid()
        imname = '.image' + spid
        dmask_name = '.day_mask' + spid
        nmask_name = '.night_mask' + spid
        imfo = file(imname, 'wb')
        dmask_fo = file(dmask_name, 'wb')
        nmask_fo = file(nmask_name, 'wb')
        imfa = file_appender(imfo, dtype=numpy.float32)
        dmask_fa = file_appender(dmask_fo, dtype=numpy.int8)
        nmask_fa = file_appender(nmask_fo, dtype=numpy.int8)

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
                # delete returns an array regardless, file_appender requires None
                if finfo["day_mask"] is not None:
                    finfo["day_mask"] = numpy.delete(finfo["day_mask"], ginfo["scan_quality"], axis=0)
                if finfo["night_mask"] is not None:
                    finfo["night_mask"] = numpy.delete(finfo["night_mask"], ginfo["scan_quality"], axis=0)

            # Append the data to the file
            imfa.append(finfo["image_data"])
            dmask_fa.append(finfo["day_mask"])
            nmask_fa.append(finfo["night_mask"])

            # Remove pointers to data so it gets garbage collected
            del finfo["image_data"]
            del finfo["image_mask"]
            del finfo["day_mask"]
            del finfo["night_mask"]
            del finfo["scan_quality"]
            del finfo

        suffix = '.real4.' + '.'.join(str(x) for x in reversed(imfa.shape))
        suffix2 = '.int1.' + '.'.join(str(x) for x in reversed(imfa.shape))
        img_base = "image_%s" % band_meta["band_name"]
        dmask_base = "day_mask_%s" % band_meta["band_name"]
        nmask_base = "night_mask_%s" % band_meta["band_name"]
        fbf_img = img_base + suffix
        fbf_dmask = dmask_base + suffix2
        fbf_nmask = nmask_base + suffix2
        os.rename(imname, fbf_img)
        os.rename(dmask_name, fbf_dmask)
        os.rename(nmask_name, fbf_nmask)
        band_meta["fbf_img"] = fbf_img
        band_meta["fbf_dmask"] = fbf_dmask
        band_meta["fbf_nmask"] = fbf_nmask
        rows,cols = imfa.shape
        band_meta["swath_rows"] = rows
        band_meta["swath_cols"] = cols
        band_meta["swath_scans"] = meta_data["swath_scans"]

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
        dmask_fo.close()
        nmask_fo.close()
        del imfa
        del dmask_fa
        del nmask_fa
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
