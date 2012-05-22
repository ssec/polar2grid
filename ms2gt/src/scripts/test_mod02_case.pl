#!/usr/bin/perl -w
$|=1;

$path_modis_src = $ENV{PATH_MODIS_SRC};
$source_modis = "$path_modis_src/scripts";
require("$source_modis/mod02_case.pl");

my $hdf1 = "MOD021KM.A2000153.1445.002.2000156075718.hdf";
my $hdfh = "MOD02HKM.A2000153.1445.002.2000156075718.hdf";
my $hdfq = "MOD02QKM.A2000153.1445.002.2000156075718.hdf";
my $hdf3 = "MOD03.A2000153.1445.002.2000156061125.hdf";

t("1", "1", $hdf1);
t("1", "1", $hdfh);
t("1", "1", $hdfq);
t("1", "1", $hdf3);

t("1", "3", $hdf1);
t("1", "3", $hdfh);
t("1", "3", $hdfq);
t("1", "3", $hdf3);

t("1", "H", $hdf1);
t("1", "H", $hdfh);
t("1", "H", $hdfq);
t("1", "H", $hdf3);

t("1", "Q", $hdf1);
t("1", "Q", $hdfh);
t("1", "Q", $hdfq);
t("1", "Q", $hdf3);

t("3", "1", $hdf1);
t("3", "1", $hdfh);
t("3", "1", $hdfq);
t("3", "1", $hdf3);

t("3", "3", $hdf1);
t("3", "3", $hdfh);
t("3", "3", $hdfq);
t("3", "3", $hdf3);

t("3", "H", $hdf1);
t("3", "H", $hdfh);
t("3", "H", $hdfq);
t("3", "H", $hdf3);

t("3", "Q", $hdf1);
t("3", "Q", $hdfh);
t("3", "Q", $hdfq);
t("3", "Q", $hdf3);

sub t {
    my @in = @_;
    my @out;

    print "$in[0] $in[1]  ";
    @out = mod02_case(@in);
    print "$out[0] $out[1] $out[2] $out[3] $out[4]";
    if ($in[0] eq $out[0] &&
	$in[1] eq $out[1]) {
	print "*\n";
    } else {
	print "\n";
    }
}

