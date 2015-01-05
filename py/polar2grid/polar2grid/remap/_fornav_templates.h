#ifndef _FORNAV_TEMPLATES_H
#define _FORNAV_TEMPLATES_H

typedef struct {
    double a;
    double b;
    double c;
    double f;
    double u_del;
    double v_del;
} ewa_parameters;

typedef struct {
    int count;
    double min;
    double distance_max;
    double delta_max;
    double sum_min;
    double alpha;
    double qmax;
    double qfactor;
    double *wtab;
} ewa_weight;

template<typename CR_TYPE, typename IMAGE_TYPE>
extern int test_cpp_templates(CR_TYPE, IMAGE_TYPE);

template<typename CR_TYPE, typename IMAGE_TYPE>
extern int compute_ewa(size_t chan_count, int maximum_weight_mode,
        size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows, CR_TYPE *uimg, CR_TYPE *vimg,
        IMAGE_TYPE **images, IMAGE_TYPE img_fill, double **grid_accums, double **grid_weights, ewa_weight *ewaw, ewa_parameters *ewap);

#endif