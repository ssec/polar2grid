Feature: Testing data conversions
    This takes test data and runs it through the command provided. 
    It then compares the new data with the expected output. 

    Scenario Outline: Data conversion
        Given input data from <source>
        When <script> <command> runs
        Then the output matches with the files in <output>

    Examples: ABI
        | source          | command                                       | output           | script      |
        | abi/input/test1 | -r abi_l1b -w geotiff --num-workers 8 -vv -f  | abi/output/test1 | geo2grid.sh |
        | abi/input/test2 | -r abi_l1b -w geotiff --num-workers 8 -vv -f  | abi/output/test2 | geo2grid.sh |
        | abi/input/test3 | -r abi_l1b -w geotiff --num-workers 8 -vv -f  | abi/output/test3 | geo2grid.sh |
        | abi/input/test4 | -r abi_l1b -w geotiff --num-workers 8 -vv -f  | abi/output/test4 | geo2grid.sh |

    Examples: ACSPO
        | source            | command                                | output             | script        |
        | acspo/input/test1 | acspo gtiff -vv --grid-coverage=0.0 -f | acspo/output/test1 | polar2grid.sh |
        | acspo/input/test2 | acspo gtiff -vv --grid-coverage=0.0 -f | acspo/output/test2 | polar2grid.sh |

    Examples: AMSR2_L1B
        | source            | command                                                    | output             | script        |
        | amsr2/input/test1 | amsr2_l1b awips -vv -g 211e -p btemp_36.5h btemp_89.0av -f | amsr2/output/test1 | polar2grid.sh |

    Examples: AVHRR
        | source            | command             | output             | script        |
        | avhrr/input/test1 | avhrr gtiff -vv -f  | avhrr/output/test1 | polar2grid.sh |

    Examples: MODIS
        | source            | command                                                                                                                               | output             | script        |
        | modis/input/test1 | crefl gtiff -vv --true-color --false-color --fornav-D 10 --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f | modis/output/test1 | polar2grid.sh |

    Examples: VIIRS
        | source            | command                                                                                                                  | output             | script        |
        | viirs/input/test1 | crefl gtiff -vv --true-color --false-color --grid-configs ${POLAR2GRID_HOME}/grid_configs/grid_example.conf -g miami -f  | viirs/output/test1 | polar2grid.sh |

    Examples: VIIRS_L1B
       | source                      | command                                                                                                                                                                                                                             | output                        | script        |
       | viirs_l1b_night/input/test1 | viirs_l1b gtiff -vv --grid-configs /data/users/kkolman/integration_tests/polar2grid/integration_tests/p2g_test_data/viirs_l1b_night/input/test1/my_grid.conf -g polar_europe -p adaptive_dnb dynamic_dnb histogram_dnb hncc_dnb -f  | viirs_l1b_night/output/test1  | polar2grid.sh |

    Examples: VIIRS_SDR
       | source                      | command                                                                | output                       | script        |
       | viirs_sdr_day/input/test1   | viirs_sdr gtiff -vv --i-bands --m-bands -p adaptive_dnb dynamic_dnb -f | viirs_sdr_day/output/test1   | polar2grid.sh |
       | viirs_sdr_day/input/test2   | viirs_sdr gtiff -vv -f                                                 | viirs_sdr_day/output/test2   | polar2grid.sh |
       | viirs_sdr_night/input/test1 | viirs_sdr gtiff -vv -p adaptive_dnb dynamic_dnb -f                     | viirs_sdr_night/output/test1 | polar2grid.sh |
