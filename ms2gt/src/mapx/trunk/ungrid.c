/*========================================================================
 * ungrid - extract point data from a grid
 *
 * 20-Feb-2004 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 2004 University of Colorado
 *========================================================================*/
static const char ungrid_c_rcsid[] = "$Id: ungrid.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "define.h"
#include "matrix.h"
#include "grids.h"

#define usage									\
"usage: ungrid [-v] [-V] [-b] [-e] [-i fill] [-n min_value] [-x max_value]\n"	\
"              [-B] [-U] [-S] [-L] [-F]\n"                                      \
"              [-c method] [-r radius] [-p power]\n"				\
"              [-C] [-I] [-R lat_min lat_max lon_min lon_max]\n"                \
"              from_gpd from_data\n"						\
"\n"										\
" input : from.gpd  - source grid parameters definition file\n"			\
"         from_data - source gridded data file (4 byte floats)\n"		\
"         < stdin - list of locations one lat/lon pair per line\n"		\
"                   (not used if -C is specified)\n"                            \
"\n"										\
" output: > stdout - list of '[lat lon] value' for each input point\n"		\
"\n"										\
" option: v - verbose\n"							\
"         V - print version information to stderr\n"                            \
"         b - binary float stdin and stdout (default is ASCII) \n"		\
"             Note: the input grid (from_data) is always binary.\n"		\
"             If binary is set, the location is not echoed to\n"		\
"             the output but the data values are written in the\n"		\
"             same order as the input points.\n"			\
"         e - If binary is not set, then output ASCII in exponential (%15.8e)\n"\
"             format (default is %f). If binary is set, then -e is ignored.\n"  \
"         i fill - fill value for missing data (default = 0)\n"			\
"         n min_value - treat values less than min_value as missing data\n"	\
"         x max_value - treat values greater than max_value as missing data\n"	\
"         B - 1 byte input data\n"                                              \
"         U - unsigned input data (default is signed)\n"                        \
"         S - short (2 byte) input data\n"                                      \
"         L - long (4 byte) input data\n"                                       \
"         F - float (4 byte) input data (default)\n"                            \
"         c method - choose interpolation method\n"				\
"                    N = nearest neighbor (default)\n"				\
"                    D = drop-in-the-bucket\n"					\
"                    B = bilinear\n"						\
"                    C = cubic convolution\n"					\
"                    I = inverse distance\n"					\
"         r radius - circle to average over (-c D or I only) \n"		\
"         p power - inverse distance exponent (default = 2, -c I only) \n"	\
"         C - output a value for the center of each cell.\n"                    \
"             Note: If -C is specified, then stdin, -b, -c method, -r radius,\n"\
"             and -p power are ignored.\n"                                      \
"         I - supress output of missing or invalid data.\n"                     \
"             Note: If -C is not specified, then -I is ignored.\n"              \
"         R lat_min lat_max lon_min lon_max - specifies latitude and longitude\n"\
"           ranges for which output is desired.\n"                              \
"           Note: If -C is not specified, then -R is ignored.\n"                \
"\n"

static int verbose = 0;

struct interp_control {
  grid_class *grid;
  bool do_binary;
  bool do_exponential;
  bool min_set;
  float min_value;
  bool max_set;
  float max_value;
  bool unsigned_data;
  bool float_data;
  int bytes_per_cell;
  float fill_value;
  float shell_radius;
  float power;
  bool use_center;
  bool supress_missing;
  float lat_min;
  float lat_max;
  float lon_min;
  float lon_max;
};

static int cubic(float *value, float **from_data, double r, double s, 
		 struct interp_control *control);
static int nearest(float *value, float **from_data, double r, double s,
		   struct interp_control *control);
static int average(float *value, float **from_data, double r, double s, 
		   struct interp_control *control);
static int bilinear(float *value, float **from_data, double r, double s, 
		    struct interp_control *control);
static int distance(float *value, float **from_data, double r, double s, 
		    struct interp_control *control);
static int read_row(float *row_from_data, FILE *from_file, void *row_buf,
		    struct interp_control *control);
static int process_row_use_center(float *row_from_data, int row,
				  struct interp_control *control);
static int write_point(double to_lat, double to_lon, float value,
		       struct interp_control *control);
static char possible_methods[] = "NDBCI";

static int (*method_function[])()  = { nearest,
				       average,
				       bilinear,
				       cubic,
				       distance };

static char *method_string[] = { "nearest-neighbor",
				 "drop-in-the-bucket",
				 "bilinear",
				 "cubic convolution",
				 "inverse distance" };


int main(int argc, char *argv[]) { 
  int io_err, status, method_number, line_num, row;
  double to_lat, to_lon;
  double from_r, from_s;
  float **from_data;
  float value;
  char *option, *position;
  char method;
  char readln[MAX_STRING];
  char from_filename[FILENAME_MAX];
  FILE *from_file;
  int (*interpolate)();
  struct interp_control control;
  int rows_in_from_data;
  int row_to_store;
  int points_processed;
  void *row_buf;

/*
 * set defaults
 */
  control.min_set = FALSE;
  control.max_set = FALSE;
  control.unsigned_data = FALSE;
  control.float_data = TRUE;
  control.bytes_per_cell = 4;
  control.fill_value = 0;
  control.shell_radius = 0.5;
  control.power = 2;
  control.use_center = FALSE;
  control.supress_missing = FALSE;
  control.lat_min = -90;
  control.lat_max = 90;
  control.lon_min = -180;
  control.lon_max = 180;
  control.do_binary = FALSE;
  control.do_exponential = FALSE;
  method = 'N';

/* 
 * get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-') {
    for (option = argv[0]+1; *option != '\0'; option++) {
      switch (*option) {
	case 'v':
	  ++verbose;
	  break;
	case 'b':
	  control.do_binary = TRUE;
	  break;
        case 'e':
          control.do_exponential = TRUE;
          break;
	case 'c':
	  ++argv; --argc;
	  method = *argv[0];
	  break;
	case 'r':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.shell_radius)) != 1) error_exit(usage);
	  break;
	case 'n':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.min_value)) != 1) error_exit(usage);
	  control.min_set = TRUE;
	  break;
	case 'x':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.max_value)) != 1) error_exit(usage);
	  control.max_set = TRUE;
	  break;
	case 'i':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.fill_value)) != 1) error_exit(usage);
	  break;
	case 'p':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.power)) != 1) error_exit(usage);
	  break;
	case 'V':
	  fprintf(stderr,"%s\n", ungrid_c_rcsid);
	  break;
        case 'B':
	  control.bytes_per_cell = 1;
	  control.float_data = FALSE;
	  break;
        case 'U':
	  control.unsigned_data = TRUE;
	  break;
        case 'S':
	  control.bytes_per_cell = 2;
	  control.float_data = FALSE;
	  break;
        case 'L':
	  control.bytes_per_cell = 4;
	  control.float_data = FALSE;
	  break;
        case 'F':
	  control.float_data = TRUE;
	  break;
        case 'C':
	  control.use_center = TRUE;
	  break;
        case 'I':
	  control.supress_missing = TRUE;
	  break;
        case 'R':
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.lat_min)) != 1) error_exit(usage);
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.lat_max)) != 1) error_exit(usage);
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.lon_min)) != 1) error_exit(usage);
	  ++argv; --argc;
	  if (sscanf(*argv, "%f", &(control.lon_max)) != 1) error_exit(usage);
	  break;
	default:
	  fprintf(stderr,"invalid option %c\n", *option);
	  error_exit(usage);
      }
    }
  }

/*
 * make options consistent
 */
  if (control.float_data) {
    control.bytes_per_cell = 4;
    control.unsigned_data = FALSE;
  }
  if (control.use_center) {
    control.do_binary = FALSE;
    while (control.lon_min > 180)
      control.lon_min -= 360;
    while (control.lon_max > 180)
      control.lon_max -= 360;
    while (control.lon_min < -180)
      control.lon_min += 360;
    while (control.lon_max < -180)
      control.lon_max += 360;
  } else {
    control.supress_missing = FALSE;
    control.lat_min = -90;
    control.lat_max = 90;
    control.lon_min = -180;
    control.lon_max = 180;
  }
  
/*
 * validate method option
 */
  position = strchr(possible_methods, method);
  if (!position) {
    fprintf(stderr,"resamp: method %c not in [%s]\n",
	    method, possible_methods);
    error_exit(usage);
  }
  method_number = position - possible_methods;
  interpolate = method_function[method_number];

/*
 * get command line arguments
 */
  if (argc != 2) error_exit(usage);

  control.grid = init_grid(*argv);
  if (!control.grid) error_exit("ungrid: ABORTING");
  ++argv; --argc;

  strcpy(from_filename, *argv);
  from_file = fopen(from_filename, "r");
  if (!from_file) { perror(from_filename); error_exit("ungrid: ABORTING"); }
  ++argv; --argc;

/*
 * echo defaults and settings
 */
  if (verbose) {
    fprintf(stderr,"> Data grid:\t%s\n", control.grid->gpd_filename);
    fprintf(stderr,"> Data file:\t%s\n", from_filename);
    if (!control.use_center)
      fprintf(stderr,"> Method:\t%c = %s\n",
	      method, method_string[method_number]);
    fprintf(stderr,"> Fill value:\t%g\n", control.fill_value);
    if (control.min_set) fprintf(stderr,"> Valid min:\t%g\n", control.min_value);
    if (control.max_set) fprintf(stderr,"> Valid max:\t%g\n", control.max_value);
    if (!control.use_center) {
      fprintf(stderr,"> Shell radius:\t%g\n", control.shell_radius);
      if (method == 'I') fprintf(stderr,"> Power:\t%g\n", control.power);
    }
    fprintf(stderr,"> Format:\t%s\n",
                   control.do_binary ? "binary" : 
                               (control.do_exponential ?
				"ascii %15.8e" : "ascii %f"));
    if (control.use_center) {
      fprintf(stderr, "> Output a value for the center of each cell.\n");
      fprintf(stderr, "> Supress output for missing or invalid data.\n");
      fprintf(stderr, "> Latitude range:\t%g\tto\t%g\n",
	      control.lat_min, control.lat_max);
      fprintf(stderr, "> Longitude range:\t%g\tto\t%g\n",
	      control.lon_min, control.lon_max);
    }
  }

/*
 * read in grid of input data values a row at a time
 */
  row_buf = calloc(control.grid->cols, control.bytes_per_cell);
  if (!row_buf) { error_exit("ungrid: ABORTING"); }

  rows_in_from_data = control.use_center ? 1 : control.grid->rows;
  from_data = (float **)matrix(rows_in_from_data, control.grid->cols,
			       sizeof(float), TRUE);
  if (!from_data) { error_exit("ungrid: ABORTING"); }

  points_processed = 0;
  for (row = 0; row < control.grid->rows; row++) {
    row_to_store = control.use_center ? 0 : row;
    status = read_row(from_data[row_to_store], from_file, row_buf, &control);
    if (status != control.grid->cols) {
      perror(from_filename);
      free(from_data);
      error_exit("ungrid: ABORTING");
    }
    /*
     * if outputting a value for the center of each cell,
     * then process this row of data.
     */
    if (control.use_center)
      points_processed +=
	process_row_use_center(from_data[row_to_store], row, &control);
  }

/*
 * loop through input points
 */
  for (line_num = 1; !control.use_center && !feof(stdin); line_num++) {

/*
 * read a point
 */
    if (control.do_binary) {
      fread(&to_lat, sizeof(to_lat), 1, from_file);
      fread(&to_lon, sizeof(to_lon), 1, from_file);
      io_err = ferror(from_file);
    } else {
      fgets(readln, MAX_STRING, stdin);
      io_err = (sscanf(readln, "%lf %lf", &to_lat, &to_lon) != 2);
    }

    if (io_err != 0) { 
      fprintf(stderr, "ungrid: error reading lat/lon at line %i\n", line_num);
      if (control.do_binary) error_exit("ungrid: ABORTING");
      continue;
    }

    if (feof(stdin)) break;

/*
 * extract data from grid
 */
    value = control.fill_value;

    status = forward_grid(control.grid, to_lat, to_lon, &from_r, &from_s);
    if (!status) {
      if (verbose >= 2) 
	fprintf(stderr,">> line %d lat/lon %f %f is off the grid\n",
		line_num, to_lat, to_lon);

    } else {

      status = interpolate(&value, from_data, from_r, from_s, &control);
      if (status < 0) {
	if (verbose >= 2) fprintf(stderr,">> can't interpolate to %f %f at line %d\n",
				  to_lat, to_lon, line_num);
      }
    }

/*
 * write the point
 */
    io_err = write_point(to_lat, to_lon, value, &control);

    if (io_err != 0) {
      perror("writing to stdout");
      fprintf(stderr, "ungrid: line %d\n", line_num);
    }
    points_processed++;
  }

  if (verbose) fprintf(stderr,"> %d points processed\n", points_processed);

  exit(EXIT_SUCCESS);
}

/*------------------------------------------------------------------------
 * cubic - cubic convolution
 *
 *	input : from_data - pointer to input data array
 *              r, s - column, row coordinates within input grid
 *              control - control parameter structure
 *
 *	output: value - data value interpolated to r,s
 *
 *	result: number of valid points sampled
 *
 *------------------------------------------------------------------------*/
static int cubic(float *value, float **from_data, double r, double s, 
		 struct interp_control *control) {
  int col, row, npts;
  double dr, ds, ccr[4], ccs[4], ccr_col, ccs_row;
  double weight, value_sum, weight_sum;
 
/*
 * get cubic coefficients
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

  value_sum = 0.;
  weight_sum = 0.;
  npts = 0;

/*
 * interpolated value is weighted sum of sixteen surrounding samples
 */
  for (row = (int)s - 1; row <= (int)s + 2; row++) {
    if (row < 0 || row >= control->grid->rows ) continue;

    ccs_row = ccs[row - ((int)s - 1)];

    for (col = (int)r - 1; col <= (int)r + 2; col++) {
      if (col < 0 || col >= control->grid->cols) continue;

      if (control->max_set && control->max_value < from_data[row][col]) continue;
      if (control->min_set && control->min_value > from_data[row][col]) continue;

      ccr_col = ccr[col - ((int)r - 1)];

      weight = ccs_row*ccr_col;

      value_sum += weight*from_data[row][col];
      weight_sum += weight;
      ++npts;
    }
  }

  if (npts > 0) {
    *value = value_sum;
    if (weight_sum != 0) *value /= weight_sum;
  } else {
    *value = control->fill_value;
  }

  return npts;
}

/*------------------------------------------------------------------------
 * average - weighted average within a radius
 *
 *	input : from_data - pointer to input data array
 *              r, s - column, row coordinates within input grid
 *              control - control parameter structure
 *
 *	output: value - data value interpolated to r,s
 *
 *	result: number of valid points sampled
 *
 *------------------------------------------------------------------------*/
static int average(float *value, float **from_data, double r, double s, 
		   struct interp_control *control) {
  int col, row, half_width;
  double dr, ds, dr2, ds2, r2, value_sum;
  int npts;

  r2 = control->shell_radius*control->shell_radius;

  value_sum = 0;
  npts = 0;

  half_width = ceil((double)control->shell_radius);
  if (half_width < 1) half_width = 1;

  for (row=(int)s - (half_width-1); row <= (int)s + half_width; row++) {
    if (row < 0 || row >= control->grid->rows) continue;

    ds = row - s;
    ds2 = ds*ds;

    for (col=(int)r - (half_width-1); col <= (int)r + half_width; col++) {
      if (col < 0 || col >= control->grid->cols) continue;
      if (control->max_set && control->max_value < from_data[row][col]) continue;
      if (control->min_set && control->min_value > from_data[row][col]) continue;

      dr = col - r;
      dr2 = dr*dr;

      if ((dr2 + ds2) <= r2) {
	value_sum += from_data[row][col];
	++npts;
      }
    }
  }

  if (npts > 0) {
    *value = value_sum/npts;
  } else {
    *value = control->fill_value;
  }

  return npts;
}

/*------------------------------------------------------------------------
 * bilinear - bilinear interpolation
 *
 *	input : from_data - pointer to input data array
 *              r, s - column, row coordinates within input grid
 *              control - control parameter structure
 *
 *	output: value - data value interpolated to r,s
 *
 *	result: number of valid points sampled
 *
 *------------------------------------------------------------------------*/
static int bilinear(float *value, float **from_data, double r, double s, 
		    struct interp_control *control) {
  int col, row;
  double dr, ds, weight, value_sum, weight_sum;
  int npts;

  value_sum = 0.;
  weight_sum = 0.;
  npts = 0;

  for (row=(int)s; row <= (int)s + 1; row++) {
    if (row < 0 || row >= control->grid->rows) continue;

    ds = fabs(s - row);

    for (col=(int)r; col <= (int)r + 1; col++) {
      if (col < 0 || col >= control->grid->cols) continue;
      if (control->max_set && control->max_value < from_data[row][col]) continue;
      if (control->min_set && control->min_value > from_data[row][col]) continue;

      dr = fabs(r - col);

      weight = (1 - ds)*(1 - dr);
      value_sum += weight*from_data[row][col];
      weight_sum += weight;
      ++npts;
    }
  }

  if (weight_sum > 0) {
    *value = value_sum/weight_sum;
  } else {
    *value = control->fill_value;
  }

  return npts;
}

/*------------------------------------------------------------------------
 * nearest - nearest-neighbor
 *
 *	input : from_data - pointer to input data array
 *              r, s - column, row coordinates within input grid
 *              control - control parameter structure
 *
 *	output: value - data value interpolated to r,s
 *
 *	result: number of valid points sampled
 *
 *------------------------------------------------------------------------*/
static int nearest(float *value, float **from_data, double r, double s, 
		   struct interp_control *control) {
  int col, row;
  int npts=0;

  row = nint(s);
  col = nint(r);

  if (row < 0 || row >= control->grid->rows
      || col < 0 || col >= control->grid->cols) {
    *value = control->fill_value;
  } else {
    *value = from_data[row][col];
    if ((control->fill_value == *value) ||
	(control->max_set && control->max_value < *value) ||
	(control->min_set && control->min_value > *value))
      *value = control->fill_value;
    else
      npts = 1;
  }

  return npts;
}

/*------------------------------------------------------------------------
 * distance - normalized distance interpolation
 *
 *	input : from_data - pointer to input data array
 *              r, s - column, row coordinates within input grid
 *              control - control parameter structure
 *
 *	output: value - data value interpolated to r,s
 *
 *	result: number of valid points sampled
 *
 *------------------------------------------------------------------------*/
static int distance(float *value, float **from_data, double r, double s, 
		    struct interp_control *control) {
  int col, row, half_width;
  double dr, ds, dr2, ds2, dd, weight, value_sum, weight_sum;
  int npts;

  value_sum = 0;
  weight_sum = 0;
  npts = 0;

  half_width = ceil((double)control->shell_radius);
  if (half_width < 1) half_width = 1;

  for (row=(int)s - (half_width-1); row <= (int)s + half_width; row++) {
    if (row < 0 || row >= control->grid->rows) continue;

    ds = row - s;
    ds2 = ds*ds;

    for (col=(int)r - (half_width-1); col <= (int)r + half_width; col++) {
      if (col < 0 || col >= control->grid->cols) continue;
      if (control->max_set && control->max_value < from_data[row][col]) continue;
      if (control->min_set && control->min_value > from_data[row][col]) continue;

      dr = col - r;
      dr2 = dr*dr;

      dd = sqrt(dr2 + ds2);

      weight = dd <= control->shell_radius ? pow(dd,-control->power) : 0.0;

      value_sum += weight*from_data[row][col];
      weight_sum += weight;
      ++npts;
    }
  }

  if (npts > 0) {
    *value = value_sum;
    if (weight_sum != 0) *value /= weight_sum;
  } else {
    *value = control->fill_value;
  }

  return npts;
}

/*------------------------------------------------------------------------
 * read_row - read a row of data, convert it to floating-point,
 *            and store it in from_data
 *
 *	input : from_data - pointer to current row of float input data
 *              from_file - file pointer for input file
 *              row_buf - buffer to use for reading a row of input data
 *              control - control parameter structure
 *
 *	output: none.
 *
 *	result: status from read
 *
 *------------------------------------------------------------------------*/
static int read_row(float *row_from_data, FILE *from_file, void *row_buf,
		    struct interp_control *control) {
  int status;
  int col;

  status = fread(row_buf, control->bytes_per_cell,
		 control->grid->cols, from_file);
  for (col = 0; col < control->grid->cols; col++) {
    if (control->float_data) {
      row_from_data[col] = ((float *)(row_buf))[col];
    } else {
      switch (control->bytes_per_cell) {
      case 1:
	row_from_data[col] = control->unsigned_data ?
	  ((unsigned char *)(row_buf))[col] :
	  ((char *)(row_buf))[col];
	break;
      case 2:
	row_from_data[col] = control->unsigned_data ?
	  ((unsigned short *)(row_buf))[col] :
	  ((short *)(row_buf))[col];
	break;
      case 4:
	row_from_data[col] = control->unsigned_data ?
	  ((unsigned int *)(row_buf))[col] :
	  ((int *)(row_buf))[col];
	break;
      }
    }
  }

  return status;
}

/*------------------------------------------------------------------------
 * process_row_use_center - process a row of image data using the center
 *                          value of each cell
 *
 *	input : row_from_data - pointer to current row of float input data
 *              row - row coordinate within input grid
 *              control - control parameter structure
 *
 *	output: none.
 *
 *	result: number of valid points sampled
 *
 *------------------------------------------------------------------------*/
static int process_row_use_center(float *row_from_data, int row,
				  struct interp_control *control) {
  int col;
  int status;
  double to_lat, to_lon;
  double from_r, from_s;
  float value;
  int io_err;
  int npts = 0;

  from_s = row;
  for (col = 0; col < control->grid->cols; col++) {
    from_r = col;
    status = inverse_grid(control->grid, from_r, from_s, &to_lat, &to_lon);
    if (!status) {
	fprintf(stderr,">> col/row: %d %d   lat/lon: %f %f is off the grid\n",
		col, row, to_lat, to_lon);
	error_exit("ungrid: ABORTING");
    }
    if (control->lat_min > to_lat || control->lat_max < to_lat ||
	control->lon_min > to_lon || control->lon_max < to_lon)
      continue;
    value = row_from_data[col];
    if ((control->max_set && control->max_value < value) ||
	(control->min_set && control->min_value > value))
      value = control->fill_value;
    if (!control->supress_missing || control->fill_value != value) {
      npts++;
      io_err = write_point(to_lat, to_lon, value, control);
      if (io_err != 0) {
	perror("writing to stdout");
	fprintf(stderr, "ungrid: col/row: %d %d\n", col, row);
      }
    }
  }
  
  return npts;
}

/*------------------------------------------------------------------------
 * write_point - write the information for a single point to stdout
 *
 *	input : to_lat - latitude of point
 *              to_lon - longitude of point
 *              value - value of point
 *              control - control parameter structure
 *
 *	output: none.
 *
 *	result: io_err from write
 *
 *------------------------------------------------------------------------*/
static int write_point(double to_lat, double to_lon, float value,
		       struct interp_control *control) {
  int io_err;

  if (control->do_binary) {
    fwrite(&value, sizeof(value), 1, stdout);
    io_err = ferror(stdout);
  } else {
    if (control->do_exponential)
      printf("%15.8e %15.8e %15.8e\n", to_lat, to_lon, value);
    else
	printf("%f %f %f\n", to_lat, to_lon, value);
    io_err = ferror(stdout);
  }

  return io_err;
}
