FUNCTION GET_METADATA, PVLSTRING, OBJSTRING, QUIET=QUIET

;+
; DESCRIPTION:
;    Extract the value for PVL object from a PVL string.
;
;    In EOS HDF product files, a PVL string is a global attribute
;    (e.g. CoreMetadata.0) which contains PVL formatted metadata.
;
;    A PVL object is an entry within the PVL formatted metadata.
;    For example, the object RANGEENDINGDATE appears as follows in
;    the global attribute CoreMetadata.0 in MODIS Level-1B files:
;
;    OBJECT     = RANGEENDINGDATE
;      NUM_VAL  = 1
;      VALUE    = 2000-04-24
;    END_OBJECT = RANGEENDINGDATE
;
;    The purpose of this function is to return the VALUE, which in this
;    is 2000-04-24.
;
; USAGE:
;    RESULT = GET_METADATA(PVLSTRING, OBJSTRING)
;
; INPUT PARAMETERS:
;    PVLSTRING    String containing PVL formatted metadata
;    OBJSTRING    String containing the name of the PVL object to extract
;
; KEYWORD PARAMETERS:
;    QUIET        If set, do not print warning messages when an OBJECT
;                 is not found (default is to print a warning when an
;                 object is not found)
;
; OUTPUT PARAMETERS:
;    RESULT       String containing the PVL object VALUE
;
; EXAMPLE:
;    Requires the HDF_SD_ATTINFO function.
;
;; Read a global attribute containing global metadata
;file = 'MOD021KM.A2000115.1710.002.2000119195542.hdf'
;hdfid = hdf_sd_start(file)
;info = hdf_sd_attinfo(hdfid, '', 'CoreMetadata.0', /global)
;hdf_sd_end, hdfid
;
;; Extract a PVL object
;pvlstring = info.data
;objstring = 'RANGEBEGINNINGDATE'
;result = get_metadata(pvlstring, objstring)
;print, result
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: get_metadata.pro,v 1.4 2000/05/03 18:29:11 gumley Exp $
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

rcs_id = '$Id: get_metadata.pro,v 1.4 2000/05/03 18:29:11 gumley Exp $'

;- Check arguments
if (n_params() ne 2) then $
  message, 'Usage: RESULT = GET_METADATA(PVLSTRING, OBJECT)'
if (n_elements(pvlstring) eq 0) then message, 'Argument PVLSTRING is undefined'
if (n_elements(objstring) eq 0) then message, 'Argument OBJSTRING is undefined'
if (objstring[0] eq '') then message, 'OBJSTRING cannot be a null string'

;- Locate beginning of PVL object
begpos = strpos(pvlstring[0], objstring[0])
if (begpos lt 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'PVL object not found: ' + object, /continue
  return, ''
endif

;- Locate start of value record
valpos = strpos(pvlstring[0], 'VALUE', begpos)

;- Locate end of object
endpos = strpos(pvlstring[0], 'END_OBJECT', valpos)

;- Extract value entry with last character removed
value = strcompress(strmid(pvlstring[0], valpos, endpos - valpos))
value = strmid(value, 0, strlen(value) - 2)

;- Extract all characters following '='
eqlpos = strpos(value, '=')
value = strmid(value, eqlpos + 1)

;- Remove leading and trailing blanks
value = strtrim(value, 2)

;- If first character is " or (, remove it
len = strlen(value)
chr = strmid(value, 0, 1)
if (chr eq '"') or (chr eq '(') then value = strmid(value, 1, len - 1)

;- If last character is " or ), remove it
len = strlen(value)
chr = strmid(value, len - 1, 1)
if (chr eq '"') or (chr eq ')') then value = strmid(value, 0, len - 1)

;- Return value to caller
return, value

END
