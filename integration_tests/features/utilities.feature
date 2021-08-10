Feature: Test polar2grid utility scripts
  This takes test data from source and runs it through the command provided.
  It then compares the new image with the expected output.

  Scenario Outline: Test add_colormap.sh
    Given input data from <source>
    Given an empty working directory
    Given input data is copied to the working directory
    When <command> runs
    Then the output matches with the files in <output>

    Examples: AMSR2_L1B
      | command                                                                  | source            | output             |
      | add_colormap.sh ${POLAR2GRID_HOME}/colormaps/amsr2_89h.cmap | utilities/add_colormap/input/test1 | utilities/add_colormap/output/test1 |
