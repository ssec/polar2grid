Corrected Reflectance

OVERVIEW:

Corrected Reflectance (Version 1.7.1)

The Corrected Reflectance algorithm performs a simple atmospheric correction
with MODIS visible, near-infrared, and short-wave infrared bands (1 to 16).
It corrects for molecular (Rayleigh) scattering and gaseous absorption (water
vapor, ozone) using climatological values for gas contents.  It requires no
real-time input of ancillary data.  The algorithm performs no aerosol
correction.  The Corrected Reflectance products are very similar to the MODIS
Land Surface Reflectance product (MOD09) in clear atmospheric conditions, since
the algorithms used to derive both are based on the 6S Radiative Transfer Model
(Vermote et al.1994).  The products show differences in the presence of
aerosols, however, because the MODIS Land Surface Reflectance product uses a
more complex atmospheric correction algorithm that includes a correction for
aerosols.

This algorithm was originally developed by the MODIS Rapid Response Team
(http://rapidfire.sci.gsfc.nasa.gov/) and made available by cooperative
agreement, with subsequent additions by the University of South Florida (USF)
and the NASA Direct Readout Laboratory (DRL).

VERSION CHANGES:

  Merged multiple independent code versions from the original author (J.
  Descloitres), the MODIS Rapid Response Team, and the University of South
  Florida into the current release.

  General code clean-up and restructuring to simplify maintenance and future
  enhancement.  New functions include usage(), input_file_type(), parse_bands(),
  set_dimnames(), init_output_sds(), write_scan(), read_scan(), interp_dem(),
  range_check(), and write_global_attributes().

  Added meaningful HDF dimensions names to HDF output files, i.e., the numerous
  "fakeDim1", "fakeDim2", "fakeDim3", etc., dimensions names have been replaced
  with "lines_250m", "samples_250m", "lines_500m", etc.)

  Added code to write global metadata as standard HDF attributes to the output
  file.

  Added code to check memory allocation and to free allocated memory.

  Eliminated superfluous double precision floating point calculations.

  Added command line switches for several internal options (nearest, TOA,
  sealevel).

  MODIS bands 8-16 may now be processed in addition to bands 1-7.

  Fix for bug in HDF SDgetinfo() function.

  Rewrote custom command line parsing code to use standard getopt_long()
  function.

  Added range checking to various user-specified parameters.

  Eliminated much code that copied strings already resident in memory into
  redundant character arrays.

  Merged several instances of redundant looping.


INSTALLATION:

The software compiles and runs under several different versions of Linux,
including Fedora Core 8 Linux and above. The code should compile and run on any
POSIX semi-compliant system, and in principal it should not be difficult to
build on any platform with an ANSI C compiler.

The Hierarchical Data Format library, HDF4.1r3 or later, is required. The HDF library
is not included in this package and must be installed prior to compilation of
these algorithms. See Documentation for further details.

RUN:

The Corrected Reflectance algorithm requires the 1 km, 500m, and 250m
radiometrically corrected, geolocated output from Level 1B (MOD21KM, MOD21HKM,
and MOD02QKM) in HDF4 format as inputs. Processing usually requires one
ancillary data set, a coarse resolution DEM, which is included (National
Geophysical Data Center TerrainBase Global DTM, Version 1.0).  The output is
in HDF format and contains a corrected reflectance SDS for each band specified
on the command line.

REFERENCE:

Vermote E., Tanré D., Deuzé J.L., Herman M., Morcrette J.J., "Second
Simulation of the Satellite Signal in the Solar Spectrum (6S)", 6S User Guide
Version 0, 1994. (http://6s.ltdri.org/).

BUILD:

Set the environment variable HDFHOME.
Run 'make' in the src directory.

INSTALL:

Place the binaries in any convienient directory.
Place the tbase.hdf file in a accessible directory.

EXECUTION:

A script is provided in this directory, 'run.csh', which demonstrates
the input requirements and calling sequence.
