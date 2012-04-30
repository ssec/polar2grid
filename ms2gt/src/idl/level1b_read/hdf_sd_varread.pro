PRO HDF_SD_VARREAD, HDFID, VARNAME, DATA, _EXTRA=EXTRA_KEYWORDS

;+
; NAME:
;    HDF_SD_VARREAD
;
; PURPOSE:
;    Read data from a Scientific Data Set (SDS) variable
;    in a HDF file.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    HDF_SD_VARREAD, HDFID, VARNAME, DATA
;
; INPUTS:
;    HDFID       Identifier of HDF file opened by caller with HDF_SD_START.
;    VARNAME     Name of Scientific Data Set variable.
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    START       Set this keyword to a vector containing the start position
;                for the read in each dimension
;                (default start position is [0, 0, ..., 0]).
;    COUNT       Set this keyword to a vector containing the number of items
;                to be read in each dimension
;                (default is to read all available data).
;    STRIDE      Set this keyword to a vector containing the sampling interval
;                along each dimension
;                (default stride vector for a contiguous read is [0, 0, ..., 0]).
;    NOREVERSE   Set the keyword to retrieve the data without transposing the
;                data from column to row order.
;
; OUTPUTS:
;    DATA        Named variable in which data will be returned
;                (degenerate dimensions are removed).
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
;hdf_sd_varread, hdfid, '2D integer array', data
;hdf_sd_end, hdfid
;help, data
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: hdf_sd_varread.pro,v 1.2 2000/01/05 18:10:55 gumley Exp $
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

rcs_id = '$Id: hdf_sd_varread.pro,v 1.2 2000/01/05 18:10:55 gumley Exp $'

;- Check arguments
if (n_params() ne 3) then message, 'Usage: HDF_SD_VARREAD, HDFID, VARNAME, DATA'
if (n_elements(hdfid) eq 0) then message, 'Argument HDFID is undefined'
if (n_elements(varname) eq 0) then message, 'Argument VARNAME is undefined'
if (arg_present(data) eq 0) then message, 'Argument VARDATA cannot be modified'

;- Get index for this variable
index = hdf_sd_nametoindex(hdfid, varname)
if (index eq -1) then $
  message, string(varname, format='("VARNAME not found: ", a)')

;- Select the variable and read the data
varid = hdf_sd_select(hdfid, index)
hdf_sd_getdata, varid, data, _extra=extra_keywords
hdf_sd_endaccess, varid
data = reform(temporary(data))

END
