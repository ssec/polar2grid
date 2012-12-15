#========================================================================
# Makefile for fornav.c
#
# 27-Dec-2000 T.Haran 303-492-1847  tharan@kryos.colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/fornav/Makefile,v 1.6 2007/05/07 18:09:57 tharan Exp $

#------------------------------------------------------------------------
# configuration section
#
#	installation directories
#
TOPDIR = ../..
LIBDIR = $(TOPDIR)/lib
INCDIR = $(TOPDIR)/include
BINDIR = $(TOPDIR)/bin
#
#	commands
#
SHELL ?= /bin/sh
CC ?= cc
AR ?= ar
RANLIB ?= touch
CO ?= co
MAKEDEPEND ?= makedepend
INSTALL ?= cp
CP ?= cp
RM ?= rm -f
TAR ?= tar
COMPRESS ?= gzip

#
#	archive file name
#
TARFILE = fornav.tar

#
#	debug or optimization settings
#
#	on least significant byte first machines (Intel, Vax)
#	add -DLSB1ST option to enable byteswapping of cdb files
#
CONFIG_CFLAGS = -O
#CONFIG_CFLAGS = -O -Wall
#CONFIG_CFLAGS = -DDEBUG -g

#
#	system libraries
#
SYSLIBS = -lm

#
# end configuration section
#------------------------------------------------------------------------

CFLAGS = -I$(INCDIR) $(CONFIG_CFLAGS) $(getconf LFS_CFLAGS)
LIBS = -L$(LIBDIR) -lmapx $(SYSLIBS)

SRCS = fornav.c
OBJS = fornav.o
HDRS = 

all : fornav

fornav: fornav.o
	$(CC) $(CFLAGS) -o fornav fornav.o $(LIBS)
	$(CP) fornav $(BINDIR)

clean:
	- $(RM) $(OBJS) fornav

tar:
	- $(CO) Makefile $(SRCS) $(HDRS)
	$(TAR) cvf $(TARFILE) Makefile $(SRCS) $(HDRS)
	$(RM) $(TARFILE).gz
	$(COMPRESS) $(TARFILE)

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

