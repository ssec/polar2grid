#!/usr/bin/perl -w

# $Id: mod35_l2.pl,v 1.4 2007/01/29 23:38:32 tharan Exp $

#========================================================================
# mod35_l2.pl - grids MOD35_L2 data
#
# 28-Jan-2001 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

$|=1;

$path_ms2gt_src = $ENV{PATH_MS2GT_SRC};
$source_ms2gt = "$path_ms2gt_src/scripts";

require("$source_ms2gt/mod35_l2_usage.pl");
require("$source_ms2gt/setup.pl");
require("$source_ms2gt/error_mail.pl");

# global variables defined in setup.pl and used only once here.
# dummy assignment here to supress warning messages.

$junk = $weight_distance_max;
$junk = $junk;

# define a global used by do_or_die and invoke_or_die

$script = "MOD35_L2";

# Set command line defaults

my $dirinout;
my $tag;
my $listfile;
my $gpdfile;
my $chanlist;
my $ancilfile = "none";
my $latlonlistfile = "none";
my $keep = 0;
my $rind = 50;

if (@ARGV < 5) {
    print $mod35_l2_usage;
    exit 1;
}
if (@ARGV <= 9) {
    $dirinout = $ARGV[0];
    $tag = $ARGV[1];
    $listfile = $ARGV[2];
    $gpdfile = $ARGV[3];
    $chanfile = $ARGV[4];
    if (@ARGV >= 6) {
	$ancilfile = $ARGV[5];
	if (@ARGV >= 7) {
	    $latlonlistfile = $ARGV[6];
	    if (@ARGV >= 8) {
		$keep = $ARGV[7];
		if ($keep ne "0" && $keep ne "1") {
		    print "invalid keep\n$mod35_l2_usage";
		    exit 1;
		}
		if (@ARGV >= 9) {
		    $rind = $ARGV[8];
		}
	    }
	}
    }
} else {
    print $mod35_l2_usage;
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
	     "> latlonlistfile   = $latlonlistfile\n".
	     "> keep             = $keep\n".
	     "> rind             = $rind\n");

chdir_or_die($dirinout);

my @list;
open_or_die("LISTFILE", "$listfile");
print_stderr("contents of listfile:\n");
while (<LISTFILE>) {
    my ($file) = /\s*(\S+)/;
    if (defined($file)) {
	chomp $file;
	push(@list, $file);
	print STDERR "$file\n";
    }
}
close(LISTFILE);

my @chans;
open_or_die("CHANFILE", "$chanfile");
print_stderr("contents of chanfile:\n");
my $line = 0;
while (<CHANFILE>) {
    my ($chan) = /(\S+)/;
    if (!defined($chan)) {
	$chan = "";
    }
    chomp $chan;
    push(@chans, $chan);
    print "$chan\n";
    $line++;
    if ($chan ne "time" &&
	$chan ne "cld0" &&
	$chan ne "cld1" &&
	$chan ne "cld2" &&
	$chan ne "cld3" &&
	$chan ne "cld4" &&
	$chan ne "cld5" &&
	$chan ne "cqa0" &&
	$chan ne "cqa1" &&
	$chan ne "cqa2" &&
	$chan ne "cqa3" &&
	$chan ne "cqa4" &&
	$chan ne "cqa5" &&
	$chan ne "cqa6" &&
	$chan ne "cqa7" &&
	$chan ne "cqa8" &&
	$chan ne "cqa9") {
	diemail("$script: FATAL: " .
		"invalid channel on line $line in $chanfile\n");
    }
}
close(CHANFILE);
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

my @latlonlist;
if ($latlonlistfile ne "none") {
    open_or_die("LATLONLISTFILE", "$latlonlistfile");
    print_stderr("contents of latlonlistfile:\n");
    while (<LATLONLISTFILE>) {
	push(@latlonlist, $_);
	print STDERR "$_";
    }
    close(LATLONLISTFILE);
}

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

my $hdf;
my $swath_cols = 0;
my $swath_rows = 0;
my $swath_scans = 0;
my $latlon_cols = 0;
my $latlon_rows = 0;
my $swath_rows_per_scan = 10;
my $this_swath_cols;
my $this_swath_rows;
my $ancil_mirror = 2;
my $this_ancil_cols;
my $this_ancil_rows = 0;
my $this_ancil_mirror = 2;
my $ancil_mirror_expected = 2;
my $interp_factor;
my $offset = 0;
my $missing_latlon_col = 0;
my $extra_latlon_col = 0;
my $latlon_rows_per_scan = 2;
my $ancil_rows_per_scan = $latlon_rows_per_scan;
my $list_index = 0;
my $lat_cat = "cat ";
my $lon_cat = "cat ";
my $i;
my @chan_cat;
for ($i = 0; $i < $chan_count; $i++) {
    $chan_cat[$i] = "cat ";
}
my @ancil_cat;
for ($i = 0; $i < $ancil_count; $i++) {
    $ancil_cat[$i] = "cat ";
}

foreach $hdf (@list) {
    chomp $hdf;
    my ($filestem) = ($hdf =~ /(.*)\.hdf/);
    my $filestem_lat = $filestem . "_latf_";
    my $filestem_lon = $filestem . "_lonf_";
    do_or_die("rm -f $filestem_lat*");
    do_or_die("rm -f $filestem_lon*");
    my $hdf_latlon = $hdf;
    my $latlon_filestem = $filestem;
    if (scalar(@latlonlist) == 0) {
	$interp_factor = 5;
	$offset = 2;
	$missing_latlon_col = 1;
	$extra_latlon_col = 1;
    } else {
	$latlon_rows_per_scan = 10;
	$ancil_rows_per_scan = $latlon_rows_per_scan;
	$interp_factor = 1;
	$hdf_latlon   = $latlonlist[$list_index++];
	chomp $hdf_latlon;
	($latlon_filestem) = ($hdf_latlon =~ /(.*)\.hdf/);
    }
    for ($i = 0; $i < $chan_count; $i++) {
	my $chan = $chans[$i];
	my $filestem_chan = $filestem . "_$chan\_raw_";
	do_or_die("rm -f $filestem_chan*");
	my $get_latlon = "";
	if ($i == 0) {
	    if (scalar(@latlonlist) == 0) {
		$get_latlon = "/get_latlon";
	    } else {
		$filestem_lat = $latlon_filestem . "_latf_";
		$filestem_lon = $latlon_filestem . "_lonf_";
		do_or_die("rm -f $filestem_lat*");
		do_or_die("rm -f $filestem_lon*");
		do_or_die("idl_sh.pl extract_latlon \"'$hdf_latlon'\" " .
			  "\"'$latlon_filestem'\"");
	    }
	}
	do_or_die("idl_sh.pl extract_chan \"'$hdf'\" \"'$filestem'\" \"'$chan'\" " .
		  "$get_latlon");
	my @chan_glob = glob("$filestem_chan*");
	my $chan_file = $chan_glob[0];
	($this_swath_cols, $this_swath_rows) =
	    ($chan_file =~ /$filestem_chan(.....)_(.....)/);
	print "$chan_file contains $this_swath_cols cols and " .
	    "$this_swath_rows rows\n";
	if ($swath_cols == 0) {
	    $swath_cols = $this_swath_cols;
	}
	if ($this_swath_cols != $swath_cols) {
	    diemail("$script: FATAL: " .
		    "inconsistent number of columns in $chan_file");
	}
	$chan_cat[$i] .= "$chan_file ";
	if ($i == 0) {
	    $swath_rows += $this_swath_rows;
	}
    }

    my @lat_glob = glob("$filestem_lat*");
    my $lat_file = $lat_glob[0];
    my ($this_lat_cols, $this_lat_rows) =
	($lat_file =~ /$filestem_lat(.....)_(.....)/);
    print "$lat_file contains $this_lat_cols cols and " .
	  "$this_lat_rows rows\n";
    if ($interp_factor * ($this_lat_cols + $missing_latlon_col) -
	$extra_latlon_col != $this_swath_cols ||
	$interp_factor * $this_lat_rows != $this_swath_rows) {
	diemail("$script: FATAL: " .
		"inconsistent size for $lat_file");
    }
    $lat_cat .= "$lat_file ";
    $latlon_cols = $this_lat_cols;
    $latlon_rows += $this_lat_rows;

    my @lon_glob = glob("$filestem_lon*");
    my $lon_file = $lon_glob[0];
    my ($this_lon_cols, $this_lon_rows) =
	($lon_file =~ /$filestem_lon(.....)_(.....)/);
    print "$lon_file contains $this_lon_cols cols and " .
	  "$this_lon_rows rows\n";
    if ($interp_factor * ($this_lon_cols + $missing_latlon_col) -
	$extra_latlon_col != $this_swath_cols ||
	$interp_factor * $this_lon_rows != $this_swath_rows) {
	diemail("$script: FATAL: " .
		"inconsistent size for $lon_file");
    }
    $lon_cat .= "$lon_file ";

    my $ancil_filestem = $latlon_filestem;
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
		  "conversion=\"'$conversion'\" ");
	@ancil_glob = glob("$filestem_ancil_conv*");
	if (@ancil_glob == 0) {
	    diemail("$script: FATAL: $filestem_ancil_conv* not found");
	}
	my $ancil_file = $ancil_glob[0];
	($this_ancil_mirror, $this_ancil_cols, $this_ancil_rows) =
	    ($ancil_file =~ /$filestem_ancil_conv(.)_(.....)_(.....)/);
	print "$ancil_file starts on mirror side $this_ancil_mirror and\n" .
	    "   contains $this_ancil_cols cols and $this_ancil_rows rows\n";
	if ($ancil_mirror_expected == 2) {
	    $ancil_mirror_expected = $this_ancil_mirror;
	}
	if ($this_ancil_mirror != $ancil_mirror_expected) {
	    diemail("$script: FATAL: expected $ancil_file to start on" .
		    "mirror side $ancil_mirror_expected");
	}
	if ($i < $ancil_count - 1) {
	    $ancil_mirror_expected = $this_ancil_mirror;
	} else {
	    $ancil_mirror_expected = ($this_ancil_mirror < 2) ?
		($this_ancil_mirror + 
		 $this_ancil_rows / $ancil_rows_per_scan) % 2 : 2;
	}
	$ancil_cat[$i] .= "$ancil_file ";
    }
    if ($line == 0) {
	$ancil_mirror = $this_ancil_mirror;
    }
}
$swath_rows = sprintf("%05d", $swath_rows);
$latlon_cols = sprintf("%05d", $latlon_cols);
$latlon_rows = sprintf("%05d", $latlon_rows);
$swath_scans = $swath_rows / $swath_rows_per_scan;

my @chan_files;
for ($i = 0; $i < $chan_count; $i++) {
    my $chan = $chans[$i];
    my $chan_rm = $chan_cat[$i];
    $chan_rm =~ s/cat/rm -f/;
    $chan_files[$i] = "$tag\_$chan\_$swath_cols\_$swath_rows.img";
    do_or_die("$chan_cat[$i] >$chan_files[$i]");
    do_or_die("$chan_rm");
}

my $ancil_interp_factor = $interp_factor;
my $ancil_rows = $latlon_rows;
my $ancil_cols = $latlon_cols;
my @ancil_files;
for ($i = 0; $i < $ancil_count; $i++) {
    my $ancil = $ancils[$i];
    my $ancil_rm = $ancil_cat[$i];
    my $tagext = substr($ancil_conversions[$i], 0, 3);
    $ancil_rm =~ s/cat/rm -f/;
    $ancil_files[$i] =
	"$tag\_$tagext\_$ancil\_$ancil_mirror\_$ancil_cols\_$ancil_rows.img";
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
		  "$nearest_neighbor mirror_side=$ancil_mirror");

	my @ancil_glob = glob("$filestem_ancil_conv*");
	if (@ancil_glob == 0) {
	    diemail("$script: FATAL: $filestem_ancil_conv* not found");
	}
	do_or_die("rm -f $ancil_file");
	$ancil_file = $ancil_glob[0];
	$ancil_files[$i] = $ancil_file;
	($this_ancil_mirror, $this_ancil_cols, $this_ancil_scans,
	 $this_ancil_scan_first, $this_ancil_rows_per_scan) =
	 ($ancil_file =~
	  /$filestem_ancil_conv\_(.)_(.....)_(.....)_(.....)_(..)/);
	print "$ancil_file starts on mirror side $this_ancil_mirror and\n" .
	  "  contains $this_ancil_cols cols,\n" .
	  "   $this_ancil_scans scans, $this_ancil_scan_first scan_first,\n" .
	  "   and $this_ancil_rows_per_scan rows_per_scan\n";

	if ($this_ancil_mirror != $ancil_mirror ||
	    $this_ancil_scans != $swath_scans ||
	    $this_ancil_scan_first != 0 ||
	    $this_ancil_rows_per_scan != $swath_rows_per_scan) {
	    diemail("$script: FATAL: " .
		    "inconsistent size for $ancil_file");
	}
    }
}

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
my $force = ($interp_factor == 1) ? "-r $rind" : "-f";
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

if ($interp_factor > 1) {
    my $col_min = -$rind;
    my $col_max = $grid_cols + $rind - 1;
    my $row_min = -$rind;
    my $row_max = $grid_rows + $rind - 1;

    do_or_die("idl_sh.pl interp_colrow " .
	      "$interp_factor $cr_cols $cr_scans $cr_rows_per_scan " .
	      "\"'$cols_file'\" \"'$rows_file'\" " .
	      "$swath_cols \"'$tag'\" " .
	      "grid_check=[$col_min,$col_max,$row_min,$row_max] " .
	      "col_offset=$offset row_offset=$offset");
    do_or_die("rm -f $cols_file");
    do_or_die("rm -f $rows_file");

    $filestem_cols = $tag . "_cols_";
    @cols_glob = glob("$filestem_cols*");
    $cols_file = $cols_glob[0];
    ($this_cols_cols, $this_cols_scans,
     $this_cols_scan_first, $this_cols_rows_per_scan) =
	 ($cols_file =~ /$filestem_cols(.....)_(.....)_(.....)_(..)/);
    print "$cols_file contains $this_cols_cols cols,\n" .
	  "   $this_cols_scans scans, $this_cols_scan_first scan_first,\n" .
	  "   and $this_cols_rows_per_scan rows_per_scan\n";

    $filestem_rows = $tag . "_rows_";
    @rows_glob = glob("$filestem_rows*");
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

if ($swath_cols != $cr_cols) {
    diemail("$script: FATAL: " .
	    "swath_cols: $swath_cols is not equal to cr_cols: $cr_cols");
}
if ($swath_rows_per_scan != $cr_rows_per_scan) {
    diemail("$script: FATAL: " .
	    "swath_rows_per_scan: $swath_rows_per_scan is not equal to cr_rows_per_scan: $cr_rows_per_scan");
}

$swath_scans = $cr_scans;
my $swath_scan_first = $cr_scan_first;

for ($i = 0; $i < $chan_count; $i++) {
    my $chan_file = $chan_files[$i];
    my $chan_name = $chans[$i];
    my $tagext = "rawm";
    my $t_option = "-t u1";
    my $f_option = "-f 0";
    if ($chan_name eq "time") {
	$t_option = "-t f8";
	$f_option = "-f -999.9002";
    }
    my $grid_file = "$tag\_$tagext\_$chan_name\_$grid_cols\_$grid_rows.img";
    do_or_die("fornav 1 -v -m $t_option $f_option " .
	      "-s $swath_scan_first 0 " .
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
              "-s $swath_scan_first 0 " .
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
