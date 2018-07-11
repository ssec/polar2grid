Feature: Testing data conversions
    This takes test data and runs it through the command provided for Polar2Grid. 
    It then compares the new data with the expected output. 


    Scenario Outline: Data conversion
        Given input data from <source>
        When <command> runs
        Then the output matches with the files in <output>

   # test data located in /data/users/kathys/test_data/ 
   Examples: ACSPO
       |source|command|output|

   Examples: AMSR2_L1B
       | source | command | output |
       | amsr2/data/GW1AM2_201607191903_137A_L1DLBTBR_1110110.h5 | amsr2_l1b awips  -g 211e -p  btemp_36.5h btemp_89.0av -f | amsr2/awips |

   Examples: AVHRR
       | source             | command            |  output            |
       | avhrr/metopa/input | avhrr gtiff -f     | avhrr/metopa/gtiff |                                       

   Examples: CLAVR-X
       | source                                                                        | command                                                                                            | output       |

   Examples: MIRS
       | source | command | output |
       #SEMI-WORKS (remove rain_rate)| mirs/input/IMG_SX.M2.D17037.S1601.E1607.B0000001.WE.HR.ORB.nc | mirs awips -vv -p surface_type tpw rain_rate --grid-coverage=0 -f | mirs/awips1    |

   Examples: MODIS
       | source                         | command                                                                                                                           | output                          |
       | ../polar2grid_test/modis/input | crefl gtiff --true-color --false-color --fornav-D 10 --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f | ../polar2grid_test/modis/output |
    #semi-works needs tolerances | modis/l1b/a1.17067.1818.1000m.hdf modis/l1b/a1.17067.1818.250m.hdf modis/l1b/a1.17067.1818.500m.hdf modis/l1b/a1.17067.1818.geo.hdf |modis awips -g 211e -f | modis/awips |
       #semi-works (needs tolerances)  |modis/l1b/MOD021KM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02QKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02HKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD03.A2017004.1732.005.2017023210017.hdf |crefl awips --fornav-D 10 -g 211e --true-color --false-color --grid-coverage=0 -f |modis/awips1|
      #needs tolerances | modis/l1b/a1.17006.1855.1000m.hdf modis/l1b/a1.17006.1855.250m.hdf modis/l1b/a1.17006.1855.500m.hdf modis/l1b/a1.17006.1855.geo.hdf |crefl awips --true-color --false-color --fornav-D 10 -g 211e -f | modis/awips2 |
 
   Examples: VIIRS
       | source                           | command                                                                                                              | output                          |
       | ../polar2grid_test/viirs/input   | crefl gtiff --true-color --false-color --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | ../polar2grid_test/viirs/output |
     #needs tolerances | viirs_sdr_day/aoml         | crefl gtiff -g lcc_fit -f                                             | viirs_sdr_day/output_tiff       |


    Examples: VIIRS-L1B
       | source               | command          | output |
      #almost works needs tolerances |viirs_l1b_day/l1b  |viirs_l1b awips -g 211e 211w -p adaptive_dnb dynamic_dnb --night-fraction=0.4 -f |viirs_l1b_day/awips   |
       | viirs_l1b_night/data/*.nc    | viirs_l1b gtiff --grid-configs /data/users/kathys/test_data/viirs_l1b_night/run/my_grid.conf -g polar_europe -p adaptive_dnb dynamic_dnb histogram_dnb hncc_dnb -f  | viirs_l1b_night/run  |    


    Examples: VIIRS_SDR
       |source|command|output|
      #works except for hncc file in the output dir | viirs_sdr_day/sdr1/|viirs_sdr gtiff --i-bands --m-bands -p adaptive_dnb dynamic_dnb -f |viirs_sdr_day |
       #needs tolerances |viirs_sdr_night/sdr|viirs_sdr awips -g 211e -p adaptive_dnb dynamic_dnb -f|viirs_sdr_night/output_awips|
       #no histogram, needs tolerances |viirs_sdr_day/sdr|viirs_sdr awips -g 211e 211w -f|viirs_sdr_day/output_awips|
       |viirs_sdr_night/sdr|viirs_sdr gtiff -p adaptive_dnb dynamic_dnb -f  | viirs_sdr_night/output_tiff  | 
     
  
