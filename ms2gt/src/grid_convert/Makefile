#========================================================================
# makefile for grid_convert
#
# 5-Jul-2006 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /data/haran/ms2gth/src/grid_convert/Makefile,v 1.2 2006/07/05 17:16:15 tharan Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section
#
#	archive file name
#
TARFILE = grid_convert.tar

#
# end configuration section
#------------------------------------------------------------------------

SRCS = grid_convert.c
OBJS = grid_convert.o
HDRS = 

all: grid_convert install

grid_convert: $(OBJS)
	$(CC) $(CFLAGS) -o grid_convert $(OBJS) $(LIBS)

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

