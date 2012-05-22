#!/usr/bin/perl -w

#==============================================================================
# grid_convert.pl - convert a set of lat lon to row col and vice versa
#
# 18-May-1999 T.Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
# $Header: /data/tharan/ms2gth/src/scripts/grid_convert.pl,v 1.4 2006/07/05 19:29:31 tharan Exp $
#
# forward: reads lat/lon pairs from stdin
#          writes col/row pairs to stdout
# inverse: reads col/row pairs from stdin
#          writes col/row pairs to stdout
#
#tell perl to dump data during the print statement, i.e., flush after each 
#    print

$|=1;

# Set source directory so that we can find required files

if (!defined($ENV{PATH_MS2GT_SRC})) {
    print STDERR "GRID_CONVERT: FATAL:\n" .
	"environment variable PATH_MS2GT_SRC is not defined\n";
    exit 1;
}
$path_ms2gt_src = $ENV{PATH_MS2GT_SRC};
$source_ms2gt = "$path_ms2gt_src/scripts";

require("$source_ms2gt/error_mail.pl");
require("$source_ms2gt/grids.pl");

$Usage = "\n
USAGE: grid_convert.pl gpdfile [direction [col_start [row_start]]]
                       defaults: forward      0          0

   gpdfile is the name of a .gpd file defining the projection
   direction is:
     forward for lat/lon to col/row
     inverse for col/row to lat/lon
   col_start:
      will be subtracted from computed col numbers if direction is forward
      will be added to supplied col numbers if direction is inverse
   row_start:
      will be subtracted from computed row numbers if direction is forward
      will be added to supplied row numbers if direction is inverse

   input is from stdin
   output is to stdout\n\n";

#The following symbols are defined in setup.pl and were used only once in
#this module. They appear here to suppress warning messages.

# set command line defaults 

$direction = "forward";
$col_start = 0;
$row_start = 0;

if (@ARGV < 1) {
    print $Usage;
    exit;
} elsif (@ARGV <= 4) {
    $gpdfile = $ARGV[0];
    if (@ARGV >= 2) {
	$direction = $ARGV[1];
	if ($direction ne "forward" && $direction ne "inverse") {
	    print "invalid direction $Usage";
	    exit;
	}
	if (@ARGV >= 3) {
	    $col_start = $ARGV[2];
	    if (@ARGV >= 4) {
		$row_start = $ARGV[3];
	    }
	}
    }
} else {
    print $Usage;
    exit;
}

my $count_max = 10000;
my $total_count = 0;
my $command = ($direction eq "forward") ? "FORWARD" : "INVERSE";
my $count;

do  {
    my ($pipehandle, $pid, $output_file) = grid_convert_open($gpdfile);

    my @whatever_array;
    my @param1_in_array;
    my @param2_in_array;
    my $i = 0;

    while (<STDIN>) {
	chomp $_;
	my ($param1_in, $param2_in, $whatever) = /^\s*(\S+)\s+(\S+)\s*(\S*)/;
	$whatever_array[$i] = defined($whatever) ? $whatever : "";
	$param1_in_array[$i] = $param1_in;
	$param2_in_array[$i] = $param2_in;
	$i++;
	if ($direction eq "inverse") {
	    $param1_in += $col_start;
	    $param2_in += $row_start;
	}
	grid_convert_command($pipehandle, $command, $param1_in, $param2_in);
	if ($i == $count_max) {
	    last;
	}
    }
    $count = $i;

    my (@output_arrays) =
	grid_convert_close($pipehandle, $pid, $output_file);
    my ($status_out, $param1_out, $param2_out);
    my $col_offset = ($direction eq "forward") ? $col_start : 0;
    my $row_offset = ($direction eq "forward") ? $row_start : 0;
    for ($i = 0; $i < $count; $i++) {
	$status_out = $output_arrays[$i];
	$param1_out = $output_arrays[$i + $count] - $col_offset;
	$param2_out = $output_arrays[$i + 2 * $count] - $row_offset;
	printf("%12.5f %12.5f %s\n",
	       $param1_out, $param2_out, $whatever_array[$i]);
    }
    $total_count += $count;
} until ($count == 0);

print STDERR "  count: $total_count\n";
