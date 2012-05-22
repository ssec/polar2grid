;*========================================================================
;* extract_valid_scans.pro - extract latitude and longitude from a mod02 or
;                       mod03 file
;*
;* 19-Nov-2004  Terry Haran  tharan@colorado.edu  492-1847
;* National Snow & Ice Data Center, University of Colorado, Boulder
;$Header: /data/tharan/ms2gth/src/idl/modis_utils/extract_valid_scans.pro,v 1.23 2010/09/04 18:44:16 tharan Exp $
;*========================================================================*/

;+
; NAME:
;	extract_valid_scans
;
; PURPOSE: Use the Latitude array to determine which scans are valid,
;          and then return the valid scans for the indicated sds_name.
;
; CATEGORY:
;	Modis.
;
; CALLING SEQUENCE:
;       image = extract_valid_scans(sd_id, sds_name_img, lines_per_scan_img,
;                                   band_index, area=area,
;                                   invalid_fraction_max=invalid_fraction_max)
;
; ARGUMENTS:
;
; KEYWORDS:
;    AREA           A four element vector specifying the area to be read,
;                   in the format [X0,Y0,NX,NY]
;                   (default is to read the entire image).
;    INVALID_FRACTION_MAX
;                   Specifies the maximum fraction of invalid pixels to
;                   tolerate. The default value is 0.5.
;
; EXAMPLE:
;
; ALGORITHM:
;
; REFERENCE:
;-

FUNCTION extract_valid_scans, sd_id, sds_name_img, lines_per_scan_img, $
                              band_index, $
                              area=area, $
                              invalid_fraction_max=invalid_fraction_max

  usage = 'usage: image = extract_valid_scans(sd_id, sds_name, ' + $
          'lines_per_scan, band_index, [area=area, ' + $
          'invalid_fraction_max=invalid_fraction_max'

  if n_params() ne 4 then $
    message, usage

  if n_elements(invalid_fraction_max) eq 0 then $
    invalid_fraction_max = 0.5
  if (invalid_fraction_max lt 0.0) or (invalid_fraction_max gt 1.0) then $
     message, 'INVALID_FRACTION_MAX must be in the range 0.0 to 1.0'

  got_mirror = 0
  if sds_name_img eq 'Mirror side' then begin

  ;- Read mirror side data
      got_mirror = 1
      hdf_sd_varread, sd_id, sds_name_img, mirror
      sds_name_img = 'Latitude'
  endif

;- Get information about the image array
  varinfo = hdf_sd_varinfo(sd_id, sds_name_img)
  if (varinfo.name eq '') then $
    message, 'Image array was not found: ' + sds_name_img
  npixels_across_img = varinfo.dims[0]
  npixels_along_img  = varinfo.dims[1]
  npixels_per_scan_img = npixels_across_img * lines_per_scan_img
  nscans_img = npixels_along_img / lines_per_scan_img
  if npixels_along_img mod lines_per_scan_img ne 0 then $
    message, 'Number of lines in image ' + sds_name_img + ': ' + $
              string(npixels_along_img) + $
              ' is not evenly divisible by ' + $
              string(lines_per_scan_img)

;- Read valid range attribute for image
    valid_name = 'valid_range'
    att_info = hdf_sd_attinfo(sd_id, sds_name_img, valid_name)
    if (att_info.name eq '') then message, 'Attribute not found: ' + valid_name
    valid_range = att_info.data

;- Get fill value for image
    attname = '_FillValue'
    attinfo = hdf_sd_attinfo(sd_id, sds_name_img, attname)
    if (attinfo.name eq attname) then $
      fill_img = attinfo.data[0] $
    else $
      fill_img = 0

;- If band_index is -1, then we have a two-dimensional array;
;- otherwise we have a band sequential, three-dimensional array,
;- with band_index the element number of the third dimension
  if band_index eq -1 then begin

  ;- Read two-dimensional data
      hdf_sd_varread, sd_id, sds_name_img, img

    endif else begin

  ;- Set start and count values
        start = [0L, 0L, band_index]
        count = [npixels_across_img, npixels_along_img, 1L]

  ;- Read the three-dimensional image array
  ;- (hdf_sd_varread not used because of bug in IDL 5.1)
        var_id = hdf_sd_select(sd_id, hdf_sd_nametoindex(sd_id, sds_name_img))
        hdf_sd_getdata, var_id, img, start=start, count=count
        hdf_sd_endaccess, var_id

    endelse

;- Reset the image name back if necessary
    if got_mirror then $
      sds_name_img = 'Mirror side'

;- Use the Latitude array to determine which scans are bad

    sds_name_lat = 'Latitude'

;- Get information about the Latitude array
  varinfo = hdf_sd_varinfo(sd_id, sds_name_lat)
  if (varinfo.name eq '') then $
    message, 'Image array was not found: ' + sds_name_lat
  npixels_across_lat = varinfo.dims[0]
  npixels_along_lat  = varinfo.dims[1]

;- Assume for now that the number of scans in the image is 
;- the same as the number of scans in the Latitude array
  nscans_lat = nscans_img
  lines_per_scan_lat = fix(npixels_along_lat / nscans_lat)
  npixels_per_scan_lat = npixels_across_lat * lines_per_scan_lat
  nscans_lat = npixels_along_lat / lines_per_scan_lat
  if npixels_along_lat mod lines_per_scan_lat ne 0 then $
    message, 'Number of lines in Latitude:' + $
             string(npixels_along_lat) + $
             ' is not evenly divisible by ' + $
             string(lines_per_scan_lat)

;- Make sure the number of scans in the image matches
;- the number of scans in the Latitude array
  if nscans_img ne nscans_lat then $
    message, $
    'Number of scans in image ' + sds_name_img + ': ' + string(nscans_img) + $
    ' is not equal to number of scans in Latitude: '  + string(nscans_lat)

;- Read two-dimensional Latitude data
    hdf_sd_varread, sd_id, sds_name_lat, lat

;- Get fill value for Latitude
    attname = '_FillValue'
    attinfo = hdf_sd_attinfo(sd_id, sds_name_lat, attname)
    if (attinfo.name eq attname) then $
      fill_lat = attinfo.data[0] $
    else $
      fill_lat = -999.0

;- Set invalid_count_max
    invalid_count = 0L
    invalid_pixel_count_max = long(invalid_fraction_max * npixels_per_scan_lat)

    if invalid_pixel_count_max gt 0 then begin

    ;- Remove any scans that have too many values equal to fill
        for i = 0L, nscans_img - 1 do begin
            k = i - invalid_count
            n = nscans_img - invalid_count

            first_img = k * npixels_per_scan_img
            last_img  = first_img + npixels_per_scan_img - 1

            first_lat = k * npixels_per_scan_lat
            last_lat  = first_lat + npixels_per_scan_lat - 1

            img_scan = img[first_img:last_img]
            lat_scan = lat[first_lat:last_lat]

        ;- count_invalid_lat gets number of fill in lat scan
        ;- j not used here
            j = where(lat_scan eq fill_lat, count_invalid_lat)
            if count_invalid_lat ge invalid_pixel_count_max then begin

            ;- scan had too many fills
                if i lt nscans_img - 1 then begin

                    img[first_img:(n - 1) * npixels_per_scan_img - 1] = $
                      img[first_img + npixels_per_scan_img: $
                            n * npixels_per_scan_img - 1]

                    lat[first_lat:(n - 1) * npixels_per_scan_lat - 1] = $
                      lat[first_lat + npixels_per_scan_lat: $
                            n * npixels_per_scan_lat - 1]

                    if got_mirror then $
                      mirror[k:n - 2] = $
                        mirror[k + 1:n - 1]

                    message, /informational, $
                      'Scan ' + string(i, format='(i3)') + $
                      ' removed from ' + sds_name_img
                endif
                invalid_count = invalid_count + 1
                npixels_along_img = npixels_along_img - lines_per_scan_img
                npixels_along_lat = npixels_along_lat - lines_per_scan_lat

            endif

        endfor
    endif

    if invalid_count gt 0 then begin
        nscans_img = nscans_img - invalid_count
        img = img[*, 0:npixels_along_img - 1]
    endif

    if not got_mirror then begin

    ;- count_img gets number of out of range in img scan
    ;- j gets the elements to be filled
        j = where((img lt valid_range[0]) or $
                  (img gt valid_range[1]), count_invalid_img)
        
        if count_invalid_img gt 0 then begin

        ;- set out of range to fill
            img[j] = fill_img
            message, /informational, $
              string(count_invalid_img) + $
              ' out of range values detected in ' + sds_name_img

        endif

    endif

    if got_mirror then begin
        if invalid_count gt 0 then $
          mirror = mirror[0:nscans_img - 1]

    ;- Use AREA keyword if it was supplied
        if (n_elements(area) eq 4) then begin
            area10 = area / 10
            start = (long(area10[1]) > 0L) < (nscans_img - 1L)
            last  = (long(area10[3] + start - 1L) > 0L) < (nscans_img - 1L)
            mirror = mirror[start:last]
        endif
        img = mirror
            
    endif else begin

    ;- Use AREA keyword if supplied
        if (n_elements(area) eq 4) then begin
            start = lonarr(2)
            last  = lonarr(2)
            start[0] = (long(area[0]) > 0L) < (npixels_across_img - 1L)
            start[1] = (long(area[1]) > 0L) < (npixels_along_img  - 1L)
            last[0]  = (long(area[2] + start[0] - 1L) > 0L) < $
                       (npixels_across_img - 1L)
            last[1]  = (long(area[3] + start[1] - 1L) > 0L) < $
                       (npixels_along_img  - 1L)
            img = img[start[0]:last[0], start[1]:last[1]]
        endif
    endelse

    return, img
END ; extract_valid_scans
