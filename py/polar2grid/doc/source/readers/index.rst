Readers
=======

Readers are the first component called in Polar2Grid. Their main
responsibility is to extract input satellite imager data and the associated
metadata from user provided input files. By using readers,
Polar2Grid can easily read data from multiple sources regardless of format.
The data that readers distribute to other Polar2Grid components are called
:term:`swath products` or "datasets" in SatPy. Sometimes readers perform
additional calculations or filtering on :term:`raw products` to create complex
products called :term:`secondary products`.

.. toctree::
    :maxdepth: 1

    amsr2_l1b
    avhrr
    crefl
    drrtv
    mirs
    modis
    nucaps
    viirs_sdr
    viirs_l1b

