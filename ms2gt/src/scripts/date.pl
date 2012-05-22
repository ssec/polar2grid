#!/usr/local/bin/perl -w

#========================================================================
# date.pl - routines to get julian day, calendar day, nextday, etc.
#
# 22-Oct-1996 T.Hutchinson hutch@hummock.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

#tell perl to dump data during the print statement, i.e., flush after each 
#    print

$|=1;

if (defined($true)) {
    return($true);
}
$true = 1;
$false = 0;

#========================================================================
# test date routines - main program to test most subroutines in this file
#
# 10-Dec-1998 T.Haran tharan@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

#
# If script is defined then date.pl has been "required" so just return
#
if (defined($script)) {
    return 1;
}

my $Usage = "\n
USAGE: date.pl routine_name [param0 [param1 [param2 [param3]]]]

       where routine_name and parameters are one of:
         tojulian date
         fromjulian juldate
         cal_plus date diff
         julian_plus juldate diff
         date2_to_date date2
         isLeapyear year
         date_ok date string
         getcurtime\n\n";

if (@ARGV < 1) {
    print $Usage;
    exit;
} else {
    my ($routine, @param) = @ARGV;
    my $out;
    if ($routine eq "tojulian" && @param == 1) {
	$out = &tojulian($param[0]);
    } elsif ($routine eq "fromjulian" && @param == 1) {
	$out = &fromjulian(@param);
    } elsif ($routine eq "cal_plus" && @param == 2) {
	$out = &cal_plus(@param);
    } elsif ($routine eq "julian_plus" && @param == 2) {
	$out = &julian_plus(@param);
    } elsif ($routine eq "date2_to_date" && @param == 1) {
	$out = &date2_to_date(@param);
    } elsif ($routine eq "isLeapyear" && @param == 1) {
	$out = &isLeapyear(@param);
    } elsif ($routine eq "date_ok" && @param == 2) {
	$out = &date_ok(@param);
    } elsif ($routine eq "getcurtime" && @param == 0) {
	$out = &getcurtime();
    } else {
	print "$routine @param is not a valid date routine invocation\n";
	print $Usage;
	exit;
    }
    print "$routine @param = $out\n";
}
exit;

#========================================================================
# tojulian-perl routine convert from calendar date to julian date
#
# 22-Sep-1996 T.Hutchinson hutch@hummock.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
# $Header: /home/haran/navdir/src/scripts/date.pl,v 1.28 2003/08/05 16:55:34 haran Exp $
#
#  A perl subroutine that returns the julian day (# days into year).
#
#    input: date in yyyymmdd format
#
#    return: date in yyyyddd format
#

sub tojulian {

    my($year) = substr($_[0], 0, 4);
    my($month) = substr($_[0], 4, 2);
    my($day) = substr($_[0], 6, 2);
    my($juldate,$month_count);

    my(@daysinmonth) = 
        ("31","28","31","30","31","30","31","31","30","31","30","31");
    my($julday) = 0;

    for ($month_count = 1; $month_count < $month; $month_count++) {
        $julday += $daysinmonth[$month_count-1];
    }
    
    $julday += $day;

    if (($month > 2) && (isLeapyear($year))) { $julday++; }

    $juldate=sprintf("%d%03d", $year, $julday);
    return $juldate;
}


#========================================================================
# fromjulian-perl routine to convert from julian date to calendar date
#
# 22-Sep-1996 T.Hutchinson hutch@hummock.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
# $Header: /home/haran/navdir/src/scripts/date.pl,v 1.28 2003/08/05 16:55:34 haran Exp $
#
#  A perl subroutine that returns the calendar day.
#
#    input: date in yyyyddd format
#
#    return: date in yyyymmdd format
#

sub fromjulian {
    my($julday) = $_[0];
    my($day) = substr($_[0],4,3);
    my($year) = substr($_[0],0,4);
    my($month);
    my($date);

# a trick to remove leading zeros from $day
    $day += 0;

    my(@daysinmonth) = 
        ("31","28","31","30","31","30","31","31","30","31","30","31");

    if ((isLeapyear($year)) && ($day >= 60)) { $daysinmonth[1] = 29; }
    
    for ($month = 0;$day > $daysinmonth[$month]; $month++) {
	$day -= $daysinmonth[$month];
    }

    $month++;
    $date = sprintf("%4d%02d%02d", $year, $month, $day);
    return $date;
}

#========================================================================
# cal_plus-perl routine to add or subtract from the calendar date
#
# 22-Sep-1996 T.Hutchinson hutch@hummock.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
# $Header: /home/haran/navdir/src/scripts/date.pl,v 1.28 2003/08/05 16:55:34 haran Exp $
#
#  Get the next day of the year.
#
#    input: first: date in yyyymmdd format
#           second: number of days to add (subtract if < 0) to date
#
#    return: next day in yyyymmdd format.
#

sub cal_plus {

    my($yyyyddd) = tojulian($_[0]);
    my($diff) = $_[1];
    $yyyyddd = julian_plus($yyyyddd,$_[1]);
    my $outdate = fromjulian($yyyyddd);
    return $outdate;
}

#========================================================================
# julian_plus-perl routine to add or subtract from the julian date
#
# 22-Sep-1996 T.Hutchinson hutch@hummock.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
# $Header: /home/haran/navdir/src/scripts/date.pl,v 1.28 2003/08/05 16:55:34 haran Exp $
#
#  Get the next day of the year.
#
#    input: $juldate: in yyyyddd format
#           $diff: number of days to add (subtract if < 0) to $juldate
#
#    return: next day in yyyyddd format.
#
sub julian_plus
{
    
    my($juldate, $diff) = ($_[0], $_[1]);
    my $day = substr($juldate,4,3);
    my $year = substr($juldate,0,4);
    if ($diff > 0) {
	while ($diff > 0) {
	    my $days_this_year = &isLeapyear($year) ? 366 : 365;
	    if ($diff > 364) {
		$juldate = &julian_plus($juldate, 364);
		$day = substr($juldate,4,3);
		$year = substr($juldate,0,4);
		$diff -= 364;
	    } else {
		$day += $diff;
		$diff = 0;
		if ($day > $days_this_year) {
		    $year++;
		    $day -= $days_this_year;
		}
	    }
	}
    } elsif ($diff < 0) {
	while ($diff < 0) {
	    my $days_previous_year = &isLeapyear($year-1) ? 366 : 365;
	    if ($diff < -364) {
		$juldate = &julian_plus($juldate, -364);
		$day = substr($juldate,4,3);
		$year = substr($juldate,0,4);
		$diff += 364;
	    } else {
		$day += $diff;
		$diff = 0;
		if ($day < 1) {
		    $year--;
		    $day += $days_previous_year;
		}
	    }
	}
    }
    $juldate = sprintf("%d%03d", $year, $day);
    return $juldate;
}

#========================================================================
# date2_to_date - converts yymmdd format to yyyymmdd format
#
# 11-May-1998 T.Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
# $Header: /home/haran/navdir/src/scripts/date.pl,v 1.28 2003/08/05 16:55:34 haran Exp $
#
#  Convert a date in yymmdd format to yyyymmdd format
#
#    input: $date2: in yymmdd format
#
#    return: $date in yyyymmdd format.
#
sub date2_to_date
{
    
    my($date2) = @_;

    my $date = (substr($date2, 0, 2) >= 70) ?
	"19" . "$date2" : "20" . "$date2";
    return $date;
}

#========================================================================
# isLeapyear-perl routine to determine if year is a leap year
#
# 22-Sep-1996 T.Hutchinson hutch@hummock.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#========================================================================
#
# $Header: /home/haran/navdir/src/scripts/date.pl,v 1.28 2003/08/05 16:55:34 haran Exp $
#
#  Check to see if year is a leap year.
#
#    input: year (4 digits)
#
#    return: True ("1") for leap year, False ("0") for non-leap year.
#

sub isLeapyear {
    
    my($year) = $_[0];
    
    if (($year % 4 == 0) && ((($year % 100) != 0) || (($year % 400) == 0))) {
	return 1;
    } else {
	return 0;
    }
}

#==============================================================================
# date_ok - Checks to see if date is in valid yyyymmdd format.
#
# 21-Aug-1997 Terry Haran haran@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
#
#  Checks to see if date is in valid format.
#
#    input:  date in yyyymmdd format
#            string identifying date
#
#    return: $true if date is ok.
#            $false otherwise.
#

sub date_ok {

    my $date   = $_[0];
    my $string = $_[1];

    my $yyyy = substr($date,0,4);
    my $mm = substr($date,4,2);
    my $dd = substr($date,6,2);
    my $success = $false;
    if (($yyyy < 1970) || ($yyyy >= 2070)) {
	print "ERROR: $string year is out of range, year: $yyyy.\n";
    } elsif (($mm < 1) || ($mm > 12)) {
	print "ERROR: $string month is out of range, month: $mm.\n";
    } elsif (($dd < 1) || ($dd > 31)) {
	print "ERROR: $string day is out of range, day: $dd.\n";
    } else {
	my $juldate = &tojulian($date);
	my $date_check = &fromjulian($juldate);
	if ($date ne $date_check) {
	    print "ERROR: $string is an invalid date: $date.\n";
	} else {
	    $success = $true;
	}
    }
    return $success;
}

#==============================================================================
# getcurtime - get current date and time
#
# 11-Sep-1997 Terry Haran haran@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
#
#  Returns current date and time in yyyymmdd.hhmm format 
#
#    input:  none
#
#    return: current date and time as a number in yyyymmdd.hhmm format
#

sub getcurtime {
    my $sec;
    my $min;
    my $hour;
    my $mday;
    my $mon;
    my $year;
    my $wday;
    my $yday;
    my $isdst;
    my $cur_time;
    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time());
    $mon  = sprintf("%02d",$mon + 1);
    $year = sprintf("%4d", $year+ 1900);
    $mday = sprintf("%02d",$mday);
    $hour = sprintf("%02d",$hour);
    $min  = sprintf("%02d",$min);
    $cur_time = $year.$mon.$mday + ($hour.$min) / 10000.0;
    return $cur_time;
}

#==============================================================================
# GetStatusFile - get the status file from the given status directory
#
# 11-Dec-1997 Terry Haran haran@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
#    input:
#            script - name of calling script
#
#            dir - status directory to look for file
#
#            date - date of the next expected file
#
#            hemisphere - "north" or "south"
#
#            stopfile - the full pathname of stopfile to look for while waiting 
#
#    return: none
#

sub GetStatusFile {
    my($script, $StatusDir, $date, $hemisphere, $stopfile) = @_;

    my($counter) = 0;
    while (!(-e "$StatusDir/$date") && !(-e $stopfile)) {
	if (-e $stopfile) { last; }
	if (!(-e "$StatusDir/$date")) {
	    if ($counter == 0) {
		warnmail("$script: WARNING: $date $hemisphere: I'm waiting for\n".
			 "$StatusDir/$date\n".
			 "to be created\n".
			 "or $stopfile\n".
			 "to be created. Perhaps there is a problem?");
	    }
	    sleep 30; 
	    $counter += 1;
	}
    }
    if (-e $stopfile) {
	diemail("$script: MESSAGE: $date $hemisphere:\n".
		"$stopfile exists -- Exitting\n");
    }
}


#==============================================================================
# GetStatusFile2 - get one status file from the either of 2 status directories
#
# 11-Dec-1997 Terry Haran haran@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
#    input:
#            script - name of calling script
#
#            check_north_first - return the north file if both exist;
#                                otherwise return south file if both exist.
#
#            dir_north - status directory north to look for file
#
#            first_north - print message about waiting if north file
#                          doesn't exist and this value is true
#
#            date_north - date of the next expected north file
#
#            dir_south - status directory south to look for file
#
#            date_south - date of the next expected south file
#
#            first_south - print message about waiting if south file
#                          doesn't exist and this value is zero
#
#            stopfile - the full pathname of stopfile to look for while waiting 
#
#    return: "north", or "south"
#

sub GetStatusFile2 {
    my($script, $check_north_first,
       $StatusDirNorth, $date_north, $first_north,
       $StatusDirSouth, $date_south, $first_south,
       $stopfile) = @_;

    my $counter = 0;
    my $north_exists = $false;
    my $south_exists = $false;
    while (!(-e $stopfile)) {
	if ($date_north != 0) {
	    if (-e "$StatusDirNorth/$date_north") {
		$north_exists = $true;
	    } elsif ($first_north && $counter == 0) {
		print_stderr("$script: WARNING: $date_north north: I'm waiting for\n".
			     "$StatusDirNorth/$date_north\n".
			     "to be created\n".
			     "or $stopfile\n".
			     "to be created.\n");
	    }
	}
	if ($date_south != 0) {
	    if (-e "$StatusDirSouth/$date_south") {
		$south_exists = $true;
	    } elsif ($first_south && $counter == 0) {
		print_stderr("$script: WARNING: $date_south south: I'm waiting for\n".
			     "$StatusDirSouth/$date_south\n".
			     "to be created\n".
			     "or $stopfile\n".
			     "to be created.\n");
	    }
	}
	if ($north_exists || $south_exists) {
	    last;
	} else {
	    sleep 30; 
	    $counter++;
	}
    }
    if (-e $stopfile) {
	diemail("$script: MESSAGE: $date_north north $date_south south:\n".
		"$stopfile exists -- Exitting\n");
    }
    my $ret_value = ($north_exists && (!$south_exists || $check_north_first)) ?
	"north" : "south";
    return $ret_value;
}


#==============================================================================
# GetBusyFile - get the given busy file
#
# 17-Dec-1998 Terry Haran haran@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
#    input:
#            script - name of calling script
#
#            date - date of the next expected file
#
#            hemisphere - "north" or "south"
#
#            busyfile - the full pathname of the busyfile to touch
#
#            stopfile - the full pathname of stopfile to look for while waiting 
#
#    return: none
#
# Before using the timberwolf, a routine calls this routine which touches its
# busy file, then waits doing ls -rt1 $busy_test until its own file is the first
# (oldest) in the resulting list of files.
#

sub GetBusyFile {
    my($script, $date, $hemisphere, $busyfile, $stopfile) = @_;

    my($counter) = 0;
    system("touch $busyfile");
    while (!(-e $stopfile)) {
	my @busyfiles = `ls -rt1 $busy_test`;
	if (!@busyfiles) {
	    diemail("script: FATAL: $date $hemisphere\n" .
		    "Unable to find $busyfile");
	}
	chomp $busyfiles[0];
	if ($busyfiles[0] eq $busyfile) {
	    last;
	}
	if ($counter == 0) {
	    print_stderr("$script: WARNING: $date $hemisphere:\n" .
			 "I'm waiting for\n".
			 "$busyfile to become the oldest busy file\n".
			 "or for $stopfile\n".
			 "to be created.\n");
	    }
	sleep 30; 
	$counter += 1;
    }
    if (-e $stopfile) {
	diemail("$script: MESSAGE: $date $hemisphere:\n".
		"$stopfile exists -- Exitting\n");
    }
}


#==============================================================================
# NewTapeLoaded - wait until the user enters y or n after loading tape
#
# 11-Dec-1997 Terry Haran haran@kryos.colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
# Boulder, CO  80309-0449
#==============================================================================
#
#    input: none
#
#    return: true if user entered "y"
#            false if user entered "n"
#

sub NewTapeLoaded {

    my $input;
    my $ret_value = 1;
    print_stderr("\n> Enter y after loading tape, or n to quit\n");
    $input=<STDIN>;
    chop $input;
    while (("y" ne $input) && ("n" ne $input)) {
	print_stderr("> You did not enter y or n, please reenter\n");
	$input=<STDIN>;
	chop $input;
    }
    if ("n" eq $input) {
	$ret_value = 0;
    }
    return $ret_value;
}


# this makes the library work correctly when using the require command
1;
