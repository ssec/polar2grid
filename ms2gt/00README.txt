Readme for MODIS Swath-to-Grid Toolbox 0.5 --  31 May 2001
Terry Haran
National Snow and Ice Data Center
tharan@colorado.edu
303-492-1847

The MODIS Swath-to-Grid Toolbox (MS2GT) is a set of software tools that
can be used to read HDF-EOS files containing MODIS swath data and produce
flat binary files containing gridded data in a variety of map
projections. Multiple input files corresponding to successively acquired 5
minute MODIS "scenes" can be processed together to produce a seamless
output grid.

MS2GT consists of three perl programs that make calls to several
standalone IDL and C programs: mod02.pl which reads MOD02 Level 1b files,
mod10_l2.pl which reads MOD10_L2 snow cover files, and mod29.pl which
reads MOD29 sea ice files.  All three Perl programs can optionally read
MOD03 files for geolocation and/or ancillary data.

The software and associated documentation can be downloaded
from ftp://baikal.colorado.edu/pub/NSIDC/ms2gt0.5.tar.gz. Save this file in
some directory and type:

gunzip ms2gt0.5.tar.gz
tar xvf ms2gt0.5.tar 

This will create a directory called ms2gt in the current directory
containing several subdirectories. Further instructions on the
installation and use of MS2GT can be then found in html files in the
ms2gt/doc subdirectory. Point your browser to ms2gt/doc/index.html.
