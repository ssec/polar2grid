#ifndef ISIN_H
#define ISIN_H

/******************************************************************************
NAME                                ISIN.H

PURPOSE:    Integerized Sinusoidal Library Header - constants, data 
            structures and prototypes for integerized sinusoidal library 
            functions.

PROGRAMMER                DATE          REASON
----------                ----          ------
Robert Wolfe (STX)        1-2-97        Initial version.
Raj Gejjagaraguppe (ARC)  1-15-97       Modified the code to work with
                                        GCTP software.
 
D*****************************************************************************/

#include "cproj.h"

/* Status returned */
#define ISIN_SUCCESS 0          /* Successful return */
#define ISIN_ERROR -1           /* Error return */

/* ISIN related defines */
#define TWOPI_INV  (1.0 / (2.0 * PI))
#define NROW_MAX  (360 * 3600)  /* Maximum number of rows (zones) */
#define NZONE_MAX (360 * 3600)  /* Maximum number of longitudinal zones */
#define EPS_SPHERE (1.0e-10)    /* Minimum sphere radius */
#define EPS_CNVT 0.01           /* Doubles must be within this of an integer 
                                   to be valid */
#define ISIN_KEY 212589603      /* Key to verify correct data structure */

/* Data Structures */

/* Row Type; Information for Eash Row (longitudinal band) in Projection */
typedef struct
{
    long ncol;                  /* Number of columns */
    long icol_cen;              /* Column number to left of center of grid */
    double ncol_inv;            /* Number of columns inverse */
}
Isin_row_t;

/* Handle Type; Values assigned in 'Isin_init' */
typedef struct
{
    double false_east;          /* Northing at projection origin */
    double false_north;         /* Easting at projection origin */
    double sphere;              /* Sphere radius (user's units) */
    double sphere_inv;          /* Sphere radius inverse (user's units) */
    double ang_size_inv;        /* Grid angular resolution inverse (1/rad) */
    long nrow;                  /* Number of rows (longitudinal zones) */
    long nrow_half;             /* Half of number of rows(longitudinal zones) */
    double ref_lon;             /* Zero reference longitude (rad) */
    double lon_cen_mer;         /* Longitude of central meridian (rad) */
    int ijustify;               /* Justify flag (see Isin_init) */
    double col_dist;            /* Distance for one column in projection 
                                 * (user's units) */
    double col_dist_inv;        /* Distance for one column in projection inverse
                                 * (user's units) */
    Isin_row_t *row;            /* Row data structure */
    long key;                   /* Data structure key */
}
Isin_t;

/* Error Structure */
typedef struct
{
    int num;                    /* Error number */
    char *str;                  /* Error message */
}
error_t;

/* Initialize integerized sinusoidal forward transformations */
long isinusforinit
( 
    double sphere, 
    double lon_cen_mer, 
    double false_east,
    double false_north, 
    double dzone, 
    double djustify 
);

Isin_t *Isin_for_init
(
    double sphere,
    double lon_cen_mer,
    double false_east, 
    double false_north,
    long nrow, 
    int ijustify 
);

/* Initialize integerized sinusoidal inverse transformations */
long isinusinvinit
( 
    double sphere, 
    double lon_cen_mer, 
    double false_east,
    double false_north, 
    double dzone, 
    double djustify 
);

Isin_t *Isin_inv_init
( 
    double sphere,
    double lon_cen_mer,
    double false_east, 
    double false_north,
    long nrow, 
    int ijustify 
);

/* Forward mapping; converts geographic coordinates ('lon', 'lat')
 * to map projection coordinates ('x', 'y') */
long isinusfor
(
    double lon, 
    double lat, 
    double *x, 
    double *y 
);

int Isin_fwd
(
    const Isin_t * this, 
    double lon, 
    double lat, 
    double *x, 
    double *y 
);

/* Inverse mapping; converts map projection coordinates ('x', 'y') to
 * geographic coordinates ('lon', 'lat') */
long isinusinv( double, double, double *, double * );
int Isin_inv( const Isin_t *, double, double, double *, double * );

/* Deallocate the 'isin' data structure and array memory */
int Isin_for_free
( 
    Isin_t * this 
);

int Isin_inv_free
( 
    Isin_t * this 
);

/* Function to handle errors */
int Isin_error
(
    const error_t *err,
    const char *routine
);

#endif
