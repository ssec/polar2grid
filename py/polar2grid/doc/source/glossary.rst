Glossary
========

.. include:: global.rst

.. glossary::

    job
        Loosely used term to mean an incremental step in polar2grid processing.

    pseudoband
        Band created by processing 'raw' data from satellite files.  For example,
        ``polar2grid.viirs`` can create a Fog product from 'raw' .h5 data.

    glue script
        The script connecting every component together.  A glue script connects
        the frontend, grid determiner, remapper, and backend.  There is one
        glue script per task, so one for every frontend to backend connection.

    navigation set
    nav set
        A set of data files or jobs that share the same navigation data.

    Data Set
        A set of data files for a specific product or data kind.

