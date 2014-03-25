Developer's Guide
=================

This guide is intended to ease the development of additional frontends,
backends, or other components to the polar2grid package. It provides the
general interface for each "chain link" as well as a minimal description
of the responibilites of that link.  To avoid being tied down to a specific
implementation, the polar2grid package
is very flexible in terms of where certain pieces of logic can go.  As the
package matures this flexibility will slowly disappear.

An example of this
flexibility is the design of the scripts tying a frontend to a backend
(glue scripts).  In
future versions of polar2grid, it may be possible to have one unified script
where a frontend and a backend are selected via command line arguments.
Currently however there are not enough use cases to define a generic 'master'
script.  So the current design has separate glue scripts that
can have as much freedom as they need to connect the frontend to the backend
and produce the proper output.  Although, there shouldn't need to be much
work outside of what has already been done to accomplish any gluing.  That is,
assuming any new frontends or backends were developed properly.

If you are trying to decide whether or not your backend idea should be
implemented in polar2grid here are a few things to think about.  Polar2grid
should not be used for anything that doesn't want remapped data.  If you want
raw scanline data, polar2grid is not the package for you.  Also, if your
backend output is not a file, polar2grid is not for you.  Non-file output may
be something like a server that provides remapped data to a client.  Although
polar2grid could provide this data to a server for storage, a polar2grid
backend should not be doing the serving.

If you are trying to decide whether or not your frontend idea should be
implemented in polar2grid there are a few things to consider first.
Polar2grid should be seen as a 'converter' of formats, not a calculator or
creator of new products.  If you are planning to create a new product that
doesn't exist in some other format, then polar2grid is not the software to
use.  A solution may be to have another piece of software produce the input
that polar2grid will remap or another piece of software that polar2grid
provides the remapped input files for.

Polar2grid is intended for polar-orbiting satellite data.  Geo-stationary
data may work with the current tool-set, but is not guaranteed to always
work.

Code repository: https://github.com/davidh-ssec/polar2grid

**Developer's Guide Components:**

 - :doc:`dev_env`
 - :doc:`glue_scripts`
 - :doc:`frontends`
 - :doc:`grids`
 - :doc:`remapping`
 - :doc:`backends`
 - :doc:`rescaling`
 - :doc:`swbundle`

Prerequisites
-------------

These polar2grid topics should be understood to get the most out of this
guide:

 - The overall 'flow' of the :doc:`Chain <../chain>`
 - The responsibilities of a frontend
 - The responsibilities of a backend
 - Package hierarchy and dependencies

A developer should be familiar with these concepts to develop a new component
for polar2grid:

 - python and numpy programming
 - memory management in terms of how arrays are created/manipulated/copied
 - flat binary files and how data is stored and arranged
   (`FBF Description <https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/flat-binary-format-fbf-files-and-utilities/FBF-file-format.pdf>`_)
 - remapping/regridding satellite imagery swaths (including types of projections)
 - python packaging, specifically `distribute <http://packages.python.org/distribute/>`_ (setuptools)
 - git source code management system and the 'forking' and 'pull request'
   features of http://github.com

.. _formats_section:

File Formats
------------

polar2grid uses flat binary files
(`FBF <https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/flat-binary-format-fbf-files-and-utilities/FBF-file-format.pdf>`_)
for all of its intermediate file
storage.  Data is primarily stored as files due to its large size and the
requirement for the current remapping utilities to have file input.

polar2grid does not require any other data format except for those required
by a frontend or backend.

Branching Model
---------------

The branching model used by the Polar2Grid team follows a basic ``feature-branch`` -> ``develop`` -> ``master``
structure.
New features still in development should get their own branches. Once these features are complete they are merged
into the ``develop`` branch. Once all features for a particular release have been tested and are considered
"release ready" they are merged into the ``master`` branch. If a master merge is for a new minor version a
maintenance branch is also created for future bug fixes. This branching model was inspired from the discussion
`here <http://nvie.com/posts/a-successful-git-branching-model/>`_.
