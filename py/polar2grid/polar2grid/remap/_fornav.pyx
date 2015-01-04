# copyright (c) 2014 space science and engineering center (ssec),
# university of wisconsin-madison.
#
#     this program is free software: you can redistribute it and/or modify
#     it under the terms of the gnu general public license as published by
#     the free software foundation, either version 3 of the license, or
#     (at your option) any later version.
#
#     this program is distributed in the hope that it will be useful,
#     but without any warranty; without even the implied warranty of
#     merchantability or fitness for a particular purpose.  see the
#     gnu general public license for more details.
#
#     you should have received a copy of the gnu general public license
#     along with this program.  if not, see <http://www.gnu.org/licenses/>.
#
# this file is part of the polar2grid software package. polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     written by david hoese    december 2014
#     university of wisconsin-madison
#     space science and engineering center
#     1225 west dayton street
#     madison, wi  53706
#     david.hoese@ssec.wisc.edu

import sys
import cython
cimport cython
import numpy
cimport numpy
cimport cpython
from libc.stdlib cimport calloc, malloc, free
# from libc.stdio cimport fprintf, printf
from libc.math cimport log, exp, sqrt, isnan, NAN

# cdef float EPSILON = 1e-8
cdef double EPSILON = 1e-8
cdef double double_nan = <double>NAN

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

cdef struct ewa_parameters:
    double a
    double b
    double c
    double f
    double u_del
    double v_del

cdef struct ewa_weight:
    int count
    double min
    double distance_max
    double delta_max
    double sum_min
    double alpha
    double qmax
    double qfactor
    double *wtab

@cython.cdivision(True)
cdef int initialize_weight(size_t chan_count, unsigned int weight_count, double weight_min, double weight_distance_max,
                            double weight_delta_max, double weight_sum_min, ewa_weight *ewaw):
    cdef unsigned int idx
    cdef double *wptr

    ewaw.wtab = <double *>calloc(weight_count, sizeof(double))
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
    cdef double ux
    cdef double uy
    cdef double vx
    cdef double vy
    cdef double f_scale
    cdef double d
    cdef double qmax = ewaw.qmax
    cdef double distance_max = ewaw.distance_max
    cdef double delta_max = ewaw.delta_max
    cdef double u_del
    cdef double v_del

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
cdef int compute_ewa(size_t chan_count, bint maximum_weight_mode,
                      size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows,
                      cr_dtype *uimg, cr_dtype *vimg, cr_dtype cr_fill,
                      image_dtype **images, image_dtype img_fill,
                      double **grid_accums, double **grid_weights, ewa_weight *ewaw, ewa_parameters *ewap):
    cdef bint got_point = 0
    cdef unsigned int row
    cdef unsigned int col
    cdef ewa_parameters this_ewap
    cdef cr_dtype u0
    cdef cr_dtype v0
    cdef int iu1
    cdef int iu2
    cdef int iv1
    cdef int iv2
    cdef int iu
    cdef int iv
    cdef double ddq
    cdef double dq
    cdef double u
    cdef double v
    cdef double a2up1
    cdef double au2
    cdef double bu
    cdef int iw
    cdef double weight
    cdef image_dtype this_val
    cdef unsigned int swath_offset
    cdef unsigned int grid_offset
    for row in range(swath_rows):
        for col in range(swath_cols):
            this_ewap = ewap[col]
            swath_offset = row * swath_cols + col
            u0 = uimg[swath_offset]
            v0 = vimg[swath_offset]
            # XXX: I don't like this part of the algorithm, why are we completely ignoring pixels out of the grid (shouldn't they affect the output?)
            if u0 < 0 or v0 < 0:
                continue
            iu1 = <int>(u0 - this_ewap.u_del)
            iu2 = <int>(u0 + this_ewap.u_del)
            iv1 = <int>(v0 - this_ewap.v_del)
            iv2 = <int>(v0 + this_ewap.v_del)

            if iu1 < 0:
                iu1 = 0
            if iu2 >= grid_cols:
                iu2 = grid_cols - 1
            if iv1 < 0:
                iv1 = 0
            if iv2 >= grid_rows:
                iv2 = grid_rows - 1
            if iu1 < grid_cols and iu2 >= 0 and iv1 < grid_rows and iv2 >= 0:
                # Do the main work
                got_point = 1
                ddq = 2.0 * this_ewap.a
                u = iu1 - u0
                a2up1 = this_ewap.a * (2.0 * u + 1.0)
                bu = this_ewap.b * u
                au2 = this_ewap.a * u * u
                for iv from iv1 <= iv <= iv2:
                    v = iv - v0
                    dq = a2up1 + this_ewap.b * v
                    q = (this_ewap.c * v + bu) * v + au2
                    for iu from iu1 <= iu <= iu2:
                        if 0 <= q < this_ewap.f:
                            iw = <int>(q * ewaw.qfactor)
                            if iw >= ewaw.count:
                                iw = ewaw.count - 1
                            weight = ewaw.wtab[iw]
                            grid_offset = iv * grid_cols + iu
                            for chan in range(chan_count):
                                this_val = images[chan][swath_offset]
                                if maximum_weight_mode:
                                    if weight > grid_weights[chan][grid_offset]:
                                        grid_weights[chan][grid_offset] = weight
                                        if image_dtype is numpy.float32_t or image_dtype is numpy.float64_t:
                                            if this_val == img_fill or isnan(this_val):
                                                grid_accums[chan][grid_offset] = double_nan
                                            else:
                                                grid_accums[chan][grid_offset] = this_val
                                        else:
                                            if this_val == img_fill:
                                                grid_accums[chan][grid_offset] = double_nan
                                            else:
                                                grid_accums[chan][grid_offset] = this_val
                                else:
                                    if image_dtype is numpy.float32_t or image_dtype is numpy.float64_t:
                                        if this_val != img_fill and not isnan(this_val):
                                            grid_weights[chan][grid_offset] += weight
                                            grid_accums[chan][grid_offset] += this_val * weight
                                    else:
                                        if this_val != img_fill:
                                            grid_weights[chan][grid_offset] += weight
                                            grid_accums[chan][grid_offset] += this_val * weight
                        q += dq
                        dq += ddq

    return got_point

@cython.cdivision(True)
cdef int write_grid_image(size_t grid_cols, size_t grid_rows,
                          double *grid_accum, double *grid_weights, bint maximum_weight_mode, double weight_sum_min,
                          grid_dtype *output_image, grid_dtype fill):
    cdef double this_weightp;
    cdef double chanf
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
                chanf = double_nan
            elif maximum_weight_mode:
                # keep the current value
                chanf = chanf
            elif chanf >= 0.0:
                chanf = chanf / this_weightp
            else:
                chanf = chanf / this_weightp
        else:
            if this_weightp < weight_sum_min:
                chanf = double_nan
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

cdef double **initialize_grid_accums(size_t chan_count, size_t grid_cols, size_t grid_rows):
    cdef double **grid_accums = <double **>malloc(chan_count * sizeof(double *))
    cdef unsigned int i

    if not grid_accums:
        return NULL
    for i in range(chan_count):
        grid_accums[i] = <double *>calloc(grid_cols * grid_rows, sizeof(double))
        if not grid_accums[i]:
            return NULL

    return grid_accums

cdef double **initialize_grid_weights(size_t chan_count, size_t grid_cols, size_t grid_rows):
    cdef double **grid_weights = <double **>malloc(chan_count * sizeof(double *))
    cdef unsigned int i

    if not grid_weights:
        return NULL
    for i in range(chan_count):
        grid_weights[i] = <double *>calloc(grid_cols * grid_rows, sizeof(double))
        if not grid_weights[i]:
            return NULL

    return grid_weights

cdef void deinitialize_grids(size_t chan_count, double **grids):
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
            cr_dtype cr_fill, image_dtype input_fill, grid_dtype output_fill, size_t rows_per_scan,
           unsigned int weight_count, double weight_min, double weight_distance_max, double weight_delta_max,
           double weight_sum_min, bint maximum_weight_mode) except -1:
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
    cdef double **grid_accums = initialize_grid_accums(chan_count, grid_cols, grid_rows)
    if grid_accums is NULL:
        raise MemoryError()
    cdef double **grid_weights = initialize_grid_weights(chan_count, grid_cols, grid_rows)
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
                    tmp_cols_pointer, tmp_rows_pointer, cr_fill,
                    input_images, input_fill, grid_accums, grid_weights, &ewaw, ewap)
        # test_data_types(chan_count, <bint>maximum_weight_mode,
        #                 swath_cols, swath_rows, grid_cols, grid_rows,
        #                 col_pointer, row_pointer, cr_fill, input_images, input_fill, grid_accums, ewap)

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
    deinitialize_grids(chan_count, grid_accums)
    deinitialize_grids(chan_count, grid_weights)
    return fill_count

@cython.boundscheck(False)
@cython.wraparound(False)
def fornav_wrapper(numpy.ndarray[cr_dtype, ndim=2, mode='c'] cols_array,
           numpy.ndarray[cr_dtype, ndim=2, mode='c'] rows_array,
           tuple input_arrays, tuple output_arrays, cr_dtype cr_fill, input_fill, output_fill,
           size_t rows_per_scan,
           unsigned int weight_count=10000, double weight_min=0.01, double weight_distance_max=1.0, double weight_delta_max=10.0, double weight_sum_min=-1.0,
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

    # for i in range(num_items):
    #     tmp_arr_f32 = input_arrays[i]
    #     input_pointer[i] = &tmp_arr_f32[0, 0]
    #     tmp_arr_f32 = output_arrays[i]
    #     output_pointer[i] = &tmp_arr_f32[0, 0]
    # ret = fornav(num_items, swath_cols, swath_rows, grid_cols, grid_rows, cols_pointer, rows_pointer,
    #              <numpy.float32_t **>input_pointer, <numpy.float32_t **>output_pointer,
    #              cr_fill, <numpy.float32_t>input_fill, <numpy.float32_t>output_fill, rows_per_scan,
    #              weight_count, weight_min, weight_distance_max, weight_delta_max, weight_sum_min,
    #              <bint>maximum_weight_mode)

    if in_type == numpy.float32:
        for i in range(num_items):
            tmp_arr_f32 = input_arrays[i]
            input_pointer[i] = &tmp_arr_f32[0, 0]
            tmp_arr_f32 = output_arrays[i]
            output_pointer[i] = &tmp_arr_f32[0, 0]
        ret = fornav(num_items, swath_cols, swath_rows, grid_cols, grid_rows, cols_pointer, rows_pointer,
                     <numpy.float32_t **>input_pointer, <numpy.float32_t **>output_pointer,
                     cr_fill, <numpy.float32_t>input_fill, <numpy.float32_t>output_fill, rows_per_scan,
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
                     cr_fill, <numpy.float64_t>input_fill, <numpy.float64_t>output_fill, rows_per_scan,
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
                     cr_fill, <numpy.int8_t>input_fill, <numpy.int8_t>output_fill, rows_per_scan,
                     weight_count, weight_min, weight_distance_max, weight_delta_max, weight_sum_min,
                     <bint>maximum_weight_mode)
    else:
        raise ValueError("Unknown input and output data type")

    free(input_pointer)
    free(output_pointer)

    return ret

# cdef test_data_types2(cr_dtype **cols_arrays):
#     if cr_dtype is numpy.float32_t:
#         print "We have a 32 bit float"
#     elif cr_dtype is numpy.float64_t:
#         print "We have a 64 bit float"
#     else:
#         print "We don't know what the data type is"


# def test_data_types2_wrapper2(cr_dtype one_val):
#     if cr_dtype is numpy.float32_t:
#         print "We have a 32 bit float"
#     elif cr_dtype is numpy.float64_t:
#         print "We have a 64 bit float"
#     else:
#         print "We don't know what the data type is"

# def test_data_types2_wrapper3(numpy.ndarray[cr_dtype, ndim=2] one_array):
#     if cr_dtype is numpy.float32_t:
#         print "We have a 32 bit float"
#     elif cr_dtype is numpy.float64_t:
#         print "We have a 64 bit float"
#     else:
#         print "We don't know what the data type is"

# cdef int test_range(size_t end1, int end2, unsigned int end3):
#     cdef unsigned int i
#     cdef size_t step1 = 2
#     cdef int step2 = 3
#     cdef unsigned int step3 = 4
#     for i in range(0, end1, -2):
#         pass
#     for i in range(0, 10, step2):
#         pass
#     for i in range(0, end3, step3):
#         pass
#     for i from 0 <= i < end3 by step3:
#         pass
#     return 0

# cdef bint test_data_types(size_t chan_count, bint maximum_weight_mode,
#                           size_t swath_cols, size_t swath_rows, size_t grid_cols, size_t grid_rows,
#                           cr_dtype *uimg, cr_dtype *vimg, cr_dtype cr_fill,
#                           image_dtype **images, image_dtype img_fill,
#                           double **grid_accums, ewa_parameters *ewap):
#     return 0

