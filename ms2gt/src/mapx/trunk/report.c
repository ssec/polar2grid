/*******************************************************************************
NAME                    Projection support routines listed below

PURPOSE:	The following functions are included in REPORT.C	

		INIT:
			Initializes the output device for error messages and
		  	report headings.

		P_ERROR:
			Reports errors to the terminal, a specified file, or
			both.

		PTITLE, RADIUS, RADIUS2, CENLON, CENLONMER, CENLAT, ORIGIN,
		STANPARL, STPARL1, OFFSET, GENRPT, GENRPT_LONG, PBLANK:
			Reports projection parameters to the terminal,
			specified file, or both. 


PROGRAMMER              DATE		REASON
----------              ----		------
D. Steinwand, EROS      July, 1991	Initial development.
T. Mittan		Mar,  1993	Adapted code to new "C" version of
					GCTP library.
S. Nelson		Jun, 1993	Added inline code. 
					Added error messages if no filename
					was specified.
S. Nelson		Jan, 1998	Returned OK instead of 0.

*******************************************************************************/
#include <stdio.h>
#include <string.h>
#include "cproj.h"

#define TRUE 1
#define FALSE 0

static long terminal_p;		/* flag for printing parameters to terminal */
static long terminal_e;		/* flag for printing errors to terminal */
static long file_p;		/* flag for printing parameters to file */
static long file_e;		/* flag for printing errors to terminal */
static FILE  *fptr_p;
static FILE  *fptr_e;
static char parm_file[256];
static char err_file[256];

/* initialize output device
-------------------------*/
long init
(
    long ipr,		/* flag for printing errors (0,1,or 2)		*/
    long jpr,		/* flag for printing parameters (0,1,or 2)	*/
    char *efile,	/* name of error file				*/
    char *pfile		/* name of parameter file			*/
)

{
if (ipr == 0)
   {
   terminal_e = TRUE;
   file_e = FALSE;
   }
else if (ipr == 1)
   {
   terminal_e = FALSE;
   if (strlen(efile) == 0)
      {
      return(6);
      }
   file_e = TRUE;
   strcpy(err_file,efile);
   }
else if (ipr == 2)
   {
   terminal_e = TRUE;
   if (strlen(efile) == 0)
      {
      file_e = FALSE;
      p_error("Output file name not specified","report-file");
      return(6);
      }
   file_e = TRUE;
   strcpy(err_file,efile);
   }
else
   {
   terminal_e = FALSE;
   file_e = FALSE;
   }

if (jpr == 0)
   {
   terminal_p = TRUE;
   file_p = FALSE;
   }
else if (jpr == 1)
   {
   terminal_p = FALSE;
   if (strlen(pfile) == 0)
      {
      return(6);
      }
   file_p = TRUE;
   strcpy(parm_file,pfile);
   }
else if (jpr == 2)
   {
   terminal_p = TRUE;
   if (strlen(pfile) == 0)
      {
      file_p = FALSE;
      p_error("Output file name not specified","report-file");
      return(6);
      }
   file_p = TRUE;
   strcpy(parm_file,pfile);
   }
else
   {
   terminal_p = FALSE;
   file_p = FALSE;
   }
return(OK);
}


/* Functions to report projection parameters
  -----------------------------------------*/
void ptitle
(
    char *A
) 
      {  
      if (terminal_p)
           printf("\n%s PROJECTION PARAMETERS:\n\n",A); 
      if (file_p)
	   {
           fptr_p = (FILE *)fopen(parm_file,"a");
           fprintf(fptr_p,"\n%s PROJECTION PARAMETERS:\n\n",A); 
	   fclose(fptr_p);
	   }
      }

void radius
(
    double A
)
      {
      if (terminal_p)
         printf("   Radius of Sphere:     %f meters\n",A); 
      if (file_p)
	 {
         fptr_p = (FILE *)fopen(parm_file,"a");
         fprintf(fptr_p,"   Radius of Sphere:     %f meters\n",A); 
	 fclose(fptr_p);
	 }
      }

void radius2
(
    double A,
    double B
)
      {
      if (terminal_p)
         {
         printf("   Semi-Major Axis of Ellipsoid:     %f meters\n",A);
         printf("   Semi-Minor Axis of Ellipsoid:     %f meters\n",B);
         }
      if (file_p)
         {
         fptr_p = (FILE *)fopen(parm_file,"a");
         fprintf(fptr_p,"   Semi-Major Axis of Ellipsoid:     %f meters\n",A);
         fprintf(fptr_p,"   Semi-Minor Axis of Ellipsoid:     %f meters\n",B); 
	 fclose(fptr_p);
         }
      }

void cenlon
(
    double A
)
   { 
   if (terminal_p)
       printf("   Longitude of Center:     %f degrees\n",A*R2D);
   if (file_p)
       {
       fptr_p = (FILE *)fopen(parm_file,"a");
       fprintf(fptr_p,"   Longitude of Center:     %f degrees\n",A*R2D);
       fclose(fptr_p);
       }
   }
 
void cenlonmer
(
    double A
)
   { 
   if (terminal_p)
     printf("   Longitude of Central Meridian:     %f degrees\n",A*R2D);
   if (file_p)
     {
     fptr_p = (FILE *)fopen(parm_file,"a");
    fprintf(fptr_p,"   Longitude of Central Meridian:     %f degrees\n",A*R2D);
     fclose(fptr_p);
     }
   }

void cenlat
(
    double A
)
   {
   if (terminal_p)
      printf("   Latitude  of Center:     %f degrees\n",A*R2D);
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   Latitude of Center:     %f degrees\n",A*R2D);
      fclose(fptr_p);
      }
   }

void origin
(
    double A
)
   {
   if (terminal_p)
      printf("   Latitude of Origin:     %f degrees\n",A*R2D);
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   Latitude  of Origin:     %f degrees\n",A*R2D);
      fclose(fptr_p);
      }
   }
void stanparl
(
    double A,
    double B
)
   {
   if (terminal_p)
      {
      printf("   1st Standard Parallel:     %f degrees\n",A*R2D);
      printf("   2nd Standard Parallel:     %f degrees\n",B*R2D);
      }
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   1st Standard Parallel:     %f degrees\n",A*R2D);
      fprintf(fptr_p,"   2nd Standard Parallel:     %f degrees\n",B*R2D);
      fclose(fptr_p);
      }
   }

void stparl1
(
    double A
)
   {
   if (terminal_p)
      {
      printf("   Standard Parallel:     %f degrees\n",A*R2D);
      }
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   Standard Parallel:     %f degrees\n",A*R2D);
      fclose(fptr_p);
      }
   }

void offsetp
(
    double A,
    double B
)
   {
   if (terminal_p)
      {
      printf("   False Easting:      %f meters \n",A);
      printf("   False Northing:     %f meters \n",B);
      }
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   False Easting:      %f meters \n",A);
      fprintf(fptr_p,"   False Northing:     %f meters \n",B);
      fclose(fptr_p);
      }      
   }

void genrpt
(
    double A,
    char *S
)
   {
   if (terminal_p)
      printf("   %s %f\n", S, A);
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   %s %f\n", S, A);
      fclose(fptr_p);
      }
   }
void genrpt_long
(
    long A,
    char *S
)
   {
   if (terminal_p)
      printf("   %s %ld\n", S, A);
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"   %s %ld\n", S, A);
      fclose(fptr_p);
      }
   }
void pblank
(void) 
   {
   if (terminal_p)
      printf("\n");
   if (file_p)
      {
      fptr_p = (FILE *)fopen(parm_file,"a");
      fprintf(fptr_p,"\n");
      fclose(fptr_p);
      }
   }

/* Function to report errors 
  -------------------------*/
void p_error
(
    char *what,
    char *where
) 
   {
   if (terminal_e)
      printf("[%s] %s\n",where,what);
   if (file_e)
      {
      fptr_e = (FILE *)fopen(err_file,"a");
      fprintf(fptr_e,"[%s] %s\n",where,what);
      fclose(fptr_e);
      }
   }
