VIIRS Frontend
==============

The VIIRS Frontend operates on Science Data Record (SDR) and Environmental Data Record (EDR) files from
the Suomi National Polar-orbiting Partnership's (NPP) Visible/Infrared
Imager Radiometer Suite (VIIRS) instrument. These SDR files are hdf5
files with filenames as below. This filenaming scheme is required to be
read by this frontend::

    SVI01_npp_d20120225_t1801245_e1802487_b01708_c20120226002130255476_noaa_ops.h5

The corresponding navigation files name::

    GITCO_npp_d20120225_t1801245_e1802487_b01708_c20120226001734123892_noaa_ops.h5

The VIIRS frontend supports all SDR bands created by the instrument and the VIIRS Sea Surface Temperature product
(listed below). It supports terrain corrected or non-terrain corrected navigation files and requires that these
files be in the same directory as the data files::

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
    SST (GMTCO)

When specifying the data files on the command line, or providing them to the
frontend in another way, only the data (``SV*``) files should be provided.

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

Local Histogram Equalization (Adaptive)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO

