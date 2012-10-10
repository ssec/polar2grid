#!/usr/bin/perl -w

#========================================================================
# grids.pl - routines to get convert lat/lon to/from col/row
#
# 12-Oct-1998 T.Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

# $Header: /disks/megadune/data/tharan/ms2gth/src/scripts/grids.pl,v 1.4 2006/07/07 17:00:03 tharan Exp $

#========================================================================
# grid_convert_open - open a pipe for sending input to grid_convert
#                     and open a temporary file for retrieving output
#                     from grid_convert.
#
# 12-Oct-1998 T.Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
#
#    input:  gpd_file
#
#    return: 3-element array consisting of:
#              pipehandle - string containing name of pipe handle
#              pid - process id of process running grid_convert
#              grid_convert_output_file - file containing output of
#                 grid_convert
#

if (!defined($ENV{PATH_MS2GT_SRC})) {
    print STDERR "GRIDS: FATAL:\n" .
	"environment variable PATH_MS2GT_SRC is not defined\n";
    exit 1;
}
$path_ms2gt_src = $ENV{PATH_MS2GT_SRC};
$source_ms2gt = "$path_ms2gt_src/scripts";

require("$source_ms2gt/error_mail.pl");

$false = 0;
$true  = 1;

sub grid_convert_open {
    my ($gpd_file) = @_;

    my $pipehandle = "GRIDPIPE";
    my $time = time();
    my $output_file =
	"grid_convert_output_" . "$time";
    my $pid = open($pipehandle,
		   "| grid_convert $gpd_file >$output_file");
    return($pipehandle, $pid, $output_file);
}


#========================================================================
# grid_convert_command - pipe a command to grid_convert
#
# 13-Oct-1998 T.Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
#
#    input: pipehandle - string containing name of pipe handle
#           command - "FORWARD" or "INVERSE"
#           param1 - latitude if FORWARD, column if INVERSE
#           param2 - longitude if FORWARD, row if INVERSE
#
#    return: none
#

sub grid_convert_command {
    my ($pipehandle, $command, $param1, $param2) = @_;

    print $pipehandle "$command $param1 $param2\n";
}


#========================================================================
# grid_convert_close - close pipe to grid_convert and return output
#
# 13-Oct-1998 T.Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#

#
#    input:  pipehandle - string containing name of pipe handle
#            pid - process id of process running grid_convert
#            output_file - file containing output of grid_convert
#
#    return: 3 arrays containing grid_convert output values:
#            output_state - "SUCCESS" or "FAILURE"
#            output_param1 -  column if FORWARD
#                            latitude if INVERSE 
#            output_param2 - row if FORWARD
#                            longitude if INVERSE
#

sub grid_convert_close {
    my ($pipehandle, $pid, $output_file) = @_;

    close($pipehandle);
    $grid_pipe_status = $?;
    if ($grid_pipe_status) {
	diemail("grid_convert_close: FATAL:\n" .
		"grid_convert pipe returned status $grid_pipe_status");
    }
    open(GRIDOUTPUT, "$output_file") ||
	diemail("grid_convert_close: FATAL:\n" .
		"can't open $output_file");
    my @grid_output;
    my $first_line = $true;
    my $line_ctr = 0;
    my @output_state;
    my @output_param1;
    my @output_param2;
    while (<GRIDOUTPUT>) {
	if ($first_line) {
	    $first_line = $false;
	    my ($test) = /(\S+)/;
	    if (!defined($test) || $test ne "SUCCESS") {
		diemail("grid_convert_close: FATAL:\n" .
			"grid_convert did not start successfully\n");
	    }
	} else {
	    ($output_state[$#output_state+1],
	     $output_param1[$#output_param1+1],
	     $output_param2[$#output_param2+1]) = /(\S+)\s+(\S+)\s+(\S+)/;
	    $line_ctr++;
	}
    }
    close(GRIDOUTPUT);
    system("rm -f $output_file");
    return (@output_state, @output_param1, @output_param2);
}

# this makes the library work correctly when using the require command
1;
