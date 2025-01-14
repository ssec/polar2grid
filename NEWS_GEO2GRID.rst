Release Notes
=============

Version 1.3.0 (unreleased)
--------------------------

* Fix resampling coverage calculations

Version 1.2.0 (2023-05-10)
--------------------------
* Preliminary GOES-19 ABI reader support added
* Preliminary EUMETSAT MTG FCI (fci_l1c_nc) reader support added
* Additional ABI Product readers support added:

  * Aerosol Optical Depth (AOD)
  * Low Cloud and Fog (FLS)
  * Land Surface Temperature (LST)

* New 3.9 micron band scaling
* Added ABI AOD product example to documenation
* Support for additional RGBs
* Optimizations
* Bug fixes

Version 1.1.0 (2022-12-12)
--------------------------
* GOES-18 ABI reader support added
* ABI Level 2 (abi_l2_nc) reader added
* Gridded GLM (glm_l2) reader added
* GEO-KOMPSAT AMI (ami_l1b) reader added
* FY-4A AGRI (agri_fy4a_l1) reader added
* FY-4B AGRI (agri_fy4b_l1) reader added
* Various optimizations
* Support for additional RGBs
* Use of yaml files for grid definitions
* Various bug fixes

Version 1.0.2 (2020-08-17)
--------------------------

* Add workaround for threading issue in pyresample

Version 1.0.1 (2020-03-18)
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
