/*========================================================================
 * irregrid - interpolate irregularly spaced lat/lon data to a grid.
 *
 * 27-Apr-1999 Derek van Westrum vanwestr@ingrid.colorado.edu 303-492-1846
 * 18-Jan-2004 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1999-2004 University of Colorado
 *========================================================================*/
static const char irregrid_c_rcsid[] = "$Id: irregrid.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "matrix.h"
#include "mapx.h"
#include "grids.h"
#include "maps.h"

#define usage									\
"$Revision: 16072 $\n"								\
"usage: irregrid [-wcdnv -i value -k kernel\n"					\
" -p value -r value -z beta_file -o outputfile\n"				\
" -t total_pts_file]  from_data to.gpd \n"					\
"\n"										\
" input : from_data - original ASCII data file (lat lon value)\n"		\
"         to.gpd    - new grid parameters definition file\n"			\
"         [to_data] - if -z option then use as initial values\n"		\
"\n"										\
" output: grid values (float) by row to stdout or optional outputfile\n"	\
"\n"										\
" options:c - Cressman weighting (default)\n"                                   \
"         d - drop in the bucket weighted\n"                                    \
"         w - inverse distance weighted sum\n"					\
"                 -p the power of the distance weight\n"			\
"         n - nearest neighbor weighted sum\n"					\
"         r - specify the search radius (units: grid cells, default: 0.)\n"	\
"         i value - ignore fill value.  Output is filled with this value\n"	\
"                   If not specified, then filled with zero.\n"			\
"         z beta_file - not yet implemented! save/restore intermediate\n"	\
"                       results\n"						\
"         t total_pts_file - name of file to write number of input\n"		\
"                            data points contributing to each grid cell\n"	\
"         v - verbose (can be repeated)\n"					\
"\n"										\
"\n"

/*------------------------------------------------------------------------
 *
 * This is a routine to grid irregularly spaced data.  Details XXXX
 *
 * The -z beta_file option XXXX
 *
 *------------------------------------------------------------------------*/

#define VV_INTERVAL 30
#define MAXLINELENGTH 1000
#define IMPOSSIBLY_LARGE 9e9;

static float fill;
static int fill_specified, verbose, preload_data, min_in_pts;
static double shell_radius;
static double inv_dist_power;

/* 
 * weighted_average is a pointer to one the various weighted average
 * routines (whose prototypes follow...
 */ 
static int (*init_grids)(grid_class*,float **,float **);
static int (*weighted_average)(double,double,double,double,float,int *,
			       grid_class *,float **,float **,int **);
static int (*normalize_result)(grid_class *,float **,float **,int **);

static int init_cressman(grid_class *,float **,float **);
static int cressman(double,double,double,double,float,int *,
		    grid_class *,float **,float **,int **);
static int normalize_cressman(grid_class *,float **, float **, int **);

static int init_drop_in_bucket(grid_class *,float **,float **);
static int drop_in_bucket(double,double,double,double,float,int *,
			 grid_class *,float **,float **,int **);
static int normalize_drop_in_bucket(grid_class *,float **, float **, int **);

static int init_inv_dist(grid_class *,float **,float **);
static int inv_dist(double,double,double,double,float,int *,
		    grid_class *,float **,float **,int **);
static int normalize_inv_dist(grid_class *,float **, float **, int **);

static int init_near_neighbor(grid_class *,float **,float **);
static int near_neighbor(double,double,double,double,float,int *,
			 grid_class *,float **,float **,int **);
static int normalize_near_neighbor(grid_class *,float **, float **, int **);

main(int argc, char *argv[]) { 
  int i, status;
  double from_lat, from_lon;
  float from_dat;
  int r_width, s_width,nearest_r, nearest_s;
  double from_r, from_s;
  int shell_range[4];
  float **to_data, **to_data_beta;
  grid_class *to_grid;
  int **to_data_num_pts;
  char *option;
  char input_line[MAXLINELENGTH];
  char from_filename[FILENAME_MAX], to_filename[FILENAME_MAX];
  char npts_filename[FILENAME_MAX];
  bool algo_specified;
  char *algo_string;
  char beta_filename[FILENAME_MAX];
  FILE *from_file, *to_file, *beta_file, *npts_file;
  int lines_processed;

/*
 * set defaults
 */
  to_file = stdout;
  beta_file = NULL;
  npts_file = NULL;
  preload_data = FALSE;
  algo_specified = FALSE;
  weighted_average = cressman;
  normalize_result = normalize_cressman;
  init_grids = init_cressman;
  fill_specified = FALSE;
  fill = 0.;
  verbose = 0;
  shell_radius = 0.;
  inv_dist_power = 2.;
  algo_string = "Cressman weighting";

/* 
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'w':
	  weighted_average = inv_dist;
          normalize_result = normalize_inv_dist;
	  init_grids = init_inv_dist;
	  algo_specified = TRUE;
	  algo_string = "Inverse distance weighting";
	  break;
	case 'p':
	  ++argv; --argc;
	  if (sscanf(*argv, "%lf", &inv_dist_power) != 1) error_exit(usage);
	  break;
	case 'c':
	  weighted_average = cressman;
	  normalize_result = normalize_cressman;
	  init_grids = init_cressman;
	  min_in_pts = 1;
	  algo_specified = TRUE;
	  algo_string = "Cressman weighting";
	  break;
	case 'd':
	  weighted_average = drop_in_bucket;
	  normalize_result = normalize_drop_in_bucket;
	  init_grids = init_drop_in_bucket;
	  algo_specified = TRUE;
	  algo_string = "Drop in the bucket";
	  break;
	case 'r':
	  ++argv; --argc;
	  if (sscanf(*argv, "%lf", &shell_radius) != 1) error_exit(usage);
	  break;
	case 'n':
	  weighted_average = near_neighbor;
	  normalize_result = normalize_near_neighbor;
	  init_grids = init_near_neighbor;
	  algo_specified = TRUE;
	  algo_string = "Nearest neighbor";
	  break;
	case 'o':
  	  ++argv; --argc;
	  if (sscanf(*argv, "%s", to_filename) != 1) error_exit(usage);
	  strcpy(to_filename, *argv);
	  to_file = fopen(to_filename, preload_data ? "r+" : "w");
	  if (!to_file) { perror(to_filename); exit(ABORT); }
	  break;
	case 'z':
	  ++argv; --argc;
	  fprintf(stderr," Input beta file option not yet implemented.\n");
	  error_exit(usage);
	  /* but someday it will, so leave the rest of this code here... */
	  strcpy(beta_filename, *argv);
	  preload_data = TRUE;
	  beta_file = fopen(beta_filename, "r+");
	  if (!beta_file)
	  { preload_data = FALSE;
	    beta_file = fopen(beta_filename, "w");
	    if (!beta_file) { perror(beta_filename); error_exit(usage); }
	  }
	  break;
	case 't':
	  ++argv; --argc;
	  strcpy(npts_filename, *argv);
	  npts_file = fopen(npts_filename, "w");
	  if (!npts_file) { perror(npts_filename); error_exit(usage); }
	  break;
	case 'i':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &fill) != 1) error_exit(usage);
	  fill_specified = TRUE;
	  break;
	case 'v':
	  ++verbose;
	  break;
	case 'V':
	  fprintf(stderr,"%s\n", irregrid_c_rcsid);
	  break;
	default:
	  fprintf(stderr,"invalid option %c\n", *option);
	  error_exit(usage);
      }
    }
  }

/*
 *	get command line arguments
 */
  if (argc != 2) error_exit(usage);
  
  strcpy(from_filename, *argv);
  from_file = fopen(from_filename, "r");
  if (!from_file) { perror(from_filename); exit(ABORT); }
  ++argv; --argc;
  
  to_grid = init_grid(*argv);
  if (!to_grid) exit(ABORT);
  ++argv; --argc;
  
/*
 *	Remind the user of defaults and settings...
 */
  if (verbose) {
    fprintf(stderr,"> Input file:\t\t%s\n", from_filename);
    fprintf(stderr,"> Output file:\t\t%s\n", to_filename);
    fprintf(stderr,"> To grid (.gpd) file:\t%s\n",
	    to_grid->gpd_filename);
    if (!algo_specified) {
      fprintf(stderr,"> No weighting algorithm specified.\tUsing Cressman...\n");
    } else {
      fprintf(stderr,"> Algorithm:\t\t%s\n",algo_string);
    }
    if (!fill_specified) {
      fprintf(stderr,"> No fill value specified.\t\tUsing 0.0.\n");
    } else {
      fprintf(stderr,"> Fill value:\t\t%7.2f\n",fill);
    }
    fprintf(stderr,"> Shell radius:\t\t%5.2f\n",shell_radius);
  }

/*
 *	allocate storage for  to_data grids
 */
  to_data = (float **)matrix(to_grid->rows, to_grid->cols,
			      sizeof(float), TRUE);
  if (!to_data) { exit(ABORT); }

  to_data_beta = (float **)matrix(to_grid->rows, to_grid->cols,
			      sizeof(float), TRUE);
  if (!to_data_beta) { exit(ABORT); }

  to_data_num_pts = (int **)matrix(to_grid->rows, to_grid->cols,
			      sizeof(int), TRUE);
  if (!to_data_num_pts) { exit(ABORT); }

/*
 *	initialize output grids
 */
 init_grids(to_grid,to_data,to_data_beta);
/*
 *	given shell radius, calculate a comfortable grid point range to
 *	encompass it.  for now radius units are grid points
 */
  r_width = (int)(2.*shell_radius);
  s_width = (int)(2.*shell_radius);

/*
 *	read location and data values from from_file one line at a time...
 */
  lines_processed = 0;
  while (fgets(input_line, MAXLINELENGTH, from_file) != NULL) {
    if (feof(from_file)) break;
    lines_processed++;
    status = sscanf(input_line,"%lf%lf%f",&from_lat,&from_lon,&from_dat);
    if (3!=status) {
      fprintf(stderr,"> Problem reading data at line %i\n",lines_processed);
    }

    if (!within_mapx(to_grid->mapx, from_lat, from_lon)) continue;
/*
 *	find the nearest grid position of this lat/lon and range of grid
 *	points around it.  
 *
 *      Note that, fortunately, "forward_grid" happily returns grid values
 *      that are off the grid (ie, negative or greater than the number of
 *      rows or columns). We want these positions because they might
 *      contribute to the weights for points that are on the grid.  So, we
 *      don't bother testing the forward_grid return status... 
 */
    forward_grid(to_grid, from_lat, from_lon, &from_r, &from_s);
    
    nearest_r = (int)(from_r + 0.5);
    nearest_s = (int)(from_s + 0.5);
    shell_range[0] = nearest_r - r_width;  /* min_r */
    shell_range[1] = nearest_r + r_width;  /* max_r */
    shell_range[2] = nearest_s - s_width;  /* min_s */
    shell_range[3] = nearest_s + s_width;  /* max_s */

/*
 *	if from_dat is not a fill value, call the weighting routine to
 *	increment the weights for grid points near this lat/lon.  
 */
    if (from_dat != fill) {
      weighted_average(from_r,from_s,from_lat,from_lon,
			  from_dat,shell_range,to_grid,to_data,
			  to_data_beta,to_data_num_pts);
    }
  }  /* End of loop over input lat/lons */
  fclose(from_file);

/*
 *	normalize result
 */
  normalize_result(to_grid,to_data,to_data_beta,to_data_num_pts);

/*
 *	write out result
 */
  for (i = 0; i < to_grid->rows; i++){
    status = fwrite(to_data[i],sizeof(float),to_grid->cols,to_file);
    if (status < to_grid->cols) {
      perror(to_filename);
      error_exit("irregrid: error writing grid data: ABORTING\n");
    }
  }
  fclose(to_file);
  
/*
 *	write out total points file
 */
  if (npts_file) {
    for (i = 0; i < to_grid->rows; i++){
      status = fwrite(to_data_num_pts[i], sizeof(int), to_grid->cols, npts_file);
      if (status < to_grid->cols) {
	perror(npts_filename);
	error_exit("irregrid: error writing total points data: ABORTING\n");
      }
    }
    fclose(to_file);
  }

  exit(EXIT_SUCCESS);
}  /*  end of main */

/*------------------------------------------------------------------------
 * Initialize (fill) grids for Cressman weighting.  Because cressman is a
 * ratio of Sum(data*weights) over Sum(weights), initialize each to zero.
 *
 *	input : to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *
 *	output : to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *
 *	result: number of points initialized
 *
 *------------------------------------------------------------------------*/
int init_cressman(grid_class *to_grid,float **to_data,float **to_data_beta)
{ int r, s, npts;
 
 npts = 0; 
 for (r = 0; r < to_grid->cols; r++) {
   for (s = 0; s < to_grid->rows; s++) {
     to_data[s][r] = 0.;
     to_data_beta[s][r] = 0.;
     npts++;
   }
 }
 return npts;
}

/*------------------------------------------------------------------------
 * Cressman interpolation algorithm.  Ref. XXXX
 *
 *	input : from_r, from_s, (the input data location)
 *              shell_range (the min and max of the search area 
 *                          on the output grid).
 *
 *	output: to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *              to_data_num_pts.
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int cressman(double from_r,double from_s,double from_lat, double from_lon,
	     float from_dat,int shell_range[],
	     grid_class *to_grid,float **to_data,float **to_data_beta,
	     int **to_data_num_pts)
{ int r, s;
  double dist;
  double weight;
  int npts=0;

/*
 *	find the distance from each grid location within the shell range
 *	of r and s (the from_location).  
 */
  for (r = shell_range[0]; r <= shell_range[1]; r++) {
    for (s = shell_range[2]; s <= shell_range[3]; s++) {
/*
 *	make sure that while stepping through the grid points we are
 *	within the grid boundaries... 
 */
      if (r >= 0 && s >= 0 && r < to_grid->cols 
	  && s < to_grid->rows) {
	dist = sqrt((from_r - r) * (from_r - r) 
		    + (from_s - s) * (from_s - s));
/*
 *	If within the shell distance increment the weights and counters...  
 */
	if (dist <= shell_radius) {
	  weight = (shell_radius * shell_radius - dist * dist)
	    /(shell_radius * shell_radius + dist * dist);
	  to_data[s][r] += from_dat * weight;
	  to_data_beta[s][r] += weight;
	  to_data_num_pts[s][r]++;
	}
	++npts;
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * Cressman normalization.  
 *
 *	input : to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *              to_data_num_pts
 *
 *      output: to_data
 *
 *	result: number of valid points normalized
 *
 *------------------------------------------------------------------------*/
int normalize_cressman(grid_class *to_grid,float **to_data,float **to_data_beta,
		       int **to_data_num_pts)
{
  int r, s;
  int npts=0;

  for (r = 0; r < to_grid->cols; r++) {
    for (s = 0; s < to_grid->rows; s++) {
      if (to_data_beta[s][r] != 0. && min_in_pts <= to_data_num_pts[s][r]) {
	to_data[s][r] = to_data[s][r]/to_data_beta[s][r];
	npts++;
      } else {
	to_data[s][r] = fill;
      }
    }
  }
  return npts;
}

/*------------------------------------------------------------------------
 * Initialize grids for drop in the bucket calculation.
 *
 *	input : to_data, (numerator: sum at grid point [r,s])
 *
 *	output : to_data, (numerator: sum of data)
 *
 *	result: number of points initialized
 *
 *------------------------------------------------------------------------*/
int init_drop_in_bucket(grid_class *to_grid,float **to_data,float **to_data_beta)
{ int r, s, npts;
 
 npts = 0; 
 for (r = 0; r < to_grid->cols; r++) {
   for (s = 0; s < to_grid->rows; s++) {
     to_data[s][r] = 0;
     npts++;
   }
 }
 return npts;
}

/*------------------------------------------------------------------------
 * Drop in the bucket algorithm.  Note this only calculates the drop in the
 * bucket value for grid locations that are within the "shell_range" of
 * each input point.
 *
 *	input : from_r, from_s, (the input data location)
 *              shell_range (the min and max of the search area 
 *                          on the output grid).
 *
 *	output: to_data, (numerator: sum of data values)
 *              to_data_num_pts, (denominator: number of points)
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int drop_in_bucket(double from_r,double from_s,double from_lat, double from_lon,
		   float from_dat,int shell_range[],
		   grid_class *to_grid,float **to_data,float **to_data_beta,
		   int **to_data_num_pts)
{ int r, s;
 int r_target, s_target;
 int npts=0;

/*
 *	use each grid location within the shell range
 *	of r and s (the from_location).  
 */
  for (r = shell_range[0]; r <= shell_range[1]; r++) {
    for (s = shell_range[2]; s <= shell_range[3]; s++) {
/*
 *	make sure that while stepping through the grid points we are
 *	within the grid boundaries... 
 */
      if (r >= 0 && s >= 0 && r < to_grid->cols 
	  && s < to_grid->rows) {
/*
 *	add the data to the sum and increment the point count 
 */
	to_data[s][r] += from_dat;
	to_data_num_pts[s][r]++;
	++npts;
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * Drop in the bucket normalization.
 *
 *	input : to_data
 *              to_data_num_pts
 *
 *      output: to_data
 *
 *	result: number of valid points normalized
 *
 *------------------------------------------------------------------------*/
int normalize_drop_in_bucket(grid_class *to_grid,float **to_data,
			     float **to_data_beta,
			     int **to_data_num_pts)
{
  int r, s;
  int npts=0;

  for (r = 0; r < to_grid->cols; r++) {
    for (s = 0; s < to_grid->rows; s++) {
      if (to_data_num_pts[s][r] != 0.) {
	to_data[s][r] = to_data[s][r]/to_data_num_pts[s][r];
	npts++;
      } else {
	to_data[s][r] = fill;
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * Initialize (fill) grids for Inverse distance weighting.  Because
 * this is a ratio of Sum(data*weights) over Sum(weights), initialize
 * each to zero.
 *
 *	input : to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *
 *	output : to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *
 *	result: number of points initialized
 *
 *------------------------------------------------------------------------*/
int init_inv_dist(grid_class *to_grid,float **to_data,float **to_data_beta)
{ int r, s, npts;
 
 npts = 0; 
 for (r = 0; r < to_grid->cols; r++) {
   for (s = 0; s < to_grid->rows; s++) {
     to_data[s][r] = 0.;
     to_data_beta[s][r] = 0.;
     npts++;
   }
 }
 return npts;
}

/*------------------------------------------------------------------------
 * Inverse distance interpolation algorithm.  Note this only calculates
 * weights for grid locations that are within the "shell_range" of each
 * input point.
 *
 *	input : from_r, from_s, (the input data location)
 *              shell_range (the min and max of the search area 
 *                          on the output grid).
 *
 *	output: to_data, , (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *              to_data_num_pts.
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int inv_dist(double from_r,double from_s,double from_lat, double from_lon,
	     float from_dat,int shell_range[],
	     grid_class *to_grid,float **to_data,float **to_data_beta,
	     int **to_data_num_pts)
{ int r, s;
  double dist;
  double weight;
  int npts=0;

/*
 *	find the distance from each grid location within the shell range
 *	of r and s (the from_location).  
 */
  for (r = shell_range[0]; r <= shell_range[1]; r++) {
    for (s = shell_range[2]; s <= shell_range[3]; s++) {
/*
 *	make sure that while stepping through the grid points we are
 *	within the grid boundaries... 
 */
      if (r >= 0 && s >= 0 && r < to_grid->cols 
	  && s < to_grid->rows) {
	dist = sqrt((from_r - r) * (from_r - r) 
		    + (from_s - s) * (from_s - s));
/*
 *	if within the search radius, increment the weights and counters...  
 */
	if (dist <= shell_radius) {
	  weight = pow(dist,inv_dist_power);
	  weight = weight > 0 ? 1/weight : fill;
	  to_data[s][r] += from_dat * weight;
	  to_data_beta[s][r] += weight;
	  to_data_num_pts[s][r]++;
	  ++npts;
	}
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * Inverse distance normalization.
 *
 *	input : to_data, (numerator:  sum of data*weights)
 *              to_data_beta,  (denominator: sum of weights)
 *              to_data_num_pts
 *
 *      output: to_data
 *
 *	result: number of valid points normalized
 *
 *------------------------------------------------------------------------*/
int normalize_inv_dist(grid_class *to_grid,float **to_data,float **to_data_beta,
		       int **to_data_num_pts)
{
  int r, s;
  int npts=0;

  for (r = 0; r < to_grid->cols; r++) {
    for (s = 0; s < to_grid->rows; s++) {
      if (to_data_beta[s][r] != 0.) {
	to_data[s][r] = to_data[s][r]/to_data_beta[s][r];
	npts++;
      } else {
	to_data[s][r] = fill;
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * Initialize (fill) grids for nearest neighbor calculation.  Because we
 * need to keep track of the minimum distance, it can't start at zero.
 * Set to IMPOSSIBLY_LARGE.
 *
 *	input : to_data, (current value at grid point [r,s])
 *              to_data_beta,  (current min_distance at grid point)
 *
 *	output : to_data, (current value at grid point [r,s])
 *              to_data_beta,  (current min_distance at grid point)
 *
 *	result: number of points initialized
 *
 *------------------------------------------------------------------------*/
int init_near_neighbor(grid_class *to_grid,float **to_data,float **to_data_beta)
{ int r, s, npts;
 
 npts = 0; 
 for (r = 0; r < to_grid->cols; r++) {
   for (s = 0; s < to_grid->rows; s++) {
     to_data[s][r] = fill;
     to_data_beta[s][r] = IMPOSSIBLY_LARGE;
     npts++;
   }
 }
 return npts;
}

/*------------------------------------------------------------------------
 * Nearest neighbor algorithm.  Note this only calculates the nearest
 * neighbor value for grid locations that are within the "shell_range" of
 * each input point.
 *
 *	input : from_r, from_s, (the input data location)
 *              shell_range (the min and max of the search area 
 *                          on the output grid).
 *
 *	output: to_data, (current value at grid point [r,s])
 *              to_data_beta,  (current min_distance at grid point)
 *              to_data_num_pts.
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int near_neighbor(double from_r,double from_s,double from_lat, double from_lon,
		  float from_dat,int shell_range[],
		  grid_class *to_grid,float **to_data,float **to_data_beta,
		  int **to_data_num_pts)
{ int r, s;
  double dist;
  int npts=0;

/*
 *	find the distance from each grid location within the shell range
 *	of r and s (the from_location).  
 */
  for (r = shell_range[0]; r <= shell_range[1]; r++) {
    for (s = shell_range[2]; s <= shell_range[3]; s++) {
/*
 *	make sure that while stepping through the grid points we are
 *	within the grid boundaries... 
 */
      if (r >= 0 && s >= 0 && r < to_grid->cols 
	  && s < to_grid->rows) {
	dist = sqrt((from_r - r) * (from_r - r) 
		    + (from_s - s) * (from_s - s));
/*
 *	if within the search radius and If distance is less than the
 *	current minimum, replace the distance and data values... 
 */
	if (dist <= shell_radius && dist <= to_data_beta[s][r]) {
	  to_data_beta[s][r] = dist;
	  to_data[s][r] = from_dat;
	}
	++npts;
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * Nearest neighbor normalization.
 *
 *	input : to_data
 *              to_data_beta 
 *              to_data_num_pts
 *
 *      output: to_data
 *
 *	result: number of valid points normalized
 *
 *------------------------------------------------------------------------*/
int normalize_near_neighbor(grid_class *to_grid,float **to_data,
			    float **to_data_beta,
			    int **to_data_num_pts)
{
  return TRUE;
}
