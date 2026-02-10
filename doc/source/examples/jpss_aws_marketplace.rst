.. raw:: latex

    \newpage

Working with Data from the JPSS AWS Marketplace
-----------------------------------------------

Polar2Grid now supports basic image creation using data from the
JPSS Amazon Web Services (AWS) Marketplace as input.

Creating JPSS AWS VIIRS SDR Images
**********************************

One of the ways that NOAA distributes satellite data is through the
`JPSS AWS Marketplace <https://registry.opendata.aws/noaa-jpss/>`_.
Polar2Grid is able to access this freely available data allowing 
users the capability to make images without downloading data. The
basic `polar2grid.sh` commands are the essentially the same, you
are just pointing at the input data from an external location. The 
following examples demonstrate how to make VIIRS SDR images from
JPSS AWS data. 

To make an image from one NOAA-21 VIIRS February 8, 2026, granule and a single band, you need
to provide the input files from the NOAA AWS s3 bucket using
a command like this:

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -p i01 -f s3://noaa-nesdis-n21-pds/VIIRS-I1-SDR/2026/02/08/SVI01_j02_d20260208_t1956574_e1958221_b16834_c20260208202125135000_oebc_ops.h5 s3://noaa-nesdis-n21-pds/VIIRS-IMG-GEO-TC/2026/02/08/GITCO_j02_d20260208_t1956574_e1958221_b16834_*.h5

This `polar2grid.sh` command provides the exact URL and single granule filename that I want to use, along with
the accompanying geolocation file. It creates an `I-Band 01` GeoTIFF file in the default 
WGS84 projection. Notice the use of the wild card in place of the
creation date and time of the `GITCO` file. The remainder of the command execution
is the same as when using a local VIIRS SDR dataset. 

Using globbing, I can produce images from more than one calibrated SDR file at a time. For instance,
to create images of both the `I-Band 1` and I-Band 2` JPSS AWS data for this same granule time,
I execute the following command:

.. code-block:: bash

    polar2grid.sh -r viirs_sdr -w geotiff -p i01 i02 -f s3://noaa-nesdis-n21-pds/VIIRS-I{1,2}-SDR/2026/02/08/SVI0{1,2}_j02_d20260208_t1956574_e1958221_b16834_*.h5 s3://noaa-nesdis-n21-pds/VIIRS-IMG-GEO-TC/2026/02/08/GITCO_j02_d20260208_t1956574_e1958221_b16834_*.h5

I can even create true color images by pointing to the required input files. For this granule,
I would use the following command:

.. code-block:: bash

   polar2grid.sh -r viirs_sdr -w geotiff -p true_color -vvv -f s3://noaa-nesdis-n21-pds/VIIRS-I1-SDR/2026/02/08/SVI01_j02_d20260208_t1956574_e1958221_b16834_*.h5 s3://noaa-nesdis-n21-pds/VIIRS-M{3,4,5}-SDR/2026/02/08/SVM0{3,4,5}_j02_d20260208_t1956574_e1958221_b16834_*.h5 s3://noaa-nesdis-n21-pds/VIIRS-{IMG,MOD}-GEO-TC/2026/02/08/G{I,M}TCO_j02_d20260208_t1956574_e1958221_b16834_*.h5 

To create true color VIIRS images, M-Bands 3,4 and 5 are used along with I-Band 1 which is used for image sharpening.
I also need to use the Terrain Corrected Geolocation files for both I- and M-Band resolution. The image
below shows the GeoTIFF created when using this command.

.. raw:: latex

    \newpage

.. figure:: ../_static/example_images/JPSS_AWS_VIIRS_Single_Granule_True_Color_Example.png
    :width: 90%
    :align: center

    VIIRS NOAA21 True Color single granule image created using a Polar2Grid command that accesses data from the JPSS AWS Marketplace. The observations were collected over the Southwestern United States on February 8, 2026, at 19:56 UTC. 














