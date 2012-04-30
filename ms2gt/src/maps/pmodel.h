/*======================================================================
 * pmodel - polynomial model
 *
 * 2-Aug-1990 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#ifndef pmodel_h_
#define pmodel_h_

static const char pmodel_h_rcsid[] = "$Header: /usr/local/src/maps/pmodel.h,v 1.4 1994/04/07 16:27:07 knowles Exp $";

#define ipow(x,i) \
((i) == 0 ? 1.0 : (i) == 1 ? (x) : (x) == 0.0 ? 0.0 : pow((x), (double) (i)))

typedef struct 
{ int dim;	/* dimension	*/
  int order;	/* size		*/
  int tcode;	/* shape	*/
  double *coef;	/* coefficients */
} Polynomial;

Polynomial *init_pmodel(int dim, int order, int tcode, int npts,
                        double *rdata, double *sdata, double *tdata);

void free_pmodel(Polynomial *P);

double eval_pmodel(Polynomial *P, double r, double s);

void test_pmodel(Polynomial *P, int npts, 
		 double *rdata, double *sdata, double *tdata,
		 double *SSE, double *R2);

double chebyshev(int i, int n, double a, double b);

#endif
