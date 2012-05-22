#!/usr/bin/perl -w
# idl_sh.pl
# this script file allows a user to run an idl program from the command line
#
# usage: idlde_sh.pl idlprogname idlprogparams
#
# installation: 
#	1. copy this script to a directory in your path; be sure that is has
#          executable permission after copying.
#	2. create a directory under your home directory called tmp.
#       3. run like this
#	     idl_sh.pl program input1 input2 ...
#	Note: To include single quotes with an input parameter, surround
#	    the input in single quotes, then surround the single quotes with
#	    double quotes, i.e, 
#	      idlde_sh, myprog, "'inputfile.dat'"
#
if (@ARGV < 1) {
   printf STDERR "usage: idlde_sh.pl idlprogramname parm1 parm2 ...\n";
   exit;
}

my $tocompile = $ARGV[0];

# define a temporary filename based on the time.

my $time = time();
my $temp = "$ENV{HOME}/tmp/run_idl_$time.scr";

# if one with that name already exists, then wait a second and try again

if (-e $temp) {
    do {
	sleep(1);
	$time = time();
	$temp = "$ENV{HOME}/tmp/run_idl_$time.scr";
    } until(!(-e $temp));
}

# define a temporary directory for the same time that will serve as a semaphore

my $tempdir = "$ENV{HOME}/tmp/run_idl_$time.dir";

# initialize the temp file with the current startup file (if any)

if (defined($ENV{IDL_STARTUP}) && -e "$ENV{IDL_STARTUP}") {
    system("cp $ENV{IDL_STARTUP} $temp");
}

# (re)define the idl startup file to be the temporary file

$ENV{IDL_STARTUP} = $temp;

open(TEMP, ">>$temp");

# have idlde create the semaphore to indicate it's running

print TEMP "\$mkdir $tempdir\n";

# add the idl command to be run

print TEMP ".compile $tocompile\n";
if (0 < @ARGV - 1) {
    print TEMP "$tocompile, \$\n";
} else {
    print TEMP "$tocompile\n";
}

# add the parameters to the idl command to be run

my $i;
for ($i = 1; $i <= @ARGV - 1; $i++) {
    if ($i < @ARGV - 1) {
	print TEMP "$ARGV[$i], \$\n";
    } else {
	print TEMP "$ARGV[$i]\n";
    }
}

# remove the semaphore

print TEMP "\$rmdir $tempdir\n";

# exit idlde

print TEMP "exit, /no_confirm\n";
close(TEMP);

# invoke idlde -- the idl startup file will run our command

system("$ENV{IDL_DIR}/bin/idlde");

# wait until idlde starts

while (!(-e "$tempdir")) {
    sleep(1);
}

# wait until idlde finishes

while (-e "$tempdir") {
    sleep(1);
}

# delete the temporary file

system("rm $temp");
