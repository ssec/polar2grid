/*========================================================================
 * cdb.h - coastline database
 *
 * 8-Jul-1992 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1992 University of Colorado
 *========================================================================*/
#ifndef cdb_h_
#define cdb_h_

#ifdef cdb_c_
const char cdb_h_rcsid[] = "$Id: cdb.h 16072 2010-01-30 19:39:09Z brodzik $";
#endif

#include "define.h"

 
/*::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
 * cdb file structure
 *
 * Each coastline database (.cdb) file consists of a fixed length header,
 * followed by variable length segment data records and a record index.
 * Each index entry represents one continuous segment of coastline. No 
 * relationship between segments in separate entries can be inferred. The 
 * segment index entry contains information about the segment and a pointer 
 * to the segment data. The segment data is a block of 2 byte delta lat,lon 
 * values. Each data pair is an offset from the previous point, starting at 
 * lat0,lon0. All lat,lon values are signed 2^-10 degrees. Latitude is 
 * positive north [-90,90]. Longitude is positive east [-180,180].
 * All disk data is stored with most significant byte first (big-endian).
 * For machines which require least significant byte first (little-endian,
 * Intel, VAX) compile cdb.c with -DLSB1ST
 *::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::*/

/*
 *	symbolic constants
 */

#define CDB_MAGIC_NUMBER 0x2E636462
#define CDB_FILE_HEADER_SIZE 80L
#define CDB_LAT_SCALE (1./1024)
#define CDB_LON_SCALE (1./1024)
#define CDB_MAX_BUFFER_SIZE (25*1024*1024)

typedef enum
{ CDB_INDEX_NO_ORDER=0,
  CDB_INDEX_LAT_MAX,
  CDB_INDEX_LON_MAX,
  CDB_INDEX_LAT_MIN,
  CDB_INDEX_LON_MIN,
  CDB_INDEX_SEG_ID
} cdb_index_sort;

static char *cdb_index_sort_string[] = 
{ "undefined",
  "decreasing max latitude",
  "decreasing max longitude",
  "increasing min latitude",
  "increasing min longitude",
  "increasing segment ID"
};

/*
 *	file header
 */

typedef struct
{
  byte4 code_number;	/* identifies this file as a cdb file */
  byte4 index_addr;	/* byte offset of segment index */
  byte4 index_size;	/* size of segment index in bytes */
  byte4 max_seg_size;	/* maximum size in bytes of any segment */
  byte4 segment_rank;	/* rank of all segments in file (from WDB II) */
  byte4 index_order;	/* sort order of index in file */
  int4 ilat_max;	/* lat,lon bounds for entire file */
  int4 ilon_max;
  int4 ilat_min;
  int4 ilon_min;
  int4 ilat_extent;	/* maximum lat,lon extent of any segment */
  int4 ilon_extent;
  char text[32];	/* null terminated description of file */
} cdb_file_header;

/*
 *	segment index entry
 */

typedef struct
{
  byte4 ID;			/* segment identifier */
  int4  ilat0, ilon0;		/* segment origin */
  int4  ilat_max, ilon_max;	/* lat,lon bounds for segment */
  int4  ilat_min, ilon_min;
  byte4 addr;	/* byte offset of segment data */
  byte4 size;	/* size of segment data in bytes */
} cdb_index_entry;

/*
 *	segment data pair
 */

typedef struct
{
  int2  dlat;
  int2  dlon;
} cdb_seg_data;


/*
 * class definition
 */

typedef struct
{
  char *filename;
  FILE *fp;
  cdb_file_header *header;	/* segment file header */
  cdb_index_entry *index;	/* array of segment index entries */
  cdb_index_entry *segment;	/* current segment index entry */
  int seg_count;		/* total number of index entries */
  cdb_index_sort index_order;	/* sort order of index in memory */
  cdb_seg_data *data_buffer;	/* segment data buffer */
  long data_buffer_size;	/* size of data buffer */
  cdb_seg_data *data_ptr;	/* current segment data */
  int npoints;			/* number of data points in current segment */
  int is_loaded;		/* if TRUE all data is loaded in memory */
  cdb_seg_data *(*get_data)();	/* read segment data function */
} cdb_class;

/*
 *	macro definitions
 */

/*------------------------------------------------------------------------
 * current_seg_cdb - current segment pointer
 *
 *	cdb_index_entry *current_seg_cdb(cdb_class *this)
 *------------------------------------------------------------------------*/
#define current_seg_cdb(this) ((this)->segment)

/*------------------------------------------------------------------------
 * set_current_seg_cdb - set current segment pointer
 *
 *	cdb_index_entry *set_current_seg_cdb(cdb_class *this, cdb_index_entry *here)
 *------------------------------------------------------------------------*/
#define set_current_seg_cdb(this,here) ((this)->segment = (here))

/*------------------------------------------------------------------------
 * next_segment_cdb - increment current segment pointer
 *
 *	cdb_index_entry *next_segment_cdb(cdb_class *this)
 *------------------------------------------------------------------------*/
#define next_segment_cdb(this) ((this)->segment++)

/*------------------------------------------------------------------------
 * reset_current_seg_cdb - reset current segment pointer
 *
 *	cdb_index_entry *reset_current_seg_cdb(cdb_class *this)
 *------------------------------------------------------------------------*/
#define reset_current_seg_cdb(this) ((this)->segment = (this)->index)

/*------------------------------------------------------------------------
 * num_segments_cdb - total number of segment index entries
 *
 *	int num_segments_cdb(cdb_class *this)
 *------------------------------------------------------------------------*/
#define num_segments_cdb(this) ((this)->seg_count)

/*------------------------------------------------------------------------
 * last_segment_cdb - pointer to last segment
 *
 *	cdb_index_entry *last_segment_cdb(cdb_class *this)
 *------------------------------------------------------------------------*/
#define last_segment_cdb(this) ((this)->index + (this)->seg_count - 1)

/*------------------------------------------------------------------------
 * normalize_lon_cdb - normalize longitude to [-180.00,180.00]
 *
 *	void normalize_lon_cdb(double lon)
 *------------------------------------------------------------------------*/
#define normalize_lon_cdb(lon) \
  do \
  { while ((lon) < -180) lon += 360;\
    while ((lon) >  180) lon -= 360;\
  } while(0)


/*
 *	function prototypes
 */

cdb_class *new_cdb(void);
cdb_class *init_cdb(const char *cdb_filename); 
void free_cdb(cdb_class *this);
cdb_class *copy_of_cdb(cdb_class *this);
void load_all_seg_data_cdb(cdb_class *this);
cdb_seg_data *load_current_seg_data_cdb(cdb_class *this);
int get_current_seg_cdb(cdb_class *this,
			double *lat, double *lon, int max_pts);
int draw_current_seg_cdb(cdb_class *this, int (*move_pu)(double,double),
			 int (*draw_pd)(double,double));
void list_cdb(cdb_class *this, int verbose);
void sort_index_cdb(cdb_class *this, cdb_index_sort order);
cdb_index_entry *find_segment_cdb(cdb_class *this, double key_value);
int index_limit_test_cdb(cdb_class *this, double lower_bound,
			 double upper_bound);
int segment_bounds_test_cdb(cdb_class *this, double south, double north,
			    double west, double east);
int draw_cdb(cdb_class *this, double start, double stop, cdb_index_sort order,
	     int (*move_pu)(double,double), int (*draw_pd)(double,double));

#endif
