VIIRS Frontend
==============

The VIIRS Frontend operates on Science Data Record (SDR) files from
the Suomi National Polar-orbiting Partnership's (NPP) Visible/Infrared
Imager Radiometer Suite (VIIRS) instrument. These SDR files are hdf5
files with filenames as below. This filenaming scheme is required to be
read by this frontend::

    SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5

The corresponding navigation files name::

    GITCO_npp_d20120225_t1801245_e1802487_b01708_c20120226001734123892_noaa_ops.h5

The VIIRS frontend supports all bands created by the instrument (listed
below). It requires terrain corrected navigation files for the bands that
have them to be in the same directory as the data files::

    I01 (GITCO)
    I02 (GITCO)
    I03 (GITCO)
    I04 (GITCO)
    I05 (GITCO)
    M01 (GMTCO)
    M02 (GMTCO)
    M03 (GMTCO)
    M04 (GMTCO)
    M05 (GMTCO)
    M06 (GMTCO)
    M07 (GMTCO)
    M08 (GMTCO)
    M09 (GMTCO)
    M10 (GMTCO)
    M11 (GMTCO)
    M12 (GMTCO)
    M13 (GMTCO)
    M14 (GMTCO)
    M15 (GMTCO)
    M16 (GMTCO)
    DNB (GDNBO)

When specifying the data files on the command line, or providing them to the
frontend in another way, only the data (``SV*``) files should be provided.
This frontend also expects that only one :term:`navigation set` be provided
at a time. Although, most glue scripts will separate out navigation sets
automatically for the user.

.. _pseudo_viirs_ifog:

SSEC Fog Product
----------------

The Space Science and Engineering Center (SSEC) of UW-Madison sometimes uses a
fog band. The fog band is actually a temperature difference of the I05 and I04
bands.

.. _prescale_viirs_dnb:

DNB Prescaling
--------------

The Day/Night Band of the |viirs| instrument does not show a lot of detail as
is. The |ssec| has developed two algorithms for bringing detail out of the
Day/Night band data, they are described below.

Histogram Equalization
^^^^^^^^^^^^^^^^^^^^^^

TODO

Local Histogram Equalization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO

