FUNCTION HDF_VD_VDATALIST, HDFID, NULLCLASS=NULLCLASS

;+
; NAME:
;    HDF_VD_VDATALIST
;
; PURPOSE:
;    Return the number, names, and class names of all Vdatas in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = HDF_VD_VDATALIST(HDFID)
;
; INPUTS:
;    HDFID       Identifier of HDF file opened by caller with HDF_OPEN.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    NULLCLASS    If set, only returns information about Vdatas which have
;                 null class names. (i.e. class name is the null string '').
;
; OUTPUTS:
;    An anonymous structure containing the number of Vdatas,
;    the name of each Vdata, and the class name of each Vdata in the file.
;    The fields in the structure are as follows:
;    NVDATAS       Number of Vdatas in the file (0 if none were found).
;    VDATANAMES    Array of Vdata names ('' if none were found).
;    CLASSNAMES    Array of class names ('' if none were found).
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
;hdfid = hdf_open(file)
;result = hdf_vd_vdatalist(hdfid)
;hdf_close, hdfid
;help, result, /structure
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_vd_vdatalist.pro,v 1.1 2000/01/04 22:22:11 gumley Exp $
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

rcs_id = '$Id: hdf_vd_vdatalist.pro,v 1.1 2000/01/04 22:22:11 gumley Exp $'

;- Check arguments
if (n_params() ne 1) then message, 'Usage: RESULT = HDF_SD_VDATALIST(HDFID)'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'

;- Set default return values
nvdatas = 0L
vdatanames = ''
classnames = ''

;- Create name storage array
maxnames = 100000L
namelist = strarr(maxnames)
classlist = strarr(maxnames)

;- Loop over all vdatas
lastid = -1
thisid = 0
while (thisid ge 0) do begin

  ;- Select next vdata
  thisid = hdf_vd_getid(hdfid, lastid)
  lastid = thisid
  
  ;- If vdata is valid, get vdata name
  if (thisid ge 0) then begin
  
    ;- Get the vdata name and class
    vdata = hdf_vd_attach(hdfid, thisid)
    hdf_vd_get, vdata, name=name, class=class
    hdf_vd_detach, vdata
    
    ;- Store the vdata name and class
    if (keyword_set(nullclass) eq 0) or $
       ((keyword_set(nullclass) eq 1) and (class eq '')) then begin
      namelist[nvdatas] = name
      classlist[nvdatas] = class
      nvdatas = nvdatas + 1L
    endif
    
    ;- Check maximum number of vdata names                      
    if (nvdatas gt maxnames) then message, 'MAXNAMES exceeded'
    
  endif
  
endwhile

;- Extract result arrays
if (nvdatas gt 0) then begin
  vdatanames = namelist[0 : nvdatas - 1]
  classnames = classlist[0 : nvdatas - 1]
endif

;- Return the result
return, {nvdatas:nvdatas, vdatanames:vdatanames, classnames:classnames}

END
