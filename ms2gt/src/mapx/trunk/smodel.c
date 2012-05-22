/*========================================================================
 * smodel - cubic spline model
 *
 *	reference: Forsythe, Malcolm, and Moler, Computer Methods for
 *		     Mathematical Computations, Prentice-Hall, 1977.
 *
 * 31-July-1992 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1992 University of Colorado
 *========================================================================*/
static const char smodel_c_rcsid[] = "$Id: smodel.c 16072 2010-01-30 19:39:09Z brodzik $";

#include <stdio.h>
#include <float.h>
#include "define.h"
#define smodel_c_
#include "smodel.h"

static smodel *new_smodel(int n);
static double linearize(double lon1, double lon2, int topo);
static double normalize(double lon, int topo);

const char *id_smodel(void)
{
  return smodel_c_rcsid;
}

/*------------------------------------------------------------------------
 * init_smodel - initialize spline model
 *
 *	input : n - number of points (>=2)
 *		x - abscissas of the knots in increasing order
 *		y - ordinates of the knots
 *		topo - topology flag, see smodel.h
 *
 *	result: pointer to new cubic spline model
 *
 *------------------------------------------------------------------------*/
smodel *init_smodel(int n, double *x, double *y, int topo)
{ smodel *this;
  register int i;
  double *b, *c, *d;
  register double t;
  double lon1, lon2;

  if (n < 2)
  { fprintf(stderr,"smodel: need at least 2 points, n=%d\n",n);
    return NULL;
  }

/*
 *	S' denotes 1st derivative of S
 *
 *	y[i] = S(x[i])
 *	b[i] = S'(x[i])
 *	c[i] = S''(x[i]) / 2
 *	d[i] = S'''(x[i]) / 6 (derivative from the right)
 */

  this = new_smodel(n);
  if (this == NULL) return NULL;
  b = this->B;
  c = this->C;
  d = this->D;

/*
 *	copy function values
 */
  this->I = 0;
  this->N = n;
  this->topo = topo;

  for (i=0; i < n; i++)
  { this->X[i] = x[i];
  }

  if (topo == FLAT_smodel)
  { for (i=0; i < n; i++)
    { this->Y[i] = y[i];
    }
  }
  else
  { this->Y[0] = lon2 = y[0];
    for (i=1; i < n; i++)
    { lon1 = lon2;
      lon2 = linearize(lon1, y[i], topo);
      this->Y[i] = lon2;
    }
  }

  x = this->X;
  y = this->Y;

/*
 *	check for linear case
 */
  if (n == 2)
  { b[0] = b[1] = (y[1] - y[0]) / (x[1] - x[0]);
    c[0] = c[1] = 0;
    d[0] = d[1] = 0;
  }
  else
/*
 *	set up tridiagonal system
 *	B = diagonal, D = off diagonal, C = right hand side
 */
  { d[0] = x[1] - x[0];
    c[1] = (y[1] - y[0]) / d[0];
    for (i=1; i < n-1; i++)
    { d[i] = x[i+1] - x[i];
      b[i] = 2*(d[i-1] + d[i]);
      c[i+1] = (y[i+1] - y[i]) / d[i];
      c[i] = c[i+1] - c[i];
    }

/*
 *	obtain third derivatives at ends by divided differences
 */
    b[0] = -d[0];
    b[n-1] = -d[n-2];
    if (n == 3)
    { c[0] = 0;
      c[n-1] = 0;
    }
    else
    { c[0] = c[2]/(x[3] - x[1]) - c[1]/(x[2] - x[0]);
      c[n-1] = c[n-2]/(x[n-1] - x[n-3]) - c[n-3]/(x[n-2] - x[n-4]);
      c[0] = c[0]*d[0]*d[0] / (x[3] - x[0]);
      c[n-1] = -c[n-1]*d[n-2]*d[n-2] / (x[n-1] - x[n-4]);
    }

/*
 *	forward elimination
 */
    for (i=1; i < n; i++)
    { t = d[i-1]/b[i-1];
      b[i] -= t*d[i-1];
      c[i] -= t*c[i-1];
    }

/*
 *	back sustitution
 */
    c[n-1] /= b[n-1];
    for (i=n-2; i >= 0; i--)
    { c[i] = (c[i] - d[i]*c[i+1]) / b[i];
    }

/*
 *	compute polynomial coefficients
 */
    b[n-1] = (y[n-1] - y[n-2])/d[n-2] + d[n-2]*(c[n-2] + 2*c[n-1]);
    for (i=0; i < n-1; i++)
    { b[i] = (y[i+1] - y[i])/d[i] - d[i]*(c[i+1] + 2*c[i]);
      d[i] = (c[i+1] - c[i])/d[i];
      c[i] *= 3;
    }
    c[n-1] *= 3;
    d[n-1] = d[n-2];

  }

  return this;
}

/*------------------------------------------------------------------------
 * eval_smodel - evaluate cubic spline
 *
 *	input : this - pointer to smodel
 *		x - abscissa at which the spline is to be evaluated
 *
 *	result: ordinate value at x
 *
 *	note :	it is the responsibility of the calling procedure
 *		to ensure that the requested value is within the
 *		bounds of the model end points. Extrapolating beyond
 *		the end points is not recomended.
 *
 *------------------------------------------------------------------------*/
double eval_smodel(smodel *this, double x)
{ register int i,j,k;
  register double dx, y;

/*
 *	find proper interval
 *	start with interval of previous evaluation
 *	then try next interval after that 
 *	then use binary search
 */
  i = this->I;
  if (x >= this->X[i] && x < this->X[i+1])
  { this->I = i;
  }
  else if (x >= this->X[i+1] && x < this->X[i+2])
  { this->I = ++i;
  }
  else 
  { i = 0;
    j = this->N;
    do
    { k = (i+j)/2;
      if (x < this->X[k]) j = k;
      if (x >= this->X[k]) i = k;
    } while (j > i+1);
    this->I = i;
  }

/*
 *	evaluate spline using Horner's rule
 */
  dx = x - this->X[i];
  y = this->Y[i] + dx*(this->B[i] + dx*(this->C[i] + dx*this->D[i]));

  return normalize(y, this->topo);
}

/*------------------------------------------------------------------------
 * write_smodel - save smodel to file
 *
 *	input : this - pointer to smodel
 *		fp - file pointer opened for write access
 *			and correctly positioned
 *
 *	result: success status, 0 = failed, 1 = success
 *
 *------------------------------------------------------------------------*/
int write_smodel(smodel *this, FILE *fp)
{ register int ios, n;

  ios = fwrite(&(this->N), sizeof(int), 1, fp);
  if (ios != 1) { perror("smodel"); return 0; }

  ios = fwrite(&(this->I), sizeof(int), 1, fp);
  if (ios != 1) { perror("smodel"); return 0; }

  ios = fwrite(&(this->topo), sizeof(int), 1, fp);
  if (ios != 1) { perror("smodel"); return 0; }

  n = this->N;

  ios = fwrite(this->X, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fwrite(this->Y, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fwrite(this->B, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fwrite(this->C, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fwrite(this->D, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }

  return 1;
}

/*------------------------------------------------------------------------
 * read_smodel - retrieve smodel from file
 *
 *	input : this - pointer to smodel or NULL for new instance
 *		fp - file pointer opened for read access
 *			and correctly positioned
 *
 *	output: this - pointer to smodel
 *
 *	result: success status, 0 = failed, 1 = success
 *
 *------------------------------------------------------------------------*/
int read_smodel(smodel *this, FILE *fp)
{ register int ios;
  int n;

  ios = fread(&n, sizeof(int), 1, fp);
  if (ios != 1) { perror("smodel"); return 0; }

  if (this == NULL) 
  { this = new_smodel(n);
    if (this == NULL) 
      return 0;
  }

  this->N = n;

  ios = fread(&(this->I), sizeof(int), 1, fp);
  if (ios != 1) { perror("smodel"); return 0; }

  ios = fread(&(this->topo), sizeof(int), 1, fp);
  if (ios != 1) { perror("smodel"); return 0; }

  ios = fread(this->X, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fread(this->Y, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fread(this->B, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fread(this->C, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }
  
  ios = fread(this->D, sizeof(double), n, fp);
  if (ios != n) { perror("smodel"); return 0; }

  return 1;
}

/*------------------------------------------------------------------------
 * free_smodel
 *
 *	input : this - pointer to smodel
 *
 *------------------------------------------------------------------------*/
void free_smodel(smodel *this)
{
  if (this == NULL) return;
  if (this->X != 0) free(this->X);
  if (this->Y != 0) free(this->Y);
  if (this->B != 0) free(this->B);
  if (this->C != 0) free(this->C);
  if (this->D != 0) free(this->D);
}

/*------------------------------------------------------------------------
 * new_smodel - smodel constructor
 *
 *	input : n - number of points
 *
 *	result: pointer to smodel structure
 *
 *------------------------------------------------------------------------*/
static smodel *new_smodel(int n)
{ smodel *this;

/*
 *	allocate storage space
 */
  this = (smodel *) calloc((size_t) 1, sizeof(smodel));
  if (this == NULL) {perror("smodel"); return NULL;}

  this->X = (double *) malloc(sizeof(double)*(n+1));
  if (this->X == NULL) {perror("smodel"); free_smodel(this); return NULL;}

  this->Y = (double *) malloc(sizeof(double)*n);
  if (this->Y == NULL) {perror("smodel"); free_smodel(this); return NULL;}

  this->B = (double *) malloc(sizeof(double)*n);
  if (this->B == NULL) {perror("smodel"); free_smodel(this); return NULL;}

  this->C = (double *) malloc(sizeof(double)*n);
  if (this->C == NULL) {perror("smodel"); free_smodel(this); return NULL;}

  this->D = (double *) malloc(sizeof(double)*n);
  if (this->D == NULL) {perror("smodel"); free_smodel(this); return NULL;}

/*
 *	add an extra X value to make search logic simpler and more efficient
 */
  this->X[n] = DBL_MAX;

  return this;
}

/*------------------------------------------------------------------------
 * linearize - convert circular topology to linear
 *
 *	input : lon1 - previous point
 *		lon2 - current point
 *		topo - topology flag
 *
 *	result: current point <= 1/2 circle away from previous point
 *
 *------------------------------------------------------------------------*/
static double linearize(double lon1, double lon2, int topo)
{
  register double full_circle, half_circle;

  switch (topo)
  { case LON_smodel:
    case ELON_smodel:
      half_circle = 180;
      break;
    case LAM_smodel:
    case ELAM_smodel:
      half_circle = PI;
      break;
    default:
      return lon2;
  }

  full_circle = 2*half_circle;

  while (lon2 - lon1 >  half_circle) lon2 -= full_circle;
  while (lon2 - lon1 < -half_circle) lon2 += full_circle;

  return lon2;
}

/*------------------------------------------------------------------------
 * normalize - return value to proper range
 *
 *	input : lon - current value
 *		topo - topology flag
 *
 *	result: current value within proper range
 *
 *------------------------------------------------------------------------*/
static double normalize(double lon, int topo)
{
  register double upper_limit, lower_limit, full_circle;

  switch (topo)
  { case LON_smodel:
      upper_limit = 180;
      lower_limit = -180;
      break;
    case ELON_smodel:
      upper_limit = 360;
      lower_limit = 0;
      break;
    case LAM_smodel:
      upper_limit = PI;
      lower_limit = -PI;
      break;
    case ELAM_smodel:
      upper_limit = 2*PI;
      lower_limit = 0;
      break;
    default:
      return lon;
  }

  full_circle = upper_limit - lower_limit;

  while (lon > upper_limit) lon -= full_circle;
  while (lon < lower_limit) lon += full_circle;

  return lon;
}

/*------------------------------------------------------------------------
 * main - test driver
 *
 *	compile with -DTEST_DRIVER
 *
 *	output should be: "cube(2.500000) = 15.625000"
 *
 *------------------------------------------------------------------------*/
#ifdef TEST_DRIVER
main()
{ double u, x[10], y[10];
  int i, n=10;
  smodel *cube;

  for (i=0; i < n; i++)
  { x[i] = i;
    y[i] = i*i*i;
  }

  cube = init_smodel(n, x, y, FLAT_smodel);
  u = 2.5;
  printf("cube(%f) = %f\n", u, eval_smodel(cube, u));

  exit(0);
}
#endif
