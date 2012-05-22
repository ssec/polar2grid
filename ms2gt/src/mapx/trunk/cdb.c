/*===========================================================================
 * cdb - coastline database interface
 *
 * See cdb.h for a complete description of the cdb file structure.
 *
 * 8-Jul-1992 K.Knowles knowlesk@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 * Copyright (C) 1992 University of Colorado
 *===========================================================================*/
static const char cdb_c_rcsid[] = "$Id: cdb.c 16072 2010-01-30 19:39:09Z brodzik $";
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "define.h"
#include "maps.h"
#define cdb_c_
#include "cdb.h"
#include "cdb_byteswap.h"

static cdb_seg_data *cdb_read_disk(cdb_class *this);
static cdb_seg_data *cdb_read_memory(cdb_class *this);

const char *id_cdb(void)
{
  return cdb_c_rcsid;
}

/*----------------------------------------------------------------------
 * new_cdb - create new cdb_class instance
 *
 *	result: pointer to new cdb or NULL
 *
 *--------------------------------------------------------------------*/
cdb_class *new_cdb(void)
{
  cdb_class *this = (cdb_class *) calloc(1, sizeof(cdb_class));
  if (this == NULL) { perror("new_cdb"); return NULL; }
  this->filename = NULL;
  this->fp = NULL;
  this->header = NULL;
  this->index = NULL;
  this->segment = NULL;
  this->seg_count = 0;
  this->index_order = CDB_INDEX_NO_ORDER;
  this->data_buffer = NULL;
  this->data_buffer_size = 0;
  this->data_ptr = NULL;
  this->npoints = 0;
  this->is_loaded = FALSE;
  this->get_data = cdb_read_disk;

  return this;
}

/*----------------------------------------------------------------------
 * init_cdb - open cdb file, read in file header and segment index
 *              allocate space for segment data buffer
 *
 *      input : cdb_filename - name of cdb file
 *
 *      result: pointer to new cdb or NULL
 *
 *	note  : if init_cdb fails to open cdb_file on its
 *		first attempt it will then search the colon
 *		separated list of paths in the environment
 *		variable PATHCDB
 *
 *--------------------------------------------------------------------*/
cdb_class *init_cdb(const char *cdb_filename)
{
  register int ios;
  cdb_class *this;

/*
 *	create new cdb_class instance
 */
  this = new_cdb();
  if (NULL == this) { return (cdb_class *)NULL; }

/*
 *	open cdb file
 */
  this->filename = (char *)realloc(this->filename, (size_t)MAX_STRING);
  if (NULL == this->filename)
  { perror("init_cdb"); free_cdb(this); return (cdb_class *)NULL; }
  strncpy(this->filename, cdb_filename, MAX_STRING);
  this->fp = search_path_fopen(this->filename, "PATHCDB", "r");
  if (NULL == this->fp)
  { fprintf(stderr,"init_cdb: error openning data file.\n");
    perror(cdb_filename);
    free_cdb(this);
    return (cdb_class *)NULL;
  }

/*
 *	read in cdb file header, byteswap it, and check magic number
 */
  this->header = (cdb_file_header *)calloc(1, sizeof(cdb_file_header));
  if (NULL == this->header) 
  { perror("init_cdb"); free_cdb(this); return (cdb_class *)NULL; }

  if (fread(this->header, 1, CDB_FILE_HEADER_SIZE, this->fp)
      != CDB_FILE_HEADER_SIZE)
  { perror(cdb_filename); free_cdb(this); return (cdb_class *)NULL; }

  cdb_byteswap_header(this->header);

  if (this->header->code_number != CDB_MAGIC_NUMBER)
  { fprintf(stderr,"<%s> is not a cdb file, code number 0x%08x != 0x%08x\n",
	    this->filename, this->header->code_number, CDB_MAGIC_NUMBER);
    free_cdb(this);
    return (cdb_class *)NULL;
  }

/*
 *	allocate space for index and segment buffer
 */
  if (this->header->index_size == 0)
  { free_cdb(this);
    fprintf(stderr,"init_cdb: <%s> has no index\n", this->filename);
    return (cdb_class *)NULL;
  }
  if (this->header->index_size > CDB_MAX_BUFFER_SIZE)
  { free_cdb(this);
    fprintf(stderr,"init_cdb: %d bytes exceeds max index size of %d bytes\n",
	    this->header->index_size, CDB_MAX_BUFFER_SIZE);
    return (cdb_class *)NULL;
  }
  this->index = (cdb_index_entry *) calloc(this->header->index_size, 1);
  if (NULL == this->index)
  { perror("init_cdb"); free_cdb(this); return (cdb_class *)NULL; }

  this->segment = this->index;
  this->seg_count = this->header->index_size/sizeof(cdb_index_entry);
  this->index_order = (cdb_index_sort)(this->header->index_order);

  if (this->header->max_seg_size > CDB_MAX_BUFFER_SIZE)
  { free_cdb(this);
    fprintf(stderr,"init_cdb: %d bytes exceeds max segment size of %d bytes\n",
	    this->header->max_seg_size, CDB_MAX_BUFFER_SIZE);
    return (cdb_class *)NULL;
  }
  this->data_buffer = (cdb_seg_data *) calloc(this->header->max_seg_size, 1);
  if (NULL == this->data_buffer)
  { perror("init_cdb"); free_cdb(this); return (cdb_class *)NULL; }

  this->data_buffer_size = this->header->max_seg_size;
  this->data_ptr = this->data_buffer;
  this->npoints = 0;

/*
 *	read in the index and byteswap it
 */
  fseek(this->fp, this->header->index_addr, SEEK_SET);
  ios = fread(this->index, 1, this->header->index_size, this->fp);
  if (ios != this->header->index_size)
  { fprintf(stderr,"init_cdb: reading index, expected %d got %d bytes.\n",
	    this->header->index_size, ios);
    perror(this->filename);
    free_cdb(this);
    return (cdb_class *) NULL;
  }

  cdb_byteswap_index(this->index, this->seg_count);

  return this;
}

/*----------------------------------------------------------------------
 * free_cdb - close cbd file, free allocated buffer space
 *
 *	input : this - pointer to cdb_class instance
 *
 *--------------------------------------------------------------------*/
void free_cdb (cdb_class *this)
{
  if (this == NULL) return;
  if (this->filename != NULL) free(this->filename);
  if (this->fp != NULL) fclose(this->fp);
  if (this->header != NULL) free(this->header);
  if (this->index != NULL) free(this->index);
  if (this->data_buffer != NULL) free(this->data_buffer);
  free(this);
}

/*----------------------------------------------------------------------
 * copy_of_cdb - copy a cdb_class instance
 *
 *	input : this - pointer to original cdb_class instance
 *
 *	result: pointer to copy
 *
 *--------------------------------------------------------------------*/
cdb_class *copy_of_cdb(cdb_class *this)
{
  cdb_class *copy;
  
/*
 *	get new instance and copy verbatim
 */
  copy = new_cdb();
  if (copy == NULL)
  { fprintf(stderr,"copy_of_cdb: unable to get new cdb_class.\n");
    return NULL;
  }

  memcpy(copy, this, sizeof(cdb_class));

/*
 *	get new storage area for filename
 */
  copy->filename = strdup(this->filename);

/*
 *	get a new file pointer
 */
  copy->fp = fopen(copy->filename, "r");
  if (copy->fp == NULL)
  { fprintf(stderr,"copy_of_cdb: unable to re-open file.\n");
    perror(copy->filename);
    free_cdb(copy);
    return NULL;
  }

/*
 *	get new storage area for header and index and copy verbatim
 */
  copy->header = (cdb_file_header *) calloc(1, sizeof(cdb_file_header));
  copy->index = (cdb_index_entry *) calloc(this->header->index_size, 1);
  if (copy->header == NULL || copy->index == NULL)
  { fprintf(stderr,"copy_of_cdb: unable to allocate header and index.\n");
    perror("malloc");
  }
  
  memcpy((void *)copy->header, (const void *)this->header, 
	 sizeof(cdb_file_header));
  memcpy((void *)copy->index, (const void *)this->index, 
	 (size_t)this->header->index_size);

/*
 *	set current segment pointer
 */
  copy->segment = copy->index;

/*
 *	get new data buffer
 */
  copy->data_buffer = (cdb_seg_data *) calloc(copy->data_buffer_size, 1);
  if (this->data_buffer == NULL)
  { fprintf(stderr,"copy_of_cdb: unable to allocate new data buffer.\n");
    perror("malloc");
    return NULL;
  }
  memcpy((void *)copy->data_buffer, (const void *)this->data_buffer, 
	 (size_t)this->data_buffer_size);
  copy->data_ptr = copy->data_buffer + (this->data_ptr - this->data_buffer);

/*
 *	copy succeeded
 */
  return copy;
}

/*----------------------------------------------------------------------
 * load_all_seg_data_cdb - load all segment data into buffer
 *
 *	input : this - pointer to cdb_class instance
 *
 *--------------------------------------------------------------------*/
void load_all_seg_data_cdb(cdb_class *this)
{
  register int ios;

  this->is_loaded = FALSE;
  this->get_data = cdb_read_disk;

/*
 *	try to re-allocate data buffer
 *	on failure try to set things right and return
 *	failing that exit before any more damage is done
 */
  this->data_buffer_size = this->header->index_addr - CDB_FILE_HEADER_SIZE;

  if (this->data_buffer_size > CDB_MAX_BUFFER_SIZE)
  { fprintf(stderr,"load_all_seg_data_cdb: %d bytes exceeds buffer max %d\n",
	    this->data_buffer_size, CDB_MAX_BUFFER_SIZE);
    this->data_buffer_size = this->header->max_seg_size;
    return;
  }

  this->data_buffer = (cdb_seg_data *)realloc(this->data_buffer, 
					      this->data_buffer_size);
  if (this->data_buffer == NULL)
  { fprintf(stderr,"load_all_seg_data_cdb: unable to allocate %d bytes\n",
	    this->data_buffer_size);
    perror("realloc");
    this->data_buffer_size = this->header->max_seg_size;
    this->data_buffer = (cdb_seg_data *)realloc(this->data_buffer, 
						this->data_buffer_size);
    if (this->data_buffer != NULL)
    { fprintf(stderr,"load_all_seg_data_cdb: segment data corrupted.\n");
      fprintf(stderr,"cdb: fatal error exiting...\n");
      exit(ABORT);
    }
    return;
  }

/*
 *	read data into buffer and byte swap it
 */
  fseek(this->fp, CDB_FILE_HEADER_SIZE, SEEK_SET);
  ios = fread(this->data_buffer, 1, this->data_buffer_size, this->fp);
  if (ios != this->data_buffer_size)
  { fprintf(stderr,"load_all_seg_data_cdb: need %d bytes, got %d.\n",
	    this->data_buffer_size, ios);
    perror("fread");
    return;
  }

  cdb_byteswap_data_buffer(this->data_buffer,
			   this->data_buffer_size/sizeof(cdb_seg_data));

/*
 *	load succeeded
 */
  this->is_loaded = TRUE;
  this->get_data = cdb_read_memory;
  return;
}

/*----------------------------------------------------------------------
 * load_current_seg_data_cdb - read data for current segment
 *
 *	input : this - pointer to cdb_class instance
 *		this->segment points to current segment
 *
 *	result: pointer to data buffer
 *		or NULL if error occurred
 *
 *--------------------------------------------------------------------*/

/*
 *	read data from disk into data buffer
 */
static cdb_seg_data *cdb_read_disk(cdb_class *this)
{
  register int ios;

/*
 *	check buffer size
 */
  if (this->segment->size > this->data_buffer_size)
  { fprintf(stderr,"cdb_read_disk: segment needs %d bytes; buffer max = %d.\n",
	    this->segment->size, this->data_buffer_size);
    this->data_buffer = (cdb_seg_data *) realloc(this->data_buffer, 
						 this->segment->size);
    if (NULL == this->data_buffer) { return (cdb_seg_data *)NULL; }
    this->data_buffer_size = this->segment->size;
  }

/*
 *	read segment point data and byteswap it
 */
  fseek(this->fp, this->segment->addr, SEEK_SET);
  ios = fread(this->data_buffer, 1, this->segment->size, this->fp);
  if (ios != this->segment->size)
  { fprintf(stderr,"load_current_seg_data_cdb: reading segment %d, expected %d got %d bytes.\n",
	    this->segment->ID, this->segment->size, ios);
    perror(this->filename);
    return NULL;
  }

  cdb_byteswap_data_buffer(this->data_buffer,
			   this->segment->size/sizeof(cdb_seg_data));

  return this->data_buffer;
}

/*
 *	find data in data buffer
 */
static cdb_seg_data *cdb_read_memory(cdb_class *this)
{
  register byte1 *offset;
/*
 *	get byte offset in data buffer
 */
  offset = (byte1 *)(this->data_buffer) + this->segment->addr - CDB_FILE_HEADER_SIZE;
  return (cdb_seg_data *)offset;
}

/*
 *	load_current_seg_data_cdb method
 */
cdb_seg_data *load_current_seg_data_cdb(cdb_class *this)
{
  this->data_ptr = (*(this->get_data))(this);
  this->npoints = this->segment->size/sizeof(cdb_seg_data);
  return this->data_ptr;
}

/*----------------------------------------------------------------------
 * get_current_seg_cdb - retrieve current segment data points
 *
 *	input : this - pointer to cdb_class instance
 *		this->segment points to current segment
 *		max_pts = size of lat,lon arrays
 *
 *	output: lat,lon - data points
 *
 *	result: N > 0 = number of points in lat,lon arrays
 *		0 = error reading data
 *		N < 0 = max_pts is too small, need -N points
 *
 *--------------------------------------------------------------------*/
int get_current_seg_cdb(cdb_class *this, double *lat, double *lon, int max_pts)
{
  register cdb_seg_data *data;
  register int ipt;
  register double clat, clon;

/*
 *	read segment point data
 */
  data = load_current_seg_data_cdb(this);
  if (data == NULL) return 0;

/*
 *	check size of array
 */
  if (max_pts < this->npoints+1) return -(this->npoints+1);

/*
 *	convert delta data to lat,lon positions
 */
  clat = this->segment->ilat0 * CDB_LAT_SCALE;
  clon = this->segment->ilon0 * CDB_LON_SCALE;
  lat[0] = clat;
  lon[0] = clon;

  for (ipt = 1; ipt <= this->npoints; data++, ipt++)
  { clat += data->dlat * CDB_LAT_SCALE;
    clon += data->dlon * CDB_LON_SCALE;
    lat[ipt] = clat;
    lon[ipt] = clon;
  }

  return this->npoints+1;
}

/*----------------------------------------------------------------------
 * draw_current_seg_cdb - draw current segment
 *
 *	input : this - pointer to cdb_class instance
 *		this->segment points to current segment
 *              move_pu - move pen up function (returns TRUE on error)
 *              draw_pd - draw pen down function (returns TRUE on error)
 *
 *	result: 0 = normal successful completion
 *		-1 = error occurred
 *
 *--------------------------------------------------------------------*/
int draw_current_seg_cdb(cdb_class *this,
			 int (*move_pu)(double lat, double lon), 
			 int (*draw_pd)(double lat, double lon))
{
  register int ipt;
  register cdb_seg_data *data;
  register double lat, lon;

/*
 *	read segment point data
 */
  data = load_current_seg_data_cdb(this);
  if (data == NULL) return -1;

/*
 *	call move pen up function for the current segment
 */
  lat = this->segment->ilat0 * CDB_LAT_SCALE;
  lon = this->segment->ilon0 * CDB_LON_SCALE;
  if (move_pu != NULL) if (move_pu(lat, lon)) return -1;

/*
 *	call draw pen down for each point
 */
  if (draw_pd != NULL)
  {  for (ipt = 0; ipt < this->npoints; data++, ipt++)
     { lat += data->dlat * CDB_LAT_SCALE;
       lon += data->dlon * CDB_LON_SCALE;
       if (draw_pd(lat, lon)) return -1;
     }
   }

  return 0;
}

/*----------------------------------------------------------------------
 * list_cdb - list header information
 *
 *	input : this - pointer to cdb_class instance
 *		verbose - if set print segment index too
 *
 *--------------------------------------------------------------------*/

#define cdb_list_printable(order) \
  ((order) >= 1 && (order) <= 5 ? cdb_index_sort_string[order] : "undefined")

void list_cdb(cdb_class *this, int verbose)
{
  register int i;
  register cdb_index_entry *seg;

/*
 *	list header information
 */
  printf("/////////////////////////////////////////////////////////////////////////////\n");
  printf("// %s - %s.\n", this->filename, this->header->text);
  printf("// (%4.2f%c - %4.2f%c) X (%4.2f%c - %4.2f%c)\n", 
	 fabs(this->header->ilat_min*CDB_LAT_SCALE), 
	 this->header->ilat_min < 0 ? 'S' : 'N',
	 fabs(this->header->ilat_max*CDB_LAT_SCALE), 
	 this->header->ilat_max < 0 ? 'S' : 'N',
	 fabs(this->header->ilon_min*CDB_LON_SCALE), 
	 this->header->ilon_min < 0 ? 'W' : 'E',
	 fabs(this->header->ilon_max*CDB_LON_SCALE), 
	 this->header->ilon_max < 0 ? 'W' : 'E');
  printf("// %d segments of rank %d, sorted in %s order\n", this->seg_count, 
	 this->header->segment_rank, 
	 cdb_list_printable(this->header->index_order));
  printf("// %d index bytes at %d\n", this->header->index_size, 
	 this->header->index_addr);
  printf("// index currently sorted in %s order\n", 
	 cdb_list_printable(this->index_order));
  printf("// max data segment size = %d bytes\n", this->header->max_seg_size);
  printf("// maximum extent in latitude = %5.3f, longitude = %5.3f.\n", 
	 this->header->ilat_extent*CDB_LAT_SCALE,
	 this->header->ilon_extent*CDB_LON_SCALE);

/*
 *	list segment index entries
 */
  if (verbose)
  {
    printf("// --------------------------------------------------------------------------\n");
    printf("//        origin          lat            lon              data\n");
    printf("//  ID     lat    lon      min    max     min     max      npts     address\n");
    printf("// -----  ------ -------  ------ ------  ------- -------  -------  ----------\n");
    for (i=1, seg=this->index; i <= this->seg_count; i++, seg++) 
    { printf("// %5d  %6.2f %7.2f  %6.2f %6.2f  %7.2f %7.2f  %7d  %10d\n", 
	     seg->ID,
	     seg->ilat0*CDB_LAT_SCALE, seg->ilon0*CDB_LAT_SCALE,
	     seg->ilat_min*CDB_LAT_SCALE, seg->ilat_max*CDB_LON_SCALE,
	     seg->ilon_min*CDB_LAT_SCALE, seg->ilon_max*CDB_LON_SCALE,
	     seg->size/sizeof(cdb_seg_data), seg->addr);
    }
  }
}

/*----------------------------------------------------------------------
 * sort_index_cdb - sort segment index
 *
 *	input : this - pointer to cdb_class instance
 *		order - index will be sorted as follows:
 *			CDB_INDEX_LAT_MAX => by decreasing ilat_max
 *			CDB_INDEX_LON_MAX => by decreasing ilon_min
 *			CDB_INDEX_LAT_MIN => by increasing ilat_min
 *			CDB_INDEX_LON_MIN => by increasing ilon_min
 *			CDB_INDEX_SEG_ID => by increasing segment ID
 *
 *--------------------------------------------------------------------*/

/*
 *	compare function to sort index by decreasing ilat_max
 *	see qsort(3C)
 */
static int cdb_sort_lat_max(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
    return seg2->ilat_max - seg1->ilat_max;
}

/*
 *	compare function to sort index by decreasing ilon_max
 */
static int cdb_sort_lon_max(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
    return seg2->ilon_max - seg1->ilon_max;
}

/*
 *	compare function to sort index by increasing ilat_min
 */
static int cdb_sort_lat_min(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
    return seg1->ilat_min - seg2->ilat_min;
}

/*
 *	compare function to sort index by increasing ilon_min
 */
static int cdb_sort_lon_min(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
    return seg1->ilon_min - seg2->ilon_min;
}

/*
 *	compare function to sort index by increasing segment ID
 */
static int cdb_sort_seg_ID(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
    return seg1->ID - seg2->ID;
}

/*
 *	sort method
 */
void sort_index_cdb(cdb_class *this, cdb_index_sort order)
{
  int (*compare)();

  if (order == this->index_order) return;

  switch (order)
  { case CDB_INDEX_LAT_MAX:
      compare = cdb_sort_lat_max;
      break;
    case CDB_INDEX_LON_MAX:
      compare = cdb_sort_lon_max;
      break;
    case CDB_INDEX_LAT_MIN:
      compare = cdb_sort_lat_min;
      break;
    case CDB_INDEX_LON_MIN:
      compare = cdb_sort_lon_min;
      break;
    case CDB_INDEX_SEG_ID:
      compare = cdb_sort_seg_ID;
      break;
    default:
      fprintf(stderr,"sort_index_cdb: unknown sort order %d.\n", order);
      return;
  }

  qsort(this->index,this->seg_count,sizeof(cdb_index_entry),compare);

  this->index_order = order;

}

/*----------------------------------------------------------------------
 * find_segment_cdb - set current pointer to specified segment
 *
 *	input : this - pointer to cdb_class instance
 *		key_value - lat or lon value to find
 *
 *	result: pointer to found index entry
 *		(also, this->segment points to found index entry)
 *		or NULL if key value not found
 *
 *--------------------------------------------------------------------*/

/*
 *	pointer for bounds checking
 *	set by find_segment_cdb, checked by compare functions
 */
static cdb_index_entry *first_seg, *last_seg;

/*
 *	compare function for index sorted by decreasing ilat_max
 *	see bsearch(3C)
 */
static int cdb_find_lat_max(cdb_index_entry *key, cdb_index_entry *seg)
{
  if (seg == first_seg && key->ilat_max >= seg->ilat_max)
    return 0;
  else if (seg == last_seg && key->ilat_max <= seg->ilat_max)
    return 0;
  else if (key->ilat_max <= seg->ilat_max
       && key->ilat_max > (seg+1)->ilat_max)
    return 0;
  else 
    return seg->ilat_max - key->ilat_max;
}

/*
 *	compare function for index sorted by decreasing ilon_max
 */
static int cdb_find_lon_max(cdb_index_entry *key, cdb_index_entry *seg)
{
  if (seg == first_seg && key->ilon_max >= seg->ilon_max)
    return 0;
  else if (seg == last_seg && key->ilon_max <= seg->ilon_max)
    return 0;
  else if (key->ilon_max <= seg->ilon_max
       && key->ilon_max > (seg+1)->ilon_max)
    return 0;
  else 
    return seg->ilon_max - key->ilon_max;
}

/*
 *	compare function for index sorted by increasing ilat_min
 */
static int cdb_find_lat_min(cdb_index_entry *key, cdb_index_entry *seg)
{
  if (seg == first_seg && key->ilat_min <= seg->ilat_min)
    return 0;
  else if (seg == last_seg && key->ilat_min >= seg->ilat_min)
    return 0;
  else if (key->ilat_min >= seg->ilat_min
       && key->ilat_min < (seg+1)->ilat_min)
    return 0;
  else 
    return key->ilat_min - seg->ilat_min;
}

/*
 *	compare function for index sorted by increasing ilon_min
 */
static int cdb_find_lon_min(cdb_index_entry *key, cdb_index_entry *seg)
{
  if (seg == first_seg && key->ilon_min <= seg->ilon_min)
    return 0;
  else if (seg == last_seg && key->ilon_min >= seg->ilon_min)
    return 0;
  else if (key->ilon_min >= seg->ilon_min
       && key->ilon_min < (seg+1)->ilon_min)
    return 0;
  else 
    return key->ilon_min - seg->ilon_min;
}

/*
 *	compare function for index sorted by increasing segment ID
 */
static int cdb_find_seg_ID(cdb_index_entry *key, cdb_index_entry *seg)
{
  return key->ID - seg->ID;
}

/*
 *	find method
 */
cdb_index_entry *find_segment_cdb(cdb_class *this, double key_value)
{
  cdb_index_entry key;
  int (*compare)();
  register double bottom_value;

  switch (this->index_order)
  { case CDB_INDEX_LAT_MAX:
      key.ilat_max = key_value/CDB_LAT_SCALE;
      compare = cdb_find_lat_max;
      bottom_value = 90.00;
      break;
    case CDB_INDEX_LON_MAX:
      normalize_lon_cdb(key_value);
      key.ilon_max = key_value/CDB_LON_SCALE;
      compare = cdb_find_lon_max;
      bottom_value = 180.00;
      break;
    case CDB_INDEX_LAT_MIN:
      key.ilat_min = key_value/CDB_LAT_SCALE;
      compare = cdb_find_lat_min;
      bottom_value = -90.00;
      break;
    case CDB_INDEX_LON_MIN:
      normalize_lon_cdb(key_value);
      key.ilon_min = key_value/CDB_LON_SCALE;
      compare = cdb_find_lon_min;
      bottom_value = -180.00;
      break;
    case CDB_INDEX_SEG_ID:
      key.ID = key_value;
      compare = cdb_find_seg_ID;
      bottom_value = -1;
      break;
    default:
      fprintf(stderr,"find_segment_cdb: "
	      "index must be sorted to search by key value.\n");
      this->segment = NULL;
      return NULL;
  }
  
  if (key_value == bottom_value)
  { this->segment = this->index;
  }
  else
  { first_seg = this->index;
    last_seg = last_segment_cdb(this);

    this->segment = bsearch((const void *)&key, (const void *)this->index,
			    (size_t)this->seg_count, sizeof(cdb_index_entry),
			    compare);
  }
  return this->segment;
}

/*----------------------------------------------------------------------
 * index_limit_test_cdb - test current segment within interval 
 *		(which field depends on sort order)
 *
 *	input : this - pointer to cdb_class instance
 *		lower_bound - lat or lon value
 *		upper_bound - lat or lon value
 *
 *	result: 1 iff current segment is within bounds
 *
 *--------------------------------------------------------------------*/
int index_limit_test_cdb(cdb_class *this, double lower_bound,
			 double upper_bound)
{
  double test_val;
  switch (this->index_order)
  { case CDB_INDEX_LAT_MAX:
      test_val = this->segment->ilat_max*CDB_LAT_SCALE;
      break;
    case CDB_INDEX_LON_MAX:
      test_val = this->segment->ilon_max*CDB_LON_SCALE;
      break;
    case CDB_INDEX_LAT_MIN:
      test_val = this->segment->ilat_min*CDB_LAT_SCALE;
      break;
    case CDB_INDEX_LON_MIN:
      test_val = this->segment->ilon_min*CDB_LON_SCALE;
      break;
    case CDB_INDEX_SEG_ID:
      test_val = this->segment->ID;
      break;
    default:
      fprintf(stderr,"index_limit_test_cdb: sort order %d not testable.\n", 
	      this->index_order);
      return 0;
  }
  return test_val >= lower_bound && test_val <= upper_bound;
}

/*----------------------------------------------------------------------
 * draw_cdb - draw all segments within bounds
 *
 *	input : this - pointer to cdb_class instance
 *		start - either lat or lon depending on order
 *		stop - either lat or lon depending on order
 *		order - sort index order
 *              move_pu - move pen up function (returns TRUE on error)
 *              draw_pd - draw pen down function (returns TRUE on error)
 *
 *	result: 0 = success, -1 = error
 *
 *	effect: calls draw_current_segment_cdb for each segment within bounds
 *
 *--------------------------------------------------------------------*/
int draw_cdb(cdb_class *this, double start, double stop, cdb_index_sort order,
	      int (*move_pu)(double lat, double lon), 
	      int (*draw_pd)(double lat, double lon))
{
  int split_search = FALSE;
  double lower, upper;
  cdb_index_entry *last;

  last = last_segment_cdb(this);

  sort_index_cdb(this, order);

  switch (this->index_order)
  { case CDB_INDEX_LAT_MAX:
      start += this->header->ilat_extent*CDB_LAT_SCALE;
      if (start > 90) start = 90;
      lower = stop;
      upper = 90;
      break;
    case CDB_INDEX_LAT_MIN:
      start -= this->header->ilat_extent*CDB_LAT_SCALE;
      if (start < -90) start = -90;
      lower = -90;
      upper = stop;
      break;
    case CDB_INDEX_LON_MAX:
      if (start <= stop || start > 180) split_search = TRUE;
      if (start != stop && start != stop+360 && start != stop-360)
	start += this->header->ilon_extent*CDB_LON_SCALE;
      if (start > 180) start = 180;
      normalize_lon_cdb(start);
      normalize_lon_cdb(stop);
      lower = stop;
      upper = 180;
      break;
    case CDB_INDEX_LON_MIN:
      if (start >= stop || stop > 180) split_search = TRUE;
      if (start != stop && start != stop+360 && start != stop-360)
	start -= this->header->ilon_extent*CDB_LON_SCALE;
      if (start < -180) start = -180;
      normalize_lon_cdb(start);
      normalize_lon_cdb(stop);
      lower = -180;
      upper = stop;
      break;
    case CDB_INDEX_SEG_ID:
      lower = 0;
      upper = stop;
    default:
      assert(NEVER);
  }

/*
 *	if sorted by longitude and bounds cross +/-180
 *	then split search into two parts
 */
  if (split_search)
  { for(find_segment_cdb(this,start);
	current_seg_cdb(this) <= last;
	next_segment_cdb(this))
      if (draw_current_seg_cdb(this, move_pu, draw_pd)) return -1;
    for(reset_current_seg_cdb(this);
	current_seg_cdb(this) <= last
	&& index_limit_test_cdb(this, lower, upper);
	next_segment_cdb(this))
      if (draw_current_seg_cdb(this, move_pu, draw_pd)) return -1;
  }

/*
 *	otherwise search in normal way
 */
  else
  { for (find_segment_cdb(this, start);
	 current_seg_cdb(this) <= last
	 && index_limit_test_cdb(this, lower, upper);
	 next_segment_cdb(this))
      if (draw_current_seg_cdb(this, move_pu, draw_pd)) return -1;
  }

  return 0;
}
