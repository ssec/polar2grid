/*------------------------------------------------------------------------
 * azimuthal_equal_area
 *------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

int init_azimuthal_equal_area(mapx_class *current)
{ 
  current->sin_phi1 = sin (RADIANS (current->lat0));
  current->cos_phi1 = cos (RADIANS (current->lat0));

  return 0;
}

int azimuthal_equal_area(mapx_class *current, float lat, float lon, float *u, float *v)
{
  float x, y;
  double kp, phi, lam, rho;
  
  phi = RADIANS (lat);
  lam = RADIANS (lon - current->lon0);
  
  if (current->lat0 == 90)
  { rho = 2*current->Rg * sin(PI/4 - phi/2);
    x =  rho * sin(lam);
    y = -rho * cos(lam);
  }
  else if (current->lat0 == -90)
  { rho = 2*current->Rg * cos(PI/4 - phi/2);
    x =  rho * sin(lam);
    y =  rho * cos(lam);
  }
  else
  { kp = sqrt(2./(1+current->sin_phi1*sin(phi) 
		  + current->cos_phi1*cos(phi)*cos(lam)));
    x = current->Rg*kp*cos(phi)*sin(lam);
    y = current->Rg*kp*(current->cos_phi1*sin(phi) 
			- current->sin_phi1*cos(phi)*cos(lam));
  }
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_azimuthal_equal_area(mapx_class *current, float u, float v, 
				 float *lat, float *lon)
{
  double phi, lam, rho, c, x, y;
  
  x =  current->T00*(u+current->u0) - current->T01*(v + current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v + current->v0);
  
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
/*** Not sure what this all is - RSS ****************/
    current->qp = 1 - ( (1 - current->e2) / (2*current->eccentricity)
		       * log( (1 - current->eccentricity)
			     / (1 + current->eccentricity) ) );
    current->q1 = (1 - current->e2) 
      * ( current->sin_phi1 
	 / (1 - current->e2 * current->sin_phi1*current->sin_phi1)
	 - (1 / 2 * current->eccentricity )
	 * log( (1 - current->eccentricity * current->sin_phi1) 
	       / (1 + current->eccentricity * current->sin_phi1) ) );
/*fprintf(stderr, "qp and q1 are: %f : %f\n", current->qp, current->q1); **/
/**************************This is what it should be *******************/
    current->qp = (1 - current->e2) 
      * ( 1 / (1 - current->e2 * current->sin_phi1*current->sin_phi1)
	 - ( (1 / (2 * current->eccentricity) )
	    * log( (1 - current->eccentricity) 
		  / (1 + current->eccentricity) ) ) );

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
  current->cos_phi1 = cos(RADIANS(current->lat0));
  current->sin_phi1 = sin(RADIANS(current->lat0));
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

int azimuthal_equal_area_ellipsoid(mapx_class *current, float lat, float lon, 
					   float *u, float *v)
{
  float x,y;
  double phi, lam, rho, beta; 
  double sin_phi,sin_beta, cos_beta, q, B;
  
  phi = RADIANS(lat);
  lam = RADIANS(lon - current->lon0);
  sin_phi = sin(phi);
  
  
  q = (1.0 - current->e2) * ((sin_phi/(1.0 - current->e2*sin_phi * sin_phi))-
			     (1.0/(2.0 * current->eccentricity)) * 
			     log((1 - current->eccentricity * sin_phi) /
				 (1.0 + current->eccentricity * sin_phi)));
  
  if (current->lat0 == 90.00)
  {
    if (fabs(current->qp - q)<0.00000001)
      rho = 0.0;
    else
      rho = current->Rg * sqrt(current->qp - q);
    x = rho * sin(lam);
    y = -rho * cos(lam);
  }
  else if (current->lat0 == -90.00)
  {
    if (fabs(current->qp - q)<0.00000001)
      rho = 0.0;
    else 
      rho = current->Rg * sqrt(current->qp + q);
    x = rho * sin(lam);
    y = rho * cos(lam);
  }
  
  else
  {
    if(fabs(fabs(q) - fabs(current->qp))<0.00000001)
      beta = RADIANS(90.0)*fabs(q)/q;
    else
      beta = asin(q/current->qp);
    sin_beta = sin(beta);
    cos_beta = cos(beta);
    B = current->Rq * sqrt(2.0/(1.0 + current->sin_beta1 * sin_beta +
				(current->cos_beta1 * cos_beta * 
				 cos(lam))));
    x = B * current->D * cos_beta * sin(lam);
    y = (B/current->D) * ((current->cos_beta1 * sin_beta)-
			  (current->sin_beta1 * cos_beta * 
			   cos(lam)));
  }
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}   

int inverse_azimuthal_equal_area_ellipsoid(mapx_class *current, float u, float v, float *lat, float *lon)
{
  double phi, lam, rho, x, y, ce, beta;
  
  if (current->eccentricity == 0.0)
    {
      return inverse_azimuthal_equal_area(current, u, v, lat, lon);
    }
  else
    {
      x = current->T00 * (u + current->u0) - (current->T01) * (v + current->v0);
      y = -current->T10 * (u + current->u0) + (current->T11) * (v + current->v0);
      
      if (current->lat0 == 90.00)
	{
	  if(x==0.0 && y==0.0)
	    {
	      phi = RADIANS(current->lat0);
	      lam = 0.0;
	    }
	  else
	    {
	      rho = ((x*x)+(y*y));
	      if (rho<0.00000000001)
		beta = asin(1.0 - 0.00000000001/(current->Rg * current->Rg *
						 (1.0-(((1.0 - current->e2) /
							(2.0 * current->eccentricity))) *
						  (log((1.0 - current->eccentricity) /
						       (1.0 + current->eccentricity))))));
	      else
		beta = asin(1.0 - rho /(current->Rg * current->Rg *
					(1.0 - (((1.0 - current->e2)/
						 (2.0 * current->eccentricity))*
						(log((1.0 - current->eccentricity)/
						     (1.0 + current->eccentricity)))))));
	      phi = beta + ((current->e2 / 3.0 +((31.0/180.0) * current->e4)+
			     ((517.0/5040.0) * current->e6)) * sin(2.0*beta))+
		((((23.0/360.0) * current->e4)+
		  ((251.0/3780.0) * current->e6)) * sin(4.0*beta))+
		(((761.0/45360.0)*current->e6) * sin(6.0*beta));
	      lam = atan2(x,(-y));
	    }
	}
      
      else if (current->lat0 == -90.00)
	{ 
	  if (x == 0.0 && y == 0.0)
	    {
	      phi = RADIANS(current->lat0);
	      lam = 0.0;
	    }
	  else
	    { rho = ((x*x) + (y*y));
	    if(rho<0.00000000001)
	      beta = asin(1.0 - 0.00000000001 /(current->Rg * current->Rg *
						(1.0-(((1.0 - current->e2)/
						       (2.0 * current->eccentricity))*
						      (log((1.0 - current->eccentricity)/
							   (1.0 + current->eccentricity)))))));
	    else
	      beta = asin(1.0- rho/(current->Rg * current->Rg *
				    (1.0 - (((1.0 - current->e2)/
					     (2.0 * current->eccentricity))*
					    (log((1.0 - current->eccentricity)/
						 (1.0 + current->eccentricity)))))));
	    lam = atan2(x,y);
	    phi = (-beta) +(((current->e2 / 3.0) + ((31.0/180.0) * current->e4)+
			     ((517.0/5040.0) * current->e6)) * sin(2.0*beta))+
	      ((((23.0/360.0) * current->e4)+
		((251.0/3780.0) * current->e6)) * sin(4.0*beta))+
	      (((761.0/45360.0) * current->e6) * sin(6.0*beta));
	    }
	}
      else 
	{ rho = sqrt(((x / current->D) * (x / current->D)) +
		     (current->D * y *current->D * y));
	ce = 2*asin(rho/(2.0 * current->Rq));
	
	if (rho<0.00000001)
	  beta = current->beta1;
	else
	  beta = asin ((cos(ce) * current->sin_beta1)+
		       (current->D * y * sin(ce) * current->cos_beta1 / rho));
	phi = beta +(((current->e2 / 3.0) + ((31.0/180.0) * current->e4)+
		      ((517.0/5040.0) * current->e6)) * sin(2.0*beta))+
	  ((((23.0/360.0) * current->e4)+
	    ((251.0/3780.0) * current->e6)) * sin(4.0*beta))+
	  (((761.0/45360.0) * current->e6) * sin(6.0*beta));
	lam = atan2(x * sin(ce),((current->D * rho * current->cos_beta1 * cos(ce))-
				 (current->D * current->D * y * 
				  current->sin_beta1 * sin(ce))));
	
	}
      *lat = DEGREES(phi);
      *lon = DEGREES(lam) + current->lon0;
      NORMALIZE(*lon);
      
      return 0;
    }
}
