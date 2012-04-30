/*======================================================================
 * svd - singular value decomposition
 *
 * 2-Aug-1990 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#ifndef svd_h_
#define svd_h_

static const char svd_h_rcsid[] = "$Header: /usr/local/src/maps/svd.h,v 1.2 1994/04/07 16:29:02 knowles Exp $";

int svdecomp(double **u, int m, int n, double *w, double **v);
int svdsolve(double **u, double *w, double **v, int m, int n, 
	     double *b, double *x);

#endif
