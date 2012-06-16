polar2grid software bundle
==========================
Author: David Hoese
Organization: University of Wisconsin - Space Science and Engineering Center
Rev Id: $Id$

Installation
============
1. Untar the tarball:
    # if you're reading this, this step is probably complete already
    tar -xzf polar2grid-swbundle-<version>.tar.gz
2. Add the following line to your .bash_profile or .bashrc:
    export POLAR2GRID_HOME=/path/to/untarred-swbundle-dir

To Run A polar2grid Script
==========================
The polar2grid scripts are usually part of a larger system, but if you want
to run a script manually:

    $POLAR2GRID_HOME/bin/viirs2awips.sh ...

or

    $POLAR2GRID_HOME/bin/viirs2awips.sh --help

for more help.

