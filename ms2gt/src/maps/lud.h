/*======================================================================
 * lud - lower, upper, diagonal matrix factoring
 *
 * 2-Aug-1990 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#ifndef lud_h_
#define lud_h_

static const char lud_h_rcsid[] = "$Header: /usr/local/src/maps/lud.h,v 1.2 1994/04/07 16:29:52 knowles Exp $";

int design(double **x, double *y, double **A, double *z, int m, int n);

int factor(double **A, int n);

int solve(double **A, double *z, int n);

#endif
