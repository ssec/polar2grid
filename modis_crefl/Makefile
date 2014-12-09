#==============================================================
# NDVI_EVI Make File
#
# Based on Makefile for Makefile for make_ndvi, modified by
#     A. Lunsford, 23 September 2003
#     G. Reichert, 26 June 2002
# Coded by C. Hoisington, Science Systems and Applications, Inc.
# 21 Sep 2001 Version 1.0
# 20 Mar 2003 modified by G. Reichert for use in velma "sandbox"
#             /raid/nppop/software/NDVI/NDVI.src/
# AUg 21 2007 modified at DRL for Cref_SPA release
#
#
# Note:
# 	Set enviroment variable HDFHOME to point to your local HDF4.1 
# 	installation.
#
#==============================================================

#HDFHOME=/home/mruebens/crefl/trunk/algorithm/hdf32
HDFHOME=/opt/local
#------------------------------------------------------------------------------
# Modify:
#	HDFHOME (see above),
# 	COMPILER to be your local C compiler,
#	CFLAGS to add installation-specific compiler or loader flags,
#	LOCAL_LIB to add installation required libraries
#------------------------------------------------------------------------------

COMPILER  = gcc
CFLAGS    = -O3

HDFLIB = $(HDFHOME)/lib
HDFINC = $(HDFHOME)/include

LIB   = -L$(HDFLIB) -lmfhdf -ldf -ljpeg -lz -lm
INC   = -I$(HDFINC)

all:	crefl

crefl: crefl.1.7.1.c
	$(COMPILER) $(CFLAGS) crefl.1.7.1.c  -o crefl.1.7.1  ${INC} ${LIB}

clean:
	rm -f *.o crefl.1.7.1

