Remapping
=========

.. ifconfig:: not is_geo2grid

    .. automodule:: polar2grid.remap.remap

    Command Line Arguments
    ----------------------

    .. argparse::
        :module: polar2grid.remap.remap
        :func: add_remap_argument_groups
        :prog: polar2grid.sh <reader> <writer>
        :passparser:

.. ifconfig:: is_geo2grid

    Remapping is the process of mapping satellite data to a uniform grid. Mapping
    data to a uniform grid makes it easier to view, manipulate, and store the data.
    Some instrument data is provided to the user already gridded (ex. ABI L1B data)
    and others are not (ex. VIIRS SDR or older GOES satellites).
    In |project| it is possible to perform the gridding process for ungridded data
    or to re-grid already gridded data. Mapping input data to an output grid can
    be a complicated process to make a good looking image. There are different ways
    to get an image the way a user wants based on what grid (projection) is chosen
    and what algorithm is used to map input pixel to output pixel.
    |project| offers various options that are described below.

    Native Resampling
    -----------------

    Native resampling is a special type of resampling that keeps input data in its
    original projection, but replicates or averages data when necessary to make
    other processing in |project| easier. Native resampling is the default for all
    data that is already gridded (ABI, AHI, etc) or when a native grid is specified
    by the user on the command line (``-g MIN``). It can also be specified on the
    command line by using ``--method native``. See the Command Line Arguments
    section below for more details and the options available.

    Nearest Neighbor Resampling
    ---------------------------

    Nearest neighbor resampling is the most basic form of resampling when gridding
    data to another grid. This type of resampling will find the nearest valid input
    pixel for each pixel in the output image. If a valid pixel can't be found near
    a location then an invalid (transparent) pixel is put in its place. Controlling
    this search distance and other options are described below in the Command Line
    Arguments section. Nearest resampling can be specified on the command line
    with ``--method nearest`` and is the default when non-native grids are specified
    to the command line (``-g my_grid``).

    Note that nearest neighbor resampling can cache intermediate calculations to files
    on disk when the same grid is used. For example, the calculations required to
    resample ABI L1B data to the same output grid for each time step are the same.
    If a directory is specified with the ``--cache-dir`` command line flag, this can
    greatly improve performance.

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
    SatPy areas are also supported by |project|, but must be specified in
    SatPy's typical "areas.yaml" file.

    For information on defining your own custom grids see the
    :doc:`Custom Grid <custom_grids>` documentation.

    Command Line Argument
    ---------------------

    .. argparse::
        :module: polar2grid.glue
        :func: add_resample_argument_groups
        :prog: geo2grid.sh -r <reader> -w <writer>
        :passparser:
