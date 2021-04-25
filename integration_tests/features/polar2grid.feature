Feature: Test polar2grid output images
  This takes test data from source and runs it through the command provided.
  It then compares the new image with the expected output.

  Scenario Outline: Test polar2grid images
    Given input data from <source>
    When <command> runs
    Then the output matches with the files in <output>

    Examples: ACSPO
      | command                                              | source            |  output            |
      | polar2grid.sh -r acspo -w geotiff -vv --grid-coverage=0.0 -f | acspo/input/test1 | acspo/output/test1 |
      | polar2grid.sh -r acspo -w geotiff -vv --grid-coverage=0.0 -f | acspo/input/test2 | acspo/output/test2 |

   Examples: AMSR2_L1B
      | command                                                                  | source            | output             |
      | polar2grid.sh -r amsr2_l1b -w awips_tiled -vv --sector-id LCC --source-name SSEC --letters -g 211e -p btemp_36.5h btemp_89.0av -f | amsr2/input/test1 | amsr2/output/test1 |

    Examples: AVHRR
      | command                          | source            | output             |
      | polar2grid.sh -r avhrr -w geotiff -vv -f | avhrr/input/test1 | avhrr/output/test1 |

    Examples: MODIS
      | command                                                                                                                                   | source            | output             |
      | polar2grid.sh -r modis -w geotiff -vv -p true_color false_color --grid-configs ${datapath}/grid_configs/grid_example.conf -g miami -f | modis/input/test1 | modis/output/test1 |

    Examples: VIIRS_L1B
      | command                                                                                                                                                                                           | source                      | output                        |
      | polar2grid.sh -r viirs_l1b -w geotiff -vv --grid-configs /data/dist/p2g_test_data/viirs_l1b_night/input/test1/my_grid.conf -g polar_europe -p adaptive_dnb dynamic_dnb histogram_dnb hncc_dnb -f  | viirs_l1b_night/input/test1 | viirs_l1b_night/output/test1  |

    Examples: VIIRS_SDR
      | command                                                                                      | source                      | output                       |
      | polar2grid.sh -r viirs_sdr -w geotiff -vv --i-bands --m-bands -p adaptive_dnb dynamic_dnb -f | viirs_sdr_day/input/test1   | viirs_sdr_day/output/test1   |
      | polar2grid.sh -r viirs_sdr -w geotiff -vv -f                                                 | viirs_sdr_day/input/test2   | viirs_sdr_day/output/test2   |
      | polar2grid.sh -r viirs_sdr -w geotiff -vv -p adaptive_dnb dynamic_dnb -f                     | viirs_sdr_night/input/test1 | viirs_sdr_night/output/test1 |
      | polar2grid.sh -r viirs_sdr -w geotiff -vv -p true_color false_color --awips-true-color --awips-false-color --grid-configs ${datapath}/grid_configs/grid_example.conf -g miami -f  | viirs/input/test1 | viirs/output/test1 |

    Examples: MiRS
      | command                                                                                           | source                      | output                       |
      | polar2grid.sh -r mirs -w hdf5 -p tpw swe btemp_183h1 btemp_57h1 sea_ice rain_rate btemp_88v -f    | mirs/input/test2            | mirs/output/test2            |
      | polar2grid.sh -r mirs -w binary -p tpw swe btemp_183h1 btemp_57h1 sea_ice rain_rate btemp_88v -f  | mirs/input/test2            | mirs/output/test3            |
      | polar2grid.sh -r mirs -w geotiff --fill-value 0 -p tpw swe btemp_183h1 btemp_57h1 sea_ice rain_rate btemp_88v -f | mirs/input/test2            | mirs/output/test4            |
      | polar2grid.sh -r mirs -w awips_tiled --grid-coverage 0 -g lcc_conus_1km --sector-id LCC --letters --compress -p tpw swe btemp_183h1 btemp_57h1 sea_ice rain_rate btemp_88v -f | mirs/input/test2            | mirs/output/test5            |

  Scenario Outline: Test list products output
    Given input data from <source>
    When <command> runs with --list-products
    Then the printed output includes the products in <output>

    Examples: VIIRS_SDR List Products
      | command                                                                                      | source                      | output                       |
      | polar2grid.sh -r viirs_sdr -w geotiff -vv -f                                                 | viirs_sdr_day/input/test1   | true_color,i01,i01_rad,ifog  |
