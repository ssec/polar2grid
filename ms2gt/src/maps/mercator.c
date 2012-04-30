/*------------------------------------------------------------------------
 * mercator
 *------------------------------------------------------------------------*/
#include "define.h"
#include "mapx.h"

int init_mercator(mapx_class *current)
{ 
  if (current->lat1 == 999) current->lat1 = 30.00;
  current->cos_phi1 = cos (RADIANS (current->lat1));

  return 0;
}

int mercator(mapx_class *current, float lat, float lon, float *u, float *v)
{
  float x, y, dlon;
  double phi, lam;
  
  dlon = lon - current->lon0;
  NORMALIZE(dlon);
  
  phi = RADIANS (lat);
  lam = RADIANS (dlon);
  
  x =  current->Rg * lam;
  y =  current->Rg * log (tan (PI/4 + phi/2));
  
  *u = current->T00*x + current->T01*y - current->u0;
  *v = current->T10*x + current->T11*y - current->v0;
  
  return 0;
}

int inverse_mercator(mapx_class *current, float u, float v, float *lat, float *lon)
{
  double phi, lam, x, y;
  
  x =  current->T00*(u+current->u0) - current->T01*(v+current->v0);
  y = -current->T10*(u+current->u0) + current->T11*(v+current->v0);
  
  phi = PI/2 - 2*atan(exp(-y/current->Rg));
  lam = x/current->Rg;
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
