#!/usr/bin/env bash

# Activate conda for bash.
/data/users/davidh/anaconda3/bin/conda init bash
# Restart the shell to enable conda.
source ~/.bashrc
conda activate jenkins_p2g_env
conda install -y sphinx

cd "$WORKSPACE"/doc
make html
cp -r source /data/users/wroberts/html/.

exit $?