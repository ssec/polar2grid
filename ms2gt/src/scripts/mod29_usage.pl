# $Id: mod29_usage.pl,v 1.4 2006/05/26 23:52:57 tharan Exp $

#========================================================================
# mod29_usage.pl - defines mod29.pl usage message
#
# 14-May-2001 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

$|=1;

$mod29_usage = "\n
USAGE: mod29.pl dirinout tag listfile gpdfile
                [chanlist [latlonlistfile [keep [rind]]]]
       defaults:    1          none         0     50

  dirinout: directory containing the input and output files.
  tag: string used as a prefix to output files.
  listfile: text file containing a list of MOD29 files to be gridded.
  gpdfile: .gpd file that defines desired output grid.
  chanlist: string specifying channel numbers to be gridded. The default
            is 1, i.e. grid channel 1 only. The channel numbers are:
              1: icer Sea Ice by Reflectance - 8-bit unsigned
              2: irqa Sea Ice by Reflectance Pixel QA - 8-bit unsigned
              3: temp Ice Surface Temperature - 16-bit unsigned (kelvin * 100)
              4: itqa Ice Surface Temperature Pixel QA - 8-bit unsigned
              5: icet Sea Ice by IST - 8-bit unsigned,
                 available only for MODIS version 004 and earlier.
              6: icrt Combined Sea Ice - 8-bit unsigned,
                 available only for MODIS version 004 and earlier.
  latlonlistfile: text file containing a list of MOD02 or MOD03 files whose
            latitude and longitude data should be used in place of the latlon
            data in the corresponding MOD29 files in listfile. The default is
            \"none\" indicating that the latlon data in each MOD29 file
            should be used without substitution.
  keep: 0: delete intermediate chan, lat, lon, col, and row files (default).
        1: do not delete intermediate chan, lat, lon, col, and row files.
  rind: number of pixels to add around intermediate grid to eliminate
        holes in final grid. Default is 50.\n\n";

# this makes the routine work properly using require in other programs
1;
