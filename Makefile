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
MAIN_PKG_DIR   = polar2grid

# Make sure target names are just the dir name with a suffix
# See targets for substitution
ALL_PKG_DIRS = $(MAIN_PKG_DIR)
ALL_PKG_INSTALL = $(ALL_PKG_DIRS:=_install)
ALL_PKG_SDIST = $(ALL_PKG_DIRS:=_sdist)
ALL_PKG_DEV = $(ALL_PKG_DIRS:=_dev)
DOC_DIR ?= /webdata/web/www/htdocs/software/polar2grid
GEO_DOC_DIR ?= /webdata/web/www/htdocs/software/geo2grid

DEV_FLAGS = -d $(INSTALL_DIR)
DOC_SERVER = $(DOC_SERVER:=webaccess.ssec.wisc.edu)

all: all_sdist

### PYTHON PACKAGING ###

all_install: $(ALL_PKG_INSTALL)

all_install2:
	pip install --no-deps dist/*.tar.gz

all_sdist: $(ALL_PKG_SDIST) clean_sdist_build

all_dev: $(ALL_PKG_DEV)

$(ALL_PKG_INSTALL): $(INSTALL_DIR)
	python setup.py install --prefix=$(INSTALL_DIR)

$(ALL_PKG_SDIST):
	python setup.py sdist

$(ALL_PKG_DEV): $(INSTALL_DIR)
	pip install -e . $(DEV_FLAGS)

$(INSTALL_DIR):
	mkdir -p $(INSTALL_DIR)

### Documentation Stuff ###
build_doc_html:
	cd doc; \
	make clean; \
	make html

FN = polar2grid_docs_$(shell date -u +%Y%m%d_%H%M%S).tar.gz
# Remake documentation and then update the main doc site
update_doc: build_doc_html
	cd doc/build/html; \
	echo $(FN); \
	tar -czf $(FN) *; \
	scp $(FN) $(DOC_SERVER):/tmp/; \
	ssh $(DOC_SERVER) "cd '$(DOC_DIR)'; rm -rf *; tar -xmzf /tmp/$(FN)"

build_doc_html_geo:
	cd doc; \
	make clean; \
	make html POLAR2GRID_DOC=geo

update_doc_geo: build_doc_html_geo
	cd doc/build/html; \
	echo $(FN); \
	tar -czf $(FN) *; \
	scp $(FN) $(DOC_SERVER):/tmp/; \
	ssh $(DOC_SERVER) "cd '$(GEO_DOC_DIR)'; rm -rf *; tar -xmzf /tmp/$(FN)"

### Clean up what we've done ###
clean_sdist:
	rm -rf $(DIST_DIR)

# This is ugly, but not sure how to make it better
clean_sdist_build:
	rm -rf $$pkg_dir/dist; \
	rm -rf $$pkg_dir/build;

clean:	clean_sdist	clean_sdist_build
