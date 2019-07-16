#!/usr/bin/env bash
# Only run by Jenkins if build was successful.

cp -r  $WORKSPACE/$tarball_name /tmp
prev_val=0
prev_fn=""
for fn in /tmp/polar2grid-swbundle-*
do
    var1=`echo ${fn/*polar2grid-swbundle-/} | sed -r 's/[-]+//g'`
    var1="$((var1))"
    if [ $var1 -ge $prev_val ]
    then
        if [ -s $prev_fn ]
        then
            rm -rf $prev_fn
        fi
    fi
    prev_val=$var1
    prev_fn=$fn
done
exit $?