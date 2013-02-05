#========================================================================
# makefile for ll2cr
#
# 23-Oct-2000 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /data/tharan/ms2gth/src/gridsize/Makefile,v 1.2 2004/08/25 23:22:24 haran Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section
#
#	archive file name
#
TARFILE = gridsize.tar

#
# end configuration section
#------------------------------------------------------------------------

SRCS = gridsize.c
OBJS = gridsize.o
HDRS = 

all: gridsize install

gridsize: $(OBJS)
	$(CC) $(CFLAGS) -o gridsize $(OBJS) $(LIBS)

install: gridsize
	$(INSTALL) gridsize $(BINDIR)

clean:
	- $(RM) $(OBJS) gridsize

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

