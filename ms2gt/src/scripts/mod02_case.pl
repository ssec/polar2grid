# $Id: mod02_case.pl,v 1.6 2004/10/29 21:46:54 haran Exp $

#========================================================================
# mod02_case.pl - determines case for mod02.pl
#
# 25-Oct-2000 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

sub mod02_case {
    my ($ancil_src, $latlon_src, $filestem) = @_;
    my $case;
    my $platform;

    my $prefix = substr($filestem, 0, 5);
    my $p = substr($prefix, 1, 1);
    if ($p eq "O") {
	$platform = "terra";
    } elsif ($p eq "Y") {
	$platform = "aqua";
    } else {
	diemail("$script: FATAL: Second character of $filestem is not O or Y");
    }
    if ($prefix eq "MOD03" || $prefix eq "MYD03") {
	$filestem = substr($filestem, 0, 19);
	$case = 9;
	$latlon_src = 3;
	$ancil_src = 3;
    } else {
	$prefix = substr($filestem, 0, 8);
	$filestem = substr($filestem, 0, 22);
	if ($ancil_src eq "1" && $latlon_src eq "3") {
	    $ancil_src = "3";
	}
	if ($ancil_src eq "3") {
	    $latlon_src = "3";
	    if ($prefix eq "MOD021KM" || $prefix eq "MYD021KM") {
		$case = 6;
	    } elsif ($prefix eq "MOD02HKM" || $prefix eq "MYD02HKM") {
		$case = 7;
	    } else {
		$case = 8;
	    }
	} else {
	    if ($latlon_src eq "1") {
		if ($prefix eq "MOD021KM" || $prefix eq "MYD021KM") {
		    $case = 1;
		} elsif ($prefix eq "MOD02HKM" || $prefix eq "MYD02HKM") {
		    $case = 3;
		    $latlon_src = "H";
		} else {
		    $case = 5;
		    $latlon_src = "Q";
		}
	    } elsif ($latlon_src eq "H") {
		if ($prefix eq "MOD021KM" || $prefix eq "MYD021KM") {
		    $case = 2;
		} elsif ($prefix eq "MOD02HKM" || $prefix eq "MYD02HKM") {
		    $case = 3;
		} else {
		    $case = 5;
		    $latlon_src = "Q";
		}
	    } else {
		if ($prefix eq "MOD021KM" || $prefix eq "MYD021KM") {
		    $case = 4;
		} elsif ($prefix eq "MOD02HKM" || $prefix eq "MYD02HKM") {
		    $case = 3;
		    $latlon_src = "H";
		} elsif ($prefix eq "MOD02QKM" || $prefix eq "MYD02QKM") {
		    $case = 5;
		} else {
		    diemail("$script: FATAL: Unrecognized prefix in $filestem");
		}
	    }
	}
    }
    return($ancil_src, $latlon_src, $filestem, $prefix, $case, $platform);
}

# this makes the routine work properly using require in other programs
1;
