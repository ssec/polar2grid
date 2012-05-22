#!/usr/bin/perl -w

# $Id: mod35_l2_usage.pl,v 1.2 2003/08/01 22:00:14 haran Exp $

#========================================================================
# mod35_l2_usage.pl - defines mod35_l2.pl usage message
#
# 14-May-2001 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

$|=1;

$mod35_l2_usage = "\n
USAGE: mod35_l2.pl dirinout tag listfile gpdfile chanfile
                [ancilfile [latlonlistfile [keep [rind]]]]
       defaults:   none         none         0     50

  dirinout: directory containing the input and output files.
  tag: string used as a prefix to output files.
  listfile: text file containing a list of MOD35_L2 files to be gridded.
  gpdfile: .gpd file that defines desired output grid.
  chanfile: text file containing a list of channels to be gridded, one line
        per channel. Each line in chanfile must contain one of the following:
            time - Scan Start Time - double precision floating-point array
              containing seconds since 1993-1-1 00:00:00.0 that indicates
              the start time for the scan in which the data point was
              acquired.
            cld0-5 - Cloud Mask - Specifies one of up to six 8-bit unsigned
              byte arrays containing the 48-bit cloud mask. The left-most bit
              (bit 7) is the most significant bit within each byte.
                 cld0 - contains Cloud Mask bits  7-0  in cld0 bits 7-0. 
                 cld1 - contains Cloud Mask bits 15-8  in cld1 bits 7-0. 
                 cld2 - contains Cloud Mask bits 23-16 in cld2 bits 7-0. 
                 cld3 - contains Cloud Mask bits 31-24 in cld3 bits 7-0. 
                 cld4 - contains Cloud Mask bits 39-32 in cld4 bits 7-0. 
                 cld5 - contains Cloud Mask bits 47-40 in cld5 bits 7-0.
            cqa0-9 - Quality Assurance - Specifies one of up to ten 8-bit
              unsigned byte arrays containing cloud mask quality assurance
              bytes 0-9.
              NOTE: For more information on interpreting cloud mask and 
                    quality assurance information, see:
                    http://cimss.ssec.wisc.edu/modis1/pdf/CMUSERSGUIDE.PDF
  ancilfile: text file containing a list of ancillary parameters to be gridded,
        one line per parameter. The default is \"none\" indicating that no
        ancillary parameters should be gridded. Each line in ancilfile should
        consist of up to four fields:
          param conversion weight_type fill
            where the fields are defined as follows:
              param - a string that specifies an ancillary parameter to be
                gridded, and must be one of the following 4 character strings:
                  hght - Height (available in MOD03 only)
                  seze - SensorZenith
                  seaz - SensorAzimuth
                  rang - Range (available in MOD03 only)
                  soze - SolarZenith
                  soaz - SolarAzimuth
                  lmsk - Land/SeaMask (available in MOD03 only)
                  gflg - gflags (available in MOD03 only)
              conversion - a string that specifies the type of conversion
                that should be performed on the channel. The string must be
                one of the following:
                  raw - raw HDF values (16-bit signed integers except that
                    Range is 16-bit unsigned integer and Land/SeaMask and
                    gflags are unsigned bytes) (default).
                  scaled - raw values multiplied by a parameter-specific
                    scale factor (floating-point). Note that scale factor
                    for Height, Land/SeaMask, and gflags is 1.
              weight_type - a string that specifies the type of weighting
                that should be perfomed on the channel. The string must be one
                of the following:
                  avg - use weighted averaging (default for all except
                        Land/SeaMask and gflags).
                  max - use maximum weighting (default for Land/SeaMask and
                        gflags).
              fill - specifies the output fill value. Default is 0.
  latlonlistfile: text file containing a list of MOD03 files whose
                  latitude and longitude data and ancillary data should be
                  used in place of the data in the corresponding MOD35_L2 files
                  in listfile.
                  The default is \"none\" indicating that the latlon and
                  ancillary data in each MOD35_L2 file should be used without
                  substitution.
  keep: 0: delete intermediate files (default).
        1: do not delete intermediate files.
  rind: number of pixels to add around intermediate grid to eliminate
        holes in final grid. Default is 50.\n\n";

# this makes the routine work properly using require in other programs
1;
