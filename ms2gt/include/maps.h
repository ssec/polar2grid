/*========================================================================
 * maps - map utility functions
 *
 * 18-Aug-1992 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1992 University of Colorado
 *========================================================================*/
#ifndef maps_h_
#define maps_h_

#ifdef maps_c_
const char maps_h_rcsid[] = "$Id: maps.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

#include "define.h"
#include "mapx.h"

#define LAT_DESIGNATORS "NSns"
#define LON_DESIGNATORS "EWew"

/*
 *	printf latitude north south, use %5.2f%c format
 *	for example printf("%5.2f%c", PF_LAT_NS(lat));
 */

#define PF_LAT_NS(lat) fabs((double)lat), ((lat) >= 0 ? 'N' : 'S')

/*
 *	printf longitude east west, use %6.2f%c format
 *	for example printf("%6.2f%c", PF_LON_EW(lon));
 */

#define PF_LON_EW(lon) fabs((double)lon), ((lon) >= 0 ? 'E' : 'W')

/*
 *	function prototypes
 */
void draw_graticule(mapx_class *mapx, int (*move_pu)(double lat, double lon),
		    int (*draw_pd)(double lat, double lon),
		    int (*label)(char *string, double lat, double lon));

double arc_length(double lat1, double lon1, double lat2, double lon2,
		  double Re);

double arc_length_km(double lat1, double lon1, double lat2, double lon2);

double west_azimuth(double lat1, double lon1, double lat2, double lon2);

bool bisect(double lat1, double lon1, double lat2, double lon2, 
	    double *lat, double *lon);

int sscanf_lat_lon(char *readln, double *lat, double *lon);

int lat_lon_decode(const char *readln, const char *designators, double *value);

FILE *search_path_fopen(char *filename, const char *pathvar, const char *mode);

double ellipsoid_radius(double sin_phig, double cos_phig, 
			double Ae2, double Be2);

void geo_to_rectangular(double r[3], double lat, double lon, 
			double Ae2, double Be2);

bool point_within_box(double lat_pt, double lon_pt, 
		      double lat_box[4], double lon_box[4]);

#endif
