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


.. ifconfig:: not is_geo2grid

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

.. ifconfig:: is_geo2grid

    .. toctree::
        :maxdepth: 1

        abi_l1b
        hrit_jma
