#!/usr/bin/env bash
# Only run by Jenkins if build was successful.

cp -r $WORKSPACE/$tarball_name /tmp
prev_val=0
prev_fn=""
for fn in /tmp/polar2grid-swbundle-*
do
    new_val=`echo ${fn/*polar2grid-swbundle-/} | sed -r 's/[-]+//g'`
    new_val="$((new_val))"
    if [ new_val -ge $prev_val ]
    then
        if [ -s $prev_fn ]
        then
            rm -rf $prev_fn
        fi
    fi
    prev_val=new_val
    prev_fn=$fn
done
exit $?