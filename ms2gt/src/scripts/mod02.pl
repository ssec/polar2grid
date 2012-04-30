#!/usr/bin/perl -w

# $Id: mod02.pl,v 1.33 2001/04/26 20:28:48 haran Exp $

#========================================================================
# mod02.pl - grids MOD02 and MOD03 data
#
# 25-Oct-2000 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

$|=1;

$path_ms2gt_src = $ENV{PATH_MS2GT_SRC};
$source_ms2gt = "$path_ms2gt_src/scripts";

require("$source_ms2gt/mod02_usage.pl");
require("$source_ms2gt/mod02_case.pl");
require("$source_ms2gt/setup.pl");
require("$source_ms2gt/error_mail.pl");

# global variables defined in setup.pl and used only once here.
# dummy assignment here to supress warning messages.

$junk = $weight_distance_max;
$junk = $junk;

# define a global used by do_or_die and invoke_or_die

$script = "MOD02";

# Set command line defaults

my $dirinout;
my $tag;
my $listfile;
my $gpdfile;
my $chanfile = "none";
my $ancilfile = "none";
my $latlon_src = "1";
my $ancil_src = "1";
my $keep = 0;
my $rind = 50;

if (@ARGV < 4) {
    print $mod02_usage;
    exit 1;
}
if (@ARGV <= 10) {
    $dirinout = $ARGV[0];
    $tag = $ARGV[1];
    $listfile = $ARGV[2];
    $gpdfile = $ARGV[3];
    if (@ARGV >= 5) {
        $chanfile = $ARGV[4];
	if (@ARGV >= 6) {
	    $ancilfile = $ARGV[5];
	    if (@ARGV >= 7) {
		$latlon_src = $ARGV[6];
		if ($latlon_src ne "1" &&
		    $latlon_src ne "3" &&
		    $latlon_src ne "H" &&
		    $latlon_src ne "Q") {
		    print "invalid latlon_src\n$mod02_usage";
		    exit 1;
		}
		if (@ARGV >= 8) {
		    $ancil_src = $ARGV[7];
		    if ($ancil_src ne "1" &&
			$ancil_src ne "3") {
			print "invalid ancil_src\n$mod02_usage";
			exit 1;
		    }
		    if (@ARGV >= 9) {
			$keep = $ARGV[8];
			if ($keep ne "0" && $keep ne "1") {
			    print "invalid keep\n$mod02_usage";
			    exit 1;
			}
			if (@ARGV >= 10) {
			    $rind = $ARGV[9];
			}
		    }
		}
	    }
	}
    }
} else {
    print $mod02_usage;
    exit 1;
}

print_stderr("\n".
	     "$script: MESSAGE:\n".
	     "> dirinout         = $dirinout\n".
	     "> tag              = $tag\n".
	     "> listfile         = $listfile\n".
	     "> gpdfile          = $gpdfile\n".
	     "> chanfile         = $chanfile\n".
	     "> ancilfile        = $ancilfile\n".
	     "> latlon_src       = $latlon_src\n".
	     "> ancil_src        = $ancil_src\n".
	     "> keep             = $keep\n".
	     "> rind             = $rind\n");

if ($chanfile eq "none" && $ancilfile eq "none") {
    diemail("$script: FATAL: chanfile and ancilfile must not both be none");
}

chdir_or_die($dirinout);

my @list;
open_or_die("LISTFILE", "$listfile");
print_stderr("contents of listfile:\n");
while (<LISTFILE>) {
    my ($file) = /\s*(\S+)/;
    if (defined($file)) {
	push(@list, $file);
	print STDERR "$file";
    }
}
close(LISTFILE);

my @chans;
my @chan_conversions;
my @chan_weight_types;
my @chan_fills;
if ($chanfile ne "none") {
    open_or_die("CHANFILE", "$chanfile");
    print_stderr("contents of chanfile:\n");
    my $line = 0;
    while (<CHANFILE>) {
	my ($chan, $conversion, $weight_type, $fill) =
	    /(\d+)\s*(\S*)\s*(\S*)\s*(\S*)/;
	if (!defined($chan) || $chan eq "") {
	    $chan = 0;
	}
	if (!defined($conversion) || $conversion eq "") {
	    $conversion = "raw";
	}
	if (!defined($weight_type) || $weight_type eq "") {
	    $weight_type = "avg";
	}
	if (!defined($fill) || $fill eq "") {
	    $fill = 0;
	}
	push(@chans, $chan);
	push(@chan_conversions, $conversion);
	push(@chan_weight_types, $weight_type);
	push(@chan_fills, $fill);
	print "$chan $conversion $weight_type $fill\n";
	$line++;
	if ($chan < 1 || $chan > 36) {
	    diemail("$script: FATAL: " .
		    "invalid channel on line $line in $chanfile\n");
	}
	if ($conversion ne "raw" &&
	    $conversion ne "corrected" &&
	    $conversion ne "radiance" &&
	    $conversion ne "reflectance" &&
	    $conversion ne "temperature") {
	    diemail("$script: FATAL: " .
		    "invalid conversion on line $line in $chanfile\n");
	}
	if ($weight_type ne "avg" &&
	    $weight_type ne "max") {
	    diemail("$script: FATAL: " .
		    "invalid weight_type on line $line in $chanfile\n");
	}
    }
    close(CHANFILE);
}
my $chan_count = scalar(@chans);

my @ancils;
my @ancil_conversions;
my @ancil_weight_types;
my @ancil_fills;
my @ancil_data_types;
if ($ancilfile ne "none") {
    open_or_die("ANCILFILE", "$ancilfile");
    print_stderr("contents of ancilfile:\n");
    my $line = 0;
    while (<ANCILFILE>) {
	my ($ancil, $conversion, $weight_type, $fill) =
	    /(\S+)\s*(\S*)\s*(\S*)\s*(\S*)/;
	if (!defined($ancil)) {
	    $ancil = "";
	}
	if (!defined($conversion) || $conversion eq "") {
	    $conversion = "raw";
	}
	if (!defined($weight_type) || $weight_type eq "") {
	    $weight_type = ($ancil eq "lmsk" ||
			    $ancil eq "gflg") ? "max" : "avg";
	}
	if (!defined($fill) || $fill eq "") {
	    $fill = 0;
	}
	my $data_type = "f4";
	if ($conversion eq "raw") {
	    $data_type = "s2";
	    if ($ancil eq "rang") {
		$data_type = "u2";
	    } elsif ($ancil eq "lmsk" ||
		     $ancil eq "gflg") {
		$data_type = "u1";
	    }
	}
	push(@ancils, $ancil);
	push(@ancil_conversions, $conversion);
	push(@ancil_weight_types, $weight_type);
	push(@ancil_fills, $fill);
	push(@ancil_data_types, $data_type);
	print "$ancil $conversion $weight_type $fill $data_type\n";
	$line++;
	if ($ancil ne "hght" &&
	    $ancil ne "seze" &&
	    $ancil ne "seaz" &&
	    $ancil ne "rang" &&
	    $ancil ne "soze" &&
	    $ancil ne "soaz" &&
	    $ancil ne "lmsk" &&
	    $ancil ne "gflg") {
	    diemail("$script: FATAL: " .
		    "invalid ancillary parameter on line $line in $ancilfile\n");
	}
	if ($conversion ne "raw" &&
	    $conversion ne "scaled") {
	    diemail("$script: FATAL: " .
		    "invalid conversion on line $line in $ancilfile\n");
	}
	if ($weight_type ne "avg" &&
	    $weight_type ne "max") {
	    diemail("$script: FATAL: " .
		    "invalid weight_type on line $line in $ancilfile\n");
	}
    }
    close(ANCILFILE);
}
my $ancil_count = scalar(@ancils);

my @gridsize = `gridsize $gpdfile`;
my ($grid_cols) = ($gridsize[0] =~ /cols:\s*(\d+)/);
my ($grid_rows) = ($gridsize[1] =~ /rows:\s*(\d+)/);
if (!defined($grid_cols) || $grid_cols == 0 ||
    !defined($grid_rows) || $grid_rows == 0) {
    diemail("$script: FATAL: " .
	    "error opening gpdfile: $gpdfile\n");
}
$grid_cols = sprintf("%05d", $grid_cols);
$grid_rows = sprintf("%05d", $grid_rows);
print_stderr("$script: MESSAGE:\n" .
	     "grid will contain $grid_cols cols and $grid_rows rows\n");

my $swath_cols = 0;
my $swath_rows = 0;
my $ancil_cols = 0;
my $ancil_rows = 0;
my $latlon_cols = 0;
my $latlon_rows = 0;
my $lat_cat = "cat ";
my $lon_cat = "cat ";
my $i;
my @chan_cat;
for ($i = 0; $i < $chan_count; $i++) {
    $chan_cat[$i] = "cat ";
    $chans[$i] = sprintf("%02d", $chans[$i]);
}
my @ancil_cat;
for ($i = 0; $i < $ancil_count; $i++) {
    $ancil_cat[$i] = "cat ";
}
my $swath_resolution;
my $swath_rows_per_scan;
my $this_swath_cols;
my $this_swath_rows = 0;

my $ancil_rows_per_scan;
my $this_ancil_cols;
my $this_ancil_rows = 0;
my $ancil_interp_factor;
my $ancil_offset = 0;
my $ancil_col_extra = 0;

my $latlon_rows_per_scan;
my $latlon_interp_factor;
my $latlon_offset = 0;
my $latlon_col_extra = 0;

my $case;
my $line;
my $hdf;
my $hdf_prefix;
my @filestems;
my @ancil_filestems;
my $old_case = -1;
my @latlon_scans_as_read;
for ($line = 0; $line < @list; $line++) {
    $hdf = $list[$line];
    chomp $hdf;
    my ($filestem) = ($hdf =~ /(.*)\.hdf/);
    my $old_latlon_src = $latlon_src;
    my $old_ancil_src = $ancil_src;
    ($ancil_src, $latlon_src, $filestem, $hdf_prefix, $case) =
	mod02_case($old_ancil_src, $old_latlon_src, $filestem);
    if ($line > 0 && $case != $old_case) {
	diemail("$script: FATAL: inconsistent case values");
    }
    $old_case = $case;
    if ($line == 0 && $old_latlon_src ne $latlon_src) {
	warnmail("$script: WARNING: " .
		 "forcing latlon_src from $old_latlon_src to $latlon_src");
    }
    if ($line == 0 && $old_ancil_src ne $ancil_src) {
	warnmail("$script: WARNING: " .
		 "forcing ancil_src from $old_ancil_src to $ancil_src");
    }
    push(@filestems, $filestem);
    my ($latlon_filestem) = $filestem;
    my ($ancil_filestem) = $filestem;
    if ($case == 1) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 5;
	$ancil_offset = 2;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 5;
	$latlon_offset = 2;
	$latlon_col_extra = 1;
	$latlon_rows_per_scan = 2;
    }
    if ($case == 2) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 5;
	$ancil_offset = 2;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 1;
	$latlon_filestem =~ s/MOD021KM/MOD02HKM/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 3) {
	$swath_resolution = "H";
	$swath_rows_per_scan = 20;
	$ancil_interp_factor = 10;
	$ancil_filestem =~ s/MOD02HKM/MOD021KM/;
	$ancil_offset = 4;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 2;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 4) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 5;
	$ancil_offset = 2;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 1;
	$latlon_filestem =~ s/MOD021KM/MOD02QKM/; 
	$latlon_rows_per_scan = 10;
    }
    if ($case == 5) {
	$swath_resolution = "Q";
	$swath_rows_per_scan = 40;
	$ancil_interp_factor = 20;
	$ancil_offset = 8;
	$ancil_col_extra = 1;
	$ancil_filestem =~ s/MOD02QKM/MOD021KM/;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 4;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 6) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 1;
	$ancil_filestem =~ s/MOD021KM/MOD03/;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 1;
	$latlon_filestem =~ s/MOD021KM/MOD03/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 7) {
	$swath_resolution = "H";
	$swath_rows_per_scan = 20;
	$ancil_interp_factor = 2;
	$ancil_filestem =~ s/MOD02HKM/MOD03/;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 2;
	$latlon_filestem =~ s/MOD02HKM/MOD03/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 8) {
	$swath_resolution = "Q";
	$swath_rows_per_scan = 40;
	$ancil_interp_factor = 4;
	$ancil_filestem =~ s/MOD02QKM/MOD03/;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 4;
	$latlon_filestem =~ s/MOD02QKM/MOD03/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 9) {
	$swath_resolution = "0";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 1;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 1;
	$latlon_rows_per_scan = 10;
	if ($chan_count != 0) {
	    diemail("$script: FATAL:\n" .
		    "listfile $listfile must contain MOD02 files since " .
		    "chanfile is not none");
	}
    }

    push(@ancil_filestems, $ancil_filestem);
    my $filestem_lat = $latlon_filestem . "_latf_";
    my $filestem_lon = $latlon_filestem . "_lonf_";
    do_or_die("rm -f $filestem_lat*");
    do_or_die("rm -f $filestem_lon*");
    
    my @latlon_glob = glob("$latlon_filestem*.hdf");
    if (@latlon_glob == 0) {
	diemail("$script: FATAL: $latlon_filestem*.hdf not found");
    }
    my $hdf_latlon = $latlon_glob[0];
    do_or_die("idl_sh.pl extract_latlon \"'$hdf_latlon'\" " .
	      "\"'$latlon_filestem'\"");

    my @lat_glob = glob("$filestem_lat*");
    if (@lat_glob == 0) {
	diemail("$script: FATAL: $filestem_lat* not found");
    }
    my $lat_file = $lat_glob[0];
    my ($this_lat_cols, $this_lat_rows) =
	($lat_file =~ /$filestem_lat(.....)_(.....)/);
    print "$lat_file contains $this_lat_cols cols and " .
	  "$this_lat_rows rows\n";
    $lat_cat .= "$lat_file ";
    $latlon_cols = $this_lat_cols;
    $latlon_rows += $this_lat_rows;
    push(@latlon_scans_as_read, $this_lat_rows / $latlon_rows_per_scan);

    my @lon_glob = glob("$filestem_lon*");
    if (@lat_glob == 0) {
	diemail("$script: FATAL: $filestem_lon* not found");
    }
    my $lon_file = $lon_glob[0];
    my ($this_lon_cols, $this_lon_rows) =
	($lon_file =~ /$filestem_lon(.....)_(.....)/);
    print "$lon_file contains $this_lon_cols cols and " .
	  "$this_lon_rows rows\n";
    $lon_cat .= "$lon_file ";
}

$latlon_cols = sprintf("%05d", $latlon_cols);
$latlon_rows = sprintf("%05d", $latlon_rows);

my $lat_rm = $lat_cat;
my $lon_rm = $lon_cat;

$lat_rm  =~ s/cat/rm -f/;
$lon_rm  =~ s/cat/rm -f/;

my $lat_file  = "$tag\_latf_$latlon_cols\_$latlon_rows.img";
my $lon_file  = "$tag\_lonf_$latlon_cols\_$latlon_rows.img";

do_or_die("$lat_cat  >$lat_file");
do_or_die("$lon_cat  >$lon_file");

do_or_die("$lat_rm");
do_or_die("$lon_rm");

my $latlon_scans = $latlon_rows / $latlon_rows_per_scan;
my $force = ($latlon_interp_factor == 1) ? "-r $rind" : "-f";
my $filestem_cols = $tag . "_cols_";
my $filestem_rows = $tag . "_rows_";
do_or_die("rm -f $filestem_cols*");
do_or_die("rm -f $filestem_rows*");
do_or_die("ll2cr -v $force $latlon_cols $latlon_scans $latlon_rows_per_scan " .
	  "$lat_file $lon_file $gpdfile $tag");
if (!$keep) {
    do_or_die("rm -f $lat_file");
    do_or_die("rm -f $lon_file");
}

my @cols_glob = glob("$filestem_cols*");
my $cols_file = $cols_glob[0];
my ($this_cols_cols, $this_cols_scans,
    $this_cols_scan_first, $this_cols_rows_per_scan) =
    ($cols_file =~ /$filestem_cols(.....)_(.....)_(.....)_(..)/);
print "$cols_file contains $this_cols_cols cols,\n" .
    "   $this_cols_scans scans, $this_cols_scan_first scan_first,\n" .
    "   and $this_cols_rows_per_scan rows_per_scan\n";

my @rows_glob = glob("$filestem_rows*");
my $rows_file = $rows_glob[0];
my ($this_rows_cols, $this_rows_scans,
    $this_rows_scan_first, $this_rows_rows_per_scan) =
    ($rows_file =~ /$filestem_rows(.....)_(.....)_(.....)_(..)/);
print "$rows_file contains $this_rows_cols cols,\n" .
    "   $this_rows_scans scans, $this_rows_scan_first scan_first,\n" .
    "   and $this_rows_rows_per_scan rows_per_scan\n";

if ($this_cols_cols != $this_rows_cols ||
    $this_cols_scans != $this_rows_scans ||
    $this_cols_scan_first != $this_rows_scan_first ||
    $this_cols_rows_per_scan != $this_rows_rows_per_scan) {
    diemail("$script: FATAL: " .
	    "inconsistent sizes for $cols_file and $rows_file");
}
my $cr_cols = $this_cols_cols;
my $cr_scans = $this_cols_scans;
my $cr_scan_first = $this_cols_scan_first;
my $cr_rows_per_scan = $this_cols_rows_per_scan;

$swath_cols = $cr_cols * $latlon_interp_factor - $latlon_col_extra;
if ($latlon_interp_factor > 1) {
    my $col_min = -$rind;
    my $col_max = $grid_cols + $rind - 1;
    my $row_min = -$rind;
    my $row_max = $grid_rows + $rind - 1;

    do_or_die("idl_sh.pl interp_colrow " .
	      "$latlon_interp_factor $cr_cols $cr_scans $cr_rows_per_scan " .
	      "\"'$cols_file'\" \"'$rows_file'\" " .
	      "$swath_cols \"'$tag'\" " .
	      "grid_check=[$col_min,$col_max,$row_min,$row_max] " .
	      "col_offset=$latlon_offset row_offset=$latlon_offset");
    do_or_die("rm -f $cols_file");
    do_or_die("rm -f $rows_file");

    $filestem_cols = $tag . "_cols_";
    @cols_glob = glob("$filestem_cols*.img");
    $cols_file = $cols_glob[0];
    ($this_cols_cols, $this_cols_scans,
     $this_cols_scan_first, $this_cols_rows_per_scan) =
	 ($cols_file =~ /$filestem_cols(.....)_(.....)_(.....)_(..)/);
    print "$cols_file contains $this_cols_cols cols,\n" .
	  "   $this_cols_scans scans, $this_cols_scan_first scan_first,\n" .
	  "   and $this_cols_rows_per_scan rows_per_scan\n";

    $filestem_rows = $tag . "_rows_";
    @rows_glob = glob("$filestem_rows*.img");
    $rows_file = $rows_glob[0];
    ($this_rows_cols, $this_rows_scans,
     $this_rows_scan_first, $this_rows_rows_per_scan) =
	 ($cols_file =~ /$filestem_cols(.....)_(.....)_(.....)_(..)/);
    print "$rows_file contains $this_rows_cols cols,\n" .
          "   $this_rows_scans scans, $this_rows_scan_first scan_first,\n" .
          "   and $this_rows_rows_per_scan rows_per_scan\n";

    if ($this_cols_cols != $this_rows_cols ||
	$this_cols_scans != $this_rows_scans ||
	$this_cols_scan_first != $this_rows_scan_first ||
	$this_cols_rows_per_scan != $this_rows_rows_per_scan) {
	diemail("$script: FATAL: " .
		"inconsistent sizes for $cols_file and $rows_file");
    }
    $cr_cols = $this_cols_cols;
    $cr_scans = $this_cols_scans;
    $cr_scan_first = $this_cols_scan_first;
    $cr_rows_per_scan = $this_cols_rows_per_scan;
}

if ($cr_scans == 0) {
    if (!$keep) {
	do_or_die("rm -f $cols_file");
	do_or_die("rm -f $rows_file");
    }
    diemail("$script: FATAL: $tag: grid contains no data");
}

my $swath_scans = $cr_scans;
my $swath_scan_first = $cr_scan_first;

my $this_swath_rows_max = $swath_scans * $swath_rows_per_scan;
my $this_swath_row_first = $swath_scan_first * $swath_rows_per_scan;
my $this_ancil_rows_max = $swath_scans * $ancil_rows_per_scan;
my $this_ancil_row_first = $swath_scan_first * $ancil_rows_per_scan;
for ($line = 0; $line < @list; $line++) {
    my $swath_rows_expected =
	$latlon_scans_as_read[$line] * $swath_rows_per_scan;
    if ($this_swath_row_first < $swath_rows_expected) {
	$hdf = $list[$line];
	chomp $hdf;
	my $filestem = $filestems[$line];
	for ($i = 0; $i < $chan_count; $i++) {
	    my $chan = $chans[$i];
	    my $conversion = $chan_conversions[$i];
	    my $conv = substr($conversion, 0, 3);
	    my $filestem_chan_conv = "$filestem\_ch$chan\_$conv\_";
	    do_or_die("rm -f $filestem_chan_conv*");
	    print_stderr("idl_sh.pl extract_chan \"'$hdf'\" \"'$filestem'\" " .
		      "$chan conversion=\"'$conversion'\" " .
		      "swath_rows=$this_swath_rows_max " .
		      "swath_row_first=$this_swath_row_first");
	    do_or_die("idl_sh.pl extract_chan \"'$hdf'\" \"'$filestem'\" " .
		      "$chan conversion=\"'$conversion'\" " .
		      "swath_rows=$this_swath_rows_max " .
		      "swath_row_first=$this_swath_row_first");
	    my @chan_glob = glob("$filestem_chan_conv*");
	    if (@chan_glob == 0) {
		diemail("$script: FATAL: $filestem_chan_conv* not found");
	    }
	    my $chan_file = $chan_glob[0];
	    ($this_swath_cols, $this_swath_rows) =
		($chan_file =~ /$filestem_chan_conv(.....)_(.....)/);
	    print "$chan_file contains $this_swath_cols cols and " .
		"$this_swath_rows rows\n";
	    if ($this_swath_cols != $swath_cols) {
		diemail("$script: FATAL: " .
			"inconsistent number of columns in $chan_file");
	    }
	    $chan_cat[$i] .= "$chan_file ";
	}
	$swath_rows += $this_swath_rows;
	$this_swath_row_first = 0;
	$this_swath_rows_max -= $this_swath_rows;
    } else {
	$this_swath_row_first -= $swath_rows_expected;
    }

    my $ancil_rows_expected =
	$latlon_scans_as_read[$line] * $ancil_rows_per_scan;
    if ($this_ancil_row_first < $ancil_rows_expected) {
	my $ancil_filestem = $ancil_filestems[$line];
	for ($i = 0; $i < $ancil_count; $i++) {
	    my $ancil = $ancils[$i];
	    my $conversion = $ancil_conversions[$i];
	    my $conv = substr($conversion, 0, 3);
	    my $filestem_ancil_conv = "$ancil_filestem\_$ancil\_$conv\_";
	    do_or_die("rm -f $filestem_ancil_conv*");
	    my @ancil_glob = glob("$ancil_filestem*.hdf");
	    if (@ancil_glob == 0) {
		diemail("$script: FATAL: $ancil_filestem*.hdf not found");
	    }
	    my $hdf_ancil = $ancil_glob[0];
	    do_or_die("idl_sh.pl extract_ancil \"'$hdf_ancil'\" " .
		      "\"'$ancil_filestem'\" \"'$ancil'\" " .
		      "conversion=\"'$conversion'\" " .
		      "swath_rows=$this_ancil_rows_max " .
		      "swath_row_first=$this_ancil_row_first");
	    @ancil_glob = glob("$filestem_ancil_conv*");
	    if (@ancil_glob == 0) {
		diemail("$script: FATAL: $filestem_ancil_conv* not found");
	    }
	    my $ancil_file = $ancil_glob[0];
	    ($this_ancil_cols, $this_ancil_rows) =
		($ancil_file =~ /$filestem_ancil_conv(.....)_(.....)/);
	    print "$ancil_file contains $this_ancil_cols cols and " .
		"$this_ancil_rows rows\n";
	    if ($chan_count == 0 && $i == 0) {
		if ($line == 0) {
		    $this_swath_cols = $ancil_interp_factor * $this_ancil_cols -
			$ancil_col_extra;
		    $swath_cols = $this_swath_cols;
		}
		$this_swath_rows = $ancil_interp_factor * $this_ancil_rows;
		$swath_rows += $this_swath_rows;
	    }
	    if ($ancil_interp_factor * $this_ancil_cols -
		$ancil_col_extra != $this_swath_cols ||
		$ancil_interp_factor * $this_ancil_rows != $this_swath_rows) {
		diemail("$script: FATAL: " .
			"inconsistent number of columns in $ancil_file");
	    }
	    $ancil_cat[$i] .= "$ancil_file ";
	}
	$ancil_cols = $this_ancil_cols;
	$ancil_rows += $this_ancil_rows;
	$this_ancil_row_first = 0;
	$this_ancil_rows_max -= $this_ancil_rows;
    } else {
	$this_ancil_row_first -= $ancil_rows_expected;
    }
}
$swath_rows = sprintf("%05d", $swath_rows);
$ancil_rows = sprintf("%05d", $ancil_rows);

my @chan_files;
for ($i = 0; $i < $chan_count; $i++) {
    my $chan = $chans[$i];
    my $chan_rm = $chan_cat[$i];
    my $tagext = substr($chan_conversions[$i], 0, 3);
    $chan_rm =~ s/cat/rm -f/;
    $chan_files[$i] = "$tag\_$tagext\_ch$chan\_$swath_cols\_$swath_rows.img";
    do_or_die("$chan_cat[$i] >$chan_files[$i]");
    do_or_die("$chan_rm");
}

my @ancil_files;
for ($i = 0; $i < $ancil_count; $i++) {
    my $ancil = $ancils[$i];
    my $ancil_rm = $ancil_cat[$i];
    my $tagext = substr($ancil_conversions[$i], 0, 3);
    $ancil_rm =~ s/cat/rm -f/;
    $ancil_files[$i] = "$tag\_$tagext\_$ancil\_$ancil_cols\_$ancil_rows.img";
    do_or_die("$ancil_cat[$i] >$ancil_files[$i]");
    do_or_die("$ancil_rm");
}

if ($ancil_interp_factor > 1) {
    my $ancil_scans = $ancil_rows / $ancil_rows_per_scan;
    for ($i = 0; $i < $ancil_count; $i++) {
	my $ancil_file = $ancil_files[$i];
	my $ancil = $ancils[$i];
	my $conversion = $ancil_conversions[$i];
	my $weight_type = $ancil_weight_types[$i];
	my $data_type = $ancil_data_types[$i];
	my $conv = substr($conversion, 0, 3);
	my $weight = substr($weight_type, 0, 1);
	my $nearest_neighbor = ($weight_type eq "max") ?
	    "/nearest_neighbor" : "";
	my $filestem_ancil_conv = "$tag\_$ancil\_$conv$weight";
	system("rm -f $filestem_ancil_conv*");
	do_or_die("idl_sh.pl interp_swath " .
		  "$ancil_interp_factor $ancil_cols $ancil_scans " .
		  "$ancil_rows_per_scan \"'$ancil_file'\" " .
		  "$swath_cols \"'$filestem_ancil_conv'\" " .
		  "data_type=\"'$data_type'\" " .
		  "col_offset=$ancil_offset row_offset=$ancil_offset " .
		  "$nearest_neighbor");

	my @ancil_glob = glob("$filestem_ancil_conv*");
	if (@ancil_glob == 0) {
	    diemail("$script: FATAL: $filestem_ancil_conv* not found");
	}
	do_or_die("rm -f $ancil_file");
	$ancil_file = $ancil_glob[0];
	$ancil_files[$i] = $ancil_file;
	($this_ancil_cols, $this_ancil_scans,
	 $this_ancil_scan_first, $this_ancil_rows_per_scan) =
	 ($ancil_file =~ /$filestem_ancil_conv\_(.....)_(.....)_(.....)_(..)/);
	print "$ancil_file contains $this_ancil_cols cols,\n" .
	  "   $this_ancil_scans scans, $this_ancil_scan_first scan_first,\n" .
	  "   and $this_ancil_rows_per_scan rows_per_scan\n";

	if ($this_ancil_cols != $swath_cols ||
	    $this_ancil_scans != $swath_scans ||
	    $this_ancil_scan_first != 0 ||
	    $this_ancil_rows_per_scan != $swath_rows_per_scan) {
	    diemail("$script: FATAL: " .
		    "inconsistent size for $ancil_file");
	}
    }
}

for ($i = 0; $i < $chan_count; $i++) {
    my $chan_file = $chan_files[$i];
    my $chan = $chans[$i];
    my $tagext = substr($chan_conversions[$i], 0, 3);
    my $m_option;
    if ($chan_weight_types[$i] eq "avg") {
	$m_option = "";
	$tagext .= "a";
    } else {
	$m_option = "-m";
	$tagext .= "m";
    }
    my $grid_file = "$tag\_$tagext\_ch$chan\_$grid_cols\_$grid_rows.img";
    my $t_option;
    my $f_option;
    if ($chan_conversions[$i] eq "raw") {
	$t_option = "-t u2";
	$f_option = "-f 65535";
    } else {
	$t_option = "-t f4";
	$f_option = "-f 65535.0";
    }
    my $fill = $chan_fills[$i];
    my $F_option = "-F $fill";
    do_or_die("fornav 1 -v $t_option $f_option $m_option $F_option " .
	      "-d $weight_distance_max " .
	      "$swath_cols $swath_scans $swath_rows_per_scan " .
	      "$cols_file $rows_file $chan_file " .
	      "$grid_cols $grid_rows $grid_file");
    if (!$keep) {
	do_or_die("rm -f $chan_file");
    }
}

for ($i = 0; $i < $ancil_count; $i++) {
    my $ancil_file = $ancil_files[$i];
    my $ancil = $ancils[$i];
    my $tagext = substr($ancil_conversions[$i], 0, 3);
    my $m_option;
    if ($ancil_weight_types[$i] eq "avg") {
	$m_option = "";
	$tagext .= "a";
    } else {
	$m_option = "-m";
	$tagext .= "m";
    }
    my $grid_file = "$tag\_$tagext\_$ancil\_$grid_cols\_$grid_rows.img";
    my $data_type = $ancil_data_types[$i];
    my $t_option = "-t $data_type";
    my $fill_in;
    if ($data_type eq "u1") {
	$fill_in = 255;
    } elsif ($data_type eq "u2") {
	$fill_in = 0;
    } elsif ($data_type eq "s2") {
	$fill_in = -32767;
    } else {
	$fill_in = -999.0;
    }
    my $f_option = "-f $fill_in";
    my $fill_out = $ancil_fills[$i];
    my $F_option = "-F $fill_out";
    do_or_die("fornav 1 -v $t_option $f_option $m_option $F_option " .
	      "-d $weight_distance_max " .
	      "$swath_cols $swath_scans $swath_rows_per_scan " .
	      "$cols_file $rows_file $ancil_file " .
	      "$grid_cols $grid_rows $grid_file");
    if (!$keep) {
	do_or_die("rm -f $ancil_file");
    }
}

if (!$keep) {
    do_or_die("rm -f $cols_file");
    do_or_die("rm -f $rows_file");
}

warnmail("$script: MESSAGE: done\n");
