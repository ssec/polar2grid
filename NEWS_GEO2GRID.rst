Release Notes
=============

Version 1.0.1 (unreleased)
--------------------------

* Significantly improved performance by enabling multithreaded geotiff compression
* Improve day/night transition region in day/night composites
* Fix resampling freezing when output grid was larger than 1024x1024
* Fix crash when certain RGBs were created with '--ll-bbox'
* Add missing '--radius-of-influence' flag for nearest neighbor resampling
* Add ability to native resample to lower resolution grids
* Add 'goes_east_Xkm' and 'goes_west_Xkm' grids for easier lower resolution resampling
* Add AHI airmass, ash, dust, fog, and night_microphysics RGBs
* Accept PNG or GeoTIFFs with gtiff2mp4.sh video generation

Version 1.0.0 (2019-03-01)
--------------------------

* New Geo2Grid Package!
* ABI L1B (abi_l1b) reader added
* AHI HSD (ahi_hsd) reader added
* AHI HRIT/HimawariCast (ahi_hrit) reader added
* Geotiff (geotiff) writer added
* Multi-threaded (multiple worker) processing
* Sharpened rayleigh-corrected full-resolution true and natural color RGBs
* Command line Lat/Lon defined subsets
* User defined grid capability
* MIN/MAX native resampling possible
