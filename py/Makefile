# Makefile to simplify polar2grid package operations
#
# Copyright (C) 2013 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    January 2013
#     University of Wisconsin-Madison 
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu

INSTALL_DIR ?= ./python
DIST_DIR ?= ./dist

CORE_PKG_DIR   = polar2grid_core
VIIRS_PKG_DIR  = polar2grid_viirs
MODIS_PKG_DIR  = polar2grid_modis
CREFL_PKG_DIR  = polar2grid_crefl
DRRTV_PKG_DIR  = polar2grid_drrtv
CRIS_PKG_DIR   = polar2grid_cris
IASI_PKG_DIR   = polar2grid_iasi
MAIN_PKG_DIR   = polar2grid

# Make sure target names are just the dir name with a suffix
# See targets for substitution
ALL_PKG_DIRS   = $(CORE_PKG_DIR) $(VIIRS_PKG_DIR) $(MODIS_PKG_DIR) $(CREFL_PKG_DIR) $(DRRTV_PKG_DIR) $(CRIS_PKG_DIR) $(MAIN_PKG_DIR)
ALL_PKG_SDIST  = $(ALL_PKG_DIRS:=_sdist)
#ALL_PKG_SDIST  = polar2grid_core_sdist polar2grid_viirs_sdist polar2grid_sdist
ALL_PKG_DEV    = polar2grid_core_dev polar2grid_viirs_dev polar2grid_modis_dev polar2grid_crefl_dev polar2grid_drrtv_dev polar2grid_dev
#DOC_DIR        = /home/davidh/test_doc
DOC_DIR        = /var/apache/www/htdocs/software/polar2grid

EGG_REPOS_MACHINE = birch
EGG_REPOS_DIR = /var/apache/larch/htdocs/eggs/repos/polar2grid/

all: all_sdist

### PYTHON PACKAGING ###

all_sdist: $(ALL_PKG_SDIST) clean_sdist_build

all_dev: $(ALL_PKG_DEV)

$(ALL_PKG_SDIST): $(DIST_DIR)
	cd $(@:_sdist=); \
	python setup.py sdist
	mv $(@:_sdist=)/dist/*.tar.gz $(DIST_DIR)

$(ALL_PKG_DEV): $(INSTALL_DIR)
	cd $(@:_dev=); \
	python setup.py develop -d $(INSTALL_DIR)

$(INSTALL_DIR):
	mkdir -p $(INSTALL_DIR)

$(DIST_DIR):
	mkdir -p $(DIST_DIR)

torepos:
	scp $(DIST_DIR)/*.tar.gz $(EGG_REPOS_MACHINE):$(EGG_REPOS_DIR)

### Documentation Stuff ###
build_doc_html:
	cd $(MAIN_PKG_DIR)/doc; \
	make clean; \
	make html

FN = polar2grid_docs_$(shell date -u +%Y%m%d_%H%M%S).tar.gz
# Remake documentation and then update the main doc site
update_doc: build_doc_html
	cd $(MAIN_PKG_DIR)/doc/build/html; \
	echo $(FN); \
	tar -czf $(FN) *; \
	scp $(FN) birch:/tmp/; \
	ssh birch "cd '$(DOC_DIR)'; rm -rf *; tar -xmzf /tmp/$(FN)"

### Clean up what we've done ###
clean_sdist:
	rm -rf $(DIST_DIR)

# This is ugly, but not sure how to make it better
clean_sdist_build:
	for pkg_dir in $(ALL_PKG_DIRS); do \
		rm -rf $$pkg_dir/dist; \
	done

clean:	clean_sdist	clean_sdist_build

