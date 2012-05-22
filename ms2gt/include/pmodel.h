/*======================================================================
 * pmodel - polynomial model
 *
 * 2-Aug-1990 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1990 University of Colorado
 *======================================================================*/
#ifndef pmodel_h_
#define pmodel_h_

#ifdef pmodel_c_
const char pmodel_h_rcsid[] = "$Id: pmodel.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

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
