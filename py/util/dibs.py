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
from glob import glob
from datetime import date, timedelta, datetime

LOG = logging.getLogger(__name__)

# FUTURE: generate FLO_FMT using PRODUCT_LIST
PRODUCT_LIST = 'GITCO GDNBO SVDNB SVI01 SVI02 SVI03 SVI04 SVI05 SVM01 SVM02 SVM03 SVM04 SVM05 SVM06 SVM07 SVM08 SVM09 SVM10 SVM11 SVM12 SVM13 SVM14 SVM15 SVM16'.split(' ')

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

ONE_DAY = timedelta(days=1)

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

def _all_products_present(key, file_nfos, products = PRODUCT_LIST):
    needs = set(products)
    for nfo in file_nfos:
        product = '%(kind)s%(band)s' % nfo.groupdict()
        if product in needs:
            needs.remove(product)
        else:
            LOG.error('unknown product type %s was downloaded, how?' % product)
    if needs:
        LOG.info('%s is missing %s, skipping for now' % (repr(key), repr(needs)))
        return False
    return True


def curl(filename, url):
    return call(['curl', '-s', '-o', filename, url])

def _key(nfo):
    nfo = nfo.groupdict()
    return (nfo['date'], nfo['start_time'], nfo['end_time'])

def sync(lat, lon, radius, start=None, end=None):
    "synchronize current working directory to include all the files available"
    if end is None:
        end = date.today() + ONE_DAY
    if start is None:
        start = end - ONE_DAY
    bad = list()
    good = list()
    new_files = defaultdict(list)
    inventory = list(flo_find(lat, lon, radius, start, end))
    for n, (nfo, url) in enumerate(inventory):
        filename = nfo.group(0)
        LOG.debug('checking %s @ %s' % (filename, url))
        if os.path.isfile(filename):
            LOG.debug('%s is already present' % filename)
        else:
            LOG.info('downloading %d/%d : %s' % (n+1, len(inventory), url))
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
    fully_intact_sets = dict((k,v) for k,v in new_files.items() if _all_products_present(k,v))
    return fully_intact_sets

def mainsync(name, lat, lon, radius, start=None, end=None):
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




hmst = lambda s: tuple(map(int, [s[0:2], s[2:4], s[4:6], s[6]+'00000']))
ymd = lambda s: tuple(map(int, [s[0:4], s[4:6], s[6:8]]))

def _key2dts(k):
    "convert (yyyymmdd, hhmmsst, hhmmsst) string key tuple into start and end datetime objects"
    d,s,e = k
    d = ymd(d)
    s = hmst(s)
    e = hmst(e)
    ds = datetime(*(d+s))
    de = datetime(*(d+e))
    if de < ds:
        de += timedelta(days=1)
    return ds,de

def _dts2key(s,e):
    "convert datetime object into key tuple"
    horus = lambda x: '%02d%02d%02d%d' % (x.hour, x.minute, x.second, x.microsecond/100000)
    return s.strftime('%Y%m%d'), horus(s), horus(e)

def _outcome_cg(seq):
    "given a sequence of (start,end) ordered datetime objects representing contiguous granules, return new outer key and list of granules"
    if not seq: return None
    grans = [seq[0][0]] + [x[1] for x in seq]
    # build new key
    s = grans[0][0]
    e = grans[-1][1]
    return (_dts2key(s,e), [_dts2key(*x) for x in grans])

def contiguous_groups(keyset, tolerance=timedelta(seconds=5)):
    "sort a set of keys into contiguous groups; yield (newkey, list-of-subkeys) sequence"
    granlist = list(sorted(map(_key2dts, keyset)))

    # pair off in start-time order
    # build a set containing contiguous granules
    # when we find a break in sequence, yield the set as an ordered tuple and start over
    seq = []
    for ((sa,ea),(sb,eb)) in zip(granlist[:-1], granlist[1:]):
        delta = sb-ea
        if delta < tolerance:
            seq.append(((sa,ea),(sb,eb)))
        else:
            if seq:
                yield _outcome_cg(seq)
            seq = []
    if seq:
        yield _outcome_cg(seq)

def read_nfo(filename=None, fobj=None):
    if fobj is None:
        fobj = file(filename, 'rt')
    for line in fobj:
        k = map(str.strip, line.split(' '))
        if len(k)==3:
            yield k

STAMP_FMT = 'd%s_t%s_e%s'

def pass_build(key, subkeys):
    "link all files belonging to subkeys to an pass directory"
    name = STAMP_FMT % key
    final_name = name + '.pass'
    if os.path.isdir(name) or os.path.isdir(final_name):
        LOG.warning('%s already has been processed' % name)
        return None
    os.mkdir(name)
    for piece in subkeys:
        pat = '*' + STAMP_FMT % piece + '*.h5'
        LOG.debug('looking for %s' % pat)
        for filename in glob(pat):
            LOG.debug('linking %s to %s' % (filename, name))
            os.symlink(os.path.join('..', filename), os.path.join(name, filename))
    os.rename(name, final_name)
    LOG.info('created %s' % final_name)



def mainpass(nfo_filename):
    "consume nfo file and link granule groups to their own .pass directories"
    fobj = file(nfo_filename, 'rt')
    stowname = '.' + nfo_filename
    if os.path.isfile(stowname):
        LOG.warning('removing old %s' % stowname)
        os.unlink(stowname)
    os.rename(nfo_filename, stowname)
    nfo = list(read_nfo(fobj=fobj))
    fobj.close()
    passes = contiguous_groups(nfo)
    for eve in passes:
        pass_build(*eve)


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
%prog madison --pass

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-a', '--lat', dest='lat', help='central latitude', type='int')
    parser.add_option('-o', '--lon', dest='lon', help='central longitude', type='int')
    parser.add_option('-r', '--radius', dest='radius', help='radius in km', type='int', default=0)
    parser.add_option('-s', '--start', dest='start', help='yyyy-mm-dd start dateoptional', default=None)
    parser.add_option('-e', '--end', dest='end', help='yyyy-mm-dd end date optional', default=None)
    parser.add_option('-p', '--pass', dest='passes', help='post-process .nfo file (consuming it) and create .pass directories', default=False, action="store_true")
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

    if options.radius:
        mainsync(args[0], options.lat, options.lon, options.radius, options.start, options.end)

    if options.passes:
        mainpass(args[0]+'.nfo')
        return 0


    return 0


if __name__=='__main__':
    sys.exit(main())
