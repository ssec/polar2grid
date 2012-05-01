#========================================================================
# Makefile for ms2gt/src
#
# 13-Apr-2001 T.Haran 303-492-1847  tharan@colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /export/data/ms2gth/src/Makefile,v 1.5 2001/04/20 14:40:57 haran Exp $

#------------------------------------------------------------------------
# configuration section

#
#	installation directories
#
TOPDIR = ..
BINDIR = $(TOPDIR)/bin
DOCDIR = $(TOPDIR)/doc
GRDDIR = $(TOPDIR)/grids
INCDIR = $(TOPDIR)/include
LIBDIR = $(TOPDIR)/lib
SRCDIR = $(TOPDIR)/src

NAVDIR = $(SRCDIR)/fornav
GSZDIR = $(SRCDIR)/gridsize
IDLDIR = $(SRCDIR)/idl
LL2DIR = $(SRCDIR)/ll2cr
MAPDIR = $(SRCDIR)/maps
SCTDIR = $(SRCDIR)/scripts

L1BDIR = $(IDLDIR)/level1b_read
UTLDIR = $(IDLDIR)/modis_utils

#
#	commands
#
SHELL = /bin/sh
CC = cc
AR = ar
RANLIB = touch
CO = co
MAKEDEPEND = makedepend
INSTALL = cp
CP = cp
CD = cd
RM = rm -f
RMDIR = rm -fr
MKDIR = mkdir -p
TAR = tar
COMPRESS = gzip

#
#	debug or optimization settings
#
#	on least significant byte first machines (Intel, Vax)
#	add -DLSB1ST option to enable byteswapping of cdb files
#
CONFIG_CFLAGS = -O
#CONFIG_CFLAGS = -DDEBUG -g

#
# end configuration section
#------------------------------------------------------------------------

all:	srcs

srcs:
	$(CD) $(MAPDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(MAPDIR); $(MAKE) $(CONFIG_FLAGS) gtest
	$(CD) $(MAPDIR); $(MAKE) $(CONFIG_FLAGS) gridloc
	$(CD) $(GSZDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(LL2DIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(NAVDIR); $(MAKE) $(CONFIG_FLAGS) all

clean:
	$(CD) $(MAPDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(GSZDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(LL2DIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(NAVDIR); $(MAKE) $(CONFIG_FLAGS) clean

depend:
	- $(CO) $(SRCS) $(HDRS)
	$(MAKEDEPEND) -I$(INCDIR) \
		-- $(CFLAGS) -- $(SRCS)

.SUFFIXES : .c,v .h,v

.c,v.o :
	$(CO) $<
	$(CC) $(CFLAGS) -c $*.c
	- $(RM) $*.c

.c,v.c :
	$(CO) $<

.h,v.h :
	$(CO) $<

# DO NOT DELETE THIS LINE -- make depend depends on it.

