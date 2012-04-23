#!/usr/bin/env python# encoding: utf-8
"""
dibs.py
$Id$

Purpose: Emulate direct broadcast using IDPS ops data stored in the PEATE

Reference:
http://peate.ssec.wisc.edu/flo/api#api_find

Created by rayg on 23 Apr 2012.
Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
"""

import logging
import os, sys, re
from urllib2 import urlopen
from subprocess import call
from collections import defaultdict
from datetime import date, timedelta, datetime

LOG = logging.getLogger(__name__)

FLO_FMT = """http://peate.ssec.wisc.edu/flo/api/find?
			start=%(start)s&end=%(end)s
			&file_type=GITCO
			&file_type=GDNBO
                        &file_type=SVDNB
                        &file_type=SVI01
			&file_type=SVI02
                        &file_type=SVI03
			&file_type=SVI04
                        &file_type=SVI05
                        &file_type=SVM01
                        &file_type=SVM02
                        &file_type=SVM03
                        &file_type=SVM04
                        &file_type=SVM05
                        &file_type=SVM06
                        &file_type=SVM07
                        &file_type=SVM08
                        &file_type=SVM09
                        &file_type=SVM10
                        &file_type=SVM11
                        &file_type=SVM12
                        &file_type=SVM13
                        &file_type=SVM14
                        &file_type=SVM15
                        &file_type=SVM16
			&loc=%(lat)s,%(lon)s
			&radius=%(radius)s
			&output=txt
"""

RE_NPP = re.compile('(?P<kind>[A-Z]+)(?P<band>[0-9]*)_(?P<sat>[A-Za-z0-9]+)_d(?P<date>\d+)_t(?P<start_time>\d+)_e(?P<end_time>\d+)_b(?P<orbit>\d+)_c(?P<created_time>\d+)_(?P<site>[a-zA-Z0-9]+)_(?P<domain>[a-zA-Z0-9]+)\.h5')


FLO_FMT = re.sub(r'\n\s+', '', FLO_FMT)

def flo_find(lat, lon, radius, start, end):
    "return shell script and filename list"
    start = start.strftime('%Y-%m-%d')
    end = end.strftime('%Y-%m-%d')
    LOG.debug('accessing %s' % (FLO_FMT % locals()))
    wp = urlopen(FLO_FMT % locals())
    for url in wp:
        url = url.strip()
        if not url:
            continue
        match = RE_NPP.search(url)
        if not match:
            continue
        LOG.debug('found %s @ %s' % (match.group(0), url))
        yield match, url
    wp.close()

def _test_flo_find():
    start = date(2011, 12, 13)
    end = date(2011, 12, 14)
    for nfo, url in flo_find(43, -89, 1000, start, end):
        print nfo.group(0), url # print filename and url


def curl(filename, url):
    return call(['curl', '-s', '-o', filename, url])

def _key(nfo):
    nfo = nfo.groupdict()
    return (nfo['date'], nfo['start_time'], nfo['end_time'])

def sync(lat, lon, radius, start=None, end=None):
    "synchronize current working directory to include all the files available"
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=1)
    bad = list()
    good = list()
    new_files = defaultdict(list)
    for nfo, url in flo_find(lat, lon, radius, start, end):
        filename = nfo.group(0)
        LOG.debug('checking %s @ %s' % (filename, url))
        if os.path.isfile(filename):
            LOG.debug('%s is already present' % filename)
        else:
            LOG.info('downloading %s' % url)
            rc = curl(filename, url)
            if rc!=0:
                bad.append(nfo)
                LOG.warning('download of %s failed' % url)
            else:
                good.append(nfo)
                LOG.info('ok!')
    # return a dictionary of date+time combinations which had no failed file transfers
    badset = set(_key(nfo) for nfo in bad)
    LOG.debug('these keys had transfer failures: %s' % repr(badset))
    for nfo in good:
        key = _key(nfo)
        if key not in badset:
            LOG.debug('adding %s to %s' % (nfo.group(0), key))
            new_files[key].append(nfo)
    return new_files

def go(name, lat, lon, radius, start=None, end=None):
    "write a .nfo file with 'date start_time end_time when we complete a transfer"
    lat = int(lat)
    lon = int(lon)
    radius = int(radius)
    if start:
        start = datetime.strptime(start, '%Y-%m-%d').date()
    if end:
        end = datetime.strptime(end, '%Y-%m-%d').date()

    fp = file(name+'.nfo', 'at')
    for key in sync(lat, lon, radius, start, end).keys():
        LOG.info('%s is ready' % repr(key))
        print >>fp, '%s %s %s' % key
        fp.flush()
    fp.close()



def main():
    import optparse
    usage = """
%prog domain-name --lat=latitude --lon=longitude --radius=radius-in-km {--start=YYYY-MM-DD} {--end=YYYY-MM-DD}
appends domain.nfo with "day start end" lines as complete sets of VIIRS files arrive
files are downloaded to current directory
files which have already been downloaded will not be re-downloaded
default start and end is yesterday~today
example:
%prog madison --lat=43 --lon=-89 --radius=1000

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-a', '--lat', dest='lat', help='central latitude', type='int')
    parser.add_option('-o', '--lon', dest='lon', help='central longitude', type='int')
    parser.add_option('-r', '--radius', dest='radius', help='radius in km', type='int')
    parser.add_option('-s', '--start', dest='start', help='yyyy-mm-dd start dateoptional', default=None)
    parser.add_option('-e', '--end', dest='end', help='yyyy-mm-dd end date optional', default=None)
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path to append to GCCXML call")
    (options, args) = parser.parse_args()

    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options

    if options.self_test:
        # FIXME - run any self-tests
        # import doctest
        # doctest.testmod()
        sys.exit(2)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])

    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 9

    go(args[0], options.lat, options.lon, options.radius, options.start, options.end)

    return 0


if __name__=='__main__':
    sys.exit(main())
