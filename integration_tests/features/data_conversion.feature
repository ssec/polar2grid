Feature: Testing data conversions
    This takes test data and runs it through the command provided for Polar2Grid. 
    It then compares the new data with the expected output. 


    Scenario Outline: Data conversion
        Given input data from <source>
        When <command> runs
        Then the output matches with the files in <output>

   # test data located in /data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data/
   Examples: ACSPO
       | source            | command                            | output             |
       | acspo/input/test1 | acspo gtiff -vv --grid-coverage=0.0 -f | acspo/output/test1 |
       | acspo/input/test2 | acspo gtiff -vv --grid-coverage=0.0 -f | acspo/output/test2 |


   Examples: AMSR2_L1B
       | source            | command                                                | output             |
       | amsr2/input/test1 | amsr2_l1b awips -vv -g 211e -p btemp_36.5h btemp_89.0av -f | amsr2/output/test1 |


   Examples: AVHRR
       | source            | command         | output             |
       | avhrr/input/test1 | avhrr gtiff -vv -f  | avhrr/output/test1 |                                       


#   Examples: MIRS
#       | source           | command                                | output            |
#       | mirs/input/test1 | mirs awips -vv -p tpw --grid-coverage=0 -f | mirs/output/test1 |


  Examples: MODIS
      | source            | command                                                                                                                           | output             |
      | modis/input/test1 | crefl gtiff -vv --true-color --false-color --fornav-D 10 --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f | modis/output/test1 |
    # tol | modis/l1b/a1.17067.1818.1000m.hdf modis/l1b/a1.17067.1818.250m.hdf modis/l1b/a1.17067.1818.500m.hdf modis/l1b/a1.17067.1818.geo.hdf |modis awips -g 211e -f | modis/awips |
    # tol |modis/l1b/MOD021KM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02QKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD02HKM.A2017004.1732.005.2017023210017.hdf modis/l1b/MOD03.A2017004.1732.005.2017023210017.hdf |crefl awips --fornav-D 10 -g 211e --true-color --false-color --grid-coverage=0 -f |modis/awips1|
    # tol | modis/l1b/a1.17006.1855.1000m.hdf modis/l1b/a1.17006.1855.250m.hdf modis/l1b/a1.17006.1855.500m.hdf modis/l1b/a1.17006.1855.geo.hdf |crefl awips --true-color --false-color --fornav-D 10 -g 211e -f | modis/awips2 |


  Examples: VIIRS
      | source            | command                                                                                                              | output             |
      | viirs/input/test1 | crefl gtiff -vv --true-color --false-color --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | viirs/output/test1 |
    # tol | viirs_sdr_day/aoml         | crefl gtiff -g lcc_fit -f                                             | viirs_sdr_day/output_tiff       |


    Examples: VIIRS_L1B
       | source                      | command | output |
      # tol |viirs_l1b_day/l1b  |viirs_l1b awips -g 211e 211w -p adaptive_dnb dynamic_dnb --night-fraction=0.4 -f |viirs_l1b_day/awips   |
       | viirs_l1b_night/input/test1 | viirs_l1b gtiff -vv --grid-configs /data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data/viirs_l1b_night/input/test1/my_grid.conf -g polar_europe -p adaptive_dnb dynamic_dnb histogram_dnb hncc_dnb -f  | viirs_l1b_night/output/test1  |    


    Examples: VIIRS_SDR
       | source                      | command                                                            | output                       |
       | viirs_sdr_day/input/test1/  | viirs_sdr gtiff -vv --i-bands --m-bands -p adaptive_dnb dynamic_dnb -f | viirs_sdr_day/output/test1   |
       # tol, remove hist (could not produce)  |viirs_sdr_night/sdr|viirs_sdr awips -g 211e -p adaptive_dnb dynamic_dnb -f|viirs_sdr_night/output_awips|
       | viirs_sdr_day/input/test2   | viirs_sdr gtiff -vv -f                                                 | viirs_sdr_day/output/test2   |
       | viirs_sdr_night/input/test1 | viirs_sdr gtiff -vv -p adaptive_dnb dynamic_dnb -f                     | viirs_sdr_night/output/test1 | 

