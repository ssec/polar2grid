/*========================================================================
 * mapenum - enumerate map feature vectors
 *
 * 4-Mar-1993 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
static const char mapenum_c_rcsid[] = "$Header: /usr/local/src/maps/mapenum.c,v 1.6 1994/11/02 17:43:42 knowles Exp $";

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "define.h"
#include "maps.h"
#include "grids.h"
#include "cdb.h"

#define usage "\n"\
  "usage: mapenum [-d cdb_file -s map_style -g grat_style] gpd_file\n"\
  "\n"\
  " input : gpd_file - grid parameters definition\n"\
  "\n"\
  " output: stdout - list of map feature vectors of the form:\n"\
  "                  style x1 y1 x2 y2\n"\
  "\n"\
  " option: d cdb_filename - specify coastline database\n"\
  "                          default is global.cdb\n"\
  "         s map_style - specify style (default 0)\n"\
  "         g grat_style - specify graticule style (default none)\n"

#define CDB_DEFAULT "global.cdb"
#define MAP_STYLE_DEFAULT 0
#define GRAT_STYLE_DEFAULT 1

static grid_class *grid;
static cdb_class *cdb;
static int pen_style = MAP_STYLE_DEFAULT;
static int move_pu(float,float);
static int draw_pd(float,float);

int main(int argc, char *argv[])
{ int map_style, grat_style, do_grat;
  char *option, *gpd_filename, *cdb_filename;

/*
 *	set defaults
 */
  map_style=MAP_STYLE_DEFAULT;
  grat_style=GRAT_STYLE_DEFAULT;
  do_grat = FALSE;
  cdb_filename = strdup(CDB_DEFAULT);

/*
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'd':
	  ++argv; --argc;
	  cdb_filename = strdup(*argv);
	  break;
	case 's':
	  ++argv; --argc;
	  if (sscanf(*argv, "%d", &map_style) != 1)
	  { map_style = MAP_STYLE_DEFAULT;
	    --argv; ++argc;
	  }
	  break;
	case 'g':
	  do_grat = TRUE;
	  ++argv; --argc;
	  if (sscanf(*argv, "%d", &grat_style) != 1)
	  { grat_style = GRAT_STYLE_DEFAULT;
	    --argv; ++argc;
	  }
	  break;
	default:
	  fprintf(stderr, "invalid option %c\n", *option);
	  error_exit(usage);
      }
    }
  }

/*
 *	process command line arguments
 */
  if (argc < 1) error_exit(usage);
  gpd_filename = strdup(*argv);
  if (gpd_filename == NULL) error_exit(usage);

  grid = init_grid(gpd_filename);
  if (grid == NULL) error_exit("mapenum: error initializing grid");

  cdb = init_cdb(cdb_filename);
  if (cdb == NULL) error_exit("mapenum: error openning coastline database");

  pen_style = map_style;
  draw_cdb(cdb, grid->mapx->west, grid->mapx->east, 
	   CDB_INDEX_LON_MIN, move_pu, draw_pd);

  if (do_grat)
  { pen_style = grat_style;
    draw_graticule(grid->mapx, move_pu, draw_pd, NULL);
  }
}

static float pen_x1, pen_y1, pen_x2, pen_y2;

/*------------------------------------------------------------------------
 * move_pu
 *
 *	input : lat, lon
 *
 *------------------------------------------------------------------------*/
static int move_pu(float lat, float lon)
{
  (void) forward_grid(grid, lat, lon, &pen_x1, &pen_y1);
  return 0;
}

/*------------------------------------------------------------------------
 * draw_pd
 *
 *	input : lat, lon
 *
 *------------------------------------------------------------------------*/
static int draw_pd(float lat, float lon)
{ int on_grid;

  on_grid = forward_grid(grid, lat, lon, &pen_x2, &pen_y2);
  if (on_grid && within_mapx(grid->mapx, lat, lon))
  { printf("%d %f %f %f %f\n", pen_style, pen_x1, pen_y1, pen_x2, pen_y2);
  }
  pen_x1 = pen_x2;
  pen_y1 = pen_y2;

  return 0;
}
