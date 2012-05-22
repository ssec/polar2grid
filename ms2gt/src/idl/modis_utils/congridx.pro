;*========================================================================
;* congridx.pro - expand a 2d array by extrapolation and interpolation
;*
;* 11-Jan-2001  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;* $Header: /data/tharan/ms2gth/src/idl/modis_utils/congridx.pro,v 1.5 2004/04/05 22:33:08 haran Exp $
;*========================================================================*/

;+
; NAME:
;	congridx
;
; PURPOSE:
;       Expand a n x m array by extrapolation to a (n+2) x (m+2) array,
;       followed by interpolation to a (N/n)(n+2) x (M/m)(m+2) array,
;       followed by extraction of the final N x M array.
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       result = CONGRIDX(array, interp_factor, cols_out, rows_out,
;                             [, col_offset=col_offset]
;                             [, row_offset=row_offset]
;                             [, cubic=value{-1 to 0}]
;                             [, /interp])
;
; ARGUMENTS:
;    Inputs:
;       array: a 2-dimensional floating-point array to expand.
;       interp_factor: interpolation factor by which array is to be expanded.
;       cols_out: number of columns returned from the expanded array.
;       rows_out: number of rows returned from the expanded array.
;    Outputs:
;       None.
;    Result:
;       A floating-point array consisting of cols_out columns and rows_out
;       rows is returned.
;
; KEYWORDS:
;    col_offset: the column number in the final array which will contain
;       the values from column 0 in the original array. The default is 0.
;       col_offset must be less than cols_out / cols_in.
;    row_offset: the row number in the final array which will contain
;       the values from row 0 in the original array. The default is 0.
;       row_offset must be less than rows_out / rows_in.
;    cubic, /interp, and /minus_one if present are passed to congrid,
;       if col_offset and row_offset are both integers or neither
;       cubic nor interp are present; otherwise cubic if present is
;       passed to interpolate.
;
; EXAMPLE:
;      scan_of_cols_out = congridx(scan_of_cols, interp_factor, $
;                                      cols_out, rows_out, $
;                                      col_offset=col_offset, $
;                                      row_offset=row_offset, $
;                                      cubic=0.5)
;
; ALGORITHM:
;
; REFERENCE:
;-

FUNCTION congridx, array, interp_factor, cols_out, rows_out, $
                   col_offset=col_offset, row_offset=row_offset, $
                   cubic=cubic, interp=interp, minus_one=minus_one
                   
usage = 'usage: result = CONGRIDX(array, interp_factor, ' + $
                                  'cols_out, rows_out, ' + $
                                  '[, col_offset=col_offset] ' + $
                                  '[, row_offset=row_offset] ' + $
                                  '[, cubic=value{-1 to 0}] ' + $
                                  '[, /interp] ' + $
                                  '[, /minus_one])'

  if n_params() ne 4 then $
    message, usage
  if n_elements(col_offset) eq 0 then $
    col_offset = 0
  if n_elements(row_offset) eq 0 then $
    row_offset = 0
  size_array = size(array)
  if size_array[0] ne 2 then $
    message, 'array must be 2-dimensional'
  cols_in = size_array[1]
  rows_in = size_array[2]
  if cols_in lt 2 then $
    message, 'array must have at least 2 columns'
  if rows_in lt 2 then $
    message, 'array must have at least 2 rows'
  if n_elements(interp) eq 0 then $
    interp = 0

  ; don't allow offsets >= interp_factor
  if abs(col_offset) ge interp_factor then $
    message, 'abs(col_offset) must be less than interp_factor'
  if abs(row_offset) ge interp_factor then $
    message, 'abs(row_offset) must be less than interp_factor'

  ; array_x will contain the extrapolated array

  col_offset_x = col_offset
  row_offset_x = row_offset
  cols_in_x = cols_in + 2
  rows_in_x = rows_in + 2
  array_x = fltarr(cols_in_x, rows_in_x)
  array_x[1:cols_in_x-2, 1:rows_in_x-2] = array

  if (interp eq 0) and (n_elements(cubic) eq 0) then begin

  ; **** use nearest neighbor extrapolation ****

  ; compute the first row
      array_x[1:cols_in_x-2, 0] = $
        array_x[1:cols_in_x-2, 1]
      
  ; compute the last row
      array_x[1:cols_in_x-2, rows_in_x-1] = $
      array_x[1:cols_in_x-2, rows_in_x-2]

  ; compute the first column
      array_x[0, 1:rows_in_x-2] = $
        array_x[1, 1:rows_in_x-2]
      
  ; compute the last column
      array_x[cols_in_x-1, 1:rows_in_x-2] = $
        array_x[cols_in_x-2, 1:rows_in_x-2]

  ; compute the upper left cell
      array_x[0, 0] = array_x[1, 1]

  ; compute the upper right cell
      array_x[cols_in_x-1, 0] = array_x[cols_in_x-2, 1]

  ; compute the lower left cell
      array_x[0, rows_in_x-1] = array_x[1, rows_in_x-2]

  ; compute the lower right cell
      array_x[cols_in_x-1, rows_in_x-1] = array_x[cols_in_x-2, rows_in_x-2]

  ; find nearest integer col_offset_x and row_offset_x
      col_offset_x = round(col_offset_x)
      row_offset_x = round(row_offset_x)

  endif else begin

  ; **** use linear extrapolation ****

  ; array_x will contain the extrapolated array

      cols_in_x = cols_in + 2
      rows_in_x = rows_in + 2
      array_x = fltarr(cols_in_x, rows_in_x)
      array_x[1:cols_in_x-2, 1:rows_in_x-2] = array

  ; compute the first row
      array_x[1:cols_in_x-2, 0] = $
        array_x[1:cols_in_x-2, 1] * 2 - $
        array_x[1:cols_in_x-2, 2]
      
  ; compute the last row
      array_x[1:cols_in_x-2, rows_in_x-1] = $
        array_x[1:cols_in_x-2, rows_in_x-2] * 2 - $
        array_x[1:cols_in_x-2, rows_in_x-3]

  ; compute the first column
      array_x[0, 1:rows_in_x-2] = $
        array_x[1, 1:rows_in_x-2] * 2 - $
        array_x[2, 1:rows_in_x-2]
      
  ; compute the last column
      array_x[cols_in_x-1, 1:rows_in_x-2] = $
        array_x[cols_in_x-2, 1:rows_in_x-2] * 2 - $
        array_x[cols_in_x-3, 1:rows_in_x-2]

  ; compute the upper left cell
      array_x[0, 0] = $
        ((array_x[1, 0] * 2 - array_x[2, 0]) + $
         (array_x[0, 1] * 2 - array_x[0, 2])) / 2

  ; compute the upper right cell
      array_x[cols_in_x-1, 0] = $
        ((array_x[cols_in_x-2, 0] * 2 - $
          array_x[cols_in_x-3, 0]) + $
         (array_x[cols_in_x-1, 1] * 2 - $
          array_x[cols_in_x-1, 2])) / 2

  ; compute the lower left cell
      array_x[0, rows_in_x-1] = $
        ((array_x[1, rows_in_x-1] * 2 - $
          array_x[2, rows_in_x-1]) + $
         (array_x[0, rows_in_x-2] * 2 - $
      array_x[0, rows_in_x-3])) / 2

  ; compute the lower right cell
      array_x[cols_in_x-1, rows_in_x-1] = $
        ((array_x[cols_in_x-2, rows_in_x-1] * 2 - $
          array_x[cols_in_x-3, rows_in_x-1]) + $
         (array_x[cols_in_x-1, rows_in_x-2] * 2 - $
          array_x[cols_in_x-1, rows_in_x-3])) / 2
  endelse

  ; array_x will be replaced by the interpolated array
  cols_out_x = fix(interp_factor * cols_in_x)
  rows_out_x = fix(interp_factor * rows_in_x)

  ; if col_offset_x and row_offset_x are both integers,
  ; then we will call congrid

  if (col_offset_x eq fix(col_offset_x)) and $
     (row_offset_x eq fix(row_offset_x)) then begin

      array_x = congrid(array_x, cols_out_x, rows_out_x, $
                        cubic=cubic, interp=interp, minus_one=minus_one)

      ; return the portion of array_x specified by cols_out, rows_out,
      ; col_offset_x, and row_offset_x
      col_first_out = fix(interp_factor) - col_offset_x
      row_first_out = fix(interp_factor) - row_offset_x
      col_last_out = col_first_out + cols_out - 1
      row_last_out = row_first_out + rows_out - 1
  endif else begin

      ; col_offset_x and/or row_offset_x is not an integer,
      ; so setup index arrays before calling interpolate

      cols = (findgen(cols_out_x) - col_offset_x) / interp_factor + 1
      rows = (findgen(rows_out_x) - row_offset_x) / interp_factor + 1
      array_x = interpolate(array_x, cols, rows, /grid, cubic=cubic)

      ; return the portion of array_x specified by cols_out, rows_out
      col_first_out = 0
      row_first_out = 0
      col_last_out = cols_out - 1
      row_last_out = rows_out - 1
  endelse
  return, array_x[col_first_out:col_last_out, row_first_out:row_last_out]
END ; congridx
