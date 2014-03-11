This is a modified version of the original "00readme.txt" that came with the VIIRS CREFL software. The original readme
text is included at the bottom of this file for reference. The code has been patched and helper files/scripts added for
easier compiling and installation of the software.

COMPILE
-------

Note: On RHEL5/6 x86_64 systems prebuilt static binaries can be retrieved by running:
    make prebuilt

The VIIRS CREFL software consists of two programs, h5SDS_transfer_rename and cviirs. These files have the following
static library dependencies:
 - HDF5 (with zlib)
 - HDF4 (with zlib and libjpeg)
 - libjpeg
 - zlib

To compile the code statically run (assuming the dependencies are already installed on the system):

    make

To specify the locations of libraries and header files the "LDFLAGS" environment variable can be used:

    LDFLAGS="-I ~/opt/include -L ~/opt/lib" make


INSTALL
-------

To install the compiled binaries run in "/home/me":

    PREFIX="/home/me" make install


RUN
---

To run VIIRS CREFL run the following command:

    run_viirs_crefl.sh <SVM05 file>

Note that this requires "CMGDEM.hdf", "cviirs", and "h5SDS_tranfer_rename" to be in the
same directory as the run script.



###########################
##### Original README #####
###########################

This short tutorial describes how to install and run the VIIRS Corrected Reflectance code on VIIRS SDR files created by CSPP.
The script files and data described in this tutorial are available at

ftp://ftp.ssec.wisc.edu/pub/gumley/viirs_crefl/

1. To install the VIIRS Corrected Reflectance code, run the install script as shown below (note: Intel Linux host computer is assumed).

chmod u+x install_crefl.bash
./install_crefl.bash

This will download the VIIRS Corrected Reflectance software package from NASA DRL, and install it in your home directory.
To install it in a different directory, just edit the script.

2. Run the VIIRS Corrected Reflectance code on the test data. Note that the run script is executed once for each granule of VIIRS SDR data.
The run script will handle aggregated SDR granules created using CSPP (-a option in viirs_sdr.sh).

chmod u+x run_viirs_crefl.bash
./run_viirs_crefl.bash data/SVM05_npp_d20130331_t1802568_e1804210_b00001_c20130331182137542989_cspp_dev.h5

This will convert the SDR files (M-bands 3,4,5,7,8,10,11 and GMTCO; I-bands 1,2,3 and GITCO) to HDF4 format,
run the Corrected Reflectance code for the M-bands and I-bands, and write the output files in HDF4 format.
The Corrected Reflectance product files are similar in format to the MODIS Corrected Reflectance product files.

3. Now you can visualize the Corrected Reflectance product. In the example below, we use IDL for this purpose.

IDL> !path = 'idl:' + !path
IDL> crefl, 'CREFLM_npp_d20130331_t1802568_e1804210.hdf'

A future tutorial will describe how to create VIIRS true color images in a map projection with all sensor artifacts
(like the bowtie-deleted pixels) removed.

