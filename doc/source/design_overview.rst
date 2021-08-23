Software Design Overview
========================

The primary goal of |project| is to allow scientists to convert satellite
imager data into a format that they can view using the forecasting tools with
which they are most comfortable. Due to the way most satellite instruments
operate, raw satellite data comes in many different forms. It often comes in
multiple resolutions that can be difficult to combine or compare. Data can
also be represented as a non-uniform swath of pixels where each pixel has a
corresponding longitude and latitude. This
type of sparse data can not be easily shown on viewing programs so it must
be resampled to a uniform grid. Resampling is only one of many difficulties
involved with processing satellite data and while their solutions can be
summarized in a few sentences, there is a lot to consider to get a good
looking image suitable for viewing.

|project| has a modular design to ease development of features added in
the future. It operates on the idea of satellite "products"; data observed
by a satellite instrument. These products can be any type of raster data,
such as temperatures, reflectances, radiances, or any other value that may be
recorded by or calculated from an instrument. As shown below there are 4 main
steps of |project| used to work with these products: the Reader, Writer,
Compositor, and Remapper. Typically these components are
":py:mod:`glued <polar2grid.glue>`" together to create gridded versions of the
user provided products. Depending on the input data and what the user wants
these steps may be optional or appear in a different order.

.. graphviz::

    digraph glue_flow {
        rankdir = LR;
        node [shape = rectangle, fillcolor="#C3DCE7:white", gradientangle="90.0", style="filled"];
        "Reader" -> "Remapper";
        "Remapper" -> "Writer";
        "Remapper" -> "Compositors" [style=dashed];
        "Compositors" -> "Writer" [style=dashed];
    }

In |project| a majority of this functionality is provided by the open source
SatPy library created by the Pytroll group. More information on SatPy and
the capabilities it provides to python users can be found in the
`SatPy documentation <https://satpy.readthedocs.io/en/latest/>`_.
For more on the Pytroll group and their work see the
`Pytroll home page <http://pytroll.github.io/>`_.

Data Container
--------------

|project|, and the SatPy library it depends on, use
:doc:`DataArray <xarray:user-guide/data-structures>` objects provided by the XArray
library. Additionally, these ``DataArray`` objects use
:doc:`dask arrays <dask:array>` underneath.
These libraries and their data structures provide community-supported
containers for scientific data and easy multithreaded processing.

Readers
-------

The Reader is responsible for reading provided
data files to create |project| products. In the simplest case, this means
reading data from the file and placing it in ``DataArray``. In
more advanced cases a Reader may choose to provide
products that require extra processing; from masking bad values to creating
a new product from the combination of others. The
:doc:`readers documentation <readers/index>` has more details on
the current readers available.

Compositors
-----------

Compositors are an optional component of |project| that may not be needed
by most users. The role of a compositor is to create new products that can
not be created by the Reader. Usually this means combining multiple
products to create a new one. The most common case is creating color (RGB)
images like true color or false colors images which are the combination
of 3 or more products. Depending on what a composite needs as input,
resampling may be needed before the composite can actually be generated.

Customizing the behavior of Compositors is considered
an advanced topic and is covered in the SatPy documentation.

Remapping
---------

Remapping is the process of putting satellite data pixels into an
equidistant grid for easier viewing, manipulation, and storage. |project|
currently offers multiple different algorithms for achieving this gridding.
See the :doc:`remapping documentation <remapping>` for more information.

Writers
-------

The Writer's responsibility is to write gridded data to a file format that
can be used for viewing and/or analyzing in another program. This usually involves
scaling the data to fit the data type used by the file format being written.
For example, most satellite temperature data is best represented as floating-point
numbers (200.0K - 320.0K), but many file formats like NetCDF or GeoTIFF
prefer unsigned 8-bit integers (0 - 255). To best represent the data in the file,
the Writer must scale the real-world value to a value that can be written to
the output file(s), whether that be with a simple linear transformation or something
more complex. For more information, see the :doc:`Writers documentation <writers/index>`.
