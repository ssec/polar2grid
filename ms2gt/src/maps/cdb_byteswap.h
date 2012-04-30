/*------------------------------------------------------------------------
 * cdb_byteswap_... - in situ byteswap routines
 *
 *	ensure correct byte order for all data in memory
 *	disk data is stored with most significant byte first
 *	for machines which require least significant byte first
 *	(Intel, VAX) compile with -DLSB1ST
 *
 * 8-Jul-1992 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *------------------------------------------------------------------------*/
#ifndef LSB1ST
#define NO_SWAP
#endif
#include "byteswap.h"

/*
 *	byteswap cdb file header if necessary
 */
static void cdb_byteswap_header(cdb_file_header *header)
{
#ifdef LSB1ST
  SWAP4_IS(&(header->code_number));
  SWAP4_IS(&(header->index_addr));
  SWAP4_IS(&(header->index_size));
  SWAP4_IS(&(header->max_seg_size));
  SWAP4_IS(&(header->segment_rank));
  SWAP4_IS(&(header->index_order));
  SWAP4_IS(&(header->ilat_max));
  SWAP4_IS(&(header->ilon_max));
  SWAP4_IS(&(header->ilat_min));
  SWAP4_IS(&(header->ilon_min));
  SWAP4_IS(&(header->ilat_extent));
  SWAP4_IS(&(header->ilon_extent));
#endif
}

/*
 *	byte swap cdb file index if necessary
 */
static void cdb_byteswap_index(cdb_index_entry *index, int seg_count)
{
#ifdef LSB1ST
  register int iseg;
  cdb_index_entry *entry;

  for(iseg = 0, entry = index; iseg < seg_count; iseg++, entry++)
  { SWAP4_IS(&(entry->ID));
    SWAP4_IS(&(entry->ilat0));
    SWAP4_IS(&(entry->ilon0));
    SWAP4_IS(&(entry->ilat_max));
    SWAP4_IS(&(entry->ilon_max));
    SWAP4_IS(&(entry->ilat_min));
    SWAP4_IS(&(entry->ilon_min));
    SWAP4_IS(&(entry->addr));
    SWAP4_IS(&(entry->size));
  }
#endif
}
/*
 *	byte swap cdb segment data buffer if necessary
 */
static void cdb_byteswap_data_buffer(cdb_seg_data *buffer, int npts)
{
#ifdef LSB1ST
  register int ipt;

  for (ipt=0; ipt < npts; ipt++)
  { SWAP2_IS(&(buffer[ipt].dlat));
    SWAP2_IS(&(buffer[ipt].dlon));
  }
#endif
}
