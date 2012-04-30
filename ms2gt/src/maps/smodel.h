/*========================================================================
 * smodel - cubic spline model
 *
 * 13-Jan-1993 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
#ifndef smodel_h_
#define smodel_h_

static const char smodel_h_rcsid[] = "$Header: /usr/local/src/maps/smodel.h,v 1.2 1994/04/07 16:29:00 knowles Exp $";

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
