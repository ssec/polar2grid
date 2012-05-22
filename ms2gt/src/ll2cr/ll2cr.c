/*========================================================================
 * ll2cr - convert latitude-longitude pairs to column-row pairs
 *
 * 23-Oct-2000 Terry Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char ll2cr_c_rcsid[] = "$Header: /data/tharan/ms2gth/src/ll2cr/ll2cr.c,v 1.14 2003/05/19 21:13:36 haran Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "mapx.h"
#include "grids.h"

#define USAGE \
"usage: ll2cr [-v] [-f] [-r rind] [-F fill_in fill_out]\n"\
"             colsin scansin rowsperscan latfile lonfile gpdfile tag\n"\
"\n"\
" input : colsin  - number of columns in each input file\n"\
"         scansin  - number of scans in each input file\n"\
"         rowsperscan - number of rows in each scan\n"\
"         latfile - grid of 4 byte floating-point latitudes\n"\
"         lonfile - grid of 4 byte floating-point longitudes\n"\
"         gpdfile - grid parameters definition file\n"\
"\n"\
" output: tag - string used to construct output filenames:\n"\
"           colfile = tag_cols_colsin_scansout_scanfirst_rowsperscan.img\n"\
"           rowfile = tag_rows_colsin_scansout_scanfirst_rowsperscan.img\n"\
"             where\n"\
"               scansout - number of scans written to each output file\n"\
"               scanfirst - scan number of first scan written\n"\
"           colfile - grid of 4 byte floating-point column numbers\n"\
"           rowfile - grid of 4 byte floating-point row numbers\n"\
"\n"\
" options:v - verbose\n"\
"         f - force scansout = scansin and scanfirst = 0. If -f is not set,\n"\
"             then scansout is set to the number of scans which contain at\n"\
"             least one point which is contained within the grid, and\n"\
"             scanfirst is set to the number of the first scan containing\n"\
"             such a point.\n"\
"         r rind - specifies the number of pixels by which the grid is to\n"\
"             be expanded in detecting whether points fall within the grid\n"\
"             for the purposes of determining scansout and scanfirst.\n"\
"             The default value of rind is 0. Note that if -f is specified,\n"\
"             then the -r option is ignored and rind is set to 0.\n"\
"         F fill_in fill_out - specifies the input and output fill values,\n"\
"             respectively. The default values are -999.0 and -1e30.\n"\
"\n"

static void DisplayUsage(void)
{
  error_exit(USAGE);
}

static void DisplayInvalidParameter(char *param)
{
  fprintf(stderr, "ll2cr: Parameter %s is invalid.\n", param);
  DisplayUsage();
}

main (int argc, char *argv[])
{
  int colsin;
  int scansin;
  int rowsperscan;
  char *latfile;
  char *lonfile;
  char *gpdfile;
  char *tag;
  char *option;
  bool verbose;
  bool force;
  int  rind;
  double fill_in;
  double fill_out;

  char colfile[FILENAME_MAX];
  char rowfile[FILENAME_MAX];
  FILE *fp_lat;
  FILE *fp_lon;
  FILE *fp_col;
  FILE *fp_row;
  float *lat_data;
  float *lon_data;
  float *col_data;
  float *row_data;
  float *latp;
  float *lonp;
  float *rowp;
  float *colp;
  double dlat;
  double dlon;
  double dcol;
  double drow;
  int bytes_per_row;
  int bytes_per_scan;
  int scansout;
  int scanfirst;
  int scanlast;
  int scan;
  int row;
  int col;
  int col_min;
  int col_max;
  int row_min;
  int row_max;
  grid_class *grid_def;

/*
 *	set defaults
 */
  verbose = FALSE;
  force = FALSE;
  rind = 0;
  fill_in = -999.0;
  fill_out = -1e30;

/* 
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-') {
    for (option = argv[0]+1; *option != '\0'; option++) {
      switch (*option) {
      case 'v':
	verbose = TRUE;
	break;
      case 'f':
	force = TRUE;
	break;
      case 'r':
	++argv; --argc;
	if (argc <= 0)
	  DisplayInvalidParameter("rind");
	if (sscanf(*argv, "%d", &rind) != 1)
	  DisplayInvalidParameter("rind");
	break;
      case 'F':
	++argv; --argc;
	if (argc <= 0)
	  DisplayInvalidParameter("fill_in");
	if (sscanf(*argv, "%lf", &fill_in) != 1)
	  DisplayInvalidParameter("fill_in");
	++argv; --argc;
	if (argc <= 0)
	  DisplayInvalidParameter("fill_out");
	if (sscanf(*argv, "%lf", &fill_out) != 1)
	  DisplayInvalidParameter("fill_out");
	break;
      default:
	fprintf(stderr,"invalid option %c\n", *option);
	DisplayUsage();
      }
    }
  }

/*
 *	get command line arguments
 */
  if (argc != 7)
    DisplayUsage();

  colsin = atoi(*argv++);
  scansin = atoi(*argv++);
  rowsperscan = atoi(*argv++);
  latfile = *argv++;
  lonfile = *argv++;
  gpdfile = *argv++;
  tag     = *argv++;

  if (force)
    rind = 0;

  if (verbose) {
    fprintf(stderr, "ll2cr:\n");
    fprintf(stderr, "  force         = %d\n", force);
    fprintf(stderr, "  rind          = %d\n", rind);
    fprintf(stderr, "  fill_in       = %lf\n", fill_in);
    fprintf(stderr, "  fill_out      = %le\n", fill_out);
    fprintf(stderr, "  colsin        = %d\n", colsin);
    fprintf(stderr, "  scansin       = %d\n", scansin);
    fprintf(stderr, "  rowsperscan   = %d\n", rowsperscan);
    fprintf(stderr, "  latfile       = %s\n", latfile);
    fprintf(stderr, "  lonfile       = %s\n", lonfile);
    fprintf(stderr, "  gpdfile       = %s\n", gpdfile);
    fprintf(stderr, "  tag           = %s\n", tag);
    fprintf(stderr, "  ll2cr_c_rcsid = %s\n", ll2cr_c_rcsid);
  }
  
  /*
   *  open input files
   */

  if ((fp_lat = fopen(latfile, "r")) == NULL) {
    fprintf(stderr, "ll2cr: error opening %s for reading\n", latfile);
    perror("ll2cr");
    exit(ABORT);
  }
  if ((fp_lon = fopen(lonfile, "r")) == NULL) {
    fprintf(stderr, "ll2cr: error opening %s for reading\n", lonfile);
    perror("ll2cr");
    exit(ABORT);
  }

  /*
   *  initialize grid
   */

  grid_def = init_grid(gpdfile);
  if (NULL == grid_def)
    exit(ABORT);
  col_min = -rind;
  col_max = grid_def->cols + rind - 1;
  row_min = -rind;
  row_max = grid_def->rows + rind - 1;

  /*
   *  Create preliminary names of output files as if force is TRUE.
   *  If force is TRUE, then these will be the final names.
   *  If force is FALSE, then we will rename the output files once
   *  we're done and we know the final values of scansout and scanfirst.
   */

  scansout = scansin;
  scanfirst = 0;
  sprintf(colfile, "%s_cols_%05d_%05d_%05d_%02d.img",
	  tag, colsin, scansout, scanfirst, rowsperscan);
  sprintf(rowfile, "%s_rows_%05d_%05d_%05d_%02d.img",
	  tag, colsin, scansout, scanfirst, rowsperscan);

  /*
   *  open output files
   */

  if ((fp_col = fopen(colfile, "w")) == NULL) {
    fprintf(stderr, "ll2cr: error opening %s for writing\n", colfile);
    perror("ll2cr");
    exit(ABORT);
  }
  if ((fp_row = fopen(rowfile, "w")) == NULL) {
    fprintf(stderr, "ll2cr: error opening %s for writing\n", rowfile);
    perror("ll2cr");
    exit(ABORT);
  }

/*
 *	allocate storage for data grids
 */
  bytes_per_row = colsin * sizeof(float);
  bytes_per_scan = bytes_per_row * rowsperscan;

  lat_data = (float *)malloc(bytes_per_scan);
  if (NULL == lat_data) {
    fprintf(stderr, "ll2cr: can't allocate memory for lat_data\n"); 
    perror("ll2cr");
    exit(ABORT);
  }
  lon_data = (float *)malloc(bytes_per_scan);
  if (NULL == lon_data) {
    fprintf(stderr, "ll2cr: can't allocate memory for lon_data\n"); 
    perror("ll2cr");
    exit(ABORT);
  }
  col_data = (float *)malloc(bytes_per_scan);
  if (NULL == col_data) {
    fprintf(stderr, "ll2cr: can't allocate memory for col_data\n"); 
    perror("ll2cr");
    exit(ABORT);
  }
  row_data = (float *)malloc(bytes_per_scan);
  if (NULL == row_data) {
    fprintf(stderr, "ll2cr: can't allocate memory for row_data\n"); 
    perror("ll2cr");
    exit(ABORT);
  }

  /*
   *  set scanfirst to -1 to indicate we haven't found a point within
   *  the grid yet.
   */
  scanfirst = -1;
  for (scan = 0; scan < scansin; scan++) {

    /*
     *  read a scan's worth of latitudes and longitudes
     */
    if (fread(lat_data, bytes_per_row, rowsperscan, fp_lat) !=
	rowsperscan) {
      fprintf(stderr, "ll2rc: premature end of file on %s\n", latfile);
      exit(ABORT);
    }
    if (fread(lon_data, bytes_per_row, rowsperscan, fp_lon) !=
	rowsperscan) {
      fprintf(stderr, "ll2rc: premature end of file on %s\n", lonfile);
      exit(ABORT);
    }

    /*
     *  set pointers to the beginning of each buffer
     */
    latp = lat_data;
    lonp = lon_data;
    colp = col_data;
    rowp = row_data;
    for (row = 0; row < rowsperscan; row++) {

      /*
       *  for each column of latitude-longitude pair
       */
      for (col = 0; col < colsin; col++, colp++, rowp++) {
      
	/*
	 *  convert latitude-longitude pair to column-row pair
	 */
	dlat = *latp++;
	dlon = *lonp++;
	*colp = fill_out;
	*rowp = fill_out;
	if (dlat != fill_in && dlon != fill_in) {
	  forward_grid(grid_def, dlat, dlon, &dcol, &drow);
	  *colp = dcol;
	  *rowp = drow;
	  if (force ||
	      (*colp >= col_min && *colp <= col_max &&
	       *rowp >= row_min && *rowp <= row_max)) {
	    if (!force) {
	      if (scanfirst < 0)
		scanfirst = scan;
	      scanlast = scan;
	    }
	  }
	}
      }
    }

    if (!force && (scanfirst >= 0) && (scanlast != scan))
      break;

    if (force || (scanfirst >= 0)) {
      /*
       *  write a scan's worth of column and row numbers
       */
      if (fwrite(col_data, bytes_per_row, rowsperscan, fp_col) !=
	  rowsperscan) {
	fprintf(stderr, "ll2rc: error writing to %s\n", colfile);
	exit(ABORT);
      }
      if (fwrite(row_data, bytes_per_row, rowsperscan, fp_row) !=
	  rowsperscan) {
	fprintf(stderr, "ll2rc: error writing to %s\n", rowfile);
	exit(ABORT);
      }
    }
  }


  /*
   *  close grid
   */
  close_grid(grid_def);

  /*
   *  close files
   */
  fclose(fp_lat);
  fclose(fp_lon);
  fclose(fp_col);
  fclose(fp_row);

  /*
   *  deallocate storage
   */
  free(lat_data);
  free(lon_data);
  free(col_data);
  free(row_data);

  /*
   *  rename the output files if force is FALSE
   */
  if (!force) {
    char colfile_new[FILENAME_MAX];
    char rowfile_new[FILENAME_MAX];

    if (scanfirst < 0) {
      scansout = 0;
      scanfirst = 0;
    } else {
      scansout = scanlast - scanfirst + 1;
    }
    sprintf(colfile_new, "%s_cols_%05d_%05d_%05d_%02d.img",
	    tag, colsin, scansout, scanfirst, rowsperscan);
    sprintf(rowfile_new, "%s_rows_%05d_%05d_%05d_%02d.img",
	    tag, colsin, scansout, scanfirst, rowsperscan);
    rename(colfile, colfile_new);
    rename(rowfile, rowfile_new);
  }
  exit(EXIT_SUCCESS);
}
