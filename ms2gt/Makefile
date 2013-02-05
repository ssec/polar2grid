#========================================================================
# Makefile for ms2gt
#
# 12-Apr-2001 T.Haran 303-492-1847  tharan@colorado.edu
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================
RCSID = $Header: /disks/megadune/data/tharan/ms2gth/Makefile,v 1.40 2012/07/24 21:50:03 tharan Exp $

include Makefile.inc

#------------------------------------------------------------------------
# configuration section

#
#       define current version and release
#
VERSION = 0
RELEASE = 24a

#
#	installation target directories
#
TARDIRNAME = ms2gt$(VERSION).$(RELEASE)
TARDIR = $(TOPDIR)/$(TARDIRNAME)
TBINDIR = $(TARDIR)/bin
TDOCDIR = $(TARDIR)/doc
TGRDDIR = $(TARDIR)/grids
TINCDIR = $(TARDIR)/include
TLIBDIR = $(TARDIR)/lib
TSRCDIR = $(TARDIR)/src
TTU1DIR = $(TARDIR)/tutorial_1
TTU2DIR = $(TARDIR)/tutorial_2
TTU3DIR = $(TARDIR)/tutorial_3
TTU4DIR = $(TARDIR)/tutorial_4

TNAVDIR = $(TSRCDIR)/fornav
TGCNDIR = $(TSRCDIR)/grid_convert
TGSZDIR = $(TSRCDIR)/gridsize
TIDLDIR = $(TSRCDIR)/idl
TLL2DIR = $(TSRCDIR)/ll2cr
TLLXDIR = $(TSRCDIR)/ll2xy
TLE2DIR = $(TSRCDIR)/lle2cre
TMAPDIR = $(TSRCDIR)/mapx/trunk
TPRJDIR = $(TSRCDIR)/projection
TSCTDIR = $(TSRCDIR)/scripts
TUTSDIR = $(TSRCDIR)/utils
TXY2DIR = $(TSRCDIR)/xy2ll

TL1BDIR = $(TIDLDIR)/level1b_read
TUTLDIR = $(TIDLDIR)/modis_utils

#
#	archive file name
#
TARFILE = $(TOPDIR)/ms2gt$(VERSION).$(RELEASE).tar

#
# end configuration section
#------------------------------------------------------------------------

#
#	makefiles
#
SRCMAKE	= $(SRCDIR)/Makefile
NAVMAKE = $(NAVDIR)/Makefile
GCNMAKE = $(GCNDIR)/Makefile
GSZMAKE = $(GSZDIR)/Makefile
LL2MAKE = $(LL2DIR)/Makefile
LLXMAKE = $(LLXDIR)/Makefile
LE2MAKE = $(LE2DIR)/Makefile
MAPMAKE = $(MAPDIR)/Makefile.ms2gt
PRJMAKE = $(PRJDIR)/Makefile
UTSMAKE = $(UTSDIR)/Makefile
XY2MAKE = $(XY2DIR)/Makefile

GPDSRCS = $(GRDDIR)/*.gpd
MPPSRCS = $(GRDDIR)/*.mpp

L1BSRCS = $(L1BDIR)/*.pro $(L1BDIR)/*.txt
UTLSRCS = $(UTLDIR)/*.pro

NAVSRCS = $(NAVMAKE) $(NAVDIR)/*.c
GCNSRCS = $(GCNMAKE) $(GCNDIR)/*.c
GSZSRCS = $(GSZMAKE) $(GSZDIR)/*.c
IDLSRCS = $(L1BSRCS) $(UTLSRCS)
LL2SRCS = $(LL2MAKE) $(LL2DIR)/*.c
LLXSRCS = $(LLXMAKE) $(LLXDIR)/*.c
LE2SRCS = $(LE2MAKE) $(LE2DIR)/*.c
MAPSRCS = $(MAPMAKE) $(MAPDIR)/*.c $(MAPDIR)/*.h $(MAPDIR)/*.mpp
PRJSRCS = $(PRJMAKE) $(PRJDIR)/*.c
SCTSRCS = $(SCTDIR)/*.pl
UTSSRCS = $(UTSMAKE) $(UTSDIR)/*.c
XY2SRCS = $(XY2MAKE) $(XY2DIR)/*.c

BINS = $(TOPDIR)/bin/*
TOPS = $(TOPDIR)/*.txt $(TOPDIR)/Makefile $(TOPDIR)/ms2gt_env.csh
DOCS = $(DOCDIR)/*.html $(DOCDIR)/*usage $(DOCDIR)/*.gif
HDRS = $(INCDIR)/*.h
GRDS = $(GPDSRCS) $(MPPSRCS)
SRCS = $(SRCMAKE) $(NAVSRCS) $(IDLSRCS) $(LL2SRCS) $(LLXSRCS) $(LE2SRCS) \
       $(MAPSRCS) $(SCTSRCS) $(UTSSRCS) $(XY2SRCS)
TU1S = $(TU1DIR)/*.txt $(TU1DIR)/*.gpd $(TU1DIR)/*.csh
TU2S = $(TU2DIR)/*.txt $(TU2DIR)/*.gpd $(TU2DIR)/*.csh
TU3S = $(TU3DIR)/*.txt $(TU3DIR)/*.gpd $(TU3DIR)/*.mpp $(TU3DIR)/*.csh
TU4S = $(TU4DIR)/*.txt $(TU4DIR)/*.gpd $(TU4DIR)/*.mpp $(TU4DIR)/*.csh

all:	srcs

srcs:
	$(CD) $(SRCDIR); $(MAKE) $(CONFIG_FLAGS) all

clean:
	$(CD) $(SRCDIR); $(MAKE) $(CONFIG_FLAGS) clean
	$(RM) $(LIBDIR)/libmaps.a

tar:
	- $(CO) $(TOPS) $(DOCS) $(HDRS) $(SRCS) $(TU1S) $(TU2S) $(TU3S) $(TU4S)
	- $(RMDIR) $(TARDIR)
	$(MKDIR) $(TARDIR)
	$(MKDIR) $(TBINDIR) $(TDOCDIR) $(TGRDDIR) $(TINCDIR) $(TLIBDIR)
	$(MKDIR) $(TSRCDIR)
	$(MKDIR) $(TNAVDIR) $(TGCNDIR) $(TGSZDIR) $(TLL2DIR) $(TLLXDIR) \
                 $(TLE2DIR) $(TMAPDIR) $(TPRJDIR) \
                 $(TSCTDIR) $(TUTSDIR) $(TXY2DIR)
	$(MKDIR) $(TIDLDIR) $(TL1BDIR) $(TUTLDIR)
	$(MKDIR) $(TTU1DIR) $(TTU2DIR) $(TTU3DIR) $(TTU4DIR)
	$(CP) $(TOPS) $(TARDIR)
	$(CP) $(BINS) $(TBINDIR)
	$(CP) $(DOCS) $(TDOCDIR)
	$(CP) $(HDRS) $(TINCDIR)
	$(CP) $(GRDS) $(TGRDDIR)
	$(CP) $(SRCMAKE) $(TSRCDIR)
	$(CP) $(NAVSRCS) $(TNAVDIR)
	$(CP) $(GCNSRCS) $(TGCNDIR)
	$(CP) $(GSZSRCS) $(TGSZDIR)
	$(CP) $(L1BSRCS) $(TL1BDIR)
	$(CP) $(UTLSRCS) $(TUTLDIR)
	$(CP) $(LL2SRCS) $(TLL2DIR)
	$(CP) $(LLXSRCS) $(TLLXDIR)
	$(CP) $(LE2SRCS) $(TLE2DIR)
	$(CP) $(MAPSRCS) $(TMAPDIR)
	$(CP) $(PRJSRCS) $(TPRJDIR)
	$(CP) $(SCTSRCS) $(TSCTDIR)
	$(CP) $(UTSSRCS) $(TUTSDIR)
	$(CP) $(XY2SRCS) $(TXY2DIR)
	$(CP) $(TU1S) $(TTU1DIR)
	$(CP) $(TU2S) $(TTU2DIR)
	$(CP) $(TU3S) $(TTU3DIR)
	$(CP) $(TU4S) $(TTU4DIR)
	$(CD) $(TOPDIR); \
	$(TAR) cvf $(TARFILE) $(TARDIRNAME);
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

