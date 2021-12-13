/* Compile with:
   cc -O0 -o h5SDS_transfer_rename h5SDS_transfer_rename.c -I$HDF5INC -I$HDFINC -L$HDF5LIB -lhdf5 -L$HDFLIB -lmfhdf -ldf -ljpeg -lz -lm

 or

   cc -O0 -o h5SDS_transfer_rename h5SDS_transfer_rename.c -I/usr/local/opt/TOOLKIT-5.2.16.orig/hdf5/linux64/hdf5-1.8.3/include -I$HDFINC -L/usr/local/opt/TOOLKIT-5.2.16.orig/hdf5/linux64/hdf5-1.8.3/lib -lhdf5 -L$HDFLIB -lmfhdf -ldf -ljpeg -lz -lm /usr/local/opt/TOOLKIT-5.2.16.orig/szip/linux64/szip-2.1/lib/libsz.a


 */
#include <stdlib.h>
#include <libgen.h>
#include "mfhdf.h"
#define H5Aiterate_vers 1
#define H5Dopen_vers 1
#define H5Gopen_vers 1
#define H5Dcreate_vers 1
#define H5Acreate_vers 1
#include "hdf5.h"
#define MAX_DATASETS 50
#define MAX_DATASETNAME 500
#define MAXLENGTH 512
#define FALSE 0
herr_t group_info(hid_t loc_id, const char *name, void *opdata);   /* Operator function */
herr_t attr_info(hid_t loc_id, const char *name, void *opdata);   /* Operator function */

int n_datasets, n_groups, n_attrs;
char datasets[MAX_DATASETS][MAX_DATASETNAME];
char groups[MAX_DATASETS][MAX_DATASETNAME];
void *get_memory(int32 count, int32 type);

int main(int argc, char **argv)
{
FILE *fd;
hid_t file, file2;
herr_t status;
hid_t dataset, datatype, dataspace;
hid_t dataset1, dataspace1;
hid_t get_H5_datatype_from_H4(int32 i);
hsize_t maxdims[2];
int i, j, jj, syze;
ssize_t n, ord, sign, size, class;
int rank, idx_f, idx[2];
hsize_t *current_dims;
hsize_t *max_dims;
char tmpstring[5000];
char charord[22], charclass[22];
void order_check(ssize_t ord, char charord[22]);
void class_check(ssize_t class, char charclass[22]);
void *data;
float *fdata;
long l, ll;
void *get_memory(int32 count, int32 type);
int32 k, f1_is_H5, f2_is_H5;
int32 start[5];
int32 sd_id3, sds_out;
int32 sd_id1, n_sets1, n_gattr1, sds_id1, rank1, dims1[5], number_type1, nattr1, dcount, dnt, dattr;
int32 sd_id2, sds_id2;
char name1[128];
char dimnames[5][128];
void *get_image(int32 id, int32 *dims, int32 type, int *size);
void transfer_attributes(int32 id1, int32 id_out);
void swapbytes(void *val, int nbbytes);
int32 *i32_array;
uint32 *ui32_array;
float64 *f64_array;
float32 *f32_array;
int16 *i16_array;
uint16 *ui16_array;
long *lng_array;
unsigned long *ulng_array;

hid_t attrid, attrdataspace, attrdatatype, attr_id;
int buf_size;
char charbuf[1000];
int big_array[10000];
int *big_ints;
int atrank;
hsize_t *atcurrent_dims;
hsize_t *atmax_dims;
void write_local_SDS_attribute(int32 sds_out, int buf_size, char charbuf[1000], int big_array[10000],
                               ssize_t ord, ssize_t sign, ssize_t size, ssize_t class);
void transfer_attributes_to_HDF5(int32 sds_id1, hid_t dataset);

n_datasets = 0;
n_groups = 0;

if (argc<5) {
       printf("\nProgram for reading an SDS from one HDF file and copying it to another HDF file -- with renaming\n");
       printf("usage: %s <donor HDF file> <recipient HDF file> <SDSname in donor> <SDSname in recipient>\n", argv[0]);
       printf("program works on either HDF4 or HDF5 files.\n");
       printf("Jim Ray, Sigma, %s\n\n", __DATE__);
       exit(0);
	}

if (!strcmp(argv[1], argv[2])) {
      printf("error: cannot use same file, '%s', as both input and output.\n", argv[1]);
      exit(-1);
       }

f1_is_H5 = H5Fis_hdf5(argv[1]);

/* Get all 'donor' file information */

if (f1_is_H5) {
   file = H5Fopen(argv[1], H5F_ACC_RDONLY, H5P_DEFAULT);

   /* first iteration */
   idx[0] = -1;
   idx[1] = 0;
   idx_f = H5Giterate(file, "/", NULL, group_info, (void *)idx);

   /* second iteration */
   j = idx[1];
   for(i=0;i<j;i++) {
      idx[0] = i;
      idx[1] = n_groups;
      idx_f = H5Giterate(file, groups[i], NULL, group_info, (void *)idx);
      }

   /* third iteration */
   jj = j;
   j = idx[1];
   for(i=jj;i<j;i++) {
      idx[0] = i;
      idx[1] = n_groups;
      idx_f = H5Giterate(file, groups[i], NULL, group_info, (void *)idx);
      }

   /* forth, fifth iteration */
   jj = j;
   j = idx[1];
   for(i=jj;i<j;i++) {
      idx[0] = i;
      idx[1] = n_groups;
      idx_f = H5Giterate(file, groups[i], NULL, group_info, (void *)idx);
      }
   jj = j;
   j = idx[1];
   for(i=jj;i<j;i++) {
      idx[0] = i;
      idx[1] = n_groups;
      idx_f = H5Giterate(file, groups[i], NULL, group_info, (void *)idx);
      }
   strcpy(groups[n_groups++], "/\0");
}
else {
   if ((sd_id1 = SDstart(argv[1], DFACC_RDONLY)) == -1) {
      printf("error: file '%s' can't be opened with SDstart().\n", argv[1]);
      exit(-1);
      }
   if (  (j = SDnametoindex(sd_id1, argv[3]) ) < 0 )   {
      printf("error: SDS '%s' not found in file '%s'.\n", argv[3], argv[1]);
      exit(-1);
      }
   else sds_id1 = SDselect(sd_id1, j);
   }

/* get some OBJECTIVE idea of whether/not output file exists... */

fd = fopen(argv[2], "r");
if (fd == NULL) {    /* it doesn't exist, try to create it. */

   /* create an HDF5 if input is HDF5, otherwise create an HDF4 */

   if ( strstr(argv[2], ".h5\0"))       f2_is_H5 = 1;
   else if ( strstr(argv[2], ".hdf\0")) f2_is_H5 = 0;
   else                                 f2_is_H5 = f1_is_H5;


   if (f2_is_H5) {

      if ((file2 = H5Fcreate(argv[2], H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT)) == -1) {
         printf("error: file '%s' can't be opened with H5Fcreate().\n", argv[2]);
         H5Fclose(file);
         exit(-1);
          }
	}
   else {
       if ((sd_id2 = SDstart(argv[2], DFACC_CREATE)) == -1) {
         printf("error: file '%s' can't be opened with SDstart().\n", argv[2]);
         SDendaccess(sds_id1);
         SDend(sd_id1);
         exit(-1);
         }

	}
      }
else {               /* it exists! Open for read/writing... */
   fclose(fd);
   f2_is_H5 = H5Fis_hdf5(argv[2]);

   if (f2_is_H5) {
       if ((file2 = H5Fopen(argv[2], H5F_ACC_RDWR, H5P_DEFAULT)) == -1) {
         printf("error: file '%s' can't be opened with H5Fopen().\n", argv[2]);
         H5Fclose(file);
         exit(-1);
           }
	}
   else	{
       if ((sd_id2 = SDstart(argv[2], DFACC_RDWR)) == -1) {
         printf("error: file '%s' can't be opened with SDstart().\n", argv[2]);
         SDendaccess(sds_id1);
         SDend(sd_id1);
         exit(-1);
          }
      }
     }

/* Now check the datasets in file 1 */

number_type1 = -1;

if (f1_is_H5) {

for(i=0;i<n_datasets;i++) {
   /*printf("%d %s\n", i, datasets[i]); */

   strcpy(tmpstring, basename(datasets[i]));

   if (  strcmp(tmpstring, argv[3])) continue;   /* skip ones we don't want */

   dataset1 = H5Dopen(file, datasets[i]);

   /* query the dataspace */
   dataspace1 = H5Dget_space(dataset1);

   rank = H5Sget_simple_extent_ndims(dataspace1);

   current_dims = (hsize_t *)malloc(rank*sizeof(hsize_t));
   max_dims = (hsize_t *)malloc(rank*sizeof(hsize_t));

   H5Sget_simple_extent_dims(dataspace1, current_dims, max_dims);  /* assuming made with H5Screate_simple() */

   l = (long)current_dims[0];
   for(j=1;j<rank;j++) {
      l *= (long)current_dims[j];
      }

   /* query the datatype */

   datatype = H5Dget_type(dataset1);
   sign = H5Tget_sign(datatype);
   size = H5Tget_size(datatype);
   class = H5Tget_class(datatype);
   ord = H5Tget_order(datatype);

#ifdef DEBUG
   printf("%d dataset '%s': rank %d: %d", i, basename(datasets[i]), rank, current_dims[0]);
   for(j=1;j<rank;j++) {
      printf(" by %d", current_dims[j]);
      }
   printf(" ---- ");

   order_check(ord, charord);
   class_check(class, charclass);

   if (class == H5T_INTEGER)
      printf("%s, %s %s, %d byte%c\n", charord, ((sign==H5T_SGN_NONE) ? "unsigned\0" : "signed\0"), charclass, size, ((size>1) ? 's' : ' '));
   else
      printf("%s, %s, %d byte%c\n", charord, charclass, size, ((size>1) ? 's' : ' '));
#endif

   data = (void *)NULL;

   /*if (rank != 2) continue;*/

   if (class == H5T_INTEGER) {
       if (sign == H5T_SGN_NONE) {
           if (size == 1) number_type1 =  DFNT_UINT8;
           else if (size == 2) number_type1 =  DFNT_UINT16;
           else if (size == 4) number_type1 =  DFNT_UINT32;
           else if (size == 8) number_type1 =  DFNT_UINT64;
	   else continue;
          }
       else {
           if (size == 1) number_type1 =  DFNT_INT8;
           else if (size == 2) number_type1 =  DFNT_INT16;
           else if (size == 4) number_type1 =  DFNT_INT32;
           else if (size == 8) number_type1 =  DFNT_INT64;
	   else continue;
          }
      }
   else if (class == H5T_FLOAT) {
      if (size == 4) number_type1 =  DFNT_FLOAT;
      else if (size == 8) number_type1 =  DFNT_FLOAT64;
      else continue;
      }
   else continue;

   data = get_memory(l, number_type1);

   status = H5Dread(dataset1, datatype, H5S_ALL, H5S_ALL, H5P_DEFAULT, data);

   /* Close all dataset/type/space for the donor data */
   /* IF, you are NOT writing to an HDF5 file.  If you ARE
      writing to an HDF5 file, close these AFTER you are done transferring
      metadata to the HDF5 output file * /
   if (f2_is_H5 == 0) {
      H5Dclose(dataset1);
      / *H5Tclose(datatype);* /
      H5Sclose(dataspace1);
      H5Fclose(file);
      }
      */

   }   /*  for(i=0;i<n_datasets;i++)  */
}
else {
    for (k=0;k<5;k++) dims1[k] = 0;
    SDgetinfo(sds_id1, name1, &rank1, dims1, &number_type1, &nattr1);

    for (k=0;k<rank1;k++) {
      SDdiminfo(SDgetdimid(sds_id1, k), dimnames[k], &dcount, &dnt, &dattr);
       }

    data = get_image(sds_id1, dims1, number_type1, &syze);


    /*if (f2_is_H5) {   / * IF we're writing to an HDF5, we can close this now, because
                          we can't xfer metadata from HDF4 to HDF5 (for now). But we
			  CAN xfer metadata from HDF4 to HDF4, so in that case KEEP THESE
			  OPEN and close 'em after the xfer * /
      SDendaccess(sds_id1);
      SDend(sd_id1);
      }*/
   }

if (number_type1 == -1) {
      printf("error: cannot find SDS '%s' in file '%s'.\n", argv[3], argv[1]);
      if (f1_is_H5) H5Fclose(file);
      else          SDend(sd_id1);
      exit(-1);
     }

if (f2_is_H5) {


   if (f1_is_H5 == 0) {
      current_dims = (hsize_t *)malloc(rank1*sizeof(hsize_t));
      for (k=0;k<rank1;k++) {
        current_dims[k] = dims1[k];
	}
      rank = rank1;
      datatype = get_H5_datatype_from_H4(number_type1);
      }

   /* Open all dataset/type/space for the output data */
   dataspace = H5Screate_simple(rank, current_dims, NULL);

   /*status = H5Tset_order(datatype, H5T_ORDER_LE);*/

   dataset = H5Dcreate(file2, argv[4], datatype, dataspace, H5P_DEFAULT);

   printf("Transferring SDS '%s' as '%s'...\n", argv[3], argv[4]);
   status = H5Dwrite(dataset, datatype, H5S_ALL, H5S_ALL,
	             H5P_DEFAULT, data);


   if (f1_is_H5 == 1) {

      /* Transfer metadata from the input HDF5 to the output HDF5 */
      n_attrs = H5Aget_num_attrs(dataset1);
      /*printf("%d attributes \n", n_attrs);*/
      for (k=0;k<n_attrs;k++) {
          attrid = H5Aopen_idx (dataset1, (unsigned int)k);
	  attrdataspace = H5Aget_space(attrid);
	  attrdatatype = H5Aget_type(attrid);

	  /* Note, charbuf (the name of the attribute) is hard-coded as
	     1000 characters, which should not be a problem.
	     However, big_array (the values of the attributes) is
	     hard-coded as 10000 ints, which may represent a problem.
	     However, floats, ints, and character strings can be transferred
	     this way without any trouble...
	   */

	  H5Aget_name(attrid, buf_size, charbuf);
	  /*printf(" attribute %s \n", charbuf);*/
	  H5Aread(attrid, attrdatatype, (void *)big_array);

          attr_id = H5Acreate(dataset, charbuf, attrdatatype, attrdataspace, H5P_DEFAULT);
          H5Awrite(attr_id, attrdatatype, (void *)big_array);

          H5Tclose(attrdatatype);
          H5Aclose(attr_id);
          H5Aclose(attrid);

         }

      /* and close everything */
      H5Dclose(dataset1);
      H5Sclose(dataspace1);
      H5Fclose(file);
      }
   else {  /* then we're xferring attributes from an HDF4 to an HDF5 */
      transfer_attributes_to_HDF5(sds_id1, dataset);
      SDendaccess(sds_id1);
      SDend(sd_id1);
      }

   free(data);

   H5Dclose(dataset);

   if (f1_is_H5 == 1) H5Tclose(datatype);

   H5Sclose(dataspace);

   H5Fclose(file2);
  }
else {

   if (f1_is_H5 == 1) {
      for (k=0;k<5;k++) dims1[k] = 0;
      for (k=0;k<rank;k++) {
        dims1[k] = (int32)current_dims[k];
	}
      rank1 = rank;

      /* if data is BE, may have to swap data around
         (assuming machine we're on is little-endian)  */
      if ((ord == H5T_ORDER_BE)&&(size > 1)) {

            switch (number_type1) {
               case(DFNT_INT16):
	          i16_array = (int16 *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(i16_array[ll]), size);
		  break;
               case(DFNT_UINT16):
	          ui16_array = (uint16 *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(ui16_array[ll]), size);
		  break;
               case(DFNT_INT32):
	          i32_array = (int32 *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(i32_array[ll]), size);
		  break;
               case(DFNT_UINT32):
	          ui32_array = (uint32 *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(ui32_array[ll]), size);
		  break;

	       /* Does plain old HDF4 have DFNT_INT64, DFNT_UINT64?
	          I keep getting error messages when trying to SDcreate()
		  SDSs of these types... */
               case(DFNT_INT64):
	          lng_array = (long *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(lng_array[ll]), size);
		  break;
               case(DFNT_UINT64):
	          ulng_array = (unsigned long *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(ulng_array[ll]), size);
		  break;


               case(DFNT_FLOAT):
	          f32_array = (float *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(f32_array[ll]), size);
		  break;
               case(DFNT_FLOAT64):
	          f64_array = (double *)data;
                  for(ll=0;ll<l;ll++) swapbytes(&(f64_array[ll]), size);
		  break;
	    }
         }

      }

   if ((sds_out = SDcreate(sd_id2, argv[4], number_type1, rank1, dims1)) == -1) {
      printf("Error creating SDS in output file '%s', cannot continue\n", argv[2]);
      exit(-3);
       }

   for (k=0;k<5;k++) start[k] = 0;
   printf("Transferring SDS '%s' as '%s'...\n", argv[3], argv[4]);
   if ((SDwritedata(sds_out, start, NULL, dims1, (VOID *)data)) == -1) {
       printf("Error writing SDS in output file '%s', cannot continue\n", argv[2]);
       exit(-3);
        }
   if (f1_is_H5 == 0) {  /* try to xfer attributes; from HDF4 to HDF4 */
      for (k=0;k<rank1;k++) {
          SDsetdimname(SDgetdimid(sds_out, k), dimnames[k]);
	   }
      transfer_attributes(sds_id1, sds_out);
      SDendaccess(sds_id1);
      SDend(sd_id1);
      }
   else {   /* try to xfer attributes from HDF5 to HDF4 */
      n_attrs = H5Aget_num_attrs(dataset1);
      /*printf("%d attributes \n", n_attrs);*/
      for (k=0;k<n_attrs;k++) {
          attrid = H5Aopen_idx (dataset1, (unsigned int)k);
	  attrdataspace = H5Aget_space(attrid);
	  attrdatatype = H5Aget_type(attrid);

	  /* Note, charbuf (the name of the attribute) is hard-coded as
	     1000 characters, which should not be a problem.
	     However, big_array (the values of the attributes) is
	     hard-coded as 10000 ints, which may represent a problem.
	     However, floats, ints, and character strings can be transferred
	     this way without any trouble...
	   */

	  atrank = H5Sget_simple_extent_ndims(attrdataspace);
	  if (atrank < 2) {

             atcurrent_dims = (hsize_t *)malloc(atrank*sizeof(hsize_t));
             atmax_dims = (hsize_t *)malloc(atrank*sizeof(hsize_t));

             H5Sget_simple_extent_dims(attrdataspace, atcurrent_dims, atmax_dims);  /* assuming made with H5Screate_simple() */


	     H5Aget_name(attrid, buf_size, charbuf);
	     /*printf(" attribute %s rank %d\n", charbuf, atrank);*/

	     if (atrank == 0) { /* this happens for strings */
	        atmax_dims = (hsize_t *)malloc(1*sizeof(hsize_t));
	        atcurrent_dims = (hsize_t *)malloc(1*sizeof(hsize_t));
		atmax_dims[0] = H5Tget_size(attrdatatype);
	        }

	     H5Aread(attrid, attrdatatype, (void *)big_array);
	     write_local_SDS_attribute(sds_out, atmax_dims[0], charbuf, big_array, H5Tget_order(attrdatatype),
	                            H5Tget_sign(attrdatatype), H5Tget_size(attrdatatype),
				    H5Tget_class(attrdatatype));

             free(atmax_dims);
             free(atcurrent_dims);

	      }
          H5Sclose(attrdataspace);
	  H5Aclose(attrid);
	  }

/**************************************/
/*  CHANGES JUST ON STEAM *************/
/* We need to read a dataset called "ReflectanceFactors" and
 * write them AS ATTRIBUTES, because they are NOT attributes in the
 * original data... */

      H5Dclose(dataset1);
      free(data);

 for(i=0;i<n_datasets;i++) {
   /*printf("%d %s\n", i, datasets[i]); */

   strcpy(tmpstring, basename(datasets[i]));

   if (  strcmp(tmpstring, "ReflectanceFactors")) continue;   /* skip ones we don't want */

   dataset1 = H5Dopen(file, datasets[i]);

   dataspace1 = H5Dget_space(dataset1);

   rank = H5Sget_simple_extent_ndims(dataspace1);

   current_dims = (hsize_t *)malloc(rank*sizeof(hsize_t));
   max_dims = (hsize_t *)malloc(rank*sizeof(hsize_t));

   H5Sget_simple_extent_dims(dataspace1, current_dims, max_dims);  /* assuming made with H5Screate_simple() */

   l = (long)current_dims[0];
   for(j=1;j<rank;j++) {
      l *= (long)current_dims[j];
      }

   /* query the datatype */

   datatype = H5Dget_type(dataset1);
   sign = H5Tget_sign(datatype);
   size = H5Tget_size(datatype);
   class = H5Tget_class(datatype);
   ord = H5Tget_order(datatype);

   data = (void *)NULL;

   /*if (rank != 2) continue;*/

   if (class == H5T_INTEGER) {
       if (sign == H5T_SGN_NONE) {
           if (size == 1) number_type1 =  DFNT_UINT8;
           else if (size == 2) number_type1 =  DFNT_UINT16;
           else if (size == 4) number_type1 =  DFNT_UINT32;
           else if (size == 8) number_type1 =  DFNT_UINT64;
          }
       else {
           if (size == 1) number_type1 =  DFNT_INT8;
           else if (size == 2) number_type1 =  DFNT_INT16;
           else if (size == 4) number_type1 =  DFNT_INT32;
           else if (size == 8) number_type1 =  DFNT_INT64;
        }
      }
   else if (class == H5T_FLOAT) {
      if (size == 4) number_type1 =  DFNT_FLOAT;
      else if (size == 8) number_type1 =  DFNT_FLOAT64;
      }

   data = get_memory(l, number_type1);

   status = H5Dread(dataset1, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, data); //DRL

   current_dims[0] = 1;
   fdata = (float *)data;
   SDsetattr(sds_out, "scale_factor", DFNT_FLOAT, current_dims[0], (VOIDP)&(fdata[0]));
   SDsetattr(sds_out, "add_offset", DFNT_FLOAT, current_dims[0], (VOIDP)&(fdata[1]));
   H5Dclose(dataset1);
   free(data);
   }

/**************************************/




      /* and close everything */
      H5Sclose(dataspace1);
      H5Fclose(file);
      }
   SDendaccess(sds_out);
   SDend(sd_id2);

   }


} /*   end of main()   */

/*
 * Operator function.
 */
herr_t group_info(hid_t loc_id, const char *name, void *opdata)
{
int *idx;
H5G_stat_t statbuf;

idx = (int *)opdata;

    /* avoid warnings */
    loc_id = loc_id;
    opdata = opdata;

    /*
     * Display group name. The name is passed to the function by
     * the Library.
     */
/*    printf("\n");
    printf("%d %d Group Name : ", idx[0], idx[1]);
    puts(name);
*/
    /* if this "group name" is actually a dataset name, start populating the
       dataset character grid */

    H5Gget_objinfo(loc_id, name, FALSE, &statbuf);
    switch (statbuf.type) {
    case H5G_GROUP:

       if(n_groups < MAX_DATASETS) {
          if (idx[0] == -1) {
             sprintf(groups[idx[1]++], "/%s", name);
	     }
          else {
             sprintf(groups[idx[1]++], "%s/%s", groups[idx[0]], name);
	     }
          n_groups++;
           }
         break;
    case H5G_DATASET:

       if(n_datasets < MAX_DATASETS) {
          if (idx[0] == -1) {
             sprintf(datasets[n_datasets], "/%s", name);
	     }
          else {
             sprintf(datasets[n_datasets], "%s/%s", groups[idx[0]], name);
	     }
          n_datasets++;
           }
         break;
    case H5G_TYPE:
             /*printf("Type, %s\n", name);*/
         break;
    default:
             /*printf("Other, %s\n", name);*/
         break;
    }

/*    if(n_groups < MAX_DATASETS) {
       if (idx[0] == -1) {
          sprintf(groups[idx[1]++], "/%s", name);
	  }
       else {
          sprintf(groups[idx[1]++], "%s/%s", groups[idx[0]], name);
	  }
       n_groups++;

       }
 */
    return 0;
 }


hid_t get_H5_datatype_from_H4(int32 i)
{
switch (i) {
   case(DFNT_CHAR):
   case(DFNT_INT8):
        return (H5T_NATIVE_CHAR);
	break;
   case(DFNT_UCHAR):
   case(DFNT_UINT8):
        return (H5T_NATIVE_UCHAR);
	break;
   case(DFNT_INT16):
        return (H5T_NATIVE_SHORT);
	break;
   case(DFNT_UINT16):
        return (H5T_NATIVE_USHORT);
	break;
   case(DFNT_INT32):
        return (H5T_NATIVE_INT);
	break;
   case(DFNT_UINT32):
        return (H5T_NATIVE_UINT);
	break;
   case(DFNT_INT64):
        return (H5T_NATIVE_LONG);
	break;
   case(DFNT_UINT64):
        return (H5T_NATIVE_ULONG);
	break;
   case(DFNT_FLOAT):
        return (H5T_NATIVE_FLOAT);
	break;
   case(DFNT_FLOAT64):
        return (H5T_NATIVE_DOUBLE);
	break;
  }
return (-1);
}


void transfer_attributes_to_HDF5(int32 id1, hid_t dataset)
{  /* Writes from HDF4 file to HDF5 file.  No byte-swapping is done here */
int32 i, j, jj;
int32 n_attr1, n_sets1, count1, rank1, dims1[5], number_type1;
char name1[MAXLENGTH];
char attrib[MAXLENGTH], attrib1[MAXLENGTH];
char *charattr;
uchar8 *ucharattr;
int8 *i8attr;
uint8 *ui8attr;
int16 *shortattr;
uint16 *ushortattr;
int32 *intattr;
uint32 *uintattr;
float32 *floatattr;
float64 *doubleattr;
long *longattr;
unsigned long *ulongattr;
hsize_t dims[1];
hid_t attr, dataspace, datatype;

SDgetinfo(id1, name1, &rank1, dims1, &number_type1, &n_attr1);

for (j=0;j<n_attr1;j++) {
     SDattrinfo(id1, j, attrib1, &number_type1, &count1);
     dims[0] = count1;
     if (count1 == 1) dataspace = H5Screate(H5S_SCALAR);
     else dataspace = H5Screate_simple(1, dims, NULL);

     switch(number_type1) {
       case DFNT_CHAR8:
       case DFNT_UCHAR8:
  	     if ((charattr = (char *)malloc((count1+1)*sizeof(char))) == NULL) {
	         printf("Out of memory, array 'charattr'\n");
		 return;
		 }
	     datatype = H5Tcopy(H5T_C_S1);
             H5Tset_size(datatype, dims[0]);
	     dims[0] = 1;  /* one string */
	     dataspace = H5Screate_simple(1, dims, NULL);

             SDreadattr(id1, j, charattr);
	     charattr[count1] = '\0';

	     attr = H5Acreate(dataset, attrib1, datatype, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, datatype, charattr);
             H5Aclose(attr);
 	     free(charattr);
             break;
       case DFNT_INT8:
	     if ((i8attr = (int8 *)malloc(count1*sizeof(int8))) == NULL) {
	         printf("Out of memory, array 'i8attr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, i8attr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_CHAR, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_CHAR, i8attr);
             H5Aclose(attr);
             free(i8attr);

             break;
       case DFNT_UINT8:
	     if ((ui8attr = (uint8 *)malloc(count1*sizeof(uint8))) == NULL) {
	         printf("Out of memory, array 'ui8attr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, ui8attr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_UCHAR, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_UCHAR, ui8attr);
             H5Aclose(attr);
             free(ui8attr);

             break;
       case DFNT_INT16:
	     if ((shortattr = (short *)malloc(count1*sizeof(short))) == NULL) {
	         printf("Out of memory, array 'shortattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, shortattr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_SHORT, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_SHORT, shortattr);
             H5Aclose(attr);
             free(shortattr);

             break;
       case DFNT_UINT16:
	     if ((ushortattr = (unsigned short *)malloc(count1*sizeof(unsigned short))) == NULL) {
	         printf("Out of memory, array 'ushortattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, ushortattr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_USHORT, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_USHORT, ushortattr);
             H5Aclose(attr);
             free(ushortattr);

             break;
       case DFNT_INT32:
	     if ((intattr = (int32 *)malloc(count1*sizeof(int32))) == NULL) {
	         printf("Out of memory, array 'intattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, intattr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_INT, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_INT, intattr);
             H5Aclose(attr);
             free(intattr);

             break;
       case DFNT_UINT32:
	     if ((uintattr = (uint32 *)malloc(count1*sizeof(uint32))) == NULL) {
	         printf("Out of memory, array 'uintattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, uintattr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_UINT, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_UINT, uintattr);
             H5Aclose(attr);
             free(uintattr);

             break;
       case DFNT_FLOAT:
	     if ((floatattr = (float *)malloc(count1*sizeof(float))) == NULL) {
	         printf("Out of memory, array 'floatattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, floatattr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_FLOAT, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_FLOAT, floatattr);
             H5Aclose(attr);
             free(floatattr);

             break;
       case DFNT_FLOAT64:
	     if ((doubleattr = (double *)malloc(count1*sizeof(double))) == NULL) {
	         printf("Out of memory, array 'doubleattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, doubleattr);

	     attr = H5Acreate(dataset, attrib1, H5T_NATIVE_DOUBLE, dataspace, H5P_DEFAULT);
	     H5Awrite(attr, H5T_NATIVE_DOUBLE, doubleattr);
             H5Aclose(attr);
             free(doubleattr);

             break;


   }
   }  /*   for (j=0;j<n_attr1;j++)  */
}

void write_local_SDS_attribute(int32 sds_out, int dim, char name[1000], int big_array[10000],
                               ssize_t ord, ssize_t sign, ssize_t size, ssize_t class)
{  /* Writes from HDF5 file to HDF4 file */
char charclass[22], charord[22];
void class_check(ssize_t class, char ret[22]);
void order_check(ssize_t ord, char ret[22]);
int32 *i32_array;
uint32 *ui32_array;
float64 *f64_array;
float32 *f32_array;
int8 *i8_array;
uint8 *ui8_array;
int16 *i16_array;
uint16 *ui16_array;
long *lng_array;
unsigned long *ulng_array;
char *char_array, *tmpchar;
void swapbytes(void *val,int nbbytes);
int i;

/*
order_check(ord, charord);
class_check(class, charclass);

printf("Attr: '%s', ", name);
   if (class == H5T_INTEGER)
      printf("length=%d, %s, %s %s, %d byte%c\n",  dim, charord, ((sign==H5T_SGN_NONE) ? "unsigned\0" : "signed\0"), charclass, size, ((size>1) ? 's' : ' '));
   else
      printf("length=%d, %s, %s, %d byte%c\n", dim, charord, charclass, size, ((size>1) ? 's' : ' '));
 */

   switch (class) {
      case H5T_STRING:
         SDsetattr(sds_out, name, DFNT_CHAR, dim, (VOIDP)big_array);
	 break;
     case H5T_FLOAT:
         if (size == 4) {
            f32_array = (float *)big_array;
	    if (ord==H5T_ORDER_BE) {
	       for(i=0;i<dim;i++) swapbytes(&(f32_array[i]), 4);
	       }
            SDsetattr(sds_out, name, DFNT_FLOAT, dim, (VOIDP)f32_array);
	    }
         else {
            f64_array = (double *)big_array;
	    if (ord==H5T_ORDER_BE) {
	       for(i=0;i<dim;i++) swapbytes(&(f64_array[i]), 8);
	       }
            SDsetattr(sds_out, name, DFNT_FLOAT64, dim, (VOIDP)f64_array);
	    }
	 break;
      case H5T_INTEGER:
         if (dim == 8) {
	    if (sign==H5T_SGN_NONE) {
               ulng_array = (unsigned long *)big_array;
	       if (ord==H5T_ORDER_BE) {
	          for(i=0;i<dim;i++) swapbytes(&(ulng_array[i]), 8);
		  }
               SDsetattr(sds_out, name, DFNT_UINT64, dim, (VOIDP)ulng_array);
	       }
	    else {
               lng_array = (long *)big_array;
	       if (ord==H5T_ORDER_BE) {
	          for(i=0;i<dim;i++) swapbytes(&(lng_array[i]), 8);
		  }
               SDsetattr(sds_out, name, DFNT_INT64, dim, (VOIDP)ulng_array);
	       }
	    }
         else if (dim == 4) {
	    if (sign==H5T_SGN_NONE) {
               ui32_array = (uint32 *)big_array;
	       if (ord==H5T_ORDER_BE) {
	          for(i=0;i<dim;i++) swapbytes(&(ui32_array[i]), 4);
		  }
               SDsetattr(sds_out, name, DFNT_UINT32, dim, (VOIDP)ui32_array);
	       }
	    else {
               i32_array = (int32 *)big_array;
	       if (ord==H5T_ORDER_BE) {
	          for(i=0;i<dim;i++) swapbytes(&(i32_array[i]), 4);
		  }
               SDsetattr(sds_out, name, DFNT_INT32, dim, (VOIDP)i32_array);
	       }
	    }
         else if (dim == 2) {
	    if (sign==H5T_SGN_NONE) {
               ui16_array = (uint16 *)big_array;
	       if (ord==H5T_ORDER_BE) {
	          for(i=0;i<dim;i++) swapbytes(&(ui16_array[i]), 2);
		  }
               SDsetattr(sds_out, name, DFNT_UINT16, dim, (VOIDP)ui16_array);
	       }
	    else {
               i16_array = (int16 *)big_array;
	       if (ord==H5T_ORDER_BE) {
	          for(i=0;i<dim;i++) swapbytes(&(i16_array[i]), 2);
		  }
               SDsetattr(sds_out, name, DFNT_INT16, dim, (VOIDP)i16_array);
	       }
	    }
         else {
	    if (sign==H5T_SGN_NONE) {
               ui8_array = (uint8 *)big_array;
               SDsetattr(sds_out, name, DFNT_UINT8, dim, (VOIDP)ui8_array);
	       }
	    else {
               i8_array = (int8 *)big_array;
               SDsetattr(sds_out, name, DFNT_INT8, dim, (VOIDP)i8_array);
	       }
	    }
	 break;
	 default:
	 break;
      }

return;
}


herr_t attr_info(hid_t loc_id, const char *name, void *opdata)
{
hid_t attr_id;
hid_t datatype, dataspace;
ssize_t class, ord, sign, size;
hsize_t *current_dims, *max_dims;
int rank, dim;
char buf[256];
int i, intarr[256];
float *fltarr;
double *dblarr;
char charclass[22], charord[22];
void class_check(ssize_t class, char ret[22]);
void order_check(ssize_t ord, char ret[22]);
int32 *i32_array;
uint32 *ui32_array;
float64 *f64_array;
float32 *f32_array;
int8 *i8_array;
uint8 *ui8_array;
int16 *i16_array;
uint16 *ui16_array;
long *lng_array;
unsigned long *ulng_array;
char *char_array, *tmpchar;
void swapbytes(void *val,int nbbytes);

attr_id = H5Aopen_name(loc_id, name);

printf("Attr: '%s', ", name);

/* get dataspace-related information */

dataspace = H5Aget_space(attr_id);

   rank = H5Sget_simple_extent_ndims(dataspace);

   if (rank == 0) {  /* then it's scalar? */
      rank = 1;
      dim = 1;
      }
   else {
      current_dims = (hsize_t *)malloc(rank*sizeof(hsize_t));
      max_dims = (hsize_t *)malloc(rank*sizeof(hsize_t));

      H5Sget_simple_extent_dims(dataspace, current_dims, max_dims);  /* assuming made with H5Screate_simple() */
      dim = current_dims[0];
      free(current_dims);
      free(max_dims);

      }

   H5Sclose(dataspace);

/* get datatype-related information */

datatype = H5Aget_type (attr_id);


   ord = H5Tget_order(datatype);
   sign = H5Tget_sign(datatype);
   size = H5Tget_size(datatype);
   class = H5Tget_class(datatype);

   order_check(ord, charord);
   class_check(class, charclass);


/* let's assume no float/integer value has more than 256 entries */
fltarr = (float *)malloc(256*sizeof(float));
dblarr = (double *)malloc(256*sizeof(double));
lng_array = (long *)malloc(256*sizeof(long));
ulng_array = (unsigned long *)malloc(256*sizeof(unsigned long));
i32_array = (int32 *)malloc(256*sizeof(int32));
ui32_array = (uint32 *)malloc(256*sizeof(uint32));
i16_array = (int16 *)malloc(256*sizeof(int16));
ui16_array = (uint16 *)malloc(256*sizeof(uint16));
i8_array = (int8 *)malloc(256*sizeof(int8));
ui8_array = (uint8 *)malloc(256*sizeof(uint8));


   if (class == H5T_INTEGER)
      printf("length=%d, %s, %s %s, %d byte%c\n",  dim, charord, ((sign==H5T_SGN_NONE) ? "unsigned\0" : "signed\0"), charclass, size, ((size>1) ? 's' : ' '));
   else
      printf("length=%d, %s, %s, %d byte%c\n", dim, charord, charclass, size, ((size>1) ? 's' : ' '));

   switch (class) {
      case H5T_STRING:
         char_array = (char *)malloc(size*dim*sizeof(char));
	 H5Aread (attr_id, datatype, char_array);
	 tmpchar = char_array;
	 for(i=0;i<dim;i++) {
	    printf("      %s\n", tmpchar);
	    tmpchar += size;
	    }
	 free(char_array);
	 break;
     case H5T_FLOAT:
         if (size == 4) {
	    H5Aread (attr_id, datatype, fltarr);
	    for(i=0;i<dim;i++) {
	       if (ord==H5T_ORDER_BE)  swapbytes(&(fltarr[i]), 4);
	       printf("     %f\n", fltarr[i]);
	       }
	    }
         else {
	    H5Aread (attr_id, datatype, dblarr);
	    for(i=0;i<dim;i++) {
	       if (ord==H5T_ORDER_BE) swapbytes(&(dblarr[i]), 8);
	       printf("     %lf\n", dblarr[i] );
	       }
	    }
	 break;
      case H5T_INTEGER:
         if (size == 8) {
	    if (sign==H5T_SGN_NONE) {
	       H5Aread (attr_id, datatype, ulng_array);
	       for(i=0;i<dim;i++) {
	          if (ord==H5T_ORDER_BE) swapbytes(&(ulng_array[i]), 8);
	          printf("     %ld\n", ulng_array[i]);
		  }
	       }
	    else {
	       H5Aread (attr_id, datatype, lng_array);
	       for(i=0;i<dim;i++) {
	          if (ord==H5T_ORDER_BE) swapbytes(&(lng_array[i]), 8);
	          printf("     %ld\n", lng_array[i]);
		  }
	       }
	    }
         else if (size == 4) {
	    if (sign==H5T_SGN_NONE) {
	       H5Aread (attr_id, datatype, ui32_array);
	       for(i=0;i<dim;i++) {
	          if (ord==H5T_ORDER_BE) swapbytes(&(ui32_array[i]), 4);
	          printf("     %d\n", ui32_array[i]);
		  }
	       }
	    else {
	       H5Aread (attr_id, datatype, i32_array);
	       for(i=0;i<dim;i++) {
	          if (ord==H5T_ORDER_BE) swapbytes(&(i32_array[i]), 4);
	          printf("     %d\n", i32_array[i]);
		  }
	       }
	    }
         else if (size == 2) {
	    if (sign==H5T_SGN_NONE) {
	       H5Aread (attr_id, datatype, ui16_array);
	       for(i=0;i<dim;i++) {
	          if (ord==H5T_ORDER_BE) swapbytes(&(ui16_array[i]), 2);
	          printf("     %d\n", ui16_array[i]);
		  }
	       }
	    else {
	       H5Aread (attr_id, datatype, i16_array);
	       for(i=0;i<dim;i++) {
	          if (ord==H5T_ORDER_BE) swapbytes(&(i16_array[i]), 2);
	          printf("     %d\n", i16_array[i]);
		  }
	       }
	    }
         else {
	    if (sign==H5T_SGN_NONE) {
	       H5Aread (attr_id, datatype, ui8_array);
	       for(i=0;i<dim;i++) {
	          printf("     %d\n", ui8_array[i]);
		  }
	       }
	    else {
	       H5Aread (attr_id, datatype, i8_array);
	       for(i=0;i<dim;i++) {
	          printf("     %d\n", i8_array[i]);
		  }
	       }
	    }
	 break;
	 default:
	 break;
      }

H5Tclose(datatype);

free(fltarr);
free(dblarr);
free(i32_array);
free(ui32_array);
free(i8_array);
free(ui8_array);
free(i16_array);
free(ui16_array);
free(lng_array);
free(ulng_array);


H5Aclose(attr_id);

return(0);
}

void order_check(ssize_t ord, char ret[22])
{

switch(ord) {
    case H5T_ORDER_LE:
      strcpy(ret, "little-endian\0");
      break;
    case H5T_ORDER_BE:
      strcpy(ret, "big-endian\0");
      break;
    case H5T_ORDER_VAX:
      strcpy(ret, "VAX mixed-byte order\0");
      break;
    /*case H5T_ORDER_MIXED:
      strcpy(ret, "mixed, compound\0");
      break;*/
    case H5T_ORDER_NONE:
      strcpy(ret, "none\0");
      break;
   default:
      strcpy(ret, "\0");
      break;
   }
return;
}

void class_check(ssize_t class, char ret[22])
{

switch(class) {
   case H5T_INTEGER:
      strcpy(ret, "INTEGER\0");
      break;
   case H5T_FLOAT:
      strcpy(ret, "FLOAT\0");
      break;
   case H5T_STRING:
      strcpy(ret, "STRING\0");
      break;
   case H5T_BITFIELD:
      strcpy(ret, "BITFIELD\0");
      break;
   case H5T_OPAQUE:
      strcpy(ret, "OPAQUE\0");
      break;
   case H5T_COMPOUND:
      strcpy(ret, "COMPOUND\0");
      break;
   case H5T_REFERENCE:
      strcpy(ret, "REFERENCE\0");
      break;
   case H5T_ENUM:
      strcpy(ret, "ENUM\0");
      break;
   case H5T_VLEN:
      strcpy(ret, "VLEN\0");
      break;
   case H5T_ARRAY:
      strcpy(ret, "ARRAY\0");
      break;
   default:
      strcpy(ret, "\0");
      break;
}
return;
}


/*****************************************************************************************************************
 **************  start of get_memory() ***************************************************************************
 ************  Can be deleted once integrated into imager    **********************************************/

void *get_memory(int32 count, int32 type)
{
    /* New, v3.5: will pass NULL pointers through to calling routine during zooms */
int32 *i32_array;
uint32 *ui32_array;
float64 *f64_array;
float32 *f32_array;
int8 *i8_array;
uint8 *ui8_array;
int16 *i16_array;
uint16 *ui16_array;
char *char_array;
uchar8 *uchar_array;
int32 size;
long *i64_array;
unsigned long *ui64_array;
void mem_error_message(void);

if (count <= 0) printf("Bug in program: call to allocate %d pixels...\n", count);

       switch(type) {
           case 4:
              char_array = (char *)calloc(count, sizeof(char));
	      if (char_array == (char *)NULL) {
	         mem_error_message();
	         }
	      return((void *)char_array);
              break;
           case 3:
              uchar_array = (uchar8 *)calloc(count, sizeof(char));
	      if (uchar_array == (uchar8 *)NULL) {
	         mem_error_message();
	         }
 	      return((void *)uchar_array);
              break;
           case 5:
              f32_array = (float *)calloc(count, sizeof(float32));
	      if (f32_array == (float *)NULL) {
	         mem_error_message();
	         }
	      return((void *)f32_array);
              break;
           case 6:
              f64_array = (double *)calloc(count, sizeof(float64));
	      if (f64_array == (double *)NULL) {
	         mem_error_message();
	         }
 	      return((void *)f64_array);
              break;
           case 20:
              i8_array = (int8 *)calloc(count, sizeof(int8));
	      if (i8_array == (int8 *)NULL) {
	         mem_error_message();
	         }
	      return((void *)i8_array);
              break;
           case 21:
              ui8_array = (uint8 *)calloc(count, sizeof(uint8));
	      if (ui8_array == (uint8 *)NULL) {
	         mem_error_message();
	         }
	      return((void *)ui8_array);
              break;
           case 22:
             i16_array = (int16 *)calloc(count, sizeof(int16));
	      if (i16_array == (int16 *)NULL) {
	         mem_error_message();
	         }
	      return((void *)i16_array);
              break;
           case 23:
              ui16_array = (uint16 *)calloc(count, sizeof(uint16));
	      if (ui16_array == (uint16 *)NULL) {
	         mem_error_message();
	         }
	      return((void *)ui16_array);
              break;
           case 24:
              i32_array = (int32 *)calloc(count, sizeof(int32));
	      if (i32_array == (int32 *)NULL) {
	         mem_error_message();
	         }
	      return((void *)i32_array);
              break;
           case 25:
              ui32_array = (uint32 *)calloc(count, sizeof(uint32));
	      if (ui32_array == (uint32 *)NULL) {
	         mem_error_message();
	         }
	      return((void *)ui32_array);
              break;
           case 26:
              i64_array = (long *)calloc(count, sizeof(long));
	      if (i64_array == (long *)NULL) {
	         mem_error_message();
	         }
	      return((void *)i64_array);
              break;
           case 27:
              ui64_array = (unsigned long *)calloc(count, sizeof(unsigned long));
	      if (ui64_array == (unsigned long *)NULL) {
	         mem_error_message();
	         }
	      return((void *)ui64_array);
              break;
                         }
}
void mem_error_message(void)
{
printf("Memory error\n");
return;
}

void swapbytes(void *val,int nbbytes) {
/******************************************************************************
!C
!Routine: swapbytes

!Description:  Does a byte reversal on value "val."

!Revision History:
 Original version:    Nazmi Z El Saleous and Eric Vermote

!Input Parameters:
        val           an array of values (cast to void)
        nbbytes       the length of val (in bytes; cannot be greater than 17
                      bytes)

!Output Parameters:
        val           (updated)

!Return value:
        none

!References and Credits:

!Developers:
      Nazmi Z El Saleous
      Eric Vermote
      University of Maryland / Dept. of Geography
      nazmi.elsaleous@gsfc.nasa.gov

!Design Notes:

!END
*******************************************************************************/
   char *tmpptr1,*tmpptr2,tmpstr[17];
   int i;

   memcpy(tmpstr,val,nbbytes);
   tmpptr1=(char *) val;
   tmpptr2=(char *) tmpstr;
   for (i=0;i<nbbytes;i++)
    tmpptr1[i]=tmpptr2[nbbytes-i-1];
}


void *get_image(int32 id, int32 *dims, int32 type, int *size)
{
int32 *i32_array;
uint32 *ui32_array;
long *i64_array;
unsigned long *ui64_array;
float64 *f64_array;
float32 *f32_array;
int8 *i8_array;
uint8 *ui8_array;
int16 *i16_array;
uint16 *ui16_array;
char *char_array;
uchar8 *uchar_array;
int i,count;
int32 start[5];

start[0] = start[1] = start[2] = start[3] = start[4] = *size = 0;
i=0;
count = dims[i++];
while(dims[i] != 0) count *= dims[i++];


       switch(type) {
           case 4:
	      *size = count;
              char_array = (char *)malloc(*size);
              SDreaddata(id, start, NULL, dims, char_array);
	      return((void *)char_array);
              break;
           case 3:
	      *size = count;
              uchar_array = (uchar8 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, uchar_array);
	      return((void *)uchar_array);
              break;
           case 5:
	      *size = count*sizeof(float);
              f32_array = (float *)malloc(*size);
              SDreaddata(id, start, NULL, dims, f32_array);
	      return((void *)f32_array);
              break;
           case 6:
	      *size = count*sizeof(double);
              f64_array = (double *)malloc(*size);
              SDreaddata(id, start, NULL, dims, f64_array);
	      return((void *)f64_array);
              break;
           case 20:
	      *size = count*sizeof(int8);
              i8_array = (int8 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, i8_array);
	      return((void *)i8_array);
              break;
           case 21:
	      *size = count*sizeof(uint8);
              ui8_array = (uint8 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, ui8_array);
	      return((void *)ui8_array);
              break;
           case 22:
	      *size = count*sizeof(int16);
              i16_array = (int16 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, i16_array);
	      return((void *)i16_array);
              break;
           case 23:
	      *size = count*sizeof(uint16);
              ui16_array = (uint16 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, ui16_array);
	      return((void *)ui16_array);
              break;
           case 24:
	      *size = count*sizeof(int32);
              i32_array = (int32 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, i32_array);
	      return((void *)i32_array);
              break;
           case 25:
	      *size = count*sizeof(uint32);
              ui32_array = (uint32 *)malloc(*size);
              SDreaddata(id, start, NULL, dims, ui32_array);
	      return((void *)ui32_array);
              break;
           case 26:
	      *size = count*sizeof(long);
              i64_array = (long *)malloc(*size);
              SDreaddata(id, start, NULL, dims, i64_array);
	      return((void *)i64_array);
              break;
           case 27:
	      *size = count*sizeof(unsigned long);
              ui64_array = (unsigned long *)malloc(*size);
              SDreaddata(id, start, NULL, dims, ui64_array);
	      return((void *)ui64_array);
              break;
                         }
}

void transfer_attributes(int32 id1, int32 id_out)
{
int32 i, j, jj;
int32 n_attr1, n_sets1, count1, rank1, dims1[5], number_type1;
char name1[MAXLENGTH];
char attrib[MAXLENGTH], attrib1[MAXLENGTH];
char label[MAXLENGTH], tag[MAXLENGTH];
short *contents;
short ii;
char *newstring;
char *charattr;
uchar8 *ucharattr;
int16 *shortattr;
uint16 *ushortattr;
int32 *intattr;
uint32 *uintattr;
float32 *floatattr;
float64 *doubleattr;
long *longattr;
unsigned long *ulongattr;
char charatt;
uchar8 ucharatt;
int16 shortatt;
uint16 ushortatt;
int32 intatt;
uint32 uintatt;
long longatt;
unsigned long ulongatt;
float32 floatatt;
float64 doubleatt;

SDgetinfo(id1, name1, &rank1, dims1, &number_type1, &n_attr1);

for (j=0;j<n_attr1;j++) {
     SDattrinfo(id1, j, attrib1, &number_type1, &count1);

     switch(number_type1) {
       case DFNT_CHAR8:
       case DFNT_INT8:
           if (count1 == 1) {
             SDreadattr(id1, j, &charatt);
	     SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&charatt);
	                    }
	   else {
	     if ((charattr = (char *)malloc((count1+1)*sizeof(char))) == NULL) {
	         printf("Out of memory, array 'charattr'\n");
		 return;
	                                                                       }
             SDreadattr(id1, j, charattr);
	     charattr[count1] = '\0';
	     SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)charattr);
 	     free(charattr);
	        }
           break;
       case DFNT_UCHAR8:    /* treat them like integers */
       case DFNT_UINT8:
           if (count1 == 1) {
             SDreadattr(id1, j, &ucharatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&ucharatt);
 	                    }
	   else {
	     if ((ucharattr =
	       (unsigned char *)malloc(count1*sizeof(unsigned char))) == NULL) {
	         printf("Out of memory, array 'ucharattr'\n");
		 return;
	                                                                       }
             SDreadattr(id1, j, ucharattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)ucharattr);
	     free(ucharattr);
	        }
           break;
       case DFNT_INT16:
           if (count1 == 1) {
             SDreadattr(id1, j, &shortatt);
	     SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&shortatt);
	                    }
	   else {
	     if ((shortattr = (short *)malloc(count1*sizeof(short))) == NULL) {
	         printf("Out of memory, array 'shortattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, shortattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)shortattr);
             free(shortattr);
	        }
           break;
       case DFNT_UINT16:
           if (count1 == 1) {
             SDreadattr(id1, j, &ushortatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&ushortatt);
 	                    }
	   else {
	     if ((ushortattr = (unsigned short *)malloc(count1*sizeof(unsigned short))) == NULL) {
	         printf("Out of memory, array 'ushortattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, ushortattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)ushortattr);
	     free(ushortattr);
	        }
           break;
       case DFNT_INT32:
           if (count1 == 1) {
             SDreadattr(id1, j, &intatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&intatt);
	                   }
	   else {
	     if ((intattr = (int32 *)malloc(count1*sizeof(int32))) == NULL) {
	         printf("Out of memory, array 'intattr'\n");
		 return;
	                                                                    }
             SDreadattr(id1, j, intattr);
	     SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)intattr);
	     free(intattr);
	        }
           break;
       case DFNT_UINT32:
           if (count1 == 1) {
             SDreadattr(id1, j, &uintatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&uintatt);
 	                     }
	   else {
	     if ((uintattr = (uint32 *)malloc(count1*sizeof(uint32))) == NULL) {
	         printf("Out of memory, array 'uintattr'\n");
		 return;
	                                                                       }
             SDreadattr(id1, j, uintattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)uintattr);
	     free(uintattr);
	        }
           break;
       case DFNT_INT64:
           if (count1 == 1) {
             SDreadattr(id1, j, &longatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&longatt);
	                   }
	   else {
	     if ((longattr = (long *)malloc(count1*sizeof(long))) == NULL) {
	         printf("Out of memory, array 'longattr'\n");
		 return;
	                                                                    }
             SDreadattr(id1, j, longattr);
	     SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)longattr);
	     free(longattr);
	        }
           break;
       case DFNT_UINT64:
           if (count1 == 1) {
             SDreadattr(id1, j, &ulongatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&ulongatt);
 	                     }
	   else {
	     if ((ulongattr = (unsigned long *)malloc(count1*sizeof(unsigned long))) == NULL) {
	         printf("Out of memory, array 'ulongattr'\n");
		 return;
	                                                                       }
             SDreadattr(id1, j, ulongattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)ulongattr);
	     free(ulongattr);
	        }
           break;
       case DFNT_FLOAT:
           if (count1 == 1) {
             SDreadattr(id1, j, &floatatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&floatatt);
 	                     }
	   else {
	     if ((floatattr = (float *)malloc(count1*sizeof(float))) == NULL) {
	         printf("Out of memory, array 'floatattr'\n");
		 return;
	                                                                      }

             SDreadattr(id1, j, floatattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)floatattr);
	     free(floatattr);
	        }
           break;
       case DFNT_DOUBLE:
           if (count1 == 1) {
             SDreadattr(id1, j, &doubleatt);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)&doubleatt);
 	                     }
	   else {
	     if ((doubleattr = (double *)malloc(count1*sizeof(double))) == NULL) {
	         printf("Out of memory, array 'doubleattr'\n");
		 return;
	                                                                      }
             SDreadattr(id1, j, doubleattr);
             SDsetattr(id_out, attrib1, number_type1, count1, (VOIDP)doubleattr);
	     free(doubleattr);
	        }
           break;
                   }  /* switch(..) */
                        }  /* for (j=0;j<n_gattr;j++) */


}
