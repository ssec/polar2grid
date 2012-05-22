/*------------------------------------------------------------------------
 * albers_conic_equal_area
 *------------------------------------------------------------------------*/
static const char albers_conic_equal_area_c_rcsid[] = "$Id: albers_conic_equal_area.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "proj.h"
#include "define.h"
#include "mapx.h"

const char *id_albers_conic_equal_area(void)
{
  return albers_conic_equal_area_c_rcsid;
}

int init_albers_conic_equal_area(mapx_class *current)
{
  current->sin_phi0 = sin(RADIANS(current->center_lat));
  current->sin_phi1 = sin(RADIANS(current->lat0));
  current->cos_phi1 = cos(RADIANS (current->lat0));

  if (999 == current->lat1 || current->lat0 == current->lat1)
    current->n = current->sin_phi1;
  else
    current->n = (current->sin_phi1 + sin(RADIANS(current->lat1)))/2;

  current->C = (current->cos_phi1*current->cos_phi1
		+ 2*current->n*current->sin_phi1);

  current->rho0 = 
    current->Rg*sqrt(current->C - 2*current->n*current->sin_phi0)/current->n;

  return 0;
}

int albers_conic_equal_area(mapx_class *current, double lat, double lon, 
			    double *x, double *y)
{
  double phi, lam, sin_phi, rho, theta;
  
  phi = RADIANS(lat);
  lam = RADIANS(lon - current->lon0);

  sin_phi = sin(phi);
  rho = current->Rg*sqrt(current->C - 2*current->n*sin_phi)/current->n;
  theta = current->n*lam;

  *x = rho*sin(theta);
  *y = current->rho0 - rho*cos(theta);

  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_albers_conic_equal_area(mapx_class *current, double x, double y, 
				    double *lat, double *lon)
{
  double phi, lam, rho, rmy, theta, chi;

  x -= current->false_easting;
  y -= current->false_northing;

  rmy = current->rho0 - y;
  rho = sqrt(x*x + rmy*rmy);
  theta = current->n >= 0 ?
    atan2( x,  rmy) :
    atan2(-x, -rmy);

  chi = rho*current->n/current->Rg;
  phi = asin((current->C - chi*chi)/(2*current->n));
  lam = theta/current->n;

  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}

/*------------------------------------------------------------------------
 * albers_conic_equal_area_ellipsoid
 *------------------------------------------------------------------------*/

int init_albers_conic_equal_area_ellipsoid(mapx_class *current)
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
  
  
  if (0 == current->eccentricity)
  {
      current->q0 = 2 * current->sin_phi0;
      current->q1 = 2 * current->sin_phi1;
      current->q2 = 2 * current->sin_phi2;
  }
  else
  {
      current->q0 = (1-current->e2) *
                      ( ( current->sin_phi0 / 
                      (1 - (current->e2 * current->sin_phi0 * current->sin_phi0)) ) - 
                      ( log( (1 - (current->eccentricity*current->sin_phi0)) / 
                      (1 + (current->eccentricity*current->sin_phi0)) ) / 
                      (2*current->eccentricity) ) );
      
      current->q1 = (1-current->e2) * 
                      ( ( current->sin_phi1 / 
                      (1 - (current->e2 * current->sin_phi1 * current->sin_phi1)) ) - 
                      ( log( (1 - (current->eccentricity*current->sin_phi1)) / 
                      (1 + (current->eccentricity*current->sin_phi1)) ) / 
                      (2*current->eccentricity) ) );
                        
      current->q2 = (1-current->e2) * 
                      ( ( current->sin_phi2 / 
                      (1 - (current->e2 * current->sin_phi2 * current->sin_phi2)) ) - 
                      ( log( (1 - (current->eccentricity*current->sin_phi2)) / 
                      (1 + (current->eccentricity*current->sin_phi2)) ) / 
                      (2*current->eccentricity) ) );
  }
  
  if (999 == current->lat1 || current->lat0 == current->lat1)
      current->n = current->sin_phi1;
  else
      current->n = ( (current->m1*current->m1) - (current->m2*current->m2) ) / 
                     (current->q2 - current->q1);
      
  current->C = (current->m1*current->m1) + (current->n*current->q1);
  
  current->rho0 = (current->Rg / current->n) * sqrt(current->C - (current->n*current->q0));

  return 0;
}


int albers_conic_equal_area_ellipsoid(mapx_class *current,
				      double lat, double lon, 
				      double *x, double *y)
{

  double phi, lam, sin_phi, rho, theta, q;
  
  phi = RADIANS(lat);
  lam = RADIANS(lon - current->lon0);
   
  sin_phi = sin(phi);  


  if (0 == current->eccentricity)
      q = 2 * sin_phi;
  else
      q = (1-current->e2) * ( ( sin_phi / (1 - (current->e2 * sin_phi * sin_phi)) ) - 
             ( log( (1 - (current->eccentricity*sin_phi)) / 
             (1 + (current->eccentricity*sin_phi)) ) / 
             (2*current->eccentricity) ) );

  rho = (current->Rg / current->n) * sqrt(current->C - (current->n*q));
  
  theta = current->n * lam;
  
  *x = rho * sin(theta);
  *y = current->rho0 - (rho * cos(theta));
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}


int inverse_albers_conic_equal_area_ellipsoid(mapx_class *current,
					      double x, double y, 
					      double *lat, double *lon)
{
  double phi, lam, rho, rmy, theta, q;
  double q_test;
  double cos_phi;
  double sin_phi;
  double esin_phi;
  double one_m_e2sin2_phi;
  double delta_phi;
  double one_m_e2;
  double one_over_2e;
  double epsilon = 1e-6;
  int it_max = 35;
  int i;
  
  x -= current->false_easting;
  y -= current->false_northing;

  rmy = current->rho0 - y;
  rho = sqrt( x*x + rmy*rmy );
  
  theta = current->n >= 0 ?
    atan2( x,  rmy) :
    atan2(-x, -rmy);
  lam = theta / current->n;
  
  
  q = (current->C - ( (rho*rho*current->n*current->n) /
		      (current->Rg*current->Rg) ) ) / current->n;
          
/***  Calculate phi using equation 3-16, Snyder 1987, p102 ***/
 
  q_test = 1.0 - (1.0 - current->e2)/(2.0 * current->eccentricity) *
    log((1.0 - current->eccentricity) / (1.0 + current->eccentricity));
  if (fabs(fabs(q) - fabs(q_test)) < epsilon) {
    phi = sign(q) * PI / 2;
  } else {

    phi = asinz(q / 2.0);
    one_m_e2 = 1.0 - current->e2;
    one_over_2e = 1.0 / (2.0 * current->eccentricity);
    
    for (i = 0; i < it_max; i++) {
      cos_phi = cos(phi);
      if (cos_phi < epsilon) {
	phi = sign(q) * PI / 2;
	break;
      }
      sin_phi = sin(phi);
      esin_phi = current->eccentricity * sin_phi;
      one_m_e2sin2_phi = 1.0 - esin_phi * esin_phi;
      delta_phi = one_m_e2sin2_phi * one_m_e2sin2_phi / (2.0 * cos_phi) *
	(q / one_m_e2 - sin_phi / one_m_e2sin2_phi + one_over_2e *
	 log((1.0 - esin_phi) / (1.0 + esin_phi)));
      phi += delta_phi;
      if (fabs(delta_phi) < epsilon)
	break;
    }
  }

  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
  
}
