Glossary
========

.. glossary::
    :sorted:

    bundle script
    bundle scripts
        A bash script provided with the polar2grid software bundle that
        sets up the environment to use the software bundle. This eases
        the use and installation process when using the software bundle.

    the chain
        The common set of library calls making up glue scripts. These include
        frontend, grid determining, remapping, and backend functions. See
        :doc:`chain` for more detailed information.

    data kind
    data kinds
        Descriptive term for what the data measures. Common data kinds are
        brightness temperature, reflectance, or radiance. Polar2grid uses
        constant values for data kinds and any command line flags that accept
        a data kind should expect the value of the constant. See the
        :ref:`constants <constants_data_kinds>`
        module for their current values. Data kinds are different from
        :term:`data types`. Data kind constants are prefixed
        with ``DKIND_``.

    data set
    data sets
        Generic term for a set of data files for a specific product,
        :term:`data kind`, band, or :term:`navigation set`.

    data type
    data types
        Size or format of the binary representation of the data. For example
        an 8-bit unsigned integer versus a 32-bit float. Polar2grid uses
        constant values for data types and any command line flags that accept
        a data type should expect the value of the constant. See the
        :ref:`constants <constants_data_types>`
        module for their current values. Data types are different from
        :term:`data kinds`. Data type constants are prefixed
        with ``DTYPE_``.

    glue script
    glue scripts
        The script connecting every component together.  A glue script connects
        the frontend, grid determiner, remapper, and backend.  There is one
        glue script per task, so one for every frontend to backend connection.

    grid job
    grid jobs
        A collection of information mapping a grid and the bands that should
        be mapped to that grid. Usually created by a grid determination
        component and then passed to remapping for processing.

    job
        Loosely used term to mean an incremental step in polar2grid processing.

    pseudoband
    pseudobands
        Band created by processing 'raw' data from satellite files that is not
        directly available from the 'raw' data and must be calculated. See :ref:`chain_pseudoband` for a detailed explanation.

    prescaling
        The scaling of data done in a frontend before it provides it to any
        other polar2grid components. See :ref:`chain_prescaling` for a detailed explanation.

    navigation set
    nav set
        A set of data files or jobs that share the same navigation data.

