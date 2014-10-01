# Simplify compiling CREFL. Compile commands were copied from original files and modified to fit Makefile (see readme).
#
# Example Compile Usage (where static dependencies headers and libaries are in ~/opt/):
#       LDFLAGS="-I ~/opt/include -L ~/opt/lib" make
#
# Example Install Usage (where files will be installed in ~/bin):
#       PREFIX="~" make install
#
# Example Dynamic Compile/Link Usage:
#		make all_dynamic
#
# Example Dynamic Compile/Link Usage (with specialized library locations)
# 		LD_RUN_PATH=/home/user/opt/lib LDFLAGS="-I ~opt/include -L ~/opt/lib" make all_dynamic
#
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
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

UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
	CFLAGS ?= -O
else
	CFLAGS ?= -O -static
endif
LDFLAGS ?=
LDLIBS ?= -lsz
PREFIX ?= .

all: h5SDS_transfer_rename cviirs CMGDEM.hdf

all_dynamic: CFLAGS := -O
all_dynamic: all

h5SDS_transfer_rename: h5SDS_transfer_rename.c
	$(CC) -o $@ $(CFLAGS) $< $(LDFLAGS) -lhdf5 -lmfhdf -ldf -ljpeg $(LDLIBS) -lz -lm -ldl

cviirs: cviirs.c
	$(CC) -o $@ -m64 $(CFLAGS) $< $(LDFLAGS) -lmfhdf -ldf -ljpeg $(LDLIBS) -lz -lm

CMGDEM.hdf:
	wget http://www.ssec.wisc.edu/~davidh/polar2grid/viirs_crefl/CMGDEM.hdf

.PHONY: install prebuilt_h5SDS_transfer_rename prebuilt_cviirs prebuilt all_dynamic clean clean_all
install: CMGDEM.hdf h5SDS_transfer_rename cviirs run_viirs_crefl.sh
	mkdir -p $(PREFIX)/bin; \
	cp $^ $(PREFIX)/bin; \
	chmod u+x $(PREFIX)/bin/cviirs; \
	chmod u+x $(PREFIX)/bin/h5SDS_transfer_rename; \
	chmod u+x $(PREFIX)/bin/run_viirs_crefl.sh

prebuilt_h5SDS_transfer_rename:
	wget  http://www.ssec.wisc.edu/~davidh/polar2grid/viirs_crefl/h5SDS_transfer_rename; \
	chmod u+x h5SDS_transfer_rename

prebuilt_cviirs:
	wget  http://www.ssec.wisc.edu/~davidh/polar2grid/viirs_crefl/cviirs; \
	chmod u+x cviirs

prebuilt: prebuilt_h5SDS_transfer_rename prebuilt_cviirs CMGDEM.hdf

clean:
	rm -f h5SDS_transfer_rename
	rm -f cviirs

clean_all: clean
	rm -f CMGDEM.hdf
