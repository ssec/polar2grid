/*------------------------------------------------------------------------
 * mercator
 *------------------------------------------------------------------------*/
static const char mercator_c_rcsid[] = "$Id: mercator.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"

const char *id_mercator(void)
{
  return mercator_c_rcsid;
}

int init_mercator(mapx_class *current)
{ 
  if (current->lat1 == 999) current->lat1 = 30.00;
  current->cos_phi1 = cos (RADIANS (current->lat1));

  return 0;
}

int mercator(mapx_class *current, double lat, double lon, double *x, double *y)
{
  double dlon;
  double phi, lam;
  
  dlon = lon - current->lon0;
  NORMALIZE(dlon);
  
  phi = RADIANS (lat);
  lam = RADIANS (dlon);
  
  *x =  current->Rg * lam;
  *y =  current->Rg * log (tan (PI/4 + phi/2));
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_mercator(mapx_class *current,
		     double x, double y, double *lat, double *lon)
{
  double phi, lam;
  
  x -= current->false_easting;
  y -= current->false_northing;

  phi = PI/2 - 2*atan(exp(-y/current->Rg));
  lam = x/current->Rg;
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
