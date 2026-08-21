# Makefile to build the polar2grid/geo2grid documentation and upload it to the web server
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

DOC_DIR ?= /webdata/web/www/htdocs/software/polar2grid
GEO_DOC_DIR ?= /webdata/web/www/htdocs/software/geo2grid

DOC_SERVER = webaccess.ssec.wisc.edu

.PHONY: build_doc_html build_doc_html_geo update_doc update_doc_geo
.DEFAULT_GOAL := build_doc_html

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
