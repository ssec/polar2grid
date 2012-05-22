/*======================================================================
 * matrix_io.h - header file for matrix_io.c:
 *   programs to read and write matrix data
 * 
 * 03-Jul-1997 brodzik brodzik@kryos.colorado.edu 303-492-8263
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1997 University of Colorado
 *======================================================================*/
#ifndef matrix_io_h_
#define matrix_io_h_

#ifdef matrix_io_c_
const char matrix_io_h_rcsid[]="$Id: matrix_io.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

#include "define.h"
#include "grids.h"

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
