# Global Makefile include file for all ms2gt Makefiles
# This file was created by David Hoese (SSEC) for the polar2grid project
# and is not part of the original ms2gt package

UNAME := $(shell uname)
TOPDIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

#
#	installation directories
#
BINDIR = $(TOPDIR)/bin
DOCDIR = $(TOPDIR)/doc
GRDDIR = $(TOPDIR)/grids
INCDIR = $(TOPDIR)/include
LIBDIR = $(TOPDIR)/lib
SRCDIR = $(TOPDIR)/src
TU1DIR = $(TOPDIR)/tutorial_1
TU2DIR = $(TOPDIR)/tutorial_2
TU3DIR = $(TOPDIR)/tutorial_3
TU4DIR = $(TOPDIR)/tutorial_4

NAVDIR = $(SRCDIR)/fornav
GCNDIR = $(SRCDIR)/grid_convert
GSZDIR = $(SRCDIR)/gridsize
IDLDIR = $(SRCDIR)/idl
LL2DIR = $(SRCDIR)/ll2cr
LLXDIR = $(SRCDIR)/ll2xy
LE2DIR = $(SRCDIR)/lle2cre
MAPDIR = $(SRCDIR)/mapx/trunk
PRJDIR = $(SRCDIR)/projection
SCTDIR = $(SRCDIR)/scripts
UTSDIR = $(SRCDIR)/utils
XY2DIR = $(SRCDIR)/xy2ll

L1BDIR = $(IDLDIR)/level1b_read
UTLDIR = $(IDLDIR)/modis_utils

#
#	special cases
#
# The mapx Makefile for ms2gt has a special name
MAPMAK = -f Makefile.ms2gt

#
#	commands
#
SHELL ?= /bin/sh
AR ?= ar
CO ?= co
MAKEDEPEND ?= makedepend
INSTALL ?= cp
CP ?= cp
CD ?= cd
RM ?= rm -f
RMDIR ?= rm -fr
MKDIR ?= mkdir -p
TAR ?= tar
COMPRESS ?= gzip
ifeq ($(UNAME), Darwin)
	CC = gcc
	RANLIB ?= ranlib
else
	CC = cc
	RANLIB ?= touch
endif

#
#	debug or optimization settings
#
#	on least significant byte first machines (Intel, Vax)
#	add -DLSB1ST option to enable byteswapping of cdb files
#	for other architectures (Sun, SGI, HP, etc.) do _not_ use
#	the -DLSB1ST flag
#	The cdb files are only in the mapx library
CONFIG_CFLAGS ?= -O -DLSB1ST
#CONFIG_CFLAGS ?= -O
#CONFIG_CFLAGS ?= -DDEBUG -g
#CONFIG_CFLAGS ?= -DDEBUG -g -DLSB1ST
#CONFIG_CFLAGS ?= -O -Wall -DLSB1ST
ifeq ($(UNAME), Darwin)
	LDFLAGS ?= 
else
	LDFLAGS ?= -static
endif

#
#	system libraries
#
LOCAL_LIBS = -lmapx
SYSLIBS = -lm

#
#	Compile and link flags
#
CFLAGS = -I$(INCDIR) $(CONFIG_CFLAGS) $(LDFLAGS)
LIBS = -L$(LIBDIR) $(LOCAL_LIBS) $(SYSLIBS)

