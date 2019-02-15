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
#     Written by David Hoese    December 2014
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
	CFLAGS ?= -O3
else
	CFLAGS ?= -O3 -static
endif
LDFLAGS ?=
LDLIBS ?= -lsz
PREFIX ?= .

all: crefl tbase.hdf

all_dynamic: CFLAGS := -O
all_dynamic: all

crefl: crefl.c
	$(CC) -o $@ $(CFLAGS) $< ${LDFLAGS} -lmfhdf -ldf -ljpeg ${LDLIBS} -lz -lm

tbase.hdf:
	wget https://www.ssec.wisc.edu/~davidh/polar2grid/modis_crefl/tbase.hdf

.PHONY: install prebuilt_crefl prebuilt all_dynamic clean clean_all
install: tbase.hdf crefl run_modis_crefl.sh
	mkdir -p $(PREFIX)/bin; \
	cp $^ $(PREFIX)/bin; \
	chmod u+x $(PREFIX)/bin/crefl; \
	chmod u+x $(PREFIX)/bin/run_modis_crefl.sh

prebuilt_crefl:
	wget https://www.ssec.wisc.edu/~davidh/polar2grid/modis_crefl/crefl

prebuilt: prebuilt_crefl tbase.hdf

clean:
	rm -f *.o crefl

clean_all: clean
	rm -f tbase.hdf

