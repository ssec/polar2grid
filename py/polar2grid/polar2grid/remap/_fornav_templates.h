#ifndef _FORNAV_TEMPLATES_H
#define _FORNAV_TEMPLATES_H

// The types used for all of the intermediate storage between input swath pixels and output grid pixels
// Mainly here for testing, but should never be a non-floating type
typedef float weight_type;
typedef float ewa_param_type;
typedef float accum_type;
//typedef double weight_type;
//typedef double ewa_param_type;
//typedef double accum_type;

//const weight_type EPSILON = 1e-8;
#define EPSILON (1e-8)

typedef struct {
    ewa_param_type a;
    ewa_param_type b;
    ewa_param_type c;
    ewa_param_type f;
    ewa_param_type u_del;
    ewa_param_type v_del;
} ewa_parameters;

typedef struct {
    int count;
    weight_type min;
    weight_type distance_max;
    weight_type delta_max;
    weight_type sum_min;
    weight_type alpha;
    weight_type qmax;
    weight_type qfactor;
    weight_type *wtab;
} ewa_weight;

template<typename CR_TYPE, typename IMAGE_TYPE>
extern int compute_ewa(size_t chan_count, int maximum_weight_mode,
        size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows, CR_TYPE *uimg, CR_TYPE *vimg,
        IMAGE_TYPE **images, IMAGE_TYPE img_fill, accum_type **grid_accums, weight_type **grid_weights, ewa_weight *ewaw, ewa_parameters *ewap);

#endif