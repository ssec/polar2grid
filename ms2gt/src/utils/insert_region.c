/*======================================================================
 * insert_region.c - insert a region from a grid file
 *
 * 22-Dec-1998 T.Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/

static const char insert_region_c_rcsid[] = "$Header: /data2/tharan/navdir/src/utils/insert_region.c,v 1.8 2010/07/08 22:49:06 tharan Exp $";

#include <stdio.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include "define.h"

#define USAGE \
"$Revision: 1.8 $\n" \
"usage: insert_region [-v] [-i [fill_value]] [-t transparent_value] [-f]\n"\
"          bytes_per_cell cols_in rows_in\n"\
"          col_start row_start cols_out rows_out\n"\
"          file_in\n"\
"          file_out\n"\
"  input : bytes_per_cell - the number of bytes per single grid location.\n"\
"          cols_in - the number of columns in the region (input file).\n"\
"          rows_in - the number of rows in the region (input file).\n"\
"          col_start - the zero-based column number in the output file\n"\
"            specifying where to insert the region.\n"\
"          row_start - the zero-based row number in the output file\n"\
"            specifying where to insert the region.\n"\
"          cols_out - the number of columns in the output file.\n"\
"          rows_out - the number of rows in the output file.\n"\
"          file_in  - the input grid filename.\n"\
"  output: file_out - the output grid filename.\n"\
"  option: v - verbose (may be repeated)\n"\
"          i [fill_value] - initialize the output file to the specified fill\n"\
"            value. If the fill value is not specified, then 0 is used.\n"\
"          t transparent_value - specifies that any occurrences of the\n"\
"            specified transparent value in the input file will not be\n"\
"            inserted into the output file.\n"\
"          f - specifies floating-point data. Requires that bytes_per_cell\n"\
"            by equal to 4 or 8.\n"

static void DisplayUsage(void)
{
  error_exit(USAGE);
}

static void DisplayInvalidParameter(char *param)
{
  fprintf(stderr, "insert_region: Parameter %s is invalid.\n", param);
  DisplayUsage();
}

/*------------------------------------------------------------------------
 * main - insert_region
 *
 *        input : argc, argv - command line args
 *
 *      result: EXIT_SUCCESS or EXIT_FAILURE
 *
 *      effect: Input consists of grid file file_in whose dimensions are
 *              defined by bytes_per_cell, cols_in, and rows_in.
 *              Output consists of grid file file_out consisting of cols_out
 *              columns and rows_out and having the same number of
 *              bytes_per_cell as file_in; file_in is inserted into file_out
 *              at the location defined by col_start and row_start; if file_out
 *              does not exist, an error is generated unless the -i option
 *              is specified. If the -t option is specified, then the any input
 *              values equal to transparent_value are not copied to the
 *              output file.
 *------------------------------------------------------------------------*/
int main(int argc, char *argv[])
{
  char *option;
  int bytes_per_cell, cols_in, rows_in;
  int col_start, row_start, cols_out, rows_out;
  char *file_in;
  char *file_out;

  bool verbose, very_verbose, very_very_verbose;
  bool initialize;
  char *fill_value_string;
  bool transparent;
  char *transparent_value_string;
  bool floating_point;

  byte1 *buf_in = NULL;
  byte1 *buf_out = NULL;
  byte1 *bufp_in;
  byte1 *bufp_out;
  int fd_in  = -1;
  int fd_out = -1;
  bool there_were_errors;
  int row, col;
  int bytes_per_row_in, bytes_per_row_out;
  int last_row_in_region;
  int open_flags;
  int ifill, itrans;
  double dfill, dtrans;
  byte1 fill_value[8];
  byte1 *fillp;
  byte1 transparent_value[8];
  byte1 *transp;

  /*
   *     set defaults
   */
  verbose = very_verbose = very_very_verbose = FALSE;
  initialize = FALSE;
  fill_value_string = "0";
  transparent = FALSE;
  transparent_value_string = "0";
  floating_point = FALSE;
  there_were_errors = FALSE;

  /*
   *     get command line options
   */
  while (--argc > 0 && (*++argv)[0] == '-') {
    for (option = argv[0]+1; *option != '\0'; option++) {
      switch (*option) {
      case 'v':
        if (very_verbose)
          very_very_verbose = TRUE;
        if (verbose)
          very_verbose = TRUE;
        verbose = TRUE;
        break;
      case 'V':
        fprintf(stderr,"%s\n", insert_region_c_rcsid);
        break;
      case 'i':
        initialize = TRUE;
        if (argc >= 11 &&
            ((*(argv+1)[0] != '-') ||
             (strlen(*(argv+1)) > 1 &&
              *(*(argv+1)+1) >= '0' && *(*(argv+1)+1) <= '9'))) {
          ++argv; --argc;
          fill_value_string = *argv;
        }
        break;
      case 't':
        ++argv; --argc;
        transparent = TRUE;
        if (argc <= 0)
          DisplayInvalidParameter("transparent_value");
        transparent_value_string = *argv;
        break;
      case 'f':
        floating_point = TRUE;
        break;
      default:
        fprintf(stderr, "insert_region: invalid option %c\n", *option);
        DisplayUsage();
      }
    }
  }

  /*
   *     get command line args
   */
  if (argc != 9)
    DisplayUsage();
  if (sscanf(*argv++, "%d", &bytes_per_cell) != 1) {
    fprintf(stderr, "invalid bytes_per_cell value %s\n", *argv);
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &cols_in) != 1) {
    fprintf(stderr, "invalid cols_in value %s\n", *argv);
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &rows_in) != 1) {
    fprintf(stderr, "invalid rows_in value %s\n", *argv);
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &col_start) != 1) {
    fprintf(stderr, "invalid col_start value %s\n", *argv);
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &row_start) != 1) {
    fprintf(stderr, "invalid row_start value %s\n", *argv);
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &cols_out) != 1) {
    fprintf(stderr, "invalid cols_out value %s\n", *argv);
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &rows_out) != 1) {
    fprintf(stderr, "invalid rows_out value %s\n", *argv);
    DisplayUsage();
  }
  file_in  = *argv++;
  file_out = *argv++;

  /*
   *     Display command line parameters
   */
  if (verbose) {
    fprintf(stderr, "insert_region:       %s\n", insert_region_c_rcsid);
    fprintf(stderr, "  bytes_per_cell:    %d\n", bytes_per_cell);
    fprintf(stderr, "  cols_in:           %d\n", cols_in);
    fprintf(stderr, "  rows_in:           %d\n", rows_in);
    fprintf(stderr, "  col_start:         %d\n", col_start);
    fprintf(stderr, "  row_start:         %d\n", row_start);
    fprintf(stderr, "  cols_out:          %d\n", cols_out);
    fprintf(stderr, "  rows_out:          %d\n", rows_out);
    fprintf(stderr, "  file_in:           %s\n", file_in);
    fprintf(stderr, "  file_out:          %s\n", file_out);
    fprintf(stderr, "  initialize:        %d\n", initialize);
    fprintf(stderr, "  fill_value:        %s\n", fill_value_string);
    fprintf(stderr, "  transparent:       %d\n", transparent);
    fprintf(stderr, "  transparent_value: %s\n", transparent_value_string);
    fprintf(stderr, "  floating_point:    %d\n", floating_point);
  }
  if (floating_point && bytes_per_cell != 4 && bytes_per_cell != 8) {
    fprintf(stderr, "if -f is specified, then bytes_per_cell must be 4 or 8\n");
    DisplayUsage();
  }

  /*
   *  Set up fill and transparent buffers
   */

  fillp = fill_value;
  transp = transparent_value;
  if (!floating_point) {
    if (sscanf(fill_value_string, "%d", &ifill) != 1)
      DisplayInvalidParameter("fill_value");
    if (sscanf(transparent_value_string, "%d", &itrans) != 1)
      DisplayInvalidParameter("transparent_value");
    switch(bytes_per_cell) {
    case 1:
      *((byte1 *)fillp) = (byte1)ifill;
      *((byte1 *)transp) = (byte1)itrans;
      break;
    case 2:
      *((short *)fillp) = (short)ifill;
      *((short *)transp) = (short)itrans;
      break;
    case 3:
      *((int *)fillp) = (int)ifill;
      *((int *)transp) = (int)itrans;
    case 4:
      *((int *)fillp) = (int)ifill;
      *((int *)transp) = (int)itrans;
      break;
    default:
      DisplayInvalidParameter("bytes_per_cell");
      break;
    }
  } else {
    if (sscanf(fill_value_string, "%lf", &dfill) != 1)
      DisplayInvalidParameter("fill_value");
    if (sscanf(transparent_value_string, "%lf", &dtrans) != 1)
      DisplayInvalidParameter("transparent_value");
    switch(bytes_per_cell) {
    case 4:
      *((float *)fillp) = (float)dfill;
      *((float *)transp) = (float)dtrans;
      break;
    case 8:
      *((double *)fillp) = (double)dfill;
      *((double *)transp) = (double)dtrans;
      break;
    default:
      DisplayInvalidParameter("bytes_per_cell");
      break;
    }
  }

  /*
   *     use loop even though it's one time through for easy error exit
   */
  for(;;) {

    /*
     *     check for a valid region
     */
    if (col_start + cols_in > cols_out) {
      fprintf(stderr,
              "insert_region: col_start + cols_in must be <= cols_out\n");
      there_were_errors = TRUE;
    }
    if (row_start + rows_in > rows_out) {
      fprintf(stderr,
              "insert_region: row_start + rows_in must be <= rows_out\n");
      there_were_errors = TRUE;
    }
    if (there_were_errors)
      break;

    /*
     *    initialize buffer size for i/o
     */
    bytes_per_row_in  = cols_in  * bytes_per_cell;
    bytes_per_row_out = cols_out * bytes_per_cell;

    /*
     *    allocate a buffer for each input and output grid file.
     */
    if (very_verbose)
      fprintf(stderr, "insert_region: allocating buffers\n");

    buf_in = (byte1 *)calloc(bytes_per_row_in, sizeof(byte1));
    if (!buf_in) {
      fprintf(stderr, "error allocating %d bytes for input buffer\n",
              bytes_per_row_in);
      perror("insert_region");
      there_were_errors = TRUE;
      break;
    }

    buf_out = (byte1 *)calloc(bytes_per_row_out, sizeof(byte1));
    if (!buf_out) {
      fprintf(stderr, "error allocating %d bytes for output buffer\n",
              bytes_per_row_out);
      perror("insert_region");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open input file
     */
    if (very_verbose)
      fprintf(stderr, "insert_region: opening input file\n");

    fd_in = open(file_in, O_RDONLY);
    if (fd_in < 0) {
      fprintf(stderr, "error opening %s\n", file_in);
      perror("insert_region");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open output file
     */
    if (very_verbose)
      fprintf(stderr, "insert_region: opening output file\n");

    open_flags = (initialize) ? O_RDWR | O_CREAT : O_RDWR;
    fd_out = open(file_out, open_flags, 0644);
    if (fd_out < 0) {
      fprintf(stderr, "error opening %s\n", file_out);
      perror("insert_region");
      there_were_errors = TRUE;
      break;
    }
    if (initialize) {
      if (very_verbose)
        fprintf(stderr, "insert_region: initializing %s\n",
                file_out);

      /*
       *  initialize buf_out to the fill value
       */

      fillp = fill_value;
      bufp_out = buf_out;
      for (col = 0; col < cols_out; col++, bufp_out += bytes_per_cell)
        memcpy(bufp_out, fillp, bytes_per_cell);

      /*
       *  write buf_out to each row in the output file
       */

      for (row = 0; row < rows_out; row++) {
        if (write(fd_out, buf_out,
                  bytes_per_row_out) != bytes_per_row_out) {
          fprintf(stderr, "error writing %s\n", file_out);
          perror("insert_region");
          there_were_errors = TRUE;
          break;
        }
      }
      if (there_were_errors)
        break;
    }

    /*
     *     seek to row containing region in output file
     */
    if (lseek(fd_out,
              (off_t)row_start * bytes_per_row_out,
              SEEK_SET) == -1) {
      fprintf(stderr, "error seeking to row %d in %s\n",
              row_start, file_out);
      perror("insert_region");
      there_were_errors = TRUE;
      break;
    }

    last_row_in_region = row_start + rows_in - 1;

    /*
     *    for each row in region
     */
    for (row = row_start; row <= last_row_in_region; row++) {

      if (very_verbose)
        fprintf(stderr, "reading row from %s\n", file_out);

      /*
       *     read the row from the output file
       */
      if (read(fd_out, buf_out,
               bytes_per_row_out) != bytes_per_row_out) {
        fprintf(stderr, "error reading %s\n", file_out);
        perror("insert_region");
        there_were_errors = TRUE;
        break;
      }

      /*
       *  read a row from the input file.
       *  read it into the input buffer if doing transparent processing;
       *  otherwise read it directly into the output buffer.
       */
      bufp_in = (transparent) ? buf_in : buf_out + col_start * bytes_per_cell;
      if (very_very_verbose)
        fprintf(stderr, "reading row %d\n", row);
      if (read(fd_in, bufp_in,
               bytes_per_row_in) != bytes_per_row_in) {
        fprintf(stderr, "error reading %s\n", file_in);
        perror("insert_region");
        there_were_errors = TRUE;
        break;
      }

      /*
       *  Perform transparent processing as needed.
       *  Only copy input values to the output buffer that are not
       *  equal to the transparent value.
       */
      if (transparent) {
        bufp_out = buf_out + col_start * bytes_per_cell;
        for (col = 0;
             col < cols_in;
             col++, bufp_in += bytes_per_cell, bufp_out += bytes_per_cell) {
          if (memcmp(bufp_in, transp, bytes_per_cell) != 0)
            memcpy(bufp_out, bufp_in, bytes_per_cell);
        }
      }

      /*
       *     seek back to the beginning of the output row
       */
      if (lseek(fd_out,
                (off_t)row * bytes_per_row_out,
                SEEK_SET) == -1) {
        fprintf(stderr, "error seeking to row %d in %s\n",
                row, file_out);
        perror("insert_region");
        there_were_errors = TRUE;
        break;
      }

      /*
       *     write the output row
       */
      if (write(fd_out, buf_out,
                bytes_per_row_out) != bytes_per_row_out) {
        fprintf(stderr, "error writing %s\n", file_out);
        perror("insert_region");
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
  if (fd_in >= 0)
    close(fd_in);

  /*
   *      Deallocate buffers
   */
  if (buf_in)
    free(buf_in);
  if (buf_out)
    free(buf_out);

  if (very_verbose) {
    if (there_were_errors)
      fprintf(stderr, "insert_region: done, but there were errors\n");
    else
      fprintf(stderr, "insert_region: done, ok\n");
  }

  return (there_were_errors ? EXIT_FAILURE : EXIT_SUCCESS);
}
