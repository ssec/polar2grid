/*------------------------------------------------------------------------
 * orthographic
 *------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

int init_orthographic(mapx_class *current)
{ 
  current->cos_phi1 = cos (RADIANS (current->lat0));
  current->sin_phi1 = sin (RADIANS (current->lat0));

  return 0;
}

int orthographic(mapx_class *current, float lat, float lon, float *u, float *v)
{
  float x, y;
  float phi, lam, sin_phi, cos_phi, sin_lam, cos_lam, cos_beta;
  
  phi = RADIANS (lat);
  lam = RADIANS (lon - current->lon0);
  
  sin_phi = sin(phi);
  cos_phi = cos(phi);
  cos_lam = cos(lam);
  
  cos_beta = current->sin_phi1 * sin_phi
    + current->cos_phi1 * cos_phi * cos_lam;
  
  if (cos_beta < 0.0) return(-1);
  
  sin_lam = sin(lam);
  x = current->Rg * cos_phi * sin_lam;
  y = current->Rg * (current->cos_phi1*sin_phi 
		     - current->sin_phi1*cos_phi*cos_lam);
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_orthographic(mapx_class *current, float u, float v, float *lat, float *lon)
{
  double phi, lam, rho, x, y, cos_beta, sin_beta;
  
  x =  current->T00*(u+current->u0) - current->T01*(v+current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v+current->v0);
  
  rho = sqrt(x*x + y*y);
  if (rho == 0.0)
  { phi = RADIANS (current->lat0);
    lam = 0.0;
  }
  else
  { sin_beta = rho/current->Rg;
    cos_beta = sqrt(1 - sin_beta*sin_beta);
    phi = asin(cos_beta*current->sin_phi1 
	       + y*sin_beta*current->cos_phi1/rho);
    if (current->lat0 == 90)
    { lam = atan2(x, -y);
    }
    else if (current->lat0 == -90)
    { lam = atan2(x, y);
    }
    else
    { lam = atan2(x*sin_beta, rho*current->cos_phi1*cos_beta
		  - y*current->sin_phi1*sin_beta);
    }
  }
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
