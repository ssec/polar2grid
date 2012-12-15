#========================================================================
# makefile for xy2ll
#
# 30-Mar-2011 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/xy2ll/Makefile,v 1.2 2011/03/30 20:45:57 tharan Exp $

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
TARFILE = xy2ll.tar

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

SRCS = xy2ll.c
OBJS = xy2ll.o
HDRS = 

all: xy2ll install

xy2ll: $(OBJS)
	cc $(CFLAGS) -o xy2ll $(OBJS) $(LIBS)

install: xy2ll
	$(INSTALL) xy2ll $(BINDIR)

clean:
	- $(RM) $(OBJS) xy2ll

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

