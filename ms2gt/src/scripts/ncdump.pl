#!/usr/bin/perl -w

$|=1;

$path_ms2gt_src = $ENV{PATH_MS2GT_SRC};
$source_ms2gt = "$path_ms2gt_src/scripts";

require("$source_ms2gt/setup.pl");
require("$source_ms2gt/error_mail.pl");

$script = "NCDUMP";
$junk = $script;
$junk = $junk;

$Usage = "\n
USAGE: ncdump.pl hdf_file(s)\n";

if (@ARGV < 1) {
    print $Usage;
    exit 1;
}

my @hdf_files = @ARGV;
my $hdf_file;
foreach $hdf_file (@hdf_files) {
    do_or_die("ncdump -h $hdf_file >$hdf_file.atr");
}
