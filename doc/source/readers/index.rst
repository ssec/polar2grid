Readers
=======

Readers are the first component used in |project| processing. Their main
responsibility is to extract input satellite imager data and the associated
metadata from user provided input files.
The data that readers distribute to other |project| components are called
:term:`products` ("datasets" in SatPy terminology).

Depending on what products are available in the files provided by the user
the reader can also provide composite products.
Due to the way |project| interfaces to the SatPy library there may be
additional readers available than those described below. Further details on
these readers can be found on the
`SatPy documentation <https://satpy.readthedocs.io/en/latest/>`_. The readers
described below have been tested and configured to work as |project| users
have come to expect. Any other readers provided by SatPy are not guaranteed
to work with all |project| features.


.. toctree-filt::
    :maxdepth: 1

    :polar2grid:viirs_sdr
    :polar2grid:viirs_l1b
    :polar2grid:modis
    :polar2grid:crefl
    :polar2grid:avhrr
    :polar2grid:amsr2_l1b
    :polar2grid:nucaps
    :polar2grid:mirs
    :polar2grid:acspo
    :polar2grid:clavrx
    :geo2grid:abi_l1b
    :geo2grid:ahi_hrit
    :geo2grid:ahi_hsd
