/*========================================================================
 * resamp - resample one grid to another 
 *
 * 19-Mar-1998 K.Knowles knowles@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char resamp_c_rcsid[] = "$Header: /usr/local/src/maps/resamp.c,v 1.3 2000/05/22 15:34:16 knowles Exp $";

#include "define.h"
#include "grids.h"
#include "grid_io.h"

#define usage								\
"usage: resamp [-vubslf -i fill -m mask -r factor -c method] \n"	\
"              from.gpd to.gpd from_data to_data\n"			\
"\n"									\
" input : from.gpd  - original grid parameters definition file\n"	\
"         to.gpd    - new grid parameters definition file\n"		\
"         from_data - original gridded data file (flat file by rows)\n"	\
"\n"									\
" output: to_data - new gridded data file (flat file by rows)\n"	\
"\n"									\
" option: v - verbose\n"						\
"         u - unsigned data\n"						\
"         b - 1 byte data (default)\n"					\
"         s - short (2 bytes per sample)\n"				\
"         l - long (4 bytes)\n"						\
"         f - single precision floating point (4 bytes)\n"              \
"         i fill - ignore fill value\n"					\
"         m mask - ignore everything but mask value\n"			\
"                  cell value is percent of cell covered by mask\n"	\
"                  output is 1 byte signed data with -1 fill value\n"	\
"                  mask can be specified as a range separated \n"\
"                  by a hyphen eg. 1-17 in which case a separate\n"\
"                  file is output for each mask value\n"	\
"         r factor - reduce resolution of to_grid by mfactor\n"		\
"         c method - choose interpolation method\n"			\
"                    N = nearest neighbor\n"				\
"                    D = drop in the bucket\n"				\
"                    B = bilinear\n"					\
"                    M = minification\n"				\
"                    R = reduction\n"					\
"                    (otherwise determined automatically)\n"		\
"\n"

static char possible_methods[] = "NDBMR";

static int nearest_neighbor(grid_class *from_grid, grid_class *to_grid, 
		     grid_io_class *from_data, grid_io_class *to_data);

static int drop_in_the_bucket(grid_class *from_grid, grid_class *to_grid, 
		       grid_io_class *from_data, grid_io_class *to_data);

static int bilinear(grid_class *from_grid, grid_class *to_grid, 
	     grid_io_class *from_data, grid_io_class *to_data);

static int minification(grid_class *from_grid, grid_class *to_grid, 
		 grid_io_class *from_data, grid_io_class *to_data);

static int reduction(grid_class *from_grid, grid_class *to_grid, 
		 grid_io_class *from_data, grid_io_class *to_data);

static int distribution(grid_class *from_grid, grid_class *to_grid, 
		 grid_io_class *from_data, grid_io_class *to_data);

static float normalized_grid_scale(grid_class *this);

static int (*method_function[])()  = { nearest_neighbor, 
				       drop_in_the_bucket, 
				       bilinear,
				       minification,
				       reduction };
				      

static bool mask_only, ignore_fill;
static int fill, mask, mask2, temp, verbose;
static int report_interval = 100; /* rows */

#define INTERCHANGE(x, y) (temp = x, x = y, y = temp)

main (int argc, char *argv[])
{ int mfactor, status, nitems, npts;
  size_t datum_size;
  bool signed_data;
  bool real_data;
  grid_class *from_grid=NULL, *to_grid=NULL;
  grid_io_class *from_data=NULL, *to_data=NULL;
  char *option=NULL, *position=NULL;
  char method;
  int (*resample)(grid_class*, grid_class*, grid_io_class*, grid_io_class*);

/*
 *	set defaults
 */
  status = EXIT_FAILURE;
  mfactor = 0;
  mask_only = FALSE;
  ignore_fill = FALSE;
  verbose = 0;
  datum_size = 1;
  signed_data = TRUE;
  real_data = FALSE;
  method = '\0';
  resample = NULL;

/* 
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'i':
	  ++argv; --argc;
	  if (sscanf(*argv, "%d", &fill) != 1) error_exit(usage);
	  ignore_fill = TRUE;
	  break;
	case 'm':
	  ++argv; --argc;
	  nitems = sscanf(*argv, "%d%d", &mask, &mask2);
	  if (2 == nitems)
	  { if (mask2 < 0) mask2 = -mask2;
	    if (mask2 < mask) INTERCHANGE(mask, mask2);
	    resample = distribution;
	  }
	  else if (1 == nitems)
	  { mask_only = TRUE;
	  }
	  else
	  { error_exit(usage);
	  }
	  break;
	case 'r':
	  ++argv; --argc;
	  if (sscanf(*argv, "%d", &mfactor) != 1) error_exit(usage);
	  if (mfactor <= 1) 
	  { fprintf(stderr,"resamp: mfactor must be greater than one\n");
	    error_exit(usage);
	  }
	  break;
	case 'b':
	  datum_size = 1;
	  break;
	case 's':
	  datum_size = 2;
	  break;
	case 'l':
	  datum_size = 4;
	  break;
        case 'f':
	  datum_size = 4;
	  real_data = TRUE;
	  break;
	case 'u':
	  signed_data = FALSE;
	  break;
	case 'v':
	  ++verbose;
	  break;
	case 'c':
	  ++argv; --argc;
	  method = *argv[0];
	  position = strchr(possible_methods, method);
	  if (!position)
	  { fprintf(stderr,"resamp: method %c not in [%s]\n",
		    method, possible_methods);
	  error_exit(usage);
	  }
	  if (resample != distribution)
	    resample = method_function[position - possible_methods];
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
  if (!from_grid) goto cleanup;
  if (verbose) fprintf(stderr,"> from .gpd file %s\n>      .mpp file %s\n", 
		       from_grid->gpd_filename,
		       from_grid->mapx->mpp_filename);
  ++argv; --argc;
  
  to_grid = init_grid(*argv);
  if (!to_grid) goto cleanup;
  if (verbose) fprintf(stderr,"> to   .gpd file %s\n>      .mpp file %s\n", 
		       to_grid->gpd_filename,
		       to_grid->mapx->mpp_filename);
  ++argv; --argc;

  if (mfactor)
  { to_grid->cols /= mfactor;
    to_grid->rows /= mfactor;
    to_grid->map_origin_col /= mfactor;
    to_grid->map_origin_row /= mfactor;
    to_grid->cols_per_map_unit /= mfactor;
    to_grid->rows_per_map_unit /= mfactor;
  }
  else
  { mfactor = 1;
  }

  from_data = init_grid_io(from_grid->cols, from_grid->rows,
			   datum_size, signed_data, real_data,
			   grid_io_READ_ONLY, *argv);
  if (!from_data) goto cleanup;
  if (verbose) fprintf(stderr,"> from data file %s, %dx%d\n", 
		       from_data->filename, 
		       from_data->width, from_data->height);
  ++argv; --argc;
  
  to_data = init_grid_io(to_grid->cols, to_grid->rows,
			 mask_only ? 1 : datum_size, 
			 mask_only ? TRUE : signed_data,
			 mask_only ? FALSE : real_data,
			 grid_io_WRITE, *argv);
  if (!to_data) goto cleanup;
  if (verbose) fprintf(stderr,"> to data file %s, %dx%d\n", 
		       to_data->filename,
		       to_data->width, to_data->height);
  ++argv; --argc;
  
/*
 *	initialize to data
 */
  fill_grid_io(to_data, mask_only ? -1 : fill);

/*
 *	check processing options
 */
  if (('M' == method || 'R' == method)
      && !streq(from_grid->gpd_filename, to_grid->gpd_filename))
  { fprintf(stderr,"resamp: to.gpd must be same as from.gpd to use M or R\n");
    goto cleanup;
  }    

  if (method && distribution == resample)
  { fprintf(stderr,"resamp: -m %d-%d overrides -c %c option\n", 
	    mask, mask2, method);
  }
  assert(mfactor >= 1);
  if (streq(from_grid->gpd_filename, to_grid->gpd_filename)
      && 1 == mfactor)
  { fprintf(stderr,"resamp: input and output grids are identical\n");
    goto cleanup;
  }

  if (verbose) 
  { fprintf(stderr,"> filling output with %d\n", 
	    mask_only || distribution == resample ? -1 : fill);
    if (mfactor > 1) 
      fprintf(stderr,"> shrinking output grid by %d\n", mfactor);
    if (ignore_fill) 
      fprintf(stderr,"> ignoring input %d\n", fill);
    if (mask_only) 
      fprintf(stderr,"> creating mask of %d\n", mask);
  }

/*
 *	set resample method
 */
  if (!resample)
  { 
    if (streq(from_grid->gpd_filename, to_grid->gpd_filename))
    { resample = (mask_only ? reduction : minification);
    }
    else if ((normalized_grid_scale(from_grid)
	      / normalized_grid_scale(to_grid)) > 2) 
/* 
 *	to cells are more than twice as big as from cells
 */
    { resample = drop_in_the_bucket;
    }
    else
/*
 *	to cells are approx. same size or smaller than from cells
 */
    { resample = bilinear;
    }
  }

  npts = resample(from_grid, to_grid, from_data, to_data);
  if (npts > 0) status = EXIT_SUCCESS;

  if (verbose) fprintf(stderr,"> resampled %d points\n", npts);

/*
 *	clean up
 */
 cleanup:
  close_grid(from_grid);
  close_grid(to_grid);
  close_grid_io(from_data);
  close_grid_io(to_data);

  exit(status);
}

/*------------------------------------------------------------------------
 * distribution - determine proportion of to_cell for each from_cell value
 *
 *	input : from_grid, to_grid, from_data
 *
 *	output: to_data 
 *
 *	result: number of valid points resampled
 *
 *	effect: to_data datum size is changed to 1 byte per bin
 *
 *------------------------------------------------------------------------*/
static int distribution(grid_class *from_grid, grid_class *to_grid, 
		     grid_io_class *from_data, grid_io_class *to_data)
{ int i, j, col, row, bin, nbins;
  float lat, lon, r, s;
  int npts=0, status;
  char *basename=NULL, *extension=NULL, filename[FILENAME_MAX];
  grid_io_class *total=NULL, **count, *original;
  double from_cell, to_cell, count_cell, total_cell;


  if (verbose) fprintf(stderr,"> distribution for masks %d-%d\n", mask, mask2);

/*
 *	create temporary grids to accumulate number of points 
 *	for each bin value as well as total points in each cell
 */
  nbins = mask2 - mask + 1;
  count = (grid_io_class **)calloc(nbins, sizeof(grid_io_class *));
  if (!count) { perror("distribution: count"); goto cleanup; }
  for (bin = 0; bin < nbins; bin++)
  { count[bin] = init_grid_io(to_grid->cols, to_grid->rows, 
			      2, FALSE, FALSE, grid_io_TEMPORARY,
			      "counttmpfile");
    if (!count[bin]) { goto cleanup; }

    fill_grid_io(count[bin], 0);
  }

  total = init_grid_io(to_grid->cols, to_grid->rows, 
		     2, TRUE, FALSE, grid_io_TEMPORARY, "totaltmpfile");
  if (!total) { goto cleanup; }

  fill_grid_io(total, -1);

/*
 *	map each from_grid value into the to_grid
 *	map i,j in from_grid to row,col in to_grid
 */
  for (i = 0; i < from_grid->rows; i++) 
  { if (verbose && i % report_interval == 0) 
      fprintf(stderr,"> %2.0f%%\015", 100.*i/from_grid->rows);

    for (j = 0; j < from_grid->cols; j++)
    {
      status = get_element_grid_io(from_data, i, j, &from_cell);
      if (!status) continue;

/*
 *	ignore fill cells and cells outside range of interest
 */
      if (ignore_fill && fill == from_cell) continue;

      if (from_cell < mask || from_cell > mask2) continue;

/*
 *	project from_grid location into to_grid
 */
      status = inverse_grid(from_grid, (float)j, (float)i, &lat, &lon);
      if (!status) continue;

      if (!within_mapx(to_grid->mapx, lat, lon)
	  || !within_mapx(from_grid->mapx, lat, lon)) continue;

      status = forward_grid(to_grid, lat, lon, &r, &s);
      if (!status) continue;

/*
 *	drop from_grid value into appropriate to_grid cell
 */
      row = (int)(s + 0.5); 
      col = (int)(r + 0.5);
      if (row < 0 || row >= to_grid->rows 
	  || col < 0 || col >= to_grid->cols) continue;

      bin = from_cell - mask;
      assert(0 <= bin && bin < nbins);

      status = get_element_grid_io(count[bin], row, col, &count_cell);
      if (!status) continue;
      status = get_element_grid_io(total, row, col, &total_cell);
      if (!status) continue;

      assert(count_cell < INT2_MAX && total_cell < INT2_MAX);
      count_cell += 1;
      total_cell += 1;
      ++npts;

      status = put_element_grid_io(count[bin], row, col, count_cell);
      if (!status) continue;
      status = put_element_grid_io(total, row, col, total_cell);
      if (!status) continue;

    }
  }

/*
 *	write a to_grid for each bin
 */
  original = to_data;
  basename = strdup(original->filename);
  extension = strrchr(basename, '.');
  if (extension) { *extension = '\0'; extension += 1; }

  for (bin = 0; bin < nbins; bin++)
  { 
    sprintf(filename, extension ? "%s%2.2d.%s" : "%s%2.2d",
	    basename, bin+mask, extension);
    to_data = init_grid_io(original->width, original->height,
			   original->datum_size, original->signed_data,
			   original->real_data,
			   grid_io_WRITE, filename);
    if (!to_data) { goto cleanup; }

    if (verbose)
      fprintf(stderr,"> writing %s\n", filename);

    for (row = 0; row < to_grid->rows; row++)
    { for (col = 0; col < to_grid->cols; col++)
      { 
	status = get_element_grid_io(count[bin], row, col, &count_cell);
        if (!status) continue;
        status = get_element_grid_io(total, row, col, &total_cell);
        if (!status) continue;

	if (total_cell == -1)
	{ to_cell = -1;
	}
	else
	{ total_cell += 1; /* because it was initialized with -1 */
	  to_cell = count_cell ? nint(100*count_cell/total_cell) : 0;
	}

        status = put_element_grid_io(to_data, row, col, to_cell);
	if (!status) continue;
      }
    }

    close_grid_io(to_data);
  }

 cleanup:
  if (basename) free(basename);
  if (count)
  { for (bin = 0; bin < nbins; bin++) close_grid_io(count[bin]);
    free(count);
  }
  close_grid_io(total);

  return npts;
}

/*------------------------------------------------------------------------
 * drop_in_the_bucket - average all data in cell
 *
 *	input : from_grid, to_grid, from_data
 *
 *	output: to_data
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
static int drop_in_the_bucket(grid_class *from_grid, grid_class *to_grid, 
			      grid_io_class *from_data, grid_io_class *to_data)
{ int i, j, col, row;
  float lat, lon, r, s;
  int npts=0, status;
  grid_io_class *pitb=NULL, *restore=NULL;
  double from_cell, to_cell, pitb_cell, avg_cell;


  if (verbose) fprintf(stderr,"> drop-in-the-bucket averaging\n");

/*
 *	create temporary grid to accumulate
 *	number of points in the bucket (pitb)
 */
  pitb = init_grid_io(to_grid->cols, to_grid->rows, 
		     2, FALSE, FALSE, grid_io_TEMPORARY, "pitbtmpfile");
  if (!pitb) 
  { fprintf(stderr,"drop_in_the_bucket: can't get tmp storage\n");
    goto cleanup;
  }
  fill_grid_io(pitb, 0);

/*
 *	if masking then 1 byte isn't enough precision to
 *      keep track of the running total so up it to 2
 */
  if (mask_only)
  { restore = to_data;
    to_data = init_grid_io(to_grid->cols, to_grid->rows, 
			   2, TRUE, FALSE, grid_io_TEMPORARY, "avgtmpfile");
    if (!to_data) 
    { fprintf(stderr,"drop_in_the_bucket: can't get tmp storage\n");
      goto cleanup;
    }
    fill_grid_io(to_data, -1);
  }

/*
 *	map each from_grid value into the to_grid
 *	map i,j in from_grid to row,col in to_grid
 */
  for (i = 0; i < from_grid->rows; i++) 
  { if (verbose && i % report_interval == 0) 
      fprintf(stderr,"> %2.0f%%\015", 100.*i/from_grid->rows);

    for (j = 0; j < from_grid->cols; j++)
    {
      status = get_element_grid_io(from_data, i, j, &from_cell);
      if (!status) continue;

/*
 *	ignore fill cells
 */
      if (ignore_fill && fill == from_cell) continue;

/*
 *	project from_grid location into to_grid
 */
      status = inverse_grid(from_grid, (float)j, (float)i, &lat, &lon);
      if (!status) continue;

      if (!within_mapx(to_grid->mapx, lat, lon)
	  || !within_mapx(from_grid->mapx, lat, lon)) continue;

      status = forward_grid(to_grid, lat, lon, &r, &s);
      if (!status) continue;

/*
 *	drop from_grid value into appropriate to_grid cell
 */
      row = (int)(s + 0.5); 
      col = (int)(r + 0.5);
      if (row < 0 || row >= to_grid->rows 
	  || col < 0 || col >= to_grid->cols) continue;

      status = get_element_grid_io(to_data, row, col, &to_cell);
      if (!status) continue;
      status = get_element_grid_io(pitb, row, col, &pitb_cell);
      if (!status) continue;

      if (mask_only) { from_cell = (mask == from_cell ? 10000 : 0); }

      to_cell = nint((to_cell*pitb_cell + from_cell)/(pitb_cell+1));
      pitb_cell += 1;
      ++npts;

      status = put_element_grid_io(to_data, row, col, to_cell);
      if (!status) continue;
      status = put_element_grid_io(pitb, row, col, pitb_cell);
      if (!status) continue;

    }
  }

/*
 *	if masking then restore to_grid to 1 byte
 */
  if (mask_only)
  { 
    for (row = 0; row < to_grid->rows; row++)
    { for (col = 0; col < to_grid->cols; col++)
      { status = get_element_grid_io(to_data, row, col, &to_cell);
        if (!status) continue;
	avg_cell = nint(to_cell/100);
        status = put_element_grid_io(restore, row, col, avg_cell);
	if (!status) continue;
      }
    }
    close_grid_io(to_data);
  }

 cleanup:
  close_grid_io(pitb);

  return npts;
}

/*------------------------------------------------------------------------
 * bilinear - proportion cell data by area
 *
 *	input : from_grid, to_grid, from_data
 *
 *	output: to_data
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
static int bilinear(grid_class *from_grid, grid_class *to_grid, 
		    grid_io_class *from_data, grid_io_class *to_data)
{ int i, j, col, row;
  float lat, lon, r, s;
  double dr, ds, norm, sum, weight;
  int npts=0, status;
  double from_cell, to_cell;

  if (verbose) fprintf(stderr,"> bilinear interpolation\n");

/*  
 *	retrieve a value in the from_grid based on a to_grid location
 *	map i,j in to_grid to row,col in from_grid
 */
  for (i = 0; i < to_grid->rows; i++) 
  { if (verbose && i % report_interval == 0)
      fprintf(stderr,"> %2.0f%%\015", 100.*i/to_grid->rows);

    for (j = 0; j < to_grid->cols; j++)
    {
      status = inverse_grid(to_grid, (float)j, (float)i, &lat, &lon);
      if (!status) continue;

      if (!within_mapx(to_grid->mapx, lat, lon)
	  || !within_mapx(from_grid->mapx, lat, lon)) continue;

      status = forward_grid(from_grid, lat, lon, &r, &s);
      if (!status) continue;

      sum = norm = 0;

      for (row=(int)s; row <= (int)s + 1; row++)
      { if (row < 0 || row >= from_grid->rows) continue;

	ds = fabs(s - row);

	for (col=(int)r; col <= (int)r + 1; col++)
	{ if (col < 0 || col >= from_grid->cols) continue;

	  status = get_element_grid_io(from_data, row, col, &from_cell);
	  if (!status) continue;

	  if (ignore_fill && fill == from_cell) continue;

	  if (mask_only) { from_cell = (mask == from_cell ? 100 : 0); }

	  dr = fabs(r - col);

	  weight = (1 - ds)*(1 - dr);

	  sum += from_cell*weight;
	  norm += weight;
	  ++npts;
	}
      }

      to_cell = (norm ? nint(sum/norm) : fill);

      status = put_element_grid_io(to_data, i, j, to_cell);
      if (!status) continue;

    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * nearest_neighbor - take the sample closest to the center of the cell
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
static int nearest_neighbor(grid_class *from_grid, grid_class *to_grid, 
			    grid_io_class *from_data, grid_io_class *to_data)
{ int i, j, col, row;
  float lat, lon, r, s;
  int npts=0, status;
  double from_cell, to_cell;

  if (verbose) fprintf(stderr,"> nearest-neighbor resampling\n");

/*  
 *	retrieve a value in the from_grid based on a to_grid location
 *	map i,j in to_grid to row,col in from_grid
 */
  for (i = 0; i < to_grid->rows; i++) 
  { if (verbose && i % report_interval == 0)
      fprintf(stderr,"> %2.0f%%\015", 100.*i/to_grid->rows);

    for (j = 0; j < to_grid->cols; j++)
    {
      status = inverse_grid(to_grid, (float)j, (float)i, &lat, &lon);
      if (!status) continue;

      if (!within_mapx(to_grid->mapx, lat, lon)
	  || !within_mapx(from_grid->mapx, lat, lon)) continue;

      status = forward_grid(from_grid, lat, lon, &r, &s);
      if (!status) continue;

      row = (int)(s + 0.5);
      col = (int)(r + 0.5);

      if (row < 0 || row >= from_grid->rows 
	  || col < 0 || col >= from_grid->cols) continue;

      status = get_element_grid_io(from_data, row, col, &from_cell);
      if (!status) continue;

      if (ignore_fill && fill == from_cell) continue;

      if (mask_only) { from_cell = (mask == from_cell ? 100 : 0); }

      to_cell = from_cell;
      ++npts;

      status = put_element_grid_io(to_data, i, j, to_cell);
      if (!status) continue;

    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * minification - same projection and grid only smaller
 *                quickly select representative sample
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
static int minification(grid_class *from_grid, grid_class *to_grid, 
			grid_io_class *from_data, grid_io_class *to_data)
{ int i, j, col, row, mfactor, npts=0, status;
  double from_cell, to_cell;

/*
 *	get minification factor
 */
  mfactor = from_data->height/to_data->height;

  assert(mfactor > 1 && from_data->width/to_data->width == mfactor);

  if (verbose) fprintf(stderr,"> minification, factor = %d\n", mfactor);

/*  
 *	each to_grid cell is center of mfactorXmfactor square in from_grid 
 *	i,j in to_grid, row,col in from_grid
 */
  for (i = 0; i < to_grid->rows; i++) 
  { if (verbose && i % report_interval == 0)
      fprintf(stderr,"> %2.0f%%\015", 100.*i/to_grid->rows);

    row = nint(mfactor*(i + .5));

    for (j = 0; j < to_grid->cols; j++)
    {
      col = nint(mfactor*(j + .5));

      status = get_element_grid_io(from_data, row, col, &from_cell);
      if (!status) continue;

      if (ignore_fill && fill == from_cell) continue;
      if (mask_only) { from_cell = (mask == from_cell ? 100 : 0); }

      to_cell = from_cell;
      ++npts;

      status = put_element_grid_io(to_data, i, j, to_cell);
      if (!status) continue;

    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * reduction - same projection and grid only smaller
 *             reduce entire from_data to to_data grid
 *
 *	input : from_grid, from_data, to_grid
 *
 *	output: to_grid, to_beta
 *
 *	result: number of valid points resampled
 *
 *------------------------------------------------------------------------*/
static int reduction(grid_class *from_grid, grid_class *to_grid, 
		     grid_io_class *from_data, grid_io_class *to_data)
{ int i, j, col, row, mfactor, norm, npts=0, status;
  double from_cell, to_cell;

/*
 *	get reduction factor
 */
  mfactor = from_data->height/to_data->height;

  assert(mfactor > 1 && from_data->width/to_data->width == mfactor);

  if (verbose) fprintf(stderr,"> reduction, factor = %d\n", mfactor);

/*  
 *	each to_grid cell is average of mfactorXmfactor square in from_grid 
 *	i,j in to_grid, row,col in from_grid
 */
  for (i = 0; i < to_grid->rows; i++) 
  { if (verbose && i % report_interval == 0) 
      fprintf(stderr,"> %2.0f%%\015", 100.*i/to_grid->rows);

    for (j = 0; j < to_grid->cols; j++)
    { 
      to_cell = norm = 0;

      for (row = mfactor*i; row < mfactor*(i + 1); row++)
      { for (col = mfactor*j; col < mfactor*(j + 1); col++)
	{

	  status = get_element_grid_io(from_data, row, col, &from_cell);
	  if (!status) continue;

	  if (ignore_fill && fill == from_cell) continue;

	  if (mask_only) { from_cell = (mask == from_cell ? 100 : 0); }

	  to_cell += from_cell;
	  norm += 1;
	  ++npts;

	}
      }

      to_cell = (norm ? nint(to_cell/norm) : mask_only ? -1 : fill);

      status = put_element_grid_io(to_data, i, j, to_cell);
      if (!status) continue;

    }
  }

  return npts;
}

/*------------------------------------------------------------------------
 * normalized_grid_scale - radians per grid cell
 *
 *------------------------------------------------------------------------*/
static float normalized_grid_scale(grid_class *this)
{
  float col_scale, row_scale, scale;

  col_scale = this->mapx->scale/this->cols_per_map_unit;
  row_scale = this->mapx->scale/this->rows_per_map_unit;
  scale = sqrt(col_scale*col_scale + row_scale*row_scale);
  scale /= this->mapx->equatorial_radius;

  return scale;
}
