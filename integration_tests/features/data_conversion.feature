Feature: Testing data conversions
    This takes test data and runs it through the command provided for Polar2Grid. 
    It then compares the new data with the expected output. 


    Scenario Outline: Data conversion
        Given input data from <source>
        When <command> runs
        Then the output matches with the files in <output>

   # test data located in /data/users/kathys/test_data/ 
      
   Examples: MODIS
       | source                         | command                                                                                                                           | output                          |
       | ../polar2grid_test/modis/input | crefl gtiff --true-color --false-color --fornav-D 10 --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f | ../polar2grid_test/modis/output |
    #semi-works needs tolerances | modis/l1b/a1.17067.1818.1000m.hdf modis/l1b/a1.17067.1818.250m.hdf modis/l1b/a1.17067.1818.500m.hdf modis/l1b/a1.17067.1818.geo.hdf |modis awips -g 211e -f | modis/awips |
    # | modis/l1b/a1.17067.1818.1000m.hdf modis/l1b/a1.17067.1818.250m.hdf modis/l1b/a1.17067.1818.500m.hdf modis/l1b/a1.17067.1818.geo.hdf |crefl gtiff --true-color --false-color --fornav-D 10 -g lcc_conus_300 -f | modis/new_gtiff |
      # | modis/l1b/a1.17067.1818.1000m.hdf modis/l1b/a1.17067.1818.250m.hdf modis/l1b/a1.17067.1818.500m.hdf modis/l1b/a1.17067.1818.geo.hdf |modis scmi -p bt27 vis02 --sector-id LCC --letters --compress -g lcc_conus_1km -f | modis/new_awips_scmi |
       #semi-works (needs tolerances)  |modis/l1b/MOD021KM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02QKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02HKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD03.A2017004.1732.005.2017023210017.hdf |crefl awips --fornav-D 10 -g 211e --true-color --false-color --grid-coverage=0 -f |modis/awips1|
      #needs tolerances | modis/l1b/a1.17006.1855.1000m.hdf modis/l1b/a1.17006.1855.250m.hdf modis/l1b/a1.17006.1855.500m.hdf modis/l1b/a1.17006.1855.geo.hdf |crefl awips --true-color --false-color --fornav-D 10 -g 211e -f | modis/awips2 |

      # |modis/l1b/MOD021KM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02QKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02HKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD03.A2017004.1732.005.2017023210017.hdf |crefl gtiff -gwgs84_fit_250 --fornav-D 10 --true-color --false-color -f |modis/crefl1|

   Examples: VIIRS_SDR
       |source|command|output|
       # all but hncc work | viirs_sdr_day/sdr1/|viirs_sdr gtiff -f |viirs_sdr_day |
       #|viirs_sdr_day/sdr|crefl awips --false-color --grid-coverage=0 -g 211e -f|viirs_sdr_day/awips|
       #|viirs_sdr_day/sdr|crefl awips --true-color --false-color --grid-coverage=0 -g 211w -f|viirs_sdr_day/crefl|
       #|viirs_sdr_day/sdr|viirs_sdr hdf5 --m-bands -f|viirs_sdr_day/h5|
       #|viirs_sdr_day/sdr1|crefl gtiff --true-color --false-color -f|viirs_sdr_day/merge1|
       #|viirs_sdr_day/sdr2|viirs gtiff -f|viirs_sdr_day/merge2|
       #needs tolerances |viirs_sdr_night/sdr|viirs_sdr awips -g 211e -p adaptive_dnb dynamic_dnb -f|viirs_sdr_night/output_awips|
       #no histogram, needs tolerances |viirs_sdr_day/sdr|viirs_sdr awips -g 211e 211w -f|viirs_sdr_day/output_awips|
       #WORKS |viirs_sdr_night/sdr|viirs_sdr gtiff -p adaptive_dnb dynamic_dnb -f  | viirs_sdr_night/output_tiff  | 





   Examples: VIIRS
       | source                           | command                                                                                                              | output                          |
      | ../polar2grid_test/viirs/input   | crefl gtiff --true-color --false-color --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | ../polar2grid_test/viirs/output |
     #needs tolerances | viirs_sdr_day/aoml               | crefl gtiff -g lcc_fit -f                                                                                            | viirs_sdr_day/output_tiff       |


    Examples: CLAVR-X
      | source                                                                        | command                                                                                            | output       |
     #  | clavrx/noaa19/day/data/clavrx_hrpt_noaa19_20170520_2212_42682.l1b.level2.hdf  | clavrx scmi --sector-id LCC -g lcc_conus_300 --compress --letters -p cloud_type cld_height_acha -f | clavrx/awips |    
    #  |clavrx/noaa19/day/data/clavrx_hrpt_noaa19_20170520_2212_42682.l1b.level2.hdf|clavrx scmi --sector-id LCC -g lcc_conus_300 --compress --letters -p cloud_type cld_temp_acha cld_height_acha -f|clavrx/newp2g|

       
    Examples: VIIRS-L1B
       | source               | command          | output |
      # | viirs_l1b_night/data | viirs_l1b gtiff -g 
      #almost works needs tolerances |viirs_l1b_day/l1b  |viirs_l1b awips -g 211e 211w -p adaptive_dnb dynamic_dnb --night-fraction=0.4 -f |viirs_l1b_day/awips   |
   # probably works, needs to gen true/false color and the other files at the same time:
   # |  viirs_l1b_day/l1b | viirs_l1b gtiff --true-color --false-color --i-bands --m-bands --products adaptive_dnb hncc_dnb dynamic_dnb histogram_dnb -f  | viirs_l1b_day/gtiff  |
    # WORKS | viirs_l1b_night/data/*.nc    | viirs_l1b gtiff --grid-configs /data/users/kathys/test_data/viirs_l1b_night/run/my_grid.conf -g polar_europe -p adaptive_dnb dynamic_dnb histogram_dnb hncc_dnb -f  | viirs_l1b_night/run  |    


    Examples: AVHRR
       | source                                          | command                                     |  output            |
    #WORKS   | avhrr/metopa/input | avhrr gtiff -f     | avhrr/metopa/gtiff |                                       
     #  | avhrr/noaa19/input/hrpt_noaa19_20170202_2042_41144.l1b | avhrr awips --grid-coverage=0 -g 203 204 -f | avhrr/noaa19/awips |
      # | avhrr/noaa18/input/ | avhrr hdf5 --output-pattern /data/users/kathys/test_data/avhrr/noaa18/hdf5/my_scene.hdf -f | avhrr/noaa18/hdf5 |
    
    Examples: AMSR2_L1B
       | source | command | output |
      #WORKS | amsr2/data/GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5 | amsr2_l1b awips  -g 211e -p  btemp_36.5h btemp_89.0av -f | amsr2/awips |
    
    Examples: MIRS
       | source | command | output |
      # | mirs/input/NPR-MIRS-IMG_v11r1_NPP_s201611111032500_e201611111044016_c201611111121100.nc | mirs awips --bt-channels -g 211e 211w -f    | mirs    |
       #SEMI-WORKS (remove rain_rate)| mirs/input/IMG_SX.M2.D17037.S1601.E1607.B0000001.WE.HR.ORB.nc | mirs awips -vv -p surface_type tpw rain_rate --grid-coverage=0 -f | mirs/awips1    |
      # | mirs/input/IMG_SX.M1.D17037.S1648.E1700.B0000001.WE.HR.ORB.nc | mirs hdf5 --add-geolocation -f | mirs/hdf5    |
       #|mirs/input| mirs gtiff -f|mirs/atms|
     

    Examples: ACSPO
       |source|command|output|
     #  | acspo/noaa18 | acspo hdf5 -p sst sea_ice_fraction --compress lzf --add-geolocation -g lcc_fit --grid-coverage=1.0 -f | acspo/awips|       
      # |amsr2/data/GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5|amsr2_l1b awips -g 211e -vv --rescale-configs /data/users/kathys/CSPP/polar2grid_v_2_2_1/rescale_configs/amsr2_png.ini -f|amsr2/images2|
       #|amsr2/data/GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5|amsr2_l1b gtiff -g lcc_fit -vv --rescale-configs /data/users/kathys/CSPP/polar2grid_v_2_2_1/rescale_configs/amsr2_png.ini -f|amsr2/images3|



