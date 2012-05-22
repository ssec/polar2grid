/*========================================================================
 * cdb_list - list segment index of cdb file
 *
 *  7-Apr-1993 R.Swick swick@kryos.colorado.edu  303-492-6069  
 *  National Snow & Ice Data Center, University of Colorado, Boulder
 *  Copyright (C) 1993 University of Colorado
 *========================================================================*/
static const char cdb_list_c_rcsid[] = "$Id: cdb_list.c 16072 2010-01-30 19:39:09Z brodzik $";

#include <stdio.h>
#include <math.h>
#include <define.h>
#include <cdb.h>

#define usage "usage: cdb_list [-v] file.cdb ... \n"

int main(int argc, char *argv[])
{
  register char *option;
  cdb_class *this;
  int verbose = FALSE;

/*
 *	get command line options
 */
  while (--argc > 0 && (*++argv)[0] == '-')
  { for (option = argv[0]+1; *option != '\0'; option++)
    { switch (*option)
      { case 'v':
	  verbose = TRUE;
	  break;
	case 'V':
	  fprintf(stderr,"%s\n", cdb_list_c_rcsid);
	  break;
	default:
	  fprintf(stderr, "invalid option %c\n", *option);
	  error_exit(usage);
      }
    }
  }

/*
 *	process command line arguments
 */
  if (argc < 1) error_exit(usage);

  for (; argc > 0; --argc, ++argv)
  { this = init_cdb(*argv);
    if (this == NULL) continue;
    list_cdb(this, verbose);
    free_cdb(this);
  }

  exit(EXIT_SUCCESS);
}


