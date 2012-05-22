PRO MODIS_SNOW_READ, FILENAME, BAND, IMAGE, $
                     LATITUDE=LATITUDE, LONGITUDE=LONGITUDE
  
;+
; NAME:
;    MODIS_SNOW_READ
;
; PURPOSE:
;    Read a single band from a MOD10_L2 modis snow product file at
;    500m resolution.
;
;    This procedure uses only HDF calls (it does *not* use HDF-EOS),
;    and only reads from SDS and Vdata arrays (it does *not* read ECS metadata).
;
; CATEGORY:
;    MODIS utilities.
;
; CALLING SEQUENCE:
;    MODIS_SNOW_READ, FILENAME, BAND, IMAGE
;
; INPUTS:
;    FILENAME       Name of MODIS Level 1B HDF file
;    BAND           Band number to be read: 1 (snow cover), 2 (qa),
;                                           3 (snow cover reduced cloud)
;                                           4 (fractional snow cover)
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    LATITUDE       On return, an array containing the reduced resolution latitude
;                   data for the entire granule (5km resolution).
;    LONGITUDE      On return, an array containing the reduced resolution longitude
;                   data for the entire granule (5km resolution).
;    
; OUTPUTS:
;    IMAGE          A two dimensional byte array of image data.
;
; OPTIONAL OUTPUTS:
;    None.
;
; COMMON BLOCKS:
;    None
;
; SIDE EFFECTS:
;    None.
;
; RESTRICTIONS:
;    Requires IDL 5.0 or higher (square bracket array syntax).
;
;    Requires the following HDF procedures by Liam.Gumley@ssec.wisc.edu:
;    HDF_SD_ATTINFO      Get information about an attribute
;    HDF_SD_ATTLIST      Get list of attribute names
;    HDF_SD_VARINFO      Get information about an SDS variable
;    HDF_SD_VARLIST      Get a list of SDS variable names
;    HDF_SD_VARREAD      Read an SDS variable
;    HDF_VD_VDATAINFO    Get information about a Vdata
;    HDF_VD_VDATALIST    Get list of Vdata names
;    HDF_VD_VDATAREAD    Read a Vdata field
;
; EXAMPLES:
;
; REFERENCE:
;    Based on modis_level1b_read from Liam Gumley.
;-

rcs_id = '$Id: modis_snow_read.pro,v 1.4 2006/05/26 17:44:53 tharan Exp $'

;-------------------------------------------------------------------------------
;- CHECK INPUT
;-------------------------------------------------------------------------------

;- Check arguments
if (n_params() ne 3) then $
  message, 'Usage: MODIS_SNOW_READ, FILENAME, BAND, IMAGE'

if (n_elements(filename) eq 0) then $
  message, 'Argument FILENAME is undefined'

if (n_elements(band) eq 0) then $
  message, 'Argument BAND is undefined'

if (arg_present(image) ne 1) then $
  message, 'Argument IMAGE cannot be modified'

;-------------------------------------------------------------------------------
;- CHECK FOR VALID MODIS SNOW HDF FILE
;-------------------------------------------------------------------------------

;- Check that file exists
if ((findfile(filename))[0] eq '') then $
  message, 'FILENAME was not found => ' + filename
  
;- Get expanded filename
openr, lun, filename, /get_lun
fileinfo = fstat(lun)
free_lun, lun

;- Check that file is HDF
if (hdf_ishdf(fileinfo.name) ne 1) then $
  message, 'FILENAME is not HDF => ' + fileinfo.name

;- Get list of SDS arrays
sd_id = hdf_sd_start(fileinfo.name)
varlist = hdf_sd_varlist(sd_id)
hdf_sd_end, sd_id

;-------------------------------------------------------------------------------
;- SET VARIABLE NAME FOR IMAGE DATA
;  -------------------------------------------------------------------------------

case band of
    1: sds_names = ['Snow Cover', 'Snow_Cover']
    2: sds_names = ['Snow Cover PixelQA', 'Snow_Cover_Pixel_QA']
    3: sds_names = ['Snow Cover Reduced Cloud']
    4: sds_names = ['Fractional_Snow_Cover']
    else: message, 'BAND range is not 1-4 for file ' + fileinfo.name 
endcase
for i = 0, n_elements(sds_names) - 1 do begin
    sds_name = sds_names[i]
    index = where(varlist.varnames eq sds_name, count_snow)
    if (count_snow eq 1) then $
      break
endfor
if (count_snow eq 0) then $
  message, $
  'No ' + sds_name + ' sds found for file ' + fileinfo.name

;-------------------------------------------------------------------------------
;- OPEN THE FILE IN SDS MODE
;-------------------------------------------------------------------------------

sd_id = hdf_sd_start(fileinfo.name)

;- Read the image array
print, 'sds_name:', sds_name
hdf_sd_varread, sd_id, sds_name, image

;- Read latitude and longitude arrays
if arg_present(latitude) then hdf_sd_varread, sd_id, 'Latitude', latitude
if arg_present(longitude) then hdf_sd_varread, sd_id, 'Longitude', longitude

;-------------------------------------------------------------------------------
;- CLOSE THE FILE IN SDS MODE
;-------------------------------------------------------------------------------

hdf_sd_end, sd_id

END
