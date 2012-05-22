#!/usr/bin/perl -w

# $Id: mod10_l2_usage.pl,v 1.4 2006/05/26 17:47:08 tharan Exp $

#========================================================================
# mod10_l2_usage.pl - defines mod10_l2.pl usage message
#
# 14-May-2001 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

$|=1;

$mod10_l2_usage = "\n
USAGE: mod10_l2.pl dirinout tag listfile gpdfile
                  [chanlist [latlonlistfile [keep [rind]]]]
       defaults:      1          none         0     50

  dirinout: directory containing the input and output files.
  tag: string used as a prefix to output files.
  listfile: text file containing a list of MOD10_L2 files to be gridded.
  gpdfile: .gpd file that defines desired output grid.
  chanlist: string specifying channel numbers to be gridded. The default
            is 1, i.e. grid channel 1 only. The channel numbers are:
              1: snow Snow Cover - 8-bit unsigned.
              2: snqa Snow Cover Pixel QA - 8-bit unsigned.
              3: snrc Snow Cover Reduced Cloud - 8-bit unsigned,
                 available only for MODIS version 004.
              4: snfr Fractional Snow Cover - 8-bit unsigned,
                 available only for MODIS version 005.
  latlonlistfile: text file containing a list of MOD02 or MOD03 files whose
                  latitude and longitude data should be used in place of the
                  latlon data in the corresponding MOD10_L2 files in listfile.
                  The default is \"none\" indicating that the latlon data in
                  each MOD10_L2 file should be used without substitution.
  keep: 0: delete intermediate chan, lat, lon, col, and row files (default).
        1: do not delete intermediate chan, lat, lon, col, and row files.
  rind: number of pixels to add around intermediate grid to eliminate
        holes in final grid. Default is 50.\n\n";

# this makes the routine work properly using require in other programs
1;
