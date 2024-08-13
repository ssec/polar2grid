:orphan:

Version 2.3 to Version 3.x Command Changes
==========================================

Important Changes
-----------------
A number of important changes were made to the Polar2Grid core software and
implementation with the relaese of Version 3.0.

* New basic implementation:  ``polar2grid.sh -r <reader> -w <writer>``.

   * For example: ``polar2grid.sh -r viirs_sdr -w geotiff -f <path to files>``.

* Some reader and writer names have been changed.

   * For example: GeoTIFF writer is now ``geotiff``.

* Improved execution speeds using the xarray and Dask python library.
* Option now available to choose how many worker threads to use: ``--num-workers``.  Default is 4.
* NOAA20 output file names standardized to "noaa20" prefix.  For instance, ``n20_viirs_sst*`` is now ``noaa20_viirs_sst*``.
* The crefl reader is no longer supported.  Use ``-p true_color false_color`` with the MODIS or VIIRS readers.
* The scmi writer is replaced by ``awips_tiled``.
* AWIPS true and false color tiles are created using ``--awips-true-color --awips-false-color``.
* GeoTIFF output files now include an “Alpha” channel by default. To reproduce output from previous versions, use ``--fill-value 0`` command line option.
* ``--list-products`` and ``list-product-all`` now available. ``--list-products-all`` includes Satpy products that can be created in addition to standard Polar2Grid products. Please note that the additional products have not been tested.
* Rescale .ini files have been replaced by the .yaml format. If you require help in converting your custom .ini files, please contact us.
* Grid definition ``.conf`` files are transitioning to ``.yaml`` file definitions. A script which converts the grid files to the new format is now available.
* Output files with the same name will now be overwritten.
* Reflectances are now stored in GeoTIFF files (dtype float32) as 0-100 (v2.3 values were stored as 0-1).
* The dtype real4 format is replaced with dtype float32.
* The way that day/night product filtering is implemented has changed.  The use of ``-–sza-threshold`` is no longer used.  Use the ``--filter-day-products`` option.
* AWIPS output files are written in a new way. We have found some problems with the current version of AWIPS not displaying fill values correctly, and the units ``Micron`` is not recognized in active version of AWIPS at the time of writing. These bugs have been fixed and will eventually be resolved in future AWIPS versions.
* VIIRS false color image creation now uses the .86 micron band for sharpening. Previous versions used the .68 micron for sharpening.
* Different option for nearest neighbor resampling ``(--method nearest)``.

  * ``--radius-of-influence`` in meters replaces ``--distance-upper-bound`` in units of grid cell.

* Different option names for elliptical weighted averaging resampling ``(--method ewa)``

  * ``-–weight-delta-max`` (replaces ``--fornav-D`` option)
  * ``--weight-distance-max`` (replaces ``--fornav-d`` option)

* Reflectances in HD5 files and binary files are now stored as 0-100%.
* The standard convention for grid configuration is now .yaml file formatting. The legacy .conf files can still be used. A script was made to convert .conf style to .yaml style grid configuration.

Examples
--------

The following show a few Polar2Grid Version 2.3 commands
and the new command structure to produce the same or similar
files in Polar2Grid Version 3.x.

Create VIIRS GeoTIFF default output files. The default GeoTIFF now includes
an Alpha Band which will make the background transparent
along with the creation of true and false color images.
Version 3 also provides the user with the option to choose how many computer worker
threads to use. The default is 4.

   **v2.3**: ``polar2grid.sh  viirs gtiff  -f <path to files>``

   **v3.x**: ``polar2grid.sh -r viirs_sdr -w geotiff --num-workers 8 -f <path to files>``

Create VIIRS SDR true and false color GeoTIFF output files. Note the version 3.x
execution will by default create an Alpha band that makes the
background transparent.  Using ``--fill-value 0`` will create an image with a black
background.

   **v2.3**: ``polar2grid.sh crefl gtiff --true-color --false-color -f <path to files>``

   **v3.x**: ``polar2grid.sh -r viirs_sdr -w geotiff -p true_color false_color --fill-value 0 -f <path to files>``

Create VIIRS SDR I-Band GeoTIFFs with 32 bit floating point output, and customize the product
output filenames. The reflectance output in version 3.x is stored as 0-100% values as opposed
to 0.0-1.0 in previous versions.

   **v2.3**: ``polar2grid.sh viirs gtiff --grid-coverage 0.002 -p i01 i02 i03 i04 i05 -g polar_300 --dtype real4 --output-pattern {satellite}{instrument}{product_name}{begin_time}{grid_name}.float.tif  -f <path to files>``

   **v3.x**  ``polar2grid.sh -r viirs_sdr -w geotiff --num-workers 4 --grid-coverage 0.002 -g polar_300 -p i01 i02 i03 i04 i05 --fill-value 0 --dtype float32 --no-enhance  --output-filename {satellite}{instrument}{product_name}{begin_time}{grid_name}.float.tif -f <path to files>``

Create true and false color MODIS AWIPS tiles for the United States CONUS Sector.

   **v2.3**: ``polar2grid.sh crefl scmi --true-color --false-color --sector-id LCC --letters --compress  -g lcc_conus_300 -f <path to files>``

   **v3.x**: ``polar2grid.sh -r viirs_sdr -w awips_tiled --awips-true-color --awips-false-color --num-workers 8 -g lcc_conus_300 --sector-id LCC --letters --compress -f <path to files>``

Create MiRS GeoTIFF product files.

   **v2.3**: ``polar2grid.sh mirs gtiff -p rain_rate sea_ice snow_cover swe tpw sfr btemp_57h1 btemp_23v btemp_165h btemp_183h1 btemp_88v -g lcc_fit -f <path to files>``

   **v3.x**: ``polar2grid.sh -r mirs -w geotiff --num-workers 6 --grid-coverage 0 --fill-value 0 -p rain_rate sea_ice snow_cover swe tpw sfr btemp_57h1 btemp_23v btemp_165h btemp_183h1 btemp_88v -g lcc_fit -f <path to files>``

Create MODIS AWIPS tiles files for the Alaska Region.

   **v2.3**: ``polar2grid.sh modis scmi -p vis01 vis02 --sector-id Polar --letters --compress --grid-coverage 0.00001 -g polar_alaska_300 -f <path to files>``

   **v3.x**: ``polar2grid.sh -r modis_l1b -w awips_tiled --grid-coverage 0.00001 -p vis01 vis02 -g polar_alaska_300 --sector-id Polar --letters --compress --num-workers 8 -f <path to files>``

Create rescaled AMSR2 GeoTIFF output files.

   **v2.3**: ``polar2grid.sh amsr2_l1b gtiff --rescale-configs $POLAR2GRID_HOME/rescale_configs/amsr2_png.ini -g lcc_fit -f <path to file>``

   **v3.x**: ``polar2grid.sh -r amsr2_l1b -w geotiff --extra-config-path $POLAR2GRID_HOME/example_enhancements/amsr2_png --fill-value 0 -f <path to file>``
