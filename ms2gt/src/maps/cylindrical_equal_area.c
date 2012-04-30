/*------------------------------------------------------------------------
 * cylindrical_equal_area
 *------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

int init_cylindrical_equal_area(mapx_class *current)
{ 
  if (current->lat1 == 999) current->lat1 = 30.00;
  current->cos_phi1 = cos (RADIANS (current->lat1));

  return 0;
}

int cylindrical_equal_area(mapx_class *current, float lat, float lon, float *u, float *v)
{
  float x, y, dlon;
  double phi, lam;
  
  dlon = lon - current->lon0;
  NORMALIZE(dlon);
  
  phi = RADIANS (lat);
  lam = RADIANS (dlon);
  
  x =  current->Rg * lam * current->cos_phi1;
  y =  current->Rg * sin (phi) / current->cos_phi1;
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_cylindrical_equal_area (mapx_class *current, float u, float v, 
					   float *lat, float *lon)
{
  double phi, lam, x, y;
  
  x =  current->T00*(u+current->u0) - current->T01*(v+current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v+current->v0);
  
  phi = asin(y*current->cos_phi1/current->Rg);
  lam = x/current->cos_phi1/current->Rg;
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}

/*--------------------------------------------------------------------------
 * cylindrical_equal_area_ellipsoid (normal aspect)
 *--------------------------------------------------------------------------*/

int init_cylindrical_equal_area_ellipsoid(mapx_class *current)
{
  current->Rg = current->equatorial_radius / current->scale; 
  current->phis = RADIANS(current->lat0);
  current->kz = cos(current->phis)/(sqrt(1.0 - ((current->e2)*sin(current->phis)
						*sin(current->phis))));
  if(current->eccentricity == 0.0)
    current->qp = 2.0;
  else 
    current->qp = (1.0 - (current->e2)) * ((1.0/(1.0 - (current->e2)))
					   - (1.0/(2.0*(current->eccentricity))) * 
					   log((1.0 - (current->eccentricity))
					       / (1.0 + (current->eccentricity))));

  return 0;
}

int cylindrical_equal_area_ellipsoid(mapx_class *current, float lat, float lon, 
					     float *u, float *v)
{
  float x, y, dlon;
  double phi, lam, q, sin_phi;
  
  dlon = (lon - current->lon0);
  NORMALIZE (dlon);
  
  phi = RADIANS(lat);
  lam = RADIANS(dlon);
  
  sin_phi = sin(phi);
  q = (1.0 - current->e2) * ((sin_phi / (1.0 - current->e2 * sin_phi * sin_phi))
			     - (1.0 / (2.0 * current->eccentricity)) * 
			     log((1.0 - current->eccentricity * sin_phi)/
				 (1.0 + current->eccentricity * sin_phi)));
  
  x = (current->Rg * current->kz * lam);
  y = (current->Rg * q) / (2.0 * current->kz);
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y -current->v0;
  
  return 0;
}

int inverse_cylindrical_equal_area_ellipsoid(mapx_class *current, float u, float v, float *lat, float *lon)
{
  double phi, lam, x, y, beta;
  
  x =  current->T00 * (u+current->u0) - current->T01 * (v+current->v0);
  y = -current->T10 * (u+current->u0) + current->T11 * (v+current->v0);
  
  beta = asin(2.0 * y * current->kz/(current->Rg * current->qp));
  
  phi = beta +(((current->e2 / 3.0) + ((31.0/180.0) * current->e4)+
		((517.0/5040.0) * current->e6)) * sin(2.0*beta))+
		  ((((23.0/360.0) * current->e4)+
		    ((251.0/3780.0) * current->e6)) * sin(4.0*beta))+
		      (((761.0/45360.0) * current->e6) * sin(6.0*beta));
  lam = (x/(current->Rg * current->kz));
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
