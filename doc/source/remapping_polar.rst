Remapping
=========

Remapping is the process of mapping satellite data to a uniform grid. Mapping
data to a uniform grid makes it easier to view, manipulate, and store the data.
Some instrument data is provided to the user already gridded (ex. VIIRS EDR
Flood) and others are not (ex. VIIRS SDR).
In |project| it is possible to perform the gridding (reprojecting) process for
ungridded data or to re-project already gridded data. Mapping input data in
order to create a high quality image can be a complicated process. There are
different techniques that can be used to create an output image based on what
grid (projection) is chosen and what algorithm is used to map input pixel to
output pixel.  |project| provides default options for each reader, but users
can customize these options. The various options are described below.

Elliptical Weighted Averaging Resampling
----------------------------------------

Elliptical Weighted Averaging (EWA) resampling is the default resampling method
for a lot of scan-based polar-orbiting instrument data. This method uses the
size of each instrument scan to determine a weight for each pixel. All input
pixels that map to output pixels are weighted and averaged. This helps
produce an image that is typically higher quality than those produced by
nearest neighbor.

Nearest Neighbor Resampling
---------------------------

Nearest neighbor resampling is the most basic form of resampling when gridding
data to another grid. This type of resampling will find the nearest valid input
pixel for each pixel in the output image. If a valid pixel can't be found near
a location then an invalid (transparent) pixel is put in its place. Controlling
this search distance and other options are described below in the Command Line
Arguments section. Nearest neighbor resampling can be specified on the command
line with ``--method nearest``. It is the default resampling method when EWA
resampling can not be used.

Grids
-----

|project| uses the idea of "grids" to define the output geographic location
that images will be remapped to. Grids are also known as "areas" in the
SatPy library. These terms may be used interchangeably through this
documentation, especially in low-level parts.

|project| uses grids defined by a PROJ.4 projection specification.
Other parameters that define a grid like its width and height can be
determined dynamically during this step. A grid is defined by the following parameters:

 - Grid Name
 - PROJ.4 String (either lat/lon or metered projection space)
 - Width (number of pixels in the X direction)
 - Height (number of pixels in the Y direction)
 - Cell Width (pixel size in the X direction in grid units)
 - Cell Height (pixel size in the Y direction in grid units)
 - X Origin (upper-left X coordinate in grid units)
 - Y Origin (upper-left Y coordinate in grid units)

|project| supports static and dynamic grids. Grids are static if they have all of the
above attributes defined. Grids are dynamic if some of the attributes are not defined.
These attributes are then computed at run time based on the data being remapped. Only
width/height and x/y origin can be unspecified in dynamic grids.

For information on defining your own custom grids see the
:doc:`Custom Grid <custom_grids>` documentation.

Command Line Argument
---------------------

.. argparse::
    :module: polar2grid.glue_legacy
    :func: add_remap_argument_groups
    :prog: polar2grid.sh <reader> <writer>
    :passparser:
    :nodefaultconst:
