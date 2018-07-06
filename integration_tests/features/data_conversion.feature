Feature: Testing data conversions
    This takes test data and runs it through the command provided for Polar2Grid. 
    It then compares the new data with the expected output. 


    Scenario Outline: Data conversion
        Given input data from <folder>
        When <command> runs
        Then the output matches with the verified files

   Examples: MODIS
       | folder  | command                                                                                                                            | 
       | modis   | crefl gtiff --true-color --false-color --fornav-D 10 --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | 

 #  Examples: VIIRS
 #      | folder  | command                                                                                                              |
 #      | viirs   | crefl gtiff --true-color --false-color --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | 

