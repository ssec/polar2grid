/*========================================================================
 * gridloc - create grids of lat, lon locations
 *
 * 20-Sep-1995 K.Knowles knowles@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char gridloc_c_rcsid[] = "$Header: /usr/local/src/maps/gridloc.c,v 1.4 2000/12/12 20:58:44 knowles Exp $";

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "mapx.h"
#include "grids.h"
#include "byteswap.h"

#define usage \
"usage: gridloc [-pmq -o output_name] file.gpd\n"\
"\n"\
" input : file.gpd  - grid parameters definition file\n"\
"\n"\
" output: grid of signed decimal latitudes and/or longitudes\n"\
"         4 byte floats by row\n"\
"\n"\
" option: o - write data to file output_name.WIDTHxHEIGHTxNBANDS.float\n"\
"             otherwise output goes to stdout\n"\
"         p - do latitudes only\n"\
"         m - do longitudes only\n"\
"         pm - do latitudes followed by longitudes\n"\
"         mp - do longitudes followed by latitudes (default)\n"\
"         q - quiet\n"\
"\n"

#define UNDEFINED -999

main (int argc, char *argv[])
{
  register int i, j, k;
  int band[2], nbands;
  int nbytes, row_bytes, status, total_bytes;
  bool verbose;
  float coord[2];
  float *value, *undefined;
  char *option, *output_name, output_filename[MAX_STRING];
  static char *coord_name[2] = {"latitude", "longitude"};
  FILE *output_file;
  grid_class *grid_def;

/*
 *	set defaults
 */
  nbands = 0;
  verbose = TRUE;
  output_name = NULL;

/* 
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'q':
	  verbose = FALSE;
	  break;
	case 'm':
	  if (nbands < 2)
	  { band[nbands] = 1;
	    nbands++;
	  }
	  break;
	case 'p':
	  if (nbands < 2)
	  { band[nbands] = 0;
	    nbands++;
	  }
	  break;
	case 'o':
	  ++argv; --argc;
	  if (argc <= 0) error_exit(usage);
	  output_name = strdup(*argv);
	  break;
	default:
	  fprintf(stderr,"invalid option %c\n", *option);
	  error_exit(usage);
      }
    }
  }

  if (0 == nbands)
  { band[0] = 1;
    band[1] = 0;
    nbands = 2;
  }

/*
 *	get command line arguments
 */
  if (argc != 1) error_exit(usage);
  
  grid_def = init_grid(*argv);
  if (NULL == grid_def) exit(ABORT);
  if (verbose) fprintf(stderr,"> using %s...\n", grid_def->gpd_filename);

  if (NULL != output_name)
  { sprintf(output_filename, "%s.%dx%dx%d.float", 
	    output_name, grid_def->cols, grid_def->rows, nbands);
    output_file = fopen(output_filename, "w");
    if (NULL == output_file) { perror(output_filename); error_exit(usage); }
  }
  else
  { strcpy(output_filename, "stdout");
    output_file = stdout;
  }

/*
 *	allocate storage for data grids
 */
  value = (float *)calloc(grid_def->cols, sizeof(float));
  if (NULL == value) { perror("value"); exit(ABORT); }
  row_bytes = grid_def->cols * sizeof(float);
  total_bytes = 0;

  undefined = (float *)calloc(grid_def->cols, sizeof(float));
  if (NULL == undefined) { perror("undefined"); exit(ABORT); }
  for (j = 0; j < grid_def->cols; j++) undefined[j] = UNDEFINED;

/*
 *	write data 
 */
  for (k = 0; k < nbands; k++)
  { if (verbose) fprintf(stderr,"> writing %s...\n", coord_name[band[k]]);
    for (i = 0; i < grid_def->rows; i++) 
    { memcpy(value, undefined, row_bytes);
      for (j = 0; j < grid_def->cols; j++)
      { status = inverse_grid(grid_def, (float)j, (float)i, 
			      &(coord[0]), &(coord[1]));
	if (!status) continue;
	value[j] = coord[band[k]];
      }
      nbytes = fwrite(value, 1, row_bytes, output_file);
      if (nbytes != row_bytes) { perror (output_filename); exit(ABORT); }
      total_bytes += nbytes;
    }
  }
  if (verbose) fprintf(stderr,"> wrote %d bytes to %s\n", 
		       total_bytes, output_filename);

}
