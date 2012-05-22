PRO HDF_VD_VDATAREAD, HDFID, VDATANAME, FIELDNAME, DATA

;+
; NAME:
;    HDF_VD_VDATAREAD
;
; PURPOSE:
;    Read data from a Vdata field in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    HDF_VD_VDATAREAD, HDFID, VDATANAME, FIELDNAME, DATA
;
; INPUTS:
;    HDFID        Identifier of HDF file opened by caller with HDF_OPEN.
;    VDATANAME    Name of the Vdata.
;    FIELDNAME    Name of the field within the Vdata.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    None.
;
; OUTPUTS:
;    DATA        Named variable in which all data will be returned
;                (all records are read from the field).
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
;hdf_vd_vdataread, hdfid, 'Vdata with mixed types', 'Float', data
;hdf_close, hdfid
;help, data
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_vd_vdataread.pro,v 1.1 2000/01/05 17:54:46 gumley Exp $
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

rcs_id = '$Id: hdf_vd_vdataread.pro,v 1.1 2000/01/05 17:54:46 gumley Exp $'

;- Check arguments
if (n_params() ne 4) then $
  message, 'Usage: HDF_VD_VDATAREAD, HDFID, VDATANAME, FIELDNAME, DATA'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'
if (n_elements(vdataname) eq 0) then message, 'Argument VDATANAME is undefined'
if (n_elements(fieldname) eq 0) then message, 'Argument FIELDNAME is undefined'
if (arg_present(data) eq 0) then message, 'Argument DATA cannot be modified'

;- Get index for the vdata
index = hdf_vd_find(hdfid, vdataname)
if (index eq 0) then message, $
  string(vdataname, format='("VDATANAME not found: ", a)')

;- Attach to the vdata
vdataid = hdf_vd_attach(hdfid, index)

;- Check that fieldname exists in this vdata
if (hdf_vd_fexist(vdataid, fieldname) ne 1) then begin
  hdf_vd_detach, vdataid
  message, string(fieldname, format='("FIELDNAME not found: ", a)')
endif

;- Read all records from the field
nread = hdf_vd_read(vdataid, data, fields=fieldname)

;- Detach from the vdata
hdf_vd_detach, vdataid

END
