#========================================================================
# makefile for ll2cr
#
# 23-Oct-2000 Terry Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/ll2cr/Makefile,v 1.7 2004/08/25 23:25:11 haran Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section
#
#	archive file name
#
TARFILE = ll2cr.tar

#
# end configuration section
#------------------------------------------------------------------------

CFLAGS += $(getconf LFS_CFLAGS)

SRCS = ll2cr.c
OBJS = ll2cr.o
HDRS = 

all: ll2cr install

ll2cr: $(OBJS)
	$(CC) $(CFLAGS) -o ll2cr $(OBJS) $(LIBS)

install: ll2cr
	$(INSTALL) ll2cr $(BINDIR)

clean:
	- $(RM) $(OBJS) ll2cr

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

