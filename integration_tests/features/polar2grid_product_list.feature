Feature: Test polar2grid --list-products produces the expected output

  Scenario Outline: Test list products output
    Given input data from <source>
    When <command> runs with --list-products
    Then the printed output includes the products in <output>

  Examples: VIIRS_SDR
    | command                                                                                      | source                      | output                       |
    | polar2grid.sh -r viirs_sdr -w geotiff -vv -f                                                 | viirs_sdr_day/input/test1   | true_color,i01,ifog          |
