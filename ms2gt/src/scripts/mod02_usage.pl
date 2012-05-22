# $Id: mod02_usage.pl,v 1.26 2010/09/24 00:59:19 tharan Exp $

#========================================================================
# mod02_usage.pl - defines mod02.pl usage message
#
# 25-Oct-2000 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

$|=1;

$mod02_usage = "\n
USAGE: mod02.pl dirinout tag listfile gpdfile chanfile
                [ancilfile [latlon_src [ancil_src [keep [rind
       defaults:    none         1          1       0     50
                [fix250 [fixcolfile1 [fixcolfile2 [fixrowfile1 [fixrowfile2
       defaults:    0        none         none         none         none
                [tile_cols [tile_rows [tile_overlap
                     1          1          300
                [maskfile [mask_factor [mask_keep
       defaults:   none        6            0
                {swath_width_fraction]]]]]]]]]]]]]]]]]
       defaults: 1.0 (0.75 for UTM)

  dirinout: directory containing the input and output files.
  tag: string used as a prefix to output files.
  listfile: text file containing a list of MOD02, MOD03, MYD02, or MYD03 files
        to be gridded. All files in listfile must be of the same type and
        the same resolution.
  gpdfile: .gpd file that defines desired output grid.
  chanfile: text file containing a list of channels to be gridded, one line
        per channel. If chanfile is \"none\" then no channel data will be
        gridded and ancilfile must not be \"none\". Each line in chanfile
        should consist of up to four fields:
          chan conversion weight_type fill
            where the fields are defined as follows:
              chan - specifies a channel number (1-36).
              conversion - a string that specifies the type of conversion
                that should be performed on the channel. The string must be
                one of the following:
                  raw - raw HDF values (16-bit unsigned integers) (default).
                  corrected - corrected counts (floating-point).
                  radiance - watts per square meter per steradian per
                    micrometer (floating-point).
                  reflectance - (channels 1-19 and 26) reflectance without
                    solar zenith angle correction (floating-point).
                  temperature - (channels 20-25 and 27-36) brightness
                    temperature in kelvin (floating-point).
              weight_type - a string that specifies the type of weighting
                that should be perfomed on the channel. The string must be one
                of the following:
                  avg - use weighted averaging (default).
                  max - use maximum weighting.
              fill - specifies the output fill value. Default is 0.
      NOTE: if first file in listfile is MOD03 or MYD02, then chanfile must be
      \"none\", and both latlon_src and ancil_src are forced to 3.
  ancilfile: text file containing a list of ancillary parameters to be gridded,
        one line per parameter. The default is \"none\" indicating that no
        ancillary parameters should be gridded. Each line in ancilfile should
        consist of up to five fields:
          param conversion weight_type fill delete
            where the fields are defined as follows:
              param - a string that specifies an ancillary parameter to be
                gridded, and must be one of the following 4 character strings:
                  hght - Height
                  seze - SensorZenith
                  seaz - SensorAzimuth
                  ssea - sine of SensorAzimuth
                  csea - cosine of SensorAziuth
                  rang - Range
                  soze - SolarZenith
                  soaz - SolarAzimuth
                  ssoa - sine of SolarAzimuth
                  csoa - cosine of SolarAziuth
                  lmsk - Land/SeaMask (available in MOD03 or MYD03 only)
                  gflg - gflags
              conversion - a string that specifies the type of conversion
                that should be performed on the channel. The string must be
                one of the following:
                  raw - raw HDF values (16-bit signed integers except that
                    Range is 16-bit unsigned integer, Land/SeaMask and
                    gflags are unsigned bytes, and ssea, csea, ssoa, and
                    csoa are floating-point) (default).
                  scaled - raw values multiplied by a parameter-specific
                    scale factor (floating-point except that ssea, csea,
                    ssoa, and csoa are 16-bit signed integers). Note that
                    scale factor for Height, Land/SeaMask, and gflags is 1;
                    scale factor for ssea, csea, ssoa, and csoa is 30000.
              weight_type - a string that specifies the type of weighting
                that should be perfomed on the channel. The string must be one
                of the following:
                  avg - use weighted averaging (default for all except
                        Land/SeaMask and gflags).
                  max - use maximum weighting (default for Land/SeaMask and
                        gflags).
              fill - specifies the output fill value. Default is 0.
              delete - 0:keep channel after fix250 is complete (default).
                       1:delete channel after fix250 is complete.
  latlon_src: 1: use 5 km lat-lon data from MOD021KM or MYD021KM file
                 (default).
              3: use 1 km lat-lon data from MOD03 or MYD03 file.
              H: use 1 km lat-lon data from MOD02HKM or MYD02HKM file.
              Q: use 1 km lat-lon data from MOD02QKM or MYD02HKM file.
      NOTE: if latlon_src is set to 3, then ancil_src is forced to 3.
  ancil_src: 1: use 5 km ancillary data from MOD021KM or MYD021KM file
                (default).
             3: use 1 km ancillary data from MOD03 or MYD03 file.
      NOTE: if ancil_src is set to 3, then latlon_src is forced to 3.
  keep: 0: delete intermediate chan, lat, lon, col, and row files (default).
        1: do not delete intermediate chan, lat, lon, col, and row files.
  rind: number of pixels to add around intermediate grid to eliminate
        holes in final grid. Default is 50. Must be greater than 0.
      NOTE: If rind is 0, then no check for min/max columns and rows is
      performed. For direct broadcast data which may contain missing lines,
      you should set rind to 0.
  fix250: 0: do not apply de-striping fix for MOD02QKM or MYD02QKM data
             (default).
          1: apply de-striping fix for MOD02QKM or MYD02QKM data and
             keep solar zenith correction.
          2: apply de-striping fix for MOD02QKM or MYD02QKM data and
             undo solar zenith correction.
          3: apply solar zenith correction only for MOD02QKM or MYD02QKM data.
      NOTE: If fix250 is not 0, then param must be set to soze (Solar Zenith)
      and conversion must be set to raw (16-bit signed integers) in ancilfile.
      NOTE: If fix250 is 1 or 2, then only channels 1 and/or 2 may be
      specified in chanfile.
  fixcolfileN: Specifies the name of an input text file containing a set of
        intercepts and slopes to be used for performing a de-striping fix for
        the columns for channel N (where N is 1 or 2) in a set of MOD02QKM or
        MYD02QKM data.
  fixrowfileN: Specifies the name of an input text file containing a set of
        intercepts and slopes to be used for performing a de-striping fix for
        the rows for channel N (where N is 1 or 2) in a set of MOD02QKM or
        MYD02QKM data.
      NOTE: If fixcolfileN or fixrowfileN is \"none\" (the default) then the
      corresponding col or row regressions for the corresponding channel will
      be performed and written to an output file. This file may then be
      specified as fixcolfileN or fixrowfileN in a subsequent call to mod02.pl.
      NOTE: If fix250 is not 1 or 2, then fixcolfileN and fixrowfileN are
      ignored.
  tile_cols: number of segments to use horizontally in breaking the specified
        grid into tiles. Default is 1. Must be greater than 0.
  tile_rows: number of segments to use vertically in breaking the specified
        grid into tiles. Default is 1. Must be greater than 0.
      NOTE: The total number of tiles produced will be tile_cols x tile_rows.
      If both tile_cols and tile_rows are equal to 1 (the defaults) then no
      tiling will be performed.
  tile_overlap: number of pixels to add around each tile edge that borders
        another tile. Default is 300. Must be greater than 0.
  maskfile: one byte per pixel image having 0 as the mask value.
  mask_factor: indicates the factor to use in expanding the mask file to
        match the dimensions of the grid defined by gpdfile. Must be greater
        than 0. The default value is 6.
  mask_keep: 0 delete all created mask files after gridding (default).
             1 do not delete any created mask files after gridding.
  swath_width_fraction: the central fraction of swath width to use.
             The default value is 1.0 except for Universal Transverse Mercator
             (UTM) projections where the default is 0.75.\n\n";

# this makes the routine work properly using require in other programs
1
