/*========================================================================
 * gridsize - print number of columns and number of rows for a grid
 *
 * 6-Mar-2001 Terry Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char gridsize_c_rcsid[] = "$Header: /export/data/ms2gth/src/gridsize/gridsize.c,v 1.2 2001/05/24 23:29:38 haran Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "mapx.h"
#include "grids.h"

#define USAGE \
"usage: gridsize [-v] gpdfile\n"\
"\n"\
" input : gpdfile - grid parameters definition file\n"\
"\n"\
" output: the number of columns and number of rows in the grid is written\n"\
"         to stdout. In the event of an error, both values are set to 0.\n"\
"\n"\
" options:v - verbose\n"\
"\n"

static void DisplayUsage(void)
{
  error_exit(USAGE);
}

main (int argc, char *argv[])
{
  char *gpdfile;
  char *option;
  bool verbose;

  grid_class *grid_def;

/*
 *	set defaults
 */
  verbose = FALSE;

/* 
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-') {
    for (option = argv[0]+1; *option != '\0'; option++) {
      switch (*option) {
      case 'v':
	verbose = TRUE;
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
  if (argc != 1)
    DisplayUsage();

  gpdfile = *argv++;

  if (verbose) {
    fprintf(stderr, "gridsize:\n");
    fprintf(stderr, "  gpdfile       = %s\n", gpdfile);
    fprintf(stderr, "  gridsize_c_rcsid = %s\n", gridsize_c_rcsid);
  }
  
  /*
   *  initialize grid
   */
  grid_def = init_grid(gpdfile);

  if (NULL == grid_def) {

    /*
     *  if grid has error, then print zeroes and exit with failure
     */
    printf("cols: 0\n");
    printf("rows: 0\n");
    exit(ABORT);
  } else {

    /*
     *  if grid is ok, then print number of columns and rows
     */
    printf("cols: %d\n", grid_def->cols);
    printf("rows: %d\n", grid_def->rows);

    /*
     *  close grid
     */
    close_grid(grid_def);
  }
  exit(EXIT_SUCCESS);
}
