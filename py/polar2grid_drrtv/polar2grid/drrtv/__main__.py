#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
polar2grid.drrtv
~~~~~~~~~~~~~~~~


A description which can be long and explain the complete
functionality of this module even with indented code examples.
Class/Function however should not be documented here.


:copyright: 2013 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""
__author__ = 'R.K.Garcia <rayg@ssec.wisc.edu>'
__revision__ = '$Id:$'
__docformat__ = 'reStructuredText'

import os, sys
import logging, unittest


LOG = logging.getLogger(__name__)


#
## FIXME code goes here.
#


def main():
    import optparse
    usage = """
%prog [options] ...


"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests")
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path")
    (options, args) = parser.parse_args()


    # make options a globally accessible structure, e.g. OPTS.
    global OPTS
    OPTS = options


    if options.self_test:
        unittest.main()
        return 0


    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])


    if not args:
        parser.error( 'incorrect arguments, try -h or --help.' )
        return 1


    # FIXME main logic

    return 0


if __name__=='__main__':
    sys.exit(main())