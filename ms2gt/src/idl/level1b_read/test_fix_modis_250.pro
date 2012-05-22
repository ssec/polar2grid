pro test_fix_modis_250
image = indgen(5, 120) * 50
openw, lun, 'unfixed.txt', /get_lun
printf, lun, image
free_lun, lun
image = fix_modis_250(temporary(image))
openw, lun, 'fixed.txt', /get_lun
printf, lun, image
free_lun, lun
end
