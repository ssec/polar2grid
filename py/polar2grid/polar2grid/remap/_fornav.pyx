import cython
cimport cython
import numpy
cimport numpy
cimport cpython
from libc.stdlib cimport calloc, malloc, free
from libc.math cimport log, exp, sqrt, isnan, NAN

cdef extern from "_fornav_templates.h":
    ctypedef float weight_type
    ctypedef float ewa_param_type
    ctypedef float accum_type
    cdef float EPSILON
    #ctypedef double weight_type
    #ctypedef double ewa_param_type
    #ctypedef double accum_type
    #cdef double EPSILON

    cdef int test_cpp_templates[CR_TYPE, IMAGE_TYPE](CR_TYPE x, IMAGE_TYPE y)

    cdef int compute_ewa[CR_TYPE, IMAGE_TYPE](size_t chan_count, bint maximum_weight_mode,
        size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows,
        CR_TYPE *uimg, CR_TYPE *vimg,
        IMAGE_TYPE **images, IMAGE_TYPE img_fill, accum_type **grid_accums, weight_type **grid_weights,
        ewa_weight *ewaw, ewa_parameters *ewap)

    ctypedef struct ewa_parameters:
        ewa_param_type a
        ewa_param_type b
        ewa_param_type c
        ewa_param_type f
        ewa_param_type u_del
        ewa_param_type v_del

    ctypedef struct ewa_weight:
        int count
        weight_type min
        weight_type distance_max
        weight_type delta_max
        weight_type sum_min
        weight_type alpha
        weight_type qmax
        weight_type qfactor
        weight_type *wtab

ctypedef fused cr_dtype:
    numpy.float32_t
    numpy.float64_t

# FUTURE: Add other types, but for now these are the basics
ctypedef fused image_dtype:
    numpy.float32_t
    numpy.float64_t
    numpy.int8_t

ctypedef fused grid_dtype:
    numpy.float32_t
    numpy.float64_t
    numpy.int8_t

ctypedef fused grid_weight_dtype:
    numpy.float32_t

@cython.cdivision(True)
cdef int initialize_weight(size_t chan_count, unsigned int weight_count, weight_type weight_min, weight_type weight_distance_max,
                            weight_type weight_delta_max, weight_type weight_sum_min, ewa_weight *ewaw):
    cdef unsigned int idx
    cdef weight_type *wptr

    ewaw.wtab = <weight_type *>calloc(weight_count, sizeof(weight_type))
    if ewaw.wtab is NULL:
        return -1

    ewaw.count = weight_count
    ewaw.min = weight_min
    ewaw.distance_max = weight_distance_max
    ewaw.delta_max = weight_delta_max
    ewaw.sum_min = weight_sum_min

    if weight_count < 2:
        # must be at least 2
        return -1
    if weight_min <= 0.0:
        # must be greater than 0
        return -1
    if weight_distance_max <= 0.0:
        # must be greater than 0
        return -1

    ewaw.qmax = ewaw.distance_max * ewaw.distance_max
    ewaw.alpha = -log(ewaw.min) / ewaw.qmax
    wptr = ewaw.wtab
    for idx in range(weight_count):
        wptr[idx] = exp(-ewaw.alpha * ewaw.qmax * idx / (ewaw.count - 1))

    # /*
    # *  Use i = (int)(q * ewaw->qfactor) to get element number i of wtab
    # *  corresponding to q.
    # *  Then for 0 < q < ewaw->qmax
    #     *    we have:
    # *      0   < i              <= ewaw->count - 1
    # *      1.0 > ewaw->wtab[i]  >= ewaw->min
    # */

    ewaw.qfactor = ewaw.count / ewaw.qmax
    return 0

cdef void deinitialize_weight(ewa_weight *ewaw):
    if ewaw.wtab:
        free(ewaw.wtab)

@cython.cdivision(True)
cdef int compute_ewa_parameters(size_t swath_cols, size_t swath_rows,
                                cr_dtype *uimg, cr_dtype *vimg, ewa_weight *ewaw, ewa_parameters *ewap):
    cdef ewa_param_type ux
    cdef ewa_param_type uy
    cdef ewa_param_type vx
    cdef ewa_param_type vy
    cdef ewa_param_type f_scale
    cdef ewa_param_type d
    cdef ewa_param_type qmax = ewaw.qmax
    cdef ewa_param_type distance_max = ewaw.distance_max
    cdef ewa_param_type delta_max = ewaw.delta_max
    cdef ewa_param_type u_del
    cdef ewa_param_type v_del

    cdef unsigned int rowsm1 = swath_rows - 1
    cdef unsigned int colsm1 = swath_cols - 1
    cdef unsigned int rowsov2 = swath_rows / 2
    cdef unsigned int col
    cdef ewa_parameters this_ewap

    for col in range(1, colsm1):
        # this_ewap = ewap[col]
        # Follow the middle row surrounding the pixel we are analyzing
        ux = (uimg[col - 1 + rowsov2 * swath_cols + 2] - uimg[col - 1 + rowsov2 * swath_cols]) / 2 * distance_max
        vx = (vimg[col - 1 + rowsov2 * swath_cols + 2] - vimg[col - 1 + rowsov2 * swath_cols]) / 2 * distance_max
        # ux = (*u_midl_row_next_col++ - *u_midl_row_prev_col++) / 2 * distance_max
        # vx = (*v_midl_row_next_col++ - *v_midl_row_prev_col++) / 2 * distance_max
        # Follow the first and last rows
        uy = (uimg[col + rowsm1 * swath_cols] - uimg[col]) / rowsm1 * distance_max
        vy = (vimg[col + rowsm1 * swath_cols] - vimg[col]) / rowsm1 * distance_max
        # uy = (*u_last_row_this_col++ - *u_frst_row_this_col++) / rowsm1 * distance_max
        # vy = (*v_last_row_this_col++ - *v_frst_row_this_col++) / rowsm1 * distance_max

        # /*
        # *  scale a, b, c, and f equally so that f = qmax
        #                                             */
        f_scale = ux * vy - uy * vx
        f_scale *= f_scale
        if f_scale < EPSILON:
            f_scale = EPSILON
        f_scale = qmax / f_scale
        this_ewap.a = (vx * vx + vy * vy) * f_scale
        this_ewap.b = -2.0 * (ux * vx + uy * vy) * f_scale
        this_ewap.c = (ux * ux + uy * uy) * f_scale
        d = 4.0 * this_ewap.a * this_ewap.c - this_ewap.b * this_ewap.b
        if d < EPSILON:
            d = EPSILON
        d = 4.0 * qmax / d
        this_ewap.f = qmax
        this_ewap.u_del = sqrt(this_ewap.c * d)
        this_ewap.v_del = sqrt(this_ewap.a * d)
        if this_ewap.u_del > delta_max:
            this_ewap.u_del = delta_max
        if this_ewap.v_del > delta_max:
            this_ewap.v_del = delta_max

        ewap[col] = this_ewap

    # /*
    # *  Copy the parameters from the penultimate column to the last column
    # */
    ewap[colsm1].a = ewap[colsm1 - 1].a
    ewap[colsm1].b = ewap[colsm1 - 1].b
    ewap[colsm1].c = ewap[colsm1 - 1].c
    ewap[colsm1].f = ewap[colsm1 - 1].f
    ewap[colsm1].u_del = ewap[colsm1 - 1].u_del
    ewap[colsm1].v_del = ewap[colsm1 - 1].v_del

    # /*
    # *  Copy the parameters from the second column to the first column
    # */
    ewap[0].a = ewap[1].a
    ewap[0].b = ewap[1].b
    ewap[0].c = ewap[1].c
    ewap[0].f = ewap[1].f
    ewap[0].u_del = ewap[1].u_del
    ewap[0].v_del = ewap[1].v_del

    return 0

@cython.cdivision(True)
cdef int write_grid_image(size_t grid_cols, size_t grid_rows,
                          accum_type *grid_accum, weight_type *grid_weights, bint maximum_weight_mode, weight_type weight_sum_min,
                          grid_dtype *output_image, grid_dtype fill):
    cdef accum_type chanf
    cdef weight_type this_weightp;
    cdef unsigned int col
    cdef int fill_count = 0

    if (weight_sum_min <= 0.0):
        weight_sum_min = EPSILON

    for col in range(grid_cols * grid_rows):
        chanf = grid_accum[col]
        this_weightp = grid_weights[col]
        # chanf = output_image[col]  # Used to be += bytes_per_cell, but that shouldn't be needed anymore

        # Calculate the elliptical weighted average value for each cell (float -> not-float needs rounding)
        # The fill value for the weight and accumulation arrays is static at NaN
        if grid_dtype is numpy.float32_t or grid_dtype is numpy.float64_t:
            if this_weightp < weight_sum_min or isnan(chanf):
                chanf = <accum_type>NAN
            elif maximum_weight_mode:
                # keep the current value
                chanf = chanf
            elif chanf >= 0.0:
                chanf = chanf / this_weightp
            else:
                chanf = chanf / this_weightp
        else:
            if this_weightp < weight_sum_min:
                chanf = <accum_type>NAN
            elif maximum_weight_mode:
                # keep the current value
                chanf = chanf
            elif chanf >= 0.0:
                chanf = chanf / this_weightp + 0.5
            else:
                chanf = chanf / this_weightp - 0.5

        if grid_dtype is numpy.uint8_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            elif chanf < 0.0:
                output_image[col] = 0
            elif chanf > 255.0:
                output_image[col] = 255
            else:
                output_image[col] = <grid_dtype>chanf
        elif grid_dtype is numpy.uint16_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            elif chanf < 0.0:
                output_image[col] = 0
            elif chanf > 65535.0:
                output_image[col] = 65535
            else:
                output_image[col] = <grid_dtype>chanf
        elif grid_dtype is numpy.int16_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            elif chanf < -32768.0:
                output_image[col] = -32768
            elif chanf > 32767.0:
                output_image[col] = 32767
            else:
                output_image[col] = <grid_dtype>chanf
        elif grid_dtype is numpy.uint32_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            elif chanf < 0.0:
                output_image[col] = 0
            elif chanf > 4294967295.0:
                output_image[col] = 4294967295
            else:
                output_image[col] = <grid_dtype>chanf
        elif grid_dtype is numpy.int32_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            elif chanf < -2147483648.0:
                output_image[col] = -2147483648
            elif chanf > 2147483647.0:
                output_image[col] = 2147483647
            else:
                output_image[col] = <grid_dtype>chanf
        elif grid_dtype is numpy.float32_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            else:
                output_image[col] = <grid_dtype>chanf
        elif grid_dtype is numpy.float64_t:
            if isnan(chanf):
                fill_count += 1
                output_image[col] = fill
            else:
                output_image[col] = <grid_dtype>chanf
        else:
            # We don't know how to handle this type yet
            return -1

    return fill_count

cdef accum_type **initialize_grid_accums(size_t chan_count, size_t grid_cols, size_t grid_rows):
    cdef accum_type **grid_accums = <accum_type **>malloc(chan_count * sizeof(accum_type *))
    cdef unsigned int i

    if not grid_accums:
        return NULL
    for i in range(chan_count):
        grid_accums[i] = <accum_type *>calloc(grid_cols * grid_rows, sizeof(accum_type))
        if not grid_accums[i]:
            return NULL

    return grid_accums

cdef weight_type **initialize_grid_weights(size_t chan_count, size_t grid_cols, size_t grid_rows):
    cdef weight_type **grid_weights = <weight_type **>malloc(chan_count * sizeof(weight_type *))
    cdef unsigned int i

    if not grid_weights:
        return NULL
    for i in range(chan_count):
        grid_weights[i] = <weight_type *>calloc(grid_cols * grid_rows, sizeof(weight_type))
        if not grid_weights[i]:
            return NULL

    return grid_weights

cdef void deinitialize_grids(size_t chan_count, void **grids):
    cdef unsigned int i
    for i in range(chan_count):
        if grids[i]:
            free(grids[i])
    free(grids)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int fornav(size_t chan_count, size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows,
            cr_dtype *cols_pointer, cr_dtype *rows_pointer,
           image_dtype **input_arrays, grid_dtype **output_arrays,
           image_dtype input_fill, grid_dtype output_fill, size_t rows_per_scan,
           unsigned int weight_count, weight_type weight_min, weight_type weight_distance_max, weight_type weight_delta_max,
           weight_type weight_sum_min, bint maximum_weight_mode) except -1:
    cdef unsigned int row_idx
    cdef unsigned int idx
    cdef bint got_point = 0
    cdef bint tmp_got_point
    cdef int func_result
    cdef int fill_count = 0
    cdef int tmp_fill_count
    cdef cr_dtype *tmp_cols_pointer
    cdef cr_dtype *tmp_rows_pointer
    cdef image_dtype **input_images
    cdef ewa_weight ewaw
    cdef ewa_parameters *ewap

    # other defaults
    if weight_sum_min == -1.0:
        weight_sum_min = weight_min

    func_result = initialize_weight(chan_count, weight_count, weight_min, weight_distance_max, weight_delta_max,
                      weight_sum_min, &ewaw)
    if func_result < 0:
        raise RuntimeError("Could not initialize weight structure for EWA resampling")

    # Allocate location for storing the sum of all of the pixels involved in each grid cell
    # XXX: Do these need to be initialized to a fill value?
    cdef accum_type **grid_accums = initialize_grid_accums(chan_count, grid_cols, grid_rows)
    if grid_accums is NULL:
        raise MemoryError()
    cdef weight_type **grid_weights = initialize_grid_weights(chan_count, grid_cols, grid_rows)
    if grid_weights is NULL:
        raise MemoryError()
    # Allocate memory for the parameters specific to each column
    ewap = <ewa_parameters *>malloc(swath_cols * sizeof(ewa_parameters))
    if ewap is NULL:
        raise MemoryError()
    # Allocate pointers to the correct portion of the data arrays that we will use
    input_images = <image_dtype **>malloc(chan_count * sizeof(image_dtype *))
    if input_images is NULL:
        raise MemoryError()


    # NOTE: Have to use old school pyrex for loop because cython only supports compile-time known steps
    for row_idx from 0 <= row_idx < swath_rows by rows_per_scan:
        tmp_cols_pointer = &cols_pointer[row_idx * swath_cols]
        tmp_rows_pointer = &rows_pointer[row_idx * swath_cols]
        # print "Current cols pointer: %d" % (<int>tmp_cols_pointer,)

        # Assign the python/numpy array objects to a pointer location for the rest of the functions
        for idx in range(chan_count):
            input_images[idx] = &input_arrays[idx][row_idx * swath_cols]
        # print "Current input 0 pointer: %d" % (<int>input_images[idx],)

        # Calculate EWA parameters for each column index
        func_result = compute_ewa_parameters(swath_cols, rows_per_scan, tmp_cols_pointer, tmp_rows_pointer, &ewaw, ewap)
        if func_result < 0:
            got_point = got_point or 0
            # raise RuntimeError("Could compute EWA parameters for EWA resampling")
            continue

        # NOTE: In the C version this is where the image array data is loaded
        tmp_got_point = compute_ewa(chan_count, maximum_weight_mode,
                    swath_cols, rows_per_scan, grid_cols, grid_rows,
                    tmp_cols_pointer, tmp_rows_pointer,
                    input_images, input_fill, grid_accums, grid_weights, &ewaw, ewap)

        got_point = got_point or tmp_got_point

    free(input_images)
    free(ewap)

    if not got_point:
        raise RuntimeError("EWA Resampling: No swath pixels found inside grid to be resampled")

    for idx in range(chan_count):
        tmp_fill_count = write_grid_image(grid_cols, grid_rows, grid_accums[idx], grid_weights[idx], maximum_weight_mode,
                         weight_sum_min, output_arrays[idx], output_fill)
        if tmp_fill_count < 0:
            raise RuntimeError("Could not write result to output arrays")
        fill_count += tmp_fill_count

    # free(grid_accums)
    deinitialize_weight(&ewaw)
    deinitialize_grids(chan_count, <void **>grid_accums)
    deinitialize_grids(chan_count, <void **>grid_weights)
    return fill_count

@cython.boundscheck(False)
@cython.wraparound(False)
def fornav_wrapper(numpy.ndarray[cr_dtype, ndim=2, mode='c'] cols_array,
           numpy.ndarray[cr_dtype, ndim=2, mode='c'] rows_array,
           tuple input_arrays, tuple output_arrays, input_fill, output_fill,
           size_t rows_per_scan,
           unsigned int weight_count=10000, weight_type weight_min=0.01, weight_type weight_distance_max=1.0, weight_type weight_delta_max=10.0, weight_type weight_sum_min=-1.0,
           cpython.bool maximum_weight_mode=False):
    cdef size_t num_items = len(input_arrays)
    cdef size_t num_outputs = len(output_arrays)
    cdef size_t swath_cols = cols_array.shape[1]
    cdef size_t swath_rows = cols_array.shape[0]
    cdef size_t grid_cols = output_arrays[0].shape[1]
    cdef size_t grid_rows = output_arrays[0].shape[0]
    cdef unsigned int i
    if num_items != num_outputs:
        raise ValueError("Must have same number of inputs and outputs")
    if num_items <= 0:
        raise ValueError("No input arrays given")

    cdef numpy.dtype in_type = input_arrays[0].dtype
    cdef numpy.dtype out_type = output_arrays[0].dtype
    if in_type != out_type:
        raise ValueError("Input and Output must be of the same type")
    if not all(input_array.dtype == in_type for input_array in input_arrays):
        raise ValueError("Input arrays must all be of the same data type")
    if not all(output_array.dtype == out_type for output_array in output_arrays):
        raise ValueError("Input arrays must all be of the same data type")

    cdef void **input_pointer = <void **>malloc(num_items * sizeof(void *))
    if not input_pointer:
        raise MemoryError()
    cdef void **output_pointer = <void **>malloc(num_items * sizeof(void *))
    if not output_pointer:
        raise MemoryError()
    cdef numpy.ndarray[numpy.float32_t, ndim=2] tmp_arr_f32
    cdef numpy.ndarray[numpy.float64_t, ndim=2] tmp_arr_f64
    cdef numpy.ndarray[numpy.int8_t, ndim=2] tmp_arr_i8
    cdef cr_dtype *cols_pointer = &cols_array[0, 0]
    cdef cr_dtype *rows_pointer = &rows_array[0, 0]
    cdef int ret = 0

    if in_type == numpy.float32:
        for i in range(num_items):
            tmp_arr_f32 = input_arrays[i]
            input_pointer[i] = &tmp_arr_f32[0, 0]
            tmp_arr_f32 = output_arrays[i]
            output_pointer[i] = &tmp_arr_f32[0, 0]
        ret = fornav(num_items, swath_cols, swath_rows, grid_cols, grid_rows, cols_pointer, rows_pointer,
                     <numpy.float32_t **>input_pointer, <numpy.float32_t **>output_pointer,
                     <numpy.float32_t>input_fill, <numpy.float32_t>output_fill, rows_per_scan,
                     weight_count, weight_min, weight_distance_max, weight_delta_max, weight_sum_min,
                     <bint>maximum_weight_mode)
    elif in_type == numpy.float64:
        for i in range(num_items):
            tmp_arr_f64 = input_arrays[i]
            input_pointer[i] = &tmp_arr_f64[0, 0]
            tmp_arr_f64 = output_arrays[i]
            output_pointer[i] = &tmp_arr_f64[0, 0]
        ret = fornav(num_items, swath_cols, swath_rows, grid_cols, grid_rows, cols_pointer, rows_pointer,
                     <numpy.float64_t **>input_pointer, <numpy.float64_t **>output_pointer,
                     <numpy.float64_t>input_fill, <numpy.float64_t>output_fill, rows_per_scan,
                     weight_count, weight_min, weight_distance_max, weight_delta_max, weight_sum_min,
                     <bint>maximum_weight_mode)
    elif in_type == numpy.int8:
        for i in range(num_items):
            tmp_arr_i8 = input_arrays[i]
            input_pointer[i] = &tmp_arr_i8[0, 0]
            tmp_arr_i8 = output_arrays[i]
            output_pointer[i] = &tmp_arr_i8[0, 0]
        ret = fornav(num_items, swath_cols, swath_rows, grid_cols, grid_rows, cols_pointer, rows_pointer,
                     <numpy.int8_t **>input_pointer, <numpy.int8_t **>output_pointer,
                     <numpy.int8_t>input_fill, <numpy.int8_t>output_fill, rows_per_scan,
                     weight_count, weight_min, weight_distance_max, weight_delta_max, weight_sum_min,
                     <bint>maximum_weight_mode)
    else:
        raise ValueError("Unknown input and output data type")

    free(input_pointer)
    free(output_pointer)

    return ret
