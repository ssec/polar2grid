/*--------------------------------------------------------------------------
 * Lambert conic conformal ellipsoid
 *--------------------------------------------------------------------------*/
static const char lambert_conic_conformal_c_rcsid[] = "$Id: lambert_conic_conformal.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"

const char *id_lambert_conic_conformal(void)
{
  return lambert_conic_conformal_c_rcsid;
}

int init_lambert_conic_conformal_ellipsoid(mapx_class *current)
{
  current->Rg = current->equatorial_radius / current->scale;
  current->sin_phi0 = sin(RADIANS(current->center_lat));
  current->sin_phi1 = sin(RADIANS(current->lat0));
  current->sin_phi2 = sin(RADIANS(current->lat1));
  current->cos_phi1 = cos(RADIANS(current->lat0));
  current->cos_phi2 = cos(RADIANS(current->lat1));
  
  current->m1 = current->cos_phi1 / 
      sqrt(1 - (current->e2 * current->sin_phi1 * current->sin_phi1));
  
  current->m2 = current->cos_phi2 / 
      sqrt(1 - (current->e2 * current->sin_phi2 * current->sin_phi2));
  
  current->t0 = sqrt( ((1.0 - current->sin_phi0)/(1.0 + current->sin_phi0)) * 
		     pow(((1.0 + (current->eccentricity * current->sin_phi0))/
			  (1.0 - (current->eccentricity * current->sin_phi0))),
			 current->eccentricity) );
 
  current->t1 = sqrt( ((1.0 - current->sin_phi1)/(1.0 + current->sin_phi1)) * 
		     pow(((1.0 +(current->eccentricity * current->sin_phi1))/
			  (1.0 - (current->eccentricity * current->sin_phi1))),
			 current->eccentricity) );
 
  current->t2 = sqrt( ((1.0 - current->sin_phi2)/(1.0 + current->sin_phi2)) * 
		     pow(((1.0 +(current->eccentricity * current->sin_phi2))/
			  (1.0 - (current->eccentricity * current->sin_phi2))),
			 current->eccentricity) );
 
  current->n = ((log(current->m1) - log(current->m2)) /
		(log(current->t1) - log(current->t2)));

  current->F = current->m1 / (current->n * pow(current->t1, current->n));

  current->rho0 = current->Rg * current->F * pow(current->t0, current->n);
  
  return 0;
}

int lambert_conic_conformal_ellipsoid (mapx_class *current,
				       double lat, double lon,
				       double *x, double *y)
{
  double phi, lam, rho, theta, sin_phi, t;
  
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
  
  *x = rho * sin(theta);
  *y = current->rho0 - (rho * cos(theta));
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_lambert_conic_conformal_ellipsoid (mapx_class *current,
					       double x, double y,
					       double *lat, double *lon)
{
  double rho, t, lam, phi, theta;
  double rho0_m_y;
  double esin_phi;
  double e_over_2;
  double phi_old;
  double delta_phi;
  double epsilon = 1e-7;
  int it_max = 35;
  int i;
  
  x -= current->false_easting;
  y -= current->false_northing;

  rho0_m_y = current->rho0 - y;
  rho = sign(current->n) * sqrt(x * x + rho0_m_y * rho0_m_y);
  theta = current->n >= 0 ?
    atan2( x,  rho0_m_y) :
    atan2(-x, -rho0_m_y);
  lam = (theta / current->n);

  t = pow((rho/(current->Rg * current->F)), (1/current->n));
  e_over_2 = current->eccentricity / 2.0;
  phi = PI / 2.0 - 2 * atan(t);
  phi_old = phi;

  /*
   * Calculate phi using equation 7-9, Snyder 1987, p109
   */

  for (i = 0; i < it_max; i++) {
    esin_phi = current->eccentricity * sin(phi);
    phi = PI / 2.0 - 2.0 * atan(t * pow((1 - esin_phi) / (1 + esin_phi),
					e_over_2));
    delta_phi = fabs(fabs(phi) - fabs(phi_old));
    if (delta_phi < epsilon)
      break;
    phi_old = phi;
  }
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE (*lon);
  
  return 0;
}
