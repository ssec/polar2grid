#!/bin/bash
# script for jenkins to run tests on polar2grid

cd "$WORKSPACE"

# environment already has polar2grid installed on it
old_list=`/data/users/davidh/anaconda3/bin/conda list -n jenkins_p2g_env`
/data/users/davidh/anaconda3/bin/conda env update -n jenkins_p2g_env -f build_environment.yml
/data/users/davidh/anaconda3/bin/conda install -c conda-forge -n jenkins_p2g_env behave
new_list=`/data/users/davidh/anaconda3/bin/conda list -n jenkins_p2g_env`
/data/users/davidh/anaconda3/bin/conda init bash
source ~/.bashrc
source activate jenkins_p2g_env
if [ "$old_list" != "$new_list" ]; then
    tarball_name=polar2grid-swbundle-`date +"%Y%m%d-%H%M%S"`
    ./create_conda_software_bundle.sh $WORKSPACE/$tarball_name
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
else
    tarball_name=/tmp/polar2grid-swbundle-*
    if [ -s $tarball_name ]
    then
        cp -r $tarball_name $WORKSPACE
    fi
fi
echo $tarball_name
export POLAR2GRID_HOME="$WORKSPACE/$tarball_name"
cd "$WORKSPACE/integration_tests"
behave --no-logcapture --no-color --no-capture -D datapath=/data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data
exit $?
