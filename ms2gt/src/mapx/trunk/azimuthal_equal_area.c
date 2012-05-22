/*------------------------------------------------------------------------
 * azimuthal_equal_area
 *------------------------------------------------------------------------*/
static const char azimuthal_equal_area_c_rcsid[] = "$Id: azimuthal_equal_area.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "proj.h"
#include "define.h"
#include "mapx.h"

const char *id_azimuthal_equal_area(void)
{
  return azimuthal_equal_area_c_rcsid;
}

int init_azimuthal_equal_area(mapx_class *current)
{ 
  current->sin_phi1 = sin (RADIANS (current->lat0));
  current->cos_phi1 = cos (RADIANS (current->lat0));

  return 0;
}

int azimuthal_equal_area(mapx_class *current,
			 double lat, double lon, double *x, double *y)
{
  double kp, phi, lam, rho;
  
  phi = RADIANS (lat);
  lam = RADIANS (lon - current->lon0);
  
  if (current->lat0 == 90)
  { rho = 2*current->Rg * sin(PI/4 - phi/2);
    *x =  rho * sin(lam);
    *y = -rho * cos(lam);
  }
  else if (current->lat0 == -90)
  { rho = 2*current->Rg * cos(PI/4 - phi/2);
    *x =  rho * sin(lam);
    *y =  rho * cos(lam);
  }
  else
  { kp = sqrt(2./(1+current->sin_phi1*sin(phi) 
		  + current->cos_phi1*cos(phi)*cos(lam)));
    *x = current->Rg*kp*cos(phi)*sin(lam);
    *y = current->Rg*kp*(current->cos_phi1*sin(phi) 
			- current->sin_phi1*cos(phi)*cos(lam));
  }

  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_azimuthal_equal_area(mapx_class *current, double x, double y, 
				 double *lat, double *lon)
{
  double phi, lam, rho, c;
  
  x -= current->false_easting;
  y -= current->false_northing;

  rho = sqrt(x*x + y*y);
  
  if (rho != 0.0)
  { c = 2*asin( rho/(2*current->Rg) );
    
    phi = asin( cos(c)*current->sin_phi1 + y*sin(c)*current->cos_phi1/rho );
    
    if (current->lat0 == 90)
      lam = atan2(x, -y);
    else if (current->lat0 == -90)
      lam = atan2(x, y);
    else
      lam = atan2(x*sin(c), rho*current->cos_phi1*cos(c)
		  - y*current->sin_phi1*sin(c));
  }
  else
  { phi = RADIANS(current->lat0);
    lam = 0.0;
  }
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}

/*-----------------------------------------------------------------------
 * Azimuthal_Equal_Area_Ellipsoid
 *------------------------------------------------------------------------*/

int init_azimuthal_equal_area_ellipsoid(mapx_class *current)
{
  current->cos_phi1 = cos(RADIANS(current->lat0));
  current->sin_phi1 = sin(RADIANS(current->lat0));
  
  if(current->eccentricity == 0.0)
  {
    current->qp = 2.0;
    current->q1 = 2.0;
  }
  else
  {
    current->qp = 1 - ( (1 - current->e2) / (2*current->eccentricity)
		       * log( (1 - current->eccentricity)
			     / (1 + current->eccentricity) ) );

    current->q1 = (1 - current->e2) 
      * ( current->sin_phi1 
	 / (1 - current->e2 * current->sin_phi1*current->sin_phi1)
	 - ( (1 / (2 * current->eccentricity) )
	 * log( (1 - current->eccentricity * current->sin_phi1) 
	       / (1 + current->eccentricity * current->sin_phi1) ) ));
/* fprintf(stderr, "qp and q1 are: %f : %f\n", current->qp, current->q1);**/
 }
  current->Rg = current->equatorial_radius / current->scale;
  current->Rq = current->Rg *(sqrt(current->qp/2));
  if (fabs(current->q1) >= fabs(current->qp))
    current->beta1 = RADIANS(90)*(fabs(current->q1/current->qp)
				  /(current->q1/current->qp));
  else
    current->beta1 = asin(current->q1/current->qp);
  current->sin_beta1 = sin(current->beta1); 
  current->cos_beta1 = cos(current->beta1); 
  current->m1 = current->cos_phi1 / sqrt(1 - current->e2 
					 * current->sin_phi1 
					 * current->sin_phi1);
  current->D = (current->Rg * current->m1) / (current->Rq * current->cos_beta1);
  return 0;
}

int azimuthal_equal_area_ellipsoid(mapx_class *current, double lat, double lon, 
					   double *x, double *y)
{
  double phi, lam, rho, beta; 
  double sin_phi,sin_beta, cos_beta, q, B;
  double epsilon = 1e-6;
  
  phi = RADIANS(lat);
  lam = RADIANS(lon - current->lon0);
  sin_phi = sin(phi);
  
  
  q = (1.0 - current->e2) * ((sin_phi/(1.0 - current->e2*sin_phi * sin_phi))-
			     (1.0/(2.0 * current->eccentricity)) * 
			     log((1 - current->eccentricity * sin_phi) /
				 (1.0 + current->eccentricity * sin_phi)));
  
  if (current->lat0 == 90.00)
  {
    if (fabs(current->qp - q) < epsilon)
      rho = 0.0;
    else
      rho = current->Rg * sqrt(current->qp - q);
    *x = rho * sin(lam);
    *y = -rho * cos(lam);
  }
  else if (current->lat0 == -90.00)
  {
    if (fabs(current->qp + q) < epsilon)
      rho = 0.0;
    else 
      rho = current->Rg * sqrt(current->qp + q);
    *x = rho * sin(lam);
    *y = rho * cos(lam);
  }
  
  else
  {
    beta = asinz(q / current->qp);
    sin_beta = sin(beta);
    cos_beta = cos(beta);
    B = current->Rq * sqrt(2.0/(1.0 + current->sin_beta1 * sin_beta +
				(current->cos_beta1 * cos_beta * 
				 cos(lam))));
    *x = B * current->D * cos_beta * sin(lam);
    *y = (B/current->D) * ((current->cos_beta1 * sin_beta)-
			  (current->sin_beta1 * cos_beta * 
			   cos(lam)));
  }
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}   

int inverse_azimuthal_equal_area_ellipsoid(mapx_class *current,
					   double x, double y,
					   double *lat, double *lon)
{
  double phi, lam, rho, ce, q;
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
  
  if (current->eccentricity == 0.0)
    {
      return inverse_azimuthal_equal_area(current, x, y, lat, lon);
    }
  else
    {
      x -= current->false_easting;
      y -= current->false_northing;

      if (fabs(current->lat0) != 90) {
	rho = sqrt(((x / current->D) * (x / current->D)) +
		   (current->D * y *current->D * y));
	ce = 2*asin(rho/(2.0 * current->Rq));
	
	lam = atan2(x * sin(ce),
		    ((current->D * rho * current->cos_beta1 * cos(ce))-
		     (current->D * current->D * y * 
		      current->sin_beta1 * sin(ce))));
	
	q = fabs(rho) < epsilon ?
	  current->qp * current->sin_beta1 :
	  current->qp * (cos(ce) * current->sin_beta1 +
			 current->D * y * sin(ce) * current->cos_beta1 / rho);
      } else {
	rho = sqrt(x * x + y * y);
	ce = rho / current->Rg;
	lam = atan2( x, sign(current->lat0) * -y);
	q = sign(current->lat0) * (current->qp - ce * ce);
      }
      
      /***  Calculate phi using equation 3-16, Snyder 1987, p188 ***/
      
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
}
