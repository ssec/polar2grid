/*======================================================================
 * grid_io - grid input/output
 * 
 * 3/18/98 K.Knowles knowles@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#ifndef grid_io_h_
#define grid_io_h_

#include "define.h"

static const char grid_io_h_RCSID[]="$Header: /usr/local/src/maps/grid_io.h,v 1.3 1999/08/31 20:29:17 knowles Exp $";

typedef enum 
{ grid_io_READ_ONLY, 
  grid_io_WRITE, 
  grid_io_UPDATE,
  grid_io_TEMPORARY,
  grid_io_NUM_MODES
} grid_io_mode;

typedef struct
{ int width, height;
  size_t datum_size;
  bool signed_data;
  bool real_data;
  grid_io_mode io_mode;
  FILE *fp;
  char *filename;
  byte1 **data;
  int row_buffer_increment;
  int start_row, final_row, num_rows;
} grid_io_class;

grid_io_class *init_grid_io(int width, int height, int datum_size, 
			    bool signed_data, bool real_data,
			    grid_io_mode mode, char *filename);

bool fill_grid_io(grid_io_class *this, double fill_value);

bool get_element_grid_io(grid_io_class *this, int row, int col, double *value);

bool put_element_grid_io(grid_io_class *this, int row, int col, double value);

void close_grid_io(grid_io_class *this);

#endif
