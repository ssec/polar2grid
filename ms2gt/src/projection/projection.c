/*========================================================================
 * projection - print projection standard name
 *
 * 04-Sep-2010 Terry Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char projection_c_rcsid[] = "$Header: /data/tharan/ms2gth/src/projection/projection.c,v 1.1 2010/09/03 18:14:28 tharan Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "mapx.h"

#define USAGE \
"usage: projection [-v] mppfile\n"\
"\n"\
" input : mppfile - map projection parameters file\n"\
"         or gpdfile - grid parameters defintion file\n"\
"\n"\
" output: The standard name of the projection defined by mppfile or gpdfile.\n"\
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

  mapx_class *mapx_def;

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
    fprintf(stderr, "projection:\n");
    fprintf(stderr, "  mppfile       = %s\n", mppfile);
    fprintf(stderr, "  projection_c_rcsid = %s\n", projection_c_rcsid);
  }
  
  /*
   *  initialize grid
   */
  mapx_def = init_mapx(mppfile);

  if (NULL == mapx_def) {

    /*
     *  if mapx has error, then print "UNDEFINED" and exit with failure
     */
    printf("UNDEFINED\n");
    exit(ABORT);
  } else {

    /*
     *  if mapx is ok, then print number of columns and rows
     */
    printf("%s\n", mapx_def->projection_name);

    /*
     *  close mapx
     */
    close_mapx(mapx_def);
  }
  exit(EXIT_SUCCESS);
}
