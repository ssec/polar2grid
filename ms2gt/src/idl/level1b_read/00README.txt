IDL routines for MODIS
----------------------
Liam E. Gumley
Space Science and Engineering Center, University of Wisconsin-Madison
Liam.Gumley@ssec.wisc.edu
608-265-5358

Last updated 04 May 2000:
- Fixed logic which checks for valid pixels in modis_level1b_read.pro

Source of these files: ftp://origin.ssec.wisc.edu/pub/MODIS/IDL

These routines are licensed under the terms of the GNU GPL (see LICENSE)

To read a single band of MODIS data, use modis_level1b_read.pro

MODIS specific routines
-----------------------
get_metadata.pro          Extract a PVL object value from a PVL string
modis_bright.pro          Compute MODIS brightness temperature
modis_file_info.pro       Get information about a MODIS product HDF file
modis_level1b_info.pro    Get information about a MODIS Level 1B HDF file
modis_level1b_read.pro    Read a single band from a MODIS Level 1B HDF file
modis_planck.pro          Compute MODIS Planck radiance

Generic routines
----------------
bright_m.pro              Compute brightness temperature (EOS radiance units)
brite_m.pro               Compute brightness temperature (UW-SSEC radiance units)
fileinfo.pro              Get information about a file
hdf_sd_attinfo.pro        Get information about a HDF attribute
hdf_sd_attlist.pro        Get a list of HDF attribute names
hdf_sd_varinfo.pro        Get information about a HDF SDS variable
hdf_sd_varlist.pro        Get a list of HDF SDS variable names
hdf_sd_varread.pro        Read a HDF SDS variable
hdf_vd_vdatainfo.pro      Get information about a HDF Vdata
hdf_vd_vdatalist.pro      Get list of HDF Vdata names
hdf_vd_vdataread.pro      Read a HDF Vdata field
planc_m.pro               Compute monochromatic Planck radiance (UW-SSEC units)
planck_m.pro              Compute monochromatic Planck radiance (EOS units)
