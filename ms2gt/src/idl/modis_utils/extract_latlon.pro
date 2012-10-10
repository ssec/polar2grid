;*========================================================================
;* extract_latlon.pro - extract latitude and longitude from a mod02 or
;                       mod03 file
;*
;* 25-Oct-2000  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /disks/megadune/data/tharan/ms2gth/src/idl/modis_utils/extract_latlon.pro,v 1.12 2010/09/04 18:45:55 tharan Exp $
;*========================================================================*/

;+
; NAME:
;	extract_latlon
;
; PURPOSE:
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       extract_latlon, hdf_file, tag
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

PRO extract_latlon, hdf_file, tag

  usage = 'usage: extract_latlon, hdf_file, tag'

  if n_params() ne 2 then $
    message, usage

  print, 'extract_latlon:'
  print, '  hdf_file:             ', hdf_file
  print, '  tag:                  ', tag

  ancillary = 'none'
  modis_ancillary_read, hdf_file, ancillary, image, $
                        latitude=lat, longitude=lon
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

END ; extract_latlon
