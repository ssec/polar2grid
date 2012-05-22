/*========================================================================
 * ll2xy - convert latitude-longitude pairs to x-y pairs
 *
 * 30-Mar-2011 Terry Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char ll2xy_c_rcsid[] = "$Header: /data/tharan/ms2gth/src/ll2xy/ll2xy.c,v 1.1 2011/03/30 20:55:31 tharan Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "mapx.h"
#include "grids.h"

#define USAGE \
"usage: ll2xy [-v] mppfile <ll.txt >llxy.txt\n"\
"\n"\
" input : mppfile - grid parameters definition file\n"\
"         ll.txt - (from stdin) ascii text containing lat and lon values\n"\
"\n"\
" output: llxy.txt - (to stdout) ascii text containing lat, lon, x, y, and\n"\
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
    fprintf(stderr, "  ll2xy_c_rcsid = %s\n", ll2xy_c_rcsid);
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
      sscanf(readln, "%lf %lf", &lat, &lon);
      
      /*
       *  convert x-y pair to latitude-longitude pair
       */
      status = forward_xy_mapx(the_map, lat, lon, &x, &y);
      
      /*
       *  print lat, lon, x, y, and status
       */
      printf("%11.7lf %12.7lf %17.7lf %17.7lf %2d\n", lat, lon, x, y, status);
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
