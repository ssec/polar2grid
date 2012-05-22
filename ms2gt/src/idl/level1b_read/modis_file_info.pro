FUNCTION MODIS_FILE_INFO, FILENAME, META_NAMES=META_NAMES, QUIET=QUIET

;+
; NAME:
;    MODIS_FILE_INFO
;
; PURPOSE:
;    Return information about a MODIS HDF product file, including file
;    status (exist/read/write/size), and selected ECS metadata parameters.
;    The ECS core and archive metadata are searched for named parameters.
;
; CATEGORY:
;    HDF utilities.
;
; CALLING SEQUENCE:
;    RESULT = MODIS_FILE_INFO(FILENAME)
;
; INPUTS:
;    FILENAME    Name of file
;
; OPTIONAL INPUTS:
;    None.
;
; KEYWORD PARAMETERS:
;    META_NAMES     String array containing names of metadata parameters
;                   to be read from the file
;                   (default values are used if this keyword is not set).
;    QUIET          If set to true (1), no warning messages are printed
;                   (default is to print warning messages).
;
; OUTPUTS:
;    An anonymous structure containing information about the file.
;    The fields in the structure are as follows:
;    NAME           String containing the name of the file
;                   (any environment variables in the path are expanded).
;    EXIST          1 if file exists, 0 otherwise.
;    READ           1 if file can be read, 0 otherwise.
;    WRITE          1 if file can be written, 0 otherwise.
;    SIZE           File size in bytes
;                   (-1 if file does not exist, or if file cannot be read).
;    NVARS          Number of HDF SDS variables in the file.
;    NGATTS         Number of HDF global attributes in the file.
;    NVDATAS        Number of HDF vdatas in the file.
;    NMETA          Number of metadata parameters read from the file.
;    VAR_NAMES      String array of SDS variables names in file
;                   ('' if no SDS variables were found).
;    GATT_NAMES     String array of global attribute names in file
;                   ('' if no global attributes were found).
;    VDATA_NAMES    String array of vdata names in file
;                   ('' if no vdatas were found).
;    META_NAMES     String array containing names of metadata parameters
;                   read from the file.
;    META_VALUES    String array containing values of metadata parameters
;                   read from the file
;                   (if parameter was not found, corresponding element is '').
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
;result = modis_file_info(filename)
;help, result, /structure
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: modis_file_info.pro,v 1.5 2000/01/25 17:26:42 gumley Exp $
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

rcs_id = '$Id: modis_file_info.pro,v 1.5 2000/01/25 17:26:42 gumley Exp $'

;-------------------------------------------------------------------------------
;- CHECK INPUT
;-------------------------------------------------------------------------------

;- Check arguments
if (n_params() eq 0) then message, 'Usage: RESULT = MODIS_L1B_INFO(FILENAME)'
if (n_elements(filename) eq 0) then message, 'Argument FILENAME is undefined'
if (n_elements(meta_names) eq 0) then begin
  meta_names = [$
    'LOCALGRANULEID', $
    'PRODUCTIONDATETIME', $
    'DAYNIGHTFLAG', $
    'ORBITNUMBER', $
    'SHORTNAME', $                
    'GRINGPOINTLONGITUDE', $
    'GRINGPOINTLATITUDE', $
    'RANGEENDINGDATE', $
    'RANGEENDINGTIME', $
    'RANGEBEGINNINGDATE', $
    'RANGEBEGINNINGTIME', $
    'PGEVERSION', $
    'ASSOCIATEDPLATFORMSHORTNAME', $
    'ASSOCIATEDINSTRUMENTSHORTNAME']
endif

;-------------------------------------------------------------------------------
;- GET FILE INFORMATION
;-------------------------------------------------------------------------------

;- Set default return value
result = {$
  name    : '', $
  exist   : 0L, $
  read    : 0L, $
  write   : 0L, $
  size    :-1L, $
  nvars   : 0L, $
  ngatts  : 0L, $
  nvdatas : 0L, $
  nmeta   : 0L}

;- Get file information
finfo = fileinfo(filename)
if (finfo.exist eq 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'File does not exist', /continue
  return, result
endif

;- Copy file information into result
result.name  = finfo.name
result.exist = finfo.exist
result.read  = finfo.read
result.write = finfo.write
result.size  = finfo.size

;- Return if file cannot be read
if (finfo.read eq 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'File cannot be read', /continue
  return, result
endif

;- Return if file is not HDF
if (finfo.hdf eq 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'File is not HDF: ' + filename, /continue
  return, result
endif

;-------------------------------------------------------------------------------
;- GET HDF INFORMATION
;-------------------------------------------------------------------------------

;- Get list of vdatas in file
hdf_id = hdf_open(result.name, /read)
vdatalist = hdf_vd_vdatalist(hdf_id)
hdf_close, hdf_id

;- Open the file in SDS mode
sd_id = hdf_sd_start(result.name, /read)

;- Get list of variables in the file
varlist = hdf_sd_varlist(sd_id)
if (varlist.nvars eq 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'No HDF SDS variables found: ' + filename,  /continue
  return, result
endif

;- Get list of global attributes
gattlist = hdf_sd_attlist(sd_id, '', /global)
if (gattlist.natts eq 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'No HDF global attributes found: ' + filename, /continue
  return, result
endif

;- Save number of variables, global attributes, and vdatas
result.nvars   = varlist.nvars
result.ngatts  = gattlist.natts
result.nvdatas = vdatalist.nvdatas 

;- Append variable, global attribute, and vdata names to output structure
result = create_struct(result, 'var_names', varlist.varnames, $
  'gatt_names', gattlist.attnames, 'vdata_names', vdatalist.vdatanames)

;-------------------------------------------------------------------------------
;- SEARCH CORE METADATA FOR PARAMETERS
;-------------------------------------------------------------------------------

;- Check that core metadata attribute exists
core_name = 'CoreMetadata.0'
loc = where(gattlist.attnames eq core_name, core_count)
if (core_count eq 0) then begin
  if (keyword_set(quiet) ne 1) then $
    message, 'Core metadata not found: ' + filename, /continue
  return, result
endif

;- Read core metadata
gattinfo = hdf_sd_attinfo(sd_id, '', core_name, /global)
core_info = gattinfo.data

;- Extract core metadata items
meta_values = strarr(n_elements(meta_names))
for index = 0, n_elements(meta_names) - 1 do begin
  meta_values[index] = get_metadata(core_info, meta_names[index], $
    quiet=keyword_set(quiet))
endfor

;-------------------------------------------------------------------------------
;- SEARCH ARCHIVE METADATA FOR ANY PARAMETERS NOT FOUND IN CORE METADATA
;-------------------------------------------------------------------------------

loc = where(meta_values eq '', meta_missing)
if (meta_missing gt 0) then begin

  ;- Check that archive metadata attribute exists
  arch_name = 'ArchiveMetadata.0'
  loc = where(gattlist.attnames eq arch_name, arch_count)
  if (arch_count eq 0) then begin
    if (keyword_set(quiet) ne 1) then $
      message, 'Archive metadata not found: ' + filename, /continue
    return, result
  endif

  ;- Read archive metadata
  gattinfo = hdf_sd_attinfo(sd_id, '', arch_name, /global)
  arch_info = gattinfo.data

  ;- Extract archive metadata items
  for index = 0, n_elements(meta_names) - 1 do begin
    if (meta_values[index] eq '') then $
      meta_values[index] = get_metadata(arch_info, meta_names[index], $
      quiet=keyword_set(quiet))
  endfor

endif

;-------------------------------------------------------------------------------
;- CLEAN UP AND EXIT
;-------------------------------------------------------------------------------

;- Save number of metadata parameters found
loc = where(meta_values ne '', nmeta)
result.nmeta = nmeta

;- Append metadata parameter names and values to output structure
result = create_struct(result, 'meta_names', meta_names, $
  'meta_values', meta_values)

;- Close the file in SDS mode
hdf_sd_end, sd_id

;- Return result to caller
return, result

END
