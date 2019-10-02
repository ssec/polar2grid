Feature: Testing data conversions
  This takes test data and runs it through the command provided.
  It then compares the new data with the expected output.

  Scenario: Data conversion
    Given input data from "acspo/input/test1"
    When "polar2grid.sh acspo gtiff -vv --grid-coverage=0.0 -f" runs
    Then the output matches with the files in "acspo/output/test1"