;*========================================================================
;* modis_adjust.pro - adjust modis data based on solar zenith and/or
;*                    regressions
;*
;* 15-Apr-2002  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /data/tharan/ms2gth/src/idl/modis_utils/modis_adjust.pro,v 1.54 2005/01/11 22:23:46 haran Exp $
;*========================================================================*/

;+
; NAME:
;	modis_adjust
;
; PURPOSE:
;       1) Optionally modify modis data with a solar zenith correction.
;       2) Optionally compute a regression for every reg_col_stride column
;          relative to the mean of the preceding and following columns
;          for a particular set of detectors at a given column offset.
;       3) Optionally normalize the mean of each detector relative to
;          the overall mean.
;       4) Optionally compute a regression for each pair of detectors
;          relative to their mean, then regress each pair of means
;          against its mean, and so on until only one mean is left,
;          and then adjust the data accordingly.
;       5) Optionally undo the solar zenith correction.
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       MODIS_ADJUST, cols, scans, file_in, file_out,
;               [, rows_per_scan=rows_per_scan]
;               [, data_type_in=data_type_in]
;               [, data_type_out=data_type_out]
;               [, file_soze=file_soze]
;               [, /undo_soze]
;               [, /interp_cols]
;               [, /reg_cols]
;               [, file_reg_cols_in=file_reg_cols_in]
;               [, file_reg_cols_out=file_reg_cols_out]
;               [, reg_col_detectors=reg_col_detectors]
;               [, reg_col_stride=reg_col_stride]
;               [, reg_col_offset=reg_col_offset]
;               [, col_y_tolerance=col_y_tolerance]
;               [, col_slope_delta_max=col_slope_delta_max]
;               [, col_regression_max=col_regression_max]
;               [, col_density_bin_width=col_density_bin_width]
;               [, col_plot_tag=col_plot_tag]
;               [, col_plot_max=col_plot_max]
;               [, /nor_rows]
;               [, /reg_rows]
;               [, file_reg_rows_in=file_reg_rows_in]
;               [, file_reg_rows_out=file_reg_rows_out]
;               [, reg_row_mirror_side=reg_row_mirror_side]
;               [, row_y_tolerance=row_y_tolerance]
;               [, row_slope_delta_max=row_slope_delta_max]
;               [, row_regression_max=row_regression_max]
;               [, row_density_bin_width=row_density_bin_width]
;               [, row_plot_tag=row_plot_tag]
;               [, row_plot_max=row_plot_max]
;
; ARGUMENTS:
;    Inputs:
;       cols: number of columns in the input file.
;       scans: number of scans to process in the input file.
;       file_in: file containing the channel data to be adjusted.
;    Outputs:
;       file_out: file containing adjusted channel data.
;
; KEYWORDS:
;       rows_per_scan: number of rows in each scan in file_in. Valid
;         values are limited to 40 (the default), 20, or 10.
;       data_type_in: 2-character string specifying the data type of the
;         input file.
;       data_type_out: 2-character string specifying the data type of the
;         output file.
;       NOTE: the following 2-character codes are used for both
;         data_type_in and data_type_out:
;           u1: unsigned 8-bit integer.
;           u2: unsigned 16-bit integer.
;           s2: signed 16-bit integer.
;           u4: unsigned 32-bit integer.
;           s4: signed 32-bit integer.
;           f4: 32-bit floating-point (default).
;       file_soze: file containing solar zenith values in 16-bit signed
;         integer format representing decimal degrees times 100.
;         Should have the same number of cols and scans as file_in.
;         Each input value is divided by the cosine of the corresponding
;         solar zenith value before any regressions are performed. The default
;         value of file_soze is a null string indicating that no solar zenith
;         file should be read.
;       undo_soze: If set then each input value is multiplied by the cosine
;         of the corresponding solar zenith value after regressions are
;         performed. If file_soze is a null string, then undo_soze is
;         ignored.
;       interp_cols: If set then column interpolations are performed.
;       reg_cols: If set then column regressions are computed.
;       NOTE: interp_cols and reg_cols may not both be set, i.e. they
;             are mutually exclusive.
;       file_reg_col_in: Specifies the name of an input text file
;         containing an initial set of intercepts and slopes that are
;         applied to the data before any column regressions (if any) are
;         computed. The file must have rows_per_scan + 1 lines.
;         The file has the following format:
;           SS_Detector  Col_Intercept     Col_Slope
;           00            0.00000000E+00    1.00000000E+00
;           01            0.00000000E+00    1.00000000E+00
;           .                   .                 .
;           39            0.00000000E+00    1.00000000E+00
;       NOTE: interp_cols and file_reg_col_in may not both be set, i.e.
;             they are mutually exclusive.
;       file_reg_col_out: Specifies the name of an output text file
;         containing the final set of intercepts and slopes for column
;         regressions. The file has the same format as for file_reg_col_out.
;       reg_col_detectors: Array of zero-based detector numbers to use for
;         column regressions and/or interpolations. The default value of
;         reg_col_detectors is [27,28,29].
;       reg_col_stride: the stride value to use for performing column
;         regressions and/or interpolations. The default value of
;         reg_col_stride is 4.
;         NOTE: reg_col_stride must divide evenly into cols.
;       reg_col_offset: the offset value to use for performing column
;         regressions and/or interpolations. The default value of
;         reg_col_offset is 0.
;         NOTE: reg_col_offset must be less than reg_col_stride.
;       nor_rows: If set then row normalization is performed.
;       reg_rows: If set then row regressions are computed.
;       file_reg_row_in: Specifies the name of an input text file
;         containing an initial set of intercepts and slopes that are
;         applied to the data before any row normalization or row
;         regressions (if any) are computed.
;         The file must have 2 * rows_per_scan + 1 lines.
;         The file has the following format:
;           DS_Detector  Row_Intercept     Row_Slope
;           00            0.00000000E+00    1.00000000E+00
;           01            0.00000000E+00    1.00000000E+00
;           .                   .                 .
;           79            0.00000000E+00    1.00000000E+00
;       file_reg_row_out: Specifies the name of an output text file
;         containing the final set of intercepts and slopes for row
;         regressions. The file has the same format as for
;         file_reg_row_out.
;       reg_row_mirror_side: Specifies the mirror side for the first
;         scan in file_in. Valid values are 0 (the default) or 1.
;       NOTE: The keywords below are preceded by either col_ or row_
;         indicating to which set of regressions they refer.
;       y_tolerance: the value to use after the first linear regression
;         has been performed to find "outliers" that will be eliminated
;         from the second linear regression. That is, after k and m have
;         been determined from the first linear regression, the values
;         y'(i) = k + m * x(i) are calculated. Then outliers are defined
;         to be all points x(i) for which
;         abs((y'(i) - y(i)) / (ymax - ymin)) >= y_tolerance.
;         Then a second regression is performed on the remaining x(i) after
;         the outliers have been removed to determine the final k and m
;         values. The default value of y_tolerance is 0.01.
;         NOTE: If y_tolerance is 0.0, then no second linear regression
;               is performed.
;         NOTE: If row_y_tolerance is a vector, then each element of
;               row_y_tolerance specifies the value to use for the
;               corresponding pass.
;       slope_delta_max: the outlier detection procedure described for
;         y_tolerance is repeated until slope_delta =
;         abs(slope - slope_old) / slope_old is less than or equal to
;         slope_delta_max. The default value of slope_delta_max is 0.0001.
;         NOTE: If slope_delta_max is 0.0, then no third linear regression
;               or higher is performed.
;       regression_max: the outlier detection procedure is repeated a maximum
;         of regression max total number of regressions.
;         The default value of regression_max is 100.
;       density_bin_width: the bin width used to create a weight map based on
;         the density of the scatterplot. If density_bin_width is 0 (default)
;         then all weights are set to 1 for the regressions.
;       plot_tag: string used to name and label regression plot files.
;         Row plot files will be labelled row_plot_tag_p_rr.ps where p is a
;         zero-based pass index and rr is a zero-based regression index
;         within the pass.
;         The default value of plot_tag is a null string indicating
;         that no plots should be created.
;       plot_max: maximum values to plot. If plot_max is 0, then the maximum
;         values in the data are used. The default value is 1.5. If
;         plot_tag is a null string, then plot_max is ignored.
;
; EXAMPLE:
;       #!/sbin/csh
;      
;       mkdir plots
;       
;       mod02.pl . inst 2001341.txt institute250.gpd chan.txt \
;                ancil.txt 3 3 1
;       
;       ############################### ch01
;       
;       idl_sh.pl modis_adjust 5416 53 \
;         "'inst_ref_ch01_5416_02120.img'" \
;         "'inst_ref_ch01_5416_02120_adj0.img'" \
;         "file_soze='inst_soze_rawa_05416_00053_00000_40.img'" \
;         "/reg_cols" \
;         "reg_col_offset=3" \
;         "file_reg_cols_out='inst_ch01_col_adj0.txt'" \
;         "col_plot_tag='plots/inst_ch01_col_adj0'" \
;         "reg_row_mirror_side=0" \
;         "/nor_rows" \
;         "/reg_rows" \
;         "file_reg_rows_out='inst_ch01_row_adj0.txt'" \
;         "row_plot_tag='plots/inst_ch01_row_adj0'"
;       
;       fornav 1 -v -t f4 -f 65535 -F 0 5416 53 40 \
;         inst_cols_05416_00053_00065_40.img \
;         inst_rows_05416_00053_00065_40.img \
;         inst_ref_ch01_5416_02120_adj0.img \
;         1820 1743 \
;         inst_refa_ch01_03033_02905_adj0.img
;       
;       ############################### ch02
;       
;       idl_sh.pl modis_adjust 5416 53 \
;         "'inst_ref_ch02_5416_02120.img'" \
;         "'inst_ref_ch02_5416_02120_adj0.img'" \
;         "file_soze='inst_soze_rawa_05416_00053_00000_40.img'" \
;         "/reg_cols" \
;         "reg_col_offset=0" \
;         "file_reg_cols_out='inst_ch02_col_adj0.txt'" \
;         "col_plot_tag='plots/inst_ch02_col_adj0'" \
;         "reg_row_mirror_side=0" \
;         "/nor_rows" \
;         "/reg_rows" \
;         "file_reg_rows_out='inst_ch02_row_adj0.txt'" \
;         "row_plot_tag='plots/inst_ch02_row_adj0'"
;       
;       fornav 1 -v -t f4 -f 65535 -F 0 5416 53 40 \
;         inst_cols_05416_00053_00065_40.img \
;         inst_rows_05416_00053_00065_40.img \
;         inst_ref_ch02_5416_02120_adj0.img \
;         1820 1743 \
;         inst_refa_ch02_03033_02905_adj0.img
;       
; ALGORITHM:
;
; REFERENCE:
;-

Pro modis_adjust, cols, scans, file_in, file_out, $
                  rows_per_scan=rows_per_scan, $
                  data_type_in=data_type_in, $
                  data_type_out=data_type_out, $
                  file_soze=file_soze, $
                  undo_soze=undo_soze, $
                  interp_cols=interp_cols, $
                  reg_cols=reg_cols, $
                  file_reg_cols_in=file_reg_cols_in, $
                  file_reg_cols_out=file_reg_cols_out, $
                  reg_col_detectors=reg_col_detectors, $
                  reg_col_stride=reg_col_stride, $
                  reg_col_offset=reg_col_offset, $
                  col_y_tolerance=col_y_tolerance, $
                  col_slope_delta_max=col_slope_delta_max, $
                  col_regression_max=col_regression_max, $
                  col_density_bin_width=col_density_bin_width, $
                  col_plot_tag=col_plot_tag, $
                  col_plot_max=col_plot_max, $
                  nor_rows=nor_rows, $
                  reg_rows=reg_rows, $
                  file_reg_rows_in=file_reg_rows_in, $
                  file_reg_rows_out=file_reg_rows_out, $
                  reg_row_mirror_side=reg_row_mirror_side, $
                  row_y_tolerance=row_y_tolerance, $
                  row_slope_delta_max=row_slope_delta_max, $
                  row_regression_max=row_regression_max, $
                  row_density_bin_width=row_density_bin_width, $
                  row_plot_tag=row_plot_tag, $
                  row_plot_max=row_plot_max

  epsilon = 1e-6

  lf = string(10B)

  usage = lf + 'usage: modis_adjust, ' + lf + $
                'cols, scans, file_in, file_out, ' + lf + $
                '[, rows_per_scan=rows_per_scan] ' + lf + $
                '[, data_type_in=data_type_in] ' +   lf + $
                '[, data_type_out=data_type_out] ' +   lf + $
                '[, file_soze=file_soze] ' + lf + $
                '[, /undo_soze] ' + lf + $
                '[, /interp_cols] ' + lf + $
                '[, /reg_cols] ' + lf + $
                '[, file_reg_cols_in=file_reg_cols_in] ' + lf + $
                '[, file_reg_cols_out=file_reg_cols_out] ' + lf + $
                '[, reg_col_detectors=reg_col_detectors] ' + lf + $
                '[, reg_col_stride=reg_col_stride] ' + lf + $
                '[, reg_col_offset=reg_col_offset] ' + lf + $
                '[, col_y_tolerance=col_y_tolerance] ' + lf + $
                '[, col_slope_delta_max=col_slope_delta_max] ' + lf + $
                '[, col_regression_max=col_regression_max] ' + lf + $
                '[, col_density_bin_width=col_density_bin_width] ' + lf + $
                '[, col_plot_tag=col_plot_tag] ' + lf + $
                '[, col_plot_max=col_plot_max] ' + lf + $
                '[, /nor_rows] ' + lf + $
                '[, /reg_rows] ' + lf + $
                '[, file_reg_rows_in=file_reg_rows_in] ' + lf + $
                '[, file_reg_rows_out=file_reg_rows_out] ' + lf + $
                '[, reg_row_mirror_side=reg_row_mirror_side]' + lf + $
                '[, row_y_tolerance=row_y_tolerance] ' + lf + $
                '[, row_slope_delta_max=row_slope_delta_max] ' + lf + $
                '[, row_regression_max=row_regression_max] ' + lf + $
                '[, row_density_bin_width=row_density_bin_width] ' + lf + $
                '[, row_plot_tag=row_plot_tag] ' + lf + $
                '[, row_plot_max=row_plot_max]'

  if n_params() ne 4 then $
    message, usage

  if n_elements(rows_per_scan) eq 0 then $
    rows_per_scan = 40
  if n_elements(data_type_in) eq 0 then $
    data_type_in = 'f4'
  if n_elements(data_type_out) eq 0 then $
    data_type_out = 'f4'
  if n_elements(file_soze) eq 0 then $
    file_soze = ''
  if n_elements(undo_soze) eq 0 then $
    undo_soze = 0
  if n_elements(interp_cols) eq 0 then $
    interp_cols = 0
  if n_elements(reg_cols) eq 0 then $
    reg_cols = 0
  if n_elements(file_reg_cols_in) eq 0 then $
    file_reg_cols_in = ''
  if n_elements(file_reg_cols_out) eq 0 then $
    file_reg_cols_out = ''
  if n_elements(reg_col_detectors) eq 0 then $
    reg_col_detectors = [27,28,29]
  if n_elements(reg_col_stride) eq 0 then $
    reg_col_stride = 4
  if n_elements(reg_col_offset) eq 0 then $
    reg_col_offset = 0
  if n_elements(col_y_tolerance) eq 0 then $
    col_y_tolerance = 0.01
  if n_elements(col_slope_delta_max) eq 0 then $
    col_slope_delta_max = 0.0001
  if n_elements(col_regression_max) eq 0 then $
    col_regression_max = 100
  if n_elements(col_density_bin_width) eq 0 then $
    col_density_bin_width = 0
  if n_elements(col_plot_tag) eq 0 then $
    col_plot_tag = ''
  if n_elements(col_plot_max) eq 0 then $
    col_plot_max = 1.5
  if n_elements(nor_rows) eq 0 then $
    nor_rows = 0
  if n_elements(reg_rows) eq 0 then $
    reg_rows = 0
  if n_elements(file_reg_rows_in) eq 0 then $
    file_reg_rows_in = ''
  if n_elements(file_reg_rows_out) eq 0 then $
    file_reg_rows_out = ''
  if n_elements(reg_row_mirror_side) eq 0 then $
    reg_row_mirror_side = 0
  if n_elements(row_y_tolerance) eq 0 then $
    row_y_tolerance = 0.01
  if n_elements(row_slope_delta_max) eq 0 then $
    row_slope_delta_max = 0.0001
  if n_elements(row_regression_max) eq 0 then $
    row_regression_max = 100
  if n_elements(row_density_bin_width) eq 0 then $
    row_density_bin_width = 0
  if n_elements(row_plot_tag) eq 0 then $
    row_plot_tag = ''
  if n_elements(row_plot_max) eq 0 then $
    row_plot_max = 1.5

  if reg_cols eq 0 then $
    col_plot_tag = ''
  if reg_rows eq 0 then $
    row_plot_tag = ''

  reg_col_detectors_count = n_elements(reg_col_detectors)
  row_y_tolerance_count   = n_elements(row_y_tolerance)

  time_start = systime(/seconds)

  print, 'modis_adjust: $Header: /data/tharan/ms2gth/src/idl/modis_utils/modis_adjust.pro,v 1.54 2005/01/11 22:23:46 haran Exp $'
  print, '  started:              ', systime(0, time_start)
  print, '  cols:                 ', cols
  print, '  scans:                ', scans
  print, '  file_in:              ', file_in
  print, '  file_out:             ', file_out
  print, '  rows_per_scan:        ', rows_per_scan
  print, '  data_type_in:         ', data_type_in
  print, '  data_type_out:        ', data_type_out
  print, '  file_soze:            ', file_soze
  print, '  undo_soze:            ', undo_soze
  print, '  interp_cols:          ', interp_cols
  print, '  reg_cols:             ', reg_cols
  print, '  file_reg_cols_in:     ', file_reg_cols_in
  print, '  file_reg_cols_out:    ', file_reg_cols_out
  for i = 0, reg_col_detectors_count - 1 do begin
      s = string(i, format='(i1)')
      print, '  reg_col_detectors[' + s + ']: ', reg_col_detectors[i]
  endfor
  print, '  reg_col_stride:       ', reg_col_stride
  print, '  reg_col_offset:       ', reg_col_offset
  print, '  col_y_tolerance:      ', col_y_tolerance
  print, '  col_slope_delta_max:  ', col_slope_delta_max
  print, '  col_regression_max:   ', col_regression_max
  print, '  col_density_bin_width:', col_density_bin_width
  print, '  col_plot_tag:         ', col_plot_tag
  print, '  col_plot_max:         ', col_plot_max
  print, '  nor_rows:             ', nor_rows
  print, '  reg_rows:             ', reg_rows
  print, '  file_reg_rows_in:     ', file_reg_rows_in
  print, '  file_reg_rows_out:    ', file_reg_rows_out
  print, '  reg_row_mirror_side:  ', reg_row_mirror_side
  for i = 0, row_y_tolerance_count - 1 do begin
      s = string(i, format='(i1)')
      print, '  row_y_tolerance[' + s + ']:   ', row_y_tolerance[i]
  endfor
  print, '  row_slope_delta_max:  ', row_slope_delta_max
  print, '  row_regression_max:   ', row_regression_max
  print, '  row_density_bin_width:', row_density_bin_width
  print, '  row_plot_tag:         ', row_plot_tag
  print, '  row_plot_max:         ', row_plot_max

  ; check for valid input

  if scans lt 2 then $
    message, 'scans must be 2 or greater'

  if (rows_per_scan ne 40) and $
     (rows_per_scan ne 20) and $
     (rows_per_scan ne 10) then $
    message, 'rows_per_scan must be 40, 20, or 10'

  for i = 0, reg_col_detectors_count - 1 do begin
      if reg_col_detectors[i] lt 0 then $
        message, 'Each element of reg_col_detector ' + $
                 'must be greater than or equal to 0'
      if reg_col_detectors[i] ge rows_per_scan then $
        message, 'Each element of reg_col_detector ' + $
                 'must be less than rows_per_scan'
  endfor

  if (cols mod reg_col_stride) ne 0 then $
    message, 'reg_col_stride must divide evenly into cols'

  if reg_col_offset gt reg_col_stride then $
    message, 'reg_col_offset must be less than reg_col_stride'

  if (reg_row_mirror_side ne 0) and (reg_row_mirror_side ne 1) then $
    message, 'reg_row_mirror_side must be 0 or 1'

  if (interp_cols ne 0) and (reg_cols ne 0) then $
    message, 'interp_cols and reg_cols may not both be set'

  if (interp_cols ne 0) and (file_reg_cols_in ne '') then $
    message, 'interp_cols and file_reg_cols_in may not both be specified'

  ; calculate the number of cells in the entire swath

  rows = scans * rows_per_scan
  cells_per_scan = long(cols) * rows_per_scan
  cells_per_swath = cells_per_scan * scans

  ; allocate arrays

  case data_type_in of
      'u1': begin
          swath = bytarr(cells_per_swath)
          min_in = 0.0
          max_in = 255.0
      end
      'u2': begin
          swath = uintarr(cells_per_swath)
          min_in = 0.0
          max_in = 65535.0
      end
      's2': begin
          swath = intarr(cells_per_swath)
          min_in = -32768.0
          max_in = 32767.0
      end
      'u4': begin
          swath = ulonarr(cells_per_swath)
          min_in = 0.0
          max_in = 4294967295.0
      end
      's4': begin
          swath = lonarr(cells_per_swath)
          min_in = -2147483648.0
          max_in = 2147483647.0
      end
      'f4': begin
          swath = fltarr(cells_per_swath)
          min_in = -32768.0
          max_in = 32767.0
      end
      else: message, 'invalid data_type_in' + usage
  end

  case data_type_out of
      'u1': begin
          test_out = bytarr(cells_per_swath)
          min_out = 0.0
          max_out = 255.0
      end
      'u2': begin
          test_out = uintarr(cells_per_swath)
          min_out = 0.0
          ;
          ; use 65534 here because 65535 is fill
          ;
          max_out = 65534.0
      end
      's2': begin
          test_out = intarr(cells_per_swath)
          min_out = -32768.0
          max_out = 32767.0
      end
      'u4': begin
          test_out = ulonarr(cells_per_swath)
          min_out = 0
          max_out = 4294967295.0d
      end
      's4': begin
          test_out = lonarr(cells_per_swath)
          min_out = -2147483648.0d
          max_out = 2147483647.0d
      end
      'f4': begin
          test_out = fltarr(cells_per_swath)
          min_out = -2147483648.0d
          max_out = 2147483647.0d
      end
      else: message, 'invalid data_type_out' + usage
  end
  type_code_out = size(test_out, /type)
  test_out = 0

  ; open, read, and close input raster files

  openr, lun, file_in, /get_lun
  readu, lun, swath
  free_lun, lun

  ; convert swath to floating-point as needed

  if data_type_in ne 'f4' then $
    swath = float(temporary(swath))

  i_min_in = where(swath le min_in, count_min_in)
  if count_min_in gt 0 then $
    swath[i_min_in] = min_in
  i_max_in = where(swath ge max_in, count_max_in)
  if count_max_in gt 0 then $
    swath[i_max_in] = max_in

  if file_soze ne '' then begin
      soze = intarr(cells_per_swath)

      openr, lun, file_soze, /get_lun
      readu, lun, soze
      free_lun, lun
      
      ;  normalize with respect to solar zenith (soze)
      ;  compute cos(soze)
      
      soze = cos(temporary(soze) * 0.01 * !dtor)

      ;  don't divide by small or negative cosines
      ;  and set swath to max value for such cosines

      i = where(soze lt epsilon, count)
      if count gt 0 then begin
          soze[i] = 1.0
          swath[i] = max_in
      endif
      i = 0

      ;  divide swath data by cos(soze)

      swath = temporary(swath) / soze

      i = where(swath ge max_in, count)
      if count gt 0 then begin
          swath[i] = max_in
      endif
  endif

  reg_slope = make_array(rows_per_scan, /float, value=1.0)
  reg_intcp = make_array(rows_per_scan, /float, value=0.0)

  if (file_reg_cols_in ne '') or $
     (interp_cols ne 0) or (reg_cols ne 0) then begin

  ; perform correction for the "fourth pixel" artifact

      if file_reg_cols_in ne '' then begin
          line = ''
          openr, lun, file_reg_cols_in, /get_lun
          readf, lun, line
      endif

      swath = reform(swath, cols, rows_per_scan, scans, /overwrite)

      ; cols_target is an array of column numbers for the "bad" pixels

      cells_per_det_target = long(cols) * scans / reg_col_stride
      i = indgen(cols)
      cols_target = where((i mod reg_col_stride) eq reg_col_offset, $
                          cols_per_target)
      if cols_per_target eq 0 then $
        message, 'No cells targeted for column regressions'

      if (interp_cols ne 0) or (reg_cols ne 0) then begin

          ; "before" are the pixels to the left of the target
          ; "after" are the pixels to the right of the target

          ; handle special cases on each end of the scan

          cols_before = cols_target - 1
          if cols_before[0] lt 0 then $
            cols_before[0] = i[1]

          cols_after = cols_target + 1
          if cols_after[cols_per_target - 1] ge cols then $
            cols_after[cols_per_target - 1] = cols - 2
      endif

      det_count = n_elements(reg_col_detectors)
      det_ctr = 0
      for det = 0, rows_per_scan - 1 do begin
          slope = reg_slope[det]
          intcp = reg_intcp[det]
          target = reform(swath[[cols_target], det, *], $
                          cells_per_det_target)
          if file_reg_cols_in ne '' then begin

              ; read in previously computed column slopes and intercepts
              ; and apply them to the swath

              det_test = 0L
              slope = 1.0
              intcp = 0.0
              readf, lun, det_test, intcp, slope
              if det_test eq det then begin
                  if abs(slope) ge epsilon then $
                    target = (target - intcp) / slope
                  reg_slope[det] = slope
                  reg_intcp[det] = intcp
              endif else begin
                  message, 'Entry for SS_Detector ' + $
                           string(det, format='(i2)') + $
                           ' missing from ' + file_reg_cols_in
              endelse
          endif
          det_target = reg_col_detectors[det_ctr]
          if ((interp_cols ne 0) or (reg_cols ne 0)) and $
             (det_target eq det) then begin

              ; perform column regressions using the mean of
              ; the before and after vectors

              ; set initial value of mean to target values
              mean = swath[[cols_target], det, *]

              before = reform(swath[[cols_before], det, *], $
                              1, cells_per_det_target)
              after =  reform(swath[[cols_after],  det, *], $
                              1, cells_per_det_target)

              ; only compute the mean if both the before and after values
              ; are less than max_in
              ok = where((before lt max_in) and (after lt max_in), count_ok)
              if count_ok gt 0 then $
                mean[ok] = (temporary(before[ok]) + temporary(after[ok])) / 2
              if interp_cols ne 0 then begin

                  ; if interpolating columns, then replace the 
                  ; target with the mean of the before and after vectors

                  swath[[cols_target], det, *] = mean
              endif else begin

                  ; perform the regression
                  
                  plot_tag = col_plot_tag
                  if plot_tag ne '' then $
                    plot_tag = string(plot_tag + '_', det, $
                                      format='(a, i2.2)')
                  xtitle=string('mean before and after' + $
                                '  stride: ', reg_col_stride, $
                                '  offset: ', reg_col_offset, $
                                format='(a, i2, a, i2)')
                  ytitle=string('det: ', det, $
                                format='(a, i2.2)')
                  modis_regress, mean, target, $
                    slope, intcp, $
                    y_tolerance=col_y_tolerance, $
                    slope_delta_max=col_slope_delta_max, $
                    regression_max=col_regression_max, $
                    density_bin_width=col_density_bin_width, $
                    plot_tag=plot_tag, $
                    plot_max=col_plot_max, $
                    plot_titles=[xtitle,ytitle]

                  ; use the calculated slope and intercept to correct the
                  ; target vector

                  if abs(slope) ge epsilon then $
                    swath[[cols_target], det, *] = (target - intcp) / slope

                  ; accumulate the calculated slope and intercept into the
                  ; previous values

                  reg_slope[det] = slope * reg_slope[det]
                  reg_intcp[det] = slope * reg_intcp[det] + intcp
              endelse
              if det_ctr lt det_count - 1 then $
                det_ctr = det_ctr + 1
          endif else begin   ;if ((interp_cols ne 0) or (reg_cols ne 0)) and $
                             ;(det_target eq det)
              swath[[cols_target], det, *] = target
          endelse
      endfor                    ; det
      if file_reg_cols_in ne '' then $
        free_lun, lun

      swath = reform(swath, cells_per_swath, /overwrite)

  endif ;if (file_reg_cols_in ne '') or $
        ;   (interp_cols ne 0) or (reg_cols ne 0) then begin

  if file_reg_cols_out ne '' then begin

      ; write the column slopes and intercepts to a file

      openw, lun, file_reg_cols_out, /get_lun
      printf, lun, 'DS_Detector  Col_Intercept    Col_Slope'
      for det = 0, rows_per_scan - 1 do $
        printf, lun, det, reg_intcp[det], reg_slope[det], $
                format='(i2.2, 11X, e15.8, 2x, e15.8)'
      free_lun, lun
  endif

  if (file_reg_cols_in ne '') or (file_reg_cols_out ne '') or $
     (reg_cols ne 0) then begin

      ; print the column slopes and intercepts

      print, 'SS_Detector  Col_Slope        Col_Intercept'
      for det = 0, rows_per_scan - 1 do $
        print, det, reg_intcp[det], reg_slope[det], $
               format='(i2.2, 11X, e15.8, 2x, e15.8)'
  endif

  ;  compute the number of double-sided scans,
  ;  and the number of rows per double-sided scan

  ds_scans = scans / 2
  rows_per_ds_scan = 2 * rows_per_scan

  reg_slope = make_array(rows_per_ds_scan, /float, value=1.0)
  reg_intcp = make_array(rows_per_ds_scan, /float, value=0.0)

  if (file_reg_rows_in ne '') or $
     (nor_rows ne 0) or $
     (reg_rows ne 0) then begin

      ;  perform row computations

      ;  if scans is odd, then increment the number of double scans,
      ;  duplicate the penultimate scan, and concatenate it onto the end

      if (scans mod 2) eq 1 then begin
          ds_scans = ds_scans + 1
          ipen_first = cells_per_scan * (scans - 2)
          ipen_last = ipen_first + cells_per_scan - 1
          ipen = swath[ipen_first:ipen_last]
          swath = [temporary(swath), ipen]
          ipen = 0
      endif

      ;  swap scans as needed to make the first scan be mirror side 0

      if reg_row_mirror_side eq 1 then begin
          scans_tmp = ds_scans * 2
          swath = reform(swath, cols, rows_per_scan, scans_tmp, /overwrite)
          for scan_ctr = 0, scans_tmp - 2, 2 do begin
              scan = swath[*, *, scan_ctr]
              swath[*, *, scan_ctr] = swath[*, *, scan_ctr + 1]
              swath[*, *, scan_ctr + 1] = scan
          endfor
          scan = 0
      endif

      ;  calculate the number of cells for a double-sided detector

      cells_per_ds_det = long(cols) * ds_scans

      ; reform swath so that it holds double-sided scans

      swath = reform(swath, cols, rows_per_ds_scan, ds_scans, /overwrite)

      if file_reg_rows_in ne '' then begin
          line = ''
          openr, lun, file_reg_rows_in, /get_lun
          readf, lun, line
          for ds_det = 0, rows_per_ds_scan - 1 do begin
              vector = reform(swath[*, ds_det, *], cells_per_ds_det)
              ds_det_test = 0L
              slope = 1.0
              intcp = 0.0
              readf, lun, ds_det_test, intcp, slope
              if ds_det_test eq ds_det then begin
                  if abs(slope) ge epsilon then $
                    swath[*, ds_det, *] = (temporary(vector) - intcp) / slope
                  reg_slope[ds_det] = slope
                  reg_intcp[ds_det] = intcp
              endif else begin
                  message, 'Entry for DS_Detector ' + $
                    string(det, format='(i2)') + $
                    ' missing from ' + file_reg_rows_in
              endelse
          endfor
          free_lun, lun
      endif                     ; if file_reg_rows_in ne ''

      if nor_rows ne 0 then begin

          ; normalize the mean of each double-scan detector vector
          ; with respect to the mean of the entire image

          mean_total = total(swath, /double) / $
                       (cells_per_ds_det * rows_per_ds_scan)
          for ds_det = 0, rows_per_ds_scan - 1 do begin
              vector = reform(swath[*, ds_det, *], cells_per_ds_det)
              slope = float((total(vector, /double) / cells_per_ds_det) $
                            / mean_total)
              swath[*, ds_det, *] = temporary(vector) / slope
              reg_slope[ds_det] = reg_slope[ds_det] * slope
          endfor
      endif                     ; if nor_rows ne 0

      if reg_rows ne 0 then begin

          ; if we're performing row regressions, then compute the
          ; number of passes

          case rows_per_scan of
              40: pass_count = 6
              20: pass_count = 5
              10: pass_count = 4
          endcase
      endif else begin

          ; if we're not performing row regressions, then there aren't
          ; any passes to perform

          pass_count = 0
      endelse
      mean_count = rows_per_ds_scan
      y_tol_ctr = 0
      for pass_ctr = 0, pass_count - 1 do begin

          ; perform row regressions
          ; calculate the number of means to use for this pass

          mean_count = mean_count / 2
          if mean_count eq 5 then $
            mean_count = mean_count - 1

          ; caluculate how many vectors will contribute to each
          ; mean in this pass

          vectors_per_mean = rows_per_ds_scan / mean_count
          ds_det = 0

          ; we will have one vector for each double-scan detector

          cells_per_vector = cells_per_ds_det

          for mean_ctr = 0, mean_count - 1 do begin
              weight_per_vector = 1.0 / vectors_per_mean
              mean = 0
              vectors = fltarr(cells_per_ds_det, vectors_per_mean)

              ; first assemble the vectors for this mean and
              ; calculate the mean for this group of vectors

              for vec_ctr = 0, vectors_per_mean - 1 do begin
                  vector = reform(swath[*, ds_det + vec_ctr, *], $
                                       1, cells_per_ds_det)
                  if reg_rows ne 0 then $
                    mean = vector * weight_per_vector + mean
                  vectors[*, vec_ctr] = temporary(vector)
              endfor ; vec_ctr

              ; now perform a set of regressions for each vector
              ; in the group against the mean of the group

              for vec_ctr = 0, vectors_per_mean - 1 do begin
                  vector = reform(vectors[*, vec_ctr])
                  plot_tag = row_plot_tag
                  if plot_tag ne '' then $
                    plot_tag = string(plot_tag + '_', pass_ctr, $
                                      '_', ds_det, $
                                      format='(a, i1.1, a, i2.2)')
                  xtitle=string('pass_ctr: ', pass_ctr, $
                                '  mean_ctr: ', mean_ctr, $
                                format='(a, i1, a, i2.2)')
                  ytitle=string('ds_det: ', ds_det, $
                                format='(a, i2.2)')
                  modis_regress, mean, vector, $
                                 slope, intcp, $
                                 y_tolerance=row_y_tolerance[y_tol_ctr], $
                                 slope_delta_max=row_slope_delta_max, $
                                 regression_max=row_regression_max, $
                                 density_bin_width=row_density_bin_width, $
                                 plot_tag=plot_tag, $
                                 plot_max=row_plot_max, $
                                 plot_titles=[xtitle,ytitle]

                  ; use the calculated slope and intercept to correct the
                  ; current vector

                  if abs(slope) ge epsilon then $
                    swath[*, ds_det, *] = (temporary(vector) - intcp) / slope

                  ; accumulate the calculated slope and intercept into the
                  ; previous values

                  reg_slope[ds_det] = slope * reg_slope[ds_det]
                  reg_intcp[ds_det] = slope * reg_intcp[ds_det] + intcp
                  ds_det = ds_det + 1
              endfor ; vec_ctr
              vectors = 0
              vector = 0
              mean = 0
          endfor ; mean_ctr
          if row_plot_tag ne '' then begin

              ; save each set of plots for a particular pass in a separate
              ; directory

              dir = string(row_plot_tag, '_', pass_ctr, $
                           format='(a, a, i1.1)')
              spawn, 'mkdir ' + dir, /sh
              spawn, 'mv ' + dir + '*.ps ' + dir, /sh
          endif
          if y_tol_ctr lt row_y_tolerance_count - 1 then $
            y_tol_ctr = y_tol_ctr + 1
      endfor ; pass_ctr

      ; reform the swath array back into its original structure

      swath = reform(swath, cols, rows_per_scan, ds_scans * 2, /overwrite)

      ;  re-swap scans as needed to make the first scan be mirror side 1

      if reg_row_mirror_side eq 1 then begin
          scans_tmp = ds_scans * 2
          for scan_ctr = 0, scans_tmp - 2, 2 do begin
              scan = swath[*, *, scan_ctr]
              swath[*, *, scan_ctr] = swath[*, *, scan_ctr + 1]
              swath[*, *, scan_ctr + 1] = scan
          endfor
          scan = 0
      endif

      ; remove bogus scan at end if necessary

      if (scans mod 2) eq 1 then $
        swath = temporary(swath[*, *, 0:scans - 1])

  endif  ; if reg_rows ne 0

  if file_reg_rows_out ne '' then begin

     ; write the row slopes and intercepts to a file

     openw, lun, file_reg_rows_out, /get_lun
     printf, lun, 'DS_Detector  Row_Intercept    Row_Slope'
     for ds_det = 0, rows_per_ds_scan - 1 do $
       printf, lun, ds_det, reg_intcp[ds_det], reg_slope[ds_det], $
                    format='(i2.2, 11X, e15.8, 2x, e15.8)'
     free_lun, lun
  endif

  if (file_reg_rows_in ne '') or (file_reg_rows_out ne '') or $
     (nor_rows ne 0) or (reg_rows ne 0) then begin

      ; print the row slopes and intercepts

      print, 'DS_Detector  Row_Intercept    Row_Slope'
      for ds_det = 0, rows_per_ds_scan - 1 do $
        print, ds_det, reg_intcp[ds_det], reg_slope[ds_det], $
               format='(i2.2, 11X, e15.8, 2x, e15.8)'
  endif

  ;  undo solar zenith normalization if required

  if (file_soze ne '') and (undo_soze ne 0) then begin
      swath = temporary(swath) * soze
      soze = 0
  endif

  ;  put the swath back into output data type as needed

  i = where(swath lt min_out, count)
  if count gt 0 then $
    swath[i] = min_out
  i = where(swath gt max_out, count)
  if count gt 0 then $
    swath[i] = max_out
  swath = fix(round(temporary(swath)), type=type_code_out)


  ;  make min and max values the same as on input
  ;  to ensure that fill values (e.g. 65535) stay as fill

  if count_min_in gt 0 then $
    swath[i_min_in] = min_in
  if count_max_in gt 0 then $
    swath[i_max_in] = max_in
 
  ;  open, write, and close output file

  openw, lun, file_out, /get_lun
  writeu, lun, swath
  free_lun, lun

  time_end = systime(/seconds)
  elapsed_seconds = time_end - time_start
  elapsed_minutes = fix(elapsed_seconds / 60)
  elapsed_seconds = elapsed_seconds - 60 * elapsed_minutes
  print, 'modis_adjust:'
  print, '  completed:            ', systime(0, time_start)
  print, '  elapsed time:         ', elapsed_minutes, ' min  ', $
                                     elapsed_seconds, ' sec  ', $
                                     format = '(a, i3, a, i2, a)'

END ; modis_adjust
