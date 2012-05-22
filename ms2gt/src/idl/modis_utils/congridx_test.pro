;*========================================================================
;* congridx_test.pro - test congridx
;*
;* 05-Apr-2004  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;* $Header: /data/tharan/ms2gth/src/idl/modis_utils/congridx_test.pro,v 1.1 2004/04/05 22:32:11 haran Exp $
;*========================================================================*/

pro congridx_test

cols_in = 7L
rows_in = 10L
n_in = cols_in * rows_in
a = reform(findgen(n_in), cols_in, rows_in)
a = a * a

openw, lun, 'a.txt', /get_lun
printf, lun, a
free_lun, lun

; test 250 meter

interp_factor = 4
cols_out = cols_in * interp_factor
rows_out = rows_in * interp_factor
col_offset = 0
row_offset = 1.5
q_nn = congridx(a, interp_factor, cols_out, rows_out, $
                col_offset=col_offset, row_offset=row_offset)
q_bl = congridx(a, interp_factor, cols_out, rows_out, $
                col_offset=col_offset, row_offset=row_offset, /interp)
qq_bl = modis_geo_interp_250(a)
q_cu = congridx(a, interp_factor, cols_out, rows_out, $
                col_offset=col_offset, row_offset=row_offset, cubic=-0.5)

openw, lun, 'q_nn.txt', /get_lun
printf, lun, q_nn
free_lun, lun

openw, lun, 'q_bl.txt', /get_lun
printf, lun, q_bl
free_lun, lun

openw, lun, 'qq_bl.txt', /get_lun
printf, lun, qq_bl
free_lun, lun

openw, lun, 'q_cu.txt', /get_lun
printf, lun, q_cu
free_lun, lun

; test 500 meter

interp_factor = 2
cols_out = cols_in * interp_factor
rows_out = rows_in * interp_factor
col_offset = 0
row_offset = 0.5
h_nn = congridx(a, interp_factor, cols_out, rows_out, $
                col_offset=col_offset, row_offset=row_offset)
h_bl = congridx(a, interp_factor, cols_out, rows_out, $
                col_offset=col_offset, row_offset=row_offset, /interp)
hh_bl = modis_geo_interp_500(a)
h_cu = congridx(a, interp_factor, cols_out, rows_out, $
                col_offset=col_offset, row_offset=row_offset, cubic=-0.5)

openw, lun, 'h_nn.txt', /get_lun
printf, lun, h_nn
free_lun, lun

openw, lun, 'h_bl.txt', /get_lun
printf, lun, h_bl
free_lun, lun

openw, lun, 'hh_bl.txt', /get_lun
printf, lun, hh_bl
free_lun, lun

openw, lun, 'h_cu.txt', /get_lun
printf, lun, h_cu
free_lun, lun

end ;congrix_test
