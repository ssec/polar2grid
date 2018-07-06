Feature: Testing data conversions
    This takes test data and runs it through the command provided for Polar2Grid. 
    It then compares the new data with the expected output. 


    Scenario Outline: Data conversion
        Given input data from <folder>
        When <command> runs
        Then the output matches with the files in <expected>

   # folders are located in /data/test_data/old_polar2grid_data/polar2grid_test
   Examples: MODIS
        | folder        | command                                                                                                                                                | expected             |
        | modis/input   | crefl gtiff --true-color --false-color --fornav-D 10 --grid-configs /data/dist/polar2grid-swbundle-2.2.1b0/grid_configs/grid_example.conf -g miami -f  | modis/output         |

  #  Examples: VIIRS
   #     | folder        | command          | expected       | 
    #    | viirs/input   | viirs gtiff -f   | viirs/output   |

