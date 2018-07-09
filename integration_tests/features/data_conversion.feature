Feature: Testing data conversions
    This takes test data and runs it through the command provided for Polar2Grid. 
    It then compares the new data with the expected output. 


    Scenario Outline: Data conversion
        Given input data from <source>
        When <command> runs
        Then the output matches with the files in <output>

   # test data located in /data/users/kathys/test_data/ 
  `    
   Examples: MODIS
       | source                         | command                                                                                                                           | output                          |
       | ../polar2grid_test/modis/input | crefl gtiff --true-color --false-color --fornav-D 10 --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f | ../polar2grid_test/modis/output |


   Examples: VIIRS
       | source                           | command                                                                                                              | output                          |
       | ../polar2grid_test/viirs/input   | crefl gtiff --true-color --false-color --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | ../polar2grid_test/viirs/output |
       | viirs_sdr_day/aoml               | crefl gtiff -g lcc_fit -f                                                                                            | viirs_sdr_day/output_tiff       |


    Examples: CLAVR-X
       | source                                                                        | command                        | output        |
       | clavrx/noaa19/day/data/clavrx_hrpt_noaa19_20170520_2212_42682.l1b.level2.hdf  | clarvx scmi --sector-id LCC -f | clavrx/newp2g |    
        
