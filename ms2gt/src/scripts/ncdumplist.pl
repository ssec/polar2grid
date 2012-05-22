#!/usr/local/bin/perl -w

$|=1;

$path_ms2gt_src = $ENV{PATH_MS2GT_SRC};
$source_ms2gt = "$path_ms2gt_src/scripts";

require("$source_ms2gt/mod35_l2_usage.pl");
require("$source_ms2gt/setup.pl");
require("$source_ms2gt/error_mail.pl");

$script = "NCDUMPLIST";
$junk = $script;
$junk = $junk;

$Usage = "\n
USAGE: ncdumplist.pl listfile [lines_to_skip]
         default:                    0\n\n";

my $listfile;
my $lines_to_skip = 0;

if (@ARGV < 1 || @ARGV > 2) {
    print $Usage;
    exit 1;
}

if (@ARGV <= 2) {
    $listfile = $ARGV[0];
    if (@ARGV >= 2) {
	$lines_to_skip = $ARGV[1];
    }
} else {
    print $Usage;
    exit 1;
}
open_or_die("LISTFILE", "$listfile");
my $lines_read = 0;
while (<LISTFILE>) {
    if ($lines_read++ < $lines_to_skip) {
	next;
    }
    chomp;
    my @files = split;
    my $file;
    foreach $file (@files) {
	do_or_die("ncdump.pl $file");
    }
}
close(LISTFILE);
