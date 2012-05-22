FUNCTION HDF_SD_VARINFO, HDFID, VARNAME

;+
; NAME:
;    HDF_SD_VARINFO
;
; PURPOSE:
;    Return information about a Scientific Data Set (SDS) variable
;    in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = HDF_SD_VARINFO(HDFID, VARNAME)
;
; INPUTS:
;    HDFID       Identifier of HDF file opened by caller with HDF_SD_START.
;    VARNAME     Name of Scientific Data Set variable.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    None.
;
; OUTPUTS:
;    An anonymous structure containing information about the SDS.
;    The fields in the structure are as follows:
;    NAME        Name of the variable ('' if variable not found)
;    NDIMS       Number of dimensions (-1 if variable not found)
;    DIMS        Array of dimension sizes (-1 if variable not found)
;    DIMNAMES    Array of dimension names ('' if variable not found)
;    TYPE        Variable data type ('' if variable not found)
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
;result = hdf_sd_varinfo(hdfid, '2D integer array')
;hdf_sd_end, hdfid
;help, result, /structure
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_sd_varinfo.pro,v 1.2 1999/12/29 21:22:30 gumley Exp $
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

rcs_id = '$Id: hdf_sd_varinfo.pro,v 1.2 1999/12/29 21:22:30 gumley Exp $'

;- Check arguments
if (n_params() ne 2) then message, 'Usage: RESULT = HDF_SD_VARINFO(HDFID)'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'
if (n_elements(varname) eq 0) then message, 'Argument VARNAME is undefined'

;- Set default return values
name     = ''
ndims    = -1
dims     = -1
dimnames = ''
type     = ''

;- Get variable information
varindex = hdf_sd_nametoindex(hdfid, varname)
if (varindex ge 0) then begin

  ;- Select the variable and get name, dimension, and type information
  varid = hdf_sd_select(hdfid, varindex)
  hdf_sd_getinfo, varid, name=name, ndims=ndims, dims=dims, type=type
  
  ;- Get dimension names
  if (ndims ge 1) then begin
    dimnames= strarr(ndims)
    for dimindex = 0, ndims - 1 do begin
      dimid = hdf_sd_dimgetid(varid, dimindex)
      hdf_sd_dimget, dimid, name=dimname
      dimnames[dimindex] = dimname
    endfor
  endif
  
  ;- Deselect the variable
  hdf_sd_endaccess, varid
  
endif

;- Return result to caller
return, {name:name, ndims:ndims, dims:dims, dimnames:dimnames, type:type}

END
