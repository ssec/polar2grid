/*========================================================================
 *  cdb_edit - edit .cdb files
 *
 *  cdb_edit assumes machine byte order is most significant byte first.
 *  For least significant byte first machines compile with -DLSB1ST.
 *
 *  Each cbd file has a 40 byte header, the header contains a pointer
 *  to the segment dictionary for the file, the dictionary has one
 *  entry for each segment in the file, each segment has a 12 byte tag,
 *  and is followed by nbytes of stroke data, each data value pair is
 *  a delta from the end of the previous stroke (starting at x0, y0) all
 *  x values are seconds of longitude, y values are seconds of latitude.
 * 
 *  7-Apr-1993 R.Swick swick@chukchi.colorado.edu  303-492-6069  
 *  National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <ctype.h>
#include <assert.h>
#include "define.h"
#include "cdb.h"
#include "mapx.h"
#include "cdb_byteswap.h"

#define SQ(x) x*x
#define MPP_FILENAME "cdb_edit.mpp"
#define MAX_SEGMENT_POINTS 100000      /* maximum number of points in any joined segment */

typedef enum 
{ JOIN_NO_METHOD=0,
  JOIN_START_TO_START,
  JOIN_START_TO_END,
  JOIN_END_TO_START,
  JOIN_END_TO_END,
} cdb_edit_join_method;


/*------------------------------------------------------------------------
 * globals
 *------------------------------------------------------------------------*/

static char *new_filename;
static char *cc_filename, *joined_filename;
static char temp[MAX_STRING];
static FILE *new_file;
static mapx_class *map;
static cdb_class *source;
static cdb_class *dest;
static cdb_index_entry *current_segment;
static int (*compare)();

static int max_index_entries = 0;
static int max_data_points = 0;
static int join = FALSE;
static int do_sort = FALSE;
static int verbose = FALSE;
static int very_verbose = FALSE;
static int very_very_verbose = FALSE;
static float thin = 0.01;
static float north = 90.0, south = -90.0, east = 180.0, west = -180.0;
static char label[32] = "created by cdb_edit";  
static float current_x_start, current_y_start;
static float current_x_end, current_y_end;
  
/*------------------------------------------------------------------------
 * function prototypes
 *------------------------------------------------------------------------*/
int move_pu(float, float);
int draw_pd(float, float);
void write_segment_data(int);
int parallels_min(cdb_index_entry *, cdb_index_entry *);
int meridians_min(cdb_index_entry *, cdb_index_entry *);
int parallels_max(cdb_index_entry *, cdb_index_entry *);
int meridians_max(cdb_index_entry *, cdb_index_entry *);
void thin_current_segment(void);
void copy_current_segment(void);
void thin_map(void);
void reverse_current_segment(void);
void join_map(void);
void append_candidate(int, float *, float *, float *, float *);
void clip_and_concat_files(int, char **, float, float, float, float);
cdb_index_entry *find_best_candidate(cdb_edit_join_method *);

/*------------------------------------------------------------------------
 * usage
 *------------------------------------------------------------------------*/
#define usage "\n"\
 "usage: cdb_edit [-tj thin -n north -s south -e east -w west\n"\
 "                 -h label -pqlmv] new_cdb_file source_cdb_file ...\n"\
 "\n"\
 " input : source_cdb_file - file(s) to edit (may be more than one)\n"\
 "\n"\
 " output: new_cdb_file - edit applied to source(s)\n"\
 "\n"\
 " option: t thin - thin strokes to a maximum error of thin kilometers.\n"\
 "                (default = 0.01 kilometer = no thinning)\n"\
 "         j join - join segments within thin kilometers then thin.\n"\
 "                (default = 0.01 kilometer = no joining, no thinning)\n"\
 "         n north - northern lat bound (default 90)\n"\
 "         s south - southern lat bound (default -90)\n"\
 "         e east - eastern lon bound (default 180)\n"\
 "         w west - western lon bound (default -180)\n"\
 "         h label - specify header label text (31 chars max)\n"\
 "         p parallels_min - sort index by lat_min (cancels -m, -q, -l)\n"\
 "         q parallels_max - sort index by lat_max (cancels -m, -l, -p)\n"\
 "         l meridians_min - sort index by lon_min (cancels -p, -q, -m)\n"\
 "         m meridians_max - sort index by lon_max (cancels -p, -q, -l)\n"\
 "         v - verbose diagnostic messages (may be repeated)\n"\
 "\n"


main(int argc, char *argv[])
{ 
  register int i, ios, extent;
  char *option;
  char command[MAX_STRING];
    
/*
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { 
    for (option = argv[0]+1; *option != '\0'; option++)
    { 
      switch (*option)
      { 
      case 't':
	argc--; argv++;
	if (argc <= 0 || sscanf(*argv,"%f", &thin) != 1) error_exit(usage);
	break;
      case 'n':
	argc--; argv++;
	if (argc <= 0 || sscanf(*argv,"%f", &north) != 1) error_exit(usage);
	break;
      case 's':
	argc--; argv++;
	if (argc <= 0 || sscanf(*argv,"%f", &south) != 1) error_exit(usage);
	break;
      case 'e':
	argc--; argv++;
	if (argc <= 0 || sscanf(*argv,"%f", &east) != 1) error_exit(usage);
	break;
      case 'w':
	argc--; argv++;
	if (argc <= 0 || sscanf(*argv,"%f", &west) != 1) error_exit(usage);
	break;
      case 'v':
	if (very_verbose) very_very_verbose = TRUE;
	if (verbose) very_verbose = TRUE;
	verbose = TRUE;
	break;
      case 'p':
	do_sort = TRUE;
	compare = parallels_min;
	break; 
      case 'q':
	do_sort = TRUE;
	compare = parallels_max;
	break;
      case 'l':
	do_sort = TRUE;
	compare = meridians_min;
	break;
      case 'm':
	do_sort = TRUE;
	compare = meridians_max;
	break;
      case 'h':
	argc--; argv++;
	strncpy(label, *argv, 31);
	break;
      case 'j':
	argc--; argv++;
	if (argc <= 0 || sscanf(*argv,"%f", &thin) != 1) error_exit(usage);
	join = TRUE;
	break;
      default:
	fprintf(stderr, "invalid option %c\n", *option);
	error_exit(usage);
      }
    }
  }

/*
 *	get new filename
 */
  if (argc < 2) error_exit(usage);
  new_filename = strdup(*argv);
  
  sprintf(temp, "cc_%s", new_filename);
  cc_filename = strdup(temp);
  
  sprintf(temp, "joined_%s", new_filename);
  joined_filename = strdup(temp);
  
  argc--; argv++;
  if (verbose) 
    fprintf(stderr,">creating: %s\n>thin: %f km\n",
	    new_filename, thin);

/*
 *      initialize .mpp file
 */

  map = init_mapx(MPP_FILENAME);
  if (NULL == map) 
  { fprintf(stderr,"cdb_edit: get a copy of %s, or set the environment\n"\
	    "          variable PATHMPP to the appropriate directory\n",
	    MPP_FILENAME);
    exit(ABORT);
  }
  map->scale = thin/3;
  reinit_mapx(map);
  if(very_verbose) 
    fprintf(stderr, ">>initialized map\n"); 

/*
 *  initialize destination cdb_file
 */

  dest = new_cdb();
  if(NULL == dest) { perror("destination cdb class"); exit(ABORT); }
  dest->header = (cdb_file_header *) calloc(1, sizeof(cdb_file_header));
    
/*
 *	record segment data and create index
 */
  if(join)
  { 
    if (verbose) fprintf(stderr,">clipping source file(s)\n");
    clip_and_concat_files(argc, argv, north, south, east, west);

    free_cdb(source);
    source = NULL;
    source = init_cdb(cc_filename);     
    if(source == NULL) { perror(cc_filename); exit(ABORT); }

    if (verbose) fprintf(stderr,">joining %s...\n", new_filename);
    join_map(); 
    
    free_cdb(source);
    source = NULL;
    source = init_cdb(joined_filename);     
    if(source == NULL) { perror(joined_filename); exit(ABORT); }

    if (verbose) fprintf(stderr,">thinning %s...\n", new_filename);
    thin_map(); 
  }
   
  else
  {
    if (verbose) fprintf(stderr,">clipping source file(s)\n");
    clip_and_concat_files(argc, argv, north, south, east, west);
        
    free_cdb(source);
    source = init_cdb(cc_filename); 
    if(source == NULL) { perror(cc_filename); exit(ABORT); }

    if (verbose) fprintf(stderr,">thining %s...\n", new_filename );
    thin_map();
  }

/*
 *	flush segment data buffer
 */
  if (dest->npoints > 0) write_segment_data(dest->seg_count);

/*
 *	sort index and finish up
 */
  if (do_sort)
  { if (verbose) fprintf(stderr,">sorting %d index entries...\n", dest->seg_count);
    qsort(dest->index, dest->seg_count, sizeof(cdb_index_entry), compare);
  }
 
  finish_new_file();
   
  sprintf(command, "cdb_list %s", new_filename);
  if(verbose) system(command);

  free(new_file);
  free(map);
  free_cdb(dest);
  free_cdb(source);
  free(label);

/*
 *  remove temporary files
 */
/******
  if(join)
    sprintf(command, "rm %s %s", cc_filename, joined_filename);
  
  else
    sprintf(command, "rm %s", cc_filename);
  
  system(command);********/ 
}


/*------------------------------------------------------------------------
 * move_pu - move pen up function.
 *
 *  input: lat, lon - beginning of a new segment
 *
 * result: previous segment is written, a new segment index entry is started,
 *         and the map is recentered.
 *
 * return: FALSE on success
 *         TRUE if fatal error occurs (unabel to allocate enough memory)
 *------------------------------------------------------------------------*/
 int move_pu(float lat, float lon)
{
  float nlon;

/*
 *	write current segment
 */

  if (dest->npoints > 0) write_segment_data(dest->seg_count);
    
/*
 *	make sure index is big enough
 */
  if (dest->seg_count >= max_index_entries)
  { max_index_entries += 1000;
    dest->index = 
      (cdb_index_entry *) realloc(dest->index, 
				  sizeof(cdb_index_entry) *  max_index_entries);
    if(NULL == dest->index)
    {
      fprintf(stderr,"move_pu: Unable to allocate %d index entries\n", 
	      max_index_entries);
      return -1;
    }
    if (verbose) fprintf(stderr,">allocating %d index entries.\n",
			 max_index_entries);
  }


/*
 *	start a new segment
 */
  dest->index[dest->seg_count].ID = dest->seg_count;
  dest->index[dest->seg_count].ilat0 = nint(lat/CDB_LAT_SCALE);
  nlon = lon;
  NORMALIZE(nlon);
  dest->index[dest->seg_count].ilon0 = nint(nlon/CDB_LON_SCALE);
  dest->index[dest->seg_count].ilat_max = dest->index[dest->seg_count].ilat0;
  dest->index[dest->seg_count].ilon_max = dest->index[dest->seg_count].ilon0;
  dest->index[dest->seg_count].ilat_min = dest->index[dest->seg_count].ilat0;
  dest->index[dest->seg_count].ilon_min = dest->index[dest->seg_count].ilon0;

/*
 * recenter map
 */

  map->center_lat = lat;
  map->center_lon = nlon;
  map->lat0 = lat;
  map->lon0 = nlon;
  reinit_mapx(map);
  dest->npoints = 0;
  if (very_very_verbose)fprintf(stderr,">>> recentered map to %f %f.\n",
				map->lat0,  map->lon0);
  return 0;
  }


/*------------------------------------------------------------------------
 * draw_pd - draw pen down function
 *
 *  input: lat, lon - position of next point.
 *
 * result: the next point of the segment is put in the data buffer
 *         and the map is recentered.
 *
 * return: 0 on success
 *         -1 if fatal error occurs (unabel to allocate enough memory)
 *------------------------------------------------------------------------*/
int draw_pd(float lat, float lon)
{
  register int ilat, ilon;
  static float lat1,lon1;
  auto float lat3,lon3;

/*
 *	make sure segment is big enough
 */
  if (dest->npoints >= max_data_points)
  { max_data_points += 1000;
    dest->data_buffer = (cdb_seg_data *)
      realloc(dest->data_buffer, sizeof(cdb_seg_data) * max_data_points);
    			
    if(NULL == dest->data_buffer)
    {
      fprintf(stderr,"draw_pd: Unable to allocate %d data points\n", 
	      max_data_points);
      return -1;
    }
    if (verbose) fprintf(stderr,">allocating %d data points.\n",
			 max_data_points);
  }

/*
 *	check for start of new segment
 */
  if (0 == dest->npoints)
  {
    lat1 = dest->index[dest->seg_count].ilat0 * CDB_LAT_SCALE;
    lon1 = dest->index[dest->seg_count].ilon0 * CDB_LON_SCALE;
    if (very_verbose)fprintf(stderr,">>new segment: %f %f.\n",lat1,lon1);
  }

/*
 *	add point lat3,lon3 to segment
 */

  lat3 = lat;
  lon3 = lon;

/*
 * Make sure segment does not end up crossing 180 due to conversion error.
 */
  if(lon3 > 180.0) lon3 = 180.0;
  if(lon3 < -180.0) lon3 = -180.0;

  lat1 = lat3 - lat1;
  lon1 = lon3 - lon1;
  lat1 = lat1/CDB_LAT_SCALE;
  lon1 = lon1/CDB_LON_SCALE;

  dest->data_buffer[dest->npoints].dlat = nint(lat1);
  dest->data_buffer[dest->npoints].dlon = nint(lon1);
  
  ilat = nint(lat3/CDB_LAT_SCALE);
  ilon = nint(lon3/CDB_LON_SCALE);
   
  lat1 = lat3;
  lon1 = lon3;
  ++dest->npoints;
   
/*
 *	update header
 */ 
  if (dest->header->max_seg_size < dest->npoints*sizeof(cdb_seg_data))
    dest->header->max_seg_size = dest->npoints*sizeof(cdb_seg_data);
  if (very_very_verbose)fprintf(stderr,">>>add point %f %f.\n",lat3,lon3);
  
/*
 *	update index entry
 */
  if (dest->index[dest->seg_count].ilat_max < ilat)
    dest->index[dest->seg_count].ilat_max = ilat;
  if (dest->index[dest->seg_count].ilon_max < ilon)
    dest->index[dest->seg_count].ilon_max = ilon;
  if (dest->index[dest->seg_count].ilat_min > ilat)
    dest->index[dest->seg_count].ilat_min = ilat;
  if (dest->index[dest->seg_count].ilon_min > ilon)
    dest->index[dest->seg_count].ilon_min = ilon;

/*
 * recenter map
 */
  map->center_lat = lat1;
  map->center_lon = lon1;
  map->lat0 = lat1;
  map->lon0 = lon1;
  reinit_mapx(map);
  if (very_very_verbose)fprintf(stderr,">>> recentered map to %f %f.\n",
				lat1, lon1);

  return 0;
}


/*------------------------------------------------------------------------
 * write_segment_data - and get segment address and size
 *------------------------------------------------------------------------*/
 void write_segment_data(int seg)
{
  register int ios;

  dest->index[seg].addr = ftell(new_file);
  dest->index[seg].size = dest->npoints*sizeof(cdb_seg_data);
  cdb_byteswap_data_buffer(dest->data_buffer, dest->npoints);
  ios = fwrite(dest->data_buffer, sizeof(cdb_seg_data), dest->npoints, new_file);
  if (very_verbose) fprintf(stderr,">>wrote %d points of segment %d.\n",
	 ios+1, dest->index[seg].ID);
  if (ios != dest->npoints)
  { fprintf(stderr,"cdb_edit: error writing data segment %d.\n",
     dest->index[seg].ID);
    perror(new_filename);
    exit(ABORT);
  }
  dest->seg_count++;
}

/*------------------------------------------------------------------------
 * parallels - compare functions for qsort.
 *             parallels_min -> increasing lat_min
 *             parallels_max -> decreasing lat_max
 *------------------------------------------------------------------------*/
 int parallels_min(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
  return (seg1->ilat_min - seg2->ilat_min);
}

 int parallels_max(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
  return (seg2->ilat_max - seg1->ilat_max);
}


/*------------------------------------------------------------------------
 * meridians - compare functions for qsort. 
 *             meridians_min -> increasing lon_min
 *             meridians_max -> decreasing lon_max
 *------------------------------------------------------------------------*/

 int meridians_min(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
  return (seg1->ilon_min - seg2->ilon_min);
}

 int meridians_max(cdb_index_entry *seg1, cdb_index_entry *seg2)
{
  return (seg2->ilon_max - seg1->ilon_max);
}


/*----------------------------------------------------------------------
 * thin_map  map thinning routine
 *
 * result: steps through source segments and thins or copys to dest,
 *         depending on the value of "thin".
 *----------------------------------------------------------------------*/
void thin_map()
{
  int iseg, ios;
 
/*
 *      open output file and reserve space for header, 
 */
  
  new_file = NULL;
  new_file = fopen(new_filename, "w");
  if (new_file == NULL) {perror(new_filename); error_exit(usage); }
  ios = fwrite(dest->header, 1, CDB_FILE_HEADER_SIZE, new_file);
  if (very_verbose) fprintf(stderr,">>wrote %d bytes for header.\n",ios);
  if (ios != CDB_FILE_HEADER_SIZE)
  { fprintf(stderr,"cdb_edit: error writing header.\n");
    perror(new_filename);
    exit(ABORT);
  }
   
/*
 *     get rank
 */
    
  if (source->header->segment_rank > dest->header->segment_rank)
    dest->header->segment_rank = source->header->segment_rank;
/*
 *	step thru segment dictionary entries
 */

  for (iseg = 0, reset_current_seg_cdb(source); 
       iseg < source->seg_count; iseg++, next_segment_cdb(source))
  {

/*
 *    read and draw the segment
 */
    load_current_seg_data_cdb(source);
    if(thin < 0.09 && NULL != source->data_ptr)
      copy_current_segment();
    else if(NULL != source->data_ptr)
      thin_current_segment();
  }
  if(verbose)
    list_cdb(source, very_very_verbose); 
}

  
/*------------------------------------------------------------------------
 * thin_current_segment - check each stroke of the current segment
 *                        and thin to one stroke per 'thin' kilometers
 *------------------------------------------------------------------------*/ 

void thin_current_segment()
{
  int idata, ipoints;
  double lat = 0.0, lon = 0.0;
  float x1, x2, x3, y1, y2, y3;
  int next_point_ok = FALSE, inside = TRUE;
  lat = (double)source->segment->ilat0 * CDB_LAT_SCALE;
  lon = (double)source->segment->ilon0 * CDB_LON_SCALE;
  
  move_pu(lat, lon);
  forward_mapx(map, lat, lon, &x1, &y1);
  x1 = nint(x1);
  y1 = nint(y1);
  x2 = x1;
  y2 = y1;
 
  for (idata = 0, ipoints = 1; idata < source->npoints; 
       idata++, source->data_ptr++)
  {
    lat += (double)source->data_ptr->dlat*CDB_LAT_SCALE;
    lon += (double)source->data_ptr->dlon*CDB_LON_SCALE;
    forward_mapx(map, lat, lon, &x3, &y3);
    x3 = nint(x3);
    y3 = nint(y3);
    next_point_ok = FALSE;
    
/*
 *    see if current point is too far away
 */    
    if(fabs(x1-x3) >= 2 || fabs(y1-y3) >= 2)
    {
      if(y1 != y2 && y1 != y3 && (x1-x3)/(y1-y3) == (x1-x2)/(y1-y2))
	next_point_ok = TRUE;
      if(x1 != x2 && x1 != x3 && (y1-y3)/(x1-x3) == (y1-y2)/(x1-x2))
	next_point_ok = TRUE;
      
      if (inside)
      {
	inside = FALSE;
	next_point_ok = TRUE;
      }
    }
    else { next_point_ok = TRUE; }
    
    if(next_point_ok)
    {
      x2 = x3;
      y2 = y3;
    }
    
    else
    { lat -= (double)source->data_ptr->dlat*CDB_LAT_SCALE;
      lon -= (double)source->data_ptr->dlon*CDB_LON_SCALE;
      draw_pd(lat, lon);
      x1 = x2;
      y1 = y2;
      source->data_ptr--;
      idata--;
      ipoints++;
      inside = TRUE;
      
    }  /* end else    */
    
  }  /* end for.... */

/*
 *      Always include the last point.
 */

  draw_pd(lat, lon);
  next_point_ok = FALSE;
  ipoints++;
  if (very_verbose) 
    { fprintf(stderr,">>segment was %d points.\n",
	      source->npoints + 1); 
      fprintf(stderr,">>segment is now %d points.\n",
	      ipoints); 
    }
  
 
}
  

/*------------------------------------------------------------------------
 * copy_current_segment - copy each stroke of the current segment
 *------------------------------------------------------------------------*/ 

 void copy_current_segment()
{
  int idata;
  double lat = 0.0, lon = 0.0;
  
  lat = (double)source->segment->ilat0*CDB_LAT_SCALE;
  lon = (double)source->segment->ilon0*CDB_LON_SCALE;
  
  move_pu(lat, lon);
   
  for (idata = 1; idata <= source->npoints; 
       idata++, source->data_ptr++)
  {
    lat += (double)source->data_ptr->dlat*CDB_LAT_SCALE;
    lon += (double)source->data_ptr->dlon*CDB_LON_SCALE;
    draw_pd(lat, lon);
  }
}

  
/*------------------------------------------------------------------------
 * reverse_current_segment - reverse the order of strokes of current
 *                           segment  (dest->index[dest->seg_count])
 *------------------------------------------------------------------------*/ 

 void reverse_current_segment()
{ 
  static float *lat = NULL;
  static float *lon = NULL;
  int ipoints;

  ipoints = dest->npoints + 1;
  lat = (float *)realloc(lat, ipoints * sizeof(double));
  lon = (float *)realloc(lon, ipoints * sizeof(double));
  if(NULL == lat || NULL == lon)
    {
      fprintf(stderr,"reverse_current_segment: Unable to allocate %d points for segment %d\n", 
	      ipoints, dest->index[dest->seg_count].ID);
      return;
    }
  if(very_verbose)
    fprintf(stderr, ">> Reversing current segment (%d).\n", 
	    dest->index[dest->seg_count].ID);


  lat[0] = (float) dest->index[dest->seg_count].ilat0 * CDB_LAT_SCALE;
  lon[0] = (float) dest->index[dest->seg_count].ilon0 * CDB_LON_SCALE;

/*
 *       Load true lat/lon for all segment points
 */

 for(ipoints = 0; ipoints < dest->npoints; ipoints++)
 {
   lat[ipoints + 1] = lat[ipoints] + 
     (float) dest->data_buffer[ipoints].dlat * CDB_LAT_SCALE;
   lon[ipoints + 1] = lon[ipoints] + 
     (float) dest->data_buffer[ipoints].dlon * CDB_LON_SCALE;
 }

/*
 *     Read segment data back into current segment in reverse order
 */

  dest->index[dest->seg_count].ilat0 = nint(lat[dest->npoints] / CDB_LAT_SCALE);
  dest->index[dest->seg_count].ilon0 = nint(lon[dest->npoints] / CDB_LON_SCALE);

  for(ipoints = dest->npoints - 1, dest->npoints = 0; 
      ipoints >= 0; ipoints--)
  {
    draw_pd(lat[ipoints], lon[ipoints]);
      
  }
  
  return;
}
    
  
/*------------------------------------------------------------------------
 * clip_and_concat_files - consolidate all source files.
 *
 *  input: number_of_files - number of files in filenames[].
 *         filenames - files to be clipped and concatenated.
 *         lat_min...lon_max - furthest bounds of map, should be
 *	      outside of any clipping window you have defined
 *	      (note: no clipping is done by this routine, it just
 *	      ignores any segment not completely within the map)
 *
 * result: a new coastlines database (filename.cdb) file, that contains
 *            all segments within bounds, is created
 *----------------------------------------------------------------------*/

 void clip_and_concat_files(int number_of_files, char *filenames[],
			    float lat_max, float lat_min, 
			    float lon_max, float lon_min)
{
  int map_stradles_180;
  int ifiles, iseg, ios;
  
/*
 *	check for special case where map stradles 180 degrees
 */
  if (lon_max < lon_min)
  { lon_max += 360;
    map_stradles_180 = TRUE;
  }
  else if (lon_min < -180)
  { lon_min += 360;
    lon_max += 360;
    map_stradles_180 = TRUE;
  }
  else if (lon_max > 180)
  { map_stradles_180 = TRUE;
  }
  else
  { map_stradles_180 = FALSE;
  }
 
/*
 *	open output file and reserve space for header
 */
  new_file = fopen(cc_filename, "w");
  if (NULL == new_file) {perror(new_filename); error_exit(usage); }
  ios = fwrite(dest->header, 1, CDB_FILE_HEADER_SIZE, new_file);
  if (very_verbose) fprintf(stderr,">>wrote %d bytes for header.\n",ios);
  if (ios != CDB_FILE_HEADER_SIZE)
  { fprintf(stderr,"cdb_edit: error writing header.\n");
    perror(new_filename);
    exit(ABORT);
  }

  for(ifiles = number_of_files; ifiles > 0; ifiles--, filenames++)
  {
    source = init_cdb(*filenames);
    
    if (source->header->segment_rank > dest->header->segment_rank)
      dest->header->segment_rank = source->header->segment_rank; 
           
/*
 *	  look at each segment and decide if we're
 *	  going to keep it or skip to the next one
 */   
    for (iseg = 0, reset_current_seg_cdb(source); 
	 iseg < source->seg_count; iseg++, next_segment_cdb(source))
    {
      if (source->segment->ilat_min*CDB_LAT_SCALE > lat_max) continue;
      if (source->segment->ilat_max*CDB_LAT_SCALE < lat_min) continue;
      
      if (map_stradles_180)
      { if (source->segment->ilon_min < 0)  
	  source->segment->ilon_min += 360/CDB_LON_SCALE;
	if (source->segment->ilon_max < 0)  
	  source->segment->ilon_max += 360/CDB_LON_SCALE;
      }
      
      if (source->segment->ilon_min*CDB_LON_SCALE > lon_max) continue;
      if (source->segment->ilon_max*CDB_LON_SCALE < lon_min) continue;
   
/*
 *    read and draw each segment that is within bounds
 */
      load_current_seg_data_cdb(source);
      copy_current_segment();
      
    }
  }
  
/*
 *	flush segment data buffer and finish
 */
  
  if (dest->npoints > 0) write_segment_data(dest->seg_count);
  
  finish_new_file();
  
  return;
}
    

/*------------------------------------------------------------------------
 *  finish_new_file - miscelaneous finishing touches on new .cdb file          
 *------------------------------------------------------------------------*/ 

void finish_new_file()
{
  int iseg, extent, ios;
  char command[MAX_STRING];

/*
 *	get maximum lat,lon extent 
 */

  for (iseg = 0; iseg < dest->seg_count; iseg++)
  { extent = dest->index[iseg].ilat_max - dest->index[iseg].ilat_min;
    if (dest->header->ilat_extent < extent) dest->header->ilat_extent = extent;
    extent = dest->index[iseg].ilon_max - dest->index[iseg].ilon_min;
    if (dest->header->ilon_extent < extent) dest->header->ilon_extent = extent;
  }

/*
 *	update header information
 */
  dest->header->code_number = CDB_MAGIC_NUMBER;
  strcpy(dest->header->text, label);
  dest->header->index_addr = ftell(new_file);
  dest->header->index_size = dest->seg_count * sizeof(cdb_index_entry);
  dest->header->index_order = (compare == parallels_min ? CDB_INDEX_LAT_MIN :
			       compare == meridians_min ? CDB_INDEX_LON_MIN :
			       compare == parallels_max ? CDB_INDEX_LAT_MAX :
			       compare == meridians_max ? CDB_INDEX_LON_MAX :
			       CDB_INDEX_SEG_ID);
  dest->header->ilat_max = nint(north/CDB_LAT_SCALE);
  dest->header->ilon_max = nint(east/CDB_LON_SCALE);
  dest->header->ilat_min = nint(south/CDB_LAT_SCALE);
  dest->header->ilon_min = nint(west/CDB_LON_SCALE);
  if (verbose) fprintf(stderr,">max segment size %d bytes.\n", 
		       dest->header->max_seg_size);

/*
 *	output index
 */
  cdb_byteswap_index(dest->index, dest->seg_count);
  ios = fwrite(dest->index, sizeof(cdb_index_entry), dest->seg_count, new_file);
  if (verbose) fprintf(stderr,">wrote %d index entries.\n",ios);
  if (ios != dest->seg_count)
  { fprintf(stderr,"cdb_edit: error writing index.\n");
    perror(new_filename);
    exit(ABORT);
  }

/*
 *	output header
 */
  cdb_byteswap_header(dest->header);
  fseek(new_file, 0L, SEEK_SET);
  ios = fwrite(dest->header, 1, CDB_FILE_HEADER_SIZE, new_file);
  if (verbose) fprintf(stderr,">wrote %d bytes of header.\n",ios);
  if (ios != CDB_FILE_HEADER_SIZE)
  { fprintf(stderr,"cdb_edit: error writing header.\n");
    perror(new_filename);
    exit(ABORT);
  }

  fflush(new_file);
  fclose(new_file);
  new_file = NULL;
  free_cdb(source);
  source = NULL;
  free_cdb(dest);
  dest = NULL;
  dest = new_cdb();
  dest->header = (cdb_file_header *) calloc(1, sizeof(cdb_file_header));

  max_index_entries = 0;
  max_data_points = 0;

}


/*------------------------------------------------------------------------
 * join_map - step through all segments, check for valid joins, 
 *            and join segments that are within 'join' kilometers.
 *------------------------------------------------------------------------*/ 

 void join_map()
{
  double current_start_lat, current_start_lon;
  double current_end_lat, current_end_lon;
  int ipoints, ios;
  cdb_edit_join_method join_method = JOIN_NO_METHOD;
  cdb_index_entry *best_candidate = NULL;
  
  int reversed_current_segment = 0, appended_candidate = 0;

  if (verbose) fprintf(stderr,"> Starting joins.\n");
  
  new_file = NULL;
  new_file = fopen(joined_filename, "w");
  if (NULL == new_file) {perror(new_filename); error_exit(usage); }
  ios = fwrite(dest->header, 1, CDB_FILE_HEADER_SIZE, new_file);
  if (very_verbose) fprintf(stderr,">>wrote %d bytes for header.\n",ios);
  if (ios != CDB_FILE_HEADER_SIZE)
  { fprintf(stderr,"cdb_edit: error writing header.\n");
    perror(new_filename);
    exit(ABORT);
  }
  
    
/*
 *     get rank
 */
    
  if (source->header->segment_rank > dest->header->segment_rank)
    dest->header->segment_rank = source->header->segment_rank;

/*
 *	step thru segment dictionary entries
 */

  if(verbose && !very_verbose)
    fprintf(stderr,"> new : appended\n");

  for(reset_current_seg_cdb(source); 
      source->segment < last_segment_cdb(source); 
      next_segment_cdb(source))
  {
    current_segment = source->segment;
    if(NULL == current_segment->addr)
      continue;

/*
 *   Get start and end of current segment
 */
    load_current_seg_data_cdb(source);

    current_start_lat = (double)source->segment->ilat0 * CDB_LAT_SCALE;
    current_start_lon = (double)source->segment->ilon0 * CDB_LON_SCALE;
    
    move_pu(current_start_lat, current_start_lon);
    
    current_end_lat = current_start_lat;
    current_end_lon = current_start_lon;
    
    for(ipoints = 0; ipoints < source->npoints;
	ipoints++, source->data_ptr++)
    {
      current_end_lat += (double) source->data_ptr->dlat * CDB_LAT_SCALE;
      current_end_lon += (double) source->data_ptr->dlon * CDB_LON_SCALE;
      draw_pd(current_end_lat, current_end_lon);
    }

/*
 *    Get start and end coordinates
 */ 
    forward_mapx(map, current_start_lat, current_start_lon, 
		 &current_x_start, &current_y_start);
    forward_mapx(map, current_end_lat, current_end_lon, 
		 &current_x_end, &current_y_end);
    
    if (very_verbose) fprintf(stderr,"> joining to old segment %d.\n",
			      source->segment->ID);
    else if(verbose) 
      {
	if(0 == dest->seg_count % 15)
	  fprintf(stderr,"\n\n> new : appended\n");
	fprintf(stderr,"\n> %d : ", dest->seg_count);
      }
/*
 *    check all later segments to find best candidate for joining (if any)
 */
    if (very_very_verbose) fprintf(stderr,">>> Searching candidates.\n");
    
    join_method = JOIN_NO_METHOD;
    best_candidate = NULL;

    best_candidate = find_best_candidate(&join_method);
   
/*
 *       Join the best candidate to the current segment
 */

    while(NULL != best_candidate)
    {
      set_current_seg_cdb(source, best_candidate);
      load_current_seg_data_cdb(source);
      if(verbose) fprintf(stderr,"%d ", source->segment->ID);
      
      switch(join_method)
      {
      case JOIN_START_TO_START:
	reverse_current_segment();             
	reversed_current_segment++;
	append_candidate(FALSE, &current_x_start, &current_y_start,
			 &current_x_end, &current_y_end);
	appended_candidate++;
	break;
      case JOIN_START_TO_END:
	reverse_current_segment();             reversed_current_segment++;
	append_candidate(TRUE, &current_x_start, &current_y_start,
			 &current_x_end, &current_y_end);
	appended_candidate++;
	break;
      case JOIN_END_TO_START:
	append_candidate(FALSE, &current_x_start, &current_y_start,
			 &current_x_end, &current_y_end);
	appended_candidate++;
	break;
      case JOIN_END_TO_END:
	append_candidate(TRUE, &current_x_start, &current_y_start,
			 &current_x_end, &current_y_end);
	appended_candidate++;
	break;     
      default:
	fprintf(stderr, "fatal error : join method not set.");
	exit(ABORT);
      }                                         /* end case */

/*
 *     try to find another candidate
 */
      
      set_current_seg_cdb(source, current_segment);
      join_method = JOIN_NO_METHOD;
      best_candidate = NULL;
      best_candidate = find_best_candidate(&join_method);
      
    }                                           /* end while loop */
    
    set_current_seg_cdb(source, current_segment);
    
  }                                          /* end current loop */
  
/*
 *	flush segment data buffer and finish
 */

  if(verbose)
  {
    fprintf(stderr, "\n> reversed current segment %d times.",
	    reversed_current_segment);
    fprintf(stderr, "\n> appended %d segments.", appended_candidate);
  }
  
  if (dest->npoints > 0) write_segment_data(dest->seg_count);
  
  finish_new_file();
  
  return;
}

   
/*------------------------------------------------------------------------
 * append_candidate - join candidate segment to current segment
 *
 *  input: reverse_candidate - if TRUE reverse candidate before appending. 
 *         current_x_start...current_y_end - pointers to (x,y) coordinates
 *            of the current segments start and end points.
 *
 * result: the candidate is appended to the current segment and the new
 *            start and end coordinates are computed.
 *------------------------------------------------------------------------*/ 

void append_candidate(int reverse_candidate, 
		      float *current_x_start, float *current_y_start, 
		      float *current_x_end, float *current_y_end)
{
  float temp_lat, temp_lon;
  float *lat = NULL;
  float *lon = NULL;
  int status, ipoints;

  ipoints = source->npoints + 1;
  lat = (float *) calloc(1, ipoints * sizeof(float));
  lon = (float *) calloc(1, ipoints * sizeof(float));

  if(NULL == lat || NULL == lon)
  {
    fprintf(stderr,"append_candidate: Unable to allocate %d points for segment %d\n", 
	    ipoints, source->segment->ID);
    return;
  }
  if (very_verbose) fprintf(stderr,">>appending candidate %d.\n", 
			    source->segment->ID);

  status = get_current_seg_cdb(source, lat, lon, source->npoints + 1);
  if(source->npoints + 1 != status)
  {
    fprintf(stderr,"append_candidate: Unable to get segment data for candidate segment %d\n", 
	    source->segment->ID);
    return;
  }

  if(reverse_candidate)
  {
    if (very_verbose) fprintf(stderr,">>Reversing candidate (segment %d).\n",
			 source->segment->ID);
  
    for(ipoints = source->npoints; ipoints >= 0; ipoints--)
    {
      draw_pd(lat[ipoints], lon[ipoints]);
    }
   
    forward_mapx(map, lat[0], lon[0], current_x_end, current_y_end);
    temp_lat = dest->index[dest->seg_count].ilat0 * CDB_LAT_SCALE;
    temp_lon = dest->index[dest->seg_count].ilon0 * CDB_LON_SCALE;
    forward_mapx(map, temp_lat, temp_lon, current_x_start, current_y_start);
  }

  else
  {
    for(ipoints = 0; ipoints <= source->npoints; ipoints++)
    {
      draw_pd(lat[ipoints], lon[ipoints]);
    }
   
    forward_mapx(map, lat[source->npoints], 
		 lon[source->npoints], current_x_end, current_y_end);
    temp_lat = dest->index[dest->seg_count].ilat0 * CDB_LAT_SCALE;
    temp_lon = dest->index[dest->seg_count].ilon0 * CDB_LON_SCALE;
    forward_mapx(map, temp_lat, temp_lon, current_x_start, current_y_start);
  }

  free(lat); free(lon);
  source->segment->addr = NULL;
}


/*---------------------------------------------------------------------------
 *  find_best_candidate - look at all segments after the current segment to find
 *                        best candidate for joining (if any).
 *
 *  input: join_method - pointer to cdb_edit_join_method
 *
 * output: best_candidate - cdb_index_entry of source segment that is the best
 *            candidate for joining to the current segment, or NULL if no good
 *            candidate is found.
 *-------------------------------------------------------------------------------*/

cdb_index_entry *find_best_candidate(cdb_edit_join_method *join_method)
{
  int ipoints;
  double temp_distance, distance = 100;
  double candidate_start_lat, candidate_start_lon;
  double candidate_end_lat, candidate_end_lon;
  float candidate_x_start, candidate_y_start;
  float candidate_x_end, candidate_y_end;
  float temp_x, temp_y;
  cdb_index_entry *best_candidate = NULL;
  cdb_index_entry *candidate_segment = NULL;
  
  if (very_very_verbose) fprintf(stderr,">>> Searching candidates.\n");
   
  candidate_segment = source->segment;
  best_candidate = NULL;

  for(next_segment_cdb(source);
      candidate_segment < last_segment_cdb(source); 
      next_segment_cdb(source))
  {                                        /* begin find best candidate loop */
    
    candidate_segment = source->segment;

/*
 *   Don't try to join a segment which has already been joined
 */  
  
    if(NULL == candidate_segment->addr)
    {
      if (very_very_verbose) 
	fprintf(stderr,">>>Segment %d has already been joined.\n",
		source->segment->ID);
      continue;
    }

/*
 *    Don't create a segment which crosses 180
 */  
    if(180 < fabs(current_segment->ilon_max - candidate_segment->ilon_min) * CDB_LON_SCALE)
      continue;

/*
 *  don't create a segment which is too long
 */
    load_current_seg_data_cdb(source);
    if(MAX_SEGMENT_POINTS < dest->npoints + source->npoints)
      continue;

/*
 *   Set up for fine checks
 */
 
    if (very_very_verbose) fprintf(stderr,"Checking candidate %d. \n", 
				   source->segment->ID);
    
    candidate_start_lat = (double)source->segment->ilat0 * CDB_LAT_SCALE;
    candidate_start_lon = (double)source->segment->ilon0 * CDB_LON_SCALE;
    
    if(!within_mapx(map, candidate_start_lat, candidate_start_lon)) continue;

    candidate_end_lat = candidate_start_lat;
    candidate_end_lon = candidate_start_lon;
    
    for(ipoints = 0; ipoints < source->npoints;
	ipoints++, source->data_ptr++)
    {
      candidate_end_lat += (double) source->data_ptr->dlat * CDB_LAT_SCALE;
      candidate_end_lon += (double) source->data_ptr->dlon * CDB_LON_SCALE;
    }
    
    forward_mapx(map, candidate_start_lat, candidate_start_lon, 
		 &candidate_x_start, &candidate_y_start);   
    forward_mapx(map, candidate_end_lat, candidate_end_lon, 
		 &candidate_x_end, &candidate_y_end);
    
/*
 *    See if this candidate is a good one.
 *    If so do fine checks to see if it is the best candidate so far.   
 */
    
    if(fabs(current_x_start - candidate_x_start) <= 2 &&
       fabs(current_y_start - candidate_y_start) <= 2 )
    {
      temp_x = current_x_start - candidate_x_start;
      temp_y = current_y_start - candidate_y_start;
      temp_distance = sqrt(SQ(temp_x) + SQ(temp_y));
      if(temp_distance < distance)
      {
	*join_method = JOIN_START_TO_START;
	distance = temp_distance;
	best_candidate = candidate_segment;
      }
    }
    
    if(fabs(current_x_start - candidate_x_end) <= 2 &&
       fabs(current_y_start - candidate_y_end) <= 2 )
    {
      temp_x = current_x_start - candidate_x_end;
      temp_y = current_y_start - candidate_y_end;
      temp_distance = sqrt(SQ(temp_x) + SQ(temp_y));
      if(temp_distance < distance)
      {
	*join_method = JOIN_START_TO_END;
	distance = temp_distance;
	best_candidate = candidate_segment;
      }
    }
    
    if(fabs(current_x_end - candidate_x_start) <= 2 &&
       fabs(current_y_end - candidate_y_start) <= 2 )
    {
      temp_x = current_x_end - candidate_x_start;
      temp_y = current_y_end - candidate_y_start;
      temp_distance = sqrt(SQ(temp_x) + SQ(temp_y));
      if(temp_distance < distance)
      {
	*join_method = JOIN_END_TO_START;
	distance = temp_distance;
	best_candidate = candidate_segment;
      }
    }
    
    if(fabs(current_x_end - candidate_x_end) <= 2 &&
       fabs(current_y_end - candidate_y_end) <= 2 )
    {
      temp_x = current_x_end - candidate_x_end;
      temp_y = current_y_end - candidate_y_end;
      temp_distance = sqrt(SQ(temp_x) + SQ(temp_y));
      if(temp_distance < distance)
      {
	*join_method = JOIN_END_TO_END;
	distance = temp_distance;
	best_candidate = candidate_segment;
      }
    }    
  }                          /** end find best candidate loop  **/
  return(best_candidate);  
}





