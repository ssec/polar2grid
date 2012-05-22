/*======================================================================
 * extract_region.c - extract a region from a grid file
 *
 * 23-Jul-1998 T.Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/

static const char extract_region_c_rcsid[] = "$Header: /home/haran/navdir/src/utils/extract_region.c,v 1.10 2007/05/02 21:46:55 tharan Exp $";

#include <stdio.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include "define.h"

static FILE *verbose, *very_verbose, *very_very_verbose;

#define usage \
"$Revision: 1.10 $\n" \
"usage: extract_region [-v] [-b] [-s scale] [-f] [-c cells_per_col]\n"\
"          bytes_per_cell cols_in rows_in\n"\
"          col_start row_start cols_out rows_out\n"\
"          file_in\n"\
"          file_out\n"\
"  input : bytes_per_cell - the number of bytes per single grid location.\n"\
"                           Must be 1, 2, 4, or 8.\n"\
"          cols_in - the number of columns in the input file\n"\
"          rows_in - the number of rows in the input file\n"\
"          col_start - the zero-based column number of the first column\n"\
"                      in the region\n"\
"          row_start - the zero-based row number of the first row\n"\
"                      in the region\n"\
"          cols_out - the number of columns in the region\n"\
"          rows_out - the number of rows in the region\n"\
"          file_in  - the input grid filename\n"\
"  output: file_out - the output grid filename\n"\
"  option: v - verbose (may be repeated)\n"\
"          b - byte swap the data\n"\
"          s scale - multiply the (byte-swapped) data by scale.\n"\
"                    The default value of scale is 1.0.\n"\
"          f - treat the (byte-swapped) data as\n"\
"              floating-point for the purposes of scaling,\n"\
"              so bytes_per_cell must be 4 or 8.\n"\
"          c cells_per_col - number of cells in each col.\n"\
"                            The default value of cells_per_col is 1.\n"

static void DisplayUsage(void)
{
  error_exit(usage);
}

static void DisplayInvalidParameter(char *param)
{
  fprintf(stderr, "extract_region: Parameter %s is invalid.\n", param);
  DisplayUsage();
}

static void swap_buffer(byte1 *buffer,
                        int cols, int cells_per_col, int bytes_per_cell)
{
  int i;
  int j;
  int cells_per_record;
  byte1 *in;
  byte1 *out;
  byte1 *tmp;
  byte1 temp[8];

  cells_per_record = cols * cells_per_col;
  in = out = buffer;
  for (i = 0; i < cells_per_record; i++) {
    memcpy(temp, in, bytes_per_cell);
    tmp = temp + bytes_per_cell - 1;
    for (j = 0; j < bytes_per_cell; j++) {
      *out++ = *tmp--;
    }
    in += bytes_per_cell;
  }
}

static void scale_buffer(byte1 *buffer,
                         int cols, int cells_per_col, int bytes_per_cell,
                         double scale, bool float_scale)
{
  int i;
  int cells_per_record;
  byte1 temp[8];
  byte1 *buf;

  cells_per_record = cols * cells_per_col;
  buf = buffer;
  for (i = 0; i < cells_per_record; i++) {
    memcpy(temp, buf, bytes_per_cell);
    if (float_scale) {
      if (bytes_per_cell == 4)
        *((float *)buf) = (float)(*((float *)buf) * scale);
      else
        *((double *)buf) = (double)(*((double *)buf) * scale);
    } else {
      if (bytes_per_cell == 1)
        *((byte1 *)buf) = (byte1)(*((byte1 *)buf) * scale);
      else if (bytes_per_cell == 2)
        *((byte2 *)buf) = (byte2)(*((byte2 *)buf) * scale);
      else if (bytes_per_cell == 4)
        *((byte4 *)buf) = (byte4)(*((byte4 *)buf) * scale);
    }
    buf += bytes_per_cell;
  }
}

/*------------------------------------------------------------------------
 * main - extract_region
 *
 *        input : argc, argv - command line args
 *
 *      result: EXIT_SUCCESS or EXIT_FAILURE
 *
 *      effect: Input consists of grid file file_in whose dimensions are
 *              defined by bytes_per_cell, cols_in, and rows_in.
 *              Output consists of raster file file_out consisting of a region
 *              of file_in defined by col_start, row_start, cols_out, and
 *              rows_out and having the same number of bytes_per_cell as
 *              file_in.
 *------------------------------------------------------------------------*/
int main(int argc, char *argv[])
{
  char *option;
  int bytes_per_cell, cols_in, rows_in;
  int col_start, row_start, cols_out, rows_out;
  char *file_in;
  char *file_out;

  byte1 *buf_in  = NULL;
  byte1 *buf_out = NULL;
  byte1 *buf_temp = NULL;
  int fd_in  = -1;
  int fd_out = -1;
  bool there_were_errors;
  int row;
  int bytes_per_row_in, bytes_per_row_out;
  int last_row_in_region;
  bool byte_swap;
  double scale;
  bool float_scale;
  int cells_per_col;

  /*
   *     set defaults
   */
  verbose = very_verbose = NULL;
  byte_swap = FALSE;
  scale = 1.0;
  float_scale = FALSE;
  cells_per_col = 1;
  there_were_errors = FALSE;

  /*
   *     get command line options
   */
  while (--argc > 0 && (*++argv)[0] == '-') {
    for (option = argv[0]+1; *option != '\0'; option++) {
      switch (*option) {
      case 'v':
        if (very_verbose)
          very_very_verbose = stdout;
        if (verbose)
          very_verbose = stdout;
        verbose = stdout;
        break;
      case 'V':
        fprintf(stderr,"%s\n", extract_region_c_rcsid);
        break;
      case 'b':
        byte_swap = TRUE;
        break;
      case 's':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("scale");
        if (sscanf(*argv, "%lf", &scale) != 1)
          DisplayInvalidParameter("scale");
        break;
      case 'f':
        float_scale = TRUE;
        break;
      case 'c':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("cells_per_col");
        if (sscanf(*argv, "%d", &cells_per_col) != 1)
          DisplayInvalidParameter("cells_per_col");
        break;
      default:
        fprintf(stderr, "extract_region: invalid option %c\n", *option);
        error_exit(usage);
      }
    }
  }

  /*
   *     get command line args
   */
  if (argc != 9)
    error_exit(usage);
  if (sscanf(*argv++, "%d", &bytes_per_cell) != 1) {
    fprintf(stderr, "invalid bytes_per_cell value %s\n", *argv);
    error_exit(usage);
  }
  if (sscanf(*argv++, "%d", &cols_in) != 1) {
    fprintf(stderr, "invalid cols_in value %s\n", *argv);
    error_exit(usage);
  }
  if (sscanf(*argv++, "%d", &rows_in) != 1) {
    fprintf(stderr, "invalid rows_in value %s\n", *argv);
    error_exit(usage);
  }
  if (sscanf(*argv++, "%d", &col_start) != 1) {
    fprintf(stderr, "invalid col_start value %s\n", *argv);
    error_exit(usage);
  }
  if (sscanf(*argv++, "%d", &row_start) != 1) {
    fprintf(stderr, "invalid row_start value %s\n", *argv);
    error_exit(usage);
  }
  if (sscanf(*argv++, "%d", &cols_out) != 1) {
    fprintf(stderr, "invalid cols_out value %s\n", *argv);
    error_exit(usage);
  }
  if (sscanf(*argv++, "%d", &rows_out) != 1) {
    fprintf(stderr, "invalid rows_out value %s\n", *argv);
    error_exit(usage);
  }
  file_in  = *argv++;
  file_out = *argv++;

  /*
   *     display command line parameters
   */
  if (verbose) {
    fprintf(stderr, "extract_region:    %s\n", extract_region_c_rcsid);
    fprintf(stderr, "  byte_swap:       %d\n", byte_swap);
    fprintf(stderr, "  scale:           %lf\n", scale);
    fprintf(stderr, "  float_scale:     %d\n", float_scale);
    fprintf(stderr, "  cells_per_col:   %d\n", cells_per_col);
    fprintf(stderr, "  bytes_per_cell:  %d\n", bytes_per_cell);
    fprintf(stderr, "  cols_in:         %d\n", cols_in);
    fprintf(stderr, "  rows_in:         %d\n", rows_in);
    fprintf(stderr, "  col_start:       %d\n", col_start);
    fprintf(stderr, "  row_start:       %d\n", row_start);
    fprintf(stderr, "  cols_out:        %d\n", cols_out);
    fprintf(stderr, "  rows_out:        %d\n", rows_out);
    fprintf(stderr, "  file_in:         %s\n", file_in);
    fprintf(stderr, "  file_out:        %s\n", file_out);
  }

  /*
   *     use loop even though it's one time through for easy error exit
   */
  for(;;) {

    /*
     *     check for a valid region
     */
    if (col_start + cols_out > cols_in) {
      fprintf(stderr,
              "extract_region: col_start + cols_out must be <= cols_in\n");
      there_were_errors = TRUE;
    }
    if (row_start + rows_out > rows_in) {
      fprintf(stderr,
              "extract_region: row_start + rows_out must be <= rows_in\n");
      there_were_errors = TRUE;
    }
    if (bytes_per_cell != 1 && bytes_per_cell != 2 &&
        bytes_per_cell != 4 && bytes_per_cell != 8) {
      fprintf(stderr,
              "extract_region: bytes_per_cell must be 1, 2, 4, or 8\n");
      there_were_errors = TRUE;
    }
    if (float_scale == TRUE && scale != 1.0 &&
        bytes_per_cell != 4 && bytes_per_cell != 8) {
      fprintf(stderr,
              "extract_region: bytes_per_cell must be 4 or 8 if -f is specified and scale != 1.0\n");
      there_were_errors = TRUE;
    }
    if (there_were_errors)
      break;

    /*
     *    initialize buffer size for i/o
     */
    bytes_per_row_in  = cols_in  * cells_per_col * bytes_per_cell;
    bytes_per_row_out = cols_out * cells_per_col * bytes_per_cell;
    last_row_in_region = row_start + rows_out - 1;

    /*
     *    allocate a buffer for each input and output grid file.
     */
    if (very_verbose)
      fprintf(stderr, "extract_region: allocating buffers\n");

    buf_in = (byte1 *)calloc(bytes_per_row_in, sizeof(byte1));
    if (!buf_in) {
      fprintf(stderr, "error allocating %d bytes for file_in buffer\n",
              bytes_per_row_in);
      perror("extract_region");
      there_were_errors = TRUE;
      break;
    }
    buf_out = buf_in + col_start * cells_per_col * bytes_per_cell;

    /*
     *     open input file
     */
    if (very_verbose)
      fprintf(stderr, "extract_region: opening input file\n");

    fd_in = open(file_in, O_RDONLY);
    if (fd_in < 0) {
      fprintf(stderr, "error opening %s\n", file_in);
      perror("extract_region");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open output file
     */
    if (very_verbose)
      fprintf(stderr, "extract_region: opening output file\n");

    fd_out = creat(file_out, 0644);
    if (fd_out < 0) {
      fprintf(stderr, "error opening %s\n", file_out);
      perror("extract_region");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     seek to first row in region of input file
     */
    if (very_verbose)
      fprintf(stderr, "extract_region: seeking to first byte in region\n");

    if (lseek(fd_in,
              (off_t)row_start * bytes_per_row_in,
              SEEK_SET) == -1) {
      fprintf(stderr, "error seeking to first row in region of %s\n", file_in);
      perror("extract_region");
      there_were_errors = TRUE;
      break;
    }

    /*
     *    for each row
     */
    for (row = row_start; row <= last_row_in_region; row++) {
      if (very_very_verbose)
        fprintf(stderr, "reading row %d\n", row);
      if (read(fd_in, buf_in,
               bytes_per_row_in) != bytes_per_row_in) {
        fprintf(stderr, "error reading %s\n", file_in);
        perror("extract_region");
        there_were_errors = TRUE;
        break;
      }
      if (byte_swap)
        swap_buffer(buf_out, cols_out, cells_per_col, bytes_per_cell);
      if (scale != 1.0)
        scale_buffer(buf_out, cols_out, cells_per_col, bytes_per_cell,
                     scale, float_scale);
      if (very_very_verbose)
        fprintf(stderr, "writing row %d\n", row);
      if (write(fd_out, buf_out,
                bytes_per_row_out) != bytes_per_row_out) {
        fprintf(stderr, "error writing %s\n", file_out);
        perror("extract_region");
        there_were_errors = TRUE;
        break;
      }
    }
    break;
  }

  /*
   *      close input and output grid files
   */
  if (fd_out >= 0)
    close(fd_out);
  if (fd_in)
    close(fd_in);

  /*
   *      Deallocate buffers
   */
  if (buf_in)
    free(buf_in);
  if (buf_temp)
    free(buf_temp);

  if (very_verbose) {
    if (there_were_errors)
      fprintf(stderr, "extract_region: done, but there were errors\n");
    else
      fprintf(stderr, "extract_region: done, ok\n");
  }

  return (there_were_errors ? EXIT_FAILURE : EXIT_SUCCESS);
}
