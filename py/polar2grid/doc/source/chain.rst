The Chain
=========

.. Do NOT reference the term 'the chain', this is the describing page

This page describes the basic steps involved in going from start to finish
in the polar2grid series of library calls, or "The Chain".  Some of the steps
described below are optional depending on the :term:`glue script` being used.
See the :doc:`Glue Scripts <glue_scripts/index>` documentation for more
information on what steps are being used in your script of interest.

See the :doc:`Developer's Guide <dev_guide/index>` if you are planning on writing
your own :term:`glue script` or polar2grid component and would like detailed
information on the inner-workings of a specific piece.

Frontends
---------

The frontend is usually the first major component used in "The Chain". It
takes in satellite data files and produces binary data files and meta data
information to be used later in processing.  The swath extraction, prescaling,
and pseudoband creation sections below describe the frontend in more detail.

Swath Extraction
^^^^^^^^^^^^^^^^

Swath extraction is the process of combining imager instrument data granules
into one swath.  The very basic responsibility of the swath extraction step
is to make flat binary swath files for latitude, longitude, and image data,
and to provide a dictionary of metadata to identify the data.

As an example the VIIRS swath extractor takes these steps:

    1. Parse meta data from the image filepaths
    2. Parse meta data from the geonav filepaths
    3. Read in latitude and longitude data and append it to flat binary files
    4. Read in image data and append it to a flat binary file
    5. Return meta data to the caller

.. _chain_prescaling:

Prescaling
^^^^^^^^^^

Prescaling is intended to scale the data before any other component uses the
data and is an optional step.  The idea is that the frontend knows
everything about the data it is
reading in.  If the frontend decides that data is not useful in it's current
state, then it will change it to be useful or not provide it at all.  It is
more likely that the frontend will be able to efficiently modify the data than
another component, since the frontend deals with granules and swaths and can
use memory more efficiently.  Most of the cases like this are configurable
via an argument on the command line or in the function calls to the frontend.

An example of prescaling can be seen in the
:ref:`Day/Night Band <prescale_viirs_dnb>` of the VIIRS instrument.  It
has different scaling parameters depending on whether
the scene is during the daytime or nighttime or a mix of both.  The day/night
masks required to make this decision can not be remapped and used after.
Therefore, this type of scaling must happen before remapping.

Again, see the :doc:`Frontends <frontends/index>` documentation for more
details on
your specific frontend being used and the
:doc:`Glue Scripts <glue_scripts/index>` documentation for any
possible differences your glue script of interest implements.

.. _chain_pseudoband:

Pseudoband Creation
^^^^^^^^^^^^^^^^^^^

:term:`Pseudoband` creation is an optional step for a frontend to create bands that
are not provided by the data files being read in.  Frontends only do this if
the calculations involved are simple.  Complex calculations are usually done
in another software package and then made available to polar2grid as another
frontend or an addition to an existing frontend.

An example of pseudoband creation is the 'fog' band created by the VIIRS
frontend.  This 'fog' product is actually just a brightness temperature
difference and can be calculated quite easily.

Grid Determination
------------------

Grid determination is used to find out what grids it would be useful to
remap the data into.  If the data doesn't overlap a grid in a significant way
there's no point in attempting to remap the data to that grid.  There are
different algorithms used to make this determination including 'bounding box'
or 'polygon intersection' algorithms, although 'bounding box' is the only one
implemented at this time. Some scripts may also allow for the grid
to be forced, skipping this step and the calculations involved. 

The other major responsibility of grid determination is to organize
:term:`navigation sets <navigation set>` and the determined grids into
:term:`grid jobs <grid job>`. The
grid jobs can be passed to remapping to determine what data should be mapped
to each grid. This step also usually checks with the backend to see what
grids it knows how to handle to save on remapping time.

Remapping
---------

Remapping or gridding is the process of putting satellite data pixels into an
equidistant grid for easier viewing, manipulation, and storage. Polar2grid
currently uses a 2-step remapping process.
The first step is called 'll2cr' and map the pixel location (lon/lat space)
into grid space. The second step is called 'fornav' which interpolates the
image data into the grid locations. There is a python
and a C version of ll2cr and currently only a C version of fornav.  The
C versions of ll2cr and fornav come from the ms2gt utility package.
You can read more about ms2gt
`here <http://nsidc.org/data/modis/ms2gt/>`_. The ms2gt utilities
were originally used for MODIS data, but have been found to fit
polar2grid's needs.  The original purpose of ms2gt (from the website above):

    The MODIS Swath-to-Grid Toolbox (MS2GT) is a set of software tools that reads HDF-EOS files containing MODIS swath data and
    produces flat binary files containing gridded data in a variety of map projections. MS2GT can produce a seamless output grid from multiple
    input files corresponding to successively acquired, 5-minute MODIS scenes.

polar2grid uses its own version of ms2gt that is not available through NSIDC.
See :doc:`Advanced Topics <advanced>` for more on the bugs fixed, changes made,
and where a copy of this ms2gt version can be found.

ll2cr (C)
^^^^^^^^^

ll2cr is a ms2gt utility that converts latitude and longitude ('ll') data into
columns and rows ('cr') which can then be used in fornav.  It uses 'gpd' files
along with the mapx library to map lon/lat points of the satellite data
to cols/rows of the grid described by the 'gpd' file.  See the
:doc:`Developer's Guide <dev_guide/index>` for more information on creating new
gpd grids.

ll2cr (python)
^^^^^^^^^^^^^^

The python version of ll2cr is meant to be a replacement of the C version,
using the more common PROJ.4 library for mapping instead of mapx. The main
advantage of the python version of ll2cr is that it can create dynamically
sized grids that fit the data. See the :doc:`Developer's Guide <dev_guide/index>`
for more information on creating new proj4 grids.

fornav
^^^^^^

fornav is a ms2gt utility that remaps imager data to the columns and rows file
created by ll2cr. fornav uses elliptical weighted averaging during forward
navigation.

Backends
--------

Backends are run using the output of the fornav calls with any meta data that
may be required to finish producing remapped products.  See the
:doc:`Backends <backends/index>` section for more information. Besides pushing the
remapped data into an output file format, the backend also prepares the data
for that output format.  This usually includes rescaling the data to a certain
value range to fit the output format.  For example, the AWIPS backend only
supports byte-sized values so the backend will scale the data to a 0-255
range.


