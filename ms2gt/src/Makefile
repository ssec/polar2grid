#========================================================================
# Makefile for ms2gt/src
#
# 13-Apr-2001 T.Haran 303-492-1847  tharan@colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/src/Makefile,v 1.14 2011/03/30 20:47:15 tharan Exp $

include ../Makefile.inc

all:	srcs

srcs:
	$(CD) $(MAPDIR); $(MAKE) $(CONFIG_FLAGS) $(MAPMAK) allall
	$(CD) $(GCNDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(GSZDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(LL2DIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(LLXDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(LE2DIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(NAVDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(PRJDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(UTSDIR); $(MAKE) $(CONFIG_FLAGS) all
	$(CD) $(XY2DIR); $(MAKE) $(CONFIG_FLAGS) all

clean:
	$(CD) $(MAPDIR); $(MAKE) $(CONFIG_FLAGS) $(MAPMAK) cleanall
	$(CD) $(GCNDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(GSZDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(LL2DIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(LLXDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(LE2DIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(NAVDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(PRJDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(UTSDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(CD) $(XY2DIR); $(MAKE) $(CONFIG_FLAGS) clean

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

