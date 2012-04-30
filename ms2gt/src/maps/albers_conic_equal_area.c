/*------------------------------------------------------------------------
 * albers_conic_equal_area
 *------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

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

int albers_conic_equal_area(mapx_class *current, float lat, float lon, 
			    float *u, float *v)
{
  float x, y;
  double phi, lam, sin_phi, rho, theta;
  
  phi = RADIANS(lat);
  lam = RADIANS(lon - current->lon0);

  sin_phi = sin(phi);
  rho = current->Rg*sqrt(current->C - 2*current->n*sin_phi)/current->n;
  theta = current->n*lam;

  x = rho*sin(theta);
  y = current->rho0 - rho*cos(theta);

  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_albers_conic_equal_area(mapx_class *current, float u, float v, 
				    float *lat, float *lon)
{
  double phi, lam, rho, rmy, theta, chi, x, y;

  x =  current->T00*(u+current->u0) - current->T01*(v + current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v + current->v0);

  rmy = current->rho0 - y;
  rho = sqrt(x*x + rmy*rmy);
  theta = atan2(x, rmy);

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


int albers_conic_equal_area_ellipsoid(mapx_class *current, float lat, float lon, 
			    float *u, float *v)
{

  float x, y;
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
  
  x = rho * sin(theta);
  y = current->rho0 - (rho * cos(theta));
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;

  return 0;
}


int inverse_albers_conic_equal_area_ellipsoid(mapx_class *current, float u, float v, 
				    float *lat, float *lon)
{
  double phi, lam, rho, rmy, theta, x, y, q, beta, sin_2beta,
         sin_4beta, sin_6beta;       
  
  x =  current->T00*(u+current->u0) - current->T01*(v + current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v + current->v0);

  rmy = current->rho0 - y;
  rho = sqrt( x*x + rmy*rmy );
  
  theta = atan2(x,rmy);
  
  q = (current->C - ( (rho*rho*current->n*current->n) / (current->Rg*current->Rg) ) ) /
          current->n;
          
          
/***  Calculate phi using equation 3-18, Snyder 1987, p102 ***/
 
   beta = asin( q / (1 - ( ((1-current->e2)/(2*current->eccentricity)) *
                  log( (1-current->eccentricity)/(1+current->eccentricity) ) )) );
                   
   sin_2beta = sin(2*beta);
   sin_4beta = sin(4*beta);
   sin_6beta = sin(6*beta);
    
   phi = beta + ( ((current->e2/3 + ((517/5040) * current->e6))*sin_2beta) +
             ((((23/360)*current->e4) + ((251/3780)*current->e6))*sin_4beta) +
             (((761/3780)*current->e6)*sin_6beta) );
 
  
   lam = theta / current->n;
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
  
}
