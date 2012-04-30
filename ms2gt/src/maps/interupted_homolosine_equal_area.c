/*--------------------------------------------------------------------------
 * interupted homolosine equal-area
 * reference: http://edcwww.cr.usgs.gov/landdaac/1KM/goodesarticle.html
 *--------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

/*
 * region boundaries
 *
 *	       40W
 *	      lam1
 *	+-------+---------------+
 *	|   0   |       2       |
 * phi1	+-------+---------------+ 40N44'11.8"
 *	|   1   |       3       |
 * phi2	+-----------------------+
 *	| 4 |  5  |   8  |   9  |
 * phi3	+---+-----+------+------+ 40S44'11.8"
 *	| 6 |  7  |  10  |  11  |
 *	+---+-----+------+------+
 *	  lam2  lam3   lam4
 *	  100W   20W    80E
 */

/*
 * 40N44'11.8" = latitude of seam between Mollweide and Sinusoidal
 * where the linear scales are equal
 */
#define IH_phi1  0.710987989993
#define IH_phi2  0.0           
#define IH_phi3 (-IH_phi1)
#define IH_lam1 -0.698131700798
#define IH_lam2 -1.74532925199 
#define IH_lam3 -0.349065850399
#define IH_lam4  1.3962634016  

/* 
 * central meridians for regions
 */
static const double IH_lam0[] = 
{-1.74532925199,	/*  0 = -100.0 degrees */
 -1.74532925199,	/*  1 = -100.0 degrees */
  0.523598775598,	/*  2 = 30.0 degrees */
  0.523598775598,	/*  3 = 30.0 degrees */
 -2.79252680319,	/*  4 = -160.0 degrees */
 -1.0471975512,		/*  5 = -60.0 degrees */
 -2.79252680319,       	/*  6 = -160.0 degrees */
 -1.0471975512,		/*  7 = -60.0 degrees */
  0.349065850399,	/*  8 = 20.0 degrees */
  2.44346095279,       	/*  9 = 140.0 degrees */
  0.349065850399,	/* 10 = 20.0 degrees */
  2.44346095279  	/* 11 = 140.0 degrees */
};

/*
 * Mollweide offset
 */
#define IH_mc3 0.0528035274542

int init_interupted_homolosine_equal_area(mapx_class *current)
{
  /* no variables require initialization */
  return 0;
}

int interupted_homolosine_equal_area(mapx_class *current, float lat, float lon, float *u, float *v)
{
  int it, max_it=30, region;
  double x, y, phi, lam, cos_phi, sin_phi, delta_lam;
  double x0, theta, delta_theta, constant, epsilon=1e-10;
  
  lam = RADIANS(lon);
  phi = RADIANS(lat);
  cos_phi = cos(phi);
  sin_phi = sin(phi);
  
  if (phi >= IH_phi1)
  { if (lam <= IH_lam1) region = 0;
    else region = 2;
  }
  else if (phi >= IH_phi2)
  { if (lam <= IH_lam1) region = 1;
    else region = 3;
  }
  else if (phi >= IH_phi3)
  { if (lam <= IH_lam2) region = 4;
    else if (lam <= IH_lam3) region = 5;
    else if (lam <= IH_lam4) region = 8;
    else region = 9;
  }
  else
  { if (lam <= IH_lam2) region = 6;
    else if (lam <= IH_lam3) region = 7;
    else if (lam <= IH_lam4) region = 10;
    else region = 11;
  }

  delta_lam = lam - IH_lam0[region];
  RNORMALIZE(delta_lam);
  x0 = current->Rg * IH_lam0[region];
 
  if (region==1||region==3||region==4||region==5||region==8||region==9)
  {
    x = x0 + current->Rg * delta_lam * cos_phi;
    y = current->Rg * phi;
  }
  else
  {
    theta = phi;
    constant = PI*sin_phi;

/* 
 *	iterate using the Newton-Raphson method to find theta
 */
    for (it=0; it < max_it; it++)
    {
      delta_theta = -(theta + sin(theta) - constant) / (1.0 + cos(theta));
      theta += delta_theta;
      if (fabs(delta_theta) < epsilon) break;
    }

    if (it >= max_it) 
    {
#ifdef DEBUG
      fprintf(stderr,"mapx: iteration failed to converge\n");
#endif
      return -1;
    }
    theta /= 2.0;
    x = x0 + 2*SQRT2/PI * current->Rg * delta_lam * cos(theta);
    y = current->Rg * (SQRT2*sin(theta) - IH_mc3*sign(phi));
  }

  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;

  return 0;
}

int inverse_interupted_homolosine_equal_area(mapx_class *current, float u, float v, float *lat, float *lon)
{
  int region;
  double x, y, xor, yor, x0;
  double lam, phi, theta, alpha, epsilon=1e-8; 
  
  x =  current->T00*(u+current->u0) - current->T01*(v+current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v+current->v0);

  xor = x/current->Rg;
  yor = y/current->Rg;

/*
 *	get region
 */
  if (yor >= IH_phi1)
  { if (xor <= IH_lam1) region = 0;
    else region = 2;
  }
  else if (yor >= IH_phi2)
  { if (xor <= IH_lam1) region = 1;
    else region = 3;
  }
  else if (yor >= IH_phi3)
  { if (xor <= IH_lam2) region = 4;
    else if (xor <= IH_lam3) region = 5;
    else if (xor <= IH_lam4) region = 8;
    else region = 9;
  }
  else
  { if (xor <= IH_lam2) region = 6;
    else if (xor <= IH_lam3) region = 7;
    else if (xor <= IH_lam4) region = 10;
    else region = 11;
  }

  x0 = current->Rg * IH_lam0[region];
  x -= x0;

  if (region==1||region==3||region==4||region==5||region==8||region==9)
  {
    phi = y / current->Rg;
    if (fabs(phi) > PI/2) return -1;

    if (fabs(fabs(phi) - PI/2) > epsilon)
    {
      lam = IH_lam0[region] + x / (current->Rg * cos(phi));
      RNORMALIZE(lam);
    }
    else lam = IH_lam0[region];
  }
  else
  {
    alpha = (y + IH_mc3*current->Rg * sign(y)) / (SQRT2*current->Rg);
    if (fabs(alpha) > 1.0) return -1;
    theta = asin(alpha);
    lam = IH_lam0[region] + x/(2*SQRT2/PI*current->Rg*cos(theta));
    if (lam < -PI) return -1;
    alpha = (2*theta + sin(2*theta)) / PI;
    if (fabs(alpha) > 1.0) return -1;
    phi = asin(alpha);
  }

/*
 * check for interupted area
 */
  switch (region)
  { case 0: case 1: if (lam < -PI || lam > IH_lam1) return -1; break;
    case 2: case 3: if (lam < IH_lam1 || lam > PI) return -1; break;
    case 4: case 6: if (lam < -PI || lam > IH_lam2) return -1; break;
    case 5: case 7: if (lam < IH_lam2 || lam > IH_lam3) return -1; break;
    case 8: case 10: if (lam < IH_lam3 || lam > IH_lam4) return -1; break;
    case 9: case 11: if (lam < IH_lam4 || lam > PI) return -1; break;
  }

  *lat = DEGREES(phi);
  *lon = DEGREES(lam);
  NORMALIZE(*lon);
  
  return 0;
}
