Frontends
=========

Frontends are the input readers of Polar2Grid. Their main responsibility is
to extract input satellite imager data and the associated metadata. By using frontends,
polar2grid can easily read data from multiple sources regardless of format.
The data that frontends distribute to other Polar2Grid components are called
:term:`swath products`. Sometimes frontends perform additional calculations or
filtering on :term:`raw products` to create complex products called
:term:`secondary products`.

Below is a list of currently available frontends for polar2grid.

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

