#!/usr/bin/env python
"""Script for users to create an event job to be run by event2grid in the future.
"""

import os
import sys
import logging
import getpass
from datetime import datetime, timedelta

LOG = logging.getLogger(__name__)

EVENT_SCRIPT_KEY = "{start}_{end}_{creation}_{user}"
EVENT_SCRIPT_DIR = "/home/davidh/event2grid_jobs"
EVENT2GRID_SCRIPT = "/data/users/davidh/event2grid_env/polar2grid/py/util/event2grid.sh"
EVENT2GRID_SCRIPT_TEXT = """#!/usr/bin/env bash
{event2grid_script} {event_key} {dl_dir} {work_dir} "{dibs_flags}" "{p2g_flags}"
"""
DATA_DL_DIR = "/data1/tmp/event2grid_download"
P2G_WORK_DIR = "/data1/tmp/event2grid_work"

ALL_VIIRS_PRODUCT_LIST = 'GMTCO GITCO GDNBO SVDNB SVI01 SVI02 SVI03 SVI04 SVI05' + ' SVM%02d'*16 % tuple(range(1, 17))
ALL_VIIRS_PRODUCT_LIST = ALL_VIIRS_PRODUCT_LIST.split(' ')
CREFL_VIIRS_PRODUCT_LIST = 'GMTCO GITCO SVM05 SVM07 SVM03 SVM04 SVM08 SVM10 SVM11 SVI01 SVI02 SVI03'.split(' ')


def get_script_text(event_key, **kwargs):
    dibs_flags = "lat lon radius start end file_types".split(' ')
    p2g_flags = "grids".split(' ')

    # FIXME: Start and End will allow times in the future for dibs
    if "start" in kwargs:
        kwargs["start"] = kwargs["start"].strftime('%Y-%m-%d')
    if "end" in kwargs:
        kwargs["end"] = kwargs["end"].strftime('%Y-%m-%d')
    if "grids" in kwargs:
        kwargs["grids"] = " ".join(kwargs["grids"])
    file_types = None
    if "file_types" in kwargs:
        file_types = " ".join(kwargs.pop("file_types"))

    dibs_flags_str = " ".join(["--%s %s" % (k.replace('_', '-'), str(kwargs.get(k, None))) for k in dibs_flags if k in kwargs])
    if file_types:
        dibs_flags_str += " " + file_types
    p2g_flags_str = " ".join(["--%s %s" % (k.replace('_', '-'), str(kwargs.get(k, None))) for k in p2g_flags if k in kwargs])

    return EVENT2GRID_SCRIPT_TEXT.format(event2grid_script=EVENT2GRID_SCRIPT, event_key=event_key, dl_dir=DATA_DL_DIR, work_dir=P2G_WORK_DIR, dibs_flags=dibs_flags_str, p2g_flags=p2g_flags_str)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Create new job to watch a certain event with event2grid")
    #parser.add_argument('-t', '--test', dest="self_test",
    #                action="store_true", default=False, help="run self-tests")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_argument('-a', '--lat', dest='lat', help='central latitude', type=float)
    parser.add_argument('-o', '--lon', dest='lon', help='central longitude', type=float)
    parser.add_argument('-r', '--radius', dest='radius', help='radius in km', type=int, default=0)
    parser.add_argument('-s', '--start', dest='start', help='yyyy-mm-dd start dateoptional', default=None)
    parser.add_argument('-e', '--end', dest='end', help='yyyy-mm-dd end date optional', default=None)
    parser.add_argument('--file-types', dest='file_types', choices=ALL_VIIRS_PRODUCT_LIST,
            default=CREFL_VIIRS_PRODUCT_LIST, help="file types to download from PEATE")
    parser.add_argument('-g', '--grids', dest="grids", default=["wgs84_fit"], nargs="*",
            help="polar2grid grid to remap the data to")
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, args.verbosity)])

    # FUTURE: Except times
    start = datetime.strptime(args.start, '%Y-%m-%d') if args.start else (datetime.utcnow().replace(hour=0, minute=0, second=0) - timedelta(days=1))
    end = (datetime.strptime(args.end, '%Y-%m-%d') if args.end else datetime.utcnow()).replace(hour=23, minute=59, second=59) # FIXME: Only needed if no time
    start_str = start.strftime('%Y%m%d_%H%M%S')
    end_str = end.strftime('%Y%m%d_%H%M%S')
    creation = datetime.utcnow()
    creation_str = creation.strftime("%Y%m%d_%H%M%S")
    user = getpass.getuser()

    event_key = EVENT_SCRIPT_KEY.format(start=start_str, end=end_str, creation=creation_str, user=user)
    event_script_fn = event_key + ".sh"
    event_script_fp = os.path.join(EVENT_SCRIPT_DIR, event_script_fn)

    if not os.path.isdir(EVENT_SCRIPT_DIR):
        LOG.info("Creating script directory '%s'", EVENT_SCRIPT_DIR)
        os.makedirs(EVENT_SCRIPT_DIR)
    if os.path.isfile(event_script_fp):
        LOG.error("Event script already exists, won't create")
        return -1
    
    # Create the script
    LOG.info("Creating event script")
    event_script = open(event_script_fp, 'wt')
    script_text = get_script_text(event_key, start=start, end=end, file_types=args.file_types, lon=args.lon, lat=args.lat, radius=args.radius, grids=args.grids)
    LOG.debug("Writing the following script text:\n%s", script_text)
    event_script.write(script_text)
    event_script.close()

    LOG.info("Changing script permissions to allow execution")
    os.chmod(event_script_fp, 0o555)

    LOG.info("Done")


if __name__ == "__main__":
    sys.exit(main())

