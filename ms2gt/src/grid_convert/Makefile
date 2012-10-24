#========================================================================
# makefile for grid_convert
#
# 5-Jul-2006 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /data/haran/ms2gth/src/grid_convert/Makefile,v 1.2 2006/07/05 17:16:15 tharan Exp $

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
TARFILE = grid_convert.tar

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

SRCS = grid_convert.c
OBJS = grid_convert.o
HDRS = 

all: grid_convert install

grid_convert: $(OBJS)
	cc $(CFLAGS) -o grid_convert $(OBJS) $(LIBS)

install: grid_convert
	$(INSTALL) grid_convert $(BINDIR)

clean:
	- $(RM) $(OBJS) grid_convert

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

