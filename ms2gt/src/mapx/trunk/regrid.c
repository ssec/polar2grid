/*========================================================================
 * regrid - resample one grid to another 
 *
 * 27-Apr-1994 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1994 University of Colorado
 *========================================================================*/
static const char regrid_c_rcsid[] = "$Id: regrid.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "matrix.h"
#include "mapx.h"
#include "grids.h"
#include "maps.h"

#define usage								   \
"$Revision: 16072 $\n"                                                             \
"usage: regrid [-fwubslFv -i value -k kernel -p power -z beta_file] \n"	   \
"              from.gpd to.gpd from_data to_data\n"			   \
"\n"									   \
" input : from.gpd  - original grid parameters definition file\n"	   \
"         to.gpd    - new grid parameters definition file\n"		   \
"         from_data - original gridded data file (flat file by rows)\n"	   \
"         [to_data] - if -z option then use as initial values\n"	   \
"\n"									   \
" output: to_data - new gridded data file (flat file by rows)\n"	   \
"\n"									   \
" option: f - forward resampling\n"					   \
"         w - weighted average\n"					   \
"         u - unsigned data\n"						   \
"         b - byte data (default)\n"					   \
"         s - short (2 bytes per sample)\n"				   \
"         l - long (4 bytes)\n"						   \
"         F - float (4 bytes)\n"                                           \
"         v - verbose (can be repeated)\n"				   \
"         i value - ignore fill value\n"				   \
"         p power - 0=smooth, 6=sharp, 2=default (used with -fw only)\n"   \
"         k kernel - force kernel size (rowsxcols) (used with -fw only)\n" \
"         z beta_file - save/restore intermediate results\n"		   \
"\n"									   \
" note: -f and -w options select interpolation method as follows:\n"	   \
"       default = nearest-neighbor\n"					   \
"       -w      = bilinear interpolation\n"				   \
"       -ww     = cubic convolution\n"					   \
"       -f      = drop-in-the-bucket averaging\n"			   \
"       -fw     = inverse distance weighted sum\n"			   \
"                 -k and -p options only effect this method\n"		   \
"\n"

/*------------------------------------------------------------------------
 *
 * The best interpolation method depends on the data being resampled
 * and the relative cell sizes of the two grids. As far as the data
 * goes, you will have to decide based on the characteristics you want
 * to preserve in the data. Weighted sums, like bilinear and inverse
 * distance, will give better looking images because they smooth the
 * data. They are geometrically more accurate since they interpolate
 * the data based on relative grid cell location, but the smoothing
 * can be an undesirable effect. Nearest neighbor resampling on the
 * otherhand will preserve the radiometric accuracy of the data but
 * will introduce geolocation (roundoff) errors on the order of one
 * output grid cell. Drop-in-the-bucket averaging is good for data
 * where the input grid cell size is much smaller than the output
 * (less than half).  Inverse distance weighting works well for all
 * data types in the situation where the input cell is significantly
 * larger than the output cell (more than double). With the inverse
 * distance method you can use the kernel and power parameters to fine
 * tune the smoothing effect.
 * 
 * The -z beta_file option allows for multiple input grids to be
 * combined into a single output grid. The program is run once for 
 * each input grid always specifying the same beta and output files.
 * The input files need not be in the same grid, but the interpolation 
 * method must be the same each time the same beta file is used.
 *
 *------------------------------------------------------------------------*/

#define VV_INTERVAL 30

static int fill, k_cols, k_rows;
static int ignore_fill, verbose, preload_data;
static bool modified_option;
static double power;

int inv_dist(grid_class *, float **, grid_class *, float **, float **);
int ditb_avg(grid_class *, float **, grid_class *, float **, float **);
int bilinear(grid_class *, float **, grid_class *, float **, float **);
int nearestn(grid_class *, float **, grid_class *, float **, float **);
int cubiccon(grid_class *, float **, grid_class *, float **, float **);

#define ROUND(x) ((x) < 0 ? (int)((x)-.5) : (int)((x)+.5))
#define FLOAT(x) ((float)(x))

/*------------------------------------------------------------------------
 * read_grid_data - read file data into float matrix
 *
 *	input : cols, rows - grid width and height
 *		data_bytes - number of bytes per datum
 *		signed_data - TRUE = signed, FALSE = unsigned
 *              float_data - TRUE = floating-point, FALSE = integer
 *		fp - file pointer
 *
 *	output: data - matrix
 *
 *	result: TRUE iff success
 *
 *------------------------------------------------------------------------*/
bool read_grid_data(int cols, int rows, int data_bytes,
		    bool signed_data, bool float_data,
		    float **data, FILE *fp)
{ int i, j, row_bytes, status, total_bytes;
  byte1 *bufp, *iobuf;

  fseek(fp, 0, SEEK_SET);

  row_bytes = cols*data_bytes;
  iobuf = (byte1 *)malloc(row_bytes);
  if (!iobuf) { perror("read_grid_data"); return FALSE; }

  total_bytes = 0;

  for (i = 0; i < rows; i++)
  { status = fread(iobuf, 1, row_bytes, fp);
    if (status != row_bytes) { 
      perror("read_grid_data"); free(iobuf); return FALSE; }
    total_bytes += status;
    for (j = 0, bufp = iobuf; j < cols; j++, bufp += data_bytes)
    { if (float_data)
      { data[i][j] = *((float *)bufp);
      } else
      { switch (data_bytes * (signed_data ? -1 : 1))
	{ case -1: data[i][j] = FLOAT(*((int1 *)bufp)); break;
          case -2: data[i][j] = FLOAT(*((int2 *)bufp)); break;
          case -4: data[i][j] = FLOAT(*((int4 *)bufp)); break;
          case  1: data[i][j] = FLOAT(*((byte1 *)bufp)); break;
	  case  2: data[i][j] = FLOAT(*((byte2 *)bufp)); break;
	  case  4: data[i][j] = FLOAT(*((byte4 *)bufp)); break;
          default: assert(NEVER); /* should never execute */
	}
      }
    }
  }

  free(iobuf);
  return TRUE;
}

/*------------------------------------------------------------------------
 * write_grid_data - write float matrix into grid data file
 *
 *	input : cols, rows - grid width and height
 *		data_bytes - number of bytes per datum
 *		signed_data - TRUE = signed, FALSE = unsigned
 *              float_data - TRUE = floating-point, FALSE = integer
 *		data - matrix
 *		fp - file pointer
 *
 *	result: TRUE iff success
 *
 *------------------------------------------------------------------------*/
bool write_grid_data(int cols, int rows, int data_bytes,
		     bool signed_data, bool float_data,
		     float **data, FILE *fp)
{ int i, j, row_bytes, status, total_bytes;
  byte1 *bufp, *iobuf;

  fseek(fp, 0, SEEK_SET);

  row_bytes = cols*data_bytes;
  iobuf = (byte1 *)malloc(row_bytes);
  if (!iobuf) { perror("write_grid_data"); return FALSE; }

  total_bytes = 0;

  for (i = 0; i < rows; i++)
  { for (j = 0, bufp = iobuf; j < cols; j++, bufp += data_bytes)
    { if (float_data)
      { *((float *)bufp) = data[i][j];
      } else
      { switch (data_bytes * (signed_data ? -1 : 1))
	{ case -1: *((int1 *)bufp) = ROUND(data[i][j]); break;
	  case -2: *((int2 *)bufp) = ROUND(data[i][j]); break;
	  case -4: *((int4 *)bufp) = ROUND(data[i][j]); break;
          case  1: *((byte1 *)bufp) = ROUND(data[i][j]); break;
	  case  2: *((byte2 *)bufp) = ROUND(data[i][j]); break;
	  case  4: *((byte4 *)bufp) = ROUND(data[i][j]); break;
          default: assert(NEVER); /* should never execute */
	}
      }
    }
    status = fwrite(iobuf, 1, row_bytes, fp);
    if (status != row_bytes) 
    { perror("write_grid_data"); free(iobuf); return FALSE; }
    total_bytes += status;
  }

  free(iobuf);
  return TRUE;
}

int main(int argc, char *argv[])
{ register int i, j;
  int data_bytes, nparams, status;
  bool forward_resample, weighted_sum;
  bool signed_data, wide_weighted;
  bool float_data;
  float **from_data, **to_data, **to_beta;
  char *option;
  char from_filename[FILENAME_MAX], to_filename[FILENAME_MAX];
  char beta_filename[FILENAME_MAX];
  FILE *from_file, *to_file, *beta_file;
  grid_class *from_grid, *to_grid;

/*
 *	set defaults
 */
  forward_resample = FALSE;
  weighted_sum = FALSE;
  wide_weighted = FALSE;
  modified_option = FALSE;
  data_bytes = 1;
  signed_data = TRUE;
  float_data = FALSE;
  k_rows = k_cols = 0;
  power = 2;
  beta_file = NULL;
  preload_data = FALSE;
  ignore_fill = FALSE;
  fill = 0;
  verbose = 0;

/* 
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'f':
	  forward_resample = TRUE;
	  break;
	case 'w':
	  if (weighted_sum) wide_weighted = TRUE;
	  weighted_sum = TRUE;
	  break;
	case 'm':
	  modified_option = TRUE;
	  break;
	case 'k':
	  ++argv; --argc;
	  if (argc <= 0) error_exit(usage);
	  nparams = sscanf(*argv, "%dx%d", &k_rows, &k_cols);
	  if (0 == nparams) error_exit(usage);
	  if (1 == nparams) k_cols = k_rows;
	  break;
	case 'p':
	  ++argv; --argc;
	  if (sscanf(*argv, "%lf", &power) != 1) error_exit(usage);
	  break;
	case 'z':
	  ++argv; --argc;
	  strcpy(beta_filename, *argv);
	  preload_data = TRUE;
	  beta_file = fopen(beta_filename, "r+");
	  if (!beta_file)
	  { preload_data = FALSE;
	    beta_file = fopen(beta_filename, "w");
	    if (!beta_file) { perror(beta_filename); error_exit(usage); }
	  }
	  break;
	case 'u':
	  signed_data = FALSE;
	  break;
	case 'b':
	  data_bytes = 1;
	  break;
	case 's':
	  data_bytes = 2;
	  break;
	case 'l':
	  data_bytes = 4;
	  break;
        case 'F':
	  float_data = TRUE;
          break;
	case 'i':
	  ++argv; --argc;
	  if (sscanf(*argv, "%d", &fill) != 1) error_exit(usage);
	  ignore_fill = TRUE;
	  break;
	case 'v':
	  ++verbose;
	  break;
	case 'V':
	  fprintf(stderr,"%s\n", regrid_c_rcsid);
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
  if (argc != 4) error_exit(usage);
  
  from_grid = init_grid(*argv);
  if (!from_grid) exit(ABORT);
  if (verbose) fprintf(stderr,"> from .gpd file %s\n", 
		       from_grid->gpd_filename);
  ++argv; --argc;
  
  to_grid = init_grid(*argv);
  if (!to_grid) exit(ABORT);
  if (verbose) fprintf(stderr,"> to .gpd file %s\n",
		       to_grid->gpd_filename);
  ++argv; --argc;
  
  strcpy(from_filename, *argv);
  from_file = fopen(from_filename, "r");
  if (!from_file) { perror(from_filename); exit(ABORT); }
  if (verbose) fprintf(stderr,"> from data file %s\n", from_filename);
  ++argv; --argc;
  
  strcpy(to_filename, *argv);
  to_file = fopen(to_filename, preload_data ? "r+" : "w");
  if (!to_file) { perror(to_filename); exit(ABORT); }
  if (verbose) fprintf(stderr,"> to data file %s\n", to_filename);
  ++argv; --argc;

  /*
   *    set up for floating-point data
   */
  if (float_data)
  { data_bytes = 4;
    signed_data = TRUE;
  }
  
/*
 *	determine extent of kernel
 */
  if (forward_resample && !k_cols)
  { k_cols = nint(from_grid->mapx->scale/from_grid->cols_per_map_unit
		  / to_grid->mapx->scale/to_grid->cols_per_map_unit);
    if (k_cols < 1) k_cols = 1;
    k_rows = nint(from_grid->mapx->scale/from_grid->rows_per_map_unit
		  / to_grid->mapx->scale/to_grid->rows_per_map_unit);
    if (k_rows < 1) k_rows = 1;
  }

/*
 *	allocate storage for data grids
 */
  if (verbose >= 2) fprintf(stderr,">> allocating...\n");

  from_data = (float **)matrix(from_grid->rows, from_grid->cols,
				sizeof(float), TRUE);
  if (!from_data) { exit(ABORT); }

  to_data = (float **)matrix(to_grid->rows, to_grid->cols,
			      sizeof(float), TRUE);
  if (!to_data) { exit(ABORT); }

  to_beta = (float **)matrix(to_grid->rows, to_grid->cols,
			      sizeof(float), TRUE);
  if (!to_beta) { exit(ABORT); }

/*
 *	read input grid data
 */
  if (verbose) {
    if (float_data) fprintf(stderr, "> single precision floating-point data\n");
    else fprintf(stderr,"> %s %s data\n",
		 (signed_data ? "signed" : "unsigned"),
		 (1 == data_bytes ? "byte" :
		  2 == data_bytes ? "short" :
		  4 == data_bytes ? "long" : 
		  "unknown"));
  }

  if (verbose >= 2) fprintf(stderr,">> initializing...\n");

  status = read_grid_data(from_grid->cols, from_grid->rows, data_bytes, 
			  signed_data, float_data, from_data, from_file);
  if (!status) { fprintf(stderr,"regrid: error reading input file: %s\n",
			 from_filename); exit(ABORT); }

/*
 *	initialize output grid
 */
  if (preload_data)
  {
    status = read_grid_data(to_grid->cols, to_grid->rows, data_bytes, 
			    signed_data, float_data, to_data, to_file);
    if (!status) { fprintf(stderr,"regrid: error reading initial data: %s\n",
			   to_filename); exit(ABORT); }

    if (verbose)
    { fprintf(stderr,"> reading initial data from %s\n", to_filename); }

    if (beta_file) {
      status = fread(to_beta[0], sizeof(float), 
		     to_grid->cols*to_grid->rows, beta_file);
      if (to_grid->cols*to_grid->rows != status) {
	fprintf(stderr,"regrid: error reading initial weights: %s\n",
		beta_filename); exit(ABORT); }

      if (verbose) 
      { fprintf(stderr,"> reading preload weights from %s\n", beta_filename); }

/*
 *	re-weight preloaded data
 */
      if (forward_resample || weighted_sum) /* i.e. not nearest-neighbor */
      { for (i = 0; i < to_grid->rows; i++)
	{ for (j = 0; j < to_grid->cols; j++)
	  { to_data[i][j] *= to_beta[i][j];
	  }
	}
      }
    }
  }

/*
 *	resample data from input grid into output grid
 */
  if (verbose >= 2) fprintf(stderr,">> resampling...\n");

  if (forward_resample)
  { 
    if (weighted_sum)
    { inv_dist(from_grid, from_data, to_grid, to_data, to_beta);
    }
    else
    { ditb_avg(from_grid, from_data, to_grid, to_data, to_beta);
    }
  }
  else /* do inverse resample */
  {
    if (wide_weighted)
    { cubiccon(from_grid, from_data, to_grid, to_data, to_beta);
    }
    else if (weighted_sum)
    { bilinear(from_grid, from_data, to_grid, to_data, to_beta);
    }
    else
    { nearestn(from_grid, from_data, to_grid, to_data, to_beta);
    }
  }

/*
 *	normalize result
 */
  if (verbose >= 2) fprintf(stderr,">> normalizing...\n");

  if (forward_resample || weighted_sum) /* i.e. not nearest-neighbor */
  { for (i = 0; i < to_grid->rows; i++)
    { for (j = 0; j < to_grid->cols; j++)
      { 
	if (to_beta[i][j] != 0) 
	{ to_data[i][j] /= to_beta[i][j];
	}
	else
	  /*
	   * beta==0 indicates missing data
	   */
	{ to_data[i][j] = fill;
	}
      }
    }
  }
  else /* for nearest-neighbor */
  { for (i = 0; i < to_grid->rows; i++)
    { for (j = 0; j < to_grid->cols; j++)
      { 
	if (0 == to_beta[i][j]) to_data[i][j] = fill;
      }
    }
  }

/*
 *	write out result
 */
  status = write_grid_data(to_grid->cols, to_grid->rows, data_bytes,
			   signed_data, float_data, to_data, to_file);
  if (!status) { perror(to_filename); exit(ABORT); }

  if (beta_file)
  { if (verbose) fprintf(stderr,"> writing beta to %s\n", beta_filename);
    fseek(beta_file, 0, SEEK_SET);
    fwrite(to_beta[0], sizeof(float), to_grid->cols*to_grid->rows, beta_file);
  }

  exit(EXIT_SUCCESS);
}

/*------------------------------------------------------------------------
 * inv_dist - inverse distance weighted sum interpolation
 *
 *	forward resampling
 *	weighted sum
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int inv_dist(grid_class *from_grid, float **from_data, 
	     grid_class *to_grid, float **to_data, float **to_beta)
{ register int i, j, col, row;
  double lat, lon, r, s;
  double dr, ds, d2, dw, weight;
  int npts=0, status;

  if (verbose) fprintf(stderr,"> inverse distance interpolation "
		       "%dx%d kernel, power = %3.1f\n", 
		       k_rows, k_cols, power);

/*
 *	map each from_grid value into the to_grid
 */
  for (i = 0; i < from_grid->rows; i++) 
  { for (j = 0; j < from_grid->cols; j++)
    {
/*
 *	ignore cells with fill value
 */
      if (ignore_fill && fill == from_data[i][j]) continue;

/*
 *	project from_grid location into to_grid
 */
      status = inverse_grid(from_grid, (double)j, (double)i, &lat, &lon);
      if (!status) continue;

      status = forward_grid(to_grid, lat, lon, &r, &s);
      if (!status || !within_mapx(to_grid->mapx, lat, lon)) continue;

      if (verbose >= 3 && 0 == i % VV_INTERVAL && 0 == j % VV_INTERVAL)
	fprintf(stderr,">>> %4d %4d --> %7.2lf %7.2lf --> %4d %4d\n",
		j, i, lat, lon, (int)(r + 0.5), (int)(s + 0.5));

/*
 *	distribute from_grid value over the appropriate to_grid cells
 */
      for (row=(int)(s-k_rows/2+.5); row <= (int)(s+k_rows/2+.5); row++)
      { if (row < 0 || row >= to_grid->rows) continue;
	ds = (s - row);
	for (col=(int)(r-k_cols/2+.5); col <= (int)(r+k_cols/2+.5); col++)
	{ if (col < 0 || col >= to_grid->cols) continue;
	  dr = (r - col);
	  d2 = dr*dr + ds*ds;
	  dw = pow(d2, power/2);
	  weight = dw > 0 ? 1/dw : 9e9;
	  to_data[row][col] += from_data[i][j]*weight;
	  to_beta[row][col] += weight;
	}
      }

      ++npts;
    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * ditb_avg - drop-in-the-bucket averaging
 *
 *	forward resampling
 *	unweighted average
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int ditb_avg(grid_class *from_grid, float **from_data, 
	     grid_class *to_grid, float **to_data, float **to_beta)
{ register int i, j, col, row;
  double lat, lon, r, s;
  int npts=0, status;

  if (verbose) fprintf(stderr,"> drop-in-the-bucket averaging\n");

/*
 *	map each from_grid value into the to_grid
 */
  for (i = 0; i < from_grid->rows; i++) 
  { for (j = 0; j < from_grid->cols; j++)
    {
/*
 *	ignore cells with fill value
 */
      if (ignore_fill && fill == from_data[i][j]) continue;

/*
 *	project from_grid location into to_grid
 */
      status = inverse_grid(from_grid, (double)j, (double)i, &lat, &lon);
      if (!status) continue;

      status = forward_grid(to_grid, lat, lon, &r, &s);
      if (!status) continue;

      if (verbose >= 3 && 0 == i % VV_INTERVAL && 0 == j % VV_INTERVAL)
	fprintf(stderr,">>> %4d %4d --> %7.2lf %7.2lf --> %4d %4d\n",
		j, i, lat, lon, (int)(r + 0.5), (int)(s + 0.5));

/*
 *	drop from_grid value into appropriate to_grid cell
 */
      row = (int)(s + 0.5); 
      col = (int)(r + 0.5);
      if (row >= 0 && row < to_grid->rows && col >= 0 && col < to_grid->cols) {
	if (modified_option) {
	  if (from_data[i][j] > to_data[row][col]) {
	    to_data[row][col] = from_data[i][j];
	    to_beta[row][col] = 1;
	  }
	} else {
	  to_data[row][col] += from_data[i][j];
	  to_beta[row][col] += 1;
	}
      }

      ++npts;
    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * bilinear - bilinear interpolation
 *
 *	inverse resampling
 *	weighted sum
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int bilinear(grid_class *from_grid, float **from_data, 
	      grid_class *to_grid, float **to_data, float **to_beta)
{ register int i, j, col, row;
  double lat, lon, r, s;
  double dr, ds, weight;
  int npts=0, status;

  if (verbose) fprintf(stderr,"> bilinear interpolation\n");

/*  
 *	retrieve a value in the from_grid based on a to_grid location
 */
  for (i = 0; i < to_grid->rows; i++) 
  { for (j = 0; j < to_grid->cols; j++)
    {
      status = inverse_grid(to_grid, (double)j, (double)i, &lat, &lon);
      if (!status) continue;

      status = forward_grid(from_grid, lat, lon, &r, &s);
      if (!status) continue;

      if (verbose >= 3 && 0 == i % VV_INTERVAL && 0 == j % VV_INTERVAL)
	fprintf(stderr,">>> %4d %4d --> %7.2lf %7.2lf --> %4d %4d\n",
		j, i, lat, lon, (int)(r + 0.5), (int)(s + 0.5));

      for (row=(int)s; row <= (int)s + 1; row++)
      { if (row < 0 || row >= from_grid->rows) continue;
	ds = fabs(s - row);
	for (col=(int)r; col <= (int)r + 1; col++)
	{ if (col < 0 || col >= from_grid->cols) continue;
	  if (ignore_fill && fill == from_data[row][col]) continue;
	  dr = fabs(r - col);
	  weight = (1 - ds)*(1 - dr);
	  to_data[i][j] += from_data[row][col]*weight;
	  to_beta[i][j] += weight;
	}
      }

      ++npts;
    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * nearestn - nearest-neighbor resampling
 *
 *	inverse resampling
 *	no averaging
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int nearestn(grid_class *from_grid, float **from_data, 
	     grid_class *to_grid, float **to_data, float **to_beta)
{ register int i, j, col, row;
  double lat, lon, r, s;
  double dd, dr, ds;
  int npts=0, status;

  if (verbose) fprintf(stderr,"> nearest-neighbor resampling\n");

/*  
 *	retrieve a value in the from_grid based on a to_grid location
 */
  for (i = 0; i < to_grid->rows; i++) 
  { for (j = 0; j < to_grid->cols; j++)
    {
      status = inverse_grid(to_grid, (double)j, (double)i, &lat, &lon);
      if (!status) continue;

      status = forward_grid(from_grid, lat, lon, &r, &s);
      if (!status) continue;

      dr = nint(r) - r;
      ds = nint(s) - s; 
      dd = sqrt(dr*dr + ds*ds);

      if (verbose >= 3 && 0 == i % VV_INTERVAL && 0 == j % VV_INTERVAL)
	fprintf(stderr,">>> %4d %4d --> %7.2lf %7.2lf --> %4d %4d\n",
		j, i, lat, lon, (int)(r + 0.5), (int)(s + 0.5));

      row = (int)(s + 0.5);
      col = (int)(r + 0.5);
      if (row >= 0 && row < from_grid->rows
	  && col >= 0 && col < from_grid->cols
	  && !(ignore_fill && fill == from_data[row][col]))
      {
/*
 *	When processing multiple files, if the input grids are
 *	the same then the distance to the nearest neighbor
 *	will always be the same. In this test then, the <= as
 *	opposed to strictly < will replace the preloaded data
 *	with the most recent data.
 */
	if (!preload_data
	    || dd <= to_beta[i][j]
	    || (0 == to_beta[i][j] && fill == to_data[i][j]))
	{
	  to_data[i][j] = from_data[row][col];
	  /*
	   * since beta==0 indicates missing data
	   * and these are just relative weights
	   * bump the distance up by 1
	   */
	  to_beta[i][j] = dd + 1;
	}
      }

      ++npts;
    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * cubiccon - cubic convolution interpolation
 *
 *	inverse resampling
 *	wide weighted sum
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
int cubiccon(grid_class *from_grid, float **from_data, 
	     grid_class *to_grid, float **to_data, float **to_beta)
{ register int i, j, col, row;
  double lat, lon, r, s;
  double ccr[4], ccs[4], ccr_col, ccs_row, dr, ds, weight;
  int npts=0, status;

  if (verbose) fprintf(stderr,"> cubic convolution\n");

/*  
 *	retrieve a value in the from_grid based on a to_grid location
 */
  for (i = 0; i < to_grid->rows; i++) 
  { for (j = 0; j < to_grid->cols; j++)
    {
      status = inverse_grid(to_grid, (double)j, (double)i, &lat, &lon);
      if (!status) continue;

      status = forward_grid(from_grid, lat, lon, &r, &s);
      if (!status) continue;

      if (verbose >= 3 && 0 == i % VV_INTERVAL && 0 == j % VV_INTERVAL)
	fprintf(stderr,">>> %4d %4d --> %7.2lf %7.2lf --> %4d %4d\n",
		j, i, lat, lon, (int)(r + 0.5), (int)(s + 0.5));

/*
 *	get cubic coefficients
 */
      dr = r - (int)r;
      ds = s - (int)s;

      ccr[0] = -dr*(1-dr)*(1-dr);
      ccr[1] = (1 - 2*dr*dr + dr*dr*dr);
      ccr[2] = dr*(1 + dr - dr*dr);
      ccr[3] = -dr*dr*(1-dr);

      ccs[0] = -ds*(1-ds)*(1-ds);
      ccs[1] = (1 - 2*ds*ds + ds*ds*ds);
      ccs[2] = ds*(1 + ds - ds*ds);
      ccs[3] = -ds*ds*(1-ds);

/*
 *	interpolated value is weighted sum of sixteen surrounding samples
 */
      for (row = (int)s-1; row <= (int)s+2; row++)
      { if (row < 0 || row >= from_grid->rows) continue;

	ccs_row = ccs[row - ((int)s-1)];

	for (col = (int)r-1; col <= (int)r+2; col++)
	{ if (col < 0 || col >= from_grid->cols) continue;
	  if (ignore_fill && fill == from_data[row][col]) continue;

	  ccr_col = ccr[col - ((int)r-1)];

	  weight = ccs_row*ccr_col;

	  to_data[i][j] += from_data[row][col]*weight;
	  to_beta[i][j] += weight;

	}
      }

      ++npts;

    }
  }

  return npts;
}
