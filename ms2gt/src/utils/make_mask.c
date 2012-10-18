/*======================================================================
 * make_mask.c - insert a region from a grid file
 *
 * 23-Nov-2004 T.Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/

static const char make_mask_c_rcsid[] = "$Header: /disks/megadune/data/tharan/ms2gth/src/utils/make_mask.c,v 1.6 2007/05/02 22:04:01 tharan Exp $";

#include <stdio.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include "define.h"
#include "matrix.h"

#define USAGE \
"$Revision: 1.6 $\n" \
"usage: make_mask [-v] [-d] [-b] [-s] [-f] [-F factor] [-i mask_file_in]\n"\
"                 [-m mask_value_in] [-M mask_value_out] [-U unmask_value_out]\n"\
"          bytes_per_cell cols_in rows_in\n"\
"          col_start_in row_start_in cols_in_region rows_in_region\n"\
"          file_in\n"\
"          mask_file_out\n"\
"  input : bytes_per_cell - the number of bytes per single grid location\n"\
"            in the input file. Must be 1, 2, 4, or 8.\n"\
"            NOTE: If bytes_per_cell is 8, then -f must be specified.\n"\
"          cols_in - the number of columns in the input file.\n"\
"          rows_in - the number of rows in the input file.\n"\
"          col_start_in - the zero-based column number in the input file\n"\
"            specifying where to start reading the input file.\n"\
"          row_start_in - the zero-based row number in the input file\n"\
"            specifying where to start reading the input file.\n"\
"          cols_in_region - the number of columns to read in the input file.\n"\
"          rows_in_region - the number of rows to read in the input file.\n"\
"          file_in  - the input filename.\n"\
"  output: mask_file_out - the one byte per cell output mask filename.\n"\
"            There will be factor * cols_in_region columns and\n"\
"            factor * rows_in_region rows in the output file.\n"\
"  option: v - verbose (may be repeated)\n"\
"          d - delete mask_file_out if it consists entirely of mask_value_out.\n"\
"          b - byte-swap the input file.\n"\
"          s - specifies signed input data.\n"\
"          f - specifies floating-point input data. Requires that\n"\
"            bytes_per_cell be equal to 4 or 8.\n"\
"            NOTE: If -f is set then -s is ignored.\n"\
"          F factor - specifies the expansion factor to use in expanding\n"\
"            the mask. Must be an integer > 0. The default value is 1.\n"\
"          i mask_file_in - specifies a 1 byte per cell input mask file to be\n"\
"            anded with the mask computed from the input file to produce the\n"\
"            mask output file. The dimensions of mask_file_in must be the\n"\
"              same as file_in.\n"\
"          m mask_value_in - specifies the mask value in the input file.\n"\
"            The default is 0.\n"\
"            NOTE: The unmask value in the input file is any value not equal\n"\
"                  to mask_value_in.\n"\
"          M mask_value_out - specifies the mask value in the mask input\n"\
"            file (if any), and the mask output file.\n"\
"            Must be between 0 and 255. The default is 0.\n"\
"          U unmask_value_out - specifies the unmask value in the mask input\n"\
"            file (if any), and the mask output file.\n"\
"            Must be between 0 and 255. The default is 1.\n"

#define MM_UNSIGNED_CHAR        1
#define MM_SIGNED_CHAR          2
#define MM_UNSIGNED_SHORT       3
#define MM_SIGNED_SHORT         4
#define MM_UNSIGNED_INT         5
#define MM_SIGNED_INT           6
#define MM_FLOAT                7
#define MM_DOUBLE               8

static void DisplayUsage(void)
{
  error_exit(USAGE);
}

static void DisplayInvalidParameter(char *param)
{
  fprintf(stderr, "make_mask: Parameter %s is invalid.\n", param);
  DisplayUsage();
}

/*------------------------------------------------------------------------
 * main - make_mask
 *
 *        input : argc, argv - command line args
 *
 *      result: EXIT_SUCCESS or EXIT_FAILURE
 *
 *------------------------------------------------------------------------*/
int main(int argc, char *argv[])
{
  char *option;
  int bytes_per_cell, cols_in, rows_in;
  int col_start_in, row_start_in, cols_in_region, rows_in_region;
  char *file_in;
  char *mask_file_out;

  bool verbose, very_verbose, very_very_verbose;
  bool delete_if_all_masked;
  bool byte_swap_input;
  bool signed_input;
  bool floating_point_input;
  int factor;
  char *mask_file_in;
  double mask_value_in;
  int mask_value_out;
  int unmask_value_out;

  byte1 *buf_in = NULL;
  byte1 *buf_mask_in = NULL;
  byte1 **buf_mask_out = NULL;
  byte1 *bufp_in;
  byte1 *bufp_mask_in;
  int fd_in  = -1;
  int fd_mask_in = -1;
  int fd_mask_out = -1;
  bool there_were_errors;
  int row, col;
  int cols_out;
  int col_out;
  int rows_per_mask_buf_out;
  int bytes_per_row_in;
  int bytes_per_mask_row_in;
  int bytes_per_mask_buf_out;
  int last_row_in_region;
  int last_col_in_region;
  int last_row_in_output_region;
  int last_col_in_output_region;
  int data_type_in;
  byte4 t4;
  byte4 *p4;
  byte2 t2;
  byte2 *p2;
  double mask_test;
  byte1 mask;
  int i, j;
  bool got_unmasked;
  char command[MAX_STRING];

  /*
   *     set defaults
   */
  verbose = very_verbose = very_very_verbose = FALSE;
  delete_if_all_masked = FALSE;
  byte_swap_input = FALSE;
  signed_input = FALSE;
  floating_point_input = FALSE;
  factor = 1;
  mask_file_in = NULL;
  mask_value_in = 0;
  mask_value_out = 0;
  unmask_value_out = 1;
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
        fprintf(stderr,"%s\n", make_mask_c_rcsid);
        break;
      case 'd':
        delete_if_all_masked = TRUE;
        break;
      case 'b':
        byte_swap_input = TRUE;
        break;
      case 's':
        signed_input = TRUE;
        break;
      case 'f':
        floating_point_input = TRUE;
        break;
      case 'F':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("factor");
        if (sscanf(*argv, "%d", &factor) != 1)
          DisplayInvalidParameter("factor");
        break;
      case 'i':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("mask_file_in");
        mask_file_in = *argv;
        break;
      case 'm':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("mask_value_in");
        if (sscanf(*argv, "%lf", &mask_value_in) != 1)
          DisplayInvalidParameter("mask_value_in");
        break;
      case 'M':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("mask_value_out");
        if (sscanf(*argv, "%d", &mask_value_out) != 1)
          DisplayInvalidParameter("mask_value_out");
        break;
      case 'U':
        ++argv; --argc;
        if (argc <= 0)
          DisplayInvalidParameter("unmask_value_out");
        if (sscanf(*argv, "%d", &mask_value_out) != 1)
          DisplayInvalidParameter("unmask_value_out");
        break;
      default:
        fprintf(stderr, "make_mask: invalid option %c\n", *option);
        DisplayUsage();
      }
    }
  }

  /*
   *     get command line args
   */
  if (argc == 0)
    DisplayUsage();
  if (argc != 9) {
    fprintf(stderr, "mask_test: incorrect number of parameters.\n");
    DisplayUsage();
  }
  if (sscanf(*argv++, "%d", &bytes_per_cell) != 1)
    DisplayInvalidParameter("bytes_per_cell");
  if (sscanf(*argv++, "%d", &cols_in) != 1)
    DisplayInvalidParameter("cols_in");
  if (sscanf(*argv++, "%d", &rows_in) != 1)
    DisplayInvalidParameter("rows_in");
  if (sscanf(*argv++, "%d", &col_start_in) != 1)
    DisplayInvalidParameter("col_start_in");
  if (sscanf(*argv++, "%d", &row_start_in) != 1)
    DisplayInvalidParameter("row_start_in");
  if (sscanf(*argv++, "%d", &cols_in_region) != 1)
    DisplayInvalidParameter("cols_in_region");
  if (sscanf(*argv++, "%d", &rows_in_region) != 1)
    DisplayInvalidParameter("rows_in_region");
  file_in  = *argv++;
  mask_file_out = *argv++;

  /*
   *     Display command line parameters
   */
  if (verbose) {
    fprintf(stderr, "make_mask:              %s\n", make_mask_c_rcsid);
    fprintf(stderr, "  bytes_per_cell:       %d\n", bytes_per_cell);
    fprintf(stderr, "  cols_in:              %d\n", cols_in);
    fprintf(stderr, "  rows_in:              %d\n", rows_in);
    fprintf(stderr, "  col_start_in:         %d\n", col_start_in);
    fprintf(stderr, "  row_start_in:         %d\n", row_start_in);
    fprintf(stderr, "  cols_in_region:       %d\n", cols_in_region);
    fprintf(stderr, "  rows_in_region:       %d\n", rows_in_region);
    fprintf(stderr, "  file_in:              %s\n", file_in);
    fprintf(stderr, "  mask_file_out:        %s\n", mask_file_out);
    fprintf(stderr, "  delete_if_all_masked: %d\n", delete_if_all_masked);
    fprintf(stderr, "  byte_swap_input:      %d\n", byte_swap_input);
    fprintf(stderr, "  signed_input:         %d\n", signed_input);
    fprintf(stderr, "  floating_point_input: %d\n", floating_point_input);
    fprintf(stderr, "  factor:               %d\n", factor);
    fprintf(stderr, "  mask_file_in:         %s\n", mask_file_in);
    fprintf(stderr, "  mask_value_in:        %lf\n", mask_value_in);
    fprintf(stderr, "  mask_value_out:       %d\n", mask_value_out);
    fprintf(stderr, "  unmask_value_out:     %d\n", unmask_value_out);
  }

  /*
   *     use loop even though it's one time through for easy error exit
   */
  for(;;) {

    /*
     *  check for valid parameters
     */
    switch (bytes_per_cell) {
    case 1:
      data_type_in = signed_input ? MM_SIGNED_CHAR : MM_UNSIGNED_CHAR;
      break;
    case 2:
      data_type_in = signed_input ? MM_SIGNED_SHORT : MM_UNSIGNED_SHORT;
      break;
    case 4:
      data_type_in = floating_point_input ? MM_FLOAT :
        (signed_input ? MM_SIGNED_CHAR : MM_UNSIGNED_CHAR);
      break;
    case 8:
      if (floating_point_input)
        data_type_in = MM_DOUBLE;
      else {
        fprintf(stderr,
                "make_mask: if bytes_per_cell is 8, then -f must be set.\n");
        there_were_errors = TRUE;
      }
      break;
    default:
      fprintf(stderr, "make_mask: bytes_per_cell must be 1, 2, 4, or 8\n");
      there_were_errors = TRUE;
      break;
    }
    
    if (factor <= 0) {
      fprintf(stderr,
              "make_mask: factor must be an integer greater than 0.\n");
      there_were_errors = TRUE;
    }
    if (floating_point_input && bytes_per_cell != 4 && bytes_per_cell != 8) {
      fprintf(stderr, "if -f is specified, then bytes_per_cell must be 4 or 8\n");
      there_were_errors = TRUE;
    }
    if (mask_value_out < 0 || mask_value_out > 255) {
      fprintf(stderr, "mask_value_out must be between 0 and 255\n");
      there_were_errors = TRUE;
    }
    if (unmask_value_out < 0 || unmask_value_out > 255) {
      fprintf(stderr, "unmask_value_out must be between 0 and 255\n");
      there_were_errors = TRUE;
    }
    
    /*
     *     check for a valid region
     */
    cols_out = cols_in_region * factor;
    if (col_start_in + cols_in_region > cols_in) {
      fprintf(stderr,
              "make_mask: col_start_in + cols_in_region must be <= cols_in\n");
      there_were_errors = TRUE;
    }
    if (row_start_in + rows_in_region > rows_in) {
      fprintf(stderr,
              "make_mask: row_start_in + rows_in_region must be <= rows_in\n");
      there_were_errors = TRUE;
    }
    if (there_were_errors)
        DisplayUsage();

    /*
     *    initialize buffer sizes for i/o
     */
    bytes_per_row_in  = cols_in  * bytes_per_cell;
    bytes_per_mask_row_in = (mask_file_in == NULL) ? 0 : cols_in;
    rows_per_mask_buf_out = factor;
    bytes_per_mask_buf_out = cols_out * rows_per_mask_buf_out;

    /*
     *    allocate a buffer for each input and output grid file.
     */
    if (very_verbose)
      fprintf(stderr, "make_mask: allocating buffers\n");

    buf_in = (byte1 *)calloc(bytes_per_row_in, sizeof(byte1));
    if (!buf_in) {
      fprintf(stderr, "error allocating %d bytes for input buffer\n",
              bytes_per_row_in);
      perror("make_mask");
      there_were_errors = TRUE;
      break;
    }

    if (bytes_per_mask_row_in) {
      buf_mask_in = (byte1 *)calloc(bytes_per_mask_row_in, sizeof(byte1));
      if (!buf_mask_in) {
        fprintf(stderr, "error allocating %d bytes for input mask buffer\n",
                bytes_per_mask_row_in);
        perror("make_mask");
        there_were_errors = TRUE;
        break;
      }
    }

    buf_mask_out = (byte1 **)matrix(rows_per_mask_buf_out, cols_out,
                                    sizeof(byte1), 1);
    if (!buf_mask_out) {
      fprintf(stderr, "error allocating %d bytes for output mask buffer\n",
              bytes_per_mask_buf_out);
      perror("make_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open input file
     */
    if (very_verbose)
      fprintf(stderr, "make_mask: opening input file\n");

    fd_in = open(file_in, O_RDONLY);
    if (fd_in < 0) {
      fprintf(stderr, "error opening %s\n", file_in);
      perror("make_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open input mask file
     */
    if (bytes_per_mask_row_in) {
      if (very_verbose)
        fprintf(stderr, "make_mask: opening input mask file\n");

      fd_mask_in = open(mask_file_in, O_RDONLY);
      if (fd_mask_in < 0) {
        fprintf(stderr, "error opening %s\n", mask_file_in);
        perror("make_mask");
        there_were_errors = TRUE;
        break;
      }
    }

    /*
     *     open output mask file
     */
    if (very_verbose)
      fprintf(stderr, "make_mask: opening output file\n");

    fd_mask_out = open(mask_file_out, O_WRONLY | O_CREAT, 0664);
    if (fd_mask_out < 0) {
      fprintf(stderr, "error opening %s\n", mask_file_out);
      perror("make_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     seek to row containing input region in input file
     */
    if (very_very_verbose)
      fprintf(stderr, "row_start_in: %d  bytes_per_row_in: %d\n",
              row_start_in, bytes_per_row_in);
    if (lseek(fd_in,
              (off_t)row_start_in * bytes_per_row_in,
              SEEK_SET) == -1) {
      fprintf(stderr, "error seeking to row %d in %s\n",
              row_start_in, file_in);
      perror("make_mask");
      there_were_errors = TRUE;
      break;
    }

    if (bytes_per_mask_row_in) {
      /*
       *     seek to row containing input region in input mask file
       */
      if (lseek(fd_mask_in,
                (off_t)row_start_in * bytes_per_mask_row_in,
                SEEK_SET) == -1) {
        fprintf(stderr, "error seeking to row %d in %s\n",
                row_start_in, mask_file_in);
        perror("make_mask");
        there_were_errors = TRUE;
        break;
      }
    }

    last_row_in_region = row_start_in + rows_in_region - 1;
    last_col_in_region = col_start_in + cols_in_region - 1;
    last_row_in_output_region = rows_per_mask_buf_out - 1;
    got_unmasked = FALSE;

    /*
     *    for each row in region
     */
    for (row = row_start_in; row <= last_row_in_region; row++) {

      if (very_very_verbose)
        fprintf(stderr, "reading row from %s\n", file_in);

      /*
       *     read the row from the input file
       */
      if (read(fd_in, buf_in,
               bytes_per_row_in) != bytes_per_row_in) {
        fprintf(stderr, "error reading %s\n", file_in);
        perror("make_mask");
        there_were_errors = TRUE;
        break;
      }

      if (bytes_per_mask_row_in) {
        /*
         *  read a row from the input mask file.
         */
        if (very_very_verbose)
          fprintf(stderr, "reading row from %s\n", mask_file_in);
        if (read(fd_mask_in, buf_mask_in,
                 bytes_per_mask_row_in) != bytes_per_mask_row_in) {
          fprintf(stderr, "error reading %s\n", mask_file_in);
          perror("make_mask");
          there_were_errors = TRUE;
          break;
        }
      }

      /*
       *  process the row
       */
      bufp_in = buf_in + col_start_in * bytes_per_cell;
      bufp_mask_in = buf_mask_in + col_start_in;
      col_out = 0;
      for (col = col_start_in; col <= last_col_in_region; col++) {

        if (byte_swap_input) {

          /*
           *  byte swap the input
           */
          if (bytes_per_cell == 4) {
            p4 = (byte4 *)bufp_in;
            t4 = *p4;
            t4 = ((t4 >> 24) & 0xff) | ((t4 >> 8) & 0xff00) |
                 ((t4 << 8) & 0xff0000) | (t4 << 24);
            *p4 = t4;
          } else {
            p2 = (byte2 *)bufp_in;
            t2 = *p2;
            t2 = ((t2 >> 8) & 0xff) | (t2 << 8);
            *p2 = t2;
          }
        }
        
        /*
         *  convert the input value to a mask value
         */
        switch (data_type_in) {
        case MM_UNSIGNED_CHAR:
          mask_test = *((byte1 *)bufp_in);
          break;
        case MM_SIGNED_CHAR:
          mask_test = *((char *)bufp_in);
          break;
        case MM_UNSIGNED_SHORT:
          mask_test = *((byte2 *)bufp_in);
          break;
        case MM_SIGNED_SHORT:
          mask_test = *((short *)bufp_in);
          break;
        case MM_UNSIGNED_INT:
          mask_test = *((byte4 *)bufp_in);
          break;
        case MM_SIGNED_INT:
          mask_test = *((int *)bufp_in);
          break;
        case MM_FLOAT:
          mask_test = *((float *)bufp_in);
          break;
        case MM_DOUBLE:
          mask_test = *((double *)bufp_in);
          break;
        }
        bufp_in += bytes_per_cell;
        if (very_very_verbose)
          fprintf(stderr,
                 "row:%d   col:%d   mask_test:%lf\n", row, col, mask_test);
        mask = (byte1)((mask_test == mask_value_in) ?
                       mask_value_out : unmask_value_out);

        if (bytes_per_mask_row_in) {

          /*
           *  and the mask with the value from mask_file_in
           */
          mask &= *bufp_mask_in++;
        }
        if (mask == unmask_value_out)
          got_unmasked = TRUE;

        /*
         *  store the mask in the output buffer, expanding as needed
         */
        last_col_in_output_region = col_out + factor - 1;
        for (i = 0; i <= last_row_in_output_region; i++) {
          for (j = col_out; j <= last_col_in_output_region; j++) {
            buf_mask_out[i][j] = mask;
          }
        }
        col_out += factor;
      }

      /*
       *     write the output buffer
       */
      if (very_very_verbose)
        fprintf(stderr, "writing buffer to %s\n", mask_file_out);

      if (write(fd_mask_out, buf_mask_out[0],
                bytes_per_mask_buf_out) != bytes_per_mask_buf_out) {
        fprintf(stderr, "error writing %s\n", mask_file_out);
        perror("make_mask");
        there_were_errors = TRUE;
        break;
      }
    }
    break;
  }

  /*
   *      close input and output files
   */
  if (fd_mask_out >= 0)
    close(fd_mask_out);
  if (fd_mask_in >= 0)
    close(fd_mask_in);
  if (fd_in >= 0)
    close(fd_in);

  /*
   *      Deallocate buffers
   */
  if (buf_in)
    free(buf_in);
  if (buf_mask_in)
    free(buf_mask_in);
  if (buf_mask_out)
    free(buf_mask_out);

  if (delete_if_all_masked && !got_unmasked) {

    /*
     *  delete the output file since there were no unmasked output values
     */
    if (verbose)
      fprintf(stderr, "make_mask: deleting %s\n", mask_file_out);
    sprintf(command, "rm -f %s", mask_file_out);
    system(command);
  }

  if (very_verbose) {
    if (there_were_errors)
      fprintf(stderr, "make_mask: done, but there were errors\n");
    else
      fprintf(stderr, "make_mask: done, ok\n");
  }

  return (there_were_errors ? EXIT_FAILURE : EXIT_SUCCESS);
}
