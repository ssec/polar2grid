# Simplify compiling CREFL. Compile commands were copied from original files and modified to fit Makefile.
#
# Example Compile Usage (where static dependencies headers and libaries are in ~/opt/):
#       LDFLAGS="-I ~/opt/include -L ~/opt/lib" make
#
# Example Install Usage (where files will be installed in ~/bin):
#       PREFIX="~" make install
#
# Copyright (C) 2013 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    February 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

CFLAGS = -O -static
LDFLAGS ?=
PREFIX ?= .

all: h5SDS_transfer_rename cviirs

h5SDS_transfer_rename: h5SDS_transfer_rename.c
	$(CC) -o $@ $(CFLAGS) $< $(LDFLAGS) -lhdf5 -lmfhdf -ldf -ljpeg -lz -lm -ldl

cviirs: cviirs.c
	$(CC) -o $@ -m64 $(CFLAGS) $< $(LDFLAGS) -lmfhdf -ldf -ljpeg -lz -lm

CMGDEM.hdf:
	wget http://www.ssec.wisc.edu/~davidh/polar2grid/viirs_crefl/CMGDEM.hdf

.PHONY: install prebuilt clean
install: CMGDEM.hdf h5SDS_transfer_rename cviirs
	mkdir -p $(PREFIX)/bin; \
	mv $^ $(PREFIX)/bin

prebuilt:
	wget  http://www.ssec.wisc.edu/~davidh/polar2grid/viirs_crefl/h5SDS_transfer_rename
	wget  http://www.ssec.wisc.edu/~davidh/polar2grid/viirs_crefl/cviirs

clean:
	rm -f CMGDEM.hdf
	rm -f h5SDS_transfer_rename
	rm -f cviirs
