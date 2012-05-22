/*========================================================================
 * xy2ll - convert x-y pairs to latitude-longitude pairs
 *
 * 30-Mar-2011 Terry Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char xy2ll_c_rcsid[] = "$Header: /data/tharan/ms2gth/src/xy2ll/xy2ll.c,v 1.3 2011/03/30 20:02:07 tharan Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "mapx.h"
#include "grids.h"

#define USAGE \
"usage: xy2ll [-v] mppfile <xy.txt >xyll.txt\n"\
"\n"\
" input : mppfile - grid parameters definition file\n"\
"         xy.txt - (from stdin) ascii text containing x and y values\n"\
"\n"\
" output: xyll.txt - (to stdout) ascii text containing x, y, lat, lon, and\n"\
"                    status values\n"\
"\n"\
" options:v - verbose\n"\
 "\n"

static void DisplayUsage(void)
{
  error_exit(USAGE);
}

main (int argc, char *argv[])
{
  char *mppfile;
  char *option;
  bool verbose;
  char readln[FILENAME_MAX];

  double x;
  double y;
  double lat;
  double lon;
  int status;

  mapx_class *the_map;

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

  mppfile = *argv++;

  if (verbose) {
    fprintf(stderr, "  mppfile       = %s\n", mppfile);
    fprintf(stderr, "  xy2ll_c_rcsid = %s\n", xy2ll_c_rcsid);
  }
  
  /*
   *  initialize the map
   */

  the_map = init_mapx(mppfile);
  if (NULL == the_map)
    exit(ABORT);

  /*
   * keep reading lines until eof
   */
  for (;;) {
    gets(readln);
    if (!feof(stdin)) {
      
      /*
       * get x-y pair
       */
      sscanf(readln, "%lf %lf", &x, &y);
      
      /*
       *  convert x-y pair to latitude-longitude pair
       */
      status = inverse_xy_mapx(the_map, x, y, &lat, &lon);
      
      /*
       *  print x, y, lat, lon, and status
       */
      printf("%17.7lf %17.7lf %11.7lf %12.7lf %2d\n", x, y, lat, lon, status);
    } else {
      
      /*
       *  close the map
       */
      close_mapx(the_map);
      break;
    }
  }
    
  exit(EXIT_SUCCESS);
}
