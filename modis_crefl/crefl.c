/*
Linux
  cc -O crefl.c -o crefl -I$HDFINC -L$HDFLIB -lmfhdf -ldf -lz -lm -ljpeg
*/

/*************************************************************************
Description:

  Simplified atmospheric correction algorithm that transforms MODIS
  top-of-the-atmosphere level-1B radiance data into corrected reflectance
  for Rapid Response applications.
  Required ancillary data: coarse resolution DEM tbase.hdf

References and Credits:

  Jacques Descloitres, MODIS Rapid Response Project, NASA/GSFC/SSAI
  http://rapidfire.sci.gsfc.nasa.gov

Revision history:

  Version 1.0   08/24/01
  Version 1.1   01/25/02
  Version 1.2   05/30/02
  Version 1.3   09/06/02
  Version 1.4   09/02/03
  Version 1.4.1 01/22/04
  Version 1.5   02/17/04
  Version 1.5.1 03/08/07 (not run in RR production)
  Version 1.5.2 06/07/07
  Version 1.6   08/18/09 (Be sure to update PROCESS_VERSION_NUMBER also)
                         Started with Version 1.5.2, version run in Rapid Response for several years,
                         this had several differences from 1.4.2, the DRL version, including the addition
                         of band 8 and a number of small, but perhaps important, computational changes
                         1) removed most code within #ifdef DEBUG clauses
                         2) left command line options for nearest, TOA, and sealevel; note that these options
                            were in Version 1.4.2 but were not available from the command line
                         3) changes by DRL to 1.4.2 to write scale factor and offset has already been 
                            incorporated into 1.5.2
                         4) Added in the modifications from Chuanmin Hu & Brock Murch of Univ South Florida
                            IMaRS to add bands 9-16.  The aO3 and taur0 parameters came "from SeaDAS codes"
                            and "The H2O parameters can be assumed 0 for bands 8-16 because those bands were
                            designed to avoid water vapor absorption."
                         Disclaimer: the nearest, TOA, and sealevel options and bands 9-16 are not used
                                     by Rapid Response so I cannot consider them tested/validated - JES

*************************************************************************/

#define PROCESS_VERSION_NUMBER "1.7.1"

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <getopt.h>
#include "mfhdf.h"

// Copied from hdf4compat.h from GDAL formats (https://trac.osgeo.org/gdal/browser/trunk/gdal/frmts/hdf4/hdf4compat.h)
#ifndef H4_MAX_VAR_DIMS
#define H4_MAX_VAR_DIMS MAX_VAR_DIMS
#endif
#ifndef H4_MAX_NC_DIMS
#define H4_MAX_NC_DIMS MAX_NC_DIMS
#endif
#ifndef H4_MAX_NC_NAME
#define H4_MAX_NC_NAME MAX_NC_NAME
#endif

#define MAXNAMELENGTH 200
#define Nbands 16
#define DEG2RAD	0.0174532925199		/* PI/180 */
#define UO3	0.319
#define UH2O	2.93
#define REFLMIN -0.01
#define REFLMAX  1.6
#define ANCPATH		"."
#define DEMFILENAME	"tbase.hdf"
#define DEMSDSNAME	"Elevation"
#define REFSDS	SOLZ
#define MISSING	-2
#define SATURATED	-3
#define CANTAGGR	-8
#define MAXSOLZ 86.5
#define MAXAIRMASS 18
#define	SCALEHEIGHT 8000
#define FILL_INT16	32767
#define	NUM1KMCOLPERSCAN	1354
#define	NUM1KMROWPERSCAN	10
#define	TAUSTEP4SPHALB		0.0001
#define MAXNUMSPHALBVALUES	4000		/* with no aerosol taur <= 0.4 in all bands everywhere */


typedef struct {
  char *name, *filename;
  int32 file_id, id, index, num_type, rank, n_attr, Nl, Np, *plane, Nplanes, rowsperscan;
  int32 start[H4_MAX_VAR_DIMS], edges[H4_MAX_VAR_DIMS], dim_sizes[H4_MAX_VAR_DIMS];
  void *data, *fillvalue;
  float64 factor, offset;
} SDS;



enum {BAND1, BAND2, BAND3, BAND4, BAND5, BAND6, BAND7, BAND8, BAND9, BAND10,
	BAND11, BAND12, BAND13, BAND14, BAND15, BAND16, SOLZ, SENZ, SOLA, SENA,
	LON, LAT, Nitems};

enum {INPUT_1KM, INPUT_500M, INPUT_250M, INPUT_UNKNOWN};



void usage(void);
int input_file_type(char *file);
int parse_bands(char *bandstr, unsigned char process[Nbands]);
int range_check(float x, float xmin, float xmax);

void set_dimnames(int samples, char **dimname1, char **dimname2);

int init_output_sds(int32 sd_id, unsigned char *process, SDS outsds[Nbands], SDS sds[Nitems],
	int gzip, int verbose);
int write_scan(int iscan, unsigned char *process, SDS outsds[Nbands]);
int read_scan(int iscan, SDS sds[Nitems]);
int write_global_attributes(int32 sd_id, char *MOD021KMfile,
	char *MOD02HKMfile, char *MOD02QKMfile, float maxsolz,
	int sealevel, int TOA, int nearest);

int getatmvariables(float mus, float muv, float phi, int16 height,
	unsigned char *process, float *sphalb, float *rhoray, float *TtotraytH2O, float *tOG);
void chand(float phi, float muv, float mus, float *tau, float *rhoray, float *trup,
	float *trdown, unsigned char *process);
float csalbr(float tau);
double fintexp1(float tau);
double fintexp3(float tau);
float correctedrefl(float refl, float TtotraytH2O, float tOG, float rhoray, float sphalb);
int interp_dem(float lat, float lon, SDS *dem);




int main(int argc, char *argv[])
{
	char *MOD021KMfile, *MOD02HKMfile, *MOD02QKMfile;
	char *filename;	/* output file */

	FILE *fp;
	int outfile_exists;

	char *ancpath;
	SDS sds[Nitems], outsds[Nbands], dem, height;
	int32 MOD02QKMfile_id, MOD02HKMfile_id, MOD021KMfile_id;
	int32 sd_id, attr_index, count, num_type;

	int ib, j, iscan, Nscans, irow, jcol, idx, crsidx;
	int nbands;

	char *SDSlocatorQKM[Nitems] = {"EV_250_RefSB", "EV_250_RefSB",
		"EV_500_RefSB", "EV_500_RefSB", "EV_500_RefSB",
		"EV_500_RefSB", "EV_500_RefSB","EV_1KM_RefSB", "EV_1KM_RefSB",
		"EV_1KM_RefSB", "EV_1KM_RefSB", "EV_1KM_RefSB", "EV_1KM_RefSB",
		"EV_1KM_RefSB", "EV_1KM_RefSB", "EV_1KM_RefSB", "SolarZenith",
		"SensorZenith", "SolarAzimuth", "SensorAzimuth", "Longitude",
		"Latitude"};

	char *SDSlocatorHKM[Nitems] = {"EV_250_Aggr500_RefSB",
		"EV_250_Aggr500_RefSB", "EV_500_RefSB", "EV_500_RefSB",
		"EV_500_RefSB", "EV_500_RefSB", "EV_500_RefSB",
		"EV_1KM_RefSB","EV_1KM_RefSB","EV_1KM_RefSB",
		"EV_1KM_RefSB","EV_1KM_RefSB","EV_1KM_RefSB", "EV_1KM_RefSB",
		"EV_1KM_RefSB", "EV_1KM_RefSB", "SolarZenith",
		"SensorZenith", "SolarAzimuth", "SensorAzimuth", "Longitude",
		"Latitude"};

	char *SDSlocator1KM[Nitems] = {"EV_250_Aggr1km_RefSB",
		"EV_250_Aggr1km_RefSB", "EV_500_Aggr1km_RefSB",
		"EV_500_Aggr1km_RefSB", "EV_500_Aggr1km_RefSB",
		"EV_500_Aggr1km_RefSB",  "EV_500_Aggr1km_RefSB",
		"EV_1KM_RefSB", "EV_1KM_RefSB", "EV_1KM_RefSB", "EV_1KM_RefSB",
		"EV_1KM_RefSB", "EV_1KM_RefSB",
		"EV_1KM_RefSB", "EV_1KM_RefSB", "EV_1KM_RefSB", "SolarZenith",
		"SensorZenith", "SolarAzimuth", "SensorAzimuth", "Longitude",
		"Latitude"};

	char indexlocator[Nitems] = {0, 1, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 5, 7,
		9, 10, 0, 0, 0, 0, 0, 0};

	char numtypelocator[Nitems] = {DFNT_UINT16, DFNT_UINT16, DFNT_UINT16,
		DFNT_UINT16, DFNT_UINT16, DFNT_UINT16, DFNT_UINT16,
		DFNT_UINT16, DFNT_UINT16, DFNT_UINT16, DFNT_UINT16,
		DFNT_UINT16, DFNT_UINT16, DFNT_UINT16, DFNT_UINT16,
		DFNT_UINT16, DFNT_INT16, DFNT_INT16, DFNT_INT16, DFNT_INT16,
		DFNT_FLOAT32, DFNT_FLOAT32};

	int16 *l1bdata[Nbands], *sola, *solz, *sena, *senz, *solzfill;
	float32 *lon, *lat, *lonfill, *latfill;
	char *attr_name;
	float64 scale_factor[Nitems], add_offset[Nitems];

	unsigned char process[Nbands];

	float refl, *mus, muv, phi;
	float *rhoray, *sphalb, *TtotraytH2O, *tOG;
	int aggfactor, crsrow1, crsrow2, crscol1, crscol2;
	int crsidx11, crsidx12, crsidx21, crsidx22;
	float mus0, mus11, mus12, mus21, mus22;
	float fractrow, fractcol, t, u;
	float rhoray0, rhoray11, rhoray12, rhoray21, rhoray22;
	float sphalb0, sphalb11, sphalb12, sphalb21, sphalb22;
	float reflmin=REFLMIN, reflmax=REFLMAX, maxsolz=MAXSOLZ;
	int bad;

	int write_mode = DFACC_CREATE;

	int st;

	size_t nbytes;

	int ftype;

	extern char *optarg;
	extern int optind, opterr;
	int option_index = 0;

	static int verbose, overwrite;
	static int gzip, append;

	static int output500m, output1km;
	static int sealevel, TOA, nearest;

	char dummy[H4_MAX_NC_NAME];

	enum{OPT_BANDS = 1, OPT_RANGE, OPT_OUTFILE, OPT_MAXSOLZ};

	static struct option long_options[] = {
		{"1km",		no_argument,		&output1km, 1},
		{"500m",	no_argument,		&output500m, 1},
		{"append",	no_argument,		&append, 1},
		{"bands",	required_argument,	(int *) NULL, OPT_BANDS},
		{"gzip",	no_argument,		&gzip,	1},
		{"maxsolz",	required_argument,	(int *) NULL, OPT_MAXSOLZ},
		{"nearest",	no_argument,		&nearest, 1},
		{"of",		required_argument,	(int *) NULL, OPT_OUTFILE},
		{"overwrite",	no_argument,		&overwrite, 1},
		{"range",	required_argument,	(int *) NULL, OPT_RANGE},
		{"sealevel",	no_argument,		&sealevel, 1},
		{"toa",		no_argument,		&TOA, 1},
		{"verbose",	no_argument,		&verbose, 1},
		{(char *) NULL, 0, (int *) NULL, 0}
		};

	int c;

	static char dem_filename_buff[MAXNAMELENGTH];


	MOD021KMfile = MOD02HKMfile = MOD02QKMfile = (char *) NULL;
	filename = (char *) NULL;

	for (ib = 0; ib < Nbands; ib++) process[ib] = FALSE;

	/* default settings */
	output500m = output1km = 0;
	append = gzip = nearest = sealevel = TOA = verbose = overwrite = 0;


	while ((c = getopt_long(argc, argv, "", long_options,
		&option_index)) >= 0) {

		switch (c) {
			case 0:
				/* do nothing for options which will have a
				flag set automatically by getopt_long() */
				break;

			case OPT_BANDS:
				if (parse_bands(optarg, process)) {
					fputs("Invalid band(s) specified.\n",
						stderr);
					exit(1);
					}
				break;

			case OPT_RANGE:
				if (sscanf(optarg, "%g,%g", &reflmin, &reflmax) != 2) {
					fputs("Error parsing reflectance range.\n", stderr);
					exit(1);
					}

				if ( range_check(reflmin, 0.0F, 1.0F) ||
					range_check(reflmax, 0.0F, 1.0F) ||
					(reflmin >= reflmax) ) {
					fputs("Invalid reflectance range.\n", stderr);
					exit(1);
					}

				printf("Output reflectance range [%.3f,%.3f] requested.\n",
					reflmin, reflmax);
				break;

			case OPT_MAXSOLZ:
				maxsolz = (float) atof(optarg);
				if (range_check(maxsolz, 0.0F, 90.0F)) {
					fputs("Invalid max. solar zenith angle.\n", stderr);
					exit(1);
					}
				break;

			case OPT_OUTFILE:
				filename = optarg;
				break;

			default:
				usage();
				exit(1);
			}
		}

	if (append) write_mode = DFACC_RDWR;

	/* at least one input file must follow */
	if (optind >= argc) {
		usage();
		exit(1);
		}


	/* check for conflicting options */
	if (overwrite && append) {
		fputs("Options --overwrite and --append are mutually exclusive.\n",
			stderr);
		exit(1);
		}
	if (sealevel && TOA) {
		fputs("Options --sealevel and --toa are mutually exclusive.\n",
			stderr);
		exit(1);
		}

#ifdef DEBUG
printf("append = %d\n", append);
if (filename) printf("output filename = %s\n", filename);
printf("output1km = %d\n", (int) output1km);
printf("output500m = %d\n", (int) output500m);
printf("gzip = %d\n", gzip);
printf("nearest = %d\n", nearest);
printf("sealevel = %d\n", sealevel);
printf("TOA = %d\n", TOA);
printf("Max. solar zenith angle: %g degrees\n", maxsolz);
if (filename) printf("Output file: %s.", filename);
#endif



	if (verbose) puts("Verbose mode requested.");
	if (overwrite) puts("Overwriting existing output file.");
	if (gzip) puts("Gzip compression requested.");
	if (sealevel) puts("Sea-level atmospheric correction requested. Terrain height ignored.");
	if (TOA) puts("Top-of-the-atmosphere reflectance requested. No atmospheric correction.");
	if (output1km) puts("1km-resolution output requested.");
	if (nearest) puts("Interpolation disabled.");



	/* parse input file names */
	for (j = optind; j < argc; j++) {
		ftype = input_file_type(argv[j]);

		switch (ftype) {
			case INPUT_1KM:
				MOD021KMfile = argv[j];
				break;

			case INPUT_500M:
				MOD02HKMfile = argv[j];
				break;

			case INPUT_250M:
				MOD02QKMfile = argv[j];
				break;

			default:
				fprintf(stderr,
					"Unrecognized input file \"%s\".\n",
					argv[j]);
				exit(1);
				break;
			}
		}



	if (verbose && MOD021KMfile)
		printf("Input geolocation file: %s\n", MOD021KMfile);


	/* output file name is mandatory */
	if (!filename) {
		fputs("Missing output file name.\n", stderr);
		exit(1);
		}

#ifdef DEBUG
if (MOD021KMfile) printf("MOD/MYD021KMfile = %s\n", MOD021KMfile);
if (MOD02HKMfile) printf("MOD/MYD02HKMfile = %s\n", MOD02HKMfile);
if (MOD02QKMfile) printf("MOD/MYD02QKMfile = %s\n", MOD02QKMfile);
#endif


	/*
	1KM file is mandatory for angles.
	HKM file is mandatory unless 1-km output is requested.
	QKM file is mandatory unless 500-m or 1-km output is requested.
	*/
	if ( (!MOD021KMfile) ||
		(!MOD02HKMfile && !output1km) ||
		(!MOD02QKMfile && !output500m && !output1km) ) {
		fputs("Invalid combination of input files.\n", stderr);
		exit(1);
		}


	/* count number of bands to process */
	for (ib = nbands = 0; ib < Nbands; ib++) if (process[ib]) nbands++;
	if (nbands < 1) {
		process[BAND1] = process[BAND3] = process[BAND4] = TRUE;
		if (verbose)
			puts("No band(s) specified.  Default is bands 1, 3, and 4.");
		}


	/* open input files */
  if ( MOD02QKMfile && (!output500m)  &&
       !output1km &&
       (MOD02QKMfile_id = SDstart(MOD02QKMfile, DFACC_READ)) == -1 ) {
    fprintf(stderr, "Cannot open input file %s.\n", MOD02QKMfile);
    exit(1);
  }
  if ( MOD02HKMfile && (!output1km) &&
       (MOD02HKMfile_id = SDstart(MOD02HKMfile, DFACC_READ)) == -1 ) {
    fprintf(stderr, "Cannot open input file %s.\n", MOD02HKMfile);
    exit(1);
  }
  if ( MOD021KMfile &&
       (MOD021KMfile_id = SDstart(MOD021KMfile, DFACC_READ)) == -1 ) {
    fprintf(stderr, "Cannot open input file %s.\n", MOD021KMfile);
    exit(1);
  }


	if (!sealevel && !TOA) {
		dem.filename = dem_filename_buff;

		if ((ancpath = getenv("ANCPATH")) == NULL)
			sprintf(dem.filename, "%s/%s", ANCPATH, DEMFILENAME);
		else
			sprintf(dem.filename, "%s/%s", ancpath, DEMFILENAME);

		if ( (dem.file_id = SDstart(dem.filename, DFACC_READ)) == -1 ) {
			fprintf(stderr, "Cannot open file %s.\n", dem.filename);
			exit(1);
			}
		}


	if ( (fp = fopen(filename, "r")) ) {
		(void) fclose(fp);
		outfile_exists = 1;
		}
	else
		outfile_exists = 0;

	if ((write_mode == DFACC_CREATE)  &&  !overwrite  && outfile_exists) {
		fprintf(stderr, "File \"%s\" already exits.\n", filename);
		exit(1);
		}

	if (output500m) {
		sds[BAND1].file_id = sds[BAND2].file_id = MOD02HKMfile_id;
		sds[BAND1].filename = sds[BAND2].filename = MOD02HKMfile;
		}
	else {
		if (output1km) {
			sds[BAND1].file_id = sds[BAND2].file_id = MOD021KMfile_id;
			sds[BAND1].filename = sds[BAND2].filename = MOD021KMfile;
			}
		else {
			sds[BAND1].file_id = sds[BAND2].file_id = MOD02QKMfile_id;
			sds[BAND1].filename = sds[BAND2].filename = MOD02QKMfile;
			}
		}

	if (output1km) {
		sds[BAND3].file_id = sds[BAND4].file_id =
			sds[BAND5].file_id = sds[BAND6].file_id =
			sds[BAND7].file_id = MOD021KMfile_id;
		sds[BAND3].filename = sds[BAND4].filename =
			sds[BAND5].filename = sds[BAND6].filename =
			sds[BAND7].filename = MOD021KMfile;
		}
	else {
		sds[BAND3].file_id = sds[BAND4].file_id =
			sds[BAND5].file_id = sds[BAND6].file_id =
			sds[BAND7].file_id = MOD02HKMfile_id;
		sds[BAND3].filename = sds[BAND4].filename =
			sds[BAND5].filename = sds[BAND6].filename =
			sds[BAND7].filename = MOD02HKMfile;
		}

	sds[BAND8].file_id = sds[SOLZ].file_id = sds[SOLA].file_id =
		sds[SENZ].file_id = sds[SENA].file_id = sds[LON].file_id =
		sds[LAT].file_id = MOD021KMfile_id;
	sds[BAND8].filename = sds[SOLZ].filename = sds[SOLA].filename =
		sds[SENZ].filename = sds[SENA].filename = sds[LON].filename =
		sds[LAT].filename = MOD021KMfile;

	sds[BAND9].file_id = sds[BAND10].file_id = sds[BAND11].file_id =
		sds[BAND12].file_id = sds[BAND13].file_id =
		sds[BAND14].file_id = sds[BAND15].file_id =
		sds[BAND16].file_id = MOD021KMfile_id;
	sds[BAND9].filename = sds[BAND10].filename = sds[BAND11].filename =
		sds[BAND12].filename = sds[BAND13].filename =
		sds[BAND14].filename = sds[BAND15].filename =
		sds[BAND16].filename = MOD021KMfile;

  for (ib=0; ib < Nitems; ib++) {
	/* initializing these fields will simplify releasing memory later */
	sds[ib].data = sds[ib].fillvalue = (void *) NULL;

    if ( ib < Nbands  &&
         ! process[ib] ) {
      sds[ib].id = -1;
      continue;
    }
    if (output500m)
      sds[ib].name = SDSlocatorHKM[ib];
    else if (output1km)
      sds[ib].name = SDSlocator1KM[ib];
    else
      sds[ib].name = SDSlocatorQKM[ib];

    if ( (sds[ib].index = SDnametoindex(sds[ib].file_id, sds[ib].name)) == -1 ) {
      fprintf(stderr, "Cannot find SDS %s in file %s.\n", sds[ib].name, sds[ib].filename);
      continue;
    }
    if ( (sds[ib].id = SDselect(sds[ib].file_id, sds[ib].index)) == -1 ) {
      fprintf(stderr, "Cannot select SDS no. %d\n", sds[ib].index);
      if (ib < Nbands)
        process[ib] = FALSE;
      continue;
    }

    /*
    Original code passed sds[ib].name as destination for SDS name in call to SDgetinfo().
    This was causing a core dump, apparently because SDgetinfo() writes some additional
    characters beyond the terminating null at the end of the SDS name, so I replaced
    the argument with a dummy character array.
    */
    if (SDgetinfo(sds[ib].id, dummy, &sds[ib].rank, sds[ib].dim_sizes, &sds[ib].num_type, &sds[ib].n_attr) == -1) {
      fprintf(stderr, "Can't get info from SDS \"%s\" in file %s.\n", sds[ib].name, sds[ib].filename);
      SDendaccess(sds[ib].id);
      sds[ib].id = -1;
      if (ib < Nbands)
        process[ib] = FALSE;
      continue;
    }


    sds[ib].factor = 1;
    attr_name = "reflectance_scales";
    if ( (attr_index = SDfindattr(sds[ib].id, attr_name)) != -1  &&
         SDattrinfo(sds[ib].id, attr_index, dummy, &num_type, &count) != -1  &&
         SDreadattr(sds[ib].id, attr_index, scale_factor) != -1 )
      sds[ib].factor = ((float32 *)scale_factor)[indexlocator[ib]];
    else {
	attr_name = "scale_factor";
	if ((attr_index = SDfindattr(sds[ib].id, attr_name)) != -1  &&
		SDattrinfo(sds[ib].id, attr_index, dummy, &num_type, &count) != -1  &&
		SDreadattr(sds[ib].id, attr_index, scale_factor) != -1 )
		sds[ib].factor = *scale_factor;
	}

    sds[ib].offset = 0;
    attr_name = "reflectance_offsets";
    if ( (attr_index = SDfindattr(sds[ib].id, attr_name)) != -1  &&
         SDattrinfo(sds[ib].id, attr_index, dummy, &num_type, &count) != -1  &&
         SDreadattr(sds[ib].id, attr_index, add_offset) != -1 )
      sds[ib].offset = ((float32 *)add_offset)[indexlocator[ib]];
    else {
	attr_name = "add_offset";
	if ( (attr_index = SDfindattr(sds[ib].id, attr_name)) != -1  &&
		SDattrinfo(sds[ib].id, attr_index, dummy, &num_type, &count) != -1  &&
		SDreadattr(sds[ib].id, attr_index, add_offset) != -1 )
		sds[ib].offset = *add_offset;
	}


    sds[ib].fillvalue = (void *) malloc(1 * DFKNTsize(sds[ib].num_type));
    if ( SDgetfillvalue(sds[ib].id, sds[ib].fillvalue) != 0 ) {
      fprintf(stderr, "Cannot read fill value of SDS \"%s\".\n", sds[ib].name);
      exit(1);
    }

    switch (sds[ib].rank) {
      case 2:
        sds[ib].Nl = sds[ib].dim_sizes[0];
        sds[ib].Np = sds[ib].dim_sizes[1];
        sds[ib].rowsperscan = (int)(NUM1KMROWPERSCAN * sds[ib].Np / (float)NUM1KMCOLPERSCAN + 0.5);
        sds[ib].start[1] = 0;
        sds[ib].edges[0] = sds[ib].rowsperscan;
        sds[ib].edges[1] = sds[ib].Np;
        break;
      case 3:
        sds[ib].Nl = sds[ib].dim_sizes[1];
        sds[ib].Np = sds[ib].dim_sizes[2];
        sds[ib].rowsperscan = (int)(NUM1KMROWPERSCAN * sds[ib].Np / (float)NUM1KMCOLPERSCAN + 0.5);
        sds[ib].start[0] = indexlocator[ib];
        sds[ib].start[2] = 0;
        sds[ib].edges[0] = 1;
        sds[ib].edges[1] = sds[ib].rowsperscan;
        sds[ib].edges[2] = sds[ib].Np;
        break;
      default:
        fprintf(stderr, "SDS rank must be 2 or 3.\n");
        continue;
    }
    if (verbose)
      printf("SDS \"%s\": %dx%d   scale factor: %g  offset: %g\n", sds[ib].name, sds[ib].Np, sds[ib].Nl, sds[ib].factor, sds[ib].offset);
    if (sds[ib].num_type != numtypelocator[ib]) {
      fprintf(stderr, "SDS \"%s\" has not the expected data type.\n", sds[ib].name);
      exit(-1);
    }
    sds[ib].data = malloc(sds[ib].Np * sds[ib].rowsperscan * DFKNTsize(sds[ib].num_type));
    if (!sds[ib].data) {
      (void) fputs("Error allocating memory.\n", stderr);
      exit(1);
      }
  }

	if (sealevel || TOA) {
		dem.id = -1;
		dem.Nl = dem.Np = 0;
		}
	else {
		/* dem.name = strdup(DEMSDSNAME); */
		dem.name = DEMSDSNAME;

		if ( (dem.index = SDnametoindex(dem.file_id, dem.name)) == -1 ) {
			fprintf(stderr, "Cannot find SDS %s in file %s.\n", dem.name, dem.filename);
			exit(1);
			}

		if ( (dem.id = SDselect(dem.file_id, dem.index)) == -1 ) {
			fprintf(stderr, "Cannot select SDS no. %d\n", dem.index);
			exit(1);
			}
		if (SDgetinfo(dem.id, dummy, &dem.rank, dem.dim_sizes, &dem.num_type, &dem.n_attr) == -1) {
			fprintf(stderr, "Can't get info from SDS \"%s\" in file %s.\n", dem.name, dem.filename);
			SDendaccess(dem.id);
			exit(1);
			}

		dem.Nl = dem.dim_sizes[0];
		dem.Np = dem.dim_sizes[1];
		dem.rowsperscan = (int)(NUM1KMROWPERSCAN * dem.Np / (float)NUM1KMCOLPERSCAN + 0.5);
		}

  if ( sds[SOLZ].id == -1 ||
       sds[SOLA].id == -1 ||
       sds[SENZ].id == -1 ||
       sds[SENA].id == -1 ||
       sds[LON].id == -1 ||
       sds[LAT].id == -1 ||
       ((dem.id == -1) && !sealevel && !TOA) ) {
    fprintf(stderr, "Solar and Sensor angles and DEM are necessary to process granule.\n");
    exit(1);
  }

  if ( sds[REFSDS].Np != sds[SOLZ].Np ||
       sds[REFSDS].Np != sds[SOLA].Np ||
       sds[REFSDS].Np != sds[SENZ].Np ||
       sds[REFSDS].Np != sds[SENA].Np ||
       sds[REFSDS].Np != sds[LON].Np ||
       sds[REFSDS].Np != sds[LAT].Np ) {
    fprintf(stderr, "Solar and Sensor angles must have identical dimensions.\n");
    exit(1);
  }

	ib = 0;
	while (sds[ib].id == -1) ib++;
	if (ib >= Nbands) {
		fprintf(stderr, "No L1B SDS can be read successfully.\n");
		exit(1);
		}
 
	Nscans = sds[ib].Nl / sds[ib].rowsperscan;


	/* finally, open output file */
	if ( (sd_id = SDstart(filename, write_mode)) == -1 ) {
		fprintf(stderr, "Cannot open output file %s.\n", filename);
		exit(1);
		}

	if (!append) {
		if (write_global_attributes(sd_id, MOD021KMfile, MOD02HKMfile,
			MOD02QKMfile, maxsolz, sealevel, TOA, nearest)) {
			fputs("Error writing global attributes.\n", stderr);
			exit(1);
			}
		}

	/* create output SDSs and set SDS-specific attributes and dimension names */
	if (init_output_sds(sd_id, process, outsds, sds, gzip, verbose)) exit(1);


	mus = (float *) malloc(sds[REFSDS].rowsperscan * sds[REFSDS].Np * sizeof(float));
	height.data = (int16 *) malloc(sds[REFSDS].rowsperscan * sds[REFSDS].Np * sizeof(int16));
	if (!mus || !height.data) {
		(void) fputs("Error allocating memory.\n", stderr);
		exit(1);
		}

	if (sealevel || TOA)
		dem.data = (void *) NULL;
	else {
		dem.data = (int16 *) malloc(dem.Nl * dem.Np * sizeof(int16));
		if (!dem.data) {
			(void) fputs("Error allocating memory.\n", stderr);
			exit(1);
			}
		}

	if (!TOA) {
		nbytes = Nbands * sds[REFSDS].rowsperscan * sds[REFSDS].Np * sizeof(float);

		rhoray =      (float *) malloc(nbytes);
		sphalb =      (float *) malloc(nbytes);
		TtotraytH2O = (float *) malloc(nbytes);
		tOG =         (float *) malloc(nbytes);

		if (!rhoray || !sphalb || !TtotraytH2O || !tOG) {
			(void) fputs("Error allocating memory.\n", stderr);
			exit(1);
			}
		}

	solz = sds[SOLZ].data;
	sola = sds[SOLA].data;
	senz = sds[SENZ].data;
	sena = sds[SENA].data;
	solzfill = sds[SOLZ].fillvalue;
	lon = sds[LON].data;
	lat = sds[LAT].data;
	lonfill = sds[LON].fillvalue;
	latfill = sds[LAT].fillvalue;
	for (ib = 0; ib < Nbands; ib++) l1bdata[ib] = sds[ib].data;

	/* don't need DEM if --sealevel or --toa specified */
	if (!sealevel && !TOA) {
		dem.start[0] = 0;
		dem.start[1] = 0;
		dem.edges[0] = dem.Nl;
		dem.edges[1] = dem.Np;
		if (SDreaddata(dem.id, dem.start, NULL, dem.edges, dem.data) == -1) {
			fprintf(stderr, "  Can't read DEM SDS \"%s\"\n", dem.name);
			exit(-1);
			}
		(void) SDendaccess(dem.id);
		(void) SDend(dem.file_id);
		}

	/* loop over each MODIS scan */
	for (iscan = 0; iscan < Nscans; iscan++) {
		if ((iscan % NUM1KMROWPERSCAN == 0) && verbose)
			printf("Processing scan %d...\n", iscan);

		/* Fill scan buffer for each band to be processed.
		Exit scan loop if error occurred while reading. */
		if (read_scan(iscan, sds)) break;

		for (idx = 0; idx < sds[REFSDS].rowsperscan*sds[REFSDS].Np; idx++) {
			if (solz[idx] * sds[SOLZ].factor >= maxsolz)
				solz[idx] = *solzfill;

			if (!sealevel &&
				(lon[idx] == *lonfill || lat[idx] == *latfill))
				solz[idx] = *solzfill;

			if (solz[idx] != *solzfill) {
				mus[idx] = cos(solz[idx] * sds[SOLZ].factor * DEG2RAD);

				if (sealevel || TOA)
					((int16 *)height.data)[idx] = 0;
				else
					((int16 *)height.data)[idx] =
						(int16) interp_dem(lat[idx],
						lon[idx], &dem);
				}
			}


		if (!TOA) {
			for (irow=0; irow<sds[REFSDS].rowsperscan; irow++) {
				for (jcol=0; jcol<sds[REFSDS].Np; jcol++) {
					idx = irow * sds[REFSDS].Np + jcol;
					if (solz[idx] == *solzfill) continue;
					phi = sola[idx] * sds[SOLA].factor - sena[idx] * sds[SENA].factor;
					muv = cos(senz[idx] * sds[SENZ].factor * DEG2RAD);
					if ( getatmvariables(mus[idx], muv, phi, ((int16 *)height.data)[idx],
						process,
						&sphalb[idx * Nbands], &rhoray[idx * Nbands],
						&TtotraytH2O[idx * Nbands], &tOG[idx * Nbands]) == -1 )
						solz[idx] = *solzfill;
					}
				}
			}

		for (ib=0; ib<Nbands; ib++) {
			if (! process[ib]) continue;
			aggfactor = outsds[ib].rowsperscan / sds[REFSDS].rowsperscan;
			for (irow=0; irow<outsds[ib].rowsperscan; irow++) {
				if (!nearest) {
					fractrow = (float)irow / aggfactor - 0.5;	/* We want fractrow integer on coarse pixel center */
					crsrow1 = floor(fractrow);
					crsrow2 = crsrow1 + 1;
					if (crsrow1 < 0) crsrow1 = crsrow2 + 1;
					if (crsrow2 > sds[REFSDS].rowsperscan - 1) crsrow2 = crsrow1 - 1;
					t = (fractrow - crsrow1) / (crsrow2 - crsrow1);
					}

				for (jcol=0; jcol<outsds[ib].Np; jcol++) {
					idx = irow * outsds[ib].Np + jcol;
					crsidx = (int)(irow / aggfactor) * sds[REFSDS].Np + (int)(jcol / aggfactor);
					if ( solz[crsidx] == *solzfill  ||	/* Bad geolocation or night pixel */
						l1bdata[ib][idx] < 0 ) {	/* L1B is read as int16, not uint16, so faulty is negative */
						if (l1bdata[ib][idx] == MISSING)
							((int16 *)outsds[ib].data)[idx] = 32768 + MISSING;
						else if (l1bdata[ib][idx] == CANTAGGR)
							((int16 *)outsds[ib].data)[idx] = 32768 + SATURATED;
						else if (l1bdata[ib][idx] == SATURATED)
							((int16 *)outsds[ib].data)[idx] = 32768 + SATURATED;
						else
							((int16 *)outsds[ib].data)[idx] = *(int16 *)outsds[ib].fillvalue;

						continue;
						}

					if (nearest) {
						mus0 = mus[crsidx];
						if (! TOA) {
							rhoray0 = rhoray[crsidx * Nbands + ib];
							sphalb0 = sphalb[crsidx * Nbands + ib];
							if ( sphalb0 <= 0.0F ) {	/* Atm variables not computed successfully in this band */
								((int16 *)outsds[ib].data)[idx] = *(int16 *)outsds[ib].fillvalue;
								continue;
								}
							}
						}
					else {
						fractcol = ((float) jcol) / aggfactor - 0.5F;	/* We want fractcol integer on coarse pixel center */
						crscol1 = (int) floor(fractcol);
						crscol2 = crscol1 + 1;
						if (crscol1 < 0) crscol1 = crscol2 + 1;
						if (crscol2 > sds[REFSDS].Np - 1) crscol2 = crscol1 - 1;
						u = (fractcol - crscol1) / (crscol2 - crscol1);		/* We want u=0 on coarse pixel center */
						crsidx11 = crsrow1 * sds[REFSDS].Np + crscol1;
						crsidx12 = crsrow1 * sds[REFSDS].Np + crscol2;
						crsidx21 = crsrow2 * sds[REFSDS].Np + crscol1;
						crsidx22 = crsrow2 * sds[REFSDS].Np + crscol2;
						mus0 = t * u * mus[crsidx22] + (1.0F - t) * u * mus[crsidx12] + t * (1.0F - u) * mus[crsidx21] + (1.0F - t) * (1.0F - u) * mus[crsidx11];

						bad = (solz[crsidx11] == *solzfill) ||
							(solz[crsidx12] == *solzfill) ||
							(solz[crsidx21] == *solzfill) ||
							(solz[crsidx22] == *solzfill);

						if (bad) {
							((int16 *)outsds[ib].data)[idx] = *(int16 *)outsds[ib].fillvalue;
							continue;
							}

						if (! TOA) {
							rhoray11 = rhoray[crsidx11 * Nbands + ib];
							rhoray12 = rhoray[crsidx12 * Nbands + ib];
							rhoray21 = rhoray[crsidx21 * Nbands + ib];
							rhoray22 = rhoray[crsidx22 * Nbands + ib];
							rhoray0 = t * u * rhoray22 + (1.0F - t) * u * rhoray12 + t * (1.0F - u) * rhoray21 + (1.0F - t) * (1.0F - u) * rhoray11;
							sphalb11 = sphalb[crsidx11 * Nbands + ib];
							sphalb12 = sphalb[crsidx12 * Nbands + ib];
							sphalb21 = sphalb[crsidx21 * Nbands + ib];
							sphalb22 = sphalb[crsidx22 * Nbands + ib];

							bad = (sphalb11 <= 0.0F) ||
								(sphalb12 <= 0.0F) ||
								(sphalb21 <= 0.0F) ||
								(sphalb22 <= 0.0F);

							if (bad) {
								((int16 *)outsds[ib].data)[idx] = *(int16 *)outsds[ib].fillvalue;
								continue;
								}
							sphalb0 = t * u * sphalb22 + (1.0F - t) * u * sphalb12 + t * (1.0F - u) * sphalb21 + (1.0F - t) * (1.0F - u) * sphalb11;
							}
						}

					/* TOA reflectance */
					refl = (l1bdata[ib][idx] - sds[ib].offset) * sds[ib].factor / mus0;

					/* corrected reflectance */
					if (!TOA)
						refl = correctedrefl(refl, TtotraytH2O[crsidx * Nbands + ib],
							tOG[crsidx * Nbands + ib], rhoray0, sphalb0);

					/* reflectance bounds checking */
					if (refl > reflmax) refl = reflmax;
					if (refl < reflmin) refl = reflmin;

					((int16 *)outsds[ib].data)[idx] = (int16) (refl / outsds[ib].factor + 0.5);
					}
				}
			}


		/* write current scan line for all processed bands */
		if (write_scan(iscan, process, outsds)) {
			fprintf(stderr, "Cannot write scan %d of SDS %s\n",
				iscan, outsds[ib].name);
			exit(1);
			}

		} /* end of scan loop */


	for (ib = 0; ib < Nitems; ib++)
		if (sds[ib].id != -1) SDendaccess(sds[ib].id);

	for (ib = 0; ib < Nbands; ib++)
		if (process[ib]) SDendaccess(outsds[ib].id);

	SDend(MOD02QKMfile_id);
	SDend(MOD02HKMfile_id);
	SDend(MOD021KMfile_id);
	SDend(sd_id);


	/* ----- free memory ----- */

	for (ib = 0; ib < Nitems; ib++) {
		if (sds[ib].fillvalue) free(sds[ib].fillvalue);
		if (sds[ib].data) free(sds[ib].data);
		}

	free(height.data);
	free(mus);

	if (!TOA) {
		free(tOG);
		free(TtotraytH2O);
		free(sphalb);
		free(rhoray);
		}

	/* not allocated if --sealevel specified */
	if (dem.data) free(dem.data);


	return 0;
}




void usage(void)
{
	fputs("Usage:\n", stderr);
	fputs("crefl [--verbose] [--1km|--500m] [--nearest] [--toa|--sealevel]\n"
		"      [--gzip] [--maxsolz=angle] [--range=min,max] [--overwrite|--append]\n"
		"      [--bands=<band1,band2,band3,...>] --of=<output file>\n"
		"      <MOD021KM|MOD02CRS|MOD09CRS file> [<MOD02HKM file>] [<MOD02QKM file>]\n", stderr);

	fprintf(stderr, "Version %s, compiled %s %s.\n", PROCESS_VERSION_NUMBER,
		__DATE__, __TIME__);
}



/*
Parse MODIS L1B or coarse-resolution input file names to identify
expected spatial resolution of the MODIS swath present in file.
*/
int input_file_type(char *filename)
{
	char *ptr;
	int maxlen;


	if ( (ptr = strrchr(filename, '/')) )
		/* move to first character after last forward slash */
		ptr++;
	else
		/* no slash in file name */
		ptr = filename;


	/* all prefixes we'll recognize have this length */
	maxlen = strlen("M?D0????.");

	if (strncmp(ptr, "MOD021KM.", maxlen) == 0) return INPUT_1KM;
	if (strncmp(ptr, "MYD021KM.", maxlen) == 0) return INPUT_1KM;

	if (strncmp(ptr, "MOD02HKM.", maxlen) == 0) return INPUT_500M;
	if (strncmp(ptr, "MYD02HKM.", maxlen) == 0) return INPUT_500M;

	if (strncmp(ptr, "MOD02QKM.", maxlen) == 0) return INPUT_250M;
	if (strncmp(ptr, "MYD02QKM.", maxlen) == 0) return INPUT_250M;


	if (strncmp(ptr, "MOD02CRS.", maxlen) == 0) return INPUT_1KM;
	if (strncmp(ptr, "MYD02CRS.", maxlen) == 0) return INPUT_1KM;
	if (strncmp(ptr, "MOD09CRS.", maxlen) == 0) return INPUT_1KM;
	if (strncmp(ptr, "MYD09CRS.", maxlen) == 0) return INPUT_1KM;


	return INPUT_UNKNOWN;
}



/*
Parse band list and set relevant elements in process[] array.
Returns non-zero if invalid band(s) specified, 0 otherwise (i.e., success).
*/
int parse_bands(char *bandstr, unsigned char process[Nbands])
{
	int band, nb;
	char *ptr, *s;

	nb = 0;
	ptr = bandstr;
	while ( (s = strtok(ptr, ",")) ) {
		band = atoi(s);

		if ((band > 0) && (band < Nbands))
			process[band - 1] = TRUE;
		else
			return -1;

		if (++nb) ptr = (char *) NULL;
		}

	return 0;
}



/* set 250-m, 500-m, or 1-km line and sample dimension names for MODIS bands
given number of samples across scan */
void set_dimnames(int samples, char **dimname1, char **dimname2)
{
	switch(samples) {
		case NUM1KMCOLPERSCAN:
			*dimname1 = "lines_1km";
			*dimname2 = "samples_1km";
			break;

		case 2708:
			*dimname1 = "lines_500m";
			*dimname2 = "samples_500m";
			break;

		case 5416:
			*dimname1 = "lines_250m";
			*dimname2 = "samples_250m";
			break;

		default:
			*dimname1 = *dimname2 = (char *) NULL;
			break;
		}	
}




int interp_dem(float lat, float lon, SDS *dem)
{
	float fractrow, fractcol, t, u;
	int demrow1, demcol1, demrow2, demcol2;
	int height11, height12, height21, height22;
	int height;

	fractrow = (90.0F - lat) * dem->Nl / 180.0F;
	demrow1 = (int) floorf(fractrow);
	demrow2 = demrow1 + 1;
	if (demrow1 < 0) demrow1 = demrow2 + 1;
	if (demrow2 > dem->Nl - 1) demrow2 = demrow1 - 1;
	t = (fractrow - demrow1) / (demrow2 - demrow1);

	fractcol = (lon + 180.0F) * dem->Np / 360.0F;
	demcol1 = (int) floorf(fractcol);
	demcol2 = demcol1 + 1;
	if (demcol1 < 0) demcol1 = demcol2 + 1;
	if (demcol2 > dem->Np - 1) demcol2 = demcol1 - 1;
	u = (fractcol - demcol1) / (demcol2 - demcol1);

	height11 = ((int16 *)dem->data)[demrow1 * dem->Np + demcol1];
	height12 = ((int16 *)dem->data)[demrow1 * dem->Np + demcol2];
	height21 = ((int16 *)dem->data)[demrow2 * dem->Np + demcol1];
	height22 = ((int16 *)dem->data)[demrow2 * dem->Np + demcol2];
	height = (int) (t * u * height22 + t * (1.0F - u) * height21 +
		(1.0F - t) * u * height12 + (1.0F - t) * (1.0F - u) * height11);

	if (height < 0) height = 0;
	return height;
}




/* Write current scan line for all processed bands.
Returns 0 if no errors, non-zero otherwise. */
int write_scan(int iscan, unsigned char *process, SDS outsds[Nbands])
{
	int ib;

	for (ib = 0; ib < Nbands; ib++) {
		if (!process[ib]) continue;

		outsds[ib].start[0] = iscan * outsds[ib].rowsperscan;
		if (SDwritedata(outsds[ib].id, outsds[ib].start, NULL,
			outsds[ib].edges, outsds[ib].data) == -1) return 1;
		}

	return 0;
}



/* Read current scan line for all bands to be processed.
Returns 0 if no errors, non-zero otherwise. */
int read_scan(int iscan, SDS sds[Nitems])
{
	int ib;

	for (ib = 0; ib < Nitems; ib++) {
		if (sds[ib].id == -1) continue;

		switch (sds[ib].rank) {
			case 2: sds[ib].start[0] = iscan * sds[ib].rowsperscan; break;
			case 3: sds[ib].start[1] = iscan * sds[ib].rowsperscan; break;
			}

		if (SDreaddata(sds[ib].id, sds[ib].start, NULL, sds[ib].edges,
			sds[ib].data) == -1) {
			fprintf(stderr, "  Can't read scan %d of SDS \"%s\"\n", iscan, sds[ib].name);
			return 1;
			}
		}

	return 0;
}



float csalbr(float tau)
{
	return (3.0F * tau - fintexp3(tau) * (4.0F + 2.0F * tau) + 2.0 * expf(-tau)) / (4.0F + 3.0F * tau);
}




double fintexp1(float tau)
{
	double xx, xftau;
	int i;
	const double a[6] = {-.57721566, 0.99999193,-0.24991055,
		0.05519968,-0.00976004, 0.00107857};
	xx = a[0];
	xftau = 1.0;
	for (i=1; i<6; i++) {
		xftau *= tau;
		xx += a[i] * xftau;
		}

	return xx - log(tau);
}




double fintexp3(float tau)
{
	return (expf(-tau) * (1.0F - tau) + tau * tau * fintexp1(tau)) / 2.0;
}




void chand(float phi, float muv, float mus, float *taur, float *rhoray, float *trup, float *trdown,
	unsigned char *process)
{
/*
phi: azimuthal difference between sun and observation in degree
     (phi=0 in backscattering direction)
mus: cosine of the sun zenith angle
muv: cosine of the observation zenith angle
taur: molecular optical depth
rhoray: molecular path reflectance
constant xdep: depolarization factor (0.0279)
         xfd = (1-xdep/(2-xdep)) / (1 + 2*xdep/(2-xdep)) = 2 * (1 - xdep) / (2 + xdep) = 0.958725775
*/
const double xfd = 0.958725775;
const float xbeta2 = 0.5F;
float pl[5];
double fs01, fs02, fs0, fs1,fs2;
const float as0[10] = {0.33243832F, 0.16285370F, -0.30924818F, -0.10324388F,
	0.11493334F, -6.777104e-02F, 1.577425e-03F, -1.240906e-02F,
	3.241678e-02F, -3.503695e-02F};
const float as1[2] = {0.19666292F, -5.439061e-02F};
const float as2[2] = {0.14545937F,-2.910845e-02F};
float phios, xcos1, xcos2, xcos3;
float xph1, xph2, xph3, xitm1, xitm2;
float xlntaur, xitot1, xitot2, xitot3;
int i,ib;

  phios = phi + 180.0F;
  xcos1 = 1.0F;
  xcos2 = cos(phios * DEG2RAD);
  xcos3 = cos(2.0 * phios * DEG2RAD);
  xph1 = 1.0 + (3.0F * mus * mus - 1.0F) * (3.0F * muv * muv - 1.0F) * xfd / 8.0;
  xph2 = - xfd * xbeta2 * 1.5 * mus * muv * sqrtf(1.0F - mus * mus) * sqrtf(1.0F - muv * muv);
  xph3 =   xfd * xbeta2 * 0.375 * (1.0F - mus * mus) * (1.0F - muv * muv);

  pl[0] = 1.0F;
  pl[1] = mus + muv;
  pl[2] = mus * muv;
  pl[3] = mus * mus + muv * muv;
  pl[4] = mus * mus * muv * muv;

  fs01 = fs02 = 0.0;
  for (i = 0; i < 5; i++) {
	fs01 += (double) (pl[i] * as0[i]);
	fs02 += (double) (pl[i] * as0[5 + i]);
	}

  for (ib = 0; ib < Nbands; ib++) {
    if (process[ib]) {
      xlntaur = logf(taur[ib]);
      fs0 = fs01 + fs02 * xlntaur;
      fs1 = as1[0] + xlntaur * as1[1];
      fs2 = as2[0] + xlntaur * as2[1];
      trdown[ib] = expf(-taur[ib]/mus);
      trup[ib]   = expf(-taur[ib]/muv);
      xitm1 = (1.0F - trdown[ib] * trup[ib]) / 4.0F / (mus + muv);
      xitm2 = (1.0F - trdown[ib]) * (1.0F - trup[ib]);
      xitot1 = xph1 * (xitm1 + xitm2 * fs0);
      xitot2 = xph2 * (xitm1 + xitm2 * fs1);
      xitot3 = xph3 * (xitm1 + xitm2 * fs2);
      rhoray[ib] = xitot1 * xcos1 + xitot2 * xcos2 * 2.0F + xitot3 * xcos3 * 2.0F;
    }
  }

}




int getatmvariables(float mus, float muv, float phi, int16 height,
	unsigned char *process, float *sphalb, float *rhoray, float *TtotraytH2O,
	float *tOG)
{
	double m, Ttotrayu, Ttotrayd, tO3, tO2, tH2O;
	float psurfratio;
	int j, ib;
/*
Values for bands 9-16 below provided by B Murch and C Hu Univ South Florida
IMaRS, obtained from SEADAS.
For the moment I've retained the Jacques values for 1-8 but show the differing
SEADAS values in the commented out line.
*/
const float aH2O[Nbands]={ -5.60723, -5.25251, 0, 0, -6.29824, -7.70944, -3.91877, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
const float bH2O[Nbands]={ 0.820175, 0.725159, 0, 0, 0.865732, 0.966947, 0.745342, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
/*const float aO3[Nbands]={ 0.0711,    0.00313, 0.0104,     0.0930,   0, 0, 0, 0.00244, 0.00383, 0.0225, 0.0663, 0.0836, 0.0485, 0.0395, 0.0119, 0.00263};*/
  const float aO3[Nbands]={ 0.0715289, 0,       0.00743232, 0.089691, 0, 0, 0, 0.001,   0.00383, 0.0225, 0.0663, 0.0836, 0.0485, 0.0395, 0.0119, 0.00263};
/*const float taur0[Nbands] = { 0.0507,  0.0164,  0.1915,  0.0948,  0.0036,  0.0012,  0.0004,  0.3109, 0.2375, 0.1596, 0.1131, 0.0994, 0.0446, 0.0416, 0.0286, 0.0155};*/
  const float taur0[Nbands] = { 0.05100, 0.01631, 0.19325, 0.09536, 0.00366, 0.00123, 0.00043, 0.3139, 0.2375, 0.1596, 0.1131, 0.0994, 0.0446, 0.0416, 0.0286, 0.0155};

	float taur[Nbands], trup[Nbands], trdown[Nbands];
	static float sphalb0[MAXNUMSPHALBVALUES];
	static char first_time = TRUE;


	if (first_time) {
		sphalb0[0] = 0.0F;
		for(j = 1; j < MAXNUMSPHALBVALUES; j++)
			sphalb0[j] = csalbr(j * TAUSTEP4SPHALB);
		first_time = FALSE;
		}

	m = 1.0 / mus + 1.0 / muv;
	if (m > MAXAIRMASS) return -1;

	psurfratio = expf(-height / (float) SCALEHEIGHT);
	for (ib = 0; ib < Nbands; ib++)
		if (process[ib]) taur[ib] = taur0[ib] * psurfratio;

	chand(phi, muv, mus, taur, rhoray, trup, trdown, process);

	for (ib = 0; ib < Nbands; ib++) {
		if (!process[ib]) continue;

		if (taur[ib] / TAUSTEP4SPHALB >= MAXNUMSPHALBVALUES) {
			sphalb[ib] = -1.0F;
			/* Use sphalb as flag to indicate atm variables are not computed successfully */
			continue;
			}

		sphalb[ib] = sphalb0[(int)(taur[ib] / TAUSTEP4SPHALB + 0.5)];
		Ttotrayu = ((2 / 3. + muv) + (2 / 3. - muv) * trup[ib])   / (4 / 3. + taur[ib]);
		Ttotrayd = ((2 / 3. + mus) + (2 / 3. - mus) * trdown[ib]) / (4 / 3. + taur[ib]);
		tO3 = tO2 = tH2O = 1.0;
		if (aO3[ib] != 0) tO3 = exp(-m * UO3 * aO3[ib]);
		if (bH2O[ib] != 0) tH2O = exp(-exp(aH2O[ib] + bH2O[ib] * log(m * UH2O)));
/*
      t02 = exp(-m * aO2);
*/
		TtotraytH2O[ib] = Ttotrayu * Ttotrayd * tH2O;
		tOG[ib] = tO3 * tO2;
		}

  return 0;

}




float correctedrefl(float refl, float TtotraytH2O, float tOG, float rhoray, float sphalb)
{
	float corr_refl;

	corr_refl = (refl / tOG - rhoray) / TtotraytH2O;
	corr_refl /= (1.0F + corr_refl * sphalb);
	return corr_refl;
}





int init_output_sds(int32 sd_id, unsigned char *process, SDS outsds[Nbands], SDS sds[Nitems],
	int gzip, int verbose)
{
	int ib;
	int32 dim_id;
	char *dimname1, *dimname2;

	HDF_CHUNK_DEF chunk_def;


	/* same fill value will be used for all output SDSs */
	static int16 fillvalue = FILL_INT16;

	/* band naming convention will be "CorrRefl_XX"
	(11 characters + terminating null) */
	char name[16];


	/* write SDS-specific attributes and dimension names */
	for (ib = 0; ib < Nbands; ib++) {
		if (!process[ib]) continue;

		outsds[ib].num_type = DFNT_INT16;
		outsds[ib].factor = 0.0001;
		outsds[ib].offset = 0;
		outsds[ib].rank = 2;

		sprintf(name, "CorrRefl_%2.2d", ib + 1);
		if ( !(outsds[ib].name = strdup(name)) ) return 1;

		outsds[ib].Nl = outsds[ib].dim_sizes[0] = sds[ib].Nl;
		outsds[ib].Np = outsds[ib].dim_sizes[1] = sds[ib].Np;
		outsds[ib].rowsperscan = sds[ib].rowsperscan;
		if (verbose)
			printf("Creating SDS %s: %dx%d\n", outsds[ib].name,
				outsds[ib].Np, outsds[ib].Nl);
		if ((outsds[ib].id = SDcreate(sd_id, outsds[ib].name, outsds[ib].num_type, outsds[ib].rank,
				outsds[ib].dim_sizes)) == -1) {
			fprintf(stderr, "Cannot create SDS %s\n", outsds[ib].name);
			return 1;
			}

		outsds[ib].fillvalue = &fillvalue;
		if ( SDsetfillvalue(outsds[ib].id, outsds[ib].fillvalue) ) {
			fprintf(stderr, "Cannot write fill value of SDS %s\n", outsds[ib].name);
			return 1;
			}
		if ( SDsetattr(outsds[ib].id, "scale_factor", DFNT_FLOAT64, 1, &outsds[ib].factor) == -1  ||
			SDsetattr(outsds[ib].id, "add_offset",   DFNT_FLOAT64, 1, &outsds[ib].offset) == -1 ) {
			fprintf(stderr, "Cannot write scale factor and offset of SDS \"%s\"\n",  outsds[ib].name);
			return 1;
			}
		if ( SDsetattr(outsds[ib].id, "units", DFNT_CHAR8, 4, "none") == -1 ) {
			fprintf(stderr, "Cannot write units attribute of SDS \"%s\"\n",  outsds[ib].name);
			return 1;
			}

		/* set dimensions */
		outsds[ib].start[1] = 0;
		outsds[ib].edges[0] = outsds[ib].rowsperscan;
		outsds[ib].edges[1] = outsds[ib].Np;

		/* allocate memory for band output data */
		outsds[ib].data = malloc(outsds[ib].rowsperscan * outsds[ib].Np * DFKNTsize(outsds[ib].num_type));
		if (!outsds[ib].data) {
			fputs("Error allocating memory.\n", stderr);
			return 1;
			}

		/* set optional compression */
		if (gzip) {
			chunk_def.chunk_lengths[0] = chunk_def.comp.chunk_lengths[0] = outsds[ib].edges[0];
			chunk_def.chunk_lengths[1] = chunk_def.comp.chunk_lengths[1] = outsds[ib].edges[1];
			chunk_def.comp.comp_type = COMP_CODE_DEFLATE;
			chunk_def.comp.cinfo.deflate.level = 4;
			if (SDsetchunk(outsds[ib].id, chunk_def, HDF_CHUNK | HDF_COMP) == FAIL) {
				fprintf(stderr, "Cannot set chunks for SDS %s\n", outsds[ib].name);
				return 1;
				}
			}


		set_dimnames(outsds[ib].Np, &dimname1, &dimname2);

if (verbose) printf("(%s x %s)\n", dimname1, dimname2);

		/* dimension names */
		if ((dim_id = SDgetdimid(outsds[ib].id, 0)) == -1) {
			fputs("Error getting dimension ID1.\n", stderr);
			return 1;
			}
		if (SDsetdimname(dim_id, dimname1) == -1) {
			fprintf(stderr, "Cannot set first dimension name for SDS %s\n", outsds[ib].name);
			return 1;
			}
		if ((dim_id = SDgetdimid(outsds[ib].id, 1)) == -1) {
			fputs("Error getting dimension ID2.\n", stderr);
			return 1;
			}
		if (SDsetdimname(dim_id, dimname2) == -1) {
			fprintf(stderr, "Cannot set second dimension name for SDS %s\n", outsds[ib].name);
			return 1;
			}
		}

	return 0;
}



/*
Write global attributes to HDF output file.
Returns 0 if no errors, non-zero otherwise.
*/
int write_global_attributes(int32 sd_id, char *MOD021KMfile,
	char *MOD02HKMfile, char *MOD02QKMfile, float maxsolz,
	int sealevel, int TOA, int nearest)
{
	char *ptr;
	int j;
	float32 f32;
	uint8 u8;

	ptr = PROCESS_VERSION_NUMBER;
	j = strlen(ptr);
	if (SDsetattr(sd_id, "ProcessVersionNumber", DFNT_CHAR8, j, ptr)) return 1;

	if (MOD021KMfile) {
		j = strlen(MOD021KMfile);
		if (SDsetattr(sd_id, "1km_input_file", DFNT_CHAR8, j, MOD021KMfile))
			return 1;
		}

	if (MOD02HKMfile) {
		j = strlen(MOD02HKMfile);
		if (SDsetattr(sd_id, "500m_input_file", DFNT_CHAR8, j, MOD02HKMfile))
			return 1;
		}

	if (MOD02QKMfile) {
		j = strlen(MOD02QKMfile);
		if (SDsetattr(sd_id, "250m_input_file", DFNT_CHAR8, j, MOD02QKMfile))
			return 1;
		}


	f32 = maxsolz;
	if (SDsetattr(sd_id, "MaxSolarZenithAngle", DFNT_FLOAT32, 1, &f32))
		return 1;

	u8 = (uint8) sealevel;
	if (SDsetattr(sd_id, "sealevel", DFNT_UINT8, 1, &u8)) return 1;
	u8 = (uint8) TOA;
	if (SDsetattr(sd_id, "toa", DFNT_UINT8, 1, &u8)) return 1;
	u8 = (uint8) nearest;
	if (SDsetattr(sd_id, "nearest", DFNT_UINT8, 1, &u8)) return 1;

	return 0;
}



/*
Returns 0 if xmin <= x <= xmax, non-zero otherwise.
*/
int range_check(float x, float xmin, float xmax)
{
	return (x < xmin) || (x > xmax);
}
