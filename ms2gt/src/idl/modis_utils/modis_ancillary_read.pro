;*========================================================================
;* modis_ancillary_read.pro - extract an ancillary array from a mod02 or
;                             mod03 file.
;*
;* 7-Feb-2001  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /export/data/ms2gth/src/idl/modis_utils/modis_ancillary_read.pro,v 1.2 2001/02/19 01:04:12 haran Exp $
;*========================================================================*/

;+
; NAME:
;    modis_ancillary_read
;
; PURPOSE:
;    Read a single ancillary array from a MODIS Level 1b product file
;    (mod02) or geolocation file (mod03).
;
;    The output image is available in the following units:
;    RAW:         Raw integer values as they appear in the HDF file.
;    SCALED:      Scaled floating-point values.
;
;    This procedure uses only HDF calls (it does *not* use HDF-EOS),
;    and only reads from SDS and Vdata arrays (it does *not* read ECS
;    metadata).
;
; CATEGORY:
;    MODIS utilities.
;
; CALLING SEQUENCE:
;    MODIS_ANCILLARY_READ, FILENAME, ANCILLARY, IMAGE
;
; INPUTS:
;    FILENAME       Name of MODIS Level 1B HDF or geolocation file.
;    ANCILLARY      Four character string specify the name of the ancillary
;                   data to be read:
;                     none - don't read any ancillary data
;                     hght - Height
;                     seze - SensorZenith
;                     seaz - SensorAzimuth
;                     rang - Range
;                     soze - SolarZenith
;                     soaz - SolarAzimuth
;                     lmsk - Land/SeaMask (available in MOD03 only)
;                     gflg - gflags
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    CONVERSION     Specifies the type of conversion to be performed on the
;                   ancillary data. Must be set to one to one of the
;                   following strings:
;                   raw - specifies that ancillary data are returned as raw
;                     HDF integer values. This is the default.
;                   scaled - specifies that ancillary data are returned as
;                     scaled floating-point values. Raw values equal to the
;                     fill value will be set to -999.0. Note that for those
;                     ancillary parameters that don't include a scale factor,
;                     namely Height, Land/SeaMask, and gflags, a scale factor
;                     of 1.0 will be used.
;    AREA           A four element vector specifying the area to be read,
;                   in the format [X0,Y0,NX,NY]
;                   (default is to read the entire image).
;    LATITUDE       On return, an array containing the latitude data as
;                   floating-point degrees.
;    LONGITUDE      On return, an array containing the longitude data as
;                   floating-point degrees.
;    
; OUTPUTS:
;    IMAGE          A two dimensional array of image data in the requested
;                   units.
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
;    HDF_SD_VARLIST      Get a list of SDS variable names
;    HDF_SD_VARREAD      Read an SDS variable
;
; EXAMPLE:
;    modis_ancillary_read, 'MOD021KM.A2000153.1445.002.2000156075718.hdf', $
;                          'soze', solar_zenith, conversion='scaled', $
;                          latitude=lat, longitude=lon
;
;-

PRO modis_ancillary_read, filename, ancillary, image, $
                          conversion=conversion, area=area, $
                          latitude=latitude, longitude=longitude

rcs_id = '$Id: modis_ancillary_read.pro,v 1.2 2001/02/19 01:04:12 haran Exp $'

;-----------------------------------------------------------------------------
;- CHECK INPUT
;-----------------------------------------------------------------------------

;- Check arguments
if (n_params() ne 3) then $
  message, 'Usage: MODIS_ANCILLARY_READ, FILENAME, ANCILLARY, IMAGE'

if (n_elements(filename) eq 0) then $
  message, 'Argument FILENAME is undefined'

if (n_elements(ancillary) eq 0) then $
  message, 'Argument ANCILLARY is undefined'

if (arg_present(image) ne 1) then $
  message, 'Argument IMAGE cannot be modified'

if (n_elements(area) gt 0) then begin
  if (n_elements(area) ne 4) then $
    message, 'AREA must be a 4-element vector of the form [X0,Y0,NX,NY]'
endif

;- Check options
if (n_elements(conversion) eq 0) then $
  conversion='raw'
conversion = strlowcase(conversion)
if (conversion ne 'raw') and (conversion ne 'scaled') then $
  message, 'CONVERSION option must be set to either RAW or SCALED'

;-----------------------------------------------------------------------------
;- CHECK FOR VALID MODIS L1B HDF FILE, AND GET FILE TYPE
;  mod02 or mod03
;-----------------------------------------------------------------------------

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
index = where(varlist.varnames eq 'Land/SeaMask',    count_geo)
case 1 of
  (count_1km eq 1) : filetype = 'MOD021KM'
  (count_500 eq 1) : filetype = 'MOD02HKM'
  (count_250 eq 1) : filetype = 'MOD02QKM'
  (count_geo eq 1) : filetype = 'MOD03'
  else : message, $
    'FILENAME is not MODIS MOD02 or MOD03 => ' + fileinfo.name
endcase  

;-----------------------------------------------------------------------------
;- CHECK ANCILLARY NAME
;-----------------------------------------------------------------------------

;- Check ancillary name
case filetype of
    'MOD021KM' : begin
        if (ancillary ne 'none') and $
          (ancillary ne 'hght') and $
          (ancillary ne 'seze') and $
          (ancillary ne 'seaz') and $
          (ancillary ne 'rang') and $
          (ancillary ne 'soze') and $
          (ancillary ne 'soaz') and $
          (ancillary ne 'gflg') then $
          message, 'ancillary value ' + ancillary + $
                   ' is not supported for this MODIS type => ' + filetype
    end
    'MOD02HKM' : begin
        if (ancillary ne 'none') then $
          message, 'ancillary value ' + ancillary + $
                   ' is not supported for this MODIS type => ' + filetype
    end
    'MOD02QKM' : begin
        if (ancillary ne 'none') then $
          message, 'ancillary value ' + ancillary + $
                   ' is not supported for this MODIS type => ' + filetype
    end
    'MOD03' : begin
        if (ancillary ne 'none') and $
          (ancillary ne 'hght') and $
          (ancillary ne 'seze') and $
          (ancillary ne 'seaz') and $
          (ancillary ne 'rang') and $
          (ancillary ne 'soze') and $
          (ancillary ne 'soaz') and $
          (ancillary ne 'lmsk') and $
          (ancillary ne 'gflg') then $
          message, 'ancillary value ' + ancillary + $
                   ' is not supported for this MODIS type => ' + filetype
    end
endcase

;-----------------------------------------------------------------------------
;- OPEN THE FILE IN SDS MODE
;-----------------------------------------------------------------------------

sd_id = hdf_sd_start(fileinfo.name)

;-----------------------------------------------------------------------------
;- PROCESS ANCILLARY DATA
;-----------------------------------------------------------------------------

if (ancillary ne 'none') then begin

  ; Set variable name for ancillary data
    case ancillary of
        'hght' : sds_name = 'Height'
        'seze' : sds_name = 'SensorZenith'
        'seaz' : sds_name = 'SensorAzimuth'
        'rang' : sds_name = 'Range'
        'soze' : sds_name = 'SolarZenith'
        'soaz' : sds_name = 'SolarAzimuth'
        'lmsk' : sds_name = 'Land/SeaMask'
        'gflg' : sds_name = 'gflags'
    endcase

  ;- Get information about the image array
    varinfo = hdf_sd_varinfo(sd_id, sds_name)
    if (varinfo.name eq '') then $
      message, 'Image array was not found: ' + sds_name
    npixels_across = varinfo.dims[0]
    npixels_along  = varinfo.dims[1]

  ;- Set start and count values
    start = [0L, 0L]
    count = [npixels_across, npixels_along]

  ;- Use AREA keyword if it was supplied
    if (n_elements(area) eq 4) then begin
        start[0] = (long(area[0]) > 0L) < (npixels_across - 1L)
        start[1] = (long(area[1]) > 0L) < (npixels_along  - 1L)
        count[0] = (long(area[2]) > 1L) < (npixels_across - start[0])
        count[1] = (long(area[3]) > 1L) < (npixels_along  - start[1])
    endif

;- Read ancillary data
    hdf_sd_varread, sd_id, sds_name, image, start=start, count=count 

    if conversion eq 'scaled' then begin

    ;- Get fill value
        attname = '_FillValue'
        attinfo = hdf_sd_attinfo(sd_id, sds_name, attname)
        if (attinfo.name eq attname) then $
          fill = attinfo.data[0] $
        else $
          fill = 0

    ;- Create an index array for filled values
        i = where(image eq fill, count)

    ;- Check for a scale factor
        attname = 'scale_factor'
        attinfo = hdf_sd_attinfo(sd_id, sds_name, attname)
        if (attinfo.name eq attname) then $
          image = float(temporary(image) * attinfo.data[0]) $
        else $
          image = temporary(image) * 1.0

    ;- Set fill values to -999.0
        if count gt 0 then $
          image[i] = -999.0
        
    endif
endif

;- Read latitude and longitude arrays
if arg_present(latitude) then hdf_sd_varread, sd_id, 'Latitude', latitude
if arg_present(longitude) then hdf_sd_varread, sd_id, 'Longitude', longitude

;-----------------------------------------------------------------------------
;- CLOSE THE FILE IN SDS MODE
;-----------------------------------------------------------------------------

hdf_sd_end, sd_id

END
