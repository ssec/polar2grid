PRO MODIS_LEVEL1B_READ, FILENAME, BAND, IMAGE, $
  RAW=RAW, CORRECTED=CORRECTED, REFLECTANCE=REFLECTANCE, TEMPERATURE=TEMPERATURE, $
  AREA=AREA, $
  UNITS=UNITS, PARAMETER=PARAMETER, $
  SCANTIME=SCANTIME, LATITUDE=LATITUDE, LONGITUDE=LONGITUDE, $
  VALID_INDEX=VALID_INDEX, VALID_COUNT=VALID_COUNT, $
  INVALID_INDEX=INVALID_INDEX, INVALID_COUNT=INVALID_COUNT, $
  RANGE=RANGE
  
;+
; NAME:
;    MODIS_LEVEL1B_READ
;
; PURPOSE:
;    Read a single band from a MODIS Level 1B HDF product file at
;    1000, 500, or 250 m resolution.
;
;    The output image is available in the following units (Radiance is default):
;    RAW DATA:    Raw data values as they appear in the HDF file
;    CORRECTED:   Corrected counts
;    RADIANCE:    Radiance (Watts per square meter per steradian per micron)
;    REFLECTANCE: Reflectance (Bands 1-19 and 26; *without* solar zenith correction)
;    TEMPERATURE: Brightness Temperature (Bands 20-25 and 27-36, Kelvin)
;
;    This procedure uses only HDF calls (it does *not* use HDF-EOS),
;    and only reads from SDS and Vdata arrays (it does *not* read ECS metadata).
;
; CATEGORY:
;    MODIS utilities.
;
; CALLING SEQUENCE:
;    MODIS_LEVEL1B_READ, FILENAME, BAND, IMAGE
;
; INPUTS:
;    FILENAME       Name of MODIS Level 1B HDF file
;    BAND           Band number to be read
;                   (1-36 for 1000 m, 1-7 for 500 m, 1-2 for 250m)
;                   (Use 13, 13.5, 14, 14.5 for 13lo, 13hi, 14lo, 14hi)
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    RAW            If set, image data are returned as raw HDF values
;                   (default is to return image data as radiance).
;    CORRECTED      If set, image data are returned as corrected counts
;                   (default is to return image data as radiance).
;    REFLECTANCE    If set, image data for bands 1-19 and 26 only are
;                   returned as reflectance *without* solar zenith angle correction
;                   (default is to return image data as radiance).
;    TEMPERATURE    If set, image data for bands 20-25 and 27-36 only are
;                   returned as brightness temperature
;                   (default is to return image data as radiance).
;    AREA           A four element vector specifying the area to be read,
;                   in the format [X0,Y0,NX,NY]
;                   (default is to read the entire image).
;    UNITS          On return, a string describing the image units.
;    PARAMETER      On return, a string describing the image (e.g. 'Radiance').
;    SCANTIME       On return, a vector containing the start time of each scan
;                   (SDPTK TAI seconds).
;    LATITUDE       On return, an array containing the reduced resolution latitude
;                   data for the entire granule (degrees, every 5th line and pixel).
;    LONGITUDE      On return, an array containing the reduced resolution longitude
;                   data for the entire granule (degrees, every 5th line and pixel).
;    VALID_INDEX    On return, a vector containing the 1D indexes of pixels which
;                   are within the 'valid_range' attribute values.
;    VALID_COUNT    On return, the number of pixels which
;                   are within the 'valid_range' attribute values.
;    INVALID_INDEX  On return, a vector containing the 1D indexes of pixels which
;                   are not within the 'valid_range' attribute values.
;    INVALID_COUNT  On return, the number of pixels which
;                   are not within the 'valid_range' attribute values.
;    RANGE          On return, a 2-element vector containing the minimum and 
;                   maximum data values within the 'valid range'.
;    
; OUTPUTS:
;    IMAGE          A two dimensional array of image data in the requested units.
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
;    Requires the following Planck procedures by Liam.Gumley@ssec.wisc.edu:
;    MODIS_BRIGHT        Compute MODIS brightness temperature
;    MODIS_PLANCK        Compute MODIS Planck radiance
;    BRIGHT_M            Compute brightness temperature (EOS radiance units)
;    BRITE_M             Compute brightness temperature (UW-SSEC radiance units)
;    PLANCK_M            Compute monochromatic Planck radiance (EOS units)
;    PLANC_M             Compute monochromatic Planck radiance (UW-SSEC units)
;
; EXAMPLES:
;
;; These examples require the IMDISP image display procedure, available from
;; http://cimss.ssec.wisc.edu/~gumley/imdisp.html
;
;; Read band 1 in radiance units from a 1000 m resolution file
;file = 'MOD021KM.A2000062.1020.002.2000066023928.hdf'
;modis_level1b_read, file, 1, band01
;imdisp, band01, margin=0, order=1
;
;; Read band 31 in temperature units from a 1000 m resolution file
;file = 'MOD021KM.A2000062.1020.002.2000066023928.hdf'
;modis_level1b_read, file, 31, band31, /temperature
;imdisp, band31, margin=0, order=1, range=[285, 320]
;
;; Read a band 1 subset in reflectance units from a 500 m resolution file
;file = 'MOD02HKM.A2000062.1020.002.2000066023928.hdf'
;modis_level1b_read, file, 1, band01, /reflectance, area=[1000, 1000, 700, 700]
;imdisp, band01, margin=0, order=1
;
;; Read band 6 in reflectance units from a 1000 m resolution file, 
;; and screen out invalid data when scaling
;file = 'MOD021KM.A2000062.1020.002.2000066023928.hdf'
;modis_level1b_read, file, 6, band06, /reflectance, valid_index=valid_index
;range = [min(band06[valid_index]), max(band06[valid_index])]
;imdisp, band06, margin=0, order=1, range=range
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: modis_level1b_read.pro,v 1.12 2010/09/04 18:26:18 tharan Exp $
;
; Copyright (C) 1999, 2000 Liam E. Gumley
;
; This program is free software; you can redistribute it and/or
; modify it under the terms of the GNU General Public License
; as published by the Free Software Foundation; either version 2
; of the License, or (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
;-

rcs_id = '$Id: modis_level1b_read.pro,v 1.12 2010/09/04 18:26:18 tharan Exp $'

;-------------------------------------------------------------------------------
;- CHECK INPUT
;-------------------------------------------------------------------------------

;- Check arguments
if (n_params() ne 3) then $
  message, 'Usage: MODIS_LEVEL1B_READ, FILENAME, BAND, IMAGE'

if (n_elements(filename) eq 0) then $
  message, 'Argument FILENAME is undefined'

if (n_elements(band) eq 0) then $
  message, 'Argument BAND is undefined'

if (arg_present(image) ne 1) then $
  message, 'Argument IMAGE cannot be modified'

if (n_elements(area) gt 0) then begin
  if (n_elements(area) ne 4) then $
    message, 'AREA must be a 4-element vector of the form [X0,Y0,NX,NY]'
endif

;-------------------------------------------------------------------------------
;- CHECK FOR VALID MODIS L1B HDF FILE, AND GET FILE TYPE (1km, 500 m, or 250 m)
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
index = where(varlist.varnames eq 'EV_1KM_Emissive', count_1km)
index = where(varlist.varnames eq 'EV_500_RefSB',    count_500)
index = where(varlist.varnames eq 'EV_250_RefSB',    count_250)
case 1 of
  (count_1km eq 1) : filetype = 'MOD021KM'
  (count_500 eq 1) : filetype = 'MOD02HKM'
  (count_250 eq 1) : filetype = 'MOD02QKM'
  else : message, 'FILENAME is not MODIS Level 1B HDF => ' + fileinfo.name
endcase  

;-------------------------------------------------------------------------------
;- CHECK BAND NUMBER, AND KEYWORDS WHICH DEPEND ON BAND NUMBER
;-------------------------------------------------------------------------------

;- Check band number
case filetype of
  'MOD021KM' : if (band lt 1) or (band gt 36) then $
    message, 'BAND range is 1-36 for this MODIS type => ' + filetype
  'MOD02HKM' : if (band lt 1) or (band gt 7) then $
    message, 'BAND range is 1-7 for this MODIS type => ' + filetype
  'MOD02QKM' : if (band lt 1) or (band gt 2) then $
    message, 'BAND range is 1-2 for this MODIS type => ' + filetype
endcase

;- Check for invalid request for reflectance units
if ((band ge 20) and (band ne 26)) and keyword_set(reflectance) then $
  message, 'REFLECTANCE units valid for bands 1-19, 26 only'

;- Check for invalid request for temperature units
if ((band le 19) or (band eq 26)) and keyword_set(temperature) then $
  message, 'TEMPERATURE units valid for bands 20-25, 27-36 only'

;-------------------------------------------------------------------------------
;- SET VARIABLE NAME FOR IMAGE DATA
;-------------------------------------------------------------------------------

case filetype of

  ;- 1 km resolution data
  'MOD021KM' : begin
      lines_per_scan = 10
    case 1 of
      (band ge  1 and band le  2) : sds_name = 'EV_250_Aggr1km_RefSB'
      (band ge  3 and band le  7) : sds_name = 'EV_500_Aggr1km_RefSB'
      (band ge  8 and band le 19) : sds_name = 'EV_1KM_RefSB'
      (band eq 26)                : sds_name = 'EV_Band26'
      (band ge 20 and band le 36) : sds_name = 'EV_1KM_Emissive'
    endcase
  end
  
  ;- 500 m resolution data
  'MOD02HKM' : begin
      lines_per_scan = 20
    case 1 of
      (band ge  1 and band le  2) : sds_name = 'EV_250_Aggr500_RefSB'
      (band ge  3 and band le  7) : sds_name = 'EV_500_RefSB'
    endcase
  end
  
  ;- 250 m resolution data
  'MOD02QKM' : begin
      lines_per_scan = 40
      sds_name = 'EV_250_RefSB'
  end

endcase

;-------------------------------------------------------------------------------
;- SET ATTRIBUTE NAMES FOR IMAGE DATA
;-------------------------------------------------------------------------------

;- Set names of scale, offset, and units attributes
case 1 of

  keyword_set(reflectance) : begin
    scale_name  = 'reflectance_scales'
    offset_name = 'reflectance_offsets'
    units_name  = 'reflectance_units'
    parameter   = 'Reflectance'
  end

  keyword_set(corrected) : begin
    scale_name  = 'corrected_counts_scales'
    offset_name = 'corrected_counts_offsets'
    units_name  = 'corrected_counts_units'
    parameter   = 'Corrected Counts'
  end

  else : begin
    scale_name  = 'radiance_scales'
    offset_name = 'radiance_offsets'
    units_name  = 'radiance_units'
    parameter   = 'Radiance'
  end

endcase

;-------------------------------------------------------------------------------
;- OPEN THE FILE IN SDS MODE
;-------------------------------------------------------------------------------

sd_id = hdf_sd_start(fileinfo.name)

;-------------------------------------------------------------------------------
;- CHECK BAND ORDER AND GET BAND INDEX
;-------------------------------------------------------------------------------

if (band ne 26) then begin

  ;- Get the actual band order
  band_name = 'band_names'
  att_info = hdf_sd_attinfo(sd_id, sds_name, band_name)
  if (att_info.name eq '') then message, 'Attribute not found: ' + band_name
  band_data = att_info.data

  ;- Set expected band order
  case 1 of
    (band ge  1 and band le  2) : $
      band_order = '1,2'
    (band ge  3 and band le  7) : $
      band_order = '3,4,5,6,7'
    (band ge  8 and band le 19) : $
      band_order = '8,9,10,11,12,13lo,13hi,14lo,14hi,15,16,17,18,19,26'
    (band ge 20 and band le 36) : $
      band_order = '20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36'
  endcase

  ;- Check actual band order against expected band order
  if (band_data ne band_order) then $
    message, 'Unexpected band order in image array'

  ;- Get band index
  case 1 of
    (band ge  1 and band le  2) : band_index = band -  1
    (band ge  3 and band le  7) : band_index = band -  3
    (band ge  8 and band le 12) : band_index = band -  8
    (band ge 13 and band lt 15) : band_index = 2 * band - 21
    (band ge 15 and band le 19) : band_index = band -  6 
    (band ge 20 and band le 25) : band_index = band - 20
    (band ge 27 and band le 36) : band_index = band - 21
  endcase
  
endif else begin

  band_index = -1
  
endelse

;-------------------------------------------------------------------------------
;- READ IMAGE DATA
;-------------------------------------------------------------------------------

;- Get valid scans for the channel data
image = extract_valid_scans(sd_id, sds_name, lines_per_scan, band_index, $
                            area=area)

if band eq 26 then $
  band_index = 0

;-------------------------------------------------------------------------------
;- READ IMAGE ATTRIBUTES
;-------------------------------------------------------------------------------

;- Read scale attribute
att_info = hdf_sd_attinfo(sd_id, sds_name, scale_name)
if (att_info.name eq '') then message, 'Attribute not found: ' + scale_name
scale = att_info.data

;- Read offset attribute
att_info = hdf_sd_attinfo(sd_id, sds_name, offset_name)
if (att_info.name eq '') then message, 'Attribute not found: ' + offset_name
offset = att_info.data

;- Read units attribute
att_info = hdf_sd_attinfo(sd_id, sds_name, units_name)
if (att_info.name eq '') then message, 'Attribute not found: ' + units_name
units = att_info.data

;- Read valid range attribute
valid_name = 'valid_range'
att_info = hdf_sd_attinfo(sd_id, sds_name, valid_name)
if (att_info.name eq '') then message, 'Attribute not found: ' + valid_name
valid_range = att_info.data

;- Read latitude and longitude arrays
area10 = (area * 10) / lines_per_scan
if arg_present(latitude) then $
   latitude = extract_valid_scans(sd_id, 'Latitude', 10, -1, area=area10)
if arg_present(longitude) then $
   latitude = extract_valid_scans(sd_id, 'Longitude', 10, -1, area=area10)

;-------------------------------------------------------------------------------
;- CLOSE THE FILE IN SDS MODE
;-------------------------------------------------------------------------------

hdf_sd_end, sd_id

;-------------------------------------------------------------------------------
;- READ VDATA INFORMATION
;-------------------------------------------------------------------------------

;- Open the file in vdata mode
hdfid = hdf_open(fileinfo.name)

;- Read scan start time (SDPTK TAI seconds)
vdataname = 'Level 1B Swath Metadata'
hdf_vd_vdataread, hdfid, vdataname, 'EV Sector Start Time', scantime

;- Close the file in vdata mode
hdf_close, hdfid

;-------------------------------------------------------------------------------
;- CONVERT IMAGE TO REQUESTED OUTPUT UNITS
;-------------------------------------------------------------------------------

; I'VE CHANGED THE BEHAVIOR HERE SO THAT THIS CONVERSION IS ONLY PERFORMED
; IF WE DON'T WANT RAW DATA -- TERRY HARAN 10/20/2000

;- Convert from unsigned short integer to signed long integer

if not keyword_set(raw) then begin
    image = temporary(image) and 65535L
    valid_range = valid_range and 65535L
endif

;- Get valid/invalid indexes and counts
if arg_present(valid_index) or arg_present(valid_count) or $
  arg_present(invalid_index) or arg_present(invalid_count) or $
  arg_present(range) then begin   
  valid_check = (image ge valid_range[0]) and (image le valid_range[1])
  valid_index = where(valid_check eq 1, valid_count)
  invalid_index = where(valid_check eq 0, invalid_count)
endif

;- Convert to units requested by caller
if keyword_set(raw) then begin

  ;- Leave as HDF values
  units = 'Unsigned 16-bit integers'
  parameter = 'Raw HDF Values'

endif else begin

  ;- Convert image to unscaled values
  image = scale[band_index] * (temporary(image) - offset[band_index])

  ;- Convert radiance to brightness temperature for IR bands
  if keyword_set(temperature) then begin
    image = modis_bright(temporary(image), band, 1)
    units = 'Kelvin'
    parameter = 'Brightness Temperature'
  endif

endelse

;- Get data range (min/max of valid image values)
if arg_present(range) then begin
  minval = min(image[valid_index], max=maxval)
  range = [minval, maxval]
endif
  
END
