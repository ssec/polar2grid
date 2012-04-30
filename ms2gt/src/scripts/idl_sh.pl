#!/usr/bin/perl -w
# idl_sh.pl
# this script file allows a user to run an idl program from the command line
#
# usage: idl_sh.pl idlprogname idlprogparams
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
#	      idl_sh, myprog, "'inputfile.dat'"
#
if (@ARGV < 1) {
   printf STDERR "usage: idl_sh.pl idlprogramname parm1 parm2 ...\n";
   exit;
}

my $tocompile = $ARGV[0];
my $time = time();
my $temp = "$ENV{HOME}/tmp/run_idl_$time.scr";
if (-e $temp) {
    do {
	sleep(1);
	$time = time();
	$temp = "$ENV{HOME}/tmp/run_idl_$time.scr";
    } until(!(-e $temp));
}
open(TEMP, ">$temp");
print TEMP ".compile $tocompile\n";
if (0 < @ARGV - 1) {
    print TEMP "$tocompile, \$\n";
} else {
    print TEMP "$tocompile\n";
}
my $i;
for ($i = 1; $i <= @ARGV - 1; $i++) {
    if ($i < @ARGV - 1) {
	print TEMP "$ARGV[$i], \$\n";
    } else {
	print TEMP "$ARGV[$i]\n";
    }
}
print TEMP "exit\n";
close(TEMP);

system("$ENV{IDL_DIR}/bin/idl $temp");
system("rm $temp");
