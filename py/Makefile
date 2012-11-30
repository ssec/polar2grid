# Makefile to simplify polar2grid package operations
# Author: David Hoese, SSEC

INSTALL_DIR ?= ./python
DIST_DIR ?= ./dist

CORE_PKG_DIR   = polar2grid_core
VIIRS_PKG_DIR  = polar2grid_viirs
MAIN_PKG_DIR   = polar2grid

# Make sure target names are just the dir name with a suffix
# See targets for substitution
ALL_PKG_DIRS   = $(CORE_PKG_DIR) $(VIIRS_PKG_DIR) $(MAIN_PKG_DIR)
ALL_PKG_SDIST  = $(ALL_PKG_DIRS:=_sdist)
#ALL_PKG_SDIST  = polar2grid_core_sdist polar2grid_viirs_sdist polar2grid_sdist
ALL_PKG_DEV    = polar2grid_core_dev polar2grid_viirs_dev polar2grid_dev

all: all_sdist

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

### Clean up what we've done ###
clean_sdist:
	rm -rf $(DIST_DIR)

# This is ugly, but not sure how to make it better
clean_sdist_build:
	for pkg_dir in $(ALL_PKG_DIRS); do \
		rm -rf $$pkg_dir/dist; \
	done

clean:	clean_sdist	clean_sdist_build

