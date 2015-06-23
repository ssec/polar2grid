Development Environment
=======================

Before adding components to polar2grid you will need to set up a polar2grid
development environment.  This will make it easier to get the newest updates
from other developers and vice versa. Creating a development environment does
not provide the bash wrapper scripts since they depend on a software bundle.
It is recommended that you contact the Polar2Grid team before adding/developing
any new features to coordinate efforts.

The main code repository for polar2grid can be found on github at
https://github.com/davidh-ssec/polar2grid.
If you plan to make a lot of changes over a long period of time it may
be beneficial to `fork <https://help.github.com/articles/fork-a-repo>`_
the main repository and then make a
`pull request <https://help.github.com/articles/using-pull-requests>`_
when you believe your code is ready for other developers to see.

The following instructions will assist in getting an environment up and running
that will allow for easy development of polar2grid. Most of the installation
logic is kept in a simple script. If you would like more control over the installation
process this script is the place to start.

1. Get a copy of the code repository:
   
    ::

        mkdir ~/polar2grid
        cd ~/polar2grid
        git clone https://github.com/davidh-ssec/polar2grid.git polar2grid
        cd polar2grid

    If you are working on a specific branch, like 'ninjo' for example,
    you should do the following in addition to the above. If you don't know
    what this is for, don't run it:

    ::

        git checkout -b ninjo origin/ninjo

    .. note::

        The ``develop`` branch has the newest features, but may not be fully tested. The ``master`` branch contains
        stable/release ready features.

2. Run the development installation script:

    ::

        ./create_dev_env.sh /path/to/your_dev_env

    This script will walk you through a few questions including whether or not to use ShellB3 (linux only), provide
    a preinstalled ShellB3, or build and install secondary polar2grid components.

3. Add paths to your environment

    At the end of step #2 the script prints a couple lines that should be added to your ``.bash_profile`` or
    ``.bashrc``. Adding these lines, logging out, and logging back in will make polar2grid available to your shell.

    To run polar2grid from your new development environment run the following
    command. This command uses viirs2awips, but any other :term:`glue script` or polar2grid utility
    should follow the same basic calling sequence::

        p2g_glue viirs awips -vvv -g 211e -f /path/to/test/data/files/SVI01*
        # for more options run
        p2g_glue viirs awips -h
