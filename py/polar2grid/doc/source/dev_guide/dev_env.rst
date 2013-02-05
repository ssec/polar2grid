Setting up a development environment
====================================

Before adding components to polar2grid you will need to set up a polar2grid
development environment.  This will allow for easy access to the newest code
updates from other developers and make it easier for you to get your code
additions added to the master polar2grid package.  As described in other
parts of the documentation, the primary installation of polar2grid is the
software bundle.  The software bundle consists of a lot of wrapper scripts
to make it easier to install and use, but it does not make it easy to
develop new features or fix bugs as it hides the command line arguments from
the user.

The main code repository for polar2grid is on github at
https://github.com/davidh-ssec/polar2grid.
If you plan to make a lot of changes over a long period of time it may
be beneficial to "fork" the main repository and then make a "pull request"
when you believe your code is ready to be added to the master branch.

The following instructions will go through a common development installation
case.  It will install everything into 1 directory in your home directory.
polar2grid development does not require this directory structure, so if you
understand every step of these instructions feel free to change the locations
where components are installed.

1. Get a copy of the main code repository:
   
    ::

        mkdir ~/polar2grid
        cd ~/polar2grid
        git clone https://github.com/davidh-ssec/polar2grid.git polar2grid
        cd polar2grid

    If you are working on a specific branch, like 'ninjo' for example,
    you should do the following in addition to the above:

    ::

        git checkout -b ninjo origin/ninjo

2. Compile ms2gt:
   
    ::

        cd polar2grid/ms2gt
        make clean
        make

3. Download and unpack ShellB3:
 
    ::

        cd ~/polar2grid
        # Download the newest version of ShellB3 from ftp://ftp.ssec.wisc.edu/pub/shellb3/
        wget ftp://ftp.ssec.wisc.edu/pub/shellb3/ShellB3-Linux-x86_64-YYYYMMDD-rXXX-core-cspp.tar.gz
        tar -xzf ShellB3-Linux-x86_64-YYYYMMDD-rXXX-core-cspp.tar.gz

    .. note::

           This step is optional. You could install python 2.7
           and the necessary python packages and libraries yourself, but ShellB3 is a
           pre-compiled binary package with all requirements included.
           Libraries required by polar2grid depend on
           the frontend and backend used, but the most common are 'netcdf4-python',
           'h5py', 'pyhdf', 'GDAL'.
 
4. Create a location to install the polar2grid python packages
   (don't install them just yet):
   
    ::

        cd ~/polar2grid
        mkdir python

4. Add the newly installed software to your PATH environment variable and
   add the new python package location to your PYTHONPATH:
   
    ::

        # Edit your ~/.bash_profile or equivalent file
        # Add this to the bottom
        export PATH=$HOME/polar2grid/ShellB3/bin:$PATH
        export PATH=$HOME/polar2grid/polar2grid/ms2gt/bin:$PATH
        export PYTHONPATH=$HOME/polar2grid/python:$PYTHONPATH
        # Log out and log back in or run 'source ~/.bash_profile' for these to take effect

5. Verify you are using the correct python:
   
    ::

        which python
        # result should be '/home/<username>/polar2grid/ShellB3/bin/python'
        python -V
        # result should be 'Python 2.7.x'

6. Install the python packages in a development mode:
   
    ::

        cd ~/polar2grid/polar2grid/py/
        cd polar2grid_core
        python setup.py develop -d ~/polar2grid/python
        cd ../polar2grid_viirs
        python setup.py develop -d ~/polar2grid/python
        cd ../polar2grid
        python setup.py develop -d ~/polar2grid/python
        cd ~

7. Verify that you can import all of the polar2grid python packages:
   
    ::

        python -c "from polar2grid import viirs2awips"
        # should result in nothing

You now have a polar2grid development environment. If you are not familiar
with python packaging (distribute/setuptools), when updating your git
repository via a "git pull" or adding files, you may have to redo step 6.
This will make the development install understand any new directory
structures or file renamings.  If a "git pull" shows that ms2gt files
were changed, you will need to recompile ms2gt by running step 2 again.

To run polar2grid from your new development environment run the following
command. This command uses viirs2awips, but any other glue script
should follow the same basic calling sequence::

    python -m polar2grid.viirs2awips -vvv -g 211e -f /path/to/test/data/files/SVI01*
    # for more options run
    python -m polar2grid.viirs2awips -h

