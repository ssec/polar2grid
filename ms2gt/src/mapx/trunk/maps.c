/*========================================================================
 * maps - map utility functions
 *
 * 18-Aug-1992 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1992 University of Colorado
 *========================================================================*/
static const char maps_c_rcsid[] = "$Id: maps.c 16072 2010-01-30 19:39:09Z brodzik $";

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <float.h>
#include "define.h"
#define maps_c_
#include "maps.h"

const char *id_maps(void)
{
  return maps_c_rcsid;
}

/*------------------------------------------------------------------------
 * draw_graticule - draw and (optionally) label grid of lat,lon lines
 *
 *	input : mapx - map definition
 *		move_pu - move pen up function
 *		draw_pd - draw pen down function
 *		label - print label function or NULL
 *
 *------------------------------------------------------------------------*/
void draw_graticule(mapx_class *mapx, int (*move_pu)(double lat, double lon),
		    int (*draw_pd)(double lat, double lon),
		    int (*label)(char *string, double lat, double lon))
{ double lat, lon, east, llon;
  char label_string[5];
  
  east = mapx->map_stradles_180 ? mapx->east+360 : mapx->east;
  
/*
 *	draw parallels
 */
  if (mapx->lat_interval > 0)
  { for (lat = mapx->south; lat <= mapx->north; lat += mapx->lat_interval)
    { move_pu(lat, (double)mapx->west);
      for (lon = mapx->west+1; lon < east; lon++)
	draw_pd(lat, lon);
      draw_pd(lat, east);
    }
  }

/*
 *	draw meridians
 */
  if (mapx->lon_interval > 0)
  { for (lon = mapx->west; lon <= east; lon += mapx->lon_interval)
    { move_pu((double)mapx->south, lon);
      for (lat = mapx->south+1; lat < mapx->north; lat++)
	draw_pd(lat, lon);
      draw_pd((double)mapx->north, lon);
    }
  }

/*
 *	label parallels
 */
  if (label != NULL)
  { if (mapx->lat_interval > 0)
    { lon = mapx->label_lon;
      for (lat = mapx->south; lat <= mapx->north; lat += mapx->lat_interval)
      { sprintf(label_string,"%3d%c", (int)fabs(lat), lat < 0 ? 'S' : 'N');
	label(label_string, lat, lon);
      }
    }

/*
 *	label meridians
 */
    if (mapx->lon_interval > 0)
    { lat = mapx->label_lat;
      for (lon = mapx->west; lon <= east; lon += mapx->lon_interval)
      { llon = lon < 180 ? lon : lon-360;
	sprintf(label_string,"%3d%c", (int)fabs(llon), llon < 0 ? 'W' : 'E');
	label(label_string, lat, lon);
      }
    }
  }
}

/*----------------------------------------------------------------------
 * arc_length - returns arc length from lat1,lon1 to lat2,lon2
 *		in same units as specified Earth radius
 *
 *	input : lat1,lon1, lat2,lon2 - in decimal degrees
 *		Re - Earth radius
 *
 *----------------------------------------------------------------------*/
double arc_length(double lat1, double lon1, double lat2, double lon2, double Re)
{ double phi1, lam1, phi2, lam2, beta;

  if (lat1 == lat2 && lon1 == lon2) return (double)0;

  phi1 = radians(lat1);
  lam1 = radians(lon1);
  phi2 = radians(lat2);
  lam2 = radians(lon2);
  beta = acos( cos(phi1) * cos(phi2) * cos(lam1-lam2)
	      + sin(phi1) * sin(phi2) );
  return (double)(Re * beta);
}
/*----------------------------------------------------------------------
 * arc_length_km - returns arc length (km) from lat1,lon1 to lat2,lon2
 *
 *	input : lat1,lon1, lat2,lon2 - in decimal degrees
 *
 *----------------------------------------------------------------------*/
double arc_length_km (double lat1, double lon1, double lat2, double lon2)
{ 
  return arc_length(lat1, lon1, lat2, lon2, mapx_Re_km);
}

/*----------------------------------------------------------------------
 * west_azimuth - azimuth west of north
 *
 *	input : lat1,lon1, lat2,lon2 (decimal degrees)
 *
 *	result: signed angle west of north from pt. 1 to 2 (decimal degrees)
 *
 *----------------------------------------------------------------------*/
double west_azimuth(double lat1, double lon1, double lat2, double lon2)
{ double phi1, phi2, dlam, sin_A, cos_A, A;

  phi1 = radians(lat1);
  phi2 = radians(lat2);
  dlam = radians(lon1 - lon2);

  sin_A = cos(phi2)*sin(dlam);
  cos_A = cos(phi1)*sin(phi2) - sin(phi1)*cos(phi2)*cos(dlam);
  A = (cos_A != 0 ? atan2(sin_A, cos_A) : 0);

  return (double)degrees(A);
}

/*----------------------------------------------------------------------
 * bisect - find geographic point exactly halfway between two points
 *
 *	input : lat1,lon1, lat2,lon2 - end points (decimal degrees)
 *
 *	output: lat,lon - mid-point (decimal degrees)
 *
 *	result: TRUE == success
 *		FALSE == error, lat,lon are undefined
 *
 *----------------------------------------------------------------------*/
bool bisect(double lat1, double lon1, double lat2, double lon2, 
	    double *lat, double *lon)
{ double phi1,lam1, phi2, lam2, beta;
  double x1, y1, z1, x2, y2, z2, x, y, z, d;
  static double tolerance=0;

  if (0 == tolerance)
  { tolerance = 10*DBL_EPSILON;
  }

  phi1 = radians(90.0 - lat1);
  lam1 = radians(lon1);
  phi2 = radians(90.0 - lat2);
  lam2 = radians(lon2);
  
/*
 *	convert to rectangular
 */
  x1 = sin(phi1) * cos(lam1);
  y1 = sin(phi1) * sin(lam1);
  z1 = cos(phi1);
  
  x2 = sin(phi2) * cos(lam2);
  y2 = sin(phi2) * sin(lam2);
  z2 = cos(phi2);
  
/*
 *	assume spherical earth
 *	normalized sum will bisect
 */
  x = x1 + x2;
  y = y1 + y2;
  z = z1 + z2;
  d = sqrt(x*x + y*y + z*z);
  if (d < tolerance) return FALSE; /* end points are diametrically opposed */

/*
 *	convert back to spherical
 */
  beta = acos(z/d);
  *lat = 90.0 - degrees(beta);
  *lon = degrees(atan2(y, x));

  return TRUE;
}

/*------------------------------------------------------------------------
 * sscanf_lat_lon - scan lat lon from string buffer
 *
 *	input : readln - pointer to buffer
 *
 *	output: lat, lon - latitude, longitude in decimal degrees
 *
 *	result: 2 - success
 *		0 - error scanning string
 *
 *	format: dd mm N/S dd mm E/W => degrees minutes
 *		[+/-]dd.dd [N/S] [+/-]dd.dd [E/W] => decimal degrees
 *
 *------------------------------------------------------------------------*/
int sscanf_lat_lon(char *readln, double *lat, double *lon)
{ double dlat, dlon, mlat, mlon;
  char ns[2], ew[2];
  
  if (sscanf(readln,"%lf %lf %s %lf %lf %s",
	     &dlat,&mlat,ns, &dlon,&mlon,ew) == 6)
  { *lat = (dlat + mlat/60.);
    if (*ns == 's' || *ns == 'S')
      *lat = -*lat;
    else if (*ns != 'n' && *ns != 'N')
      return 0;
    
    *lon = (dlon + mlon/60.);
    if (*ew == 'w' || *ew == 'W')
      *lon = -*lon;
    else if (*ew != 'e' && *ew != 'E')
      return 0;
    
    return 2;
  }
  else if (sscanf(readln,"%lf %s %lf %s", &dlat,ns, &dlon,ew) == 4)
  { *lat = dlat;
    if (*ns == 's' || *ns == 'S')
      *lat = -*lat;
    else if (*ns != 'n' && *ns != 'N')
      return 0;
    
    *lon = dlon;
    if (*ew == 'w' || *ew == 'W')
      *lon = -*lon;
    else if (*ew != 'e' && *ew != 'E')
      return 0;
    *lon = dlon * (*ew == 'e' || *ew == 'E' ? 1 : -1);
    
    return 2;
  }
  else if (sscanf(readln,"%lf %lf", &dlat, &dlon) == 2)
  { *lat = dlat;
    *lon = dlon;
    return 2;
  }
  else if (lat_lon_decode(readln, LAT_DESIGNATORS, &dlat)
	   && lat_lon_decode(readln, LON_DESIGNATORS, &dlon))
  { *lat = dlat;
    *lon = dlon;
    return 2;
  }
  else
    return 0;
}

/*------------------------------------------------------------------------
 * lat_lon_decode - decode lat or lon (decimal degrees) from buffer
 *
 *	input : readln - pointer to buffer
 *		designators - string of possible hemisphere designators
 *			for example "EWew" to extract a longitude
 *
 *	output: value - latitude or longitude in decimal degrees
 *
 *	result: 1 - success
 *		0 - error scanning string
 *
 *	format: dd.dd[optional white space]designator
 *		this function will attempt to extract the value from
 *		anywhere in the buffer up to the first newline
 *
 *------------------------------------------------------------------------*/
int lat_lon_decode(const char *readln, const char *designators, double *value)
{ const char *end, *pos;
  char hemi, number[80];
  int len;

  end = strchr(readln, '\n');
  if (NULL == end) end = readln + strlen(readln);

  pos = strpbrk(readln, designators);
  if (NULL == pos || pos > end) return 0;

  hemi = toupper(*pos);

  while (pos > readln && isspace(*--pos));

  while (pos > readln && NULL != strchr("0123456789.+-", *--pos));

  if (NULL == strchr("0123456789.+-", *pos)) ++pos;

  len = strspn(pos, "0123456789.+-");
  if (len <= 0) return 0;
  strncpy(number, pos, len);
  number[len] = '\0';

  if (sscanf(number, "%lf", value) != 1) return 0;

  if ('W' == hemi || 'S' == hemi) *value = -(*value);

  return 1;
}

/*------------------------------------------------------------------------
 * search_path_fopen - search for file in colon separated list of directories
 *
 *	input : filename - name of file to try first
 *		pathvar - environment variable containing path
 *		mode - same as fopen modes ("r", "w", etc.)
 *
 *	output: filename - name of file successfully openned
 *
 *	result: file pointer of openned file or NULL on failure
 *
 *	note  : directories are searched in order
 *		if first attempt to open file fails then the directory
 *		information preceeding the filename is stripped before
 *		searching the directory path
 *
 *------------------------------------------------------------------------*/
FILE *search_path_fopen(char *filename, const char *pathvar, const char *mode)
{ const char *envpointer;
  char *basename = NULL, *directory, *pathvalue = NULL;
  FILE *fp = NULL;

/*
 *	try to open original name
 */
  fp = fopen(filename, mode);

/* 
 *	failing that, get path information
 */
  if (fp == NULL)
  { envpointer = getenv(pathvar);

/*
 *	strip off directory name
 */
    if (envpointer != NULL)
    { pathvalue = strdup(envpointer);
      basename = strrchr(filename,'/');
      basename = (basename != NULL) ? strdup(basename+1) : strdup(filename);
      if (basename == NULL) return NULL;

/*
 *	try each directory in turn
 */
      directory = strtok(pathvalue, ": ");
      while (directory != NULL)
      {	strcat(strcat(strcpy(filename, directory), "/"), basename);
	fp = fopen(filename, mode);
	if (fp != NULL) break;
	directory = strtok(NULL, ": ");
      }
    }
  }
  if (basename != NULL) free(basename);
  if (pathvalue != NULL) free(pathvalue);

  return fp;
}

/*------------------------------------------------------------------------
 * ellipsoid_radius - ellipsoidal radius at given latitude
 *
 *	input : sin_phig, cos_phig - sin and cosine of 
 *				     parametric latitude
 *		Ae2 - equatorial radius squared
 *		Be2 - polar radius squared
 *		
 *	result: ellipsoidal radius at given latitude
 *
 *------------------------------------------------------------------------*/
double ellipsoid_radius(double sin_phig, double cos_phig, 
			double Ae2, double Be2)
{ 
  return sqrt(Ae2*Be2 / (Ae2*sin_phig*sin_phig + Be2*cos_phig*cos_phig));
}

/*------------------------------------------------------------------------
 * geo_to_rectangular - convert geographic to rectangular coordinates
 *
 *	input : lat, lon - geodetic coord.s (decimal degrees)
 *		Ae2 - equatorial radius squared
 *		Be2 - polar radius squared
 *
 *	output: r - rectangular coord.s (same units as Ae and Be)
 *
 *------------------------------------------------------------------------*/
void geo_to_rectangular(double r[3], double lat, double lon, 
			double Ae2, double Be2)
{ 
  double phi, phig, lam, sin_phig, cos_phig, Re;

  if (90 == lat)
  { r[0] = r[1] = 0;
    r[2] = sqrt(Be2);
    return;
  }
  else if (-90 == lat)
  { r[0] = r[1] = 0;
    r[2] = -sqrt(Be2);
    return;
  }

  assert(-90 < lat && lat < 90);

  phi = radians(lat);
  lam = radians(lon);
  phig = atan(Be2/Ae2*tan(phi)); /* geocentric latitude */

  sin_phig = sin(phig);
  cos_phig = cos(phig);

  Re = ellipsoid_radius(sin_phig, cos_phig, Ae2, Be2);

  r[0] = Re*cos_phig*cos(lam);
  r[1] = Re*cos_phig*sin(lam);
  r[2] = Re*sin_phig;

}

/*------------------------------------------------------------------------
 * stp_test - scalar triple product test 
 *
 *	input : r1, r2, r3 - rectangular coordinates
 *
 *	result: 1 == first point is to the left of the line
 *		joining the second and third points
 *	       -1 == to the right
 *		0 == indeterminate
 *
 *------------------------------------------------------------------------*/
static int stp_test(double r1[3], double r2[3], double r3[3])
{ 
  double product;

  product =
    r1[0]*r2[1]*r3[2]
      + r2[0]*r3[1]*r1[2]
	+ r3[0]*r1[1]*r2[2]
	  - r3[0]*r2[1]*r1[2]
	    - r1[0]*r3[1]*r2[2]
	      -r2[0]*r1[1]*r3[2];

  if (fabs(product) < 10*DBL_EPSILON) product = 0;

  return product > 0 ? 1 : product < 0 ? -1 : 0;
}

/*------------------------------------------------------------------------
 * point_within_polygon - determine if point is within polygon
 *
 *	input : pt - rectangular coord.s of point
 *		poly - rectangular coord.s of polygon vertices
 *		       vertices must be listed in order clockwise
 *		num_points - number of vertices
 *		is_convex - TRUE iff polygon is known to be convex
 *
 *	result: TRUE == point is definitely within polygon
 *		FALSE == don't know (outside if is_convex)
 *
 *	note  : not yet implemented for non-convex polygons
 *		always returns FALSE if is_convex == FALSE
 *
 *------------------------------------------------------------------------*/
static bool point_within_polygon(double pt[3], double poly[][3],
			  int num_points, bool is_convex)
{ register int vertex;

  if (!is_convex) return FALSE;

/*
 *	if point is inside then it will be on or to 
 *	the right of each side, start with the last side
 */
  if (stp_test(pt, poly[num_points-1], poly[0]) > 0) return FALSE;

/*
 *	check the other sides
 */
  for (vertex = 0; vertex < num_points-1; vertex++)
  { if (stp_test(pt, poly[vertex], poly[vertex+1]) > 0) return FALSE;
  }

  return TRUE;
}

/*------------------------------------------------------------------------
 * point_within_box - determine if point is within any quadrilateral
 *
 *	input : lat_pt, lon_pt - point (decimal degrees)
 *		lat_box, lon_box - quadrilateral vertices (decimal degrees)
 *		       vertices must be listed in order clockwise
 *
 *	result: TRUE == point is definitely within box
 *		FALSE == point is probably not in box
 *
 *------------------------------------------------------------------------*/
bool point_within_box(double lat_pt, double lon_pt, 
		      double lat_box[4], double lon_box[4])
{
  register int dim, vertex, concave_vertex=-1;
  static const char *triangle1[] = { "\0\1\2", "\1\0\3", "\2\3\0", "\3\0\1" };
  static const char *triangle2[] = { "\0\3\2", "\1\2\3", "\2\1\0", "\3\2\1" };
  double pt[3], box[4][3], tri[3][3];

/*
 *	convert to rectangular
 */
 geo_to_rectangular(pt, lat_pt, lon_pt, 1, 1);

 for (vertex = 0; vertex < 4; vertex++)
 { geo_to_rectangular(box[vertex], lat_box[vertex], lon_box[vertex], 1, 1);
 }

/*
 *	see if any corner is concave and keep track of which one
 */
  for (vertex = 0; vertex < 4; vertex++)
  { if (stp_test(box[vertex], box[(vertex+1)%4], box[(vertex+2)%4]) > 0)
    { concave_vertex = (vertex+1)%4;
      break;
    }
  }

/*
 *	divide concave quadrilaterals into two triangles
 *	otherwise just test for four sided convex polygon
 */
  if (concave_vertex >= 0)
  { 
    for (vertex = 0; vertex < 3; vertex++)
    { for (dim = 0; dim < 3; dim++)
      { tri[vertex][dim] = box[triangle1[concave_vertex][vertex]][dim];
      }
    }

    if (point_within_polygon(pt, tri, 3, TRUE)) 
    { return TRUE;
    }
    else
    { 
      for (vertex = 0; vertex < 3; vertex++)
      { for (dim = 0; dim < 3; dim++)
	{ tri[vertex][dim] = box[triangle2[concave_vertex][vertex]][dim];
	}
      }

      return point_within_polygon(pt, tri, 3, TRUE);
    }
  }
  else
  { 
    return point_within_polygon(pt, box, 4, TRUE);
  }
}
