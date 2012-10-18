;*========================================================================
;* modis_regress.pro - perform a modis regression of two vectors
;*
;* 20-Nov-2002  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /disks/megadune/data/tharan/ms2gth/src/idl/modis_utils/modis_regress.pro,v 1.13 2004/10/31 23:50:05 haran Exp $
;*========================================================================*/

;+
; NAME:
;	modis_regress
;
; PURPOSE:
;       Perform a regression of one vector vs. another vector,
;       and optionally plot the results.
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       MODIS_REGESS, x, y, slope, intercept
;               [, skip_first_regression=skip_first_regression]
;               [, y_tolerance=y_tolerance]
;               [, slope_delta_max=slope_delta_max]
;               [, regression_max=regression_max]
;               [, density_bin_width=density_bin_width]
;               [, plot_tag=plot_tag]
;               [, plot_max=plot_max]
;               [, plot_titles=plot_titles]
;
; ARGUMENTS:
;    Inputs:
;       x: the independent variable to plot along the x axis.
;         Note that this must be a column vector, i.e. [1, n].
;       y: the dependent variable to plot along the y axis.
;    Outputs:
;       slope: the slope computed from the regression.
;       intercept: the intercept computed from the regression.
;       Thus the best fit line is y = slope * x + intercept.
;       NOTE: If skip_first_regression is set, then slope and intercept
;             also serve as inputs.
;
; KEYWORDS:
;       skip_first_regression: If set then the first regression is skipped
;         and the slope and intercept provided are used to detect outliers
;         on the second linear regression.
;       y_tolerance: the value to use after the first linear regression
;         has been performed to find "outliers" that will be eliminated
;         from the second linear regression. That is, after k and m have
;         been determined from the first linear regression, the values
;         y'(i) = k + m * x(i) are calculated. Then outliers are defined
;         to be all points x(i) for which
;         abs((y'(i) - y(i)) / (ymax - ymin)) >= y_tolerance.
;         Then a second regression is performed on the remaining x(i) after
;         the outliers have been removed to determine the final k and m
;         values. The default value of y_tolerance is 0.0.
;         NOTE: If y_tolerance is 0.0, then no second linear regression
;               is performed.
;       slope_delta_max: the outlier detection procedure described for
;         y_tolerance is repeated until slope_delta =
;         abs(slope - slope_old) / slope_old is less than or equal to
;         slope_delta_max. The default value of slope_delta_max is 0.001.
;         NOTE: If slope_delta_max is 0.0, then no third linear regression
;               or higher is performed.
;       regression_max: the outlier detection procedure is repeated a maximum
;         of regression max total number of regressions.
;         The default value of regression_max is 10.
;       density_bin_width: the bin width used to create a weight map based on
;         the density of the scatterplot. If density_bin_width is 0 (default)
;         then all weights are set to 1 for the regressions.
;       plot_tag: string used to name and label regression plot files. Plot
;         files will be labelled plot_tag.ps. The default value of
;         plot_tag is a null string indicating that no plots should be created.
;       plot_max: maximum values to plot. Default is 0 meaning use the maximum
;         values in the data. if plot_tag is a null string, then plot_max is
;         ignored.
;       plot_titles: 2-element string array containing the x and y titles,
;         respectively. The default is that both titles are the null string.
;
; EXAMPLE:
;       modis_regress(mean_this, mean_old_this, $
;                     slope_this, intcp_this, $
;                     y_tolerance=row_y_tolerance, $
;                     slope_delta_max=row_slope_delta_max, $
;                     regression_max=row_regression_max, $
;                     density_bin_width=row_density_bin_width, $
;                     plot_tag=plot_tag, $
;                     plot_max=row_plot_max, $
;                     plot_titles=[xtitle,ytitle]

; ALGORITHM:
;
; REFERENCE:
;-

Pro modis_regress, x, y, slope, intercept, $
                  skip_first_regression=skip_first_regression, $
                  y_tolerance=y_tolerance, $
                  slope_delta_max=slope_delta_max, $
                  regression_max=regression_max, $
                  density_bin_width=density_bin_width, $
                  plot_tag=plot_tag, $
                  plot_max=plot_max, $
                  plot_titles=plot_titles

  epsilon = 1e-6

  lf = string(10B)

  usage = lf + 'usage: modis_adjust, ' + lf + $
                'x, y, slope, intercept' + lf + $
                '[, skip_first_regression=skip_first_regression' + lf + $
                '[, y_tolerance=y_tolerance] ' + lf + $
                '[, slope_delta_max=slope_delta_max] ' + lf + $
                '[, regression_max=regression_max] ' + lf + $
                '[, density_bin_width=density_bin_width] ' + lf + $
                '[, plot_tag=plot_tag] ' + lf + $
                '[, plot_max=plot_max] ' + lf + $
                '[, plot_titles=plot_titles]'

  if n_params() ne 4 then $
    message, usage

  if n_elements(skip_first_regression) eq 0 then $
    skip_first_regression = 0
  if n_elements(y_tolerance) eq 0 then $
    y_tolerance = 0.0
  if n_elements(slope_delta_max) eq 0 then $
    slope_delta_max = 0.001
  if n_elements(regression_max) eq 0 then $
    regression_max = 10
  if n_elements(density_bin_width) eq 0 then $
    density_bin_width = 0
  if n_elements(plot_tag) eq 0 then $
    plot_tag = ''
  if n_elements(plot_max) eq 0 then $
    plot_max = 0
  if n_elements(plot_titles) eq 0 then $
    plot_titles = ['', '']

  reg_col_detectors_count = n_elements(reg_col_detectors)

  print, 'modis_regress: $Header: /disks/megadune/data/tharan/ms2gth/src/idl/modis_utils/modis_regress.pro,v 1.13 2004/10/31 23:50:05 haran Exp $'
  if skip_first_regression then begin
      print, '  slope:                 ', slope[0]
      print, '  intercept:             ', intercept
  endif
  print, '  skip_first_regression: ', skip_first_regression
  print, '  y_tolerance:           ', y_tolerance
  print, '  slope_delta_max:       ', slope_delta_max
  print, '  regression_max:        ', regression_max
  print, '  density_bin_width:     ', density_bin_width
  print, '  plot_tag:              ', plot_tag
  print, '  plot_max:              ', plot_max
  size_plot_titles = size(plot_titles)
  if size_plot_titles[0] eq 1 then begin
      if size_plot_titles[1] eq 2 then begin
          print, '  plot_titles[0]:        ', plot_titles[0]
          print, '  plot_titles[1]:        ', plot_titles[1]
      endif
  endif

  ; check for valid input

  size_x = size(x)
  if size_x[0] ne 2 then $
    message, 'x must be a 2-dimensional array'
  if size_x[1] ne 1 then $
    message, 'The first dimension of x must be of size 1'
  size_y = size(y)
  if size_y[0] ne 1 then $
    message, 'y must be a 1-dimensional array'
  if size_y[1] ne size_x[2] then $
    message, $
    'The second dimension of x must be the same size as the dimension of y'
  if size_plot_titles[0] ne 1 then $
    message, 'plot_titles must be a 1-dimensional array'
  if size_plot_titles[1] ne 2 then $
    message, 'plot_titles must be a 2-element array'

  ;  intialize outputs and status

  if not skip_first_regression then begin
      slope = 1.0
      intercept = 0.0
  endif
  status = 0L

  ;  if using weights, then compute y density parameters

  y_max = max(y, min=y_min)
  y_range = y_min - y_max
  if density_bin_width gt 0 then begin
      x_max = max(x, min=x_min)
      x_bin_count = floor((x_max - x_min) / density_bin_width) + 1L
      x_factor = x_bin_count / (x_max - x_min)
      y_bin_count = floor((y_max - y_min) / density_bin_width) + 1L
      y_factor = y_bin_count / y_range
      h = long((x - x_min) * x_factor) * y_bin_count + $
          long((y - y_min) * y_factor)
      h = histogram(h, reverse_indices=r)
      n = n_elements(h)
      weight = fltarr(n)
      for i = 0L, n - 1 do begin
          if (r[i] ne r[i+1]) then begin
              weight[r[r[i] : r[i+1] - 1]] = h[i]
          endif
      endfor
      h = 0
      r = 0
      i = where(weight lt epsilon, count)
      if count gt 0 then $
        weight[i] = epsilon
      i = 0
      weight = 1.0 / temporary(weight)
  endif

  regression_count = 1
  if not skip_first_regression then begin
      if density_bin_width gt 0 then begin
          slope = regress(x, y, const=intercept, status=status, $
                          measure_errors=weight)
      endif else begin
          slope = regress(x, y, const=intercept, status=status)
      endelse
  endif

  if (status eq 0) and (y_tolerance gt 0) then $
    final = '' $
  else $
    final = ' final'
  if skip_first_regression then $
    final = ' input'
  annot = string('  tag: ', plot_tag, $
                 '  iteration: ', regression_count, $
                 '  status: ', status, $
                 '  intercept: ', intercept, $
                 '  slope: ', slope[0], final, $
                 format='(a,a,a,i2,a,i2,a,e12.5,a,f8.5,a)')
  print, annot
  if final ne ' final' then begin
      
  ; compare original y values to computed y values and
  ; select only those within y_tolerance

  ; keep iterating until the change in slope is less than
  ; slope_delta_max or until the number of iterations exceeds
  ; regression_max

      repeat begin
          slope_old = slope[0]
          i = where(abs((y - (slope[0] * x + intercept)) / y_range) lt $
                    y_tolerance, n2)
          if n2 lt 2 then begin
              slope = 1.0
              intercept = 0.0
              regression_count = regression_max
          endif else begin
              x2 = reform(x[i], 1, n2)
              y2 = y[i]
              status = 0L
              slope = 1.0
              intercept = 0.0
              if density_bin_width gt 0 then begin
                  weight2 = weight[i]
                  slope = regress(x2, y2, const=intercept, $
                                  status=status, $
                                  measure_errors=weight2)
              endif else begin
                  slope = regress(x2, y2, const=intercept, $
                                  status=status)
              endelse
              i = 0
              if (status ne 0) then begin
                  regression_count = regression_max
              endif
          endelse
          regression_count = regression_count + 1
          if abs(slope_old) gt epsilon then $
            slope_delta = abs(slope[0] - slope_old) / slope_old $
          else $
            slope_delta = 0.0
          if (slope_delta_max eq 0) or $
            (slope_delta le slope_delta_max) or $
            (regression_count ge regression_max) then $
            final = ' final' $
          else $
            final = ''
          annot = string('  tag: ', plot_tag, $
                         '  iteration: ', regression_count, $
                         '  status: ', status, $
                         '  intercept: ', intercept, $
                         '  slope: ', slope[0], final, $
                         format='(a,a,a,i2,a,i2,a,e12.5,a,f8.5,a)')
          print, annot
      endrep until (final ne '')
      x2 = 0
      y2 = 0
  endif                         ; if (status eq 0) and (y_tolerance gt 0)
  weight = 0
  
  if plot_tag ne '' then begin
      
  ;  create the scatter plot for this sensor

      file_plot = plot_tag + '.ps'
      mydev = !D.NAME
      set_plot, 'ps'
      
      device, filename=file_plot, /landscape, /color, $
        bits_per_pixel=8
      device, xsize=10.0, ysize=7.5, /inches
      x_min = 0
      if plot_max eq 0 then $
        plot_max = max(x)
      plot, x, y, psym=3, xstyle=1, ystyle=1, charsize=1.0, $
        xrange=[x_min, plot_max], yrange=[x_min, plot_max], $
        title=plot_file, $
        xtitle=plot_titles[0], $
        ytitle=plot_titles[1]
      xmm = [x_min, plot_max]
      ymm = slope[0] * xmm + intercept
      oplot, xmm, ymm, psym=0, color=125
      if y_tolerance gt 0 then begin
          ymm = slope[0] * xmm + intercept + y_tolerance
          oplot, xmm, ymm, psym=0, color=125
          ymm = slope[0] * xmm + intercept - y_tolerance
          oplot, xmm, ymm, psym=0, color=125
      endif
      xyouts, .10, .92, annot, charsize=1.0, /normal
      annot = string('  y_tolerance: ', y_tolerance)
      xyouts, .10, .89, annot, charsize=1.0, /normal
      annot = string('  regression count: ', regression_count)
      xyouts, .10, .86, annot, charsize=1.0, /normal
  endif

  slope = slope[0]

END ; modis_regress
