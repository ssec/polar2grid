;*========================================================================
;* extract_ancil.pro - extract an ancillary file from a level1b modis file
;*
;* 8-Feb-2001  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /export/data/ms2gth/src/idl/modis_utils/extract_ancil.pro,v 1.2 2001/02/19 01:03:14 haran Exp $
;*========================================================================*/

;+
; NAME:
;	extract_ancil
;
; PURPOSE:
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       extract_ancil, hdf_file, tag, ancillary, $
;                      /get_latlon, conversion=conversion, $
;                      swath_rows=swath_rows, $
;                      swath_row_first=swath_row_first
;
; ARGUMENTS:         
;
; KEYWORDS:
;
; EXAMPLE:
;
; ALGORITHM:
;
; REFERENCE:
;-

PRO extract_ancil, hdf_file, tag, ancillary, $
                   get_latlon=get_latlon, conversion=conversion, $
                   swath_rows=swath_rows, $
                   swath_row_first=swath_row_first

  usage = 'usage: extract_ancil, hdf_file, tag, ancillary ' + $
          '[, /get_latlon]' + $
          '[, conversion=conversion]' + $
          '[, swath_rows=swath_rows]' + $
          '[, swath_row_first=swath_row_first]'

  if n_params() ne 3 then $
    message, usage
  if n_elements(get_latlon) eq 0 then $
    get_latlon = 0
  if n_elements(conversion) eq 0 then $
    conversion = 'raw'
  if n_elements(swath_rows) eq 0 then $
    swath_rows = 0
  if n_elements(swath_row_first) eq 0 then $
    swath_row_first = 0

  print, 'extract_ancil:'
  print, '  hdf_file:       ', hdf_file
  print, '  tag:            ', tag
  print, '  ancillary:      ', ancillary
  print, '  get_latlon:     ', get_latlon
  print, '  conversion:     ', conversion
  print, '  swath_rows:     ', swath_rows
  print, '  swath_row_first:', swath_row_first

  area = [0L, swath_row_first, 999999L, swath_rows]
  if get_latlon ne 0 then begin
      modis_ancillary_read, hdf_file, ancillary, image, $
                            conversion=conversion, area=area, $
                            latitude=lat, longitude=lon, $
      lat_dimen = size(lat, /dimensions)
      cols = lat_dimen[0]
      rows = lat_dimen[1]
      cols_string = string(cols, format='(I5.5)')
      rows_string = string(rows, format='(I5.5)')
      lat_file_out = tag + '_latf_' + $
        cols_string + '_' + rows_string + '.img'
      lon_file_out = tag + '_lonf_' + $
        cols_string + '_' + rows_string + '.img'
      openw, lat_lun, lat_file_out, /get_lun
      openw, lon_lun, lon_file_out, /get_lun
      writeu, lat_lun, lat
      writeu, lon_lun, lon
      free_lun, lat_lun
      free_lun, lon_lun
  endif else begin
      modis_ancillary_read, hdf_file, ancillary, image, $
                            conversion=conversion, area=area
  endelse
  image_dimen = size(image, /dimensions)
  conv_string = strmid(conversion, 0, 3)
  cols_string = string(image_dimen[0], format='(I5.5)')
  rows_string = string(image_dimen[1], format='(I5.5)')
  file_out = tag + '_' + ancillary + '_' + $
             conv_string + '_' + $
             cols_string + '_' + rows_string + '.img'
  openw, lun, file_out, /get_lun
  writeu, lun, image
  free_lun, lun

END ; extract_ancil
