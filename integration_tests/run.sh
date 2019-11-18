#!/bin/bash
# Script for jenkins to run tests on polar2grid.
# Optional commit message requests (pick one only): [skip-tests], [p2g], [g2g], [p2g-skip-tests], and [g2g-skip-tests].
# The git tag name can be used to specify a release and the name specified by it will be used for the tarball/tests.
# Example; Create a release polar2grid tarball without running tests and release it as
#          polar2grid-swbundle-1.0.0b.tar.gz along with its documentation in
#          bumi:/tmp/polar2grid-swbundle-1.0.0b if all tests pass:
#          $ git commit -m "Change wording in polar2grid documentation [skip-tests]"
#          $ git tag -a p2g-v1.0.0b -m "P2G version 1.0.0b"
#          $ git push --follow-tags
# Note that in the above example both [skip-tests] and [p2g-skip-tests] would work the same since the tag specifies p2g.
# Example; Create a polar2grid tarball without running tests, but do not release as a version. The tarball and its
#          documentation can be found in bumi:/tmp/polar2grid-swbundle-YYYYmmhh-HHMMSS:
#          $ git commit -m "Test that polar2grid documentation builds [p2g-skip-tests]"
#          $ git push
# Example; Create a non-release geo2grid tarball and run tests on it. The tarball and its
#           documentation can be found in bumi:/tmp/geo2grid-swbundle-YYYYmmhh-HHMMSS:
#          $ git commit -m "Update abi_l1b in geo2grid [g2g]"
#          $ git push
# Example; Create both a non-release geo2grid and a non-release polar2grid tarball and run tests on them. The
#          tarballs and their documentation can be found in bumi:/tmp/geo2grid-swbundle-YYYYmmhh-HHMMSS and
#          bumi:/tmp/polar2grid-swbundle-YYYYmmhh-HHMMSS:
#          $ git commit -m "Update geo2grid and polar2grid"
#          $ git push
# Example; Create a geo2grid tarball, run tests on it, and release it as geo2grid-swbundle-3.0.0.tar.gz if all tests
#          pass. The tarball and its documentation can be found in bumi:/tmp/geo2grid-swbundle-YYYYmmhh-HHMMSS:
#          $ git commit -m "Release geo2grid version 3.0.0"
#          $ git tag -a g2g-v3.0.0 -m "G2G version 3.0.0"
#          $ git push --follow-tags

try()
{
    set +e
}

save_vars()
{
    # Variables in here are used in email information.
    variables="${WORKSPACE}/variables.txt"
    touch "$variables"
    tmp_variables="${WORKSPACE}/tmp_variables.txt"
    for variable in "$@"; do
        cp "$variables" "$tmp_variables"
        name=`echo $variable | cut -d'=' -f 1`
        # Removes the variable if already present (in order to update it).
        sed "/^${name}=.*/d" "$tmp_variables" > "$variables"
        # Adds variable.
        echo "$variable" >> "$variables"
    done
    rm "$tmp_variables"
}

setup_vars()
{
    # Make empty files.
    touch "${WORKSPACE}/integration_tests/p2g_test_details.txt"
    touch "${WORKSPACE}/integration_tests/g2g_test_details.txt"
    commit_message=`git log --format=%B -n 1 "$GIT_COMMIT"`
    # Handle release vs test naming.
    suffix=`date "+%Y%m%d-%H%M%S"`

    # Format string to be YYYY-mm-dd HH:MM:SS.
    # git_author: https://stackoverflow.com/questions/29876342/how-to-get-only-author-name-or-email-in-git-given-sha1.
    save_vars "start_time=${suffix:0:4}-${suffix:4:2}-${suffix:6:2} ${suffix:9:2}:${suffix:11:2}:${suffix:13:2}"\
     "git_author=`git show -s --format="%ae" "$GIT_COMMIT"`" "p2g_package_published=FALSE"\
     "g2g_package_published=FALSE" "GIT_TAG_NAME=$GIT_TAG_NAME" "commit_message=$commit_message"


    # If the tag is correct and a version was specified, make a version release.
    if [[ "$GIT_TAG_NAME" =~ ^[pg]2g-v[0-9]+\.[0-9]+\.[0-9]+ ]]; then
        # Removes prefix from $GIT_TAG_NAME.
        suffix="${GIT_TAG_NAME:5}"
    fi

    if [[ "${GIT_TAG_NAME:0:3}" = "g2g" ]] || [[ "$commit_message" =~ (^|.[[:space:]])"["g2g(-skip-tests)?"]"$ ]]; then
        prefixes=geo
        save_vars "p2g_tests=SKIPPED" "p2g_documentation=SKIPPED" "p2g_package="\
         "g2g_tests=FAILED" "g2g_documentation=FAILED" "g2g_package=geo2grid-${suffix}"
    elif [[ "${GIT_TAG_NAME:0:3}" = "p2g" ]] || [[ "$commit_message" =~ (^|.[[:space:]])"["p2g(-skip-tests)?"]"$ ]]; then
        prefixes=polar
        save_vars "p2g_tests=FAILED" "p2g_documentation=FAILED" "p2g_package=polar2grid-${suffix}"\
         "g2g_tests=SKIPPED" "g2g_documentation=SKIPPED" "g2g_package="
    else
        prefixes="geo polar"
        save_vars "p2g_tests=FAILED" "p2g_documentation=FAILED" "p2g_package=polar2grid-${suffix}"\
         "g2g_tests=FAILED" "g2g_documentation=FAILED" "g2g_package=geo2grid-${suffix}"
    fi
}

setup_conda()
{
    # Activate conda for bash.
    /data/users/davidh/miniconda3/bin/conda init bash
    # Restart the shell to enable conda.
    source ~/.bashrc

    conda env update -n jenkins_p2g_swbundle -f "$WORKSPACE"/build_environment.yml
    # Documentation environment also has behave, while the build environment does not.
    conda env update -n jenkins_p2g_docs -f "$WORKSPACE"/build_environment.yml -f "${WORKSPACE}/jenkins_environment.yml"
    conda activate jenkins_p2g_docs
    pip install -U --no-deps "$WORKSPACE"
}

format_test_details()
{
    test_details="$1"
    json_file="${WORKSPACE}/integration_tests/json_file.txt"
    # Gets the line before json data starts.
    i=`grep -n "^\[$" "$test_details" | grep -oE "[0-9]+"`
    # Gets the line after json data ends.
    j=`grep -n "^\]$" "$test_details" | grep -oE "[0-9]+"`
    # Remove lines that are not json data.
    sed "1,${i}d;${j},\$d" "$test_details" > "$json_file"
    set +x
    python << EOF > "$test_details"
import json
with open("json_file.txt") as json_file:
    data = json.load(json_file)
    print()
    for test in data['elements']:
        name = test['name'].split('@')[1]
        duration = 0
        for step in test['steps']:
            duration += step['result']['duration'] if step.get('result') else 0
        end = '\n'
        if test == data['elements'][-1]:
            end = ''
        print("\t\t{0}: {1} in {2} seconds".format(name, test['status'], round(duration)), end=end)
EOF
    set -x
    rm "$json_file"
}

run_tests()
{
    try
    (
        set -e
        export POLAR2GRID_HOME="$swbundle_name"
        prefix=$1
        test_details="${WORKSPACE}/integration_tests/${prefix:0:1}2g_test_details.txt"
        json_file="${WORKSPACE}/integration_tests/json_file.txt"
        cd "${WORKSPACE}/integration_tests"
        # Prints output to stdout and to an output file.
        behave --no-logcapture --no-color --no-capture -D datapath=/data/test_data -i "${prefix}2grid.feature"\
         --format pretty --format json.pretty 2>&1 | tee "$test_details"

        format_test_details "$test_details"

        # Replace FAILED with SUCCESSFUL.
        save_vars "${prefix:0:1}2g_tests=SUCCESSFUL"
    )
}

create_documentation()
{
    prefix=$1
    package_name=$2
    # Make docs.
    cd "$WORKSPACE"/doc
    make latexpdf POLAR2GRID_DOC="$prefix"
    # Copy pdfs to package directory.
    cp "$WORKSPACE"/doc/build/latex/*.pdf "${WORKSPACE}/$package_name"
    # Clear out intermediate results and rebuild for HTML document.
    make clean
    # Needs to be second since Jenkins makes an html in workspace from the file generated by this command.
    make html POLAR2GRID_DOC="$prefix"
    # Copy html to package directory.
    cp -r "$WORKSPACE"/doc/build/html "${WORKSPACE}/$package_name"
    # Replaces FAILED with SUCCESSFUL.
    save_vars "${prefix:0:1}2g_documentation=SUCCESSFUL"
}

# Copies ("publishes") tarball and documentation to bumi:/tmp and give the ability for others to copy it.
publish_package()
{
    prefix=$1
    package_name=$2
    # Remove the directory if it was already made.
    rm -rf "/tmp/$package_name"
    cp -r "${WORKSPACE}/$package_name" "/tmp/$package_name"
    chmod -R a+rX "/tmp/$package_name"
    save_vars "${prefix:0:1}2g_package_published=TRUE"
}

set -ex
exit_status=0
try
(
    set -e
    export PATH="/usr/local/texlive/2019/bin/x86_64-linux":$PATH

    setup_vars
    setup_conda

    # Make polar2grid and geo2grid separately.
    for prefix in ${prefixes}; do
        try
        (
            set -e
            swbundle_name="${WORKSPACE}/${prefix}2grid-swbundle-${suffix}"
            cd "$WORKSPACE"
            conda activate jenkins_p2g_swbundle
            "$WORKSPACE"/create_conda_software_bundle.sh "$swbundle_name"

            package_name="${prefix}2grid-${suffix}"
            mkdir "${WORKSPACE}/$package_name"
            # Copies tarball to package directory.
            cp "${swbundle_name}.tar.gz" "${WORKSPACE}/$package_name"

            conda activate jenkins_p2g_docs
            if [[ "$commit_message" =~ (^|.[[:space:]])"["([pg]2g-)?skip-tests"]"$ ]]; then
                # Replace FAILED with SKIPPED.
                save_vars "${prefix:0:1}2g_tests=SKIPPED"
            else
                run_tests $prefix
            fi
            test_status=$?
            create_documentation $prefix $package_name
            # Only publishes if both tests and documentation passed.
            if [[ ${test_status} -eq 0 ]]; then
                publish_package $prefix $package_name
            else
                exit_status=${test_status}
            fi
        )
        # If there was an error, keep note, but run other prefix.
        if [[ ${exit_status} -eq 0 ]]; then
            exit_status=$?
        fi
    done
)
if [[ ${exit_status} -eq 0 ]]; then
    exit_status=$?
fi
# Allows errors to happen in save_vars.
set -e
save_vars "finish_time=`date "+%Y-%m-%d %H:%M:%S"`"
exit ${exit_status}
