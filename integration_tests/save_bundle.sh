#!/usr/bin/env bash
# Only run by Jenkins if build was successful.

for fn in /tmp/polar2grid-swbundle-*
do
    rm -rf $fn
done
cp -r $POLAR2GRID_HOME /tmp
exit $?