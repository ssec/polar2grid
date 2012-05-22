FUNCTION HDF_SD_ATTLIST, HDFID, VARNAME, GLOBAL=GLOBAL

;+
; NAME:
;    HDF_SD_ATTLIST
;
; PURPOSE:
;    Return the number and names of all attributes associated with
;    an individual Scientific Data Set (SDS) variable in a HDF file,
;    or the number and names of all global attributes in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = HDF_SD_ATTLIST(HDFID, VARNAME)
;
; INPUTS:
;    HDFID       Identifier of HDF file opened by caller with HDF_SD_START.
;    VARNAME     Name of variable to examine (ignored if GLOBAL keyword set).
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    GLOBAL      If set, global attribute information is returned.
;
; OUTPUTS:
;    An anonymous structure containing the number of attributes,
;    and the name of each attribute.
;    The fields in the structure are as follows:
;    NATTS       Number of attributes
;                (0 if none were found).
;    ATTNAMES    Array of attribute names
;                ('' if none were found, or variable was not found).
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
;result = hdf_sd_attlist(hdfid, '', /global)
;help, result, /structure
;result = hdf_sd_attlist(hdfid, '2D integer array')
;help, result, /structure
;hdf_sd_end, hdfid
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_sd_attlist.pro,v 1.2 1999/12/29 22:35:54 gumley Exp $
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

rcs_id = '$Id: hdf_sd_attlist.pro,v 1.2 1999/12/29 22:35:54 gumley Exp $'

;- Check arguments
if (n_params() ne 2) then message, 'Usage: RESULT = HDF_SD_ATTDIR(HDFID, VARNAME)'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'
if (n_elements(varname) eq 0) then message, 'Argument VARNAME is undefined'

;- Set default return values
natts = 0
attnames = ''

;- Get attribute information
if (keyword_set(global)) then begin

  ;- Get number of global attributes
  hdf_sd_fileinfo, hdfid, nvars, natts
  
endif else begin

  ;- Get number of variable attributes
  varindex = hdf_sd_nametoindex(hdfid, varname)
  if (varindex ge 0) then begin
    varid = hdf_sd_select(hdfid, varindex)
    hdf_sd_getinfo, varid, natts=natts
  endif
  
endelse

;- If attributes were found, get attribute names
if (natts gt 0) then begin

  attnames = strarr(natts)
  for index = 0, natts - 1 do begin

    if (keyword_set(global)) then begin
  
      ;- Get name of global attribute
      hdf_sd_attrinfo, hdfid, index, name=name
      
    endif else begin
    
      ;- Get name of variable attribute
      if (varindex ge 0) then hdf_sd_attrinfo, varid, index, name=name
      
    endelse

    attnames[index] = name

  endfor

endif

;- End access to this variable if necessary
if (keyword_set(global) eq 0) then begin
  if (varindex ge 0) then hdf_sd_endaccess, varid
endif

;- Return result to caller
return, {natts:natts, attnames:attnames}

END
