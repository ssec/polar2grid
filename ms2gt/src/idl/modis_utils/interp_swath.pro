;*========================================================================
;* interp_swath.pro - interpolate swath files
;*
;* 8-Feb-2001  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /data/tharan/ms2gth/src/idl/modis_utils/interp_swath.pro,v 1.3 2004/10/23 17:42:01 haran Exp $
;*========================================================================*/

;+
; NAME:
;	interp_swath
;
; PURPOSE:
;       Expand a swath of data using interpolation.
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       INTERP_SWATH, interp_factor, colsin, scans, rowsperscanin,
;               filein, colsout, tag,
;               [, data_type=data_type]
;               [, scanfirst=scanfirst]
;               [, col_offset=col_offset]
;               [, row_offset=row_offset]
;               [, /nearest_neighbor]
;               [, mirror_side=mirror_side]
;
; ARGUMENTS:
;    Inputs:
;       interp_factor: interpolation factor by which the number of colums
;         and rows in the input files is to be expanded.
;       colsin: number of columns in the input file.
;       scans: number of scans to process in the input file.
;       rowsperscanin: number of rows constituting an input scan.
;       filein: file containing the channel data to be interpolated.
;    Outputs:
;       colsout: number of columns in each output file. Must be less than
;         or equal to colsin * interp_factor.
;       tag: string used to construct output filenames:
;         fileout = tag_mirror_colsout_scans_scanfirst_rowsperscanout.img
;             where
;               mirror - mirror side of first scan in each output file.
;               scansout - number of scans written to each output file.
;               rowsperscanout = interp_factor * rowsperscanin.
;           Each output file contains colsout * scans * rowsperscanout values.
;
; KEYWORDS:
;       data_type: 2-character string specifying the data type of the data
;         to be interpolated as follows:
;           u1: unsigned 8-bit integer.
;           u2: unsigned 16-bit integer.
;           s2: signed 16-bit integer.
;           u4: unsigned 32-bit integer.
;           s4: signed 32-bit integer.
;           f4: 32-bit floating-point (default).
;       scanfirst: the scan number of the first scan in filein to be
;         processed. The default is 0.
;       col_offset: the column number in the output grid to which the
;         first column in the input grid is to be mapped. The default is 0.
;       row_offset: the row number in the output grid to which the
;         first row in the input grid is to be mapped. The default is 0.
;       nearest_neighbor: if set, then nearest neighbor sampling is used.
;         Otherwise, bilinear interpolation (if rowsperscanin is less than
;         4) or cubic convolution (if rowsperscanin is greater than or equal
;         to 4) is used.
;       mirror_side: if 0 or 1, then indicates the mirror side of scan 0
;         in filein. If 2, then mirror side is undefined. The default is 2.
;
; EXAMPLE:
;         interp_swath, 5, 271, 330, 5, $
;                       'gl1_2000153_1445_raw_soze_00271_00812.img', $
;                        1354, 'gl1_2000153_1445_soze_raw', $
;                        data_type='u2', scanfirst=17, $
;                        col_offset=2, row_offset=2, mirror_side=1
;
; ALGORITHM:
;
; REFERENCE:
;-

forward_function congridx

Pro interp_swath, interp_factor, colsin, scans, rowsperscanin, $
                  filein, colsout, tag, $
                  data_type=data_type, $
                  scanfirst=scanfirst, $
                  col_offset=col_offset, row_offset=row_offset, $
                  nearest_neighbor=nearest_neighbor, $
                  mirror_side=mirror_side

  usage = 'usage: interp_swath, ' + $
                  'interp_factor, colsin, scans, rowsperscanin, ' + $
                  'filein, colsout, tag' + $
                  '[, data_type=data_type]' + $
                  '[, scanfirst=scanfirst]' + $
                  '[, col_offset=col_offset]' + $
                  '[, row_offset=row_offset]' + $
                  '[, nearest_neighbor=nearest_neighbor]' + $
                  '[, mirror_side=mirror_side]'

  if n_params() ne 7 then $
    message, usage

  if n_elements(data_type) eq 0 then $
    data_type = 'f4';
  if n_elements(scanfirst) eq 0 then $
    scanfirst = 0;
  if n_elements(col_offset) eq 0 then $
    col_offset = 0
  if n_elements(row_offset) eq 0 then $
    row_offset = 0
  if n_elements(nearest_neighbor) eq 0 then $
    nearest_neighbor = 0
  if n_elements(mirror_side) eq 0 then $
    mirror_side = 2

  print, 'interp_swath:'
  print, '  interp_factor:    ', interp_factor
  print, '  colsin:           ', colsin
  print, '  scans:            ', scans
  print, '  rowsperscanin:    ', rowsperscanin
  print, '  filein:           ', filein
  print, '  colsout:          ', colsout
  print, '  tag:              ', tag
  print, '  data_type:        ', data_type
  print, '  scanfirst:        ', scanfirst
  print, '  col_offset:       ', col_offset
  print, '  row_offset:       ', row_offset
  print, '  nearest_neighbor: ', nearest_neighbor
  print, '  mirror_side:      ', mirror_side

  if colsout gt colsin * interp_factor then $
    message, 'colsout must be less than or equal to colsin * interp_factor'

  ; allocate arrays

  case data_type of
      'u1': begin
          scan_of_swath_in = bytarr(colsin, rowsperscanin)
          bytes_per_element = 1
          min_out = 0.0
          max_out = 255.0
      end
      'u2': begin
          scan_of_swath_in = uintarr(colsin, rowsperscanin)
          bytes_per_element = 2
          min_out = 0.0
          max_out = 65535.0
      end
      's2': begin
          scan_of_swath_in = intarr(colsin, rowsperscanin)
          bytes_per_element = 2
          min_out = -32768.0
          max_out = 32767.0
      end
      'u4': begin
          scan_of_swath_in = ulonarr(colsin, rowsperscanin)
          bytes_per_element = 4
          min_out = 0.0
          max_out = 4294967295.0
      end
      's4': begin
          scan_of_swath_in = lontarr(colsin, rowsperscanin)
          bytes_per_element = 4
          min_out = -2147483648.0
          max_out = 2147483647.0
      end
      'f4': begin
          scan_of_swath_in = fltarr(colsin, rowsperscanin)
          bytes_per_element = 4
      end
      else: message, 'invalid data_type'
  end
  type_code = size(scan_of_swath_in, /type)

  ; open input file

  openr, lun_in, filein, /get_lun

  ;  Seek to the first scan we will process

  point_lun, lun_in, n_elements(scan_of_swath_in) * bytes_per_element * $
                     scanfirst

  ;  Create output file name.

  rowsperscanout = rowsperscanin * interp_factor
  mirror = mirror_side
  if mirror lt 2 then $
    mirror = (mirror + scanfirst) mod 2

  suffix = string(mirror, format='(I1.1)') + '_' + $
           string(colsout, format='(I5.5)') + '_' + $
           string(scans, format='(I5.5)') + '_' + $
           string(scanfirst, format='(I5.5)') + '_' + $
           string(rowsperscanout, format='(I2.2)') + '.img'
  fileout = tag + '_' + suffix

  ;  Open output files

  openw, lun_out, fileout, /get_lun

  ;  Process a scan's worth of data at a time

  for scan = 0, scans - 1 do begin

      if (scan mod 10) eq 0 then $
        print, 'scan:', scan

      ;  read in a scan's worth of data

      readu, lun_in, scan_of_swath_in

      if nearest_neighbor eq 0 then begin
          if rowsperscanin le 4 then begin
              scan_of_swath_out = congridx(float(scan_of_swath_in), $
                                           interp_factor, $
                                           colsout, rowsperscanout, $
                                           col_offset=col_offset, $
                                           row_offset=row_offset, $
                                           /interp)
          endif else begin
              scan_of_swath_out = congridx(float(scan_of_swath_in), $
                                           interp_factor, $
                                           colsout, rowsperscanout, $
                                           col_offset=col_offset, $
                                           row_offset=row_offset, $
                                           cubic=-0.5)
          endelse
      endif else begin
          scan_of_swath_out = congridx(float(scan_of_swath_in), $
                                       interp_factor, $
                                       colsout, rowsperscanout, $
                                       col_offset=col_offset, $
                                       row_offset=row_offset)
      endelse

      ;  convert back to original data type

      if data_type ne 'f4' then begin
          i = where(scan_of_swath_out lt min_out, count)
          if count gt 0 then $
            scan_of_swath_out[i] = min_out
          i = where(scan_of_swath_out gt max_out, count)
          if count gt 0 then $
            scan_of_swath_out[i] = max_out
          scan_of_swath_out = fix(round(temporary(scan_of_swath_out)), $
                                  type=type_code)
      endif
      
      ;  write out a scan's worth of data

      writeu, lun_out, scan_of_swath_out

  endfor

  DONE:

  ; close files

  free_lun, lun_in
  free_lun, lun_out

END ; interp_swath
