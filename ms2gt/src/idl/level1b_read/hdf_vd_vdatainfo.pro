FUNCTION HDF_VD_VDATAINFO, HDFID, VDATANAME

;+
; NAME:
;    HDF_VD_VDATAINFO
;
; PURPOSE:
;    Return information about a Vdata in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = HDF_VD_VDATAINFO(HDFID, VDATANAME)
;
; INPUTS:
;    HDFID        Identifier of HDF file opened by caller with HDF_OPEN.
;    VDATANAME    Name of Vdata.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    None.
;
; OUTPUTS:
;    An anonymous structure containing information about the Vdata.
;    The fields in the structure are as follows:
;    NAME          Name of the Vdata ('' if Vdata not found).
;    NFIELDS       Number of fields (-1 if Vdata not found).
;    FIELDNAMES    Array of field names ('' if Vdata not found).
;    NRECORDS      Number of records (-1 if Vdata not found).
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
;result = hdf_vd_vdatainfo(hdfid, 'Vdata with mixed types')
;hdf_close, hdfid
;help, result, /structure
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_vd_vdatainfo.pro,v 1.2 2000/01/05 15:53:21 gumley Exp $
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

rcs_id = '$Id: hdf_vd_vdatainfo.pro,v 1.2 2000/01/05 15:53:21 gumley Exp $'

;- Check arguments
if (n_params() ne 2) then message, 'Usage: RESULT = HDF_SD_VDATAINFO(HDFID, VDATANAME)'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'
if (n_elements(vdataname) eq 0) then message, 'Argument VDATANAME is undefined'

;- Set default return values
name = ''
nfields = -1
fieldnames = ''
nrecords = -1

;- Get the index for the vdata
index = hdf_vd_find(hdfid, vdataname)

;- If the vdata is valid, get vdata information
if (index gt 0) then begin

  ;- Attach to the vdata
  vdataid = hdf_vd_attach(hdfid, index)
  
  ;- Get information
  hdf_vd_get, vdataid, name=name, nfields=nfields, fields=fields, count=nrecords

  ;- Detach from the vdata
  hdf_vd_detach, vdataid
  
  ;- Convert field name string to array
  fieldnames = str_sep(fields, ',', /trim)
    
endif

;- Return result to caller
return, {name:name, nfields:nfields, fieldnames:fieldnames, nrecords:nrecords}

END
