/*========================================================================
 * map projections - convert geographic to map coordinates
 *
 * 2-July-1991 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * 10-Dec-1992 R.Swick swick@kryos.colorado.edu 303-492-1395
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1991 University of Colorado
 *========================================================================*/
static const char mapx_c_rcsid[] = "$Id: mapx.c 16072 2010-01-30 19:39:09Z brodzik $";

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <ctype.h>
#include <math.h>
#include "isin.h"
#include "define.h"
#include "keyval.h"
#define mapx_c_
#include "mapx.h"
#include "maps.h"

static bool decode_mpp(mapx_class *this, char *label);
static bool old_fixed_format_decode_mpp(mapx_class *this, char *label);
static int forward_xy_mapx_check (int status, mapx_class *this,
				  double lat, double lon,
				  double *x, double *y);
static int inverse_xy_mapx_check (int status, mapx_class *this,
				  double x, double y,
				  double *lat, double *lon);
static double dist_latlon_map_units(mapx_class *this,
				    double lat, double lon,
				    double lat2, double lon2);
static double dist_xy_map_units(mapx_class *this,
				double x, double y,
				double x2, double y2);
static char *standard_name(char *);

/*::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 * projections 
 *
 *	To add a new projection the projection names should be added
 *	to the standard_name function, the standard name is added to
 *	the if-else-if construct in new_mapx and three private functions
 *	must be defined in a separate file and declared in the prototypes 
 *	section below.
 *
 *	The initialization function sets all pre-computed projection
 *	constants.
 *
 *	The forward function converts geographic to map coordinates.
 *
 *	input : lat,lon - geographic coords. (decimal degrees)
 *
 *	output: u,v - map coordinates (map units)
 *
 *	result: 0 = valid coordinates
 *		-1 = invalid point
 *
 *	The inverse function converts map to geographic coordinates.
 *
 *	input : u,v - map coordinates (map units)
 *
 *	output: lat,lon - geographic coords. (decimal degrees);
 *
 *	result: 0 = valid coordinates
 *		-1 = invalid point
 *
 *
 *::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::*/
int init_azimuthal_equal_area(void *);
int azimuthal_equal_area(void *, double, double, double *, double *);
int inverse_azimuthal_equal_area(void *, double, double, double *, double *);
int init_cylindrical_equidistant(void *);
int cylindrical_equidistant(void *, double, double, double *, double *);
int inverse_cylindrical_equidistant(void *,
				    double, double, double *, double *);
int init_cylindrical_equal_area(void *);
int cylindrical_equal_area(void *, double, double, double *, double *);
int inverse_cylindrical_equal_area(void *, double, double, double *, double *);
int init_mercator(void *);
int mercator(void *, double, double, double *, double *);
int inverse_mercator(void *, double, double, double *, double *);
int init_mollweide(void *);
int mollweide(void *, double, double, double *, double *);
int inverse_mollweide(void *, double, double, double *, double *);
int init_orthographic(void *);
int orthographic(void *, double, double, double *, double *);
int inverse_orthographic(void *, double, double, double *, double *);
int init_polar_stereographic(void *);
int polar_stereographic(void *, double, double, double *, double *);
int inverse_polar_stereographic(void *, double, double, double *, double *);
int init_polar_stereographic_ellipsoid(void *);
int polar_stereographic_ellipsoid(void *, double, double, double *, double *);
int inverse_polar_stereographic_ellipsoid(void *,
					  double, double, double *, double *);
int init_sinusoidal(void *);
int sinusoidal(void *, double, double, double *, double *);
int inverse_sinusoidal(void *, double, double, double *, double *);
int init_azimuthal_equal_area_ellipsoid(void *);
int azimuthal_equal_area_ellipsoid(void *, double, double, double *, double *);
int inverse_azimuthal_equal_area_ellipsoid(void *,
					   double, double, double *, double *);
int init_cylindrical_equal_area_ellipsoid(void *);
int cylindrical_equal_area_ellipsoid(void *,
				     double, double, double *, double *);
int inverse_cylindrical_equal_area_ellipsoid(void *,
					     double, double,
					     double *, double *);
int init_lambert_conic_conformal_ellipsoid(void *);
int lambert_conic_conformal_ellipsoid(void *,
				      double, double, double *, double *);
int inverse_lambert_conic_conformal_ellipsoid(void *,
					      double, double,
					      double *, double *);
int init_interupted_homolosine_equal_area(void *);
int interupted_homolosine_equal_area(void *,
				     double, double, double *, double *);
int inverse_interupted_homolosine_equal_area(void *,
					     double, double,
					     double *, double *);
int init_albers_conic_equal_area(void *);
int albers_conic_equal_area(void *, double, double, double *, double *);
int inverse_albers_conic_equal_area(void *,
				    double, double, double *, double *);
int init_albers_conic_equal_area_ellipsoid(void *);
int albers_conic_equal_area_ellipsoid(void *,
				      double, double, double *, double *);
int inverse_albers_conic_equal_area_ellipsoid(void *,
					      double, double,
					      double *, double *);
int init_integerized_sinusoidal(void *);
int integerized_sinusoidal(void *, double, double, double *, double *);
int inverse_integerized_sinusoidal(void *,
				   double, double, double *, double *);
int init_transverse_mercator(void *);
int transverse_mercator(void *,
			double, double, double *, double *);
int inverse_transverse_mercator(void *, double, double, double *, double *);
int init_transverse_mercator_ellipsoid(void *);
int transverse_mercator_ellipsoid(void *, double, double, double *, double *);
int inverse_transverse_mercator_ellipsoid(void *,
					  double, double, double *, double *);
int init_universal_transverse_mercator(void *);
/*
  uses transverse_mercator_ellipsoid
  uses inverse_transverse_mercator_ellipsoid
*/

const char *id_mapx(void)
{
  return mapx_c_rcsid;
}

/*----------------------------------------------------------------------
 * init_mapx - initialize map projection from file
 *
 *	input : filename - map parameters file name
 *			file must have following fields:
 *			 Map Projection: see below
 *			 Map Reference Latitude: lat0 (required except for UTM)
 *			 Map Reference Longitude: lon0 (required except for UTM)
 *			may also contain optional fields:
 *			 Map Second Reference Latitude: lat1
 *			 Map Second Reference Longitude: lon1
 *			 Map Rotation: counter-clockwise
 *			 Map Scale: scale (radius units per map unit)
 *                       Map ISin NZone: Number of latitudinal zones for ISin
 *			 Map ISin Justify: justify flag for ISin
 *			 Map Origin Latitude: center_lat
 *			 Map Origin Longitude: center_lon
 *                       Map Origin X: x0
 *                       Map Origin Y: y0
 *                       Map False Easting: false_easting
 *                       Map False Northing: false_northing
 *			 Map Southern Bound: southernmost lat
 *			 Map Northern Bound: northernmost lat
 *			 Map Western Bound: westernmost longitude
 *			 Map Eastern Bound: easternmost longitude
 *			 Map Graticule Latitude Interval: default 30
 *			 Map Graticule Longitude Interval: default 30
 *			 Map Graticule Label Latitude: default 0N
 *			 Map Graticule Label Longitude: default 0E
 *			 Map CIL Detail Level: default 1
 *			 Map BDY Detail Level: default 0
 *			 Map RIV Detail Level: default 0
 *			 Map Eccentricity: default Clark 1866
 *                       Map Eccentricity Squared: default Clark 1866
 *			 Map Equatorial Radius: default Clark 1866 for ellipsoid, authalic for sphere
 *                       Map Polar Radius: default Clark 1866
 *                       Map Center Scale: default 1.0
 *                       Map UTM Zone: default 0

 *			old fixed format was as follows:
 *			 Map_Projection_Name
 *			 lat0 lon0 [lat1 lon1] (decimal degrees)
 *			 rotation (portrait=0, landscape=90)
 *			 scale (kilometers per map unit)
 *			 center_lat center_lon (for map)
 *			 south north (decimal degrees)
 *			 west east (decimal degrees)
 *			 lat_interval lon_interval (for graticule)
 *			 label_lat label_lon (for graticule)
 *			 cil_detail bdy_detail riv_detail (see database_info)
 *	    [optional]   equatorial_radius (kilometers) 
 *	    [optional]	 eccentricity 
 *			                  
 *
 *			valid projection names are:
 *			 Azimuthal_Equal_Area
 *			 Cylindrical_Equal_Area
 *			 Mercator
 *			 Mollweide
 *			 Orthographic
 *			 Sinusoidal
 *			 Cylindrical_Equidistant
 *			 Polar_Stereographic
 *			 Polar_Stereographic_Ellipsoid
 *			 Azimuthal_Equal_Area_Ellipsoid			 
 *			 Cylindrical_Equal_Area_Ellipsoid
 *                       Lambert_Conic_Conformal_Ellipsoid
 *			 Interupted_Homolosine_Equal_Area
 *                       Albers_Conic_Equal_Area
 *                       Albers_Conic_Equal_Area_Ellipsoid
 *			 Integerized_Sinusoidal
 *                       Transverse_Mercator
 *                       Transverse_Mercator_Ellipsoid
 *                       Universal_Transverse_Mercator
 *			or anything reasonably similar
 *
 *	The parameter lat1 is currently used for the Polar_Stereographic
 *	projection to define the "true at" parallel (default pole) and
 *	the Cylindrical_Equal_Area projection to define the latitude of
 *	1:1 aspect ratio (default 30.00). In the Lambert Conic Conformal
 *	and Albers Conic Equal-Area lat0 and lat1 are the standard parallels.
 *
 *	result: pointer to new mapx_class instance for this map
 *		or NULL if an error occurs during initialization
 *
 *	note  : if unable to open .mpp file on first attempt then the
 *		value of the search path environment variable is prepended
 *		to the filename and a second attempt is made
 *
 *		Some important notes on specifying longitudes:
 *		All longitudes should be >= -180 and <= 360.
 *		West to east should not span more than 360 degrees.
 *		West specifies the left side of the map and east the right,
 *		not necessarily the minimum and maximum longitudes.
 *		For purposes of bounds checking all longitudes are 
 *		normalized -180 to 180.
 *
 *----------------------------------------------------------------------*/
mapx_class *init_mapx(char *filename)
{
  mapx_class *this=NULL;
  char *label=NULL, *mpp_filename=NULL;
  FILE *mpp_file=NULL;

  /*
   *	open .mpp file and read label
   */
  mpp_filename = (char *)malloc(FILENAME_MAX);
  if (!mpp_filename) { perror("init_mapx"); return NULL; }
  strncpy(mpp_filename, filename, FILENAME_MAX);

  mpp_file = search_path_fopen(mpp_filename, mapx_PATH, "r");
  if (mpp_file == NULL) {
    perror(filename);
    goto error_return;
  }
  label = get_label_keyval(mpp_filename, mpp_file, 0);
  if (NULL == label) goto error_return;

  /*
   *	initialize projection parameters
   */
  this = new_mapx(label, FALSE);
  if (NULL == this) goto error_return;
  free(label); label = NULL;

  /*
   *	fill in file and filename fields
   */
  this->mpp_filename = mpp_filename;
  this->mpp_file = mpp_file;

  return this;

error_return:
  fprintf(stderr,"init_mapx: error reading map projection parameters file\n");
  if (label) free(label);
  if (mpp_filename) free(mpp_filename);
  if (mpp_file) fclose(mpp_file);
  close_mapx(this);
  return NULL;

}
/*----------------------------------------------------------------------
 * new_mapx - initialize map projection from label
 *
 *	input : label - char buffer with initialization information
 *			see init_mapx for format
 *              quiet - if set, then don't complain about unknown
 *                      projection              
 *
 *	result: pointer to new mapx_class instance for this map
 *		or NULL if an error occurs during initialization
 *
 *----------------------------------------------------------------------*/
mapx_class *new_mapx (char *label, bool quiet)
{
  mapx_class *this;
  
  /*
   *	allocate storage for projection parameters
   */
  this = (mapx_class *)calloc(1, sizeof(mapx_class));
  if (!this) { perror("new_mapx"); return NULL; }
  
  /*
   *	decode map projection parameters
   */
  if (!decode_mpp(this, label)) { close_mapx(this); return NULL; }
  
  /*
   *	match projection name and initialize remaining parameters
   */
  if (strcmp (this->projection_name, "AZIMUTHALEQUALAREA") == 0)     
  { this->initialize = init_azimuthal_equal_area; 
    this->geo_to_map = azimuthal_equal_area;
    this->map_to_geo = inverse_azimuthal_equal_area;
  }
  else if (strcmp (this->projection_name, "CYLINDRICALEQUALAREA") == 0)
  { this->initialize = init_cylindrical_equal_area;
    this->geo_to_map = cylindrical_equal_area;
    this->map_to_geo = inverse_cylindrical_equal_area;
  }
  else if (strcmp (this->projection_name, "MERCATOR") == 0)
  { this->initialize = init_mercator;
    this->geo_to_map = mercator;
    this->map_to_geo = inverse_mercator;
  }
  else if (strcmp (this->projection_name, "MOLLWEIDE") == 0)
  { this->initialize = init_mollweide;
    this->geo_to_map = mollweide;
    this->map_to_geo = inverse_mollweide;
  }
  else if (strcmp (this->projection_name, "ORTHOGRAPHIC") == 0)
  { this->initialize = init_orthographic;
    this->geo_to_map = orthographic;
    this->map_to_geo = inverse_orthographic;
  }
  else if (strcmp (this->projection_name, "SINUSOIDAL") == 0)
  { this->initialize = init_sinusoidal;
    this->geo_to_map = sinusoidal;
    this->map_to_geo = inverse_sinusoidal;
  }
  else if (strcmp (this->projection_name, "CYLINDRICALEQUIDISTANT") == 0)
  { this->initialize = init_cylindrical_equidistant;
    this->geo_to_map = cylindrical_equidistant;
    this->map_to_geo = inverse_cylindrical_equidistant;
  }
  else if (strcmp (this->projection_name, "POLARSTEREOGRAPHIC") == 0)
  { this->initialize = init_polar_stereographic;
    this->geo_to_map = polar_stereographic;
    this->map_to_geo = inverse_polar_stereographic;
  }
  
  else if (strcmp (this->projection_name, "POLARSTEREOGRAPHICELLIPSOID") == 0)
  { this->initialize = init_polar_stereographic_ellipsoid;
    this->geo_to_map = polar_stereographic_ellipsoid;
    this->map_to_geo = inverse_polar_stereographic_ellipsoid;
  }
  
  else if (strcmp (this->projection_name, "AZIMUTHALEQUALAREAELLIPSOID") == 0) 
  { this->initialize = init_azimuthal_equal_area_ellipsoid;
    this->geo_to_map = azimuthal_equal_area_ellipsoid;
    this->map_to_geo = inverse_azimuthal_equal_area_ellipsoid;
  }
  
  else if (strcmp (this->projection_name, "CYLINDRICALEQUALAREAELLIPSOID") == 0) 
  { this->initialize = init_cylindrical_equal_area_ellipsoid;
    this->geo_to_map = cylindrical_equal_area_ellipsoid;
    this->map_to_geo = inverse_cylindrical_equal_area_ellipsoid;
  }
  
  else if (strcmp (this->projection_name, "LAMBERTCONICCONFORMALELLIPSOID") == 0) 
  { this->initialize =init_lambert_conic_conformal_ellipsoid;
    this->geo_to_map = lambert_conic_conformal_ellipsoid;
    this->map_to_geo = inverse_lambert_conic_conformal_ellipsoid;
  }
  else if (strcmp (this->projection_name, "INTERUPTEDHOMOLOSINEEQUALAREA") == 0) 
  { this->initialize =init_interupted_homolosine_equal_area;
    this->geo_to_map = interupted_homolosine_equal_area;
    this->map_to_geo = inverse_interupted_homolosine_equal_area;
  }
  else if (strcmp (this->projection_name, "ALBERSCONICEQUALAREA") == 0)     
  { this->initialize = init_albers_conic_equal_area; 
    this->geo_to_map = albers_conic_equal_area;
    this->map_to_geo = inverse_albers_conic_equal_area;
  }
  else if (strcmp (this->projection_name, "ALBERSCONICEQUALAREAELLIPSOID") == 0)     
  { this->initialize = init_albers_conic_equal_area_ellipsoid; 
    this->geo_to_map = albers_conic_equal_area_ellipsoid;
    this->map_to_geo = inverse_albers_conic_equal_area_ellipsoid;
  }
  else if (strcmp (this->projection_name, "INTEGERIZEDSINUSOIDAL") == 0)     
  { this->initialize = init_integerized_sinusoidal; 
    this->geo_to_map = integerized_sinusoidal;
    this->map_to_geo = inverse_integerized_sinusoidal;
  }
  else if (strcmp (this->projection_name, "TRANSVERSEMERCATOR") == 0)
    {
      this->initialize = init_transverse_mercator;
      this->geo_to_map = transverse_mercator;
      this->map_to_geo = inverse_transverse_mercator;
    }
  else if (strcmp (this->projection_name, "TRANSVERSEMERCATORELLIPSOID") == 0)
    {
      this->initialize = init_transverse_mercator_ellipsoid;
      this->geo_to_map = transverse_mercator_ellipsoid;
      this->map_to_geo = inverse_transverse_mercator_ellipsoid;
    }
  else if (strcmp (this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") == 0)
    {
      this->initialize = init_universal_transverse_mercator;
      /*
      this->geo_to_map = universal_transverse_mercator;
      this->map_to_geo = inverse_universal_transverse_mercator;
      */
      this->geo_to_map = transverse_mercator_ellipsoid;
      this->map_to_geo = inverse_transverse_mercator_ellipsoid;
    }
  else
    {
      if (!quiet) {
	fprintf (stderr, "mapx: unknown projection %s\n",
		 this->projection_name);
	fprintf (stderr, "valid types are:\n");
	fprintf (stderr, " Albers Conic Equal-Area\n");
	fprintf (stderr, " Albers Conic Equal-Area Ellipsoid\n");
	fprintf (stderr, " Azimuthal Equal-Area\n");
	fprintf (stderr, " Azimuthal Equal-Area Ellipsoid\n");
	fprintf (stderr, " Cylindrical Equal-Area\n");
	fprintf (stderr, " Cylindrical Equal-Area Ellipsoid\n");
	fprintf (stderr, " Cylindrical Equidistant\n");
	fprintf (stderr, " Integerized Sinusoidal\n");
	fprintf (stderr, " Interupted Homolosine Equal-Area\n");
	fprintf (stderr, " Lambert Conic Conformal Ellipsoid\n");
	fprintf (stderr, " Mercator\n");
	fprintf (stderr, " Mollweide\n");
	fprintf (stderr, " Orthographic\n");
	fprintf (stderr, " Polar Stereographic\n");
	fprintf (stderr, " Polar Stereographic Ellipsoid\n");
	fprintf (stderr, " Sinusoidal\n");
	fprintf (stderr, " Transverse Mercator\n");
	fprintf (stderr, " Transverse Mercator Ellipsoid\n");
	fprintf (stderr, " Universal Transverse Mercator\n");
      }
    close_mapx (this);
    return NULL;
  }
  
  /*
   *	initialize map projection constants
   */
  if (0 != reinit_mapx(this))
  { close_mapx(this);
    return NULL;
  }
  
  return this;
}


/*------------------------------------------------------------------------
 * decode_mpp - parse information in map projection parameters label
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		label - map projection parameters label
 *
 *	result: TRUE iff success
 *
 *	effect: fills map data structure with values read from label
 *
 *------------------------------------------------------------------------*/
static bool decode_mpp(mapx_class *this, char *label)
{
  bool success;
  char *projection_name=NULL;
  char *default_value;

  /*
   *	if Map Projection tag present then interpret as new keyval format
   *  	otherwise try for old fixed format
   */
  projection_name = get_field_keyval(label, "Map Projection", keyval_FALL_THRU_STRING);

  if (streq(projection_name, keyval_FALL_THRU_STRING)) {
    if (mapx_verbose) fprintf(stderr,"> assuming old style fixed format file\n");
    return old_fixed_format_decode_mpp(this, label);
  }

  this->projection_name = strdup(standard_name(projection_name));
  free(projection_name); projection_name = NULL;

  /*
   *	get "required" fields.
   *    Map Reference Latitude and Longitude are required fields if and
   *    only if the projection is not Universal Transverse Mercator
   *    nor Integerized Sinusoidal.
   */
  if (streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR"))
    default_value = "999";
  else if (streq(this->projection_name, "INTEGERIZEDSINUSOIDAL"))
    default_value = "0.0";
  else
    default_value = NULL;

  success = get_value_keyval(label, "Map Reference Latitude",
			     "%lat", &(this->lat0), default_value);
  if (!success) {
    fprintf(stderr,"mapx: Map Reference Latitude is a required field\n");
    goto error_return;
  }
	  
  success = get_value_keyval(label, "Map Reference Longitude",
			     "%lon", &(this->lon0), default_value);
  if (!success) {
    fprintf(stderr,"mapx: Map Reference Longitude is a required field\n");
    goto error_return;
  }

  /*
   *	get optional fields
   */
  get_value_keyval(label, "Map Second Reference Latitude", "%lat", &(this->lat1), "999");
  get_value_keyval(label, "Map Second Reference Longitude", "%lon", &(this->lon1), "999");

  get_value_keyval(label, "Map Rotation", "%lf", &(this->rotation), "0.0");
  get_value_keyval(label, "Map Scale", "%lf", &(this->scale), "1.0");

  get_value_keyval(label, "Map ISin NZone", "%d", &(this->isin_nzone), "86400");
  get_value_keyval(label, "Map ISin Justify", "%d", &(this->isin_justify), "1");

  get_value_keyval(label, "Map Origin X", "%lf", &(this->x0),
		   "KEYVAL_UNINITIALIZED");
  get_value_keyval(label, "Map Origin Y", "%lf", &(this->y0),
		   "KEYVAL_UNINITIALIZED");
  if (this->x0 == KEYVAL_UNINITIALIZED && this->y0 != KEYVAL_UNINITIALIZED) {
    fprintf(stderr,
	    "mapx: Map Origin X must be specified if Map Origin Y is specified\n");
    goto error_return;
  }    
  if (this->x0 != KEYVAL_UNINITIALIZED && this->y0 == KEYVAL_UNINITIALIZED) {
    fprintf(stderr,
	    "mapx: Map Origin Y must be specified if Map Origin X is specified\n");
    goto error_return;
  }

  /*
   *  defer assuming that Map Origin Latitude and Longitude
   *  take on Reference Latitude and Longitude values,
   *  respectively, when the former are not defined and the
   *  projection is UTM until UTM initialization.
   */

  get_value_keyval(label, "Map Origin Latitude", "%lat", &(this->center_lat), "999");
  if (999 == this->center_lat &&
      !streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") &&
      KEYVAL_UNINITIALIZED == this->x0) {
    if (mapx_verbose) fprintf(stderr,"> assuming map origin lat is same as ref. lat %lf\n", this->lat0);
    this->center_lat = this->lat0;
  }
  get_value_keyval(label, "Map Origin Longitude", "%lon", &(this->center_lon), "999");
  if (999 == this->center_lon &&
      !streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") &&
      KEYVAL_UNINITIALIZED == this->x0) {
    if (mapx_verbose) fprintf(stderr,"> assuming map origin lon is same as ref. lon %lf\n", this->lon0);
    this->center_lon = this->lon0;
  }

  /*
   *  defer assigning of default values to Map False Easting and
   *  Northing keywords when they are not defined and the
   *  projection is UTM until UTM initialization.
   */

  default_value =
    streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") ?
    "KEYVAL_UNINITIALIZED" : "0.0";
  get_value_keyval(label, "Map False Easting", "%lf", &(this->false_easting),
		   default_value);
  get_value_keyval(label, "Map False Northing", "%lf", &(this->false_northing),
		   default_value);

  get_value_keyval(label, "Map Southern Bound", "%lat", &(this->south), "90S");
  get_value_keyval(label, "Map Northern Bound", "%lat", &(this->north), "90N");
  get_value_keyval(label, "Map Western Bound", "%lon", &(this->west), "180W");
  get_value_keyval(label, "Map Eastern Bound", "%lon", &(this->east), "180E");

  get_value_keyval(label, "Map Graticule Latitude Interval", "%lf",
		   &(this->lat_interval), "30.");
  get_value_keyval(label, "Map Graticule Longitude Interval", "%lf",
		   &(this->lon_interval), "30.");
  get_value_keyval(label, "Map Graticule Label Latitude", "%lat",
		   &(this->label_lat), "0.0");
  get_value_keyval(label, "Map Graticule Label Longitude", "%lon",
		   &(this->label_lon), "0.0");

  get_value_keyval(label, "Map CIL Detail Level", "%d", &(this->cil_detail), "1");
  get_value_keyval(label, "Map BDY Detail Level", "%d", &(this->bdy_detail), "0");
  get_value_keyval(label, "Map RIV Detail Level", "%d", &(this->riv_detail), "0");

  get_value_keyval(label, "Map Equatorial Radius", "%lf", &(this->equatorial_radius), "0.0");
  get_value_keyval(label, "Map Polar Radius", "%lf", &(this->polar_radius), "0.0");
  get_value_keyval(label, "Map Eccentricity", "%lf", &(this->eccentricity), "999");
  get_value_keyval(label, "Map Eccentricity Squared", "%lf", &(this->e2), "999");

  /*
   *  default value for Map Center Scale is 0.9996 for UTM;
   *  otherwise it's 1.0
   */

  default_value =
    streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") ?
    "0.9996" : "1.0";
  get_value_keyval(label, "Map Center Scale", "%lf", &(this->center_scale),
		   default_value);

  /*
   *  default value for Map Maximum Error is 100.0 for UTM;
   *  otherwise it's 0.0
   */

  default_value =
    streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") ?
    "100.0" : "0.0";
  get_value_keyval(label, "Map Maximum Error", "%lf", &(this->maximum_error),
		   default_value);

  get_value_keyval(label, "Map UTM Zone", "%d", &(this->utm_zone), "0");

  /*
   *  If we have eccentricity squared but not eccentricity,
   *  then derive eccentricity from eccentricity squared
   */
  if (999 != this->e2 && 999 == this->eccentricity)
    this->eccentricity = sqrt(this->e2);

  /*  If we have equatorial radius and polar radius, but not eccentricity,
   *  then derive eccentricity from equatorial radius and polar radius
   */
  if (0.0 != this->equatorial_radius && 0.0 != this->polar_radius &&
      999 == this->eccentricity)
    this->eccentricity =
      sqrt(1.0 - ((this->polar_radius * this->polar_radius) /
		  (this->equatorial_radius * this->equatorial_radius)));

  /*  If we have polar radius and eccentricity but not equatorial radius,
   *  then derive equatorial radius from polar radius and eccentricity
   */
  if (0.0 != this->polar_radius && 999 != this->eccentricity &&
      0.0 == this->equatorial_radius)
    this->equatorial_radius =
      this->polar_radius / sqrt(1.0 - this->eccentricity * this->eccentricity);

  /*
   *	try to make educated guess at defaults
   *    for map eccentricity and equatorial radius
   */
  if (streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR")) {
    if (999 == this->eccentricity) {
      this->eccentricity = mapx_eccentricity_wgs84;
      if (mapx_verbose)
	fprintf(stderr,"> using default eccentricity %lf\n",
		this->eccentricity);
    }
    if (0.0 == this->equatorial_radius) {
      this->equatorial_radius = mapx_equatorial_radius_wgs84_m;
      if (mapx_verbose)
	fprintf(stderr,"> using default equatorial radius %lfm\n",
		this->equatorial_radius);
    }
  } else if (streq(this->projection_name, "INTEGERIZEDSINUSOIDAL")) {
    if (0.0 == this->equatorial_radius) {
      this->equatorial_radius = mapx_equatorial_radius_isin_m;
      if (mapx_verbose)
	fprintf(stderr,"> using default equatorial radius %lfm\n",
		this->equatorial_radius);
    }
    this->eccentricity = 0.0;
  }
  else if (strstr(this->projection_name, "ELLIPSOID")) {
    if (999 == this->eccentricity) {
      this->eccentricity = mapx_eccentricity;
      if (mapx_verbose)
	fprintf(stderr,"> using default eccentricity %lf\n",
		this->eccentricity);
    }
    if (0.0 == this->equatorial_radius) {
      this->equatorial_radius = mapx_equatorial_radius_km;
      if (mapx_verbose)
	fprintf(stderr,"> using default equatorial radius %lfkm\n",
		this->equatorial_radius);
    }
  } else {
    if (0.0 == this->equatorial_radius) {
      this->equatorial_radius = mapx_Re_km;
      if (mapx_verbose)
	fprintf(stderr,"> using default equatorial radius %lfkm\n",
		this->equatorial_radius);
    }
    if (999 == this->eccentricity) {
      this->eccentricity = 0.0;
    }
    if (0 == this->polar_radius) {
      this->polar_radius = this->equatorial_radius;
    }
    if (0 != this->eccentricity ||
	this->polar_radius != this->equatorial_radius) {
      fprintf(stderr,"mapx: eccentricity specified or\n"\
	      "      polar radius not equal to equatorial radius specified\n"\
	      "      with spherical map projection;\n"\
	      "      use Ellipsoid version of projection name\n");
      goto error_return;
    }
  }

  return TRUE;

error_return:
  if (projection_name) free(projection_name);
  return FALSE;

}

/*------------------------------------------------------------------------
 * old_fixed_format_decode_mpp
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		label - contents of map projection parameters file
 *
 *	result: TRUE iff success
 *
 *	effect: fills map data structure with values read from label
 *
 *------------------------------------------------------------------------*/
static bool old_fixed_format_decode_mpp(mapx_class *this, char *label)
{
  double f1, f2, f3, f4;
  int i1, i2, i3, ios;
  char projection[MAX_STRING], readln[MAX_STRING], original_name[MAX_STRING];
  double default_value;
  double default_eccentricity, default_equatorial_radius;

  /*
   *	get projection parameters
   */
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  strcpy(original_name, readln);
  strcpy(projection, standard_name(original_name));
  this->projection_name = strdup(projection);

  /*
   *    set default values for equatorial radius and eccentricity
   *    based on the map projection
   */
  if (streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR")) {
    default_equatorial_radius = mapx_equatorial_radius_wgs84_m;
    default_eccentricity = mapx_eccentricity_wgs84;
  } else if (streq(this->projection_name, "INTEGERIZEDSINUSOIDAL")) {
    default_equatorial_radius = mapx_equatorial_radius_isin_m;
    default_eccentricity = 0.0;
  } else if (strstr(this->projection_name, "ELLIPSOID")) {
    default_equatorial_radius = mapx_Re_km;
    default_eccentricity = mapx_eccentricity;
  } else {
    default_equatorial_radius = mapx_Re_km;
    default_eccentricity = 0.0;
  }

  /*
   *    set unsupported parameters to default values
   */
  this->x0 = KEYVAL_UNINITIALIZED;
  this->y0 = KEYVAL_UNINITIALIZED;
  default_value =
    streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") ?
    KEYVAL_UNINITIALIZED : 0.0;
  this->false_easting = default_value;
  this->false_northing = default_value;
  default_value =
    streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") ?
    0.9996 : 1.0;
  this->center_scale = default_value;
  default_value =
    streq(this->projection_name, "UNIVERSALTRANSVERSEMERCATOR") ?
    100.0 : 0.0;
  this->maximum_error = default_value;
  this->utm_zone = 0;
  this->isin_nzone = 86400;
  this->isin_justify = 1;
  this->e2 = 999;
  this->polar_radius = 0.0;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf %lf %lf %lf", &f1, &f2, &f3, &f4);
  this->lat0 = (ios >= 1) ? f1 : 0.0;
  this->lon0 = (ios >= 2) ? f2 : 0.0;
  this->lat1 = (ios >= 3) ? f3 : 999;
  this->lon1 = (ios >= 4) ? f4 : 999;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf", &f1);
  this->rotation = (ios >= 1) ? f1 : 0.0;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf", &f1);
  this->scale = (ios >= 1) ? f1 : 1.0;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf %lf", &f1, &f2);
  this->center_lat = (ios >= 1) ? f1 : 0.0;
  this->center_lon = (ios >= 2) ? f2 : 0.0;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf %lf", &f1, &f2);
  this->south = (ios >= 1) ? f1 : -90.;
  this->north = (ios >= 2) ? f2 :  90.;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf %lf", &f1, &f2);
  this->west = (ios >= 1) ? f1 : -180.;
  this->east = (ios >= 2) ? f2 :  180.;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf %lf", &f1, &f2);
  this->lat_interval = (ios >= 1) ? f1 : 30.;
  this->lon_interval = (ios >= 2) ? f2 : 30.;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%lf %lf", &f1, &f2);
  this->label_lat = (ios >= 1) ? f1 : 0.0;
  this->label_lon = (ios >= 2) ? f2 : 0.0;
  
  if ((label = next_line_from_buffer(label, readln)) == NULL) goto error_return;
  ios = sscanf (readln, "%d %d %d", &i1, &i2, &i3);
  this->cil_detail = (ios >= 1) ? i1 : 1;
  this->bdy_detail = (ios >= 2) ? i2 : 0;
  this->riv_detail = (ios >= 3) ? i3 : 0;

  /*
   *	look for optional parameters
   */
  label = next_line_from_buffer(label, readln);
  if (NULL == label) 
  { this->equatorial_radius = default_equatorial_radius;
    this->eccentricity = default_eccentricity;
  }
  else
  { ios = sscanf (readln, "%lf", &f1);           
    this->equatorial_radius = (ios >= 1) ? f1 : default_equatorial_radius;
    
    label = next_line_from_buffer(label, readln);
    if (NULL == label)
      this->eccentricity = default_eccentricity;
    else
    { ios = sscanf (readln, "%lf", &f1);            
      this->eccentricity = (ios >= 1) ? f1 : default_eccentricity;
    }
    if (0 != this->eccentricity && 0 == default_eccentricity) {
      fprintf(stderr, "mapx: eccentricity specified\n"\
              "       with spherical map projection;\n"\
	      "       use Ellipsoid version of projection name\n");
      label = NULL;
      goto error_return;
    }
  }
  return TRUE;
  
  /*
   *	check for errors when reading
   */
error_return:
  if (mapx_verbose && label && strlen(label) <= MAX_STRING) fprintf(stderr,"> bad label: %s\n", label);
  return FALSE;

}
/*------------------------------------------------------------------------
 * next_line_from_buffer
 *
 *	input : bufptr - pointer to current line in buffer
 *		readln - pointer to space to copy current line into
 *
 *	result: pointer to next line in buffer or NULL if buffer is empty
 *
 *      NOTE: Ignore lines beginning with # or ;
 *
 *------------------------------------------------------------------------*/
char *next_line_from_buffer(char *bufptr, char *readln)
{
  char *next_line;
  int line_length;
  bool got_comment;

  if (NULL == bufptr) return NULL;

  /*
   *  Keep looping until we don't get a comment or
   *  we reach the end of the buffer
   */
  do {

    /*
     *	get length of field and pointer to next line
     */
    line_length = strcspn(bufptr, "\n");
    if (0 != line_length) {
      next_line = bufptr + line_length + 1;
    } else {
      line_length = strlen(bufptr);
      if (0 == line_length) return NULL;
      next_line = bufptr + line_length;
    }

    /*
     *	copy value field to new buffer
     */
    strncpy(readln, bufptr, line_length);
    readln[line_length] = '\0';
    got_comment = (*bufptr == '#' || *bufptr == ';') ? TRUE : FALSE;
    bufptr = next_line;
  } while (got_comment);

  return next_line;
}

/*------------------------------------------------------------------------
 * close_mapx - free resources associated with active mapx struct
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *
 *------------------------------------------------------------------------*/
void close_mapx (mapx_class *this)
{
  if (this == NULL) return;
  if (this->projection_name != NULL) free(this->projection_name);
  if (this->mpp_file != NULL) fclose(this->mpp_file);
  if (this->mpp_filename != NULL) free(this->mpp_filename);
  if (this->isin_data != NULL) Isin_for_free(this->isin_data);
  free (this);
}

/*------------------------------------------------------------------------
 * reinit_mapx - re-initialize map projection constants
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *
 *		The client may set user specified constants in the 
 *		mapx_class struct and this routine will re-calculate
 *		the appropriate private constants for the projection
 *
 *	result: 0 = success, -1 = error return
 *
 *------------------------------------------------------------------------*/
int reinit_mapx (mapx_class *this)
{ double theta;
  
  /*
   *	check map bounds
   */
  if (this->east < -180 || this->east > 360 
      || this->west < -180 || this->west > 360)
  { fprintf(stderr,"mapx: illegal bounds: west=%lf, east=%lf\n",
	    this->west, this->east);
    fprintf(stderr,"           should be >= -180 and <= 360\n");
    return -1;
  }
  
  if (fabs(this->east - this->west) > 360)
  { fprintf(stderr,"mapx: illegal bounds: west=%lf, east=%lf\n",
	    this->west, this->east);
    fprintf(stderr,"           bounds cannot span > 360 degrees.\n");
    return -1;
  }
  
  if (this->east > 180 && this->west > 180)
  { this->east -=360;
    this->west -=360;
  }
  
  /*
   *	set flag for bounds checking
   */
  if (this->east < this->west || this->east > 180)
    this->map_stradles_180 = TRUE;
  else
    this->map_stradles_180 = FALSE;
  
  NORMALIZE(this->east);
  NORMALIZE(this->west);
  
  /*
   *	set series expansion constants
   */
  this->e2 = (this->eccentricity) * (this->eccentricity);
  this->e4 = (this->e2) * (this->e2);
  this->e6 = (this->e4) * (this->e2); 
  this->e8 = (this->e4) * (this->e4);

  /*
   *    set the polar radius
   */
  this->polar_radius = this->equatorial_radius * sqrt(1.0 - this->e2);

  /*
   *    set the flattening
   */
  this->f = 1.0 - this->polar_radius / this->equatorial_radius;

  /*
   *	set scaled radius for spherical projections
   */
  this->Rg = this->equatorial_radius / this->scale;
  
  /*
   *	set projection constants
   */
  if ((*(this->initialize))(this)) return -1;

  /*
   *	create rotation matrix
   */
  theta = RADIANS(this->rotation);
  
  this->T00 =  cos(theta);
  this->T01 =  sin(theta);
  this->T10 = -sin(theta);
  this->T11 =  cos(theta);

  if (KEYVAL_UNINITIALIZED == this->x0) {

    /*
     *  convert center_lat and center_lon to x0 and y0
     */

    forward_xy_mapx(this, this->center_lat, this->center_lon,
		    &(this->x0), &(this->y0));
  }

  /*
   *  rotate x0, y0 into u0, v0.
   *  x0, y0 will be the center of the rotation.
   */

  this->u0 = this->T00 * this->x0 + this->T01 * this->y0;
  this->v0 = this->T10 * this->x0 + this->T11 * this->y0;
  
  return 0;
}

/*------------------------------------------------------------------------
 * within_mapx - test if lat,lon are within map transformation bounds
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		lat,lon - geographic coordinates in decimal degrees
 *
 *	result: TRUE iff lat,lon are within specified mapx min,max
 *
 *------------------------------------------------------------------------*/
int within_mapx (mapx_class *this, double lat, double lon)
{
  if (lat < this->south || lat > this->north) return FALSE;
  
  NORMALIZE(lon);
  
  if (this->map_stradles_180)
  { if (lon > this->east && lon < this->west)
      return FALSE;
  }
  else
  { if (lon < this->west || lon > this->east)
      return FALSE;
  }
  
  return TRUE;
}

/*------------------------------------------------------------------------
 * forward_mapx - forward map transformation
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		lat,lon - geographic coordinates in decimal degrees
 *
 *	output: u,v - rotated and translated map coordinates in map units
 *
 *------------------------------------------------------------------------*/
int forward_mapx (mapx_class *this, double lat, double lon, double *u, double *v)
{
  int status, errno_sav;
  double x, y;

  errno = 0;
  status = (*(this->geo_to_map))(this, lat, lon, &x, &y);
  errno_sav = errno;
  status = forward_xy_mapx_check(status, this, lat, lon, &x, &y);
  *u = this->T00 * x + this->T01 * y - this->u0;
  *v = this->T10 * x + this->T11 * y - this->v0;
  if (errno_sav != 0) 
    return -1; 
  else
    return status;
}

/*------------------------------------------------------------------------
 * inverse_mapx - inverse map transformation
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		u,v - rotated and translated map coordinates in map units
 *
 *	output: lat,lon - geographic coordinates in decimal degrees
 *
 *------------------------------------------------------------------------*/
int inverse_mapx (mapx_class *this, double u, double v, double *lat, double *lon)
{
  int status, errno_sav;
  double x, y;

  u += this->u0;
  v += this->v0;
  x =  this->T00 * u - this->T01 * v;
  y = -this->T10 * u + this->T11 * v;
  errno = 0;
  status = (*(this->map_to_geo))(this, x, y, lat, lon);
  errno_sav = errno;
  status = inverse_xy_mapx_check(status, this, x, y, lat, lon);
  if (errno_sav != 0) 
    return -1; 
  else
    return status;
}

/*------------------------------------------------------------------------
 * forward_xy_mapx - forward map transformation
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		lat,lon - geographic coordinates in decimal degrees
 *
 *	output: x,y - original map coordinates in map units
 *
 *------------------------------------------------------------------------*/
int forward_xy_mapx (mapx_class *this, double lat, double lon,
		     double *x, double *y)
{
  int status, errno_sav;

  errno = 0;
  status = (*(this->geo_to_map))(this, lat, lon, x, y);
  errno_sav = errno;
  status = forward_xy_mapx_check(status, this, lat, lon, x, y);
  if (errno_sav != 0) 
    return -1; 
  else
    return status;
}

/*------------------------------------------------------------------------
 * inverse_xy_mapx - inverse map transformation
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		x,y - original map coordinates in map units
 *
 *	output: lat,lon - geographic coordinates in decimal degrees
 *
 *------------------------------------------------------------------------*/
int inverse_xy_mapx (mapx_class *this, double x, double y,
		     double *lat, double *lon)
{
  int status, errno_sav;

  errno = 0;
  status = (*(this->map_to_geo))(this, x, y, lat, lon);
  errno_sav = errno;
  status = inverse_xy_mapx_check(status, this, x, y, lat, lon);
  if (errno_sav != 0) 
    return -1; 
  else
    return status;
}

/*------------------------------------------------------------------------
 * forward_xy_mapx_check - forward map transformation error check
 *
 *	input : status - status returned by geo_to_map
 *              this - pointer to map data structure (returned by new_mapx)
 *		lat,lon - geographic coordinates in decimal degrees
 *              x,y - original map coordinates in map units returned by
 *                    geo_to_map
 *
 *      output: x,y - unchanged if returned status is 0;
 *                    set to NAN otherwise
 *
 *      return: status - 0 if ok; -1 otherwise
 *
 *------------------------------------------------------------------------*/
static int forward_xy_mapx_check (int status, mapx_class *this,
				     double lat, double lon,
				     double *x, double *y)
{
  double lat2, lon2, dist;

  if (this->maximum_error != 0.0 && errno == 0 && status == 0) {
    status = (*(this->map_to_geo))(this, *x, *y, &lat2, &lon2);
    dist = dist_latlon_map_units(this, lat, lon, lat2, lon2);
    if (errno != 0) 
      status = -1;
    if (status != 0 || !finite(dist) || dist > this->maximum_error) {
      *x = NAN;
      *y = NAN;
      status = -1;
    }
  }
  return status;
}

/*------------------------------------------------------------------------
 * inverse_xy_mapx_check - inverse map transformation error check
 *
 *	input : status - status returned by map_to_geo
 *              this - pointer to map data structure (returned by new_mapx)
 *		x,y - original map coordinates in map units
 *              lat,lon - geographic coordinates in decimal degrees
 *                        returned by map_to_geo
 *
 *	output: lat,lon - unchanged if returned status is 0;
 *                        set to NAN otherwise
 *
 *      return: status - 0 if ok; -1 otherwise
 *
 *------------------------------------------------------------------------*/
static int inverse_xy_mapx_check (int status, mapx_class *this,
				  double x, double y,
				  double *lat, double *lon)
{
  double x2, y2, dist;

  if (this->maximum_error != 0.0 && errno == 0 && status == 0) {
    status = (*(this->geo_to_map))(this, *lat, *lon, &x2, &y2);
    dist = dist_xy_map_units(this, x, y, x2, y2);
    if (errno != 0) 
      status = -1;
    if (status != 0 || !finite(dist) || dist > this->maximum_error) {
      *lat = NAN;
      *lon = NAN;
      status = -1;
    }
  }
  return status;
}

/*------------------------------------------------------------------------
 * dist_latlon_map_units - return distance between two lat-lon pairs
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		lat1,lon1 - geographic coordinates in decimal degrees
 *		lat2,lon2 - geographic coordinates in decimal degrees
 *
 *      output: none
 *
 *      return: distance on ellipsoid surface between lat-lon pairs
 *              measured in map units
 *
 *      reference: Astronomical Algorithms, Jean Meeus, 1991,
 *                 Willmann-Bell, Inc., pp. 77-82
 *
 *------------------------------------------------------------------------*/
static double dist_latlon_map_units(mapx_class *this,
				    double lat1, double lon1,
				    double lat2, double lon2)
{
  double F, G, lambda;
  double S, C, omega;
  double R, D, H1, H2;
  double sinsqF, cossqF, sinsqG, cossqG, sinsqlambda, cossqlambda;
  double eps = 1e-12;
  double s = 0.0;

  F = RADIANS(lat1 + lat2) / 2;
  G = RADIANS(lat1 - lat2) / 2;
  lambda = RADIANS(lon1 - lon2) / 2;

  sinsqF = sin(F);
  sinsqF = sinsqF * sinsqF;
  cossqF = 1.0 - sinsqF;

  sinsqG = sin(G);
  sinsqG = sinsqG * sinsqG;
  cossqG = 1.0 - sinsqG;

  sinsqlambda = sin(lambda);
  sinsqlambda = sinsqlambda * sinsqlambda;
  cossqlambda = 1.0 - sinsqlambda;

  S = sinsqG * cossqlambda + cossqF * sinsqlambda;
  C = cossqG * cossqlambda + sinsqF * sinsqlambda;


  omega = atan(sqrt(S / C));
  if (fabs(omega) > eps) {
    R = sqrt(S * C) / omega;
    D = 2 * omega * this->Rg;
    if (this->f != 0) {
      H1 = (3 * R - 1) / (2 * C);
      H2 = (3 * R + 1) / (2 * S);
      s = D * (1 + this->f * H1 * sinsqF * cossqG -
	       this->f * H2 * cossqF * sinsqG);
    } else {
      s = D;
    }
  }
  return(s);
}

/*------------------------------------------------------------------------
 * dist_xy_map_units - return distance between two x-y pairs
 *
 *	input : this - pointer to map data structure (returned by new_mapx)
 *		x1,y1 - map coordinates in map units
 *		x2,y2 - map coordinates in map units
 *
 *      output: none
 *
 *      return: distance on projected surface between x-y pairs
 *              measured in map units
 *
 *      reference: Astronomical Algorithms, Jean Meeus, 1991,
 *                 Willmann-Bell, Inc., pp. 77-82
 *
 *------------------------------------------------------------------------*/
static double dist_xy_map_units(mapx_class *this,
				double x1, double y1,
				double x2, double y2)
{
  double xdiff, ydiff;

  xdiff = x1 - x2;
  ydiff = y1 - y2;

  return(sqrt(xdiff * xdiff + ydiff * ydiff));
}

/*--------------------------------------------------------------------------
 * standard_name - standardize projection name
 *
 *	input : original_name - original projection name string
 *
 *	result: a valid projection name or ""
 *
 *-------------------------------------------------------------------------*/
static char *standard_name(char *original_name)
{
  static char new_name[80];
  char *p = new_name, *s;
  
  for(s = original_name; *s != '\n' && *s != '\0'; ++s)
  {
    if ((*s == '_') || (*s == ' ') || (*s == '-') 
	|| (*s == '(') || (*s == ')'))
      ;
    else 
      *p++ = toupper(*s);
  }
  
  *p = '\0';
  
  if (streq(new_name, "AZIMUTHALEQUALAREA") || 
      streq(new_name, "AZIMUTHALEQUALAREASPHERE") || 
      streq(new_name, "EQUALAREAAZIMUTHALSPHERE") || 
      streq(new_name, "SPHEREAZIMUTHALEQUALAREA") || 
      streq(new_name, "SPHEREEQUALAREAAZIMUTHAL") || 
      streq(new_name, "EQUALAREAAZIMUTHAL"))
  { strcpy(new_name,"AZIMUTHALEQUALAREA");
  }
  else if (streq(new_name, "EQUALAREACYLINDRICAL") || 
	   streq(new_name, "CYLINDRICALEQUALAREA") ) 
  { strcpy(new_name,"CYLINDRICALEQUALAREA");
  }
  else if (streq(new_name, "CYLINDRICALEQUIDISTANT") || 
	   streq(new_name, "EQUIDISTANTCYLINDRICAL"))
  { strcpy(new_name, "CYLINDRICALEQUIDISTANT");
  }
  else if (streq(new_name, "POLARSTEREOGRAPHIC") || 
	   streq(new_name, "STEREOGRAPHICPOLAR"))
  { strcpy(new_name, "POLARSTEREOGRAPHIC");
  }
  else if (streq(new_name, "POLARSTEREOGRAPHICELLIPSOID") || 
	   streq(new_name, "ELLIPSOIDPOLARSTEREOGRAPHIC") ||
	   streq(new_name, "STEREOGRAPHICPOLARELLIPSOID") ||
	   streq(new_name, "ELLIPSOIDSTEREOGRAPHICPOLAR"))
  { strcpy(new_name, "POLARSTEREOGRAPHICELLIPSOID");
  }
  else if (streq(new_name, "AZIMUTHALEQUALAREAELLIPSOID") || 
	   streq(new_name, "ELLIPSOIDAZIMUTHALEQUALAREA") || 
	   streq(new_name, "EQUALAREAAZIMUTHALELLIPSOID") || 
	   streq(new_name, "ELLIPSOIDEQUALAREAAZIMUTHAL"))
  { strcpy(new_name, "AZIMUTHALEQUALAREAELLIPSOID");
  }
  else if (streq(new_name, "CYLINDRICALEQUALAREAELLIPSOID") || 
	   streq(new_name, "ELLIPSOIDCYLINDRICALEQUALAREA") || 
	   streq(new_name, "EQUALAREACYLINDRICALELLIPSOID") || 
	   streq(new_name, "ELLIPSOIDEQUALAREACYLINDRICAL") )
  { strcpy(new_name,  "CYLINDRICALEQUALAREAELLIPSOID");
  }
  else if (streq(new_name, "LAMBERTCONICCONFORMALELLIPSOID") ||
	   streq(new_name, "LAMBERTCONFORMALCONICELLIPSOID") ||
	   streq(new_name, "ELLIPSOIDLAMBERTCONICCONFORMAL") ||
	   streq(new_name, "ELLIPSOIDLAMBERTCONFORMALCONIC"))
  { strcpy(new_name, "LAMBERTCONICCONFORMALELLIPSOID");
  }
  else if (streq(new_name, "INTERUPTEDHOMOLOSINEEQUALAREA") ||
	   streq(new_name, "GOODESINTERUPTEDHOMOLOSINE") ||
	   streq(new_name, "GOODEHOMOLOSINEEQUALAREA") ||
	   streq(new_name, "GOODESHOMOLOSINEEQUALAREA") ||
	   streq(new_name, "INTERUPTEDHOMOLOSINE") ||
	   streq(new_name, "GOODEINTERRUPTEDHOMOLOSINE") ||
	   streq(new_name, "INTERRUPTEDHOMOLOSINEEQUALAREA") ||
	   streq(new_name, "GOODESINTERRUPTEDHOMOLOSINE") ||
	   streq(new_name, "INTERRUPTEDHOMOLOSINE") ||
	   streq(new_name, "GOODEINTERRUPTEDHOMOLOSINE") ||
streq(new_name, "GOODEHOMOLOSINE") ||
	   streq(new_name, "GOODESHOMOLOSINE"))
  { strcpy(new_name, "INTERUPTEDHOMOLOSINEEQUALAREA");
  }
  else if (streq(new_name, "ALBERSCONICEQUALAREA") || 
      streq(new_name, "ALBERSCONICEQUALAREASPHERE") || 
      streq(new_name, "ALBERSEQUALAREACONIC") || 
      streq(new_name, "CONICEQUALAREA") || 
      streq(new_name, "EQUALAREACONIC") || 
      streq(new_name, "ALBERSCONIC") || 
      streq(new_name, "ALBERSEQUALAREA"))
  { strcpy(new_name,"ALBERSCONICEQUALAREA");
  }
  else if (streq(new_name, "ALBERSCONICEQUALAREAELLIPSOID") || 
      streq(new_name, "ELLIPSOIDALBERSCONICEQUALAREA") || 
      streq(new_name, "ALBERSEQUALAREACONICELLIPSOID") || 
      streq(new_name, "CONICEQUALAREAELLIPSOID") || 
      streq(new_name, "EQUALAREACONICELLIPSOID") || 
      streq(new_name, "ALBERSCONICELLIPSOID") || 
      streq(new_name, "ALBERSEQUALAREAELLIPSOID"))
  { strcpy(new_name,"ALBERSCONICEQUALAREAELLIPSOID");
  }
  else if (streq(new_name, "INTEGERIZEDSINUSOIDAL") || 
      streq(new_name, "ISIN") || 
      streq(new_name, "ISINUS"))
  { strcpy(new_name,"INTEGERIZEDSINUSOIDAL");
  }
  else if (streq(new_name, "TRANSVERSEMERCATOR") ||
	   streq(new_name, "MERCATORTRANSVERSE"))
    { strcpy(new_name,"TRANSVERSEMERCATOR");
    }
  else if (streq(new_name, "TRANSVERSEMERCATORELLIPSOID") ||
           streq(new_name, "ELLIPSOIDTRANSVERSEMERCATOR") ||
	   streq(new_name, "MERCATORTRANSVERSEELLIPSOID") ||
	   streq(new_name, "ELLIPSOIDMERCATORTRANSVERSE"))
    { strcpy(new_name,"TRANSVERSEMERCATORELLIPSOID");
    }
  else if (streq(new_name, "UNIVERSALTRANSVERSEMERCATOR") ||
	   streq(new_name, "UNIVERSALMERCATORTRANSVERSE") ||
           streq(new_name, "UTM") ||
	   streq(new_name, "UNIVERSALTRANSVERSEMERCATORELLIPSOID") ||
           streq(new_name, "ELLIPSOIDUNIVERSALTRANSVERSEMERCATOR") ||
	   streq(new_name, "UNIVERSALMERCATORTRANSVERSEELLIPSOID") ||
	   streq(new_name, "ELLIPSOIDUNIVERSALMERCATORTRANSVERSE") ||
	   streq(new_name, "UTMELLIPSOID") ||
	   streq(new_name, "ELLIPSOIDUTM"))
    { strcpy(new_name,"UNIVERSALTRANSVERSEMERCATOR");
    }
  
  return new_name;
}

#ifdef XYTEST
/*------------------------------------------------------------------------
 * xytest - interactive test for mapx routines
 *------------------------------------------------------------------------*/
main(int argc, char *argv[])
{
  double lat, lon, x, y;
  int status;
  char readln[FILENAME_MAX];
  mapx_class *the_map;

  mapx_verbose = 1;

  for (;;)
  { 
    if (argc > 1) {
      --argc; ++argv;
      strcpy(readln, *argv);
    }
    else {
      printf("\nenter .mpp file name - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
    }

    the_map = init_mapx(readln);
    if (the_map == NULL) continue;
    
    printf("\nforward_mapx:\n");
    for (;;)
    { printf("enter lat lon - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
      sscanf(readln, "%lf %lf", &lat, &lon);
      status = forward_xy_mapx(the_map, lat, lon, &x, &y);
      printf("x,y = %17.7lf %17.7lf     %s\n", x, y, 
	     status == 0 ? "valid" : "invalid");
      status = inverse_xy_mapx(the_map, x, y, &lat, &lon);
      printf("lat,lon = %11.7lf %12.7lf     %s\n", lat, lon, 
	     status == 0 ? "valid" : "invalid");
    }
    
    printf("\ninverse_mapx:\n");
    for (;;)
    { printf("enter x y - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
      sscanf(readln, "%lf %lf", &x, &y);
      status = inverse_xy_mapx(the_map, x, y, &lat, &lon);
      printf("lat,lon = %11.7lf %#12.7lf    %s\n", lat, lon, 
	     status == 0 ? "valid" : "invalid");
      status = forward_xy_mapx(the_map, lat, lon, &x, &y);
      printf("x,y = %17.7lf %#17.7lf    %s\n", x, y, 
	     status == 0 ? "valid" : "invalid");
    }
    
    close_mapx(the_map);
  }
}
#endif

#ifdef MTEST
/*------------------------------------------------------------------------
 * mtest - interactive test for mapx routines
 *------------------------------------------------------------------------*/
main(int argc, char *argv[])
{
  double lat, lon, u, v;
  int status;
  char readln[FILENAME_MAX];
  mapx_class *the_map;

  mapx_verbose = 1;

  for (;;)
  { 
    if (argc > 1) {
      --argc; ++argv;
      strcpy(readln, *argv);
    }
    else {
      printf("\nenter .mpp file name - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
    }

    the_map = init_mapx(readln);
    if (the_map == NULL) continue;
    
    printf("\nforward_mapx:\n");
    for (;;)
    { printf("enter lat lon - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
      sscanf(readln, "%lf %lf", &lat, &lon);
      status = forward_mapx(the_map, lat, lon, &u, &v);
      printf("u,v = %lf %lf    %s\n", u, v, 
	     status == 0 ? "valid" : "invalid");
      status = inverse_mapx(the_map, u, v, &lat, &lon);
      printf("lat,lon = %lf %lf     %s\n", lat, lon, 
	     status == 0 ? "valid" : "invalid");
    }
    
    printf("\ninverse_mapx:\n");
    for (;;)
    { printf("enter u v - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
      sscanf(readln, "%lf %lf", &u, &v);
      status = inverse_mapx(the_map, u, v, &lat, &lon);
      printf("lat,lon = %lf %lf    %s\n", lat, lon, 
	     status == 0 ? "valid" : "invalid");
      status = forward_mapx(the_map, lat, lon, &u, &v);
      printf("u,v = %lf %lf    %s\n", u, v, 
	     status == 0 ? "valid" : "invalid");
    }
    printf("\nwithin_mapx:\n");
    for (;;)
    { printf("enter lat lon - ");
      gets(readln);
      if (feof(stdin)) { printf("\n"); exit(0);}
      if (*readln == '\0') break;
      sscanf(readln, "%lf %lf", &lat, &lon);
      printf("%s\n", within_mapx(the_map, lat, lon) ? "INSIDE" : "OUTSIDE");
    }
    
    close_mapx(the_map);
  }
}
#endif

#ifdef MACCT
#define usage "usage: macct mpp_file"
/*------------------------------------------------------------------------
 * macct - accuracy test mapx routines
 *------------------------------------------------------------------------*/
#define MPMON
static double dist_km(double lat1, double lon1, double lat2, double lon2)
{ register double phi1, lam1, phi2, lam2, beta;
  phi1 = radians(lat1);
  lam1 = radians(lon1);
  phi2 = radians(lat2);
  lam2 = radians(lon2);
  beta = acos(cos(phi1)*cos(phi2)*cos(lam1-lam2) + sin(phi1)*sin(phi2));
  return beta*mapx_Re_km;
}
#endif

#ifdef MPMON
#ifndef usage
#define usage "usage: mpmon mpp_file [num_its]"
#endif
/*------------------------------------------------------------------------
 * mpmon - performance test mapx routines
 *------------------------------------------------------------------------*/
main(int argc, char *argv[])
{
  register int i_lat, i_lon, npts = 0, bad_pts = 0;
  int status1, status2;
  int ii, its = 1, pts_lat = 319, pts_lon = 319;
  register double lat, lon, dlat, dlon;
  double latx, lonx, u, v;
  mapx_class *the_map;
#ifdef MACCT
  double err=0, sum=0, sum2=0, stdv=0, max_err=-1, lat_max=0, lon_max=0;
#endif
  
  if (argc < 2)
#ifdef MACCT
  { fprintf(stderr,"#\tmacct can be used to test the accuracy\n");
    fprintf(stderr,"#\tof the mapx routines. It runs the forward and\n");
    fprintf(stderr,"#\tinverse transforms at ~100K points over the whole\n");
    fprintf(stderr,"#\tmap. Error statistics are accumulated in kilometers.\n");
    fprintf(stderr,"#\tTo run the test type:\n");
    fprintf(stderr,"#\t\tmacct test.mpp\n");
    fprintf(stderr,"\n");
    error_exit(usage);
  }
#else
  { fprintf(stderr,"#\tmpmon can be used to monitor the performance\n");
    fprintf(stderr,"#\tof the mapx routines. It runs the forward and\n");
    fprintf(stderr,"#\tinverse transforms at ~100K points over the whole\n");
    fprintf(stderr,"#\tmap. The optional parameter num_its specifies how\n");
    fprintf(stderr,"#\tmany times to run through the entire map, (the\n");
    fprintf(stderr,"#\tdefault is 1). To run the test type:\n");
    fprintf(stderr,"#\t\tmpmon test.mpp\n");
    fprintf(stderr,"#\t\tprof mpmon\n");
    fprintf(stderr,"\n");
    error_exit(usage);
  }
#endif
  
  the_map = init_mapx(argv[1]);
  if (the_map == NULL) error_exit(usage);
  if (argc < 3 || sscanf(argv[2],"%d",&its) != 1) its = 1;
  
  dlat = the_map->north - the_map->south;
  dlon = the_map->east - the_map->west;
  
  for (ii = 1; ii <= its; ii++)
  { for (i_lat = 0; i_lat <= pts_lat; i_lat++)
    { lat = (double)i_lat/pts_lat * dlat + the_map->south;
      for (i_lon = 0; i_lon <= pts_lon; i_lon++)
      { lon = (double)i_lon/pts_lon * dlon + the_map->west;
	status1 = forward_mapx(the_map, lat, lon, &u, &v);
	status2 = inverse_mapx(the_map, u, v, &latx, &lonx);
	if ((status1 | status2) != 0) ++bad_pts;
	++npts;
#ifdef MACCT
	if ((status1 | status2) == 0)
	{ err = dist_km(lat, lon, latx, lonx);
	  if (err > 0) { sum += err; sum2 += err*err; }
	  if (err > max_err) { max_err=err; lat_max=lat; lon_max=lon; }
	}
#endif
      }
    }
  }
  fprintf(stderr,"%d points,  %d bad points\n", npts, bad_pts);
#ifdef MACCT
  npts -= bad_pts;
  if (npts > 0)
  { err = sum/npts;
    stdv = sqrt((sum2 - npts*err*err)/(npts-1));
  }
  fprintf(stderr,"average error = %10.4le km\n", err);
  fprintf(stderr,"std dev error = %10.4le km\n", stdv);
  fprintf(stderr,"maximum error = %10.4le km\n", max_err);
  fprintf(stderr,"max error was at %4.2lf%c %4.2lf%c\n",
	  fabs(lat_max), lat_max >= 0 ? 'N' : 'S',
	  fabs(lon_max), lon_max >= 0 ? 'E' : 'W');
#endif
}
#endif
