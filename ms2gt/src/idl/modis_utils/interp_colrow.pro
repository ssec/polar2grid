;*========================================================================
;* interp_colrow.pro - interpolate column and row files
;*
;* 10-Jan-2001  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /export/data/ms2gth/src/idl/modis_utils/interp_colrow.pro,v 1.4 2001/01/24 17:50:27 haran Exp $
;*========================================================================*/

;+
; NAME:
;	interp_colrow
;
; PURPOSE:
;       Expand a grid of column and row numbers using interpolation.
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       INTERP_COLROW, interp_factor, colsin, scansin, rowsperscanin,
;               colfilein, rowfilein, colsout, tag,
;               [, grid_check=[col_min, col_max, row_min, row_max]]
;               [, col_offset=col_offset]
;               [, row_offset=row_offset]
;
; ARGUMENTS:
;    Inputs:
;       interp_factor: interpolation factor by which the number of colums
;         and rows in the input files is to be expanded.
;       colsin: number of columns in each input file.
;       scansin: number of scans in each input file.
;       rowsperscanin: number of rows constituting an input scan.
;       colfilein: file containing the projected column number of each
;         cell and consisting of cols x scans x rowsperscanin of 4 byte
;         floating-point numbers. 
;       rowfilein: file containing the projected row number of each
;         cell and consisting of cols x rows x rowsperscanin of 4 byte
;         floating-point numbers. 
;    Outputs:
;       colsout: number of columns in each output file. Must be less than
;         or equal to colsin * interp_factor.
;       tag: string used to construct output filenames:
;         colfileout = tag_cols_colsout_scansout_scanfirst_rowsperscanout.img
;         rowfileout = tag_rows_colsout_scansout_scanfirst_rowsperscanout.img
;             where
;               scansout - number of scans written to each output file.
;               scanfirst - scan number of first scan written.
;               rowsperscanout = interp_factor * rowsperscanin.
;           Each output file contains colsout * scansout * rowsperscanout
;           4 byte floating-point numbers:
;             colfileout - grid of 4 byte floating-point column numbers.
;             rowfileout - grid of 4 byte floating-point row numbers.
;
; KEYWORDS:
;       grid_check: 4 element integer array containing the minimum and
;         maximum column and row numbers constituting the projected grid.
;         The 4 elements are as follows:
;           col_min - minimum column number.
;           col_max - maximum column nubmer.
;           row_min - minimum row number.
;           row_max - maximum row number.
;         If grid_check is not specified, then each input scan will produce
;         one expanded output scan. In this case:
;           scansout = scansin
;           scanfirst = 0
;         If grid_check is specified, then each output scan is checked
;         to see if it contains at least one point in the given range. The
;         scanfirst value is set to the scan number of the first scan for
;         which this is true, scansout is set to the number of scans
;         for which this is true, and only those scans are written to the
;         output files.
;       col_offset: the column number in the output grid to which the
;         first column in the input grid is to be mapped. The default is 0.
;       row_offset: the row number in the output grid to which the
;         first column in the input grid is to be mapped. The default is 0.
;
; EXAMPLE:
;         interp_colrow, 4, 1354, 203, 10, $
;                        'neross250_2000334_cols_01354_00203_00000_10.img', $
;                        'neross250_2000334_rows_01354_00203_00000_10.img', $
;                        5416, 'neross250_2000334', $
;                        grid_check=[0, 3599, 0, 2999]
;
; ALGORITHM:
;
; REFERENCE:
;-

forward_function congridx

Pro interp_colrow, interp_factor, colsin, scansin, rowsperscanin, $
                   colfilein, rowfilein, colsout, tag, $
                   grid_check=grid_check, $
                   col_offset=col_offset, row_offset=row_offset

  usage = 'usage: interp_colrow, ' + $
                  'interp_factor, colsin, scansin, rowsperscanin, ' + $
                  'colfilein, rowfilein, colsout, tag' + $
                  '[, grid_check=[col_min, col_max, row_min, row_max]]' + $
                  '[, col_offset=col_offset]' + $
                  '[, row_offset=row_offset]'

  if n_params() ne 8 then $
    message, usage
  if n_elements(grid_check) ne 4 then begin
      grid_check = 0
      check_grid = 0
  endif else begin
      check_grid = 1
      col_min = grid_check[0]
      col_max = grid_check[1]
      row_min = grid_check[2]
      row_max = grid_check[3]
  endelse
    
  if n_elements(col_offset) eq 0 then $
    col_offset = 0
  if n_elements(row_offset) eq 0 then $
    row_offset = 0

  print, 'interp_colrow:'
  print, '  interp_factor: ', interp_factor
  print, '  colsin:        ', colsin
  print, '  scansin:       ', scansin
  print, '  rowsperscanin: ', rowsperscanin
  print, '  colfilein:     ', colfilein
  print, '  rowfilein:     ', rowfilein
  print, '  colsout:       ', colsout
  print, '  tag:           ', tag
  print, '  grid_check:    ', grid_check
  print, '  col_offset:    ', col_offset
  print, '  row_offset:    ', row_offset

  if colsout gt colsin * interp_factor then $
    message, 'colsout must be less than or equal to colsin * interp_factor'

  ; allocate arrays

  scan_of_cols_in = fltarr(colsin, rowsperscanin)
  scan_of_rows_in = fltarr(colsin, rowsperscanin)

  ; open input files

  openr, col_lun_in, colfilein, /get_lun
  openr, row_lun_in, rowfilein, /get_lun

  ;  Create preliminary names of output files as if check_grid is FALSE.
  ;  If check_grid is FALSE, then these will be the final names.
  ;  If check_grid is TRUE, then we will rename the output files once
  ;  we're done and we know the final values of scansout and scanfirst.

  scansout = scansin
  scanfirst = 0
  rowsperscanout = rowsperscanin * interp_factor

  suffix = string(colsout, format='(I5.5)') + '_' + $
           string(scansout, format='(I5.5)') + '_' + $
           string(scanfirst, format='(I5.5)') + '_' + $
           string(rowsperscanout, format='(I2.2)') + '.img'
  colfileout = tag + '_cols_' + suffix
  rowfileout = tag + '_rows_' + suffix

  ;  Open output files

  openw, col_lun_out, colfileout, /get_lun
  openw, row_lun_out, rowfileout, /get_lun

  ;  set scanfirst to -1 to indicate we haven't found a point within
  ;  the grid yet.

  if check_grid eq 1 then begin
      scanfirst = -1
      scanlast  = -2
  endif
  for scan = 0, scansin - 1 do begin

      if (scan mod 10) eq 0 then $
        print, 'scan:', scan
      ;  read in a scan's worth of data

      readu, col_lun_in, scan_of_cols_in
      readu, row_lun_in, scan_of_rows_in

      if rowsperscanin le 4 then begin
          scan_of_cols_out = congridx(scan_of_cols_in, interp_factor, $
                                      colsout, rowsperscanout, $
                                      col_offset=col_offset, $
                                      row_offset=row_offset, $
                                      /interp)
          scan_of_rows_out = congridx(scan_of_rows_in, interp_factor, $
                                      colsout, rowsperscanout, $
                                      col_offset=col_offset, $
                                      row_offset=row_offset, $
                                      /interp)
      endif else begin
          scan_of_cols_out = congridx(scan_of_cols_in, interp_factor, $
                                      colsout, rowsperscanout, $
                                      col_offset=col_offset, $
                                      row_offset=row_offset, $
                                      cubic=-0.5)
          scan_of_rows_out = congridx(scan_of_rows_in, interp_factor, $
                                      colsout, rowsperscanout, $
                                      col_offset=col_offset, $
                                      row_offset=row_offset, $
                                      cubic=-0.5)
      endelse

      if check_grid eq 1 then begin
          i = where((scan_of_cols_out ge col_min) and $
                    (scan_of_cols_out le col_max) and $
                    (scan_of_rows_out ge row_min) and $
                    (scan_of_rows_out le row_max), count)
          if count gt 0 then begin
              scanlast = scan
              if scanfirst lt 0 then $
                scanfirst = scan
          endif
      endif else begin
          scanlast = scan
      endelse

      if (check_grid eq 1) and (scanfirst ge 0) and (scanlast ne scan) then $
        goto, DONE
      if scanfirst ge 0 then begin

          ;  write out a scan's worth of data

          writeu, col_lun_out, scan_of_cols_out
          writeu, row_lun_out, scan_of_rows_out
      endif

  endfor

  DONE:

  ; close files

  free_lun, col_lun_in
  free_lun, row_lun_in
  free_lun, col_lun_out
  free_lun, row_lun_out

  ;  rename the output files if check grid is true

  if check_grid eq 1 then begin
      if scanfirst lt 0 then begin
          scansout = 0
          scanfirst = 0
      endif else begin
          scansout = scanlast - scanfirst + 1
      endelse
      suffix = string(colsout, format='(I5.5)') + '_' + $
               string(scansout, format='(I5.5)') + '_' + $
               string(scanfirst, format='(I5.5)') + '_' + $
               string(rowsperscanout, format='(I2.2)') + '.img'
      colfileout_new = tag + '_cols_' + suffix
      rowfileout_new = tag + '_rows_' + suffix
      spawn, 'mv ' + colfileout + ' ' + colfileout_new, /sh
      spawn, 'mv ' + rowfileout + ' ' + rowfileout_new, /sh
  endif

END ; interp_colrow
