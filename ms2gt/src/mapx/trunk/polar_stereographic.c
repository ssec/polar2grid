/*------------------------------------------------------------------------
 * polar_stereographic
 *------------------------------------------------------------------------*/
static const char polar_stereographic_c_rcsid[] = "$Id: polar_stereographic.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"

const char *id_polar_stereographic(void)
{
  return polar_stereographic_c_rcsid;
}

int init_polar_stereographic(mapx_class *current)
{
  if (current->lat1 == 999) current->lat1 = current->lat0;
  current->sin_phi1 = sin (RADIANS (current->lat1));
  if (current->lat0 != 90.00 && current->lat0 != -90.00)
  { fprintf(stderr,"mapx: only polar aspects allowed: lat0 = %7.2f\n",
	    current->lat0);
    return -1;
  }
  return 0;
}

int polar_stereographic(mapx_class *current,
			double lat, double lon, double *x, double *y)
{
  double phi, lam, rho;
  
  phi = RADIANS (lat);
  lam = RADIANS (lon - current->lon0);
  
  if (90.0 == current->lat0)
  { rho = current->Rg * cos(phi) 
      * (1 + current->sin_phi1) / (1 + sin(phi));
    *x =  rho * sin(lam);
    *y = -rho * cos(lam);
  }
  else if (-90.0 == current->lat0)
  { rho = current->Rg * cos(phi) 
      * (1 - current->sin_phi1) / (1 - sin(phi));
    *x = rho * sin(lam);
    *y = rho * cos(lam);
  }
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_polar_stereographic(mapx_class *current,
				double x, double y, double *lat, double *lon)
{
  double phi, lam, rho, c, q;
  
  x -= current->false_easting;
  y -= current->false_northing;

  rho = sqrt(x*x + y*y);
  
  if (90.0 == current->lat0)
  { 
    q = current->Rg*(1 + current->sin_phi1);
    c = 2*atan2(rho, q);
    phi = asin(cos(c));
    lam = atan2(x, -y);
  }
  else if (-90.0 == current->lat0)
  { 
    q = current->Rg*(1 - current->sin_phi1);
    c = 2*atan2(rho, q);
    phi = asin(-cos(c));
    lam = atan2(x, y);
  }
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}

/*------------------------------------------------------------------------
 * polar_stereographic_ellipsoid
 *------------------------------------------------------------------------*/

int init_polar_stereographic_ellipsoid(mapx_class *current)
{
  double numerator, denominator;

  if (current->lat1 == 999) current->lat1 = current->lat0;
  if (current->lat0 != 90.00 && current->lat0 != -90.00)
  { fprintf(stderr,"mapx: only polar aspects allowed: lat0 = %7.2f\n",
	    current->lat0);
    return -1;
  } 
  current->Rg = current->equatorial_radius / current->scale;
  
  if(90.0 == current->lat0)
  {
    current->cos_phi1 = cos(RADIANS(current->lat1));
    current->sin_phi0 = sin(RADIANS(current->lat0));
    current->sin_phi1 = sin(RADIANS(current->lat1));
  }

  else if(-90.0 == current->lat0)     
  {
    current->cos_phi1 = cos(RADIANS(-current->lat1));
    current->sin_phi0 = sin(RADIANS(-current->lat0));
    current->sin_phi1 = sin(RADIANS(-current->lat1));
  }

  current->m1 = ((current->cos_phi1) / sqrt(1 - (current->e2 * current->sin_phi1 
					     * current->sin_phi1)));
  
  numerator = (1 - current->eccentricity * current->sin_phi1);
  denominator =  (1 + current->eccentricity * current->sin_phi1);
   
  if(90.0 == current->lat0)
  {
    current->t1 = tan(PI / 4 - RADIANS(current->lat1) / 2) 
      / pow(numerator / denominator, current->eccentricity / 2);
  }
  
  else if(-90.0 == current->lat0)
  {
    current->t1 = tan(PI / 4 - RADIANS(-current->lat1) / 2) 
      / pow(numerator / denominator, current->eccentricity / 2);
  }
  
  return 0;
}

int polar_stereographic_ellipsoid(mapx_class *current,
				  double lat, double lon, 
				  double *x, double *y)
{
  double phi, lam, rho, t;
  double numerator, denominator;
  double sin_phi;
    
  if (90.0 == current->lat0)
  {  
    phi = RADIANS(lat);
    lam = RADIANS(lon - current->lon0);
  }
  else if(-90.0 == current->lat0)
  {  
    phi = RADIANS(-lat);
    lam = RADIANS(-lon + current->lon0);
  }

  sin_phi = sin(phi);
  numerator = 1.0 + current->eccentricity * sin_phi;
  denominator =  1.0 - current->eccentricity * sin_phi;
  t = sqrt((1.0 - sin_phi) / (1.0 + sin_phi) *
	   pow(numerator / denominator, current->eccentricity));

  if((90.0 != current->lat1) && (-90.0 != current->lat1))
  {
    rho = current->Rg * current->m1 * t / current->t1; 
  }
  else 
  { 
    numerator = 2 * current->Rg * current->scale * t;
    denominator = sqrt(pow(1 + current->eccentricity, 1 + current->eccentricity)
		       * pow(1 - current->eccentricity, 1 - current->eccentricity));
    rho = numerator / denominator;
  }

  *x =  rho * sin(lam);
  *y = -rho * cos(lam);

  if(-90.0 == current->lat0)
  {
    *x = -*x;
    *y = -*y;
  }

  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_polar_stereographic_ellipsoid(mapx_class *current,
					  double x, double y, 
					  double *lat, double *lon)
{
  double phi, lam, rho, chi, t;
  double numerator, denominator;
  double sin2chi, sin4chi, sin6chi;

  x -= current->false_easting;
  y -= current->false_northing;

  rho = sqrt(x*x + y*y);

  if(90.0 == current->lat1 || -90.0 == current->lat1)
  {
    numerator = rho * sqrt(pow(1 + current->eccentricity, 1 + current->eccentricity) 
			   * pow(1 - current->eccentricity, 1 - current->eccentricity) );
    denominator = 2 * current->Rg * current->scale;
    t = numerator / denominator;
  }
  else
  {
    numerator = rho * current->t1;
    denominator = current->Rg * current->m1;
    t = numerator / denominator;
  }
 

  chi = PI / 2.0 - 2.0 * atan(t);
  sin2chi = sin(2.0 * chi);
  sin4chi = sin(4.0 * chi);
  sin6chi = sin(6.0 * chi);

  phi = chi + (sin2chi * current->e2 / 2.0) + (sin2chi * 5.0 * current->e4 / 24.0)
    + (sin2chi * current->e6 / 12.0) + (sin2chi * 13.0 * current->e8 / 360.0) 
      + (sin4chi * 7.0 * current->e4 / 48.0) + (sin4chi * 29.0 * current->e6 / 240.0)
	+ (sin4chi * 811.0 * current->e8 / 11520.0)
	  + (sin6chi * 7.0 * current->e6 / 120.0)
	    +(sin6chi * 81.0 * current->e8 / 1120.0)
	      +(sin(8.0 * chi) * 4279.0 * current->e8 / 161280.0);
     
  if(90.0 == current->lat0)
  {  
    *lat = DEGREES(phi);
    
    lam = atan2(x, -y);
    *lon = DEGREES(lam) + current->lon0;
    NORMALIZE(*lon);
  }
  else if(-90.0 == current->lat0)
  {  
    *lat = -DEGREES(phi);
    
    lam = atan2(-x, y);
    *lon  = -DEGREES(lam) + current->lon0;
    NORMALIZE(*lon);
  } 
  return 0;
}
