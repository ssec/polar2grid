/*======================================================================
 * keyval - "keyword: value" decoder
 *
 * 23-Oct-1996 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1996 University of Colorado
 *======================================================================*/
#ifndef keyval_h_
#define keyval_h_

#ifdef keyval_c_
const char keyval_h_rcsid[] = "$Id: keyval.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

#include "define.h"

/*
 * define symbol to use for marking uninitialized keyword values
 */
#ifdef FLT_MAX
#define KEYVAL_UNINITIALIZED ((double)FLT_MAX)
#else
#define KEYVAL_UNINITIALIZED ((double)9e30)
#endif

static const char *keyval_FALL_THRU_STRING = "-+-keyval_FALL_THRU_STRING-+-";

char *get_label_keyval(const char *filename, FILE *fp, int label_length);

char *get_field_keyval(const char *label, const char *keyword, 
		       const char *default_string);

bool get_value_keyval(const char *label, const char *keyword, 
		      const char *format, void *value, 
		      const char *default_string);

int boolean_keyval(const char *field_ptr, bool *value);

int lat_lon_keyval(const char *field_ptr, const char *designators, 
		   double *value);

#endif
