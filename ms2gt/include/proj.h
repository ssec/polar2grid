#ifndef PROJ_H
#define PROJ_H

/* Projection codes


   0 = Geographic
   1 = Universal Transverse Mercator (UTM)
   2 = State Plane Coordinates
   3 = Albers Conical Equal Area
   4 = Lambert Conformal Conic
   5 = Mercator
   6 = Polar Stereographic
   7 = Polyconic
   8 = Equidistant Conic
   9 = Transverse Mercator
  10 = Stereographic
  11 = Lambert Azimuthal Equal Area
  12 = Azimuthal Equidistant
  13 = Gnomonic
  14 = Orthographic
  15 = General Vertical Near-Side Perspective
  16 = Sinusiodal
  17 = Equirectangular
  18 = Miller Cylindrical
  19 = Van der Grinten
  20 = (Hotine) Oblique Mercator 
  21 = Robinson
  22 = Space Oblique Mercator (SOM)
  23 = Alaska Conformal
  24 = Interrupted Goode Homolosine 
  25 = Mollweide
  26 = Interrupted Mollweide
  27 = Hammer
  28 = Wagner IV
  29 = Wagner VII
  30 = Oblated Equal Area
  31 = Integerized Sinusiodal
  99 = User defined
*/

/* Define projection codes */
#define GEO 0
#define UTM 1
#define SPCS 2
#define ALBERS 3
#define LAMCC 4
#define MERCAT 5
#define PS 6
#define POLYC 7
#define EQUIDC 8
#define TM 9
#define STEREO 10
#define LAMAZ 11
#define AZMEQD 12
#define GNOMON 13
#define ORTHO 14
#define GVNSP 15
#define SNSOID 16
#define EQRECT 17
#define MILLER 18
#define VGRINT 19
#define HOM 20
#define ROBIN 21
#define SOM 22
#define ALASKA 23
#define GOOD 24
#define MOLL 25
#define IMOLL 26
#define HAMMER 27
#define WAGIV 28
#define WAGVII 29
#define OBEQA 30
#define ISIN 31
#define USDEF 99 

/* Define unit code numbers to their names */

#define RADIAN 0		/* Radians */
#define FEET 1			/* Feed */
#define METER 2			/* Meters */
#define SECOND 3		/* Seconds */
#define DEGREE 4		/* Decimal degrees */
#define INT_FEET 5		/* International Feet */

/* The STPLN_TABLE unit value is specifically used for State Plane -- if units
   equals STPLN_TABLE and Datum is NAD83--actual units are retrieved from
   a table according to the zone.  If Datum is NAD27--actual units will be feet.
   An error will occur with this unit if the projection is not State Plane.  */

#define STPLN_TABLE 6

/* General code numbers */

#define IN_BREAK -2		/* Return status if the interupted projection
				    point lies in the break area */
#define COEFCT 15		/* projection coefficient count */
#define MAXPROJ 31		/* largest supported projection number */
#define PROJCT (MAXPROJ + 1) /* count of supported projections */
#define SPHDCT 32		/* spheroid count */

#define MAXUNIT 5		/* Maximum unit code number */
#define GEO_TERM 0		/* Array index for print-to-term flag */
#define GEO_FILE 1		/* Array index for print-to-file flag */
#define GEO_TRUE 1		/* True value for geometric true/false flags */
#define GEO_FALSE -1		/*  False val for geometric true/false flags */

/* GCTP Function prototypes */

long alberforint
(
    double r_maj,
    double r_min,
    double lat1,
    double lat2,
    double lon0,
    double lat0,
    double false_east,
    double false_north
);

long alberfor
(
    double lon,
    double lat,
    double *x,
    double *y
);

long alberinvint
(
    double r_maj,               /* major axis                           */
    double r_min,               /* minor axis                           */
    double lat1,                /* first standard parallel              */
    double lat2,                /* second standard parallel             */
    double lon0,                /* center longitude                     */
    double lat0,                /* center lattitude                     */
    double false_east,          /* x offset in meters                   */
    double false_north          /* y offset in meters                   */
);

long alberinv
(
    double x,                   /* (O) X projection coordinate  */
    double y,                   /* (O) Y projection coordinate      */
    double *lon,                /* (I) Longitude                */
    double *lat                 /* (I) Latitude             */
);

long alconforint
(
    double r_maj,               /* Major axis                           */
    double r_min,               /* Minor axis                           */
    double false_east,          /* x offset in meters                   */
    double false_north          /* y offset in meters                   */
);

long alconfor
(
    double lon,                 /* (I) Longitude */
    double lat,                 /* (I) Latitude */
    double *x,                  /* (O) X projection coordinate */
    double *y                   /* (O) Y projection coordinate */
);

long alconinvint
(
    double r_maj,               /* Major axis                           */
    double r_min,               /* Minor axis                           */
    double false_east,          /* x offset in meters                   */
    double false_north          /* y offset in meters                   */
);

long alconinv
(
    double x,                   /* (O) X projection coordinate */
    double y,                   /* (O) Y projection coordinate */
    double *lon,                /* (I) Longitude */
    double *lat                 /* (I) Latitude */
);

long azimforint
(
    double r_maj,               /* major axis                   */
    double center_lon,          /* center longitude             */
    double center_lat,          /* center latitude              */
    double false_east,          /* x offset in meters           */
    double false_north          /* y offset in meters           */
);

long azimfor
(
    double lon,                 /* (I) Longitude                */
    double lat,                 /* (I) Latitude                 */
    double *x,                  /* (O) X projection coordinate  */
    double *y                   /* (O) Y projection coordinate  */
);

long aziminvint
(
    double r_maj,               /* major axis                   */
    double center_lon,          /* center longitude             */
    double center_lat,          /* center latitude              */
    double false_east,          /* x offset in meters           */
    double false_north          /* y offset in meters           */
);

long aziminv
(
    double x,                   /* (O) X projection coordinate  */
    double y,                   /* (O) Y projection coordinate  */
    double *lon,                /* (I) Longitude                */
    double *lat                 /* (I) Latitude                 */
);

void gctp_
(
    double *incoor,
    long *insys,
    long *inzone,
    double *inparm,
    long *inunit,
    long *inspheroid,
    long *ipr,        /* printout flag for error messages. 0=yes, 1=no*/
    char *efile,
    long *jpr,        /* printout flag for projection parameters 0=yes, 1=no*/
    char *pfile,
    double *outcoor,
    long *outsys,
    long *outzone,
    double *outparm,
    long *outunit,
    long *outspheroid,
    int fn27,
    int fn83,
    long *iflg
);

double asinz
(
    double con
);

double msfnz
(
    double eccent,
    double sinphi,
    double cosphi
);

double qsfnz
(
    double eccent,
    double sinphi
);

double phi1z
(
    double eccent,           /* Eccentricity angle in radians                */
    double qs,               /* Angle in radians                             */
    long *flag               /* Error flag number                            */
);

double phi2z
(
    double eccent,           /* Spheroid eccentricity                */
    double ts,               /* Constant value t                     */
    long *flag               /* Error flag number                    */
);

double phi3z
(
    double ml,               /* Constant                     */
    double e0,               /* Constant                     */
    double e1,               /* Constant                     */
    double e2,               /* Constant                     */
    double e3,               /* Constant                     */
    long *flag               /* Error flag number            */
);

int phi4z
(
    double eccent,           /* Spheroid eccentricity squared        */
    double e0,
    double e1,
    double e2,
    double e3,
    double a,
    double b,
    double *c,
    double *phi
);

double pakcz
(
    double pak               /* Angle in alternate packed DMS format */
);

double pakr2dm
(
    double pak               /* Angle in radians                     */
);

double tsfnz
(
    double eccent,           /* Eccentricity of the spheroid         */
    double phi,              /* Latitude phi                         */
    double sinphi            /* Sine of the latitude                 */
);

int sign
(
    double x
);

double adjust_lon
(
    double x                 /* Angle in radians                     */
);

double e0fn
(
    double x
);

double e1fn
(
    double x
);

double e2fn
(
    double x
);

double e3fn
(
    double x
);

double e4fn
(
    double x
);

double mlfn
(
    double e0,
    double e1,
    double e2,
    double e3,
    double phi
);

long calc_utm_zone
(
    double lon
);

long eqconforint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double lat1,             /* latitude of standard parallel*/
    double lat2,             /* latitude of standard parallel*/
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north,      /* y offset in meters           */
    long mode                /* which format is present A B  */
);

long eqconfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long eqconinvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double lat1,             /* latitude of standard parallel*/
    double lat2,             /* latitude of standard parallel*/
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north,      /* y offset in meters           */
    long mode                /* which format is present A B  */
);

long eqconinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long equiforint
(
    double r_maj,            /* major axis                   */
    double center_lon,       /* center longitude             */
    double lat1,             /* latitude of true scale       */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long equifor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long equiinvint
(
    double r_maj,            /* major axis                   */
    double center_lon,       /* center longitude             */
    double lat1,             /* latitude of true scale       */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long equiinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

void for_init
(
    long outsys,             /* output system code                           */
    long outzone,            /* output zone number                           */
    double *outparm,         /* output array of projection parameters        */
    long outspheroid,        /* output spheroid                              */
    char *fn27,              /* NAD 1927 parameter file                      */
    char *fn83,              /* NAD 1983 parameter file                      */
    long *iflg,              /* status flag                                  */
    long (*for_trans[])(void)/* forward function pointer                     */
);

void gctp
(
    double *incoor,          /* input coordinates                            */
    long *insys,             /* input projection code                        */
    long *inzone,            /* input zone number                            */
    double *inparm,          /* input projection parameter array             */
    long *inunit,            /* input units                                  */
    long *inspheroid,        /* input spheroid                               */
    long *ipr,               /* printout flag for error messages. 0=screen, 
                                1=file, 2=both*/
    char *efile,             /* error file name                              */
    long *jpr,               /* printout flag for projection parameters 
                                0=screen, 1=file, 2 = both*/
    char *pfile,             /* error file name                              */
    double *outcoor,         /* output coordinates                           */
    long *outsys,            /* output projection code                       */
    long *outzone,           /* output zone                                  */
    double *outparm,         /* output projection array                      */
    long *outunit,           /* output units                                 */
    long *outspheroid,       /* output spheroid                              */
    char fn27[],             /* file name of NAD 1927 parameter file         */
    char fn83[],             /* file name of NAD 1983 parameter file         */
    long *iflg               /* error flag                                   */
);

long gnomforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double center_lat,       /* (I) Center latitude                  */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long gnomfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long gnominvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double center_lat,       /* (I) Center latitude                  */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long gnominv
(
    double x,                /* (O) X projection coordinate */
    double y,                /* (O) Y projection coordinate */
    double *lon,             /* (I) Longitude */
    double *lat              /* (I) Latitude */
);

long goodforint
(
    double r                 /* (I) Radius of the earth (sphere) */
);

long goodfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long goodinvint
(
    double r                 /* (I) Radius of the earth (sphere) */
);

long goodinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long gvnspforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double h,                /* height above sphere                  */
    double center_long,      /* (I) Center longitude                 */
    double center_lat,       /* (I) Center latitude                  */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long gvnspfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long gvnspinvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double h,                /* height above sphere                  */
    double center_long,      /* (I) Center longitude                 */
    double center_lat,       /* (I) Center latitude                  */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long gvnspinv
(
    double x,                /* (O) X projection coordinate */
    double y,                /* (O) Y projection coordinate */
    double *lon,             /* (I) Longitude */
    double *lat              /* (I) Latitude */
);

long hamforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long hamfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long haminvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long haminv
(
    double x,                /* (O) X projection coordinate */
    double y,                /* (O) Y projection coordinate */
    double *lon,             /* (I) Longitude */
    double *lat              /* (I) Latitude */
);

long imolwforint
(
    double r                 /* (I) Radius of the earth (sphere) */
);

long imolwfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long imolwinvint
(
    double r                 /* (I) Radius of the earth (sphere) */
);

long imolwinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

void inv_init
(
    long insys,              /* input system code                            */
    long inzone,             /* input zone number                            */
    double *inparm,          /* input array of projection parameters         */
    long inspheroid,         /* input spheroid code                          */
    char *fn27,              /* NAD 1927 parameter file                      */
    char *fn83,              /* NAD 1983 parameter file                      */
    long *iflg,              /* status flag                                  */
    long (*inv_trans[])(void)/* inverse function pointer                     */
);

long isinusforinit
( 
    double sphere,           /* (I) Radius of the earth (sphere) */
    double lon_cen_mer,	     /* (I) Longitude of central meridian (radians) */
    double false_east,	     /* (I) Easting at projection origin (meters) */
    double false_north,	     /* (I) Northing at projection origin (meters) */
    double dzone,	     /* (I) Number of longitudinal zones */
    double djustify	     /* (I) Justify (flag for rows w/odd # of columns)*/
);

long isinusfor
(
    double lon,	             /* (I) Longitude */
    double lat,	             /* (I) Latitude */
    double *x,	             /* (O) X projection coordinate */
    double *y	             /* (O) Y projection coordinate */
);

long isinusinvinit
(
    double sphere,	     /* (I) Radius of the earth (sphere) */
    double lon_cen_mer,	     /* (I) Longitude of central meridian (radians) */
    double false_east,	     /* (I) Easting at projection origin (meters) */
    double false_north,	     /* (I) Northing at projection origin (meters) */
    double dzone,	     /* (I) Number of longitudinal zones */
    double djustify	     /* (I) Justify (flag for rows w/odd # of columns)*/
);

long isinusinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long lamazforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double center_lat,       /* (I) Center latitude                  */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long lamazfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long lamazinvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double center_lat,       /* (I) Center latitude                  */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long lamazinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long lamccforint
(
    double r_maj,            /* major axis                           */
    double r_min,            /* minor axis                           */
    double lat1,             /* first standard parallel              */
    double lat2,             /* second standard parallel             */
    double c_lon,            /* center longitude                     */
    double c_lat,            /* center latitude                      */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long lamccfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long lamccinvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double lat1,             /* first standard parallel      */
    double lat2,             /* second standard parallel     */
    double c_lon,            /* center longitude             */
    double c_lat,            /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long lamccinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long merforint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long merfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long merinvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long merinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long millforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long millfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long millinvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long millinv
(
    double x,                /* (O) X projection coordinate */
    double y,                /* (O) Y projection coordinate */
    double *lon,             /* (I) Longitude */
    double *lat              /* (I) Latitude */
);

long molwforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long molwfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long molwinvint
(
    double r,                /* (I) Radius of the earth (sphere) */
    double center_long,      /* (I) Center longitude */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long molwinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long obleqforint
(
    double r,
    double center_long,
    double center_lat,
    double shape_m,
    double shape_n,
    double angle,
    double false_east,
    double false_north
);

long obleqfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long obleqinvint
(
    double r,
    double center_long,
    double center_lat,
    double shape_m,
    double shape_n,
    double angle,
    double false_east,
    double false_north
);

long obleqinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long omerforint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double scale_fact,       /* scale factor                 */
    double azimuth,          /* azimuth east of north        */
    double lon_orig,         /* longitude of origin          */
    double lat_orig,         /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north,      /* y offset in meters           */
    double lon1,             /* fist point to define central line    */
    double lat1,             /* fist point to define central line    */
    double lon2,             /* second point to define central line  */
    double lat2,             /* second point to define central line  */
    long mode                /* which format type A or B     */
);

long omerfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long omerinvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double scale_fact,       /* scale factor                 */
    double azimuth,          /* azimuth east of north        */
    double lon_orig,         /* longitude of origin          */
    double lat_orig,         /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north,      /* y offset in meters           */
    double lon1,             /* fist point to define central line    */
    double lat1,             /* fist point to define central line    */
    double lon2,             /* second point to define central line  */
    double lat2,             /* second point to define central line  */
    long mode                /* which format type A or B     */
);

long omerinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long orthforint
(
    double r_maj,            /* major axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long orthfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long orthinvint
(
    double r_maj,            /* major axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long orthinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

double paksz
(
    double ang,              /* angle which in DMS           */
    long *iflg               /* error flag number            */
);

long polyforint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long polyfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long polyinvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long polyinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long psforint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double c_lon,            /* center longitude             */
    double c_lat,            /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long psfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long psinvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double c_lon,            /* center longitude             */
    double c_lat,            /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long psinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long init
(
    long ipr,                /* flag for printing errors (0,1,or 2)          */
    long jpr,                /* flag for printing parameters (0,1,or 2)      */
    char *efile,             /* name of error file                           */
    char *pfile              /* name of parameter file                       */
);

/* Functions to report projection parameters
  -----------------------------------------*/
void ptitle
(
    char *A
);

void ptitle
(
    char *A
);

void radius
(
    double A
);

void radius2
(
    double A,
    double B
);

void cenlon
(
    double A
);

void cenlonmer
(
    double A
);

void cenlat
(
    double A
);

void origin
(
    double A
);

void stanparl
(
    double A,
    double B
);

void stparl1
(
    double A
);

void offsetp
(
    double A,
    double B
);

void genrpt
(
    double A,
    char *S
);

void genrpt_long
(
    long A,
    char *S
);

void pblank(void);

void p_error
(
    char *what,
    char *where
);

long robforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long robfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long robinvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long robinv
(
    double x,                /* (O) X projection coordinate */
    double y,                /* (O) Y projection coordinate */
    double *lon,             /* (I) Longitude */
    double *lat              /* (I) Latitude */
);

long sinforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long sinfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long sininvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long sininv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long somforint
(
    double r_major,          /* major axis                           */
    double r_minor,          /* minor axis                           */
    long satnum,             /* Landsat satellite number (1,2,3,4,5) */
    long path,               /* Landsat path number */
    double alf_in,
    double lon,
    double false_east,       /* x offset in meters                   */
    double false_north,      /* y offset in meters                   */
    double time,
    long start1,
    long flag
);

long somfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *y,               /* (O) Y projection coordinate  */
    double *x                /* (O) X projection coordinate  */
);

long sominvint
(
    double r_major,          /* major axis                           */
    double r_minor,          /* minor axis                           */
    long satnum,             /* Landsat satellite number (1,2,3,4,5) */
    long path,               /* Landsat path number */
    double alf_in,
    double lon,
    double false_east,       /* x offset in meters                   */
    double false_north,      /* y offset in meters                   */
    double time,
    long start1,
    long flag
);

long sominv
(
    double y,                /* (I) Y projection coordinate */
    double x,                /* (I) X projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

void sphdz
(
    long isph,               /* spheroid code number                         */
    double *parm,            /* projection parameters                        */
    double *r_major,         /* major axis                                   */
    double *r_minor,         /* minor axis                                   */
    double *radius           /* radius                                       */
);

long sterforint
(
    double r_maj,            /* major axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long sterfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long sterinvint
(
    double r_maj,            /* major axis                   */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long sterinv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long stplnforint
(
    long zone,               /* zone number */
    long sphere,             /* spheroid number */
    char *fn27,              /* name of file containing the NAD27 parameters */
    char *fn83               /* name of file containing the NAD83 parameters */
);

long stplnfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long stplninvint
(
    long zone,               /* zone number */
    long sphere,             /* spheroid number */
    char *fn27,              /* name of file containing the NAD27 parameters */
    char *fn83               /* name of file containing the NAD83 parameters */
);

long stplninv
(
    double x,                /* (O) X projection coordinate  */
    double y,                /* (O) Y projection coordinate  */
    double *lon,             /* (I) Longitude                */
    double *lat              /* (I) Latitude                 */
);

long tmforint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double scale_fact,       /* scale factor                 */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long tmfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long tminvint
(
    double r_maj,            /* major axis                   */
    double r_min,            /* minor axis                   */
    double scale_fact,       /* scale factor                 */
    double center_lon,       /* center longitude             */
    double center_lat,       /* center latitude              */
    double false_east,       /* x offset in meters           */
    double false_north       /* y offset in meters           */
);

long tminv
(
    double x,                /* (I) X projection coordinate                  */
    double y,                /* (I) Y projection coordinate                  */
    double *lon,             /* (O) Longitude                                */
    double *lat              /* (O) Latitude                                 */
);

long untfz
(
    long inunit,
    long outunit,
    double *factor
);

long utmforint
(
    double r_maj,            /* major axis                           */
    double r_min,            /* minor axis                           */
    double scale_fact,       /* scale factor                         */
    long zone                /* zone number                          */
);

long utmfor
(
    double lon,              /* (I) Longitude                */
    double lat,              /* (I) Latitude                 */
    double *x,               /* (O) X projection coordinate  */
    double *y                /* (O) Y projection coordinate  */
);

long utminvint
(
    double r_maj,            /* major axis                           */
    double r_min,            /* minor axis                           */
    double scale_fact,       /* scale factor                         */
    long zone                /* zone number                          */
);

long utminv
(
    double x,                /* (I) X projection coordinate                  */
    double y,                /* (I) Y projection coordinate                  */
    double *lon,             /* (O) Longitude                                */
    double *lat              /* (O) Latitude                                 */
);

long vandgforint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long vandgfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long vandginvint
(
    double r,                /* (I) Radius of the earth (sphere)     */
    double center_long,      /* (I) Center longitude                 */
    double false_east,       /* x offset in meters                   */
    double false_north       /* y offset in meters                   */
);

long vandginv
(
    double x,                /* (O) X projection coordinate */
    double y,                /* (O) Y projection coordinate */
    double *lon,             /* (I) Longitude */
    double *lat              /* (I) Latitude */
);

long wivforint
(
    double r,                /* (I) Radius of the earth (sphere) */
    double center_long,      /* (I) Center longitude */
    double false_east,       /* x offset                             */
    double false_north       /* y offset                             */
);

long wivfor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long wivinvint
(
    double r,                /* (I) Radius of the earth (sphere) */
    double center_long,      /* (I) Center longitude */
    double false_east,       /* x offset                             */
    double false_north       /* y offset                             */
);

long wivinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

long wviiforint
(
    double r,                /* (I) Radius of the earth (sphere) */
    double center_long,      /* (I) Center longitude */
    double false_east,       /* x offset                             */
    double false_north       /* y offset                             */
);

long wviifor
(
    double lon,              /* (I) Longitude */
    double lat,              /* (I) Latitude */
    double *x,               /* (O) X projection coordinate */
    double *y                /* (O) Y projection coordinate */
);

long wviiinvint
(
    double r,                /* (I) Radius of the earth (sphere) */
    double center_long,      /* (I) Center longitude */
    double false_east,       /* x offset                             */
    double false_north       /* y offset                             */
);

long wviiinv
(
    double x,                /* (I) X projection coordinate */
    double y,                /* (I) Y projection coordinate */
    double *lon,             /* (O) Longitude */
    double *lat              /* (O) Latitude */
);

#endif
