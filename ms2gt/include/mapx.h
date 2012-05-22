/*======================================================================
 * mapx.h - definitions for map projection routines
 *
 * 2-July-1991 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * 15-Dec-1992 R.Swick swick@kryos.colorado.edu 303-492-1395
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1991 University of Colorado
 *======================================================================*/
#ifndef mapx_h_
#define mapx_h_

#ifdef mapx_c_
const char mapx_h_rcsid[] = "$Id: mapx.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

/*
 * global verbose flag
 */
#ifdef mapx_c_
#  define GLOBAL
#else
#  define GLOBAL extern
#endif

GLOBAL int mapx_verbose;

#undef GLOBAL

/* 
 * useful macros
 */
#define NORMALIZE(lon) \
{ while (lon < -180) lon += 360; \
  while (lon >  180) lon -= 360; \
}

#define RNORMALIZE(lam) \
{ while (lam < -PI) lam += 2*PI; \
  while (lam >  PI) lam -= 2*PI; \
}

#ifndef SQRT2
#define SQRT2 1.414213562373095
#endif

#ifndef PI
#define PI 3.141592653589793
#endif

#ifndef NAN
#define NAN (asin(2.0))
#endif

/* radius of the Earth in km, authalic sphere based on International datum */
#define mapx_Re_km  6371.228
/* equatorial radius in km and eccentricity of the Earth based on Clark 1866 Datum */
#define mapx_equatorial_radius_km 6378.2064
#define mapx_eccentricity 0.082271673

/*
 *  define WGS-84 values for equatorial radius in meters and eccentricity
 */
#define mapx_equatorial_radius_wgs84_m  6378137.0
#define mapx_eccentricity_wgs84         0.081819190843

/*
 *  define ISin value for equatorial radius in meters
 */
#define mapx_equatorial_radius_isin_m  6371007.181

#define RADIANS(t) ((t) * PI/180)
#define DEGREES(t) ((t) * 180/PI)

/*
 * environment variable for parameter files search path
 */
#define mapx_PATH "PATHMPP"

/*
 * map parameters structure
 */
typedef struct {
/*
 *	user specified constants
 *      use of dummy values is to maintain 16-byte alignment of doubles so that
 *      gdb prints doubles correctly
 */
  double lat0, lon0, lat1, lon1;
  double rotation, scale;
  double south, north, west, east;
  double center_lat, center_lon, label_lat, label_lon;
  double lat_interval, lon_interval;
  int cil_detail, bdy_detail, riv_detail, dummy1;
  double equatorial_radius, polar_radius, eccentricity, e2;
  double x0, y0, false_easting, false_northing;
  double center_scale, maximum_error;
  int utm_zone;
  int isin_nzone, isin_justify, dummy2;
/*
 *	private projection constants
 */
  double T00, T01, T10, T11, u0, v0;
  int map_stradles_180, dummy3;
  double e4, e6, e8, qp, Rq, q0, q1, q2, Rg;
  double sin_phi0, sin_phi1, sin_phi2, sin_lam1;
  double cos_phi0, cos_phi1, cos_phi2, cos_lam1;
  double beta1, sin_beta1, cos_beta1, D, phis, kz;
  double rho0, n, C, F, m0, m1, m2, t0, t1, t2;
  void *isin_data, *dummy4;
  double e0, e1p, e2p, e3p, ml0, esp;
  double f1, f2, f3, f4, f;
  int (*geo_to_map)(void *, double, double, double *, double *);
  int (*map_to_geo)(void *, double, double, double *, double *);
  int (*initialize)(void *);
  char *projection_name;
  FILE *mpp_file;
  char *mpp_filename;
} mapx_class;

/*
 * function prototypes
 */
mapx_class *init_mapx(char *filename);
mapx_class *new_mapx(char *label, bool quiet);
char *next_line_from_buffer(char *bufptr, char *readln);
void close_mapx(mapx_class *this);
int reinit_mapx(mapx_class *this);
int within_mapx(mapx_class *this, double lat, double lon);
int forward_mapx(mapx_class *this,
		 double lat, double lon, double *u, double *v);
int inverse_mapx(mapx_class *this,
		 double u, double v, double *lat, double *lon);
int forward_xy_mapx(mapx_class *this,
		    double lat, double lon, double *x, double *y);
int inverse_xy_mapx(mapx_class *this,
		    double x, double u, double *lat, double *lon);

#endif
