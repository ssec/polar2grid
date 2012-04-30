/*======================================================================
 * matrix_io.h - header file for matrix_io.c:
 *   programs to read and write matrix data
 * 
 * 03/7/1997 brodzik brodzik@zamboni.colorado.edu 303-492-8263
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
#ifndef matrix_io_h_
#define matrix_io_h_

#include "define.h"
#include "grids.h"

static const char matrix_io_h_RCSID[]="$Header: /usr/local/src/maps/matrix_io.h,v 1.6 1997/10/03 20:47:25 root Exp $";

size_t read_matrix (void **data, const char *file_name, 
		    int rows, int cols, size_t size);
size_t write_matrix (const char *file_name, void **data, 
		     int rows, int cols, size_t size);

/* Allocate memory for and read matrix object from external file */
void **initialize_matrix (grid_class *grid, 
			  size_t size, 
			  const char *file_name,
			  const char *object_name, 
			  bool verbose);

#endif
