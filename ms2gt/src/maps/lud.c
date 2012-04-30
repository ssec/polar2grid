/*======================================================================
 * lud - lower, upper, diagonal matrix factoring
 *
 *	to solve x*b = y, where x is m x n
 *	first calculate xT*x*b = xT*y, xT*x is n x n, pos.def.symmetric
 *	then, factor xT*x into triangular form
 *	and solve for b by back substitution
 *
 * 2-Aug-1990 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "define.h"
#include "lud.h"

static const char lud_c_rcsid[] = "$Header: /usr/local/src/maps/lud.c,v 1.3 1994/04/07 16:29:50 knowles Exp $";

/*----------------------------------------------------------------------
 * design - calculate xT*x and xT*y
 *
 *	input : x - design matrix (m x n)
 *		y - data
 *		m - number of data points
 *		n - number of variables
 *
 *	output: A - xT*x (n x n)
 *		z - xT*y
 *
 *	result: 0 = success, -1 = error
 *
 *----------------------------------------------------------------------*/
int design(double **x, double *y, double **A, double *z, int m, int n)
{
  int i, j, k;
  double sum;

/*
 *	A = xT*x, z = xT*y
 */
  for (i = 0; i < n; i++)
  { for (j = 0; j < n; j++)
    { sum = 0.0;
      for (k = 0; k < m; k++)
	sum += x[k][i]*x[k][j];
      A[i][j] = sum;
    }
    sum = 0.0;
    for (k = 0; k < m; k++)
      sum += x[k][i]*y[k];
    z[i] = sum;
  }
  return 0;
}

/*----------------------------------------------------------------------
 * factor - factor positive definite symmetric matrix into triangular form
 *
 *	input : A - pos. def. sym. matrix (n x n)
 *		n - dimension of A
 *
 *	output: A - factored matrix
 *
 *	result: 0 = success, -1 = error
 *
 *----------------------------------------------------------------------*/
int factor(double **A, int n)
{
  double nf;
  int i, j, k;

/*
 *	triangularization
 */
  nf = sqrt(A[0][0]);
  for (i = 0; i < n; i++)
    A[0][i] /= nf;
  for (i = 1; i < n; i++)
  { for (j = i; j < n; j++)
      for (k = 0; k < i; k++)
	A[i][j] -= A[k][i]*A[k][j];
    nf = sqrt(A[i][i]);
    for (j = i; j < n; j++)
      A[i][j] /= nf;
  }
  return 0;
}

/*----------------------------------------------------------------------
 * solve - substitute z into A to solve A*b = z
 *
 *	input : A - triangular matrix
 *		z - data vector
 *		n - dimension of A (and z)
 *
 *	output: z - solution vector
 *
 *	result: 0 = success, -1 = error
 *
 *----------------------------------------------------------------------*/
int solve(double **A, double *z, int n)
{
  int i, k;
  double sum;

/*
 *	forward elimination
 */
  z[0] /= A[0][0];
  for (i = 1; i < n; i++)
  { sum = 0.0;
    for (k = 0; k < i; k++)
      sum += A[k][i]*z[k];
    z[i] = (z[i] - sum) / A[i][i];
  }

/*
 *	back substitution
 */
  z[n-1] /= A[n-1][n-1];
  for (i = n-1; i >= 1; i--)
  { for (k = i; k < n; k++)
      z[i-1] -= A[i-1][k]*z[k];
    z[i-1] /= A[i-1][i-1];
  }

  return 0;
}
