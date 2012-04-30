/*========================================================================
 * fornav - forward navigation using elliptical weighted average
 *
 * 27-Dec-2000 T.Haran tharan@kryos.colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char fornav_c_rcsid[] = "$Header: /export/data/ms2gth/src/fornav/fornav.c,v 1.22 2001/05/24 23:26:13 haran Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "matrix.h"

#define USAGE \
"usage: fornav chan_count\n"\
"              [-v] [-m]\n"\
"              [-s chan_scan_first colrow_scan_first]\n"\
"       defaults:         0                 0\n"\
"              [-S grid_col_start grid_row_start]\n"\
"       defaults:         0                     0              0\n"\
"              [-t swath_data_type_1 ... swath_data_type_chan_count]\n"\
"       defaults:          s2                       s2\n"\
"              [-T grid_data_type_1 ... grid_data_type_chan_count]\n"\
"       defaults:  swath_data_type_1    swath_data_type_chan_count]\n"\
"              [-f swath_fill_1 ... swath_fill_chan_count]\n"\
"       defaults:       0                      0\n"\
"              [-F grid_fill_1 ... grid_fill_chan_count]\n"\
"       defaults:  swath_fill_1    swath_fill_chan_count\n"\
"              [-r col_row_fill]\n"\
"       defaults:     -1e30\n"\
"              [-c weight_count] [-w weight_min] [-d weight_distance_max]\n"\
"       defaults:     10000             .01               1.0\n"\
"              [-D weight_delta_max] [-W weight_sum_min]\n"\
"       defaults:       10.0               weight_min\n"\
"              swath_cols swath_scans swath_rows_per_scan\n"\
"              swath_col_file swath_row_file\n"\
"              swath_chan_file_1 ... swath_chan_file_chan_count\n"\
"              grid_cols grid_rows\n"\
"              grid_chan_file_1 ... grid_chan_file_chan_count\n"\
"\n"\
" input : chan_count: number of input and output channel files. This parameter\n"\
"           must precede any specified options.\n"\
"         swath_cols: number of columns in each input swath file.\n"\
"         swath_scans: number of scans in each input swath file.\n"\
"         swath_rows_per_scan: number of swath rows constituting a scan.\n"\
"           Must be at least 2.\n"\
"         swath_col_file: file containing the projected column number of each\n"\
"           swath cell and consisting of swatch_cols x swath_rows of 4 byte\n"\
"           floating-point numbers.\n"\
"         swath_row_file: file containing the projected row number of each\n"\
"           swath cell and consisting of swatch_cols x swath_rows of 4 byte\n"\
"           floating-point numbers.\n"\
"         swath_chan_file_1 ... swath_chan_file_chan_count: swath channel files\n"\
"           1 through chan_count. Each file consists of swath_cols x swath_rows\n"\
"           cells as indicated by swath_data_type (see below).\n"\
"         grid_cols: number of columns in each output grid file.\n"\
"         grid_rows: number of rows in each output grid file.\n"\
"\n"\
" output: grid_chan_file_1 ... grid_chan_file_chan_count: grid channel files\n"\
"           1 through chan_count. Each file consists of grid_cols x grid_rows\n"\
"           cells as indicated by grid_type (see below).\n"\
"\n"\
" option: v: verbose (may be repeated).\n"\
"         m: maximum weight mode. If -m is not present, a weighted average of\n"\
"             all swath cells that map to a particular grid cell is used.\n"\
"             If -m is present, the swath cell having the maximum weight of all\n"\
"             swath cells that map to a particular grid cell is used. The -m\n"\
"             option should be used for coded data, i.e. snow cover.\n"\
"         s chan_scan_first colrow_scan_first: the first scan number to process\n"\
"             in the swath channel files and column and row files, respectively.\n"\
"             Default is 0 for both.\n"\
"         S grid_col_start grid_row_start: starting grid column number and row\n"\
"             number to write to each output grid file. The defaults are 0.\n"\
"         t swath_data_type_1 ... swath_data_type_chan_count: specifies the type\n"\
"             of each swath cell for each channel as follows:\n"\
"               u1: unsigned 8-bit integer.\n"\
"               u2: unsigned 16-bit integer.\n"\
"               s2: signed 16-bit integer (default).\n"\
"               u4: unsigned 32-bit integer.\n"\
"               s4: signed 32-bit integer.\n"\
"               f4: 32-bit floating-point.\n"\
"         T grid_data_type_1 ... grid_data_type_chan_count: specifies the type\n"\
"             of each grid cell for each channel as in the -t option. If the\n"\
"             default value is the corresponding swath data type value.\n"\
"         f swath_fill_1 ... swath_fill_chan_count: specifies fill value to use\n"\
"             for detecting any missing cells in each swath file. Missing swath\n"\
"             cells are ignored. The default value is 0.\n"\
"         F grid_fill_1 ... grid_fill_chan_count: specifies fill value to use\n"\
"             for any unmapped cells in each grid file. The default value is the\n"\
"             corresponding swath fill value.\n"\
"         r col_row_fill: specifies fill value to use for detecting any\n"\
"             missing cells in each column and row file. Missing swath cells\n"\
"             are ignored. The default value is -1e30.\n"\
"         c weight_count: number of elements to create in the gaussian weight\n"\
"             table. Default is 10000. Must be at least 2.\n"\
"         w weight_min: the minimum value to store in the last position of the\n"\
"             weight table. Default is 0.01, which, with a weight_distance_max\n"\
"             of 1.0 produces a weight of 0.01 at a grid cell distance of 1.0.\n"\
"             Must be greater than 0.\n"\
"         d weight_distance_max: distance in grid cell units at which to apply a\n"\
"             weight of weight_min. Default is 1.0. Must be greater than 0.\n"\
"         D weight_delta_max: maximum distance in grid cells in each grid\n"\
"             dimension over which to distribute a single swath cell.\n"\
"             Default is 10.0.\n"\
"         W weight_sum_min: minimum weight sum value. Cells whose weight sums\n"\
"             are less than weight_sum_min are set to the grid fill value.\n"\
"             Default is weight_sum_min.\n"\
"\n"

#define TYPE_UNDEF  0
#define TYPE_BYTE   1
#define TYPE_UINT2  2
#define TYPE_SINT2  3
#define TYPE_UINT4  4
#define TYPE_SINT4  5
#define TYPE_FLOAT  6

#define EPSILON (1e-8)

typedef struct {
  char  *name;
  char  *file;
  FILE  *fp;
  char  *open_type_str;
  char  *data_type_str;
  int   data_type;
  int   bytes_per_cell;
  float fill;
  int   cols;
  int   rows;
  int   bytes_per_row;
  void  **buf;
} image;

typedef struct {
  float a;
  float b;
  float c;
  float f;
  float u_del;
  float v_del;
} ewa_parameters;

typedef struct {
  int   count;
  float min;
  float distance_max;
  float delta_max;
  float sum_min;
  float alpha;
  float qmax;
  float qfactor;
  float *wtab;
  float *swath_chan_buf;
  float *swath_fill_buf;
  float **grid_chan_buf;
  float *grid_fill_buf;
  float col_row_fill;
} ewa_weight;

static int verbose;
static int very_verbose;

static void DisplayUsage(void)
{
  error_exit(USAGE);
}

static void DisplayInvalidParameter(char *param)
{
  fprintf(stderr, "fornav: Parameter %s is invalid.\n", param);
  DisplayUsage();
}

static void InitializeImage(image *ip, char *name, char *open_type_str,
                            char *data_type_str, int cols, int rows,
                            int swath_scan_first)
{
  if (very_verbose)
    fprintf(stderr, "Initializing %s\n", name);
  ip->name = strdup(name);
  ip->open_type_str = strdup(open_type_str);
  if (strlen(ip->open_type_str)) {
    if ((ip->fp = fopen(ip->file, ip->open_type_str)) == NULL) {
      fprintf(stderr, "fornav: InitializeImage: error opening %s\n", ip->file);
      perror("fornav");
      exit(ABORT);
    }
  } else
    ip->fp = NULL;
  ip->data_type_str = strdup(data_type_str);
  if (!strcmp(ip->data_type_str, "u1"))
    ip->data_type = TYPE_BYTE;
  else if (!strcmp(ip->data_type_str, "u2"))
    ip->data_type = TYPE_UINT2;
  else if (!strcmp(ip->data_type_str, "s2"))
    ip->data_type = TYPE_SINT2;
  else if (!strcmp(ip->data_type_str, "u4"))
    ip->data_type = TYPE_UINT4;
  else if (!strcmp(ip->data_type_str, "s4"))
    ip->data_type = TYPE_SINT4;
  else if (!strcmp(ip->data_type_str, "f4"))
    ip->data_type = TYPE_FLOAT;
  else
    ip->data_type = TYPE_UNDEF;

  switch (ip->data_type) {
  case TYPE_BYTE:
    ip->bytes_per_cell = 1;
    break;
  case TYPE_UINT2:
  case TYPE_SINT2:
    ip->bytes_per_cell = 2;
    break;
  case TYPE_UINT4:
  case TYPE_SINT4:
  case TYPE_FLOAT:
    ip->bytes_per_cell = 4;
    break;
  case TYPE_UNDEF:
  default:
    error_exit("fornav: InitializeImage: Undefined data type");
    break;
  }

  ip->cols = cols;
  ip->rows = rows;
  ip->bytes_per_row = ip->bytes_per_cell * cols;
  ip->buf = matrix(ip->rows, ip->cols, ip->bytes_per_cell, 1);
  if (ip->buf == NULL) {
    fprintf(stderr, "Error initializing %s\n", name);
    error_exit("fornav: InitializeImage: can't allocate memory for buffer");
  }
  
  if (!strcmp(ip->open_type_str, "r")) {
    int offset;
    offset = ip->bytes_per_row * ip->rows * swath_scan_first;
    if (very_verbose)
      fprintf(stderr, "seeking to byte %d in %s\n", offset, ip->file);
    if (fseek(ip->fp, offset, 0) != 0) {
      fprintf(stderr,
              "fornav: InitializeImage: error seeking to byte %d in %s\n",
              offset, ip->file);
      perror("fornav");
      exit(ABORT);
    }
  }
}

static void DeInitializeImage(image *ip)
{
  if (very_verbose)
    fprintf(stderr, "DeInitializing %s\n", ip->name);
  if (ip->name)
    free(ip->name);
  if (ip->open_type_str)
    free(ip->open_type_str);
  if (ip->data_type_str)
    free(ip->data_type_str);
  if (ip->fp)
    fclose(ip->fp);
  if (ip->buf)
    free(ip->buf);
}

static void ReadImage(image *ip)
{
  if (very_verbose)
    fprintf(stderr, "Reading %s\n", ip->file);
  if (fread(ip->buf[0], ip->bytes_per_row, ip->rows, ip->fp) != ip->rows) {
    fprintf(stderr, "fornav: ReadImage: error reading %s\n", ip->file);
    perror("fornav");
    exit(ABORT);
  }
}

static void InitializeWeight(int chan_count,
                             int weight_count, float weight_min,
                             float weight_distance_max,
                             float weight_delta_max, float weight_sum_min,
                             float col_row_fill,
                             ewa_weight *ewaw)
{
  float  *wptr;
  int    i;

  if (very_verbose)
    fprintf(stderr, "Initializing weight structure\n");
  ewaw->count        = weight_count;
  ewaw->min          = weight_min;
  ewaw->distance_max = weight_distance_max;
  ewaw->delta_max    = weight_delta_max;
  ewaw->sum_min      = weight_sum_min;
  ewaw->col_row_fill = col_row_fill;

  ewaw->wtab         = (float *)calloc(weight_count, sizeof(float));
  if (ewaw->wtab == NULL)
    error_exit("fornav: InitializeWeight: can't allocate memory for wtab");

  ewaw->swath_chan_buf = (float *)calloc(chan_count, sizeof(float));
  if (ewaw->swath_chan_buf == NULL)
    error_exit("fornav: InitializeWeight: can't allocate memory for swath_chan_buf");

  ewaw->swath_fill_buf = (float *)calloc(chan_count, sizeof(float));
  if (ewaw->swath_fill_buf == NULL)
    error_exit("fornav: InitializeWeight: can't allocate memory for swath_fill_buf");

  ewaw->grid_chan_buf = (float **)calloc(chan_count, sizeof(float *));
  if (ewaw->grid_chan_buf == NULL)
    error_exit("fornav: InitializeWeight: can't allocate memory for grid_chan_buf");

  ewaw->grid_fill_buf = (float *)calloc(chan_count, sizeof(float));
  if (ewaw->grid_fill_buf == NULL)
    error_exit("fornav: InitializeWeight: can't allocate memory for grid_fill_buf");

  if (weight_count < 2)
    error_exit("fornav: InitializeWeight: weight_count must be at least 2");
  if (weight_min <= 0.0)
    error_exit("fornav: InitializeWeight: weight_min must be greater than 0");
  if (weight_distance_max <= 0.0)
    error_exit("fornav: InitializeWeight: weight_distance_max must be greater than 0");
  ewaw->qmax = ewaw->distance_max * ewaw->distance_max;
  ewaw->alpha = -log(ewaw->min) / ewaw->qmax;
  wptr = ewaw->wtab;
  for (i = 0; i < weight_count; i++)
    *wptr++ = exp(-ewaw->alpha * ewaw->qmax * (float)i / (ewaw->count - 1));

  /*
   *  Use i = (int)(q * ewaw->qfactor) to get element number i of wtab
   *  corresponding to q.
   *  Then for 0 < q < ewaw->qmax
   *    we have:
   *      0   < i              <= ewaw->count - 1
   *      1.0 > ewaw->wtab[i]  >= ewaw->min
   */

  ewaw->qfactor = ewaw->count / ewaw->qmax;
  if (very_verbose) {
    fprintf(stderr, "alpha = %f  qmax = %f\n",
            ewaw->alpha, ewaw->qmax);
    fprintf(stderr, "wtab[%d] = %f\n",
            0, ewaw->wtab[0]);
    fprintf(stderr, "wtab[%d] = %f\n",
            ewaw->count - 1, ewaw->wtab[ewaw->count - 1]);
  }
}

static void DeInitializeWeight(ewa_weight *ewaw)
{
  if (very_verbose)
    fprintf(stderr, "DeInitializing weight structure\n");
  if (ewaw->wtab)
    free(ewaw->wtab);
  if (ewaw->swath_chan_buf)
    free(ewaw->swath_chan_buf);
  if (ewaw->swath_fill_buf)
    free(ewaw->swath_fill_buf);
  if (ewaw->grid_chan_buf)
    free(ewaw->grid_chan_buf);
}

static void ComputeEwaParameters(image *uimg, image *vimg, ewa_weight *ewaw,
                                 ewa_parameters *ewap)
{
  int rowsm1;
  int colsm1;
  int rowsov2;
  int col;
  float *u_frst_row_this_col;
  float *u_last_row_this_col;
  float *v_frst_row_this_col;
  float *v_last_row_this_col;
  float *u_midl_row_prev_col;
  float *u_midl_row_next_col;
  float *v_midl_row_prev_col;
  float *v_midl_row_next_col;
  ewa_parameters *this_ewap;
  double ux;
  double uy;
  double vx;
  double vy;
  double f_scale;
  float qmax;
  float distance_max;
  float delta_max;
  float a;
  float b;
  float c;
  float d;
  float u_del;
  float v_del;

  if (very_verbose) {
    fprintf(stderr, "Computing ewa parameters\n");
    fprintf(stderr,
            " col            ux            vx            uy            vy             a             b             c         u_del         v_del\n");
  }
  rowsm1 = uimg->rows - 1;
  colsm1 = uimg->cols - 1;
  rowsov2 = uimg->rows / 2;
  qmax = ewaw->qmax;
  distance_max = ewaw->distance_max;
  delta_max = ewaw->delta_max;
  u_frst_row_this_col = (float *)(uimg->buf[0]) + 1;
  u_last_row_this_col = (float *)(uimg->buf[rowsm1]) + 1;
  v_frst_row_this_col = (float *)(vimg->buf[0]) + 1;
  v_last_row_this_col = (float *)(vimg->buf[rowsm1]) + 1;
  u_midl_row_prev_col = (float *)(uimg->buf[rowsov2]);
  u_midl_row_next_col = u_midl_row_prev_col + 2;
  v_midl_row_prev_col = (float *)(vimg->buf[rowsov2]);
  v_midl_row_next_col = v_midl_row_prev_col + 2;
  for (col = 1, this_ewap = ewap + 1;
       col < colsm1;
       col++, this_ewap++) {
    ux = (*u_midl_row_next_col++ - *u_midl_row_prev_col++) / 2 *
      distance_max;
    vx = (*v_midl_row_next_col++ - *v_midl_row_prev_col++) / 2 *
      distance_max;;
    uy = (*u_last_row_this_col++ - *u_frst_row_this_col++) / rowsm1 *
      distance_max;
    vy = (*v_last_row_this_col++ - *v_frst_row_this_col++) / rowsm1 *
      distance_max;

    /*
     *  scale a, b, c, and f equally so that f = qmax
     */
    f_scale = ux * vy - uy * vx;
    f_scale *= f_scale;
    if (f_scale > EPSILON) {
      f_scale = qmax / f_scale;
      a = (vx * vx + vy * vy) * f_scale;
      b = -2.0 * (ux * vx + uy * vy) * f_scale;
      c = (ux * ux + uy * uy) * f_scale;
    } else {
      a = 1.0;
      b = 0.0;
      c = 1.0;
    }
    d = 4.0 * a * c - b * b;
    d = (d > EPSILON) ? 4.0 * qmax / d : 1.0;
    this_ewap->a = a;
    this_ewap->b = b;
    this_ewap->c = c;
    this_ewap->f = qmax;
    u_del = sqrt(c * d);
    v_del = sqrt(a * d);
    if (u_del > delta_max)
      u_del = delta_max;
    if (v_del > delta_max)
      v_del = delta_max;
    this_ewap->u_del = u_del;
    this_ewap->v_del = v_del;
    if (very_verbose &&
        (col == 1 || col == uimg->cols / 2 || col == uimg->cols - 2))
      fprintf(stderr,
              "%4d %13e %13e %13e %13e %13e %13e %13e %13e %13e\n",
              col, ux, vx, uy, vy, a, b, c,
              this_ewap->u_del, this_ewap->v_del);
  }

  /*
   *  Copy the parameters from the penultimate column to the last column
   */
  this_ewap->a = (this_ewap - 1)->a;
  this_ewap->b = (this_ewap - 1)->b;
  this_ewap->c = (this_ewap - 1)->c;
  this_ewap->f = (this_ewap - 1)->f;
  this_ewap->u_del = (this_ewap - 1)->u_del;
  this_ewap->v_del = (this_ewap - 1)->v_del;

  /*
   *  Copy the parameters from the second column to the first column
   */
  this_ewap = ewap;
  this_ewap->a = (this_ewap + 1)->a;
  this_ewap->b = (this_ewap + 1)->b;
  this_ewap->c = (this_ewap + 1)->c;
  this_ewap->f = (this_ewap + 1)->f;
  this_ewap->u_del = (this_ewap + 1)->u_del;
  this_ewap->v_del = (this_ewap + 1)->v_del;
}

bool ComputeEwa(image *uimg, image *vimg,
                       ewa_weight *ewaw, ewa_parameters *ewap,
                       int chan_count, image *swath_chan_image,
                       bool maximum_weight_mode,
                       int grid_col_start, int grid_row_start,
                       image *grid_chan_image, image *grid_weight_image)
{
  int   row;
  int   rows;
  int   col;
  int   cols;
  float *u0p;
  float *v0p;
  float *wtab;
  float *weightp;
  float *this_weightp;
  float *swath_chanp;
  float *swath_fillp;
  float **grid_chanpp;
  float *grid_fillp;
  float *this_swath_chanp;
  float *this_swath_fillp;
  float **this_grid_chanpp;
  float *this_grid_fillp;
  void  *this_buf;
  bool  got_fill;
  bool  got_point;
  double col_row_fill;
  double u0;
  double v0;
  double u;
  double v;
  double ddq;
  double dq;
  double q;
  double a;
  double b;
  double c;
  double f;
  double a2up1;
  double bu;
  double au2;
  double weight;
  double qfactor;
  int   iu1;
  int   iu2;
  int   iv1;
  int   iv2;
  int   iu;
  int   iv;
  int   grid_cols;
  int   grid_rows;
  int   chan;
  int   weight_count;
  int   iw;
  int   swath_offset;
  int   grid_offset;
  image *this_swath;
  image *this_grid;
  ewa_parameters *this_ewap;

  if (very_verbose)
    fprintf(stderr, "Computing ewa\n");
  col_row_fill = ewaw->col_row_fill;
  rows = uimg->rows;
  cols = uimg->cols;
  grid_cols = grid_chan_image[0].cols;
  grid_rows = grid_chan_image[0].rows;
  wtab = ewaw->wtab;
  qfactor = ewaw->qfactor;
  weight_count = ewaw->count;
  swath_chanp = ewaw->swath_chan_buf;
  swath_fillp = ewaw->swath_fill_buf;
  grid_chanpp = ewaw->grid_chan_buf;
  grid_fillp  = ewaw->grid_fill_buf;
  weightp = grid_weight_image->buf[0];
  this_swath = swath_chan_image;
  this_grid = grid_chan_image;
  this_swath_fillp = swath_fillp;
  this_grid_chanpp = grid_chanpp;
  this_grid_fillp  = grid_fillp;
  for (chan = 0; chan < chan_count; chan++) {
    *this_swath_fillp++ = (this_swath++)->fill;
    *this_grid_chanpp++ = (float *)((this_grid)->buf[0]);
    *this_grid_fillp++ = (this_grid++)->fill;
  }
  got_point = FALSE;
  for (row = 0; row < rows; row++) {
    u0p = (float *)(uimg->buf[row]);
    v0p = (float *)(vimg->buf[row]);
    for (col = 0, this_ewap = ewap;
         col < cols;
         col++, this_ewap++) {
      u0 = *u0p++;
      v0 = *v0p++;
      if (u0 != col_row_fill && v0 != col_row_fill) {
        u0 -= grid_col_start;
        v0 -= grid_row_start;
        iu1 = (int)(u0 - this_ewap->u_del);
        iu2 = (int)(u0 + this_ewap->u_del);
        iv1 = (int)(v0 - this_ewap->v_del);
        iv2 = (int)(v0 + this_ewap->v_del);
        if (iu1 < 0)
          iu1 = 0;
        if (iu2 >= grid_cols)
          iu2 = grid_cols - 1;
        if (iv1 < 0)
          iv1 = 0;
        if (iv2 >= grid_rows)
          iv2 = grid_rows - 1;
        if (iu1 < grid_cols && iu2 >= 0 &&
            iv1 < grid_rows && iv2 >= 0) {
          got_point = TRUE;
          swath_offset = col + row * cols;
          this_swath = swath_chan_image;
          this_swath_chanp = swath_chanp;
          this_swath_fillp = swath_fillp;
          got_fill = FALSE;
          for (chan = 0; chan < chan_count; chan++, this_swath++) {
            this_buf = this_swath->buf[0];
            switch (this_swath->data_type) {
            case TYPE_BYTE:
              *this_swath_chanp = *((byte1 *)this_buf + swath_offset);
              break;
            case TYPE_UINT2:
              *this_swath_chanp = *((byte2 *)this_buf + swath_offset);
              break;
            case TYPE_SINT2:
              *this_swath_chanp = *((int2 *)this_buf + swath_offset);
              break;
            case TYPE_UINT4:
              *this_swath_chanp = *((byte4 *)this_buf + swath_offset);
              break;
            case TYPE_SINT4:
              *this_swath_chanp = *((int4 *)this_buf + swath_offset);
              break;
            case TYPE_FLOAT:
              *this_swath_chanp = *((float *)this_buf + swath_offset);
              break;
            }
            if (*this_swath_chanp++ == *this_swath_fillp++) {
              got_fill = TRUE;
              break;
            }
          } /* for (chan = 0; chan < chan_count; chan++, this_swath++) */
          a = this_ewap->a;
          b = this_ewap->b;
          c = this_ewap->c;
          f = this_ewap->f;
          ddq = 2.0 * a;
          u = iu1 - u0;
          a2up1 = a * (2.0 * u + 1.0);
          bu = b * u;
          au2 = a * u * u;
          for (iv = iv1; iv <= iv2; iv++) {
            v = iv - v0;
            dq = a2up1 + b * v;
            q = (c * v + bu) * v + au2;
            for (iu = iu1; iu <= iu2; iu++) {
              if (q < f) {
                iw = (int)(q * qfactor);
                if (iw >= weight_count)
                  iw = weight_count - 1;
                weight = wtab[iw];
                grid_offset = iu + iv * grid_cols;
                this_weightp = weightp + grid_offset;
                this_swath_chanp = swath_chanp;
                this_grid_fillp  = grid_fillp;
                this_grid_chanpp = grid_chanpp;
                if (maximum_weight_mode) {
                  if (weight > *this_weightp) {
                    *this_weightp = weight;
                    if (got_fill) {
                      for (chan = 0; chan < chan_count; chan++)
                        *((*this_grid_chanpp++) + grid_offset) =
                          *this_grid_fillp++;
                    } else {
                      for (chan = 0; chan < chan_count; chan++) {
                        *((*this_grid_chanpp++) + grid_offset) =
                          *this_swath_chanp++;
                      }
                    }
                  }
                } else if (!got_fill) {
                  *this_weightp += weight;
                  for (chan = 0; chan < chan_count; chan++) {
                      if (*(*this_grid_chanpp + grid_offset) == *this_grid_fillp++) {
                          // If the fill value is nonzero we don't want to
                          // effect the weight/grid values
                        *((*this_grid_chanpp++) + grid_offset) =
                          *this_swath_chanp++ * weight;
                      } else {
                        *((*this_grid_chanpp++) + grid_offset) +=
                          *this_swath_chanp++ * weight;
                      }
                  }
                }
              } /* if (q < f) */
              q += dq;
              dq += ddq;
            } /* for (iu = iu1; iu <= iu2; iu++) */
          } /* for (iv = iv1; iv <= iv2; iv++) */
        } /* if (iu1 < grid_cols && iu2 >= 0 && */
      } /* if (u0 != col_row_fill && v0 != col_row_fill) */
    } /* for (col = 0, this_ewap = ewap; */
  } /* for (row = 0; row < rows; row++) */
  return(got_point);
}

int WriteGridImage(image *ip, image *wp,
                   bool maximum_weight_mode, float weight_sum_min,
                   image *iop)
{
  float **chanpp;
  float *this_chanp;
  float **weightpp;
  float *this_weightp;
  float fill;
  float chanf;
  float roundoff;
  void  *chanp_out;
  byte1 *this_chanp_out;
  int   rows;
  int   row;
  int   cols;
  int   col;
  int   bytes_per_cell;
  int   bytes_per_row;
  int   rows_out;
  int   data_type;
  int   fill_count;
  FILE  *fp;

  if (very_verbose)
    fprintf(stderr, "Writing %s\n", iop->file);
  chanpp = (float **)(ip->buf);
  weightpp = (float **)(wp->buf);
  chanp_out = iop->buf[0];
  bytes_per_cell = iop->bytes_per_cell;
  bytes_per_row = iop->bytes_per_row;
  rows_out = iop->rows;
  fp = iop->fp;
  rows = ip->rows;
  cols = ip->cols;
  fill = iop->fill;
  data_type = iop->data_type;
  if (weight_sum_min <= 0.0)
    weight_sum_min = EPSILON;
  roundoff = (data_type == TYPE_FLOAT) ? 0.0 : 0.5;
  fill_count = 0;
  for (row = 0; row < rows; row++) {
    this_chanp = *chanpp++;
    this_weightp = *weightpp++;
    this_chanp_out = (byte1 *)chanp_out;
    for (col = 0;
         col < cols;
         col++,
           this_chanp++,
           this_weightp++,
           this_chanp_out += bytes_per_cell) {
      if (*this_weightp < weight_sum_min)
        chanf = fill;
      else if (maximum_weight_mode)
        chanf = *this_chanp;
      else if (*this_chanp >= 0.0)
        chanf = *this_chanp / *this_weightp + roundoff;
      else
        chanf = *this_chanp / *this_weightp - roundoff;
      switch (data_type) {
      case TYPE_BYTE:
        if (chanf < 0.0)
          chanf = 0.0;
        if (chanf > 255.0)
          chanf = 255.0;
        if (chanf == fill)
          fill_count++;
        *((byte1 *)this_chanp_out) = (byte1)chanf;
        break;
      case TYPE_UINT2:
        if (chanf < 0.0)
          chanf = 0.0;
        if (chanf > 65535.0)
          chanf = 65535.0;
        if (chanf == fill)
          fill_count++;
        *((byte2 *)this_chanp_out) = (byte2)chanf;
        break;
      case TYPE_SINT2:
        if (chanf < -32768.0)
          chanf = -32768.0;
        if (chanf > 32767.0)
          chanf = 32767.0;
        if (chanf == fill)
          fill_count++;
        *((int2 *)this_chanp_out) = (int2)chanf;
        break;
      case TYPE_UINT4:
        if (chanf < 0.0)
          chanf = 0.0;
        if (chanf > 4294967295.0)
          chanf = 4294967295.0;
        if (chanf == fill)
          fill_count++;
        *((byte4 *)this_chanp_out) = (byte4)chanf;
        break;
      case TYPE_SINT4:
        if (chanf < -2147483648.0)
          chanf = -2147483648.0;
        if (chanf > 2147483647.0)
          chanf = 2147483647.0;
        if (chanf == fill)
          fill_count++;
        *((int4 *)this_chanp_out) = (int4)chanf;
        break;
      case TYPE_FLOAT:
        if (chanf == fill)
          fill_count++;
        *((float *)this_chanp_out) = chanf;
        break;
      }
    } /* for (col = 0; col < cols; col++) */

    if (fwrite(chanp_out, bytes_per_row, rows_out, fp) != rows_out) {
      fprintf(stderr, "fornav: WriteGridImage: error writing %s\n",
              iop->file);
      perror("fornav");
      exit(ABORT);
    }
  } /* for (row = 0; row < rows; row++) */
  return(fill_count);
}

main (int argc, char *argv[])
{
  char  *option;
  int   chan_count;
  int   chan_scan_first;
  int   colrow_scan_first;
  int   grid_col_start;
  int   grid_row_start;
  bool  maximum_weight_mode;
  bool  got_grid_data_type;
  bool  got_grid_fill;
  int   first_scan_with_data;
  int   last_scan_with_data;
  int   weight_count;
  float weight_min;
  float weight_distance_max;
  float weight_delta_max;
  float weight_sum_min;
  bool  got_weight_sum_min;
  int   swath_cols;
  int   swath_scans;
  int   swath_rows_per_scan;
  int   grid_cols;
  int   grid_rows;
  int   fill_count;
  float col_row_fill;

  image  *swath_col_image;
  image  *swath_row_image;
  image  *swath_chan_image;
  image  *grid_chan_io_image;
  image  *grid_chan_image;
  image  *grid_weight_image;
  image  *ip;

  ewa_parameters *ewap;
  ewa_weight     ewaw;

  int   i;
  int   j;
  int   n;
  int   chan_scan_last;
  int   scan;
  float *fptr;
  float fill;
  
  /*
   *        set defaults
   */
  verbose                = FALSE;
  very_verbose           = FALSE;
  maximum_weight_mode    = FALSE;
  chan_scan_first        = 0;
  colrow_scan_first      = 0;
  grid_col_start         = 0;
  grid_row_start         = 0;
  got_grid_data_type     = FALSE;
  got_grid_fill          = FALSE;
  weight_count           = 10000;
  weight_min             = 0.01;
  weight_distance_max    = 1.0;
  weight_delta_max       = 10.0;
  got_weight_sum_min     = FALSE;
  col_row_fill           = -1e30;

  /*
   *  Get channel count and use it to allocate images and set default values
   */

  ++argv; --argc;
  if (argc <= 0)
    DisplayUsage();
  if (sscanf(*argv, "%d", &chan_count) != 1)
    DisplayInvalidParameter("chan_count");

  if ((swath_col_image = (image *)malloc(sizeof(image))) == NULL)
    error_exit("fornav: can't allocate swath_col_image\n");
  if ((swath_row_image = (image *)malloc(sizeof(image))) == NULL)
    error_exit("fornav: can't allocate swath_row_image\n");
  if ((swath_chan_image = (image *)calloc(chan_count, sizeof(image))) == NULL)
    error_exit("fornav: can't allocate swath_chan_image\n");
  if ((grid_chan_io_image = (image *)calloc(chan_count, sizeof(image))) == NULL)
    error_exit("fornav: can't allocate grid_chan_io_image\n");
  if ((grid_chan_image = (image *)calloc(chan_count, sizeof(image))) == NULL)
    error_exit("fornav: can't allocate grid_chan_image\n");
  if ((grid_weight_image = (image *)malloc(sizeof(image))) == NULL)
    error_exit("fornav: can't allocate grid_weight_image\n"); 

  for (i = 0; i < chan_count; i++) {
    ip = &swath_chan_image[i];
    ip->data_type_str = "s2";
    ip->fill = 0.0;

    ip = &grid_chan_io_image[i];
    ip->data_type_str = "s2";
    ip->fill = 0.0;
  }

  /* 
   *        Get command line options
   */
  while (--argc > 0 && (*++argv)[0] == '-') {
    for (option = argv[0]+1; *option != '\0'; option++) {
      switch (*option) {
      case 'v':
        if (verbose)
          very_verbose = TRUE;
        verbose = TRUE;
        break;
      case 'm':
        maximum_weight_mode = TRUE;
        break;
      case 's':
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("chan_scan_first");
        if (sscanf(*argv, "%d", &chan_scan_first) != 1)
          DisplayInvalidParameter("chan_scan_first");
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("colrow_scan_first");
        if (sscanf(*argv, "%d", &colrow_scan_first) != 1)
          DisplayInvalidParameter("colrow_scan_first");
        break;
      case 'S':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("grid_col_start");
        if (sscanf(*argv, "%d", &grid_col_start) != 1)
          DisplayInvalidParameter("grid_col_start");
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("grid_row_start");
        if (sscanf(*argv, "%d", &grid_row_start) != 1)
          DisplayInvalidParameter("grid_row_start");
        break;
      case 't':
        for (i = 0; i < chan_count; i++) {
          ++argv; --argc;
          if (argc <= 0)
            DisplayInvalidParameter("swath_data_type");
          if (strcmp(*argv, "u1") &&
              strcmp(*argv, "u2") &&
              strcmp(*argv, "s2") &&
              strcmp(*argv, "u4") &&
              strcmp(*argv, "s4") &&
              strcmp(*argv, "f4"))
            DisplayInvalidParameter("swath_data_type");
          swath_chan_image[i].data_type_str = *argv;
        }
        break;
      case 'T':
        got_grid_data_type = TRUE;
        for (i = 0; i < chan_count; i++) {
          ++argv; --argc;
          if (argc <= 0)
            DisplayInvalidParameter("grid_data_type");
          if (strcmp(*argv, "u1") &&
              strcmp(*argv, "u2") &&
              strcmp(*argv, "s2") &&
              strcmp(*argv, "u4") &&
              strcmp(*argv, "s4") &&
              strcmp(*argv, "f4"))
            DisplayInvalidParameter("grid_data_type");
          grid_chan_io_image[i].data_type_str = *argv;
        }
        break;
      case 'f':
        for (i = 0; i < chan_count; i++) {
          ++argv; --argc;
          if (argc <= 0)
            DisplayInvalidParameter("swath_fill");
          if (sscanf(*argv, "%f", &swath_chan_image[i].fill) != 1)
            DisplayInvalidParameter("swath_fill");
        }
        break;
      case 'F':
        got_grid_fill = TRUE;
        for (i = 0; i < chan_count; i++) {
          ++argv; --argc;
          if (argc <= 0)
            DisplayInvalidParameter("grid_fill");
          if (sscanf(*argv, "%f", &grid_chan_io_image[i].fill) != 1)
            DisplayInvalidParameter("grid_fill");
          grid_chan_image[i].fill = grid_chan_io_image[i].fill;
        }
        break;
      case 'r':
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("col_row_fill");
        if (sscanf(*argv, "%f", &col_row_fill) != 1)
          DisplayInvalidParameter("col_row_fill");
        break;
      case 'c':
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("weight_count");
        if (sscanf(*argv, "%d", &weight_count) != 1)
          DisplayInvalidParameter("weight_count");
        break;
      case 'w':
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("weight_min");
        if (sscanf(*argv, "%f", &weight_min) != 1)
          DisplayInvalidParameter("weight_min");
        break;
      case 'd':
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("weight_distance_max");
        if (sscanf(*argv, "%f", &weight_distance_max) != 1)
          DisplayInvalidParameter("weight_distance_max");
        break;
      case 'D':
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("weight_delta_max");
        if (sscanf(*argv, "%f", &weight_delta_max) != 1)
          DisplayInvalidParameter("weight_delta_max");
        break;
      case 'W':
        got_weight_sum_min = TRUE;
        ++argv; --argc;
        if (argc <= 0)          
          DisplayInvalidParameter("weight_sum_min");
        if (sscanf(*argv, "%f", &weight_sum_min) != 1)
          DisplayInvalidParameter("weight_sum_min");
        break;
      default:
        fprintf(stderr,"invalid option %c\n", *option);
        DisplayUsage();
      }
    }
  }
  if (!got_grid_data_type)
    for (i = 0; i < chan_count; i++)
      grid_chan_io_image[i].data_type_str = swath_chan_image[i].data_type_str;
  if (!got_grid_fill)
    for (i = 0; i < chan_count; i++) {
      grid_chan_io_image[i].fill = swath_chan_image[i].fill;
      grid_chan_image[i].fill = swath_chan_image[i].fill;
    }
  if (!got_weight_sum_min)
    weight_sum_min = weight_min;

  /*
   *        Get command line parameters.
   */
  if (very_verbose)
    fprintf(stderr, "fornav_c_rcsid: %s\n", fornav_c_rcsid);
  if (argc != 7 + 2 * chan_count)
    DisplayUsage();
  if (sscanf(*argv++, "%d", &swath_cols) != 1)
    DisplayInvalidParameter("swath_cols");
  if (sscanf(*argv++, "%d", &swath_scans) != 1)
    DisplayInvalidParameter("swath_scans");
  if (sscanf(*argv++, "%d", &swath_rows_per_scan) != 1)
    DisplayInvalidParameter("swath_rows_per_scan");
  swath_col_image->file = *argv++;
  swath_row_image->file = *argv++;
  for (i = 0; i < chan_count; i++)
    swath_chan_image[i].file = *argv++;
  if (sscanf(*argv++, "%d", &grid_cols) != 1)
    DisplayInvalidParameter("grid_cols");
  if (sscanf(*argv++, "%d", &grid_rows) != 1)
    DisplayInvalidParameter("grid_rows");
  for (i = 0; i < chan_count; i++)
    grid_chan_io_image[i].file = *argv++;

  if (verbose) {
    fprintf(stderr, "fornav:\n");
    fprintf(stderr, "  chan_count          = %d\n", chan_count);
    fprintf(stderr, "  swath_cols          = %d\n", swath_cols);
    fprintf(stderr, "  swath_scans         = %d\n", swath_scans);
    fprintf(stderr, "  swath_rows_per_scan = %d\n", swath_rows_per_scan);
    fprintf(stderr, "  swath_col_file      = %s\n", swath_col_image->file);
    fprintf(stderr, "  swath_row_file      = %s\n", swath_row_image->file);
    for (i = 0; i < chan_count; i++)
      fprintf(stderr, "  swath_chan_file[%d]  = %s\n", i,
              swath_chan_image[i].file);
    fprintf(stderr, "  grid_cols           = %d\n", grid_cols);
    fprintf(stderr, "  grid_rows           = %d\n", grid_rows);
    for (i = 0; i < chan_count; i++)
      fprintf(stderr, "  grid_chan_file[%d]   = %s\n", i,
              grid_chan_io_image[i].file);
    fprintf(stderr, "\n");
    fprintf(stderr, "  maximum_weight_mode = %d\n", maximum_weight_mode);
    fprintf(stderr, "  chan_scan_first     = %d\n", chan_scan_first);
    fprintf(stderr, "  colrow_scan_first   = %d\n", colrow_scan_first);
    fprintf(stderr, "  grid_col_start      = %d\n", grid_col_start);
    fprintf(stderr, "  grid_row_start      = %d\n", grid_row_start);
    for (i = 0; i < chan_count; i++)
      fprintf(stderr, "  swath_data_type[%d]  = %s\n", i,
              swath_chan_image[i].data_type_str);
    for (i = 0; i < chan_count; i++)
      fprintf(stderr, "  grid_data_type[%d]   = %s\n", i,
              grid_chan_io_image[i].data_type_str);
    for (i = 0; i < chan_count; i++)
      fprintf(stderr, "  swath_fill[%d]       = %f\n", i,
              swath_chan_image[i].fill);
    for (i = 0; i < chan_count; i++)
      fprintf(stderr, "  grid_fill[%d]        = %f\n", i,
              grid_chan_io_image[i].fill);
    fprintf(stderr, "\n");
    fprintf(stderr, "  col_row_fill        = %e\n", col_row_fill);
    fprintf(stderr, "  weight_count        = %d\n", weight_count);
    fprintf(stderr, "  weight_min          = %f\n", weight_min);
    fprintf(stderr, "  weight_distance_max = %f\n", weight_distance_max);
    fprintf(stderr, "  weight_delta_max    = %f\n", weight_delta_max);
    fprintf(stderr, "  weight_sum_min      = %f\n", weight_sum_min);
    fprintf(stderr, "\n");
  }

  /*
   *  Initialize images
   */
  if (swath_rows_per_scan < 2)
    error_exit("fornav: swath_rows_per_scan must be at least 2");
  InitializeImage(swath_col_image, "swath_col_image", "r", "f4",
                  swath_cols, swath_rows_per_scan, colrow_scan_first);

  InitializeImage(swath_row_image, "swath_row_image", "r", "f4",
                  swath_cols, swath_rows_per_scan, colrow_scan_first);
  for (i = 0; i < chan_count; i++) {
    char name[100];
    sprintf(name, "swath_chan_image %d", i); 
    InitializeImage(&swath_chan_image[i], name, "r",
                    swath_chan_image[i].data_type_str,
                    swath_cols, swath_rows_per_scan, chan_scan_first);
    sprintf(name, "grid_chan_io_image %d", i); 
    InitializeImage(&grid_chan_io_image[i], name, "w",
                    grid_chan_io_image[i].data_type_str,
                    grid_cols, 1, 0);
    sprintf(name, "grid_chan_image %d", i); 
    InitializeImage(&grid_chan_image[i], name, "", "f4",
                    grid_cols, grid_rows, 0);
    n = grid_cols * grid_rows;
    fptr =&(**((float **)grid_chan_image[i].buf));
    fill = grid_chan_io_image[i].fill;
    for (j = 0; j < n; j++)
      *fptr++ = fill;
  }

  InitializeImage(grid_weight_image, "grid_weight_image", "", "f4",
                  grid_cols, grid_rows, 0);

  /*
   *  Allocate an array of ewa parameters, one element per swath column
   */
  ewap = (ewa_parameters *)calloc(swath_cols, sizeof(ewa_parameters));
  if (ewap == NULL)
    error_exit("fornav: can't allocate ewa parameters\n");

  /*
   *  Initialize the ewa weight structure
   */
  InitializeWeight(chan_count, weight_count, weight_min, weight_distance_max,
                   weight_delta_max, weight_sum_min, col_row_fill, &ewaw);

  /*
   *  Process each scan
   */
  chan_scan_last = chan_scan_first + swath_scans - 1;
  first_scan_with_data = -1;
  for (scan = chan_scan_first; scan <= chan_scan_last; scan++) {
    if (very_verbose)
      fprintf(stderr, "Processing scan %d\n", scan);

    /*
     *  Read a scan from each col and row swath file
     */
    ReadImage(swath_col_image);
    ReadImage(swath_row_image);

    /*
     *  Compute ewa parameters for this scan
     */
    ComputeEwaParameters(swath_col_image, swath_row_image, &ewaw, ewap);

    /*
     *  Read a scan from each channel swath file
     */
    for (i = 0; i < chan_count; i++)
      ReadImage(&swath_chan_image[i]);

    /*
     *  Compute ewa for this scan
     */
    if (ComputeEwa(swath_col_image, swath_row_image, &ewaw, ewap,
                   chan_count, swath_chan_image, maximum_weight_mode,
                   grid_col_start, grid_row_start,
                   grid_chan_image, grid_weight_image)) {
      if (first_scan_with_data < 0)
        first_scan_with_data = scan;
      last_scan_with_data = scan;
    }

  } /* for (scan = chan_scan_first; scan <= chan_scan_last; scan++) */

  /*
   *  Write out gridded channel data for each channel
   */
  for (i = 0; i < chan_count; i++) {
    fill_count = WriteGridImage(&grid_chan_image[i], grid_weight_image,
                                maximum_weight_mode, weight_sum_min,
                                &grid_chan_io_image[i]);
    if (verbose)
      fprintf(stderr, "fill count[%d]: %d\n", i, fill_count);
  }

  /*
   *  De-Initialize images
   */
  DeInitializeImage(swath_col_image);
  DeInitializeImage(swath_row_image);
  for (i = 0; i < chan_count; i++) {
    DeInitializeImage(&swath_chan_image[i]);
    DeInitializeImage(&grid_chan_io_image[i]);
    DeInitializeImage(&grid_chan_image[i]);
  }
  DeInitializeImage(grid_weight_image);

  /*
   *  De-Initialize the weight structure
   */
  DeInitializeWeight(&ewaw);

  /*
   *  Free allocated memory
   */
  free(swath_col_image);
  free(swath_row_image);
  free(swath_chan_image);
  free(grid_chan_io_image);
  free(grid_chan_image);
  free(grid_weight_image);
  free(ewap);

  if (verbose) {
    int scans_with_data;

    scans_with_data = last_scan_with_data - first_scan_with_data + 1;
    if (chan_scan_first != first_scan_with_data ||
        swath_scans     != scans_with_data) {
      fprintf(stderr, "On next call to fornav, use:\n");
      fprintf(stderr, "  chan_scan_first:   %d\n", first_scan_with_data);
      fprintf(stderr, "  colrow_scan_first: %d\n",
              colrow_scan_first + first_scan_with_data - chan_scan_first);
      fprintf(stderr, "  swath_scans:       %d\n", scans_with_data);
    }
  }
  exit(EXIT_SUCCESS);
}
