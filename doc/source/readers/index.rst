Readers
=======

Readers are the first component used in Polar2Grid processing. Their main
responsibility is to extract input satellite imager data and the associated
metadata from user provided input files.
The data that readers distribute to other Polar2Grid components are called
:term:`swath products` ("datasets" in SatPy terminology). Sometimes readers
perform additional calculations or filtering on :term:`raw products` to create
complex products called :term:`secondary products`.

.. toctree::
    :maxdepth: 1

    viirs_sdr
    viirs_l1b
    modis
    crefl
    avhrr
    amsr2_l1b
    nucaps
    mirs
    acspo
    clavrx
