PRO MODIS_CLOUD_READ, FILENAME, BAND, IMAGE, $
                    LATITUDE=LATITUDE, LONGITUDE=LONGITUDE
  
;+
; NAME:
;    MODIS_CLOUD_READ
;
; PURPOSE:
;    Read a single band from a MOD35_L2 modis ice product file at
;    1km resolution.
;
;    This procedure uses only HDF calls (it does *not* use HDF-EOS),
;    and only reads from SDS and Vdata arrays (it does *not* read ECS metadata).
;
; CATEGORY:
;    MODIS utilities.
;
; CALLING SEQUENCE:
;    MODIS_CLOUD_READ, FILENAME, BAND, IMAGE
;
; INPUTS:
;    FILENAME       Name of MODIS Level 1B HDF file
;    BAND           String specifying Band to be read. Must be one of the
;                   following:
;                     time - Scan Start Time
;                     cld0 - contains Cloud Mask bits  7-0  in cld0 bits 7-0. 
;                     cld1 - contains Cloud Mask bits 15-8  in cld1 bits 7-0. 
;                     cld2 - contains Cloud Mask bits 23-16 in cld2 bits 7-0. 
;                     cld3 - contains Cloud Mask bits 31-24 in cld3 bits 7-0. 
;                     cld4 - contains Cloud Mask bits 39-32 in cld4 bits 7-0. 
;                     cld5 - contains Cloud Mask bits 47-40 in cld5 bits 7-0.
;                     cqa0 - Cloud Quality Assurance byte 0.
;                     cqa1 - Cloud Quality Assurance byte 1.
;                     cqa2 - Cloud Quality Assurance byte 2.
;                     cqa3 - Cloud Quality Assurance byte 3.
;                     cqa4 - Cloud Quality Assurance byte 4.
;                     cqa5 - Cloud Quality Assurance byte 5.
;                     cqa6 - Cloud Quality Assurance byte 6.
;                     cqa7 - Cloud Quality Assurance byte 7.
;                     cqa8 - Cloud Quality Assurance byte 8.
;                     cqa9 - Cloud Quality Assurance byte 9.
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
;    IMAGE          A two dimensional double (band = time) or byte array
;                   of image data at 1km resolution.
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

rcs_id = '$Id: modis_cloud_read.pro,v 1.2 2003/08/01 22:20:14 haran Exp $'

;-------------------------------------------------------------------------------
;- CHECK INPUT
;-------------------------------------------------------------------------------

;- Check arguments
if (n_params() ne 3) then $
  message, 'Usage: MODIS_CLOUD_READ, FILENAME, BAND, IMAGE'

if (n_elements(filename) eq 0) then $
  message, 'Argument FILENAME is undefined'

if (n_elements(band) eq 0) then $
  message, 'Argument BAND is undefined'

if (arg_present(image) ne 1) then $
  message, 'Argument IMAGE cannot be modified'

;-------------------------------------------------------------------------------
;- CHECK FOR VALID MODIS CLOUD HDF FILE
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

;- Locate image arrays
index = where(varlist.varnames eq 'Scan_Start_Time', count_time)
index = where(varlist.varnames eq 'Cloud_Mask', count_cld)
index = where(varlist.varnames eq 'Quality_Assurance', count_cqa)
if (count_time ne 1) or (count_cld ne 1) or (count_cqa ne 1) then $
  message, 'FILENAME is not MODIS Cloud Mask HDF => ' + fileinfo.name

;-------------------------------------------------------------------------------
;- SET VARIABLE NAME FOR IMAGE DATA
;-------------------------------------------------------------------------------

filetype = 'MOD35_L2'

case band of
  'time': begin & sds_name = 'Scan_Start_Time' & end
  'cld0': begin & sds_name = 'Cloud_Mask' & byte_elem = 0 & end
  'cld1': begin & sds_name = 'Cloud_Mask' & byte_elem = 1 & end
  'cld2': begin & sds_name = 'Cloud_Mask' & byte_elem = 2 & end
  'cld3': begin & sds_name = 'Cloud_Mask' & byte_elem = 3 & end
  'cld4': begin & sds_name = 'Cloud_Mask' & byte_elem = 4 & end
  'cld5': begin & sds_name = 'Cloud_Mask' & byte_elem = 5 & end
  'cqa0': begin & sds_name = 'Quality_Assurance' & byte_elem = 0 & end
  'cqa1': begin & sds_name = 'Quality_Assurance' & byte_elem = 1 & end
  'cqa2': begin & sds_name = 'Quality_Assurance' & byte_elem = 2 & end
  'cqa3': begin & sds_name = 'Quality_Assurance' & byte_elem = 3 & end
  'cqa4': begin & sds_name = 'Quality_Assurance' & byte_elem = 4 & end
  'cqa5': begin & sds_name = 'Quality_Assurance' & byte_elem = 5 & end
  'cqa6': begin & sds_name = 'Quality_Assurance' & byte_elem = 6 & end
  'cqa7': begin & sds_name = 'Quality_Assurance' & byte_elem = 7 & end
  'cqa8': begin & sds_name = 'Quality_Assurance' & byte_elem = 8 & end
  'cqa9': begin & sds_name = 'Quality_Assurance' & byte_elem = 9 & end
else: message, 'Unrecognized band => ' + band + $
  ' for this MODIS type => ' + filetype
endcase

;-------------------------------------------------------------------------------
;- OPEN THE FILE IN SDS MODE
;-------------------------------------------------------------------------------

sd_id = hdf_sd_start(fileinfo.name)

;-------------------------------------------------------------------------------
;- READ IMAGE DATA
;-------------------------------------------------------------------------------

;- read the image array and get its size
hdf_sd_varread, sd_id, sds_name, image
image_size = size(image, /dimensions)

if sds_name eq 'Scan_Start_Time' then begin

    ;- Get size information for the 1km Cloud Mask image array
    varinfo = hdf_sd_varinfo(sd_id, 'Cloud_Mask')
    if (varinfo.name eq '') then $
      message, 'Image array was not found: ' + 'Cloud_Mask'
    time1km_cols = varinfo.dims[0]
    time1km_rows = varinfo.dims[1]

    ;- expand the time array to 1km without interpolation
    time5km = image
    image = 0
    time5km_cols = image_size[0]
    time5km_rows = image_size[1]
    image = dblarr(time1km_cols, time1km_rows)
    if time1km_rows ne 5 * time5km_rows then $
      message, 'Cloud Mask array does not have 5 times the row count of the ' + $
               'Scan Start Time array'
    for i = 0, time5km_rows - 1 do begin
        time = time5km[0, i]
        time1km = replicate(time, time1km_cols)
        for j = 0, 4 do begin
            image[*, i * 5 + j] = time1km
        endfor
    endfor

endif else begin

    if sds_name eq 'Cloud_Mask' then begin
        image = reform(image[*, *, byte_elem], /overwrite)
    endif else begin
        image = reform(image[byte_elem, *, *], /overwrite)
    endelse

endelse

;- Read latitude and longitude arrays
if arg_present(latitude) then hdf_sd_varread, sd_id, 'Latitude', latitude
if arg_present(longitude) then hdf_sd_varread, sd_id, 'Longitude', longitude

;-------------------------------------------------------------------------------
;- CLOSE THE FILE IN SDS MODE
;-------------------------------------------------------------------------------

hdf_sd_end, sd_id

END
