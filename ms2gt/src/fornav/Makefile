#========================================================================
# Makefile for fornav.c
#
# 27-Dec-2000 T.Haran 303-492-1847  tharan@kryos.colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/fornav/Makefile,v 1.6 2007/05/07 18:09:57 tharan Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section

#
#	archive file name
#
TARFILE = fornav.tar

#
# end configuration section
#------------------------------------------------------------------------

CFLAGS += $(getconf LFS_CFLAGS)

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

