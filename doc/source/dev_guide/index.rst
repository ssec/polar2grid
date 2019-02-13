Developer's Guide
=================

.. warning::

    Due to the collaboration with the PyTroll team on the SatPy package
    much of this documentation will change or is inaccurate. Future
    versions will have better documentation about contributing. For now,
    please contact the Polar2Grid or PyTroll team.

This guide is intended to ease the development of additional readers,
writers, or other components to the polar2grid package. Polar2Grid has
gone through a major redesign process and it is much easier to modify
existing components and create new components. However, due to some collaboration
with the PyTroll team a majority (if not all) of the python functionality
provided by Polar2Grid will be absorbed by the PyTroll package "mpop" in
a future version. Polar2Grid will continue to provide the same interface,
but with more advanced features. Since this refactoring is currently in
progress, any documentation on modifying source code for Polar2Grid has
been removed from the Developer's Guide.

If you would like to contribute to either Polar2Grid or MPOP or have any
questions about the collaboration please contact the CSPP/Polar2Grid team.

Code repository: https://github.com/ssec/polar2grid

**Developer's Guide Components:**

 - :doc:`dev_env`
 - :doc:`swbundle`
 - :doc:`json_input`

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
 - memory management in terms of how arrays are created/manipulated/copied
 - remapping/regridding satellite imagery swaths (including types of projections)
 - python packaging, specifically `distribute <http://packages.python.org/distribute/>`_ (setuptools)
 - git source code management system and the 'forking' and 'pull request'
   features of http://github.com

Branching Model
---------------

The branching model used by the Polar2Grid team follows a basic ``feature-branch`` -> ``develop`` -> ``master``
structure.
New features still in development should get their own branches. Once these features are complete they are merged
into the ``develop`` branch. Once all features for a particular release have been tested and are considered
"release ready" they are merged into the ``master`` branch. If a master merge is for a new minor version a
maintenance branch is also created for future bug fixes. This branching model was inspired from the discussion
`here <http://nvie.com/posts/a-successful-git-branching-model/>`_.
