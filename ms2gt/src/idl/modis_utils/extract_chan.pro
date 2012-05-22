;*========================================================================
;* extract_chan.pro - extract a channel file from a level1b modis file
;*
;* 25-Oct-2000  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /data/tharan/ms2gth/src/idl/modis_utils/extract_chan.pro,v 1.22 2010/09/04 18:39:21 tharan Exp $
;*========================================================================*/

;+
; NAME:
;	extract_chan
;
; PURPOSE:
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       extract_chan, hdf_file, tag, channel, $
;                     /get_latlon, conversion=conversion, $
;                     swath_rows=swath_rows, $
;                     swath_row_first=swath_row_first
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

PRO extract_chan, hdf_file, tag, channel, $
                  get_latlon=get_latlon, conversion=conversion, $
                  swath_rows=swath_rows, $
                  swath_row_first=swath_row_first

  usage = 'usage: extract_chan, hdf_file, tag, channel ' + $
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

  raw = 0
  corrected = 0
  reflectance = 0
  temperature = 0

  if conversion eq 'raw' then $
    raw = 1
  if conversion eq 'corrected' then $
    corrected = 1
  if conversion eq 'reflectance' then $
    reflectance = 1
  if conversion eq 'temperature' then $
    temperature = 1

  modis_type = strmid(hdf_file, 0, 5)

  print, 'extract_chan:'
  print, '  hdf_file:             ', hdf_file
  print, '  tag:                  ', tag
  print, '  channel:              ', channel
  print, '  get_latlon:           ', get_latlon
  print, '  conversion:           ', conversion
  area = [0L, swath_row_first, 999999L, swath_rows]
  if (modis_type eq 'MOD02') or (modis_type eq 'MYD02') then begin
      print, '  swath_rows:           ', swath_rows
      print, '  swath_row_first:      ', swath_row_first
      print, '  area:                 ', area
  endif

  ; NOTE -- area only supported for mod02 for now
  if get_latlon ne 0 then begin
      if (modis_type eq 'MOD02') or (modis_type eq 'MYD02') then begin
          modis_level1b_read, hdf_file, channel, image, $
                              latitude=lat, longitude=lon, $
                              raw=raw, corrected=corrected, $
                              reflectance=reflectance, $
                              temperature=temperature, $
                              area=area
      endif else if (modis_type eq 'MOD10') or $
                    (modis_type eq 'MYD10') then begin
          modis_snow_read, hdf_file, channel, image, $
            latitude=lat, longitude=lon
      endif else if (modis_type eq 'MOD29') or $
                    (modis_type eq 'MYD29') then begin
          modis_ice_read, hdf_file, channel, image, $
            latitude=lat, longitude=lon
      endif else if (modis_type eq 'MOD35') or $
                    (modis_type eq 'MYD35') then begin
          modis_cloud_read, hdf_file, channel, image, $
            latitude=lat, longitude=lon
      endif else begin
          message, 'Unrecognized modis type: ' + modis_type
      endelse
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
      if (modis_type eq 'MOD02') or (modis_type eq 'MYD02') then begin 
          modis_level1b_read, hdf_file, channel, image, $
                              raw=raw, corrected=corrected, $
                              reflectance=reflectance, $
                              temperature=temperature, $
                              area=area
      endif else if (modis_type eq 'MOD10') or $
                    (modis_type eq 'MYD10') then begin
          modis_snow_read, hdf_file, channel, image
      endif else if (modis_type eq 'MOD29') or $
                    (modis_type eq 'MYD29') then begin
          modis_ice_read, hdf_file, channel, image
      endif else if (modis_type eq 'MOD35') or $
                    (modis_type eq 'MYD35') then begin
          modis_cloud_read, hdf_file, channel, image
      endif else begin
          message, 'Unrecognized modis type: ' + modis_type
      endelse
  endelse
  image_dimen = size(image, /dimensions)
  cols_string = string(image_dimen[0], format='(I5.5)')
  rows_string = string(image_dimen[1], format='(I5.5)')
  if (modis_type ne 'MOD35') and (modis_type ne 'MYD35') then begin
      channel_string = string(channel, format='(I2.2)')
      conv_string = strmid(conversion, 0, 3)
      file_out = tag + '_ch' + channel_string + '_' + $
        conv_string + '_' + $
        cols_string + '_' + rows_string + '.img'
  endif else begin
      file_out = tag + '_' + channel + '_raw_' + $
        cols_string + '_' + rows_string + '.img'
  endelse
  openw, lun, file_out, /get_lun
  writeu, lun, image
  free_lun, lun

END ; extract_chan
