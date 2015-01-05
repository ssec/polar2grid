#include <stddef.h>
#include "math.h"
#include "Python.h"
#include "numpy/arrayobject.h"
#include "_fornav_templates.h"
template<typename CR_TYPE, typename IMAGE_TYPE>
int test_cpp_templates(CR_TYPE x, IMAGE_TYPE y) {
    if (x) {
        return 0;
    } else if (y) {
        return 1;
    } else {
        return 2;
    }
}

template int test_cpp_templates<int, int>(int, int);
template int test_cpp_templates<npy_uint8, npy_int8>(npy_uint8, npy_int8);

template<typename CR_TYPE, typename IMAGE_TYPE>
int compute_ewa(size_t chan_count, int maximum_weight_mode,
        size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows, CR_TYPE *uimg, CR_TYPE *vimg, CR_TYPE cr_fill,
        IMAGE_TYPE **images, IMAGE_TYPE img_fill, double **grid_accums, double **grid_weights, ewa_weight *ewaw, ewa_parameters *ewap) {
  // This was originally copied from a cython C file for 32-bit float inputs (that explains some of the weird parens and other syntax
  // TODO: Make `this_ewap` a pointer to the structure, I think the copying to the stack might actually be wasting time
  int got_point;
  unsigned int row;
  unsigned int col;
  ewa_parameters *this_ewap;
  CR_TYPE u0;
  CR_TYPE v0;
  int iu1;
  int iu2;
  int iv1;
  int iv2;
  int iu;
  int iv;
  double ddq;
  double dq;
  double q;
  double u;
  double v;
  double a2up1;
  double au2;
  double bu;
  int iw;
  double weight;
  IMAGE_TYPE this_val;
  unsigned int swath_offset;
  unsigned int grid_offset;
  size_t chan;

  got_point = 0;
  for (row = 0, swath_offset=0; row < swath_rows; row+=1) {
    for (col = 0, this_ewap = ewap; col < swath_cols; col+=1, this_ewap++, swath_offset++) {

      u0 = uimg[swath_offset];
      v0 = vimg[swath_offset];

      if ((u0 < 0.0) || (v0 < 0.0)) {
        continue;
      }

      iu1 = ((int)(u0 - this_ewap->u_del));
      iu2 = ((int)(u0 + this_ewap->u_del));
      iv1 = ((int)(v0 - this_ewap->v_del));
      iv2 = ((int)(v0 + this_ewap->v_del));

      if (iu1 < 0) {
        iu1 = 0;
      }
      if (iu2 >= grid_cols) {
        iu2 = (grid_cols - 1);
      }
      if (iv1 < 0) {
        iv1 = 0;
      }
      if (iv2 >= grid_rows) {
        iv2 = (grid_rows - 1);
      }

      if (iu1 < grid_cols && iu2 >= 0 && iv1 < grid_rows && iv2 >= 0) {
        got_point = 1;
        ddq = (2.0 * this_ewap->a);

        u = (iu1 - u0);
        a2up1 = (this_ewap->a * ((2.0 * u) + 1.0));
        bu = (this_ewap->b * u);
        au2 = ((this_ewap->a * u) * u);

        for (iv = iv1; iv <= iv2; iv++) {
          v = (iv - v0);
          dq = (a2up1 + (this_ewap->b * v));
          q = ((((this_ewap->c * v) + bu) * v) + au2);
          for (iu = iu1; iu <= iu2; iu++) {
            if ((q >= 0.0) && (q < this_ewap->f)) {
              iw = ((int)(q * ewaw->qfactor));
              if (iw >= ewaw->count) {
                iw = (ewaw->count - 1);
              }
              weight = (ewaw->wtab[iw]);
              grid_offset = ((iv * grid_cols) + iu);

              for (chan = 0; chan < chan_count; chan+=1) {
                this_val = ((images[chan])[swath_offset]);
                if (maximum_weight_mode) {
                  if (weight > grid_weights[chan][grid_offset]) {
                    ((grid_weights[chan])[grid_offset]) = weight;
                    if ((this_val == img_fill) || (isnan(this_val))) {
                      ((grid_accums[chan])[grid_offset]) = (double)NAN;
                    } else {
                      ((grid_accums[chan])[grid_offset]) = (double)this_val;
                    }
                  }
                } else {
                  if ((this_val != img_fill) && !(isnan(this_val))) {
                    ((grid_weights[chan])[grid_offset]) += weight;
                    ((grid_accums[chan])[grid_offset]) += (double)this_val * weight;
                  }
                }
              }
            }
            q += dq;
            dq += ddq;
          }
        }
      }
    }
  }

  /* function exit code */
  return got_point;
}

// Col/Row as 32-bit floats
template int compute_ewa<npy_float32, npy_float32>(size_t, int, size_t, size_t, size_t, size_t, npy_float32*, npy_float32*, npy_float32, npy_float32**, npy_float32, double**, double**, ewa_weight*, ewa_parameters*);
template int compute_ewa<npy_float32, npy_float64>(size_t, int, size_t, size_t, size_t, size_t, npy_float32*, npy_float32*, npy_float32, npy_float64**, npy_float64, double**, double**, ewa_weight*, ewa_parameters*);
template int compute_ewa<npy_float32, npy_int8>(size_t, int, size_t, size_t, size_t, size_t, npy_float32*, npy_float32*, npy_float32, npy_int8**, npy_int8, double**, double**, ewa_weight*, ewa_parameters*);
// Col/Row as 64-bit floats
template int compute_ewa<npy_float64, npy_float32>(size_t, int, size_t, size_t, size_t, size_t, npy_float64*, npy_float64*, npy_float64, npy_float32**, npy_float32, double**, double**, ewa_weight*, ewa_parameters*);
template int compute_ewa<npy_float64, npy_float64>(size_t, int, size_t, size_t, size_t, size_t, npy_float64*, npy_float64*, npy_float64, npy_float64**, npy_float64, double**, double**, ewa_weight*, ewa_parameters*);
template int compute_ewa<npy_float64, npy_int8>(size_t, int, size_t, size_t, size_t, size_t, npy_float64*, npy_float64*, npy_float64, npy_int8**, npy_int8, double**, double**, ewa_weight*, ewa_parameters*);
