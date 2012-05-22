/*========================================================================
 * smodel - cubic spline model
 *
 * 13-Jan-1993 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1993 University of Colorado
 *========================================================================*/
#ifndef smodel_h_
#define smodel_h_

#ifdef smodel_c_
const char smodel_h_rcsid[] = "$Id: smodel.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

typedef struct {
  double *X, *Y, *B, *C, *D;
  int N, I, topo;
} smodel;

/*
 * topology flags
 */
#define FLAT_smodel 0	/* flat model i.e. y-axis is linear */
#define LON_smodel 1	/* longitude -180 <= y <= 180 */
#define ELON_smodel 2	/* longitude 0 <= y <= 360 */
#define LAM_smodel 3	/* longitude -PI <= y <= PI */
#define ELAM_smodel 4	/* longitude 0 <= y <= 2*PI */

/*
 * function prototypes
 */
smodel *init_smodel(int n, double *x, double *y, int topo);
void free_smodel(smodel *this);
double eval_smodel(smodel *this, double x);
int write_smodel(smodel *this, FILE *fp);
int read_smodel(smodel *this, FILE *fp);

#endif
