/*======================================================================
 * mapx.h - definitions for map projection routines
 *
 * 2-July-1991 K.Knowles knowles@kryos.colorado.edu 303-492-0644
 * 15-Dec-1992 R.Swick swick@krusty.colorado.edu 303-492-1395
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#ifndef mapx_h_
#define mapx_h_
static const char mapx_h_rcsid[] = "$Header: /usr/local/src/maps/mapx.h,v 1.22 1999/11/29 22:56:47 knowles Exp $";

/*
 * global verbose flag
 */
#ifdef MAPX_C_
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

/* radius of the Earth in km, authalic sphere based on International datum */
#define mapx_Re_km  6371.228
/* equatorial radius in km and eccentricity of the Earth based on Clark 1866 Datum */
#define mapx_equatorial_radius_km 6378.2064
#define mapx_eccentricity 0.082271673

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
 */
  float lat0, lon0, lat1, lon1;
  float rotation, scale;
  float south, north, west, east;
  float center_lat, center_lon, label_lat, label_lon;
  float lat_interval, lon_interval;
  int cil_detail, bdy_detail, riv_detail;
  double equatorial_radius, eccentricity;
/*
 *	private projection constants
 */
  float T00, T01, T10, T11, u0, v0;
  int map_stradles_180;
  double e2, e4, e6, e8, qp, Rq, q0, q1, q2, Rg;
  double sin_phi0, sin_phi1, sin_phi2, sin_lam1;
  double cos_phi0, cos_phi1, cos_phi2, cos_lam1;
  double beta1, sin_beta1, cos_beta1, D, phis, kz;
  double rho0, n, C, F, m0, m1, m2, t0, t1;
  int (*geo_to_map)(void *, float, float, float *, float *);
  int (*map_to_geo)(void *, float, float, float *, float *);
  int (*initialize)(void *);
  char *projection_name;
  FILE *mpp_file;
  char *mpp_filename;
} mapx_class;

/*
 * function prototypes
 */
mapx_class *init_mapx(char *filename);
mapx_class *new_mapx(char *label);
void close_mapx(mapx_class *this);
int reinit_mapx(mapx_class *this);
int within_mapx(mapx_class *this, float lat, float lon);
int forward_mapx(mapx_class *this, float lat, float lon, float *u, float *v);
int inverse_mapx(mapx_class *this, float u, float v, float *lat, float *lon);

#endif
