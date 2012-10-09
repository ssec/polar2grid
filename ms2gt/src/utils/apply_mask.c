/*======================================================================
 * apply_mask.c - insert a region from a grid file
 *
 * 25-Nov-2004 T.Haran tharan@colorado.edu 303-492-1847
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *======================================================================*/

static const char apply_mask_c_rcsid[] = "$Header: /disks/megadune/data/tharan/ms2gth/src/utils/apply_mask.c,v 1.6 2010/10/06 17:15:31 tharan Exp $";

#include <stdio.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include "define.h"

#define USAGE \
"$Revision: 1.6 $\n" \
"usage: apply_mask [-v] [-d] [-b] [-B] [-s] [-f] [-S]\n"\
"                  [-m mask_value_in] [-M mask_value_out]\n"\
"          bytes_per_cell cols_in rows_in\n"\
"          col_start_in row_start_in cols_in_region rows_in_region\n"\
"          mask_file_in file_in file_out\n"\
"  input : bytes_per_cell - the number of bytes per single grid location\n"\
"            in file_in and file_out. Must be 1, 2, 4, or 8.\n"\
"            NOTE: If bytes_per_cell is 8, then -f must be specified and\n"\
"                  neither -b nor -B may be specified.\n"\
"          cols_in - the number of columns in the input files.\n"\
"          rows_in - the number of rows in the input files.\n"\
"          col_start_in - the zero-based column number in the input files\n"\
"            specifying where to start reading.\n"\
"          row_start_in - the zero-based row number in the input files\n"\
"            specifying where to start reading.\n"\
"          cols_in_region - the number of columns to read in the input files\n"\
"            and the number of columns in the output file.\n"\
"          rows_in_region - the number of rows to read in the input files\n"\
"            and the number of rows in the output file.\n"\
"          mask_file_in - specifies a 1 byte per cell input mask file.\n"\
"          file_in  - the input filename.\n"\
"              NOTE: The dimensions of mask_file_in must be the\n"\
"                    same as file_in.\n"\
"  output: file_out - the masked output file.\n"\
"  option: v - verbose (may be repeated)\n"\
"          d - delete file_out if it consists entirely of mask_value_out.\n"\
"          b - byte-swap the input file.\n"\
"          B - byte-swap the output file.\n"\
"          s - specifies signed input and output data.\n"\
"          f - specifies floating-point input and output data. Requires that\n"\
"            bytes_per_cell be equal to 4 or 8.\n"\
"          S - specifies that the mask file is in the same format as that\n"\
"              specified for the input file.\n"\
"              The default is that the mask file is 1 byte per cell.\n"\
"            NOTE: If -f is set then -s is ignored.\n"\
"          m mask_value_in - specifies the mask value in mask_file_in.\n"\
"            Must be between 0 and 255 unless -S is specified. The default is 0.\n"\
"          M mask_value_out - specifies the value in the output file to which\n"\
"            all occurrences of mask_value_in in mask_file_in will be mapped.\n"\
"            The default is 0.\n"

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
  fprintf(stderr, "apply_mask: Parameter %s is invalid.\n", param);
  DisplayUsage();
}

/*------------------------------------------------------------------------
 * main - apply_mask
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
  char *mask_file_in;
  char *file_in;
  char *file_out;

  bool verbose, very_verbose, very_very_verbose;
  bool delete_if_all_masked;
  bool byte_swap_input;
  bool byte_swap_output;
  bool signed_data;
  bool floating_point_data;
  bool mask_same_as_input;
  double mask_value_in;
  double mask_value_out;

  byte1 *buf_mask_in = NULL;
  byte1 *buf_in = NULL;
  byte1 *buf_out = NULL;
  byte1 *bufp_mask_in;
  byte1 *bufp_in;
  byte1 *bufp_out;
  int fd_mask_in = -1;
  int fd_in  = -1;
  int fd_out = -1;
  bool there_were_errors;
  int row, col;
  int cols_out;
  int bytes_per_mask;
  int bytes_per_row_in;
  int bytes_per_mask_row_in;
  int bytes_per_row_out;
  int last_row_in_region;
  int last_col_in_region;
  int data_type;
  byte4 t4;
  byte4 *p4;
  byte2 t2;
  byte2 *p2;
  double mask_test;
  double mask;
  bool got_unmasked;
  char command[MAX_STRING];

  /*
   *     set defaults
   */
  verbose = very_verbose = very_very_verbose = FALSE;
  delete_if_all_masked = FALSE;
  byte_swap_input = FALSE;
  byte_swap_output = FALSE;
  signed_data = FALSE;
  floating_point_data = FALSE;
  mask_same_as_input = FALSE;
  mask_value_in = 0;
  mask_value_out = 0;
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
        fprintf(stderr,"%s\n", apply_mask_c_rcsid);
        break;
      case 'd':
        delete_if_all_masked = TRUE;
        break;
      case 'b':
        byte_swap_input = TRUE;
        break;
      case 'B':
        byte_swap_output = TRUE;
        break;
      case 's':
        signed_data = TRUE;
        break;
      case 'f':
        floating_point_data = TRUE;
        break;
      case 'S':
        mask_same_as_input = TRUE;
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
        if (sscanf(*argv, "%lf", &mask_value_out) != 1)
          DisplayInvalidParameter("mask_value_out");
        break;
      default:
        fprintf(stderr, "apply_mask: invalid option %c\n", *option);
        DisplayUsage();
      }
    }
  }

  /*
   *     get command line args
   */
  if (argc == 0)
    DisplayUsage();
  if (argc != 10) {
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
  mask_file_in = *argv++;
  file_in  = *argv++;
  file_out = *argv++;

  /*
   *     Display command line parameters
   */
  if (verbose) {
    fprintf(stderr, "apply_mask:             %s\n", apply_mask_c_rcsid);
    fprintf(stderr, "  bytes_per_cell:       %d\n", bytes_per_cell);
    fprintf(stderr, "  cols_in:              %d\n", cols_in);
    fprintf(stderr, "  rows_in:              %d\n", rows_in);
    fprintf(stderr, "  col_start_in:         %d\n", col_start_in);
    fprintf(stderr, "  row_start_in:         %d\n", row_start_in);
    fprintf(stderr, "  cols_in_region:       %d\n", cols_in_region);
    fprintf(stderr, "  rows_in_region:       %d\n", rows_in_region);
    fprintf(stderr, "  mask_file_in:         %s\n", mask_file_in);
    fprintf(stderr, "  file_in:              %s\n", file_in);
    fprintf(stderr, "  file_out:             %s\n", file_out);
    fprintf(stderr, "  delete_if_all_masked: %d\n", delete_if_all_masked);
    fprintf(stderr, "  byte_swap_input:      %d\n", byte_swap_input);
    fprintf(stderr, "  byte_swap_output:     %d\n", byte_swap_output);
    fprintf(stderr, "  signed_data:          %d\n", signed_data);
    fprintf(stderr, "  floating_point_data:  %d\n", floating_point_data);
    fprintf(stderr, "  mask_same_as_input:   %d\n", mask_same_as_input);
    fprintf(stderr, "  mask_value_in:        %lf\n", mask_value_in);
    fprintf(stderr, "  mask_value_out:       %lf\n", mask_value_out);
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
      data_type = signed_data ? MM_SIGNED_CHAR : MM_UNSIGNED_CHAR;
      break;
    case 2:
      data_type = signed_data ? MM_SIGNED_SHORT : MM_UNSIGNED_SHORT;
      break;
    case 4:
      data_type = floating_point_data ? MM_FLOAT :
        (signed_data ? MM_SIGNED_CHAR : MM_UNSIGNED_CHAR);
      break;
    case 8:
      if (floating_point_data)
        data_type = MM_DOUBLE;
      else {
        fprintf(stderr,
                "apply_mask: if bytes_per_cell is 8, then -f must be set.\n");
        there_were_errors = TRUE;
      }
      break;
    default:
      fprintf(stderr, "apply_mask: bytes_per_cell must be 1, 2, 4, or 8\n");
      there_were_errors = TRUE;
      break;
    }
    
    if (floating_point_data && bytes_per_cell != 4 && bytes_per_cell != 8) {
      fprintf(stderr,
              "if -f is specified, then bytes_per_cell must be 4 or 8\n");
      there_were_errors = TRUE;
    }
    if (bytes_per_cell == 8 && (byte_swap_input || byte_swap_output)) {
      fprintf(stderr,
           "if bytes_per_cell is 8 then neither -b nor -B may be specified.\n");
      there_were_errors = TRUE;
    }
    if (!mask_same_as_input && (mask_value_in < 0 || mask_value_in > 255)) {
      fprintf(stderr, "mask_value_in must be between 0 and 255\n");
      there_were_errors = TRUE;
    }
    
    /*
     *     check for a valid region
     */
    cols_out = cols_in_region;
    if (col_start_in + cols_in_region > cols_in) {
      fprintf(stderr,
              "apply_mask: col_start_in + cols_in_region must be <= cols_in\n");
      there_were_errors = TRUE;
    }
    if (row_start_in + rows_in_region > rows_in) {
      fprintf(stderr,
              "apply_mask: row_start_in + rows_in_region must be <= rows_in\n");
      there_were_errors = TRUE;
    }
    if (there_were_errors)
        DisplayUsage();

    /*
     *    initialize buffer sizes for i/o
     */
    bytes_per_mask = mask_same_as_input ? bytes_per_cell : 1;
    bytes_per_mask_row_in = cols_in  * bytes_per_mask;
    bytes_per_row_in      = cols_in  * bytes_per_cell;
    bytes_per_row_out     = cols_out * bytes_per_cell;

    /*
     *    allocate a buffer for each input and output grid file.
     */
    if (very_verbose)
      fprintf(stderr, "apply_mask: allocating buffers\n");

    buf_mask_in = (byte1 *)calloc(bytes_per_mask_row_in, sizeof(byte1));
    if (!buf_mask_in) {
      fprintf(stderr, "error allocating %d bytes for input mask buffer\n",
              bytes_per_mask_row_in);
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    buf_in = (byte1 *)calloc(bytes_per_row_in, sizeof(byte1));
    if (!buf_in) {
      fprintf(stderr, "error allocating %d bytes for input buffer\n",
              bytes_per_row_in);
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    buf_out = (byte1 *)calloc(bytes_per_row_out, sizeof(byte1));
    if (!buf_out) {
      fprintf(stderr, "error allocating %d bytes for output buffer\n",
              bytes_per_row_out);
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open input mask file
     */
    if (very_verbose)
      fprintf(stderr, "apply_mask: opening input mask file\n");
    
    fd_mask_in = open(mask_file_in, O_RDONLY);
    if (fd_mask_in < 0) {
      fprintf(stderr, "error opening %s\n", mask_file_in);
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open input file
     */
    if (very_verbose)
      fprintf(stderr, "apply_mask: opening input file\n");

    fd_in = open(file_in, O_RDONLY);
    if (fd_in < 0) {
      fprintf(stderr, "error opening %s\n", file_in);
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     open output mask file
     */
    if (very_verbose)
      fprintf(stderr, "apply_mask: opening output file\n");

    fd_out = open(file_out, O_WRONLY | O_CREAT, 0664);
    if (fd_out < 0) {
      fprintf(stderr, "error opening %s\n", file_out);
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    /*
     *     seek to row containing input region in input mask file
     */
    if (lseek(fd_mask_in,
              (off_t)row_start_in * bytes_per_mask_row_in,
              SEEK_SET) == -1) {
      fprintf(stderr, "error seeking to row %d in %s\n",
              row_start_in, mask_file_in);
      perror("apply_mask");
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
      perror("apply_mask");
      there_were_errors = TRUE;
      break;
    }

    last_row_in_region = row_start_in + rows_in_region - 1;
    last_col_in_region = col_start_in + cols_in_region - 1;
    got_unmasked = FALSE;

    /*
     *    for each row in region
     */
    for (row = row_start_in; row <= last_row_in_region; row++) {

      if (very_very_verbose)
        fprintf(stderr, "reading row from %s\n", file_in);

      /*
       *  read a row from the input mask file.
       */
      if (very_very_verbose)
        fprintf(stderr, "reading row from %s\n", mask_file_in);
      if (read(fd_mask_in, buf_mask_in,
               bytes_per_mask_row_in) != bytes_per_mask_row_in) {
        fprintf(stderr, "error reading %s\n", mask_file_in);
        perror("apply_mask");
        there_were_errors = TRUE;
        break;
      }

      /*
       *     read the row from the input file
       */
      if (read(fd_in, buf_in,
               bytes_per_row_in) != bytes_per_row_in) {
        fprintf(stderr, "error reading %s\n", file_in);
        perror("apply_mask");
        there_were_errors = TRUE;
        break;
      }

      /*
       *  process the row
       */
      bufp_mask_in = buf_mask_in + col_start_in * bytes_per_mask;
      bufp_in      = buf_in      + col_start_in * bytes_per_cell;
      bufp_out     = buf_out;
      for (col = col_start_in; col <= last_col_in_region; col++) {

        /*
         *  get the value from mask_file_in
         */

        if (mask_same_as_input) {
          if (byte_swap_input) {

            /*
             *  byte swap the mask
             */
            if (bytes_per_cell == 4) {
              p4 = (byte4 *)bufp_mask_in;
              t4 = *p4;
              t4 = ((t4 >> 24) & 0xff) | ((t4 >> 8) & 0xff00) |
                ((t4 << 8) & 0xff0000) | (t4 << 24);
              *p4 = t4;
            } else {
              p2 = (byte2 *)bufp_mask_in;
              t2 = *p2;
              t2 = ((t2 >> 8) & 0xff) | (t2 << 8);
              *p2 = t2;
            }
          }

          /*
           *  get the mask value
           */
          switch (data_type) {
          case MM_UNSIGNED_CHAR:
            mask = *((byte1 *)bufp_mask_in);
            break;
          case MM_SIGNED_CHAR:
            mask = *((char *)bufp_mask_in);
            break;
          case MM_UNSIGNED_SHORT:
            mask = *((byte2 *)bufp_mask_in);
            break;
          case MM_SIGNED_SHORT:
            mask = *((short *)bufp_mask_in);
            break;
          case MM_UNSIGNED_INT:
            mask = *((byte4 *)bufp_mask_in);
            break;
          case MM_SIGNED_INT:
            mask = *((int *)bufp_mask_in);
            break;
          case MM_FLOAT:
            mask = *((float *)bufp_mask_in);
            break;
          case MM_DOUBLE:
            mask = *((double *)bufp_mask_in);
            break;
          }
          bufp_mask_in += bytes_per_mask;
        } else {
          mask = *bufp_mask_in++;
        }

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
         *  check the input value
         */
        switch (data_type) {
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

        if (mask == mask_value_in)
          mask_test = mask_value_out;
        if (mask_test != mask_value_out)
          got_unmasked = TRUE;

        /*
         *  store the masked value in the output buffer
         */
        switch (data_type) {
        case MM_UNSIGNED_CHAR:
          *((byte1 *)bufp_out) = (byte1)mask_test;
          break;
        case MM_SIGNED_CHAR:
          *((char *)bufp_out) = (char)mask_test;
          break;
        case MM_UNSIGNED_SHORT:
          *((byte2 *)bufp_out) = (byte2)mask_test;
          break;
        case MM_SIGNED_SHORT:
          *((short *)bufp_out) = (short)mask_test;
          break;
        case MM_UNSIGNED_INT:
          *((byte4 *)bufp_out) = (byte4)mask_test;
          break;
        case MM_SIGNED_INT:
          *((int *)bufp_out) = (int)mask_test;
          break;
        case MM_FLOAT:
          *((float *)bufp_out) = (float)mask_test;
          break;
        case MM_DOUBLE:
          *((double *)bufp_out) = mask_test;
          break;
        }
        bufp_out += bytes_per_cell;

        if (byte_swap_output) {

          /*
           *  byte swap the output
           */
          if (bytes_per_cell == 4) {
            p4 = (byte4 *)bufp_out;
            t4 = *p4;
            t4 = ((t4 >> 24) & 0xff) | ((t4 >> 8) & 0xff00) |
                 ((t4 << 8) & 0xff0000) | (t4 << 24);
            *p4 = t4;
          } else {
            p2 = (byte2 *)bufp_out;
            t2 = *p2;
            t2 = ((t2 >> 8) & 0xff) | (t2 << 8);
            *p2 = t2;
          }
        }
        
        if (very_very_verbose)
          fprintf(stderr,
                 "row:%d   col:%d   mask: %lf   mask_test: %lf\n",
                  row, col, mask, mask_test);

      }

      /*
       *     write the output buffer
       */
      if (very_very_verbose)
        fprintf(stderr, "writing buffer to %s\n", file_out);

      if (write(fd_out, buf_out,
                bytes_per_row_out) != bytes_per_row_out) {
        fprintf(stderr, "error writing %s\n", file_out);
        perror("apply_mask");
        there_were_errors = TRUE;
        break;
      }
    }
    break;
  }

  /*
   *      close input and output files
   */
  if (fd_out >= 0)
    close(fd_out);
  if (fd_in >= 0)
    close(fd_in);
  if (fd_mask_in >= 0)
    close(fd_mask_in);

  /*
   *      Deallocate buffers
   */
  if (buf_mask_in)
    free(buf_mask_in);
  if (buf_in)
    free(buf_in);
  if (buf_out)
    free(buf_out);

  if (delete_if_all_masked && !got_unmasked) {

    /*
     *  delete the output file since there were no unmasked output values
     */
    if (verbose)
      fprintf(stderr, "apply_mask: deleting %s\n", file_out);
    sprintf(command, "rm -f %s", file_out);
    system(command);
  }

  if (very_verbose) {
    if (there_were_errors)
      fprintf(stderr, "apply_mask: done, but there were errors\n");
    else
      fprintf(stderr, "apply_mask: done, ok\n");
  }

  return (there_were_errors ? EXIT_FAILURE : EXIT_SUCCESS);
}
