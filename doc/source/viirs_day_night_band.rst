:orphan:

Scaling of the VIIRS Day/Night Band in Polar2Grid
=================================================

Scaling of the Day/Night Band (DNB) is complicated due to the
huge range of values that can exist across a given scene.
The Day/Night Band is centered on .7 microns with a wide
spectral response function (half width .505 to .890 microns).
Polar2Grid offers the user four different
options for enhancing the final image product.  If no
specific DNB enhancement is provided to the viirs readers
(for example, polar2grid.sh -r viirs_sdr -w geotiff),
three different output products will be created for the given
scene by default.  The three options are:

* Adaptive Day/Night Band scaling   -  option ``-p adaptive_dnb``
* Dynamic Day/Night Band scaling    -  option ``-p dynamic_dnb``
* Simplified HNCC Day/Night scaling -  option ``-p hncc_dnb``

In addition, a fourth enhancement option is available by
explicitly requesting it in the command line (using the ``-p`` option).

* Histogram Day/Night Band scaling  -  option ``-p histogram_dnb``

The Histogram and Adaptive enhancements work by breaking up the
radiance values and scale them based upon three regimes:

* Day – Solar zenith angles less than 88 degrees,
* Twilight or Terminator Region – Solar Zenith angles between 88 and 100 degrees, and
* Night – Solar Zenith Angles less than 100 degrees.

For each of these regions, a histogram equalization is calculated,
excluding data that falls beyond 4 standard deviations of the mean.
Then a histogram equalization is calculated across all the data in
all of the regions.  Then the data are scaled from 0-1, remapped
to the requested projection and then finally rescaled to 0-255.
This allows us to display day and night data together in one image,
and make the maximum use of all of the data no matter how many regimes
are included in a swath.

Figure 8.1 below shows a Polar2Grid VIIRS Day/Night band
image created using data that includes the transition region
between day and night regimes (left panel).  This data set
was acquired on 22 June 2015.

The Adaptive Scaling Option (center panel) is an alternative that attempts
to provide better contrast across the Terminator region of the
Day/Night band. This algorithm cuts each region into tiles and
calculates a histogram equalization for each tile. Once the
histogram equalization functions have been calculated for each
tile, each tile is processed separately. The "current tile" is
equalized using the histogram equalization calculated from
itself and it is also separately equalized using the
surrounding tiles. These resulting equalized versions of
the tiles are combined using bi-linear interpolation, so
that each pixel uses a weighted amount in inverse relation
to it's distance from the centers of the nearest 4 tiles.
An example of the result of applying this technique to the
same data set can be seen in the following image.  Please
note that some image artifacts (wave patterns) are introduced
when applying this technique over the Terminator region.

The Dynamic option (right panel) implements an error function to scale
the VIIRS Day/Night band data.  This algorithm was provided by
Dr. Curtis Seaman, NOAA Cooperative Institute for Research in
the Atmosphere (CIRA), Colorado State University.  For detailed
information on this technique, please see:

     Curtis J. Seaman, Steven D. Miller, 2015: A dynamic
     scaling algorithm for the optimized digital   display of
     VIIRS Day/Night Band imagery.  International Journal of
     Remote Sensing, Vol. 36, Iss. 7, pp. 1839-1854.
     DOI: 10.1080/01431161.2015.1029100.

And finally, Figure 8.2 provides an example of a technique that
utilizes a simplified high and near-constant contrast approach. This
approach was created by Stephan Zinke of the European Organisation
for the Exploitation of Meteorological Satellites (EUMETSAT).  His
technique supports the display of VIIRS Day/Night Band
granules using consistent settings for all granules. In this way,
it provides consistent results whether applied to single
granules whose images are then stitched together or if it is
applied to a concatenation of granules.

For more information about this technique, and for more
details about the example dataset shown in Figure 8.2
please see :

     Zinke, Stephan, 2017: A simplified high and near-constant
     contrast approach for the display of VIIRS day/night band
     imagery. International Journal of Remote Sensing, Vol. 38
     Iss. 19, pp.5374-5387. DOI:  10.1080/01431161.2017.1338838

.. raw:: latex

    \newpage
    \begin{landscape}

.. figure:: _static/example_images/VIIRS_DNB_Enhancement_Comparison.png
    :width: 100%
    :align: center

    Example of three options for scaling the VIIRS Day/Night
    band in Polar2Grid for a S-NPP pass collected on 22 June 2015.
    The left panel applies a histogram equalization
    technique (histogram_dnb), center panel utilizes an adaptive
    histogram equalization technique (adaptive_dnb), and the third
    option (right panel) implements an dynamic error function
    scaling technique (dynamic_dnb).

.. raw:: latex

    \end{landscape}


.. figure:: _static/example_images/HNCC_DNB_Band_Example.png
    :width: 60%
    :align: center


    Example of the high and near-constant contrast VIIRS
    Day/Night band scaling option (-p hncc_dnb) image created
    from a S-NPP pass collected on 1 September 2016. For more
    information about the lunar illumination regimes of this
    data, please see Zinke, 2017.
