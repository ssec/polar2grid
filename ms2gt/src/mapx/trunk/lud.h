/*======================================================================
 * lud - lower, upper, diagonal matrix factoring
 *
 * 2-Aug-1990 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1990 University of Colorado
 *======================================================================*/
#ifndef lud_h_
#define lud_h_

#ifdef lud_c_
const char lud_h_rcsid[] = "$Id: lud.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

int design(double **x, double *y, double **A, double *z, int m, int n);

int factor(double **A, int n);

int solve(double **A, double *z, int n);

#endif
