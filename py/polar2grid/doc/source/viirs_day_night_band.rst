Scaling of the VIIRS Day/Night Band in Polar2Grid
-------------------------------------------------

Scaling of the Day/Night Band is complicated due to the 
huge range of values that can exist across a given scene. 
The Day/Night Band is centered on .7 microns with a wide 
spectral response function (half width .505 to .890 microns).  
Polar2Grid offers the user three different 
options for enhancing the final image product.  If no 
specific dnb enhancement is provided to the viirs2gtiff.sh 
or viirs2awips.sh scripts, three different output products 
will be created for the given scene.  The three options are:

* Histogram Day/Night Band scaling  -  option -p histogram_dnb
* Adaptive Day/Night Band scaling   -  option -p adaptive_dnb
* Dynamic Day/Night Band scaling    -  option -p dynamic_dnb

For the first two options, we have chosen to break up the 
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

The figure below shows a polar2grid VIIRS Day/Night band 
image created using data that includes the transition region 
between day and night regimes (Scaling option 1 - left panel). 
This data set was acquired on 22 June 2015. 

Option 2 (center panel) is an alternative scaling that attempts to provide 
better contrast across the Terminator region of the Day/Night 
band. This algorithm cuts each region into tiles and calculates 
a histogram equalization for each tile. Once the histogram 
equalization functions have been calculated for each tile, 
each tile is processed separately. The "current tile" is 
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

A new option was added in Polar2Grid Version 2.0 that 
implements an error function to scale the VIIRS Day/Night 
band data (option 3 - right panel).  This algorithm was 
provided by Dr. Curtis Seaman, 
NOAA Cooperative Institute for Research in the Atmosphere 
(CIRA), Colorado State University.  For detailed information 
on this technique, please see:   

     Curtis J. Seaman, Steven D. Miller, 2015: A dynamic 
     scaling algorithm for the optimized digital   display of 
     VIIRS Day/Night Band imagery.  International Journal of 
     Remote Sensing, Vol. 36, Iss. 7, pp. 1839-1854.  
     DOI: 10.1080/01431161.2015.1029100.

.. raw:: latex

    \newpage
    \begin{landscape}




.. figure:: _static/example_images/VIIRS_DNB_Enhancement_Comparison.png
    :width: 100%
    :align: center

    Example of all three options for scaling the VIIRS Day/Night
    band in Polar2Grid for a S-NPP pass collected on 22 June 2015.  
    The left panel applies a histogram equalization
    technique (histogram_dnb), center panel utilizes an adaptive
    histogram equalization technique (adaptive_dnb), and the third
    option (right panel) implements an dynamic error function
    scaling technique (dynamic_dnb). The data set is for a 

.. raw:: latex

    \end{landscape}
    \newpage
