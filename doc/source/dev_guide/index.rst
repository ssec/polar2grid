:orphan:

Developer's Guide
=================

This guide is intended to ease the development of additional readers,
writers, or other components to the polar2grid package.

If you would like to contribute to either Polar2Grid or the Pytroll Satpy
package or have any questions about the collaboration please contact the
CSPP/Polar2Grid team.

Code repository: https://github.com/ssec/polar2grid

**Developer's Guide Components:**

.. toctree::
    :maxdepth: 1

    dev_env
    swbundle
    json_input
    adding_readers
    Python API <api/modules>

Prerequisites
-------------

These polar2grid topics should be understood to get the most out of this
guide:

 - The general :doc:`design <../design_overview>` of Polar2Grid
 - The responsibilities of a reader
 - The responsibilities of a writer
 - Package hierarchy and dependencies

A developer should be familiar with these concepts to develop a new component
for polar2grid:

 - python and numpy programming
 - remapping/regridding satellite imagery swaths (including types of projections)
 - python packaging, specifically `distribute <http://packages.python.org/distribute/>`_ (setuptools)
 - git source code management system and the 'forking' and 'pull request'
   features of http://github.com
 - Xarray and dask programming and how it is used by the Satpy library

