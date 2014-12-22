#========================================================================
# Makefile for fornav.c
#
# 27-Dec-2000 T.Haran 303-492-1847  tharan@kryos.colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/fornav/Makefile,v 1.6 2007/05/07 18:09:57 tharan Exp $

CFLAGS += -O3 $(getconf LFS_CFLAGS)

SRCS = fornav.c
OBJS = fornav.o

all : fornav

fornav: fornav.c
	$(CC) $(CFLAGS) -o $@ $< -lm

clean:
	- $(RM) $(OBJS) fornav

tar:
	- $(CO) Makefile $(SRCS) $(HDRS)
	$(TAR) cvf $(TARFILE) Makefile $(SRCS) $(HDRS)
	$(RM) $(TARFILE).gz
	$(COMPRESS) $(TARFILE)

# DO NOT DELETE THIS LINE -- make depend depends on it.

