FUNCTION MODIS_LEVEL1B_INFO, FILENAME, QUIET=QUIET

;+
; NAME:
;    MODIS_LEVEL1B_INFO
;
; PURPOSE:
;    Return information about a MODIS Level 1B HDF product file, including
;    number of scans (total, day, night), number of frames (pixels),
;    start and end time, and geographic location.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = MODIS_LEVEL1B_INFO(FILENAME)
;
; INPUTS:
;    FILENAME    Name of file
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    QUIET          If set to true (1), no warning messages are printed
;                   (default is to print warning messages).
;
; OUTPUTS:
;    An anonymous structure containing information about the file.
;    The fields in the structure are as follows:
;    NAME            String containing the name of the file
;                    (environment variables in the path are expanded).
;    PRODUCT         String containing product name
;                    (possible values are 'MOD021KM', 'MOD02HKM', 'MOD02QKM',
;                     or '' if file is not in MODIS Level 1B format).
;    LATBOX          Array of latitude bounding box values (degrees).
;    LONBOX          Array of longitude bounding box values (degrees,
;                     -180W to 180E, Greenwich is zero).
;    NSCANS          Number of earth scans.
;    NSCANS_DAY      Number of earth scans in day mode.
;    NSCANS_NIGHT    Number of earth scans in night mode.
;    START_TIME      Earth view scan start time for first scan (TAI seconds).
;    END_TIME        Earth view scan start time for last scan (TAI seconds).
;    START_LAT       Nadir frame latitude for first scan (degrees).
;    START_LON       Nadir frame longitude for first scan (degrees).
;    END_LAT         Nadir frame latitude for last scan (degrees).
;    END_LON         Nadir frame longitude for last scan (degrees).
;
; OPTIONAL OUTPUTS:
;    None
;
; COMMON BLOCKS:
;    None
;
; SIDE EFFECTS:
;    None.
;
; RESTRICTIONS:
;    Requires IDL 5.0 or higher (square bracket array syntax).
;
; EXAMPLE:
;
;filename = 'MOD021KM.A1999056.1600.002.2000008081137.hdf'
;result = modis_level1b_info(filename)
;help, result, /structure
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: modis_level1b_info.pro,v 1.1 2000/01/27 17:38:18 gumley Exp $
;
; Copyright (C) 1999, 2000 Liam E. Gumley
;
; This program is free software; you can redistribute it and/or
; modify it under the terms of the GNU General Public License
; as published by the Free Software Foundation; either version 2
; of the License, or (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
;-

rcs_id = '$Id: modis_level1b_info.pro,v 1.1 2000/01/27 17:38:18 gumley Exp $'

;-------------------------------------------------------------------------------
;- CHECK INPUT
;-------------------------------------------------------------------------------

;- Check arguments
if (n_params() eq 0) then $
  message, 'Usage: RESULT = MODIS_LEVEL1B_INFO(FILENAME)'
if (n_elements(filename) eq 0) then message, 'Argument FILENAME is undefined'

;- Set default return value
result = {$
  name         : '', $
  product      : '', $
  latbox       : replicate(-9999.0, 4), $
  lonbox       : replicate(-9999.0, 4), $
  nscans       : 0L, $
  nframes      : 0L, $
  nscans_day   : 0L, $
  nscans_night : 0L, $
  start_time   : 0.0D, $
  end_time     : 0.0D, $
  start_lat    : -9999.0, $
  start_lon    : -9999.0, $
  end_lat      : -9999.0, $
  end_lon      : -9999.0}

;-------------------------------------------------------------------------------
;- GET MODIS FILE INFORMATION
;-------------------------------------------------------------------------------

;- Get file information
fileinfo = modis_file_info(filename, /quiet)
result.name = fileinfo.name

;- Check for the presence of SDS variables
if (fileinfo.nvars eq 0) then begin
  if (keyword_set(quiet) eq 0) then $
    message, 'No HDF SDS variables were found: ' + filename, /continue
  return, result
endif

;- Check for variable names which signify MODIS Level 1B data
index_1km = where(fileinfo.var_names eq 'EV_1KM_RefSB', count_1km)
index_500 = where(fileinfo.var_names eq 'EV_500_RefSB', count_500)
index_250 = where(fileinfo.var_names eq 'EV_250_RefSB', count_250)
if (total([count_1km, count_500, count_250]) eq 0) then begin
  if (keyword_set(quiet) eq 0) then $
    message, 'No MODIS Level 1B variables were found: ' + filename, /continue
  return, result
endif

;- Save the product name
case 1 of
  (count_1km gt 0) : result.product = 'MOD021KM'
  (count_500 gt 0) : result.product = 'MOD02HKM'
  (count_250 gt 0) : result.product = 'MOD02QKM'
endcase  

;- Get latitude bounding box (on_ioerror handles read errors)
latbox = fltarr(4)
index = where(fileinfo.meta_names eq 'GRINGPOINTLATITUDE', count)
on_ioerror, done_latbox
if (count gt 0) then reads, fileinfo.meta_values[index], latbox
result.latbox = latbox
done_latbox:

;- Get longitude bounding box (on_ioerror handles read errors)
lonbox = fltarr(4)
index = where(fileinfo.meta_names eq 'GRINGPOINTLONGITUDE', count)
on_ioerror, done_lonbox
if (count gt 0) then reads, fileinfo.meta_values[index], lonbox
result.lonbox = lonbox
done_lonbox:

;- Cancel error handler
on_ioerror, null

;-------------------------------------------------------------------------------
;- READ MODIS PARAMETERS FROM GLOBAL ATTRIBUTES
;-------------------------------------------------------------------------------

;- Open file in SDS mode
sd_id = hdf_sd_start(result.name, /read)

;- Get scan and frame information from global attributes
attinfo = hdf_sd_attinfo(sd_id, '', 'Number of Scans', /global)
result.nscans = attinfo.data
attinfo = hdf_sd_attinfo(sd_id, '', 'Max Earth View Frames', /global)
result.nframes = attinfo.data
attinfo = hdf_sd_attinfo(sd_id, '', 'Number of Day mode scans', /global)
result.nscans_day = attinfo.data
attinfo = hdf_sd_attinfo(sd_id, '', 'Number of Night mode scans', /global)
result.nscans_night = attinfo.data

;- Close file in SDS mode
hdf_sd_end, sd_id

;-------------------------------------------------------------------------------
;- READ MODIS PARAMETERS FROM VDATAS
;-------------------------------------------------------------------------------

;- Open file in HDF mode
hdfid = hdf_open(result.name, /read)

;- Get start and end time, lat, lon information from vdatas
vdataname = 'Level 1B Swath Metadata'
hdf_vd_vdataread, hdfid, vdataname, 'EV Sector Start Time', time
hdf_vd_vdataread, hdfid, vdataname, 'Latitude of Nadir Frame', lat
hdf_vd_vdataread, hdfid, vdataname, 'Longitude of Nadir Frame', lon
result.start_time = time[0]
result.start_lat  = lat[0]
result.start_lon  = lon[0]
result.end_time   = time[result.nscans - 1]
result.end_lat    = lat[result.nscans - 1]
result.end_lon    = lon[result.nscans - 1]

;- Close file in HDF mode
hdf_close, hdfid

;- Return result to caller
return, result

END
