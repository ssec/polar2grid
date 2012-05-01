The Chain
=========

This page describes the basic steps involved in going from start to finish
in the polar2grid series of steps, or "The Chain".  Some of the steps
described below are optional depending on the script being used.  See the
:doc:`Scripts <scripts>` documentation for more information on what steps
are being used in your script of interest.

Swath Extraction
----------------

Swath extraction is the process of combining imager data granules into one
swath.  This is usually the first major step in the polar2grid remapping
process, which means that it is also responsible for providing all
the meta data to the rest of the polar2grid "chain".  The very basic
responsibility of the swath extraction step is to make flat binary
swath files for latitude, longitude, and image data.  The software involved
in creating swaths is able to remove entire "scans" of data if the
geolocation data is bad/invalid.  This is required to use the ms2gt utilities
(described below) properly because they can not handle invalid navigation
data.

From a developer stand point, there is no required series of steps or
order to any steps for the swath extraction process.  It is only required that
at least the 3 swath files and a meta data dictionary are provided
to allow for further processing.  As an example the VIIRS swath extractor
takes these steps:

    1. Parse meta data from the image filepaths
    2. Parse meta data from the geonav filepaths
    3. Read in latitude and longitude data and append it to flat binary files
    4. Read in image data and append it to a flat binary file

Prescaling
----------

Prescaling is intended to scale the data before remapping, which is usually
required if there is meta data used in the scaling.  For example, the DNB
of the VIIRS instrument has different scaling parameters depending on whether
the scene is during the daytime or nighttime or a mix of both.  The day/night
masks required to make this decision can not be remapped and used after.
Therefore, this type of scaling must happen before remapping.

Again, see the :doc:`Scripts <scripts>` section for more details on your
specific script being used.

Grid Determination
------------------

Grid determination is used to find out what grids it would be useful to
remap the data into.  If the data doesn't overlap a grid in a significant way
there's no point in attempting to remap the data to that grid.  There are
different algorithms used to make this determination including 'bounding box'
or 'polygon intersection' algorithms. Some scripts may also allow for the grid
to be forced, skipping this step and the calculations involved.

Remapping
---------

The ms2gt utilties used for remapping data in polar2grid are 'll2cr' and
'fornav'.  You can read more about ms2gt
`here <http://nsidc.org/data/modis/ms2gt/>`_. The ms2gt utilities
were originally used for MODIS data, but have been found to fit
polar2grid's needs.  The original purpose of ms2gt (from the website above):

    The MODIS Swath-to-Grid Toolbox (MS2GT) is a set of software tools that reads HDF-EOS files containing MODIS swath data and
    produces flat binary files containing gridded data in a variety of map projections. MS2GT can produce a seamless output grid from multiple
    input files corresponding to successively acquired, 5-minute MODIS scenes.

polar2grid uses its own version of ms2gt that is not available through NSIDC.
See :doc:`Advanced Topics <advanced>` for more on the bugs fixed, changes made,
and where a copy of this ms2gt version can be found.

ll2cr
^^^^^

ll2cr is a ms2gt utility that converts latitude and longitude ('ll') data into
columns and rows ('cr') which can then be used in fornav.

fornav
^^^^^^

fornav is a ms2gt utility that remaps imager data to the columns and rows file
created by ll2cr.  fornav uses elliptical weighted averaging during forward
navigation.

Backends
--------

Backends are run using the output of the fornav calls with any meta data that
may be required to finish producing remapped products.  See the
:doc:`Backends <backends>` section for more information.


