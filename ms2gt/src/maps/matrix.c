/*========================================================================
 * matrix - allocate 2-D matrix
 *
 * 13-Jan-1993 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "define.h"
#include "matrix.h"

static const char matrix_c_rcsid[] = "$Header: /usr/local/src/maps/matrix.c,v 1.7 1996/03/07 23:19:40 knowles Exp $";

/*------------------------------------------------------------------------
 * matrix - allocate 2-D matrix
 *
 *	input : rows - number of rows
 *		cols - number of columns
 *		bytes - number of bytes per entry
 *		zero - if set then zero fill entries
 *
 *	result: pointer to column of pointers to rows
 *		i.e. matrix is accessed as matrix_ptr[row][col]
 *		data storage block is contiguous starting at matrix_ptr[0]
 *
 *	note: Resources can be de-allocated using the normal free routine.
 *	      Matrix entries will be suitably aligned for all primitive 
 *	      types. It is up to the caller to ensure that structures are
 *	      properly aligned, i.e. bytes should be a multiple of the
 *	      sizeof the first member of the struct. 
 *
 *------------------------------------------------------------------------*/
void **matrix(int rows, int cols, int bytes, int zero)
{
  register int irow;
  void **matrix_ptr;
  char *block_ptr, **row_ptr;
  size_t row_size, row_ptr_size;

/*
 *	allocate row pointer storage followed by data storage
 *	make sure the data storage is suitably alligned
 */
  row_size = cols*bytes;
  row_ptr_size = rows * sizeof(void *);
  row_ptr_size = ceil((double)row_ptr_size/bytes) * bytes;
  block_ptr = (char *)malloc(row_ptr_size + rows*row_size);
  if (NULL == block_ptr) { perror("matrix"); return(NULL); }

/*
 *	assign row pointers
 */
  matrix_ptr = (void **)block_ptr;
  row_ptr = (char **)matrix_ptr;
  block_ptr += row_ptr_size;
  for (irow = 0; irow < rows; irow++)
  { *row_ptr = block_ptr;
    block_ptr += row_size;
    ++row_ptr;
  }

/*
 *	clear data area
 */
  if (zero) memset(matrix_ptr[0], 0, rows*row_size);

  return(matrix_ptr);
}
