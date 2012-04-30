# $Id: setup.pl,v 1.5 2001/04/26 20:37:55 haran Exp $

#========================================================================
# setup.pl - sets up some global variables for mod02.pl, mod10_l2.pl and
#            mod29.pl 
#
# 25-Oct-2000 T. Haran tharan@colorado.edu 303-492-1847
# National Snow & Ice Data Center, University of Colorado, Boulder
#========================================================================

# The email address of the user running the processing.
#     email will be sent to this user.
# If you want email messages sent to you, then uncomment the next line,
# or set $user_mail_address to a specific address
# (but don't forget the \ in front of the @).

# $user_mail_address="$ENV{USER}\@$ENV{HOST}";

#The default value for the fornav -d weight_distance_max parameter is 1.0.
#The larger value defined here has been found to do a better job of
#supressing holes in the resulting grids with a minimum of blurring.

$weight_distance_max = 1.2;

# this makes the routine work properly using require in other programs
1;
