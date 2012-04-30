/*----------------------------------------------------------------------
 * define.h - operating system dependent stuff
 *----------------------------------------------------------------------*/
#ifndef define_h_
#define define_h_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <math.h>

#ifndef DEBUG
#define NDEBUG
#endif
#include <assert.h>

#ifdef DEBUG_MALLOC
#include "dbmalloc.h"
#endif

#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE 1
#endif

#define NEVER FALSE

#ifndef PI
#define PI 3.141592653589793
#endif

#define radians(t) ( (t) * PI / 180.0)
#define degrees(t) ( (t) * 180.0 / PI)

#define nint(x) ((int)((x)+.5))

#define sign(x) ((x) < 0 ? -1 : 1)

#define streq(s1,s2) (strcmp(s1,s2) == 0)

#ifdef NEED_STRDUP
static char *t_sd_p;
#define strdup(string) \
  t_sd_p = (char *)malloc(strlen(string)+1); \
  if (t_sd_p) strcpy(t_sd_p, string); 
#endif

#define NUMBER(a) ((int)(sizeof(a)/sizeof(a[0])))

#define ABORT EXIT_FAILURE

#define error_exit(msg) {fprintf(stderr,"%s\n",msg); exit(ABORT);}

#define repeat do
#define until(condition) while(!(condition))

#define MAX_STRING 256

typedef int bool;

typedef unsigned char byte1;
typedef unsigned short int byte2;
typedef unsigned long int byte4;

typedef char int1;
typedef short int int2;
typedef long int int4;

#define BYTE1_BITS CHAR_BIT
#define BYTE1_MAX UCHAR_MAX
#define BYTE2_MAX USHRT_MAX
#define BYTE4_MAX ULONG_MAX

#define INT1_MAX SCHAR_MAX
#define INT2_MAX SHRT_MAX
#define INT4_MAX LONG_MAX

#define BYTE1_MIN 0
#define BYTE2_MIN 0
#define BYTE4_MIN 0

#define INT1_MIN SCHAR_MIN
#define INT2_MIN SHRT_MIN
#define INT4_MIN LONG_MIN

#endif
