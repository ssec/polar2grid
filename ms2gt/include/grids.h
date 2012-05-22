/*======================================================================
 * grids.h - grid coordinate system parameters
 *
 * 26-Dec-1991 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1991 University of Colorado
 *======================================================================*/
#ifndef grids_h_
#define grids_h_

#ifdef grids_c_
const char grids_h_rcsid[] = "$Id: grids.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

#include "mapx.h"

/*
 * global verbose flag
 */
#ifdef grids_c_
#  define GLOBAL
#else
#  define GLOBAL extern
#endif

GLOBAL int grid_verbose;

#undef GLOBAL

/* 
 * useful macros
 */

/*
 * grid parameters structure
 */
typedef struct {
	double map_origin_col, map_origin_row;
	double cols_per_map_unit, rows_per_map_unit;
	int cols, rows;
	FILE *gpd_file;
	char *gpd_filename;
	mapx_class *mapx;
} grid_class;

/*
 * function prototypes
 */
grid_class *init_grid(char *filename);
grid_class *new_grid(char *label);
void close_grid(grid_class *this);
int forward_grid(grid_class *this,
		 double lat, double lon, double *r, double *s);
int inverse_grid(grid_class *this,
		 double r, double s, double *lat, double *lon);

#endif
