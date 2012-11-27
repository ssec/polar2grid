#========================================================================
# makefile for ll2xy
#
# 30-Mar-2011 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/ll2xy/Makefile,v 1.2 2011/03/30 20:47:00 tharan Exp $

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
CO ?= co
MAKEDEPEND ?= makedepend
INSTALL ?= cp
RM ?= rm -f
TAR ?= tar
COMPRESS ?= gzip

#
#	archive file name
#
TARFILE = ll2xy.tar

#
#	debug or optimization settings
#
CONFIG_CFLAGS = -O
#CONFIG_CFLAGS = -DDEBUG -g
LOCAL_CFLAGS =

#
#	libraries
#
LOCAL_LIBS = -lmapx
SYSTEM_LIBS = -lm 

#
# end configuration section
#------------------------------------------------------------------------

CFLAGS = -I$(INCDIR) $(LOCAL_CFLAGS) $(CONFIG_CFLAGS)
LIBS = -L$(LIBDIR) $(LOCAL_LIBS) $(SYSTEM_LIBS)

SRCS = ll2xy.c
OBJS = ll2xy.o
HDRS = 

all: ll2xy install

ll2xy: $(OBJS)
	cc $(CFLAGS) -o ll2xy $(OBJS) $(LIBS)

install: ll2xy
	$(INSTALL) ll2xy $(BINDIR)

clean:
	- $(RM) $(OBJS) ll2xy

tar:
	- $(CO) Makefile $(SRCS) $(HDRS)
	$(TAR) cvf $(TARFILE) Makefile $(SRCS) $(HDRS)
	$(RM) $(TARFILE).gz
	$(COMPRESS) $(TARFILE)

depend:
	- $(CO) $(SRCS) $(HDRS)
	$(MAKEDEPEND) -I$(INCDIR) \
		-- $(CFLAGS) -- $(SRCS)

.SUFFIXES : .c,v .h,v .x .x,v

.c,v.o :
	$(CO) $<
	$(CC) $(CFLAGS) -c $*.c
	- $(RM) $*.c

.c,v.c :
	$(CO) $<

.h,v.h :
	$(CO) $<

