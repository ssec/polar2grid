/*======================================================================
 * grid_io - grid input/output
 * 
 * 3/18/98 K.Knowles knowles@kryos.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/
static const char grid_io_c_RCSID[]="$Header: /usr/local/src/maps/grid_io.c,v 1.7 1999/11/19 16:57:42 knowles Exp $";

#include "define.h"
#include "matrix.h"
#include "grid_io.h"

#ifndef MAX_ROW_BUFFER_SIZE
#define MAX_ROW_BUFFER_SIZE (2*1024*1024)
#endif

#ifdef DEBUG
static int x_rdpix=-1, y_rdpix=-1, test_rdpix=0;
#endif

static bool exchange_row_buffer(grid_io_class *this, int row);

/*------------------------------------------------------------------------
 * init_grid_io - creat and initialize new grid_io_class
 *
 *	input : width, height - dimensions
 *		datum_size - number of bytes per datum (1,2,4)
 *		signed_data - TRUE iff signed else unsigned data type
 *		real_data - TRUE iff floating point data else integer
 *		mode - input/output mode (see grid_io.h)
 *		filename - name of file to open
 *
 *	result: new grid_io_class pointer or NULL on failure
 *
 *------------------------------------------------------------------------*/
grid_io_class *init_grid_io(int width, int height, int datum_size, 
			    bool signed_data, bool real_data,
			    grid_io_mode mode, char *filename)
{ int nrows;
  grid_io_class *this;

  assert(1 == datum_size || 2 == datum_size 
	 || 4 == datum_size || 8 == datum_size);

/*
 *	initialize new structure
 */
  this = (grid_io_class *)calloc(1, sizeof(grid_io_class));
  if (!this) { perror("init_grid_io"); return NULL; }
  this->data = NULL;
  this->fp = NULL;

/*
 *	establish number of rows to buffer
 */
  nrows = MAX_ROW_BUFFER_SIZE/(datum_size*width);

  if (0 == nrows)
  { fprintf(stderr,"init_grid_io: can't even fit one row in memory!\n");
    fprintf(stderr,"  need %d bytes only have %d bytes.\n",
	   datum_size*width,  MAX_ROW_BUFFER_SIZE);
    close_grid_io(this);
    return NULL;
  }

  if (nrows > height) nrows = height;

  this->width = width;
  this->height = height;
  this->datum_size = datum_size;
  this->signed_data = signed_data;
  this->real_data = real_data;

/*
 *	open data file
 */
  this->io_mode = mode;

  switch (mode)
  { case grid_io_READ_ONLY:
      this->fp = fopen(filename, "rb");
      break;
    case grid_io_WRITE:
      this->fp = fopen(filename, "wb+");
      break;
    case grid_io_UPDATE:
      this->fp = fopen(filename, "rb+");
      if (!this->fp) this->fp = fopen(filename, "wb+");
      break;
    case grid_io_TEMPORARY:
      filename = tempnam(".", "");
      if (!filename) break;
      this->fp = fopen(filename, "w+");
      unlink(filename);
      free(filename);
      break;
    default: 
      assert(NEVER);
  }

  if (!this->fp) { perror(filename); close_grid_io(this); return NULL; }

  this->filename = strdup(filename);

/*
 *	allocate buffer
 */
  this->data = (byte1 **)matrix(nrows, width, datum_size, matrix_ZERO);
  if (!this->data)
  { perror("init_grid_io->data"); close_grid_io(this); return NULL; }

  this->row_buffer_increment = nrows;
  this->start_row = 0;
  this->final_row = nrows - 1;
  this->num_rows = nrows;

/*
 *	preload buffer
 */ 
  fread(this->data[0], this->datum_size,
	this->width*this->num_rows, this->fp);
  if (ferror(this->fp)) { perror(filename); close_grid_io(this); return NULL; }

  return this;
}

/*------------------------------------------------------------------------
 * close_grid_io - release resources allocated by init_grid_io
 *
 *	input : this - grid_io_class
 *
 *	note  : when using buffered output mode, close_grid_io must be
 *		called to flush last buffer of data
 *
 *------------------------------------------------------------------------*/
void close_grid_io(grid_io_class *this)
{
  if (!this) return;
  if (this->fp && this->data) exchange_row_buffer(this, this->start_row);
  if (this->data) free(this->data);
  if (this->fp) fclose(this->fp);
  if (this->filename) free(this->filename);
  free(this);
  return;
}

/*------------------------------------------------------------------------
 * fill_grid_io - initialize grid with fill value
 *
 *	input : this - grid_io_class
 *		fill_value - fill value
 *
 *	result: TRUE iff success
 *
 *------------------------------------------------------------------------*/
bool fill_grid_io(grid_io_class *this, double fill_value)
{ int col, row, sub;
  byte1 *pattern, *bufp;
  bool success;

/*
 *	make a sample row
 */
  pattern = (byte1 *)malloc(this->width*this->datum_size);
  if (!pattern) { perror("pattern buffer"); return FALSE; }
  bufp = pattern;

  if (!this->real_data) {
    switch (this->datum_size * (this->signed_data ? -1 : 1)) {
    case -1: 
      for (col = 0; col < this->width; col++) {
	*((int1 *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    case -2:
      for (col = 0; col < this->width; col++) {
	*((int2 *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    case -4:
      for (col = 0; col < this->width; col++) {
	*((int4 *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    case  1:
      for (col = 0; col < this->width; col++) {
	*((byte1 *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    case  2:
      for (col = 0; col < this->width; col++) {
	*((byte2 *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    case  4:
      for (col = 0; col < this->width; col++) {
	*((byte4 *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    default: assert(NEVER); /* should never execute */
    }
  }
  else {
    switch (this->datum_size) {
    case 4:
      for (col = 0; col < this->width; col++) {
	*((float *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    case 8:
      for (col = 0; col < this->width; col++) {
	*((double *)bufp) = fill_value;
	bufp += this->datum_size;
      }
      break;
    default: assert(NEVER); /* should never execute */
    }
  }

/*
 *	copy the pattern into each row of the grid
 */
  for (row = 0; row < this->height; row += this->row_buffer_increment)
  { success = exchange_row_buffer(this, row);
    if (!success) { free(pattern); return FALSE; }
    for (sub = 0; sub < this->num_rows; sub++)
    { memcpy(this->data[sub], pattern, this->width*this->datum_size);
    }
  }

  free(pattern);
  return TRUE;
}

/*------------------------------------------------------------------------
 * get_element_grid_io - return value from grid location
 *
 *	input : this - grid_io_class
 *		row, col - grid location
 *
 *	output: value - grid element
 *
 *	result: TRUE iff success
 *
 *------------------------------------------------------------------------*/
bool get_element_grid_io(grid_io_class *this, int row, int col, double *value)
{ bool success;
  byte1 *bufp;

#ifdef DEBUG
  if (col == x_rdpix && row == y_rdpix)
    ++test_rdpix;
#endif

/*
 *	bounds check
 */
  if (row < 0 || row >= this->height || 
      col < 0 || col >= this->width) return FALSE;

/*
 *	swap check
 */
  if (row < this->start_row || row > this->final_row)
  { success = exchange_row_buffer(this, row);
    if (!success) return FALSE;
  }

  assert(0 <= row - this->start_row && row - this->start_row < this->num_rows);

  bufp = this->data[row - this->start_row] + this->datum_size*col;

  if (!this->real_data) {
    switch (this->datum_size * (this->signed_data ? -1 : 1)) {
    case -1: *value = (double) *((int1 *)bufp); break;
    case -2: *value = (double) *((int2 *)bufp); break;
    case -4: *value = (double) *((int4 *)bufp); break;
    case  1: *value = (double) *((byte1 *)bufp); break;
    case  2: *value = (double) *((byte2 *)bufp); break;
    case  4: *value = (double) *((byte4 *)bufp); break;
    default: assert(NEVER); /* should never execute */
    }
  } 
  else {
    switch (this->datum_size) {
    case  4: *value = (double) *((float *)bufp); break;
    case  8: *value = (double) *((double *)bufp); break;
    default: assert(NEVER); /* should never execute */
    }
  }

  return TRUE;
}

/*------------------------------------------------------------------------
 * put_element_grid_io - store value in grid location
 *
 *	input : this - grid_io_class
 *		row, col - grid location
 *		value - grid element
 *
 *	result: TRUE iff success
 *
 *------------------------------------------------------------------------*/
bool put_element_grid_io(grid_io_class *this, int row, int col, double value)
{ bool success;
  byte1 *bufp;

/*
 *	bounds check
 */
  if (row < 0 || row >= this->height ||
      col < 0 || col >= this->width) return FALSE;

/*
 *	swap check
 */
  if (row < this->start_row || row > this->final_row)
  { success = exchange_row_buffer(this, row);
    if (!success) return FALSE;
  }

  assert(0 <= row - this->start_row && row - this->start_row < this->num_rows);

  bufp = this->data[row - this->start_row] + this->datum_size*col;

  if (!this->real_data) {
    switch (this->datum_size * (this->signed_data ? -1 : 1)) {
    case -1: *((int1 *)bufp) = value; break;
    case -2: *((int2 *)bufp) = value; break;
    case -4: *((int4 *)bufp) = value; break;
    case  1: *((byte1 *)bufp) = value; break;
    case  2: *((byte2 *)bufp) = value; break;
    case  4: *((byte4 *)bufp) = value; break;
    default: assert(NEVER); /* should never execute */
    }
  }
  else {
    switch (this->datum_size) {
    case  4: *((float *)bufp) = value; break;
    case  8: *((double *)bufp) = value; break;
    default: assert(NEVER); /* should never execute */
    }
  }


  return TRUE;
}

/*------------------------------------------------------------------------
 * exchange_row_buffer - update current grid data buffer
 *
 *	input : this - grid_io_class
 *		row - new row to be within buffer
 *
 *	effect: this->data - contains new row
 *		this->start_row and final_row are updated
 *		depending on mode data is written to file
 *
 *------------------------------------------------------------------------*/
static bool exchange_row_buffer(grid_io_class *this, int row)
{ long offset;

  assert(0 <= row && row < this->height);

/*
 *	write out current buffer (if appropriate)
 */
  if (grid_io_READ_ONLY != this->io_mode)
  { offset = this->datum_size * this->width * this->start_row;
    fseek(this->fp, offset, SEEK_SET);

    fwrite(this->data[0], this->datum_size, 
	   this->width*this->num_rows, this->fp);
    if (ferror(this->fp)) { perror(this->filename); return FALSE;}
  }

  if (this->start_row <= row && row <= this->final_row) return TRUE;

/*
 *	adjust row offset to whole buffer increment
 */
  row = (row / this->row_buffer_increment) * this->row_buffer_increment;

/*
 *	don't let the row buffer run off the end of the grid
 */
  this->num_rows = this->height - row;
  if (this->num_rows > this->row_buffer_increment)
  { this->num_rows = this->row_buffer_increment;
  }

/*
 *	read new buffer
 */
  offset = this->datum_size * this->width * row;
  fseek(this->fp, offset, SEEK_SET);

  fread(this->data[0], this->datum_size,
	this->width*this->num_rows, this->fp);
  if (ferror(this->fp)) { perror(this->filename); return FALSE; }

  this->start_row = row;
  this->final_row = row + this->num_rows - 1;
  assert(this->final_row < this->height);

  return TRUE;
}
