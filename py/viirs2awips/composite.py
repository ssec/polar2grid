"""Combine 2 or more orbits into one grid.
"""
from keoni.fbf import Workspace

import os
import sys
import logging
import numpy

log = logging.getLogger(__name__)

def compose(*filepaths):
    fbf_attrs = []
    for f in filepaths:
        if not os.path.exists(f):
            log.error("FBF file %s does not exist" % f)
            raise ValueError("FBF file %s does not exist" % f)

        tmp_attr = f.split(".")[0]
        fbf_attrs.append(tmp_attr)

    size = None
    base_arr = None
    W = Workspace('.')
    for a in fbf_attrs:
        tmp_arr = getattr(W, a)[0]
        if base_arr is None:
            base_arr = tmp_arr.copy()
            size = base_arr.shape
            print base_arr.min(),base_arr.max()
        else:
            if tmp_arr.shape != size:
                log.error("Images are not the same shape, expected %r, got %r" % (size, tmp_arr.shape))
                raise ValueError("Images are not the same shape, expected %r, got %r" % (size, tmp_arr.shape))
            nz = numpy.nonzero(tmp_arr != 0)
            # TODO: Check if data is overlapping
            base_arr[nz] = tmp_arr[nz]
            print base_arr.min(),base_arr.max()

    return base_arr

def compose_nc(nc_template, *filepaths):
    from awips_netcdf import fill, UTC
    from rescale import rescale,K_REFLECTANCE
    from datetime import datetime
    new_comp = compose(*filepaths)
    new_comp = rescale(new_comp, data_kind=K_REFLECTANCE)
    fill("./composite.nc", new_comp, nc_template, datetime.utcnow().replace(tzinfo=UTC))

def main():
    import optparse
    usage = """%prog nc_tempalte result1.fbf result2.fbf ..."""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    options,args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])

    if len(args) < 3 or "help" in args:
        parser.print_help()
        return 0

    #return compose(*args)
    return compose_nc(*args)

if __name__ == "__main__":
    sys.exit(main())


