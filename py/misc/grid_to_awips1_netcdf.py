#!/usr/bin/env python
# encoding: utf-8
"""
FIXME
$Id$

Purpose: FIXME

Created by FIXME on FIXME.
Copyright (c) 2011 University of Wisconsin SSEC. All rights reserved.
"""

import sys
import re
import ctypes as c
import numpy as np
import logging

# every module should have a LOG object
# e.g. LOG.warning('my dog has fleas')
LOG = logging.getLogger(__name__)



###
###  FIXME insert your routines here, or import other modules from your application
###



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
        # FIXME - run any self-tests
        # import doctest
        # doctest.testmod()
        sys.exit(2)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[options.verbosity])

    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 9

    # FIXME - main() logic code here

    return 0


if __name__=='__main__':
    sys.exit(main())
