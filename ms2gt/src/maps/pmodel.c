/*======================================================================
 * pmodel - polynomial model
 *
 *	1 dimensional model : t = [b](r)
 *
 *	solve P([rdata])*[b] = [tdata] for [b] by least squares
 *
 *	2 dimensional model : t = [b](r,s) 
 *
 *	solve P([rdata],[sdata])*[b] = [tdata] for [b] by least squares
 *	  
 * 2-Aug-1990 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include "define.h"
#include "matrix.h"
#include "svd.h"
#include "pmodel.h"

static const char pmodel_c_rcsid[] = "$Header: /usr/local/src/maps/pmodel.c,v 1.5 1994/04/07 16:27:05 knowles Exp $";

/*----------------------------------------------------------------------
 * eval_pmodel - evaluate polynomial
 *
 *	input : P - polynomial model
 *		r,s - point to evaluate at
 *
 *	result: polynomial evaluated at r,s
 *
 *	dim = 1:
 *
 *	t = b0 + b1*r + b2*r^2 + ... + bk*r^k,  k = order
 *
 *	dim = 2:
 *
 *	tcode = 1 means triangular coefficient matrix
 *	tcode = 0 means full coefficient matrix
 *
 *	For example order=2, tcode=1          tcode=0
 *		             1    s   s^2      1    s     s^2
 *	                     r    rs           r    rs    rs^2
 *	                     r^2               r^2  r^2s  r^2s^2
 *
 *	Coefficients are numbered sequentially in either case,
 *	starting at upper left increasing down each column.
 *
 *	For the above examples
 *	                    b0   b3   b5       b0   b3   b6
 *                          b1   b4            b1   b4   b7
 *	                    b2                 b2   b5   b8
 *
 *----------------------------------------------------------------------*/
double eval_pmodel(Polynomial *P, double r, double s)
{ int i, j, k, m, n;
  double sum_i, sum_j;
  
/*
 *	the polynomials are factored for significantly
 *	faster evaluation and to avoid over/underflow
 */
  if (P->dim == 1)
  { sum_i = P->coef[P->order];
    for (i = P->order - 1; i >= 0; i--)
      sum_i = r*sum_i + P->coef[i];
    return (sum_i);
  }
  else if (P->dim == 2)
  { n = P->order + 1;
    if (P->tcode)
    { m = 1;
      k = n*(n+1)/2 -1;
    }
    else
    { m = n;
      k = m*n -1;
    }
    sum_j = 0.0;
    for (j = 0; j < n; j++)
    { sum_i = 0.0;
      for (i = 0; i < m; i++)
      { sum_i = r*sum_i + P->coef[k];
	--k;
      }
      sum_j = s*sum_j + sum_i;
      if (P->tcode)  m++;
    }
    return sum_j;
  }
}

/*----------------------------------------------------------------------
 * design_matrix - get design matrix for polynomial model
 *
 *	input : P - polynomial model (dim, order, tcode)
 *		npts - number of data points
 *		rdata,sdata - coords. of the data points
 *			(sdata = NULL for dim == 1)
 *		
 *	result: design matrix (can be freed with free(3C))
 *
 *	number of data points must be greater than number of variables
 *	for example, with a 2 dimensional model,
 *		if order=2 and tcode=1
 *		then (b0, b1, ... b5) = 6 variables
 *		so, you must have at least 7 data points
 *
 *----------------------------------------------------------------------*/
static double **design_matrix(Polynomial *P, int npts, 
			      double *rdata, double *sdata)
{ int i, ipt, j, k, m, n, nvars;
  double **M = NULL;
  
  if (P->dim == 1)
  { nvars = P->order + 1;
  }
  else if (P->dim == 2)
  { nvars = P->tcode == 0 
      ? (P->order + 1) * (P->order + 1)
        : (P->order + 1) * (P->order + 2) / 2;
  }
  
  if (npts <= nvars)
  { fprintf(stderr,"pmodel: not enough data to support model\n"
	    "        need at least %d points\n", nvars+1);
    return NULL;
  }
  
  M = (double **)matrix(npts, nvars, sizeof(double), TRUE);
  if (NULL == M) { perror("pmodel"); return NULL; }
  
  if (P->dim == 1)
  { for (ipt = 0; ipt < npts; ipt++)
    { for (k = 0; k <= P->order; k++)
      { M[ipt][k] = ipow(rdata[ipt], k);
      }
    }
  }
  else if (P->dim == 2)
  { m = P->order + 1;
    for (ipt = 0; ipt < npts; ipt++)
    { n = m;
      k = 0;
      for (j = 0; j < m; j++)
      { for (i=0; i < n; i++)
	{ M[ipt][k] = ipow(rdata[ipt],i) * ipow(sdata[ipt],j);
	  k++;
	}
	n -= P->tcode;
      }
    }
  }

  return M;
}

/*----------------------------------------------------------------------
 * init_pmodel - solve for polynomial coefficients
 *
 *	input : dim - dimension (1 or 2)
 *		order - highest power term (e.g. 2 = quadratic, 3 = cubic)
 *		tcode - 0 = full rank, 1 = triangular (see eval_pmodel)
 *		npts - number of data points
 *		rdata,sdata - coords. of the data points
 *			(sdata = NULL for dim == 1)
 *		tdata - values at data points
 *
 *	result: polynomial model or NULL on error
 *
 *	notes : uses Singular Value Decomposition technique
 *		to solve for polynomial coefficients in a 
 *		least squares sense
 *
 *----------------------------------------------------------------------*/
Polynomial *init_pmodel(int dim, int order, int tcode, int npts,
			double *rdata, double *sdata, double *tdata)
{ int i, j, nvars;
  double *sval = NULL, **v = NULL, **M = NULL;
  double max_sval, thresh;
  Polynomial *P = NULL;
  
  if (dim != 1 && dim != 2)
  { fprintf(stderr,"pmodel: dimension must be 1 or 2, not %d\n", dim);
    return NULL;
  }
  if (tcode != 0 && tcode != 1)
  { fprintf(stderr,"pmodel: tcode must be 0 or 1, not %d\n", tcode);
    return NULL;
  }
  
  P = (Polynomial *)calloc(1, sizeof(Polynomial));
  if (NULL == P) { perror("pmodel"); return NULL; }
  P->dim = dim;
  P->order = order;
  P->tcode = tcode;
  P->coef = NULL;

  if (P->dim == 1)
  { nvars = P->order + 1;
  }
  else if (P->dim == 2)
  { nvars = P->tcode == 0 
      ? (P->order + 1) * (P->order + 1)
	: (P->order + 1) * (P->order + 2) / 2;
  }
  
  P->coef = (double *)calloc(nvars, sizeof(double));
  if (NULL == P->coef) { perror("pmodel"); free_pmodel(P); return NULL; }

  M = design_matrix(P, npts, rdata, sdata);
  if (NULL == M) { free_pmodel(P); return NULL; }
  
  v = (double **)matrix(nvars, nvars, sizeof(double), TRUE);
  if (NULL == v) { free_pmodel(P); free(M); return NULL; }
  
  sval = (double *)calloc(nvars, sizeof(double));
  if (NULL == sval) { free_pmodel(P); free(M); free(v); return NULL; }
  
  if (svdecomp(M, npts, nvars, sval, v) != 0)
  { free_pmodel(P); free(M); free(v); free(sval); return NULL; }
  
  max_sval = 0.0;
  for (j = 0; j < nvars; j++)
  { if (sval[j] > max_sval) max_sval = sval[j];
  }
  thresh = nvars * DBL_EPSILON * max_sval;
  for (j = 0; j < nvars; j++)
  { if (sval[j] < thresh) sval[j] = 0.0;
  }
  
  if (svdsolve(M, sval, v, npts, nvars, tdata, P->coef) != 0)
  { free_pmodel(P); free(M); free(v); free(sval); return NULL; }
  
  free(v);
  free(sval);
  free(M);
  
  return P;
}

/*----------------------------------------------------------------------
 * free_pmodel - free polynomial model
 *
 *	input : P - polynomial model
 *
 *----------------------------------------------------------------------*/
void free_pmodel(Polynomial *P)
{ 
  if (NULL == P) return;
  if (NULL != P->coef) free(P->coef);
  free(P);
  return;
}

/*----------------------------------------------------------------------
 * test_pmodel - test fit of polynomial model
 *
 *	input : P - polynomial model
 *		npts - number of data points
 *		rdata,sdata,tdata - data point coords. and values
 *
 *	output: SSE - Sum Squared Error, the value to be minimized in
 *		      the least squares method, the smaller the better
 *		R2 - a measure of how well the model accounts for the
 *		     variance in the data values, should be near 1.
 *
 *----------------------------------------------------------------------*/
void test_pmodel(Polynomial *P, int npts, 
		 double *rdata, double *sdata, double *tdata,
		 double *SSE, double *R2)
{ int ipt;
  double e, t, sum_t, sum_t2, TSS;
  double r, s;
  
  *SSE = 0.0;
  sum_t = sum_t2 = 0.0;
  for (ipt=0; ipt < npts; ipt++)
  { r = rdata[ipt];
    s = P->dim == 2 ? sdata[ipt] : 0.0;
    t = eval_pmodel(P, r, s);
    sum_t += t;
    sum_t2 += t*t;
    e = t - tdata[ipt];
    *SSE += e*e;
  }
  TSS = sum_t2 - sum_t*sum_t / npts;
  *R2 = 1 - *SSE/TSS;
}

/*------------------------------------------------------------------------
 * chebyshev - determine the ith Chebyshev point on an interval
 *------------------------------------------------------------------------*/
double chebyshev(int i, int n, double a, double b)
{
  return .5*(a+b + (a-b)*cos(PI*(2.*i+1)/(2.*n+2)));
}
