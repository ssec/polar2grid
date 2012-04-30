/*========================================================================
 * wdbtocdb - WDB2 (or WVS) to cdb file conversion
 *
 *	note:	most significant byte first is assumed, on
 *		least significant byte first machines compile
 *		with -DLSB1ST
 *
 *========================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include "define.h"
#include "mapx.h"
#include "cdb.h"
#include "cdb_byteswap.h"

static const char wdbtocdb_c_rcsid[] = "$Header: /usr/local/src/maps/wdbtocdb.c,v 1.2 1993/11/11 17:00:40 knowles Exp $";

/*------------------------------------------------------------------------
 * globals
 *------------------------------------------------------------------------*/
static char *cdb_filename;
static FILE *cdb_file;
static cdb_file_header header;
static cdb_index_entry *seg_index = NULL;
static cdb_seg_data *data = NULL;
static int seg_count = 0;
static int npoints = 0;
static int max_seg_size = 0;
static int ilat_extent = 0, ilon_extent = 0;
static int max_index_entries = 0;
static int max_data_points = 0;
static int verbose = FALSE;
static int very_verbose = FALSE;
static int very_very_verbose = FALSE;

#define MAX_RANKS 64

/*------------------------------------------------------------------------
 * function prototypes
 *------------------------------------------------------------------------*/
int move_pu(float, float);
int draw_pd(float, float);
int write_segment_data(int);

/*------------------------------------------------------------------------
 * usage
 *------------------------------------------------------------------------*/
#define usage "\n"\
"usage: wdbtocdb [-tdnsewpmlv] output_filename source_filename ...\n"\
"\n"\
" input : World Data Bank 2 and/or World Vector Shoreline sources\n"\
"\n"\
" output: cdb formatted file\n"\
"\n"\
" option: t thin - use only one out of every thin strokes (default 1)\n"\
"         d detail - only use segments with rank <= detail (default 1)\n"\
"         r ranks - specify rank vector (e.g. '10001' = ranks 1 and 5)\n"\
"         n north - northern bound (default 90)\n"\
"         s south - southern bound (default -90)\n"\
"         e east - eastern bound (default 180)\n"\
"         w west - western bound (default -180)\n"\
"         h label - file header text (max 31 chars)\n"\
"         v - verbose diagnostic messages (may be repeated)\n"\
"\n"

/*------------------------------------------------------------------------
 * wdbtocdb - create coastline database from binary WDB2 and/or WVS files
 *
 *	input : World Data Bank 2 and/or World Vector Shoreline sources
 *
 *	output: "cdb" formatted file
 *
 *------------------------------------------------------------------------*/
main(int argc, char *argv[])
{
  register int i, ios, extent;
  char *option;
  int detail = 1;
  float north = 90, south = -90, east = 180, west = -180;
  char thin = 1, rank[MAX_RANKS+1], rank_string[MAX_STRING] = "";
  char label[MAX_STRING] = "wdbtocdb";

/*
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'd':
	  argc--; argv++;
	  if (argc <= 0 || sscanf(*argv,"%d",&detail) != 1) error_exit(usage);
	  break;
        case 'r':
	  argc--; argv++;
	  strncpy(rank_string, *argv, MAX_STRING);
	  break;
        case 't':
	  argc--; argv++;
	  if (argc <= 0 || sscanf(*argv,"%d",&thin) != 1) error_exit(usage);
	  break;
        case 'n':
	  argc--; argv++;
	  if (argc <= 0 || sscanf(*argv,"%f",&north) != 1) error_exit(usage);
	  break;
        case 's':
	  argc--; argv++;
	  if (argc <= 0 || sscanf(*argv,"%f",&south) != 1) error_exit(usage);
	  break;
        case 'e':
	  argc--; argv++;
	  if (argc <= 0 || sscanf(*argv,"%f",&east) != 1) error_exit(usage);
	  break;
        case 'w':
	  argc--; argv++;
	  if (argc <= 0 || sscanf(*argv,"%f",&west) != 1) error_exit(usage);
	  break;
        case 'h':
	  argc--; argv++;
	  strncpy(label, *argv, MAX_STRING);
	  break;
        case 'v':
	  if (very_verbose) very_very_verbose = TRUE;
	  if (verbose) very_verbose = TRUE;
	  verbose = TRUE;
	  break;
	default:
	  fprintf(stderr, "invalid option %c\n", *option);
	  error_exit(usage);
      }
    }
  }

/*
 *	fill rank vector
 */
  for(i = 0; i <= MAX_RANKS; i++) 
  { rank[i] = (i <= detail ? 1 : 0);
  }
  if (*rank_string)
  { for (i = 0; i < strlen(rank_string) && i < MAX_RANKS; i++)
    { if ('0' == rank_string[i]) rank[i+1] = 0;
    }
  }

/*
 *	get command line arguments
 */
  if (argc < 2) error_exit(usage);
  cdb_filename = *argv;
  argc--; argv++;

  if (verbose) fprintf(stderr,">filename: %s, thin: %d, detail: %d, %s\n",
		       cdb_filename, thin, detail, label);

/*
 *	open output file and reserve space for header
 */
  cdb_file = fopen(cdb_filename, "w");
  if (cdb_file == NULL) { perror(cdb_filename); error_exit(usage); }
  ios = fwrite(&header, 1, CDB_FILE_HEADER_SIZE, cdb_file);
  if (very_verbose) fprintf(stderr,">>wrote %d bytes for header.\n",ios);
  if (ios != CDB_FILE_HEADER_SIZE)
  { fprintf(stderr,"wdbtocdb: error writing header.\n");
    perror(cdb_filename);
    exit(ABORT);
  }

/*
 *	record segment data and create index
 */
  for (; argc > 0; argc--, argv++)
  { if (verbose) fprintf(stderr,">processing %s...\n", *argv);
    wdbplt(*argv, south, 0., north, 0., west, 0., east, 0., 0., rank, thin);
  }

/*
 *	flush segment data buffer
 */
  if (npoints > 0) write_segment_data(seg_count-1);

/*
 *	get maximum lat,lon extent
 */
  if (verbose) fprintf(stderr,"> %d index entries...\n",seg_count);
  for (i=0; i < seg_count; i++)
  { extent = seg_index[i].ilat_max - seg_index[i].ilat_min;
    if (ilat_extent < extent) ilat_extent = extent;
    extent = seg_index[i].ilon_max - seg_index[i].ilon_min;
    if (ilon_extent < extent) ilon_extent = extent;
  }

/*
 *	update header information
 */
  header.code_number = CDB_MAGIC_NUMBER;
  header.max_seg_size = max_seg_size;
  header.segment_rank = detail;
  strncpy(header.text, label, 31);
  header.index_addr = ftell(cdb_file);
  header.index_size = seg_count*sizeof(cdb_index_entry);
  header.index_order = CDB_INDEX_SEG_ID;
  header.ilat_max = nint(north/CDB_LAT_SCALE);
  header.ilon_max = nint(east/CDB_LON_SCALE);
  header.ilat_min = nint(south/CDB_LAT_SCALE);
  header.ilon_min = nint(west/CDB_LON_SCALE);
  header.ilat_extent = ilat_extent;
  header.ilon_extent = ilon_extent;
  if (verbose) fprintf(stderr,">max segment size %d bytes.\n", max_seg_size);

/*
 *	output index
 */
  cdb_byteswap_index(seg_index, seg_count);
  ios = fwrite(seg_index, sizeof(cdb_index_entry), seg_count, cdb_file);
  if (verbose) fprintf(stderr,">wrote %d index entries.\n",ios);
  if (ios != seg_count)
  { fprintf(stderr,"wdbtocdb: error writing index.\n");
    perror(cdb_filename);
    exit(ABORT);
  }

/*
 *	output header
 */
  cdb_byteswap_header(&header);
  fseek(cdb_file, 0L, SEEK_SET);
  ios = fwrite(&header, 1, CDB_FILE_HEADER_SIZE, cdb_file);
  if (verbose) fprintf(stderr,">wrote %d bytes of header.\n",ios);
  if (ios != CDB_FILE_HEADER_SIZE)
  { fprintf(stderr,"wdbtocdb: error writing header.\n");
    perror(cdb_filename);
    exit(ABORT);
  }


  fclose(cdb_file);
}

/*------------------------------------------------------------------------
 * move_pu - first point of next segment
 *------------------------------------------------------------------------*/
int move_pu(float lat, float lon)
{
  float nlon;

/*
 *	write current segment
 */
  if (npoints > 0) write_segment_data(seg_count-1);

/*
 *	make sure index is big enough
 */
  if (seg_count >= max_index_entries)
  { max_index_entries += 1000;
    seg_index = (cdb_index_entry *)
      realloc(seg_index,sizeof(cdb_index_entry)*max_index_entries);
    assert(seg_index != NULL);
    if (verbose) fprintf(stderr,">allocating %d index entries.\n",
			 max_index_entries);
  }

/*
 *	start a new segment
 */
  seg_index[seg_count].ID = seg_count;
  seg_index[seg_count].ilat0 = nint(lat/CDB_LAT_SCALE);
  nlon = lon;
  NORMALIZE(nlon);
  seg_index[seg_count].ilon0 = nint(nlon/CDB_LON_SCALE);
  seg_index[seg_count].ilat_max = seg_index[seg_count].ilat0;
  seg_index[seg_count].ilon_max = seg_index[seg_count].ilon0;
  seg_index[seg_count].ilat_min = seg_index[seg_count].ilat0;
  seg_index[seg_count].ilon_min = seg_index[seg_count].ilon0;
  ++seg_count;
  npoints = 0;

}

/*------------------------------------------------------------------------
 * draw_pd - add a point to the current segment
 *------------------------------------------------------------------------*/
int draw_pd(float lat, float lon)
{
  register int split = 0, ilat, ilon;
  static float lat1,lon1;
  auto float lat2,lon2, lat3,lon3;

/*
 *	make sure segment is big enough
 */
  if (npoints >= max_data_points)
  { max_data_points += 1000;
    data = (cdb_seg_data *)
      realloc(data,sizeof(cdb_seg_data)*max_data_points);
    assert(data != NULL);
    if (verbose) fprintf(stderr,">allocating %d data points.\n",
			 max_data_points);
  }

/*
 *	check for start of new segment
 */
  if (npoints == 0)
  { lat1 = seg_index[seg_count-1].ilat0 * CDB_LAT_SCALE;
    lon1 = seg_index[seg_count-1].ilon0 * CDB_LON_SCALE;
    if (very_verbose)fprintf(stderr,">>new segment: %f %f.\n",lat1,lon1);
  }

/*
 *	split segments which cross +/-180
 *
 *	split =  0 => don't split
 *	      = +1 => split left to right
 *	      = -1 => split right to left  
 */
  lat3 = lat;
  lon3 = lon;
  NORMALIZE(lon3);
  if (lon1 > 90 && lon3 < -90)
    split = 1;
  else if (lon1 < -90 && lon3 > 90)
    split = -1;

  if (split)
  { while (lon1 < 0) lon1 += 360;
    while (lon3 < 0) lon3 += 360;
    lon2 = 180;
    lat2 = (lon2-lon1) * (lat3-lat1)/(lon3-lon1) + lat1;
    NORMALIZE(lon1);
    NORMALIZE(lon3);
    if (very_verbose)fprintf(stderr,">>split %d %f %f, %f %f, %f %f\n",
				  split, lat1,lon1, lat2,lon2, lat3,lon3);
    lon2 = split*180;
    draw_pd(lat2, lon2);
    lon2 = -split*180;
    move_pu(lat2, lon2);
    draw_pd(lat3, lon3);
  }


/*
 *	add point lat3,lon3 to segment
 */
  else
  { ilat = nint(lat3/CDB_LAT_SCALE);
    ilon = nint(lon3/CDB_LON_SCALE);
    data[npoints].dlat = nint((lat3 - lat1)/CDB_LAT_SCALE);
    data[npoints].dlon = nint((lon3 - lon1)/CDB_LON_SCALE);
    lat1 = lat3;
    lon1 = lon3;
    ++npoints;
    if (max_seg_size < npoints*sizeof(cdb_seg_data))
      max_seg_size = npoints*sizeof(cdb_seg_data);
    if (very_very_verbose)fprintf(stderr,">>>add point %f %f.\n",lat3,lon3);

/*
 *	update index entry
 */
    if (seg_index[seg_count-1].ilat_max < ilat)
      seg_index[seg_count-1].ilat_max = ilat;
    if (seg_index[seg_count-1].ilon_max < ilon)
      seg_index[seg_count-1].ilon_max = ilon;
    if (seg_index[seg_count-1].ilat_min > ilat)
      seg_index[seg_count-1].ilat_min = ilat;
    if (seg_index[seg_count-1].ilon_min > ilon)
      seg_index[seg_count-1].ilon_min = ilon;
  }
}

/*------------------------------------------------------------------------
 * curve - called by wdbplt to plot each segment
 *------------------------------------------------------------------------*/
void curve(float *lon, float *lat, short count, char color)
{ register int ipt;

  if (count <= 0) return;

  if (count > 1)
  { move_pu(lat[0], lon[0]);

    for (ipt = 1; ipt < count; ipt++)
    { draw_pd(lat[ipt], lon[ipt]);
    }
  }
  else
  { move_pu(lat[0], lon[0]);
    draw_pd(lat[0], lon[0]);
  }
}

/*------------------------------------------------------------------------
 * write_segment_data - and get segment address and size
 *------------------------------------------------------------------------*/
int write_segment_data(int seg)
{
  register int ios;

  seg_index[seg].addr = ftell(cdb_file);
  seg_index[seg].size = npoints*sizeof(cdb_seg_data);
  cdb_byteswap_data_buffer(data, npoints);
  ios = fwrite(data, sizeof(cdb_seg_data), npoints, cdb_file);
  if (very_verbose) fprintf(stderr,">>wrote %d points of segment %d.\n",
	 ios, seg_index[seg].ID);
  if (ios != npoints)
  { fprintf(stderr,"wdbtocdb: error writing data segment %d.\n",
     seg_index[seg].ID);
    perror(cdb_filename);
    exit(ABORT);
  }
}
