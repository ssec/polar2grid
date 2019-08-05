Release Notes
=============

Version 1.0.1 (unreleased)
--------------------------

* Fix resampling freezing when output grid was larger than 1024x1024
* Fix crash when certain RGBs were created with '--ll-bbox'
* Add missing '--radius-of-influence' flag for nearest neighbor resampling

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
