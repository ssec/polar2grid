#========================================================================
# makefile for projection
#
# 03-Sep-2010 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /data/tharan/ms2gth/src/projection/Makefile,v 1.1 2010/09/03 18:14:11 tharan Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section
#
#	archive file name
#
TARFILE = projection.tar

#
# end configuration section
#------------------------------------------------------------------------

SRCS = projection.c
OBJS = projection.o
HDRS = 

all: projection install

projection: $(OBJS)
	$(CC) $(CFLAGS) -o projection $(OBJS) $(LIBS)

install: projection
	$(INSTALL) projection $(BINDIR)

clean:
	- $(RM) $(OBJS) projection

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

