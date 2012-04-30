/*------------------------------------------------------------------------
 * mollweide
 *------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

int init_mollweide(mapx_class *current)
{
  /* no variables require initialization */
  return 0;
}

int mollweide(mapx_class *current, float lat, float lon, float *u, float *v)
{
  float x, y, dlon;
  double phi, lam, theta, delta;
  double sin_theta, cos_theta, psi, epsilon=.0025;
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
  
  x =  2*SQRT2/PI * current->Rg * lam * cos_theta;
  y =  SQRT2 * current->Rg * sin_theta;
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_mollweide (mapx_class *current, float u, float v, float *lat, float *lon)
{
  double phi, lam, theta, cos_theta, x, y;
  
  x =  current->T00*(u+current->u0) - current->T01*(v+current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v+current->v0);
  
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
