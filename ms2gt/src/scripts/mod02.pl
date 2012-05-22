#!/usr/bin/perl -w

# $Id: mod02.pl,v 1.70 2010/09/24 01:00:46 tharan Exp $

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
my $fix250 = 0;
my $fixcolfile1 = "none";
my $fixcolfile2 = "none";
my $fixrowfile1 = "none";
my $fixrowfile2 = "none";
my $tile_cols = 1;
my $tile_rows = 1;
my $tile_overlap = 300;
my $maskfile = "none";
my $mask_factor = 6;
my $mask_keep = 0;
my $swath_width_fraction = 1.0;

if (@ARGV < 4) {
    print $mod02_usage;
    exit 1;
}
if (@ARGV <= 22) {
    $dirinout = shift(@ARGV);
    $tag = shift(@ARGV);
    $listfile = shift(@ARGV);
    $gpdfile = shift(@ARGV);
    my $projection = `projection $gpdfile`;
    chomp $projection;
    if ($projection eq "UNIVERSALTRANSVERSEMERCATOR") {
	$swath_width_fraction = 0.75;
    }
    if (@ARGV) {
        $chanfile = shift(@ARGV);
    }
    if (@ARGV) {
	$ancilfile = shift(@ARGV);
    }
    if (@ARGV) {
	$latlon_src = shift(@ARGV);
	if ($latlon_src ne "1" &&
	    $latlon_src ne "3" &&
	    $latlon_src ne "H" &&
	    $latlon_src ne "Q") {
	    print "invalid latlon_src\n$mod02_usage";
	    exit 1;
	}
    }
    if (@ARGV) {
	$ancil_src = shift(@ARGV);
	if ($ancil_src ne "1" &&
	    $ancil_src ne "3") {
	    print "invalid ancil_src\n$mod02_usage";
	    exit 1;
	}
    }
    if (@ARGV) {
	$keep = shift(@ARGV);
	if ($keep ne "0" && $keep ne "1") {
	    print "invalid keep\n$mod02_usage";
	    exit 1;
	}
    }
    if (@ARGV) {
	$rind = shift(@ARGV);
	if ($rind < 0) {
	    print "invalid rind\n$mod02_usage";
	}
    }
    if (@ARGV) {
	$fix250 = shift(@ARGV);
	if ($fix250 ne "0" && $fix250 ne "1" &&
	    $fix250 ne "2" && $fix250 ne "3") {
	    print "invalid fix250\n$mod02_usage";
	    exit 1;
	}
    }
    if (@ARGV) {
	$fixcolfile1 = shift(@ARGV);
    }
    if (@ARGV) {
	$fixcolfile2 = shift(@ARGV);
    }
    if (@ARGV) {
	$fixrowfile1 = shift(@ARGV);
    }
    if (@ARGV) {
	$fixrowfile2 = shift(@ARGV);
    }
    if (@ARGV) {
	$tile_cols = shift(@ARGV);
	if ($tile_cols < 1) {
	    print "invalid tile_cols\n$mod02_usage";
	}
    }
    if (@ARGV) {
	$tile_rows = shift(@ARGV);
	if ($tile_rows < 1) {
	    print "invalid tile_rows\n$mod02_usage";
	}
    }
    if (@ARGV) {
	$tile_overlap = shift(@ARGV);
	if ($tile_overlap < 0) {
	    print "invalid tile_overlap\n$mod02_usage";
	}
    }
    if (@ARGV) {
	$maskfile = shift(@ARGV);
    }
    if (@ARGV) {
	$mask_factor = shift(@ARGV);
	if ($mask_factor < 1) {
	    print "invalid mask_factor\n$mod02_usage";
	}
    }
    if (@ARGV) {
	$mask_keep = shift(@ARGV);
	if ($mask_keep ne "0" && $mask_keep ne "1") {
	    print "invalid mask_keep\n$mod02_usage";
	    exit 1;
	}
    }
    if (@ARGV) {
	$swath_width_fraction = shift(@ARGV);
	if ($swath_width_fraction < 0.0 || $swath_width_fraction > 1.0) {
	    print "swath_width_fraction must be in the range 0 to 1\n$mod02_usage";
	    exit 1;
	}
    }
} else {
    print $mod02_usage;
    exit 1;
}

print_stderr("\n".
	     "$script: MESSAGE:\n".
	     "> dirinout             = $dirinout\n".
	     "> tag                  = $tag\n".
	     "> listfile             = $listfile\n".
	     "> gpdfile              = $gpdfile\n".
	     "> chanfile             = $chanfile\n".
	     "> ancilfile            = $ancilfile\n".
	     "> latlon_src           = $latlon_src\n".
	     "> ancil_src            = $ancil_src\n".
	     "> keep                 = $keep\n".
	     "> rind                 = $rind\n".
	     "> fix250               = $fix250\n".
	     "> fixcolfile1          = $fixcolfile1\n".
	     "> fixcolfile2          = $fixcolfile2\n".
	     "> fixrowfile1          = $fixrowfile1\n".
	     "> fixrowfile2          = $fixrowfile2\n".
             "> tile_cols            = $tile_cols\n".
             "> tile_rows            = $tile_rows\n".
             "> tile_overlap         = $tile_overlap\n".
             "> maskfile             = $maskfile\n".
	     "> mask_factor          = $mask_factor\n".
             "> mask_keep            = $mask_keep\n".
             "> swath_width_fraction = $swath_width_fraction\n");

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
my @ancil_deletes;
my @ancil_data_types;
if ($ancilfile ne "none") {
    open_or_die("ANCILFILE", "$ancilfile");
    print_stderr("contents of ancilfile (data_type):\n");
    my $line = 0;
    while (<ANCILFILE>) {
	my ($ancil, $conversion, $weight_type, $fill, $delete) =
	    /(\S+)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)/;
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
	if (!defined($delete) || $delete eq "") {
	    $delete = 0;
	}
	my $data_type = "f4";
	if ($ancil eq "ssea" || $ancil eq "csea" ||
	    $ancil eq "ssoa" || $ancil eq "csoa") {
	    if ($conversion eq "scaled") {
		$data_type = "s2";
	    }
	} elsif ($conversion eq "raw") {
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
	push(@ancil_deletes, $delete);
	push(@ancil_data_types, $data_type);
	print "$ancil $conversion $weight_type $fill $delete ($data_type)\n";
	$line++;
	if ($ancil ne "hght" &&
	    $ancil ne "seze" &&
	    $ancil ne "seaz" &&
	    $ancil ne "ssea" &&
	    $ancil ne "csea" &&
	    $ancil ne "rang" &&
	    $ancil ne "soze" &&
	    $ancil ne "soaz" &&
	    $ancil ne "ssoa" &&
	    $ancil ne "csoa" &&
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
my $ancil_mirror = 2;
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
my $this_ancil_cols = 0;
my $this_ancil_rows = 0;
my $this_ancil_mirror = 2;
my $ancil_mirror_expected = 2;
my $ancil_interp_factor;
my $ancil_col_offset = 0;
my $ancil_row_offset = 0;
my $ancil_col_extra = 0;

my $latlon_rows_per_scan;
my $latlon_interp_factor;
my $latlon_col_offset = 0;
my $latlon_row_offset = 0;
my $latlon_col_extra = 0;

my $case;
my $line;
my $hdf;
my $hdf_prefix;
my $platform;
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
    ($ancil_src, $latlon_src, $filestem, $hdf_prefix, $case, $platform) =
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
	$ancil_col_offset = 2;
	$ancil_row_offset = 2;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 5;
	$latlon_col_offset = 2;
	$latlon_row_offset = 2;
	$latlon_col_extra = 1;
	$latlon_rows_per_scan = 2;
    }
    if ($case == 2) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 5;
	$ancil_col_offset = 2;
	$ancil_row_offset = 2;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 1;
	$latlon_filestem =~ s/D021KM/D02HKM/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 3) {
	$swath_resolution = "H";
	$swath_rows_per_scan = 20;
	$ancil_interp_factor = 10;
	$ancil_filestem =~ s/D02HKM/D021KM/;
	$ancil_col_offset = 4;
	$ancil_row_offset = 4;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 2;
	$latlon_row_offset = 0.5;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 4) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 5;
	$ancil_col_offset = 2;
	$ancil_row_offset = 2;
	$ancil_col_extra = 1;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 1;
	$latlon_filestem =~ s/D021KM/D02QKM/; 
	$latlon_rows_per_scan = 10;
    }
    if ($case == 5) {
	$swath_resolution = "Q";
	$swath_rows_per_scan = 40;
	$ancil_interp_factor = 20;
	$ancil_col_offset = 8;
	$ancil_row_offset = 8;
	$ancil_col_extra = 1;
	$ancil_filestem =~ s/D02QKM/D021KM/;
	$ancil_rows_per_scan = 2;
	$latlon_interp_factor = 4;
	$latlon_row_offset = 1.5;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 6) {
	$swath_resolution = "1";
	$swath_rows_per_scan = 10;
	$ancil_interp_factor = 1;
	$ancil_filestem =~ s/D021KM/D03/;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 1;
	$latlon_filestem =~ s/D021KM/D03/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 7) {
	$swath_resolution = "H";
	$swath_rows_per_scan = 20;
	$ancil_interp_factor = 2;
	$ancil_row_offset = 0.5;
	$ancil_filestem =~ s/D02HKM/D03/;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 2;
	$latlon_row_offset = 0.5;
	$latlon_filestem =~ s/D02HKM/D03/;
	$latlon_rows_per_scan = 10;
    }
    if ($case == 8) {
	$swath_resolution = "Q";
	$swath_rows_per_scan = 40;
	$ancil_interp_factor = 4;
	$ancil_row_offset = 1.5;
	$ancil_filestem =~ s/D02QKM/D03/;
	$ancil_rows_per_scan = 10;
	$latlon_interp_factor = 4;
	$latlon_row_offset = 1.5;
	$latlon_filestem =~ s/D02QKM/D03/;
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
		    "listfile $listfile must contain MOD02 or MYD02 files " .
		    "since chanfile is not none");
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
my $force = ($latlon_interp_factor == 1 && $rind != 0) ? "-r $rind" : "-f";
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
    my $grid_check = "";
    if ($rind != 0) {
	my $col_min = -$rind;
	my $col_max = $grid_cols + $rind - 1;
	my $row_min = -$rind;
	my $row_max = $grid_rows + $rind - 1;
	$grid_check = "grid_check=[$col_min,$col_max,$row_min,$row_max] ";
    }

    do_or_die("idl_sh.pl interp_colrow " .
	      "$latlon_interp_factor $cr_cols $cr_scans $cr_rows_per_scan " .
	      "\"'$cols_file'\" \"'$rows_file'\" " .
	      "$swath_cols \"'$tag'\" " .
	      $grid_check .
	      "col_offset=$latlon_col_offset row_offset=$latlon_row_offset");
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
	    my $extract_command = 
		"idl_sh.pl extract_chan \"'$hdf'\" \"'$filestem'\" " .
		"$chan conversion=\"'$conversion'\" " .
		"swath_rows=$this_swath_rows_max " .
		"swath_row_first=$this_swath_row_first";
	    print_stderr($extract_command);
	    do_or_die($extract_command);
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
	    my $extract_command =
		"idl_sh.pl extract_ancil \"'$hdf_ancil'\" " .
		"\"'$ancil_filestem'\" \"'$ancil'\" " .
		"conversion=\"'$conversion'\" " .
		"swath_rows=$this_ancil_rows_max " .
		"swath_row_first=$this_ancil_row_first";
	    print_stderr($extract_command);
	    do_or_die($extract_command);
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
	    if ($this_ancil_mirror != $ancil_mirror_expected &&
		($fix250 == 1 || $fix250 == 2)) {
		diemail("$script: FATAL: expected $ancil_file to start on " .
			"mirror side $ancil_mirror_expected");
	    }
	    if ($i < $ancil_count - 1) {
		$ancil_mirror_expected = $this_ancil_mirror;
	    } else {
		$ancil_mirror_expected = ($this_ancil_mirror < 2) ?
		    ($this_ancil_mirror + 
		     $this_ancil_rows / $ancil_rows_per_scan) % 2 : 2;
	    }
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
		$ancil_col_extra != $this_swath_cols) {
		diemail("$script: FATAL: " .
			"inconsistent number of columns in $ancil_file");
	    }
	    if ($ancil_interp_factor * $this_ancil_rows != $this_swath_rows) {
		diemail("$script: FATAL: " .
			"inconsistent number of rows in $ancil_file");
	    }
	    $ancil_cat[$i] .= "$ancil_file ";
	}
	if ($line == 0) {
	    $ancil_mirror = $this_ancil_mirror;
	}
	$ancil_cols = $this_ancil_cols;
	$ancil_rows += $this_ancil_rows;
	$this_ancil_row_first = 0;
	$this_ancil_rows_max -= $this_ancil_rows;
    } else {
	$this_ancil_row_first -= $ancil_rows_expected;
    }
}
my $swath_col_start = 0;
my $swath_cols_new = $swath_cols;
my $swath_cols_s;
my $swath_cols_new_s;
if ($swath_width_fraction != 1.0) {
    $swath_col_start = int((1.0 - $swath_width_fraction) * 0.5 * $swath_cols);
    $swath_cols_new = $swath_cols - 2 * $swath_col_start;
    $swath_cols_s     = sprintf("_%05d_", $swath_cols);
    $swath_cols_new_s = sprintf("_%05d_", $swath_cols_new);

    my $cols_file_fixed = $cols_file;
    $cols_file_fixed =~ s/$swath_cols_s/$swath_cols_new_s/;
    do_or_die("extract_region -v 4 $swath_cols $swath_rows " .
	      "$swath_col_start 0 $swath_cols_new $swath_rows " .
	      "$cols_file $cols_file_fixed");

    my $rows_file_fixed = $rows_file;
    $rows_file_fixed =~ s/$swath_cols_s/$swath_cols_new_s/;
    do_or_die("extract_region -v 4 $swath_cols $swath_rows " .
	      "$swath_col_start 0 $swath_cols_new $swath_rows " .
	      "$rows_file $rows_file_fixed");

    if (!$keep) {
	do_or_die("rm -f $cols_file");
	do_or_die("rm -f $rows_file");
    }

    $cols_file = $cols_file_fixed;
    $rows_file = $rows_file_fixed;
}

$swath_cols = sprintf("%05d", $swath_cols);
$swath_rows = sprintf("%05d", $swath_rows);
$ancil_cols = sprintf("%05d", $ancil_cols);
$ancil_rows = sprintf("%05d", $ancil_rows);

my @chan_files;
my $got_not_1_or_2 = 0;
for ($i = 0; $i < $chan_count; $i++) {
    my $chan = $chans[$i];
    if ($chan != 1 && $chan != 2) {
	$got_not_1_or_2 = 1;
    }
    my $chan_rm = $chan_cat[$i];
    my $tagext = substr($chan_conversions[$i], 0, 3);
    $chan_rm =~ s/cat/rm -f/;
    $chan_files[$i] = "$tag\_$tagext\_ch$chan\_$swath_cols\_$swath_rows.img";
    do_or_die("$chan_cat[$i] >$chan_files[$i]");
    do_or_die("$chan_rm");
}
if (($fix250 == 1 || $fix250 == 2) && $got_not_1_or_2 == 1) {
    diemail("$script: FATAL:" .
	    " if fix250 is 1 or 2, then only channels 1 and/or 2 may be\n" .
	    "  specified in chanfile");
}

my @ancil_files;
my $soze_file = "";
my $soze_conv = "";
for ($i = 0; $i < $ancil_count; $i++) {
    my $ancil = $ancils[$i];
    my $ancil_rm = $ancil_cat[$i];
    my $tagext = substr($ancil_conversions[$i], 0, 3);
    $ancil_rm =~ s/cat/rm -f/;
    $ancil_files[$i] =
	"$tag\_$tagext\_$ancil\_$ancil_mirror\_$ancil_cols\_$ancil_rows.img";
    do_or_die("$ancil_cat[$i] >$ancil_files[$i]");
    do_or_die("$ancil_rm");
    if ($ancil eq "soze") {
	$soze_file = $ancil_files[$i];
	$soze_conv = $ancil_conversions[$i];
    }
}

if ($fix250 != 0 && ($soze_file eq "" || $soze_conv ne "raw")) {
    diemail("$script: FATAL:" .
	    " if fix250 is not 0, then soze must be specified in ancilfile,\n".
	    "  and soze conversion must be set to raw");
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
		  "col_offset=$ancil_col_offset row_offset=$ancil_row_offset " .
		  "$nearest_neighbor mirror_side=$ancil_mirror");

	my @ancil_glob = glob("$filestem_ancil_conv*");
	if (@ancil_glob == 0) {
	    diemail("$script: FATAL: $filestem_ancil_conv* not found");
	}
	do_or_die("rm -f $ancil_file");
	$ancil_file = $ancil_glob[0];
	$ancil_files[$i] = $ancil_file;
	if ($ancil eq "soze") {
	    $soze_file = $ancil_files[$i];
	}
	($this_ancil_mirror, $this_ancil_cols, $this_ancil_scans,
	 $this_ancil_scan_first, $this_ancil_rows_per_scan) =
	 ($ancil_file =~
	  /$filestem_ancil_conv\_(.)_(.....)_(.....)_(.....)_(..)/);
	print "$ancil_file starts on mirror side $this_ancil_mirror and\n" .
	  "  contains $this_ancil_cols cols,\n" .
	  "   $this_ancil_scans scans, $this_ancil_scan_first scan_first,\n" .
	  "   and $this_ancil_rows_per_scan rows_per_scan\n";

	if ($this_ancil_mirror != $ancil_mirror ||
	    $this_ancil_cols != $swath_cols ||
	    $this_ancil_scans != $swath_scans ||
	    $this_ancil_scan_first != 0 ||
	    $this_ancil_rows_per_scan != $swath_rows_per_scan) {
	    diemail("$script: FATAL: " .
		    "inconsistent size for $ancil_file");
	}
    }
}

my $tile_grid_cols = $grid_cols / $tile_cols;
my $tile_grid_rows = $grid_rows / $tile_rows;
my $tile_col;
my $tile_row;
for ($tile_row = 0; $tile_row < $tile_rows; $tile_row++) {
    my $tile_row_offset = $tile_row * $tile_grid_rows;
    my $tile_row_offset_this = $tile_row_offset;
    my $tile_grid_rows_this = $tile_grid_rows + $tile_overlap;
    if ($tile_row > 0) {
	$tile_row_offset_this -= $tile_overlap;
	$tile_grid_rows_this += $tile_overlap;
    }
    if ($tile_row == $tile_rows - 1) {
	$tile_grid_rows_this = $grid_rows - $tile_row_offset_this;
    }
    for ($tile_col = 0; $tile_col < $tile_cols; $tile_col++) {
	my $tile_col_offset = $tile_col * $tile_grid_cols;
	my $tile_col_offset_this = $tile_col_offset;
	my $tile_grid_cols_this = $tile_grid_cols + $tile_overlap;
	if ($tile_col > 0) {
	    $tile_col_offset_this -= $tile_overlap;
	    $tile_grid_cols_this += $tile_overlap;
	}
	if ($tile_col == $tile_cols - 1) {
	    $tile_grid_cols_this = $grid_cols - $tile_col_offset_this;
	}
	my $tile_num = $tile_row * $tile_cols + $tile_col;
	my $tile_ext = "";
	my $tile_ext_this = "";
	if ($tile_cols > 1 || $tile_rows > 1) {
	    $tile_ext = sprintf("_%02d", $tile_num);
	    $tile_ext_this = $tile_ext;
	    if ($tile_overlap > 0) {
		$tile_ext_this .= sprintf("_%05d_%05d",
					  $tile_col_offset_this,
					  $tile_row_offset_this);
	    }
	}
	my $command;
	my $mask_tile = "";
	if ($maskfile ne "none") {
	    #
	    #  First try to make a low-res mask without overlap.
	    #  If it exists, then make make the high-res mask with overlap.
	    #
	    $mask_tile = sprintf("%s_mask%s_%05d_%05d.img",
				 $tag, $tile_ext,
				 $tile_grid_cols,
				 $tile_grid_rows);
	    my $mask_bytes_per_cell = 1;
	    my $mask_cols_in = $grid_cols / $mask_factor;
	    my $mask_rows_in = $grid_rows / $mask_factor;
	    my $mask_col_start_in = $tile_col_offset / $mask_factor;
	    my $mask_row_start_in = $tile_row_offset / $mask_factor;
	    my $mask_cols_in_region = $tile_grid_cols / $mask_factor;
	    my $mask_rows_in_region = $tile_grid_rows / $mask_factor;
	    $command = "make_mask -v -d " .
		"$mask_bytes_per_cell $mask_cols_in $mask_rows_in " .
		"$mask_col_start_in $mask_row_start_in " .
		"$mask_cols_in_region $mask_rows_in_region " .
		"$maskfile $mask_tile";
	    do_or_die($command);
	    if (-e $mask_tile) {
		system("rm -f $mask_tile");
		$mask_tile = sprintf("%s_mask%s_%05d_%05d.img",
				     $tag, $tile_ext_this,
				     $tile_grid_cols_this,
				     $tile_grid_rows_this);
		$mask_col_start_in = $tile_col_offset_this / $mask_factor;
		$mask_row_start_in = $tile_row_offset_this / $mask_factor;
		$mask_cols_in_region = $tile_grid_cols_this / $mask_factor;
		$mask_rows_in_region = $tile_grid_rows_this / $mask_factor;
		$command = "make_mask -v -d -F $mask_factor " .
		    "$mask_bytes_per_cell $mask_cols_in $mask_rows_in " .
		    "$mask_col_start_in $mask_row_start_in " .
		    "$mask_cols_in_region $mask_rows_in_region " .
		    "$maskfile $mask_tile";
		do_or_die($command);
	    }
	}
	my $grid_file = "";
	for ($i = 0; $i < $chan_count; $i++) {
	    my $chan_file = $chan_files[$i];
	    my $chan = $chans[$i];
	    if ($fix250 &&
		$tile_col == 0 &&
		$tile_row == 0) {
		my $chan_file_unfixed = $chan_file . ".unfixed";
		do_or_die("mv $chan_file $chan_file_unfixed");
		my $reg_col_offset = "";
		my $interp_cols = "";
		my $reg_cols = "";
		my $nor_rows = "";
		my $reg_rows = "";
		my $undo_soze = "";
		my $file_reg_cols_in = "";
		my $file_reg_cols_out = "";
		my $file_reg_rows_in = "";
		my $file_reg_rows_out = "";
		my $reg_row_mirror_side = "";
		my $fixcolfile = "";
		my $fixrowfile = "";
		if ($fix250 == 1 || $fix250 == 2) {
		    if ($chan == 1) {
			$reg_col_offset = "reg_col_offset=3";
			$fixcolfile = $fixcolfile1;
			$fixrowfile = $fixrowfile1;
		    } elsif ($chan == 2) {
			$reg_col_offset = "reg_col_offset=0";
			$fixcolfile = $fixcolfile2;
			$fixrowfile = $fixrowfile2;
		    } else {
			diemail("$script: FATAL: " .
				"chan must be 1 or 2 if fix250 is 1 or 2");
		    }
		    if ($fixcolfile eq "none") {
			if ($platform eq "terra") {
			    $interp_cols = "/interp_cols";
			}
			$file_reg_cols_out = "file_reg_cols_out=\"'$chan_file" . ".colfix'\"";
		    } elsif ($platform eq "terra") {
			$file_reg_cols_in =
			    "file_reg_cols_in=\"'$fixcolfile'\"";
		    }
		    if ($fixrowfile eq "none") {
			$nor_rows = "/nor_rows";
			$reg_rows = "/reg_rows";
			$file_reg_rows_out = "file_reg_rows_out=\"'$chan_file" . ".rowfix'\"";
		    } else {
			$file_reg_rows_in = "file_reg_rows_in=\"'$fixrowfile'\"";
		    }
		    if ($fix250 == 2) {
			$undo_soze = "/undo_soze";
		    }
		    if ($ancil_mirror != 2) {
			$reg_row_mirror_side = "reg_row_mirror_side=$ancil_mirror";
		    }
		}
		my $data_type = $chan_conversions[$i] eq "raw" ? "u2" : "f4";
		my $data_type_in = "data_type_in=\"'$data_type'\"";
		my $data_type_out = "data_type_out=\"'$data_type'\"";
		
		$command = "idl_sh.pl modis_adjust $swath_cols $swath_scans " .
		    "\"'$chan_file_unfixed'\" \"'$chan_file'\" " .
		    "file_soze=\"'$soze_file'\" " .
		    "$interp_cols $reg_cols $reg_col_offset " .
		    "$nor_rows $reg_rows $undo_soze " .
		    "$data_type_in $data_type_out " .
		    "$file_reg_cols_in $file_reg_cols_out " .
		    "$file_reg_rows_in $file_reg_rows_out " .
		    "$reg_row_mirror_side";
		print_stderr("$command\n");
		do_or_die($command);
		if (!$keep) {
		    system("rm -f $chan_file_unfixed");
		}
	    }
	    if ((!$grid_file || -e $grid_file) &&
		(!$mask_tile || -e $mask_tile)) {
		my $tagext = substr($chan_conversions[$i], 0, 3);
		my $m_option;
		if ($chan_weight_types[$i] eq "avg") {
		    $m_option = "";
		    $tagext .= "a";
		} else {
		    $m_option = "-m";
		    $tagext .= "m";
		}
		$tagext .= $tile_ext_this;
		$grid_file = sprintf("%s_%s_ch%s_%05d_%05d.img",
				     $tag, $tagext, $chan,
				     $tile_grid_cols_this,
				     $tile_grid_rows_this);
		my $t_option;
		my $f_option;
		my $bytes_per_cell;
		if ($chan_conversions[$i] eq "raw") {
		    $t_option = "-t u2";
		    $f_option = "-f 65535";
		    $bytes_per_cell = 2;
		} else {
		    $t_option = "-t f4";
		    $f_option = "-f 65535.0";
		    $bytes_per_cell = 4;
		}
		if ($swath_width_fraction != 1.0) {
		    my $chan_file_fixed = $chan_file;
		    $chan_file_fixed =~ s/$swath_cols_s/$swath_cols_new_s/;
		    do_or_die("extract_region -v $bytes_per_cell " .
			      "$swath_cols $swath_rows " .
			      "$swath_col_start 0 $swath_cols_new " .
			      "$swath_rows " .
			      "$chan_file $chan_file_fixed");
		    if (!$keep) {
			do_or_die("rm -f $chan_file");
		    }
		    $chan_file = $chan_file_fixed;
		}
		my $fill = $chan_fills[$i];
		my $F_option = "-F $fill";
		my $C_option = "-C $tile_col_offset_this";
		my $R_option = "-R $tile_row_offset_this";
		do_or_die("fornav 1 -v $t_option $f_option " .
			  "$m_option $F_option " .
			  "-d $weight_distance_max $C_option $R_option " .
			  "$swath_cols_new $swath_scans $swath_rows_per_scan " .
			  "$cols_file $rows_file $chan_file " .
			  "$tile_grid_cols_this $tile_grid_rows_this " .
			  "$grid_file");
		if (-e $grid_file && $mask_tile) {
		    my $grid_file_unmasked = $grid_file . ".unmasked";
		    do_or_die("mv $grid_file $grid_file_unmasked");
		    do_or_die("apply_mask -v -d $bytes_per_cell " .
			      "$tile_grid_cols_this $tile_grid_rows_this " .
			      "0 0 " .
			      "$tile_grid_cols_this $tile_grid_rows_this " .
			      "$mask_tile $grid_file_unmasked $grid_file");
		    if (!$keep) {
			system("rm -f $grid_file_unmasked");
		    }
		}
	    }
	    if (!$keep &&
		$tile_col == $tile_cols - 1 &&
		$tile_row == $tile_rows - 1) {
		do_or_die("rm -f $chan_file");
	    }
	}

	for ($i = 0; $i < $ancil_count; $i++) {
	    my $ancil_file = $ancil_files[$i];
	    if (!$ancil_deletes[$i] &&
		(!$grid_file || -e $grid_file) &&
		(!$mask_tile || -e $mask_tile)) {
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
		$tagext .= $tile_ext_this;
		$grid_file = sprintf("%s_%s_%s_%05d_%05d.img",
				     $tag, $tagext, $ancil,
				     $tile_grid_cols_this,
				     $tile_grid_rows_this);
		my $data_type = $ancil_data_types[$i];
		my $t_option = "-t $data_type";
		my $fill_in;
		my $bytes_per_cell;
		if ($data_type eq "u1") {
		    $fill_in = 255;
		    $bytes_per_cell = 1;
		} elsif ($data_type eq "u2") {
		    $fill_in = 0;
		    $bytes_per_cell = 2;
		} elsif ($data_type eq "s2") {
		    $fill_in = -32767;
		    $bytes_per_cell = 2;
		} else {
		    $fill_in = -999.0;
		    $bytes_per_cell = 4;
		}
		if ($swath_width_fraction != 1.0) {
		    my $ancil_file_fixed = $ancil_file;
		    $ancil_file_fixed =~ s/$swath_cols_s/$swath_cols_new_s/;
		    do_or_die("extract_region -v $bytes_per_cell " .
			      "$swath_cols $swath_rows " .
			      "$swath_col_start 0 $swath_cols_new " .
			      "$swath_rows " .
			      "$ancil_file $ancil_file_fixed");
		    if (!$keep) {
			do_or_die("rm -f $ancil_file");
		    }
		    $ancil_file = $ancil_file_fixed;
		}
		my $f_option = "-f $fill_in";
		my $fill_out = $ancil_fills[$i];
		my $F_option = "-F $fill_out";
		my $C_option = "-C $tile_col_offset_this";
		my $R_option = "-R $tile_row_offset_this";
		do_or_die("fornav 1 -v $t_option $f_option " .
			  "$m_option $F_option " .
			  "-d $weight_distance_max $C_option $R_option " .
			  "$swath_cols_new $swath_scans $swath_rows_per_scan " .
			  "$cols_file $rows_file $ancil_file " .
			  "$tile_grid_cols_this $tile_grid_rows_this " .
			  "$grid_file");
		if (-e $grid_file && $mask_tile) {
		    my $grid_file_unmasked = $grid_file . ".unmasked";
		    do_or_die("mv $grid_file $grid_file_unmasked");
		    do_or_die("apply_mask -v -d $bytes_per_cell " .
			      "$tile_grid_cols_this $tile_grid_rows_this " .
			      "0 0 " .
			      "$tile_grid_cols_this $tile_grid_rows_this " .
			      "$mask_tile $grid_file_unmasked $grid_file");
		    if (!$keep) {
			system("rm -f $grid_file_unmasked");
		    }
		}
	    }
	    if (!$keep &&
		$tile_col == $tile_cols - 1 &&
		$tile_row == $tile_rows - 1) {
		do_or_die("rm -f $ancil_file");
	    }
	}
	if (!$mask_keep && $mask_tile) {
	    do_or_die("rm -f $mask_tile");
	}
    }
}

if (!$keep) {
    do_or_die("rm -f $cols_file");
    do_or_die("rm -f $rows_file");
}

warnmail("$script: MESSAGE: done\n");
