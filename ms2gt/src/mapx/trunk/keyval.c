/*======================================================================
 * keyval - "keyword: value" decoder
 *
 * 23-Oct-1996 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1996 University of Colorado
 *======================================================================*/
static const char keyval_c_rcsid[] = "$Id: keyval.c 16072 2010-01-30 19:39:09Z brodzik $";

#include <ctype.h>
#include "define.h"
#define keyval_c_
#include "keyval.h"
#include "mapx.h"

static const char *keyval_LATITUDE = "NSns";
static const char *keyval_LONGITUDE = "EWew";

const char *id_keyval(void)
{
  return keyval_c_rcsid;
}

/*------------------------------------------------------------------------
 * get_label_keyval - read label from file
 *
 *	input : filename - file name or NULL
 *		fp - FILE pointer or NULL
 *		  if fp is non-NULL then it should point to an open file
 *		  otherwise filename is used to open the file
 *		label_length - length of label in bytes or 0
 *		  if 0 then read entire file
 *
 *	result: pointer to label buffer or NULL on error
 *		space for buffer is obtained with malloc
 *
 * A "label" consists of a list of "keyword: value" pairs. The keyword
 * field is terminated by a colon and separated from the value field
 * by blanks or tabs. The value field is terminated by a semi-colon,
 * pound sign or newline. Each "keyword: value" pair describes a single
 * parameter.
 * For each line, any characters following a semi-colon or pound sign
 * are replaced with blanks.
 *
 *------------------------------------------------------------------------*/
char *get_label_keyval(const char *filename, FILE *fp, int label_length)
{ char *label;
 int i;
 int got_comment;

  assert(fp != NULL || filename != NULL);

/*
 *	open file if not already open
 */
  if (NULL == fp)
  { fp = fopen(filename, "r");
    if (NULL == fp) { perror(filename); return NULL; }
  }

/*
 *	get length of label string and allocate buffer
 */
  if (0 == label_length)
  { long offset;
    offset = ftell(fp);
    fseek(fp, 0L, SEEK_END);
    label_length = ftell(fp);
    fseek(fp, offset, SEEK_SET);
  }

  label = (char *)malloc(label_length+1);
  if (NULL == label) { perror("get_label_keyval"); return NULL; }

/*
 *	read label string into new buffer
 */
  fread(label, 1, label_length, fp);
  if (ferror(fp)) 
  { free(label); 
    perror(filename ? filename : "get_label_keyval"); 
    return NULL; 
  }

  label[label_length] = '\0';

  /*
   *  For each line, replace any characters following a semi-colon
   *  or a pound sign with blanks.
   */
  got_comment = 0;
  for (i = 0; i < label_length; i++) {
    if ('\n' == label[i])
      got_comment = 0;
    else if (';' == label[i] || '#' == label[i])
      got_comment = 1;
    else if (got_comment)
      label[i] = ' ';
  }

  return label;
}

/*------------------------------------------------------------------------
 * get_field_keyval - return field from label
 *
 *	input : label - pointer to label buffer
 *		keyword - name of label field
 *		default_string - pointer to default string or NULL
 *			  if keyword is not found then default is returned
 *
 *	result: pointer to NULL terminated field value buffer
 *		or NULL if field not found, space for buffer
 *		is obtained with malloc
 *
 *      NOTE: keyword is converted to uppercase before the search is
 *            performed.
 *
 *------------------------------------------------------------------------*/
char *get_field_keyval(const char *label, const char *keyword, 
		       const char *default_string)
{
  register char *field_ptr, *field_start;
  int i;
  char *keyword_upper;
  char *label_upper;
  int keyword_length;
  int label_length;
  int field_length;
  int got_valid_keyword = 0;

  /*
   *  Convert keyword to uppercase
   */

  keyword_upper = strdup(keyword);
  if (NULL == keyword_upper) { perror("get_field_keyval"); return NULL; }
  keyword_length = strlen(keyword);
  for (i = 0; i < keyword_length; i++)
    keyword_upper[i] = toupper(keyword_upper[i]);

  /*
   *  Convert label to uppercase for searching for keyword
   */

  label_upper = strdup(label);
  if (NULL == label_upper) { perror("get_field_keyval"); return NULL; }
  label_length = strlen(label);
  for (i = 0; i < label_length; i++)
    label_upper[i] = toupper(label_upper[i]);
  field_start = label_upper;

  /*
   *	find keyword
   */
  
  while (!got_valid_keyword)
    {

    field_start = strstr(field_start, keyword_upper);

    if (NULL == field_start)
      { 
	free(keyword_upper);
	free(label_upper);
	if (NULL == default_string)
	  { fprintf(stderr,"get_field_keyval: <%s> not found\n", keyword);
	  return NULL;
	  }
	else
	  { return strdup(default_string);
	  }
      } else {

	/*
	 *  Make sure that the keyword is immediately followed by a colon
	 */

	field_start += keyword_length;
	if (field_start - label_upper + 2 < label_length) {
	  if (*field_start++ == ':') {

	    /*
	     *  Reset the field pointer to the same position in the
	     *  original label. This will allow lower case in
	     *  the field values (e.g. an mpp filename).
	     */
	    
	    field_start = (char *)label + (field_start - label_upper);
	    got_valid_keyword = 1;
	  }
	}
      }
    }

/*
 *	skip to start of value field
 */

  free(keyword_upper);
  free(label_upper);
  field_start += strspn(field_start, " \t\n");

/*
 *	get length of field and allocate new buffer
 */
  field_length = strcspn(field_start, ";#\n");
  if (0 == field_length) field_length = strlen(field_start);

  field_ptr = (char *)malloc(field_length+1);
  if (NULL == field_ptr) { perror("get_field_keyval"); return NULL; }

/*
 *	copy value field to new buffer
 */
  strncpy(field_ptr, field_start, field_length);
  field_ptr[field_length] = '\0';

  return field_ptr;
}

/*------------------------------------------------------------------------
 * get_value_keyval - retrieve value from label
 *
 *	input : label - pointer to label buffer
 *		keyword - name of label field
 *		format - either "%lat" for latitude
 *			 "%lon" for longitude
 *			 "%bool" for boolean value (see below)
 *			 or regular scanf format string
 *		default_string - pointer to default string or NULL.
 *			  If keyword is not found then default is returned.
 *                        Use "KEYVAL_UNINITIALIZED" to return
 *                        KEYVAL_UNINITIALIZED for %f or %lf.
 *
 *	output: value from header label field (or converted default value)
 *
 *	result: TRUE = success, FALSE = error
 *
 *------------------------------------------------------------------------*/
bool get_value_keyval(const char *label, const char *keyword, 
		      const char *format, void *value, 
		      const char *default_string)
{ int status;
  char *field_ptr;

/*
 *	get value field
 */
  field_ptr = get_field_keyval(label, keyword, default_string);
  if (NULL == field_ptr) { return FALSE; }

/*
 *	decode field based on format
 */
  if (streq("%lat", format))
  { status = lat_lon_keyval(field_ptr, keyval_LATITUDE, value);
    if (!status) status = sscanf(field_ptr, "%lf", (double *)value);
  }
  else if (streq("%lon", format))
  { status = lat_lon_keyval(field_ptr, keyval_LONGITUDE, value);
    if (!status) status = sscanf(field_ptr, "%lf", (double *)value);
  }
  else if (streq("%bool", format))
  { status = boolean_keyval(field_ptr, value);
  }
  else if (streq("%f", format)) {
    if (streq("KEYVAL_UNINITIALIZED", field_ptr)) {
      *(float *)value = (float)KEYVAL_UNINITIALIZED;
      status = 1;
    } else {
      status = sscanf(field_ptr, format, value);
    }
  }
  else if (streq("%lf", format)) {
    if (streq("KEYVAL_UNINITIALIZED", field_ptr)) {
      *(double *)value = KEYVAL_UNINITIALIZED;
      status = 1;
    } else {
      status = sscanf(field_ptr, format, value);
    }
  }
  else
  { status = sscanf(field_ptr, format, value);
  }

  free(field_ptr);

  if (1 != status) 
  { fprintf(stderr,"get_value_keyval: can't retrieve value <%s>\n", keyword);
    return FALSE;
  }

  return TRUE;
}

/*------------------------------------------------------------------------
 * boolean_keyval - interpret boolean indicator
 *
 *	input : field_ptr - pointer to NULL terminated string
 *
 *	output: value - bool TRUE or FALSE
 *
 *	result: number of values transferred (0 on failure, 1 on success)
 *
 *	TRUE values include: TRUE, YES, Y, ON 
 *	FALSE values include: FALSE, NO, N, OFF 
 *	not case sensitive
 *
 *------------------------------------------------------------------------*/
int boolean_keyval(const char *field_ptr, bool *value)
{ register char *test, *cur;

/*
 *	get a copy of the input and convert to all upper case  
 */
  test = strdup(field_ptr);
  if (NULL == test) { perror("boolean_keyval"); return FALSE; }

  for (cur = test; *cur != '\0'; cur++) *cur = (char)toupper((int)*cur);

/*
 *	look for TRUE values
 */
  if (streq(test, "Y") ||
      streq(test, "ON") ||
      streq(test, "YES") ||
      streq(test, "TRUE"))
  { *value = TRUE;
    free(test);
    return 1;
  }

/*
 *	look for FALSE values
 */
  if (streq(test, "N") ||
      streq(test, "NO") ||
      streq(test, "OFF") ||
      streq(test, "FALSE"))
  { *value = FALSE;
    free(test);
    return 1;
  }

/*
 *	no match
 */
  return 0;
}

/*------------------------------------------------------------------------
 * lat_lon_keyval - decode lat or lon (decimal degrees) from buffer
 *
 *	input : field_ptr - pointer to buffer
 *		designators - string of possible hemisphere designators
 *			"EWew" to extract a longitude
 *			"NSns" to extract a latitude
 *
 *	output: value - latitude or longitude in decimal degrees
 *
 *	result: number of values transferred (0 on failure, 1 on success)
 *
 *	format: dd.dd[optional white space]designator
 *
 *------------------------------------------------------------------------*/
int lat_lon_keyval(const char *field_ptr, const char *designators, 
		   double *value)
{ const char *end, *pos;
  char hemi, number[MAX_STRING];
  int len;

/*
 *	find designator in field and get hemisphere
 */
  end = field_ptr + strlen(field_ptr);

  pos = strpbrk(field_ptr, designators);
  if (NULL == pos || pos > end) return 0;

  hemi = toupper(*pos);

/*
 *	work backwards to start of numeric value
 */
  while (pos > field_ptr && isspace(*--pos));

  while (pos > field_ptr && NULL != strchr("0123456789.+-", *--pos));

  if (NULL == strchr("0123456789.+-", *pos)) ++pos;

/*
 *	extract numerical value
 */
  len = strspn(pos, "0123456789.+-");
  if (len <= 0 || len >= MAX_STRING) return 0;
  strncpy(number, pos, len);
  number[len] = '\0';

  if (sscanf(number, "%lf", value) != 1) return 0;

/*
 *	change sign for "negative" hemispheres
 */
  if ('W' == hemi || 'S' == hemi) *value = -(*value);

  return 1;
}
