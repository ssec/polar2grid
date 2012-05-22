/*------------------------------------------------------------------------
 * sinusoidal
 *------------------------------------------------------------------------*/
static const char sinusoidal_c_rcsid[] = "$Id: sinusoidal.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"

const char *id_sinusoidal(void)
{
  return sinusoidal_c_rcsid;
}

int init_sinusoidal(mapx_class *current)
{
  /* no variables require initialization */
  return 0;
}

int sinusoidal(mapx_class *current,
	       double lat, double lon, double *x, double *y)
{
  double dlon;
  double phi, lam;
  
  dlon = lon - current->lon0;
  NORMALIZE(dlon);
  
  phi = RADIANS (lat);
  lam = RADIANS (dlon);
  
  *x =  current->Rg * lam * cos (phi);
  *y =  current->Rg * phi;
  
  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_sinusoidal(mapx_class *current,
		       double x, double y, double *lat, double *lon)
{
  double phi, lam;
  
  x -= current->false_easting;
  y -= current->false_northing;

  phi = y/current->Rg;
  lam = x/(current->Rg*cos(phi));
  
  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}
