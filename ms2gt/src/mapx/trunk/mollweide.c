/*------------------------------------------------------------------------
 * mollweide
 *------------------------------------------------------------------------*/
static const char mollweide_c_rcsid[] = "$Id: mollweide.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"

const char *id_mollweide(void)
{
  return mollweide_c_rcsid;
}

int init_mollweide(mapx_class *current)
{
  /* no variables require initialization */
  return 0;
}

int mollweide(mapx_class *current, double lat, double lon,
	      double *x, double *y)
{
  double dlon;
  double phi, lam, theta, delta;
  double sin_theta, cos_theta, psi, epsilon=1e-6;
  int it, maxit=10;
  
  dlon = lon - current->lon0;
  NORMALIZE(dlon);
  
  phi = RADIANS (lat);
  lam = RADIANS (dlon);
  
  delta = 0.0;
  theta = phi;
  sin_theta = sin(theta);
  cos_theta = cos(theta);
  if (fabs(cos_theta) > epsilon)
  { psi = PI*sin(phi);
    it = 0;
    repeat
    { delta = -(theta + sin_theta - psi) / (1 + cos_theta);
      theta += delta;
      sin_theta = sin(theta);
      cos_theta = cos(theta);
      if (++it >= maxit) break;
    } until (fabs(delta) <= epsilon);
    theta /= 2.0;
    sin_theta = sin(theta);
    cos_theta = cos(theta);
  }
  
  *x =  2*SQRT2/PI * current->Rg * lam * cos_theta;
  *y =  SQRT2 * current->Rg * sin_theta;
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_mollweide (mapx_class *current, double x, double y,
		       double *lat, double *lon)
{
  double phi, lam, theta, cos_theta;
  
  x -= current->false_easting;
  y -= current->false_northing;

  theta = asin( y / (SQRT2*current->Rg) );
  phi = asin( (2*theta + sin(2*theta)) / PI);
  cos_theta = cos(theta);
  if (cos_theta != 0.0)
    lam = PI*x / (2*SQRT2*current->Rg*cos_theta);
  else
    lam = 0.0;
  
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
