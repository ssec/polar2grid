FUNCTION HDF_SD_ATTINFO, HDFID, VARNAME, ATTNAME, GLOBAL=GLOBAL

;+
; NAME:
;    HDF_SD_ATTINFO
;
; PURPOSE:
;    Return the name, type, and data for an attribute associated with
;    an individual Scientific Data Set (SDS) variable in a HDF file,
;    or a global attribute in a HDF file.
;
; INPUTS:
;    HDFID       Identifier of HDF file opened by caller with HDF_SD_START.
;    VARNAME     Name of variable to examine (ignored if GLOBAL keyword set).
;    ATTNAME     Name of attribute.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    GLOBAL      If set, information about a global attribute is returned.
;
; OUTPUTS:
;    An anonymous structure containing the name, type, and data for the
;    requested attribute.
;    The fields in the structure are as follows:
;    NAME    Name of the attribute ('' if attribute or variable was not found).
;    TYPE    Attribute data type ('' if attribute or variable was not found).
;    DATA    Attribute data (-1 if attribute or variable was not found).
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
;result = hdf_sd_attinfo(hdfid, '', 'message')
;help, result, /structure
;result = hdf_sd_attinfo(hdfid, '2D integer array', 'units')
;help, result, /structure
;hdf_sd_end, hdfid
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_sd_attinfo.pro,v 1.2 2000/02/03 22:25:57 gumley Exp $
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

rcs_id = '$Id: hdf_sd_attinfo.pro,v 1.2 2000/02/03 22:25:57 gumley Exp $'

;- Check arguments
if (n_params() ne 3) then $
  message, 'Usage: RESULT = HDF_SD_ATTDIR(HDFID, VARNAME, ATTNAME)'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'
if (n_elements(varname) eq 0) then message, 'Argument VARNAME is undefined'
if (n_elements(attname) eq 0) then message, 'Argument ATTNAME is undefined'

;- Set default return values
name = ''
type = ''
data = -1

;- Get attribute information
if (keyword_set(global)) then begin

  ;- Get information about a global attribute
  attindex = hdf_sd_attrfind(hdfid, attname)
  if (attindex ge 0) then hdf_sd_attrinfo, hdfid, attindex, $
    name=name, type=type, data=data
      
endif else begin

  ;- Get information about a variable attribute
  varindex = hdf_sd_nametoindex(hdfid, varname)
  if (varindex ge 0) then begin
    varid = hdf_sd_select(hdfid, varindex)
    attindex = hdf_sd_attrfind(varid, attname)
    if (attindex ge 0) then hdf_sd_attrinfo, varid, attindex, $
      name=name, type=type, data=data
    hdf_sd_endaccess, varid
  endif
  
endelse

;- Return result to caller
return, {name:name, type:type, data:data}

END
