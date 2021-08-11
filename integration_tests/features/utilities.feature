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
      | add_colormap.sh ${POLAR2GRID_HOME}/colormaps/amsr2_89h.cmap | add_colormap/input/test1 | add_colormap/output/test1 |

    Examples: ACSPO
      | command                                                                  | source            | output             |
      | add_colormap.sh ${POLAR2GRID_HOME}/colormaps/p2g_sst_palette.txt | add_colormap/input/test2 | add_colormap/output/test2 |

  Scenario Outline: Test add_coastlines.sh
    Given input data from <source>
    Given an empty working directory
    Given input data is copied to the working directory
    When <command> runs
    Then the output matches with the files in <output>

    Examples: ACSPO
      | command                                                                  | source            | output             |
      | add_coastlines.sh --add-colorbar --colorbar-text-color="white" --colorbar-units="K" --colorbar-align top --colorbar-title="VIIRS ACSPO SST" --colorbar-text-size 20 --colorbar-height=35 --add-coastlines --add-borders --  | add_coastlines/input/test1 | add_coastlines/output/test1 |
