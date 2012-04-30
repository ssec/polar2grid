/*--------------------------------------------------------------------------
 * Lambert conic conformal ellipsoid
 *--------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

int init_lambert_conic_conformal_ellipsoid(mapx_class *current)
{
  current->Rg = current->equatorial_radius / current->scale;
  current->cos_phi0 = cos(RADIANS(current->lat0));
  current->cos_phi1 = cos(RADIANS(current->lat1));
  current->sin_phi0 = sin(RADIANS(current->lat0));
  current->sin_phi1 = sin(RADIANS(current->lat1));
  current->m0 = ((current->cos_phi0)/sqrt(1 - (current->e2 * current->sin_phi0 
					     * current->sin_phi0))); 
  current->m1 = ((current->cos_phi1)/sqrt(1 - (current->e2 * current->sin_phi1 
					     * current->sin_phi1)));
  current->t0 = sqrt( ((1.0 - current->sin_phi0)/(1.0 + current->sin_phi0)) * 
		     pow(((1.0 + (current->eccentricity * current->sin_phi0))/
			  (1.0 - (current->eccentricity * current->sin_phi0))),
			 current->eccentricity) ); 
  current->t1 = sqrt( ((1.0 - current->sin_phi1)/(1.0 + current->sin_phi1)) * 
		     pow(((1.0 +(current->eccentricity * current->sin_phi1))/
			  (1.0 - (current->eccentricity * current->sin_phi1))),
			 current->eccentricity) ); 
  current->n = (log(current->m0) - log(current->m1)) / (log(current->t0) -log(current->t1));
  current->F = current->m0/(current->n * pow(current->t0,current->n));
  current->rho0 = current->Rg * current->F * pow(current->t0, current->n);
  
  return 0;
}

int lambert_conic_conformal_ellipsoid (mapx_class *current, float lat, float lon, float *u, float *v)
{
  double phi, lam, x, y, chi, rho, theta, sin_phi, t;
  
  lam = lon - current->lon0;
  NORMALIZE (lam);
  lam = RADIANS(lam);
  phi = RADIANS(lat);
  sin_phi = sin(phi);
  
  t = sqrt( ((1 - sin_phi)/(1 + sin_phi)) * 
	   pow(((1 + (current->eccentricity * sin_phi))/
		(1 - (current->eccentricity * sin_phi))),
	       current->eccentricity) );
  rho = current->Rg * current->F * pow(t, current->n);
  theta = current->n * lam;
  
  x = rho * sin(theta);
  y = current->rho0 - (rho * cos(theta));
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_lambert_conic_conformal_ellipsoid (mapx_class *current, float u, float v, float *lat, float *lon)
{
  double rho, x, y, t, chi, lam, phi, theta; 
  
  x =  current->T00*(u+current->u0) - current->T01*(v+current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v+current->v0);
  
  rho = (fabs(current->n) / current->n) * 
    sqrt((x*x) + ((current->rho0 - y) * (current->rho0 - y)));
  t = pow((rho/(current->Rg * current->F)), (1/current->n));
  chi = PI/2.0 - 2.0 * atan(t);
  
  if (current->n < 0.0)
    theta = atan( -x / (y - current->rho0));
  else
    theta = atan(x / (current->rho0 - y));
  
  lam = (theta / current->n);
  phi = chi + (((current->e2 / 2.0) + ((5.0 / 24.0) * current->e4) +
		(current->e6 / 12.0) + ((13.0 / 360.0) * current->e8)) * 
	       sin(2.0 * chi)) +
		 ((((7.0 / 48.0) * current->e4) + ((29.0 / 240.0) * current->e6) +
		   ((811.0 / 11520.0) * current->e8)) * sin(6.0 * chi)) +
		     ((((7.0 / 120.0) * current->e6) + 
		       ((81.0 / 1120.0) * current->e8)) * sin(6.0 * chi)) +
			 (((4279.0 / 161280.0) * current->e8) * sin(8.0 * chi));
  
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE (*lon);
  
  return 0;
}
