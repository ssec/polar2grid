#========================================================================
# makefile for ll2xy
#
# 30-Mar-2011 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/ll2xy/Makefile,v 1.2 2011/03/30 20:47:00 tharan Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section
#
#	archive file name
#
TARFILE = ll2xy.tar

#
# end configuration section
#------------------------------------------------------------------------

SRCS = ll2xy.c
OBJS = ll2xy.o
HDRS = 

all: ll2xy install

ll2xy: $(OBJS)
	$(CC) $(CFLAGS) -o ll2xy $(OBJS) $(LIBS)

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

