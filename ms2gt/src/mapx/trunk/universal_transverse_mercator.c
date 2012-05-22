/*------------------------------------------------------------------------
 * universal_transverse_mercator
 *------------------------------------------------------------------------*/
static const char universal_transverse_mercator_c_rcsid[] = "$Id: universal_transverse_mercator.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "mapx.h"
#include "keyval.h"

/*************************************************************************
 * CAVEAT - at this time UTM will return invalid results for points wildly
 * outside the zone. Sometimes the returned coordinates will even be
 * inside the zone. So, you should do your own gross bounds checking
 * before sending points to forward_mapx. Calling within_mapx won't help
 * this problem.
 *************************************************************************/

int init_transverse_mercator_ellipsoid(mapx_class *current);

static int process_utm_zone(mapx_class *current);

const char *id_unversal_transverse_mercator(void)
{
  return universal_transverse_mercator_c_rcsid;
}

int init_universal_transverse_mercator(mapx_class *current)
{
  int ret_code;

  ret_code = process_utm_zone(current);
  if (!ret_code)
    ret_code = init_transverse_mercator_ellipsoid(current);

  return(ret_code);
}

/*------------------------------------------------------------------------
 * process_utm_zone - perform necessary processing of UTM zone
 *
 *	input : current - pointer to current mapx structure.
 *
 *	result: 0 - ok
 *              -1 - error
 */

static int process_utm_zone(mapx_class *current)
{
  int ret_code = 0;

  if (current->utm_zone < -60 || current->utm_zone > 60) {
    fprintf(stderr,
	    "mapx: UTM zone must be in the range -60 to 60: utm_zone = %d\n",
	    current->utm_zone);
    ret_code = -1;
  } else if (current->utm_zone == 0 &&
	     (current->lat0 == 999 || current->lon0 == 999)) {
    fprintf(stderr,
	    "mapx: map reference latitude and longitude must be specified\n");
    fprintf(stderr,
	    "      if utm_zone is 0.\n");
    ret_code = -1;
  } else {
    if (current->utm_zone == 0) {
      if (current->lon0 >= 180.0)
	current->lon0 -= 360.0;
      current->utm_zone = (int)((current->lon0 + 180.0) / 6.0 + 1.0);
      if (current->lat0 < 0)
	current->utm_zone *= -1;
    }
    current->lat0 = 0.0;
    current->lon0 = 6 * abs(current->utm_zone) - 183.0;
    if (999 == current->center_lat && KEYVAL_UNINITIALIZED == current->x0) {
      if (mapx_verbose) fprintf(stderr,
				"> assuming map origin lat is same as ref. lat %f\n",
				current->lat0);
      current->center_lat = current->lat0;
    }
    if (999 == current->center_lon && KEYVAL_UNINITIALIZED == current->x0) {
      if (mapx_verbose) fprintf(stderr,
				"> assuming map origin lon is same as ref. lon %f\n",
				current->lon0);
      current->center_lon = current->lon0;
    }
    if (KEYVAL_UNINITIALIZED == current->false_easting)
      current->false_easting = 500000.0;
    if (KEYVAL_UNINITIALIZED == current->false_northing)
      current->false_northing = (current->utm_zone > 0) ? 0.0 : 1e7;
  }

  return(ret_code);
}
