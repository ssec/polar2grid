/*======================================================================
 * svd - singular value decomposition
 *
 * reference: Computer Methods for Mathematical Computations,
 *		Forsythe, Malcolm, and Moler, 1977.
 *
 * 2-Aug-1990 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
static const char svd_c_rcsid[] = "$Id: svd.c 16072 2010-01-30 19:39:09Z brodzik $";

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "define.h"
#include "matrix.h"
#define svd_c_
#include "svd.h"

/*
 *	set default value for maximum number of iterations
 */
#ifndef MAX_ITS
#define MAX_ITS 30
#endif

/*
 *	"safe" geometric mean
 */
static double gmean_c_;
#define GEOMETRIC_MEAN(a,b) (fabs(a) > fabs(b) \
		     ? (gmean_c_ = (b)/(a), \
			fabs(a)*sqrt(1 + gmean_c_*gmean_c_)) \
		     : (0 != (b) \
			? (gmean_c_ = (a)/(b), \
			   fabs(b)*sqrt(1 + gmean_c_*gmean_c_)) \
			: (double)0.0))

/*
 *	macros to replace some FORTRAN intrinsics
 */
#define AMAX1(a,b) ((a) > (b) ? (a) : (b))

#define SIGN(a,b) ((b) >= 0.0 ? fabs(a) : -fabs(a))

const char *id_svd(void)
{
  return svd_c_rcsid;
}

/*----------------------------------------------------------------------
 * svdecomp - singular value decomposition
 *
 *	input : u - matrix to factor (m x n)
 *		m - row dimension
 *		n - column dimension
 *
 *	output: u - first factor of input a (m x n)
 *		w - diagonal of second factor (singular values)
 *		v - third factor (n x n)
 *
 *	result: 0 = success
 *		-1 = error 
 *		+n = nth singular value failed to converge
 *
 *----------------------------------------------------------------------*/
int svdecomp(double **u, int m, int n, double *w, double **v)
{
  int flag, i, its, j, jj, k, l, l1, k1;
  double c, f, h, s, x, y, z;
  double anorm = 0.0, g = 0.0, scale = 0.0;
  double *rv1 = NULL;
  
  if (m < n) 
  { fprintf(stderr,"svdecomp: matrix is row deficient\n");
    return -1;
  }
  
  rv1 = (double *)calloc(n, sizeof(double));
  if (NULL == rv1) 
  { perror("svdecomp"); return -1; }
  
  for (i = 0; i < n; i++)
  { l = i + 1;
    rv1[i] = scale*g;

/*
 *	Householder reduction to bidiagonal form
 */
    g = s = scale = 0.0;
    if (i < m)
    { for (k = i; k < m; k++)
      { scale += fabs(u[k][i]);
      }
      if (0 != scale)
      { for (k = i; k < m; k++)
	{ u[k][i] /= scale;
	  s += u[k][i]*u[k][i];
	}
	f = u[i][i];
	g = -SIGN(sqrt(s), f);
	h = f*g - s;
	u[i][i] = f - g;
	if (i != n-1)
	{ for (j = l; j < n; j++)
	  { s = 0.0;
	    for (k = i; k < m; k++)
	    { s += u[k][i]*u[k][j];
	    }
	    f = s/h;
	    for (k = i; k < m; k++)
	    { u[k][j] += f*u[k][i];
	    }
	  }
	}
	for (k = i; k < m; k++)
	{ u[k][i] *= scale;
	}
      }
    }

    w[i] = scale * g;
    g = s = scale = 0.0;
    if (i < m && i != n-1)
    { for (k = l; k < n; k++)
      { scale += fabs(u[i][k]);
      }
      if (0 != scale)
      { for (k = l; k < n; k++) 
	{ u[i][k] /= scale;
	  s += u[i][k]*u[i][k];
	}
	f = u[i][l];
	g = -SIGN(sqrt(s),f);
	h = f*g - s;
	u[i][l] = f - g;
	for (k = l; k < n; k++)
	{ rv1[k] = u[i][k]/h;
	}
	if (i != m-1)
	{ for (j = l; j < m; j++)
	  { s = 0.0;
	    for (k = l; k < n; k++)
	    { s += u[j][k]*u[i][k];
	    }
	    for (k = l; k < n; k++)
	    { u[j][k] += s*rv1[k];
	    }
	  }
	}
	for (k = l; k < n; k++)
	{ u[i][k] *= scale;
	}
      }
    }

    anorm = AMAX1(anorm,(fabs(w[i]) + fabs(rv1[i])));
  }

/*
 *	accumulation of right-hand transformations
 */
  for (i = n-1; i >= 0; i--)
  { if (i < n-1)
    { if (0 != g) 
      { for (j = l; j < n; j++)
	{ v[j][i] = u[i][j] / u[i][l] / g;
	}
	for (j = l; j < n; j++) 
	{ s = 0.0;
	  for (k = l; k < n; k++)
	  { s += u[i][k]*v[k][j];
	  }
	  for (k = l; k < n; k++)
	  { v[k][j] += s*v[k][i];
	  }
	}
      }
      for (j = l; j < n; j++)
      { v[i][j] = v[j][i] = 0.0;
      }
    }
    v[i][i] = 1.0;
    g = rv1[i];
    l = i;
  }

/*
 *	accumulation of left-hand transformations
 */
  for (i = n-1; i >= 0; i--)
  { l = i + 1;
    g = w[i];
    if (i < n-1)
    { for (j = l; j < n; j++)
      { u[i][j] = 0.0;
      }
    }
    if (0 != g)
    { g = 1/g;
      if (i != n-1)
      { for (j = l; j < n; j++)
	{ s = 0.0;
	  for (k = l; k < m; k++)
	  { s += u[k][i]*u[k][j];
	  }
	  f = (s/u[i][i])*g;
	  for (k=i; k < m; k++)
	  { u[k][j] += f*u[k][i];
	  }
	}
      }
      for (j = i; j < m; j++)
      { u[j][i] *= g;
      }
    } 
    else
    { for (j = i; j < m; j++)
      { u[j][i] = 0.0;
      }
    }
    ++u[i][i];
  }

/*
 *	diagonalization of the bidiagonal form
 */
  for (k = n-1; k > 0; k--)
  { for (its = 1; its <= MAX_ITS; its++)
    { 
/*
 *	test for splitting
 */
      flag = 1;
      for (l = k; l >= 0; l--)
      { l1 = l - 1;
	if (fabs(rv1[l])+anorm == anorm)
	{ flag = 0;
	  break;
	}
	if (fabs(w[l1])+anorm == anorm) break;
      }
/*
 *	cancellation of rv1[l] for l greater than 0
 */
      if (flag)
      { c = 0;
	s = 1;
	for (i = l; i <= k; i++)
	{ f = s*rv1[i];
	  if (fabs(f)+anorm != anorm)
	  { g = w[i];
	    h = GEOMETRIC_MEAN(f, g);
	    w[i] = h;
	    c = g/h;
	    s = -f/h;
	    for (j = 0;j < m; j++)
	    { y = u[j][l1];
	      z = u[j][i];
	      u[j][l1] = y*c + z*s;
	      u[j][i] = z*c - y*s;
	    }
	  }
	}
      }

/*
 *	test for convergence
 */
      z = w[k];
      if (l == k) 
      { if (z < 0.0)
	{ w[k] = -z;
	  for (j = 0; j < n; j++)
	  { v[j][k] = -v[j][k];
	  }
	}
	break;
      }

      if (its == MAX_ITS) 
      { fprintf(stderr,"svdecomp: failed to converge in %d iterations\n",
		MAX_ITS);
	free(rv1);
	return k;
      }

/*
 *	shift from bottom 2 by 2 minor
 */
      x = w[l];
      k1 = k-1;
      y = w[k1];
      g = rv1[k1];
      h = rv1[k];
      f = ((y - z)*(y + z) + (g - h)*(g + h)) / (2.0*h*y);
      g = GEOMETRIC_MEAN(f, 1.0);
      f = ((x - z)*(x + z) + h*((y / (f + SIGN(g, f))) - h)) / x;
      c = s = 1;
      for (j = l; j <= k1; j++)
      {	i = j + 1;
	g = rv1[i];
	y = w[i];
	h = s*g;
	g = c*g;
	z = GEOMETRIC_MEAN(f, h);
	rv1[j] = z;
	c = f/z;
	s = h/z;
	f = x*c + g*s;
	g = g*c - x*s;
	h = y*s;
	y = y*c;
	for (jj = 0; jj < n; jj++)
	{ x = v[jj][j];
	  z = v[jj][i];
	  v[jj][j] = x*c + z*s;
	  v[jj][i] = z*c - x*s;
	}
	z = GEOMETRIC_MEAN(f, h);
	w[j] = z;
	if (0 != z)
	{ c = f/z;
	  s = h/z;
	}
	f = c*g + s*y;
	x = c*y - s*g;
	for (jj = 0; jj < m; jj++)
	{ y = u[jj][j];
	  z = u[jj][i];
	  u[jj][j] = y*c + z*s;
	  u[jj][i] = z*c - y*s;
	}
      }
      rv1[l] = 0.0;
      rv1[k] = f;
      w[k] = x;
    }
  }
  free(rv1);
  return 0;
}

/*----------------------------------------------------------------------
 * svdsolve - solve A*x = b using back substitution after svdecomp
 *
 *	input : u,w,v - factors of A from svdecomp
 *		m - row dimension
 *		n - column dimension
 *		b - data vector
 *
 *	output: x - solution vector
 *
 *	result: 0 = success
 *		-1 = error
 *
 *----------------------------------------------------------------------*/
int svdsolve(double **u, double *w, double **v, int m, int n,
	       double *b, double *x)
{
  int jj, j, i;
  double s, *tmp = NULL;
  
  tmp = (double *)calloc(n, sizeof(double));
  if (NULL == tmp) { perror("svdsolve"); return -1; }

  for (j = 0;j < n; j++)
  { s = 0.0;
    if (w[j])
    { for (i=0; i < m; i++)
      { s += u[i][j]*b[i];
      }
      s /= w[j];
    }
    tmp[j] = s;
  }
  for (j = 0; j < n; j++)
  { s = 0.0;
    for (jj = 0; jj < n; jj++)
    { s += v[j][jj]*tmp[jj];
    }
    x[j] = s;
  }
  free(tmp);
  return 0;
}
