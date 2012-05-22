/*------------------------------------------------------------------------
 * cylindrical_equidistant
 *------------------------------------------------------------------------*/
static const char cylindrical_equidistant_c_rcsid[] = "$Id: cylindrical_equidistant.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"

const char *id_cylindrical_equidistant(void)
{
  return cylindrical_equidistant_c_rcsid;
}

int init_cylindrical_equidistant(mapx_class *current)
{ 
  if (current->lat1 == 999) current->lat1 = 0.00;
  current->cos_phi1 = cos (RADIANS (current->lat1));

  return 0;
}

int cylindrical_equidistant (mapx_class *current,
			     double lat, double lon, double *x, double *y)
{
  double dlon;
  double phi, lam;
  
  dlon = lon - current->lon0;
  NORMALIZE(dlon);
  
  phi = RADIANS (lat);
  lam = RADIANS (dlon);
  
  *x =  current->Rg * lam * current->cos_phi1;
  *y =  current->Rg * phi;
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_cylindrical_equidistant (mapx_class *current,
				     double x, double y,
				     double *lat, double *lon)
{
  double phi, lam;
  
  x -= current->false_easting;
  y -= current->false_northing;

  phi = y/current->Rg;
  lam = x/(current->Rg*current->cos_phi1);
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
