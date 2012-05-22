/*========================================================================
 * grid_convert - grid transform server for IDL interface
 *
 *	to convert lat,lon to grid coordinates - 
 *	send stdin: FORWARD lat lon
 *	receive stdout: SUCCESS col row
 *
 *	to convert grid coordinates to lat,lon -
 *	send stdin: INVERSE col row
 *	receive stdout: SUCCESS lat lon
 *
 *      to retrieve km per pixel horizontally, vertically -
 *      send stdin: RESOLUT 0 0
 *      receive stdout: SUCCESS km_per_pixel_horizontal, km_per_pixel_vertical
 *
 *	to terminate either close pipe or send EOF
 *
 * 29-Jan-1993 K.Knowles knowles@kryos.colorado.edu 303-492-0644
 *========================================================================*/
static const char grid_convert_c_rcsid[] = "$Header: /data/tharan/ms2gth/src/grid_convert/grid_convert.c,v 1.2 2008/09/23 16:16:04 tharan Exp $";

#include <stdio.h>
#include <string.h>
#include <define.h>
#include <mapx.h>
#include <grids.h>

#define usage "usage: grid_convert gpdfile"

static const char msg_format[] = "%7s%16.8le%16.8le\n";
static const char success[] = "SUCCESS";
static const char failure[] = "FAILURE";

int main(int argc, char *argv[])
{ register int ios;
  double f1, f2, f3, f4;
  grid_class *grid;
  char readln[80], action[80];

  /*
   * disable output buffering
  (void) setbuf(stdout, (char *)0);
   */

  /*
   * Rather than disabling output buffering, let's
   * try line buffering instead in an attempt to solve an intermittent
   * i/o error problem when reading pipe input from this program after
   * it has been spawned from an idl program.
   */
  setlinebuf(stdout);

  if (argc < 2)
  { printf("%s\nFAILURE\n",  grid_convert_c_rcsid);
    error_exit(usage);
  }

  grid = init_grid(argv[1]); 
  if (grid == NULL) { printf("FAILURE\n"); error_exit(usage); }

  printf("SUCCESS\n");

  repeat
  {
    gets(readln);
    if (feof(stdin)) break;

    ios = sscanf(readln,"%s %lf %lf", action, &f1, &f2);
    if (ios != 3) { printf("%s %lf %lf\n", "FAILURE", f1, f2); continue; }

    if (streq(action,"FORWARD"))
    { ios = forward_grid(grid, f1, f2, &f3, &f4);
    }
    else if (streq(action,"INVERSE"))
    { ios = inverse_grid(grid, f1, f2, &f3, &f4);
    }
    else if (streq(action,"RESOLUT")) {
      f3 = grid->mapx->scale / grid->cols_per_map_unit;
      f4 = grid->mapx->scale / grid->rows_per_map_unit;
      ios = TRUE;
    }
    else {
      f3 = 0.0;
      f4 = 0.0;
      ios = FALSE;
    }

    printf(msg_format, ios ? success : failure, f3, f4);

#ifdef DEBUG
    fprintf(stderr,"%s %lf %lf %lf %lf %s\n",
	    action, f1, f2, f3, f4, ios ? "SUCCESS" : "FAILURE");
#endif

  } until(feof(stdin));

  exit(EXIT_SUCCESS);
}
