/*========================================================================
 * cdb_list - list segment index of cdb file
 *========================================================================*/
#include <stdio.h>
#include <math.h>
#include <define.h>
#include <cdb.h>

#define usage "usage: cdb_list [-v] file.cdb ... \n"
main(int argc, char *argv[])
{
  register int i;
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
}


