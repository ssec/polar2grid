Glossary
========

.. glossary::
    :sorted:

    data kind
    data kinds
        Descriptive term for what the data measures. Common data kinds are
        brightness temperature, reflectance, or radiance. Data kinds are
        created and set by the reader. While most readers have the
        same descriptive term for a product, it is not required and in some
        cases may not be desired. Note that Data kinds are different from
        :term:`data types`.

    data type
    data types
        Size or format of the binary representation of the data. For example
        an 8-bit unsigned integer versus a 32-bit floating point number.
        Data types are different from :term:`data kinds`. Data types consist
        of two parts: the format of the data and the number of bytes used.
        The current set of available data types can be found in the
        :py:mod:`polar2grid.core.dtype` module.


    glue script
    glue scripts
        The script connecting every component together.  A glue script connects
        a reader, the remapper, compositors, and a writer. The only glue script
        in Polar2Grid is called ``polar2grid.sh``, but in previous versions
        there were glue scripts named ``<reader>2<writer>.sh``. The bash script
        is simply a wrapper around the python call
        `python -m polar2grid.glue <reader> <writer> -vv ...`,
        except for in rare cases where specific defaults are needed, such as
        ``crefl2gtiff.sh``.

    product
    products
        A swath of instrument data. When from a Polar2Grid Reader a product is considered
        a :term:`swath product`. After a swath product has been remapped it is considered
        a :term:`gridded product`.

    swath product
    swath products
        :term:`Products <products>` representing the direct observations of a satellite
        instrument. Swath products are not guaranteed to be uniformly spaced and are usually
        not.

    gridded product
    gridded products
        :term:`Products <products>` that have been mapped to a uniform grid. These are usually
        created from :term:`swath products` by remapping.

    raw product
    raw products
        :term:`Swath product <swath product>` created by a reader requiring little more than reading the data from
        a data file. It is common for raw products to require scaling from the raw
        data stored in the file using a scaling factor and offset. There are also a few
        cases where raw products require additional masking (ex. cloud clearing) that
        requires another product. In this way, raw products are sometimes treated as
        :term:`secondary products`. To allow for more flexibility when raw products
        require extra processing, readers should consider having access to the
        original raw product and a secondary product created from that original product,
        rather than one single product. Obviously this depends on the usefulness of
        the original product to potential uses.

    secondary product
    secondary products
        :term:Swath product <swath product>` created by a reader requiring one
        or more other products and some extra processing. Secondary products
        may require :term:`raw products` or other secondary products.
