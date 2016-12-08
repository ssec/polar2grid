Software Design Overview
========================

The primary goal of Polar2Grid is to allow scientists to convert satellite
imager data in to a format that they can view using the forecasting tools with
which they are most comfortable. Due to the way most satellite instruments
operate, raw satellite data is typically represented as a non-uniform swath
of pixels where each pixel has a corresponding longitude and latitude. This
type of sparse data can not be easily shown on viewing programs so it must
be resampled to a uniform grid. While this solution can be
summarized in a few sentences, there is much more
that goes in to extracting swath data from input files, remapping the data
to a grid, and writing the gridded data to a new file format for viewing.

Polar2Grid has a modular design to ease development of features added in
the future. It operates on the idea of satellite "products"; data observed
by a satellite instrument. These products can be any type of raster data,
such as temperatures,
reflectances, radiances, or any other value that may be recorded by or calculated
from an instrument. As shown below there are 4 main components of Polar2Grid
used to work with these products: the Frontend, Backend, Compositor,
and Remapper. Typically these components are ":py:mod:`glued <polar2grid.glue>`"
together to create gridded versions of the user provided swath products.

.. graphviz::

    digraph glue_flow {
        rankdir = LR;
        node [shape = rectangle, fillcolor="#C3DCE7:white", gradientangle="90.0", style="filled"];
        "Reader" -> "Remapper";
        "Remapper" -> "Writer";
        "Remapper" -> "Compositors" [style=dashed];
        "Compositors" -> "Writer" [style=dashed];
    }

Intermediate Containers
-----------------------

To pass data between components Polar2Grid uses an intermediate container
to store product data and the associated metadata. These containers allow
for easy transfer of data through Polar2Grid whether it's used from Python
or from the command line. They
can be stored on-disk as one or more JSON files referencing one or more binary
data arrays. In memory, the containers are represented as python dictionaries with
numpy memory-mapped files or data arrays.

Readers
-------

The Reader is responsible for reading provided
data files to create Polar2Grid swath products. In the simplest case, this means
reading data from the file and placing it in an intermediate container. In
more advanced cases a Reader may choose to provide
products that require extra processing; from masking bad values to creating
a new product from the combination of others. The
:doc:`readers documentation <readers/index>` has more details on
the current readers available.

Remapping
---------

Remapping is the process of putting satellite data pixels into an
equidistant grid for easier viewing, manipulation, and storage. Polar2grid
currently uses a 2-step remapping process to grid and then resample the data.
The first step is called 'll2cr' which stands for "longitude/latitude to
column/row". This step maps the pixel location (lon/lat space) into grid
space. Polar2Grid uses grids defined by a PROJ.4 projection specification.
Other parameters that define a grid like its width and height can be
determined dynamically during this step. See the
:doc:`remapping documentation <remapping>` for more information.

The second step of remapping is
to resample the input swath pixels to each output grid pixel. Polar2Grid
provides an 'elliptical weight averaging' or 'EWA' resampling method as
well as the traditional nearest neighbor method, with other algorithms
planned for future releases. In the past both of these steps were handled
by third-party software, but have been rewritten to be directly accessed
from python.

Compositors
-----------

Compositors are an optional component of Polar2Grid that may not be needed
by most users. The role of a compositor is to create new products that can
not be created by the Reader. Usually this means combining multiple
products to create a new one. The most common case is creating color images
(RGB) like true color or false colors images which are the combination
of 3 products. Customizing the behavior of Compositors is considered an
advanced topic. More information can be found on the
:doc:`Compositors documentation <compositors>`.

Writers
-------

The Writer's responsibility is to write gridded data to a file format that
can be used for viewing and/or analyzing in another program. This usually involves
scaling the data to fit the data type used by the file format being written.
For example, most satellite temperature data is best represented as floating-point
numbers (200.0K - 320.0K), but many file formats like NetCDF or Geotiff
prefer unsigned 8-bit integers (0 - 255). To best represent the data in the file,
the Writer must scale the real-world value to a value that can be written to
the output file(s), whether that be with a simple linear transformation or something
more complex. For more information, see the :doc:`Writers documentation <writers/index>`.
