#========================================================================
# Makefile for lle2cre.c
#
# 26-Nov-2001 T.Haran 303-492-1847  tharan@kryos.colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/lle2cre/Makefile,v 1.5 2004/09/02 16:51:10 haran Exp $

include ../../Makefile.inc

#------------------------------------------------------------------------
# configuration section
#
#	archive file name
#
TARFILE = lle2cre.tar

#
# end configuration section
#------------------------------------------------------------------------

SRCS = lle2cre.c
OBJS = lle2cre.o
HDRS = 

all: lle2cre install

lle2cre: $(OBJS)
	$(CC) $(CFLAGS) -o lle2cre $(OBJS) $(LIBS)

install: lle2cre
	$(INSTALL) lle2cre $(BINDIR)

clean:
	- $(RM) $(OBJS) lle2cre

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

