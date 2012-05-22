/******************************************************************************
NAME                           ISINFOR.C     

PURPOSE:    Integerized Sinusoidal Library Functions - library routines to 
            perform mapping to and from the Integerized Sinusoidal.  These  
            functions perform the mapping from geographic coordinates  
            (longitude/latitude) to the map projection coordinates (x/y).
 
PROGRAMMER                DATE          REASON
----------                ----          ------
Robert Wolfe (STX)        1-2-97        Initial version.
Raj Gejjagaraguppe (ARC)  1-21-97       Modified and added code to make
                                        this work with GCTP software.
Gail Schmidt (SAIC)       11-02         Changed ISIN_ERANGE to GCTP_ERANGE.
 

   Usage Notes:
   1. The following functions are available:  

        isinusforinit - Initialize integerized sinusoidal transformations
        isinusfor     - Forward mapping; converts geographic coordinates 
                        (longitude/latitude) to map projection 
                        coordinates (x/y)

   2. Since there are discontinuities at the top and bottom of each zone 
      within the integerized sinusoidal grid care should be taken when 
      mapping points near the edges of the zones.  Also, care should be taken 
      near the discontinuity at the most eastward and westward portions of 
      the projection (180 degrees from the central meridian).

   3. Latitudes are expected to in the range [-'HALF_PI' to 'HALF_PI'].

   4. Longitudes are expected to be in the range [-'TWO_PI' to 'TWO_PI'].
   
   5. The justify flag is used to indicate what to do with zones with an 
      odd number of columns.  If it has a value of 0 or 1 it indicates the 
      extra column is on the right (zero) or left (one) of the projection 
      y axis.  If the flag is set to 2 the columns are calculated so there 
      are always an even number of column in each zone.
      
   6. The origin is located at the equator which is at the bottom of the first 
      zone above the equator and the top of the first zone below the equator.
      
   7. These routines were designed as an GCTP (General Cartographic
      Transformation Package) interface to the 'isin' library.

*****************************************************************************/

#include <stdlib.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include "cproj.h"
#include "isin.h"

/* #define NO_OUTPUT *//* if defined, error messages are not written */

/* #define CHECK_EDGE *//* if defined, statistics are gathered on how
 * close the column calculations are to being
 * dependent on the machine precision */

static void error( const char *routine, const char *text )
{
#ifndef NO_OUTPUT
    fprintf( stderr, " error (isinusfor.c/%s : %s\n", routine, text );
#endif

/*  exit(EXIT_FAILURE); */
}

/* Error Messages */

static error_t ISIN_BADALLOC = { -3, "memory allocation" };
static error_t ISIN_BADPARAM = { -4, "invalid parameter" };
static error_t ISIN_BADHANDLE = { -5, "invalid handle" };
static error_t ISIN_BADKEY = { -6, "invalid key" };

/* Local data structure for 'Isin' library */

static Isin_t *isin = NULL;

/* Variables common to all subroutines in this code file
  -----------------------------------------------------*/
static double lon_center;       /* Center longitude (projection center) */
static double R;                /* Radius of the earth (sphere) */
static double false_easting;    /* x offset                             */
static double false_northing;   /* y offset                             */
static long zone;               /* number of longitudinal zones */
static int justify;             /* justify flag */

/*
!C******************************************************************************
!Description: isinusforinit (initialize mapping) initializes the integerized 
 sinusoidal transformations.

!Input Parameters:
                   sphere radius (meters)
                   longitude of central meridian (radians)
                   easting at projection origin (meters)
                   northing at projection origin (meters)
                   number of longitudinal zones
                   justify flag; flag to indicate what to do with 
                   rows with an odd number of columns: 
                      0.0 - indicates the extra column is on the right 
                            of the projection y axis;
                      1.0 - indicates the extra column is on the left
                            of the projection y axis;
                      2.0 - calculate an even number of columns

!Output Parameters:
 (none)

!Team Unique Header:

 ! Usage Notes:
   1. The sphere radius must not be smaller than 'EPS_SPHERE'.
   2. The longitude must be in the range [-'TWO_PI' to 'TWO_PI'].
   3. The number of longitudinal zones must be a positive multiple of two 
      and no more than 'NZONE_MAX'.
   4. The number of longitudinal zones and the justify flag must be within 
      'EPS_CNVT' of an integer.

!END****************************************************************************
*/
long isinusforinit
( 
    double sphere, 
    double lon_cen_mer, 
    double false_east,
    double false_north, 
    double dzone, 
    double djustify 
)
{
    long nzone;                 /* Number of longitudinal zones  */
    int ijustify;               /* Justify flag (see above) */
    int istat;                  /* Status returned from 'Isin' functions */

    /* Check to see if this data set was already initialized; if it was, 
     * free the data structure so it can be re-used */
    if ( isin != NULL )
    {
        istat = Isin_for_free( isin );
        if ( istat != ISIN_SUCCESS )
        {
            error( "isinusforinit", "bad return from Isin_for_free" );
            return ISIN_ERROR;
        }
    }

    /* Check the input parameters */
    if ( sphere <= 0.0 )
    {
        error( "isinusforinit", "bad parameter; sphere radius invalid" );
        return ISIN_ERROR;
    }

    if ( lon_cen_mer < -TWO_PI || lon_cen_mer > TWO_PI )
    {
        error( "isinusforinit",
               "bad parameter; longitude of central meridian invalid" );
        return ISIN_ERROR;
    }

    if (dzone < (2.0 - EPS_CNVT) || dzone > ((double)NZONE_MAX + EPS_CNVT))
    {
        error( "isinusforinit", "bad parameter; nzone out of range" );
        return ISIN_ERROR;
    }

    nzone = (long)(dzone + EPS_CNVT);
    if ( fabs( dzone - nzone ) > EPS_CNVT )
    {
        error("isinusforinit","bad parameter; nzone not near an integer value");
        return ISIN_ERROR;
    }

    if ( ( nzone % 2 ) != 0 )
    {
        error( "isinusforinit", "bad parameter; nzone not multiple of two" );
        return ISIN_ERROR;
    }

    if ( djustify < -EPS_CNVT || djustify > ( 2.0 + EPS_CNVT ) )
    {
        error( "isinusforinit", "bad parameter; ijustify out of range" );
        return ISIN_ERROR;
    }

    ijustify = djustify + EPS_CNVT;
    if ( fabs( djustify - ijustify ) > EPS_CNVT )
    {
        error( "isinusforinit",
               "bad parameter; ijustify not near an integer value" );
        return ISIN_ERROR;
    }

    /* Initialize the projection */
    isin = Isin_for_init( sphere, lon_cen_mer, false_east, false_north,
                          nzone, ijustify );
    if ( isin == NULL )
    {
        error( "Isin_for_init", "bad return from Isin_for_init" );
        return ISIN_ERROR;
    }

    return ISIN_SUCCESS;
}

/*
!C******************************************************************************
!Description: Isin_for_init (initialize mapping) initializes the integerized 
 sinusoidal transformations by calculating constants and a short-cut 
 lookup table.

!Input Parameters:
 sphere         sphere radius (user's units)
 lon_cen_mer    longitude of central meridian (radians)
 false_east     easting at projection origin (user's units)
 false_north    northing at projection origin (user's units)
 nrow           number of rows (longitudinal zones)
 ijustify       justify flag; flag to indicate what to do with rows with an 
                odd number of columns; 
                  0 = indicates the extra column is on the right 
                      of the projection y axis;
                  1 = indicates the extra column is on the left
                      of the projection y axis;
                  2 = calculate an even number of columns

!Output Parameters:
 (returns)      a handle for this instance of the integerized sinusoidal 
                projection or NULL for error

!Team Unique Header:

 ! Usage Notes:
   1. The sphere radius must not be smaller than 'EPS_SPHERE'.
   2. The longitude must be in the range [-'TWO_PI' to 'TWO_PI'].
   3. The number of rows must be a multiple of two and no more than 'NROW_MAX'.

!END****************************************************************************
*/
Isin_t *Isin_for_init
(
    double sphere,
    double lon_cen_mer,
    double false_east, 
    double false_north,
    long nrow, 
    int ijustify 
)
{
    Isin_t *this;           /* 'isin' data structure */
    Isin_row_t *row;        /* current row data structure */
    long irow;              /* row (zone) index */
    double clat;            /* central latitude of the row */
    long ncol_cen;          /* number of columns in the central row of the grid
                               (at the equator) */

#ifdef CHECK_EDGE
    double dcol;            /* delta column (normalized by number of columns) */
    double dcol_min,        /* minimum delta column */
    double log2_dcol_min;   /* log base 2 of minimum delta column */

    dcol_min = 1.0;
#endif

    /* Check input parameters */
    if ( sphere < EPS_SPHERE )
    {
        Isin_error( &ISIN_BADPARAM, "Isin_for_init" );
        return NULL;
    }

    if ( lon_cen_mer < -TWO_PI || lon_cen_mer > TWO_PI )
    {
        Isin_error( &ISIN_BADPARAM, "Isin_for_init" );
        return NULL;
    }
    if ( lon_cen_mer < PI )
        lon_cen_mer += TWO_PI;
    if ( lon_cen_mer >= PI )
        lon_cen_mer -= TWO_PI;

    if ( nrow < 2 || nrow > NROW_MAX )
    {
        Isin_error( &ISIN_BADPARAM, "Isin_for_init" );
        return NULL;
    }
    if ( ( nrow % 2 ) != 0 )
    {
        Isin_error( &ISIN_BADPARAM, "Isin_for_init" );
        return NULL;
    }

    if ( ijustify < 0 || ijustify > 2 )
    {
        Isin_error( &ISIN_BADPARAM, "Isin_for_init" );
        return NULL;
    }

    /* Allocate 'isin' data structure */
    this = ( Isin_t * ) malloc( sizeof( Isin_t ) );
    if ( this == NULL )
    {
        Isin_error( &ISIN_BADALLOC, "Isin_for_init" );
        return NULL;
    }

    /* Place parameters in static storage for common use
       -------------------------------------------------*/
    R = sphere;
    lon_center = lon_cen_mer;
    false_easting = false_east;
    false_northing = false_north;
    zone = nrow;
    justify = ijustify;

    /* Report parameters to the user
       -----------------------------*/
    ptitle("INTEGERIZED SINUSOIDAL");
    radius(sphere);
    cenlon(lon_cen_mer);
    offsetp(false_east,false_north);
    genrpt_long(nrow, "Number of Latitudinal Zones:    ");
    genrpt(ijustify, "Right Justify Columns Flag:    ");

    /* Initialize data structure */
    this->key = ( long ) NULL;
    this->false_east = false_east;
    this->false_north = false_north;
    this->sphere = sphere;
    this->sphere_inv = 1.0 / sphere;
    this->ang_size_inv = ( ( double ) nrow ) / PI;
    this->nrow = nrow;
    this->nrow_half = nrow / 2;
    this->lon_cen_mer = lon_cen_mer;
    this->ref_lon = lon_cen_mer - PI;
    if ( this->ref_lon < -PI )
        this->ref_lon += TWO_PI;
    this->ijustify = ijustify;

    /* Allocate space for information about each row */
    this->row = (Isin_row_t *)malloc(this->nrow_half * sizeof(Isin_row_t));
    if ( this->row == NULL )
    {
        free( this );
        Isin_error( &ISIN_BADALLOC, "Isin_for_init" );
        return NULL;
    }

    /* Do calculations for each row; calculations are only done for half
     * the rows because of the symmetry between the rows above the 
     * equator and the ones below */
    row = this->row;
    for ( irow = 0; irow < this->nrow_half; irow++, row++ )
    {

        /* Calculate latitude at center of row */
        clat = HALF_PI * ( 1.0 - ( ( double ) irow + 0.5 ) / this->nrow_half );

        /* Calculate number of columns per row */
        if ( ijustify < 2 )
            row->ncol = (long)((2.0 * cos(clat) * nrow) + 0.5);
        else
        {
            /* make the number of columns even */
            row->ncol = (long)((cos(clat) * nrow) + 0.5);
            row->ncol *= 2;
        }

#ifdef CHECK_EDGE
        /* Check to be sure the are no less then three columns per row and that 
         * there are exactly three columns at the poles */
        if ( ijustify < 2 )
        {
            if ( row->ncol < 3 || ( irow == 0 && row->ncol != 3 ) )
                printf( "  irow = %d  ncol = %d\n", irow, row->ncol );
        }
        else
        {
            if ( row->ncol < 6 || ( irow == 0 && row->ncol != 6 ) )
                printf( "  irow = %d  ncol = %d\n", irow, row->ncol );
        }
#endif

        /* Must have at least one column */
        if ( row->ncol < 1 )
            row->ncol = 1;

#ifdef CHECK_EDGE

        /* Calculate the minimum delta column (normalized by the number of
         * columns in the row) */
        if ( ijustify < 2 )
            dcol = fabs( ( 2.0 * cos( clat ) * nrow ) + 0.5 - row->ncol );
        else
            dcol = 2.0 * fabs((cos(clat) * nrow) + 0.5 - (row->ncol/2));
        dcol = dcol / row->ncol;
        if ( dcol < dcol_min )
            dcol_min = dcol;

        if ( ijustify < 2 )
        {
            dcol = fabs((2.0 * cos(clat) * nrow) + 0.5 - (row->ncol + 1));
            dcol = dcol / ( row->ncol + 1 );
        }
        else
        {
            dcol = 2.0 * fabs((cos(clat) * nrow) + 0.5 - ((row->ncol/2) + 1));
            dcol = dcol / ( row->ncol + 2 );
        }
        if ( dcol < dcol_min )
            dcol_min = dcol;
#endif

        /* Save the inverse of the number of columns */
        row->ncol_inv = 1.0 / ( ( double ) row->ncol );

        /* Calculate the column number of the column whose left edge touches 
           the central meridian */
        if ( ijustify == 1 )
            row->icol_cen = ( row->ncol + 1 ) / 2;
        else
            row->icol_cen = row->ncol / 2;

    }                           /* for (irow... */

    /* Get the number of columns at the equator */
    ncol_cen = this->row[this->nrow_half - 1].ncol;

#ifdef CHECK_EDGE

    /* Print the minimum delta column and its base 2 log */
    log2_dcol_min = log( dcol_min ) / log( 2.0 );
    printf( "  dcol_min = %g  log2_dcol_min = %g\n", dcol_min, log2_dcol_min );

    /* Check to be sure the number of columns at the equator is twice the 
     * number of rows */
    if ( ncol_cen != nrow * 2 )
        printf( " ncol_cen = %d  nrow = %d\n", ncol_cen, nrow );
#endif

    /* Calculate the distance at the equator between 
     * the centers of two columns (and the inverse) */
    this->col_dist = ( TWO_PI * sphere ) / ncol_cen;
    this->col_dist_inv = ncol_cen / ( TWO_PI * sphere );

    /* Give the data structure a valid key */

    this->key = ISIN_KEY;

    /* All done */
    return this;
}

/*
!C******************************************************************************
!Description: isinusfor (forward mapping) converts geographic
 coordinates ('lon', 'lat') to map projection coordinates ('x', 'y').
 
!Input Parameters:
 lon            longitude (radians)
 lat            latitude (radians)
 
!Output Parameters:
 x              easting in map projection (same units as 'sphere')
 y              northing in map projection (same units as 'sphere')
 
!Team Unique Header:
 
 ! Usage Notes:
   1. 'isinusforinit' must have been previously called.
   2. The longitude must be in the range [-'TWO_PI' to 'TWO_PI'].
   3. The latitude must be in the range [-'HALF_PI' to 'HALF_PI'].
 
!END****************************************************************************
*/
long isinusfor
(
    double lon, 
    double lat, 
    double *x, 
    double *y 
)
{
    int istat;                  /* Status returned from 'Isin_fwd' function */

    istat = Isin_fwd( isin, lon, lat, x, y );
    if ( istat != ISIN_SUCCESS )
    {
        error( "isinusfor", "bad return from Isin_fwd" );
        return ISIN_ERROR;
    }

    return ISIN_SUCCESS;
}

/*
!C******************************************************************************
!Description: Isin_fwd (forward mapping) converts geographic
 coordinates ('lon', 'lat') to map projection coordinates ('x', 'y').

!Input Parameters:
 this           handle for this instance of the integerized sinusoidal 
                projection
 lon            longitude (radians)
 lat            latitude (radians)

!Output Parameters:
 x              easting in map projection (same units as 'sphere')
 y              northing in map projection (same units as 'sphere')
 (returns)      status:
                  ISIN_SUCCESS - normal return
                  GCTP_ERANGE - longitude or latitude not in range
                  ISIN_ERROR - error return

!Team Unique Header:

 ! Usage Notes:
   1. 'Isin_for_init' must have been previously called for the handle.
   2. The longitude must be in the range [-'TWO_PI' to 'TWO_PI'].
   3. The latitude must be in the range [-'HALF_PI' to 'HALF_PI'].

!END****************************************************************************
*/
int Isin_fwd
(
    const Isin_t *this, 
    double lon, 
    double lat, 
    double *x, 
    double *y 
)
{
    double row, col;            /* Row (zone) and column; column is relative
                                   to central; 0.5 is the center of a row or
                                   column */
    double flon;                /* Fractional longitude (multiples of PI) */
    long irow;                  /* Integer row (zone) number */

    /* make sure the longitude is between +/- PI radians */
    lon = adjust_lon(lon);

    /* Check input parameters */
    *x = 0.0;
    *y = 0.0;

    if ( this == NULL )
        return Isin_error( &ISIN_BADHANDLE, "Isin_fwd" );
    if ( this->key != ISIN_KEY )
        return Isin_error( &ISIN_BADKEY, "Isin_fwd" );
    if ( lon < -TWO_PI || lon > TWO_PI )
        return GCTP_ERANGE;
    if ( lat < -HALF_PI || lat > HALF_PI )
        return GCTP_ERANGE;

    /* Northing */
    *y = this->false_north + ( lat * this->sphere );

    /* Integer row number */
    row = ( HALF_PI - lat ) * this->ang_size_inv;
    irow = (long)row;
    if ( irow >= this->nrow_half )
        irow = ( this->nrow - 1 ) - irow;
    if ( irow < 0 )
        irow = 0;

    /* Fractional longitude */
    flon = ( lon - this->ref_lon ) * TWOPI_INV;
    if ( flon < 0.0 )
        flon += ( 1 - ( long ) flon );
    if ( flon > 1.0 )
        flon -= ( long ) flon;

    /* Column number (relative to center) */
    col = ( this->row[irow].ncol * flon ) - this->row[irow].icol_cen;

    /* Easting */
    *x = this->false_east + ( this->col_dist * col );

    return ISIN_SUCCESS;
}

/*
!C******************************************************************************
!Description: Isin_for_free (free) deallocates the 'isin' data structure and
 array memory.

!Input Parameters:
 this           handle for this instance of the integerized sinusoidal 
                projection
!Output Parameters:
 (returns)      status:
                  ISIN_SUCCESS - normal return
                  ISIN_ERROR - error return

!Team Unique Header:

 ! Usage Notes:
   1. 'Isin_for_init' must have been previously called for the handle.

!END****************************************************************************
*/
int Isin_for_free
( 
    Isin_t * this 
)
{
    if ( this == NULL )
        return Isin_error( &ISIN_BADHANDLE, "Isin_for_free" );
    if ( this->key != ISIN_KEY )
        return Isin_error( &ISIN_BADKEY, "Isin_for_free" );

    /* Set the key to NULL */
    this->key = ( long ) NULL;

    /* Free the memory */
    free( this->row );
    this->row = NULL;
    free( this );
    this = NULL;

    return ISIN_SUCCESS;
}
