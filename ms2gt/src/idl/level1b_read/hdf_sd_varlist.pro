FUNCTION HDF_SD_VARLIST, HDFID

;+
; NAME:
;    HDF_SD_VARLIST
;
; PURPOSE:
;    Return the number and names of Scientific Data Set (SDS) variables
;    in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = HDF_SD_VARLIST(HDFID)
;
; INPUTS:
;    HDFID       Identifier of HDF file opened by caller with HDF_SD_START.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    None.
;
; OUTPUTS:
;    An anonymous structure containing the number of SDS variables in the file,
;    and the name of each SDS variable in the file.
;    The fields in the structure are as follows:
;    NVARS       Number of SDS variables in the file (0 if none were found).
;    VARNAMES    Array of SDS variable names ('' if none were found).
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
;file = 'sdsvdata.hdf'
;hdfid = hdf_sd_start(file)
;result = hdf_sd_varlist(hdfid)
;hdf_sd_end, hdfid
;help, result, /structure
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_sd_varlist.pro,v 1.2 1999/12/29 20:24:33 gumley Exp $
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

rcs_id = '$Id: hdf_sd_varlist.pro,v 1.2 1999/12/29 20:24:33 gumley Exp $'

;- Check arguments
if (n_params() ne 1) then message, 'Usage: RESULT = HDF_SD_VARLIST(HDFID)'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'

;- Set default return values
nvars = 0
varnames = ''

;- Get number of SDS variables and global attributes
hdf_sd_fileinfo, hdfid, nvars, ngatts

;- Get SDS variable names
if (nvars gt 0) then begin
  varnames = strarr(nvars)
  for index = 0, nvars - 1 do begin
    varid = hdf_sd_select(hdfid, index)
    hdf_sd_getinfo, varid, name=name
    hdf_sd_endaccess, varid
    varnames[index] = name
  endfor
endif

;- Return the result
return, {nvars:nvars, varnames:varnames}

END
