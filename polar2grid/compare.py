#!/usr/bin/env python3
# encoding: utf-8
# Copyright (C) 2014-2021 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
"""Script for comparing writer output."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from glob import glob
from typing import Optional

import numpy as np
import xarray as xr

LOG = logging.getLogger(__name__)


@dataclass
class ArrayComparisonResult:
    almost_equal: bool
    num_diff_pixels: int
    total_pixels: int
    different_shape: bool

    @property
    def failed(self):
        return self.different_shape or not self.almost_equal

    @property
    def diff_percentage(self):
        if not self.total_pixels or self.different_shape:
            return 100.0
        return self.num_diff_pixels / self.total_pixels * 100


@dataclass
class FlatArrayComparisonResult(ArrayComparisonResult):
    # add additional information for formats that don't contain it
    shape1: tuple
    shape2: tuple
    dtype1: np.dtype
    dtype2: np.dtype


@dataclass
class VariableComparisonResult(ArrayComparisonResult):
    variable: str
    variable_missing: bool

    @property
    def failed(self):
        return super().failed or self.variable_missing


@dataclass
class FileComparisonResults:
    file1: str
    file2: str
    files_missing: bool
    unknown_file_type: bool
    sub_results: list[ArrayComparisonResult] = field(default_factory=list)

    @property
    def any_failed(self) -> bool:
        if self.files_missing or self.unknown_file_type:
            return True
        for sub_result in self.sub_results:
            if sub_result.failed:
                return True
        return False


def isclose_array(array1, array2, atol=0.0, rtol=0.0, margin_of_error=0.0, **kwargs) -> ArrayComparisonResult:
    """Compare 2 binary arrays per pixel.

    Two pixels are considered different if the absolute value of their
    difference is greater than 1. This function assumes the arrays are
    in useful data types, which may cause erroneous results. For example,
    if both arrays are unsigned integers and the different results in a
    negative value overflow will occur and the threshold will likely not
    be met.

    Args:
        array1: numpy array for comparison
        array2: numpy array for comparison

    Returns:
        1 if more than margin_of_error pixels are different, 0 otherwise.

    """
    if array1.shape != array2.shape:
        LOG.error("Data shapes were not equal: %r | %r", array1.shape, array2.shape)
        return ArrayComparisonResult(False, 0, 0, True)

    total_pixels = array1.size
    equal_pixels = np.count_nonzero(np.isclose(array1, array2, rtol=rtol, atol=atol, equal_nan=True))
    diff_pixels = total_pixels - equal_pixels
    if diff_pixels > margin_of_error / 100 * total_pixels:
        LOG.warning("%d pixels out of %d pixels are different" % (diff_pixels, total_pixels))
        return ArrayComparisonResult(False, diff_pixels, total_pixels, False)
    LOG.info("%d pixels out of %d pixels are different" % (diff_pixels, total_pixels))
    return ArrayComparisonResult(True, diff_pixels, total_pixels, False)


def plot_array(array1, array2, cmap="viridis", vmin=None, vmax=None, **kwargs):
    """Debug two arrays being different by visually comparing them."""
    import matplotlib.pyplot as plt

    LOG.info("Plotting arrays...")
    vmin = vmin if vmin else -10
    vmax = vmax if vmax else 10

    fig, (ax1, ax2) = plt.subplots(2, 2)
    array3 = array1 - array2
    q = [0, 0.25, 0.5, 0.75, 1.0]
    array3_quantiles = np.nanquantile(array3, q)
    subtitle = np.array2string(array3_quantiles, precision=8, separator=",", suppress_small=True)
    fig.suptitle(subtitle)
    img1 = ax1[0].imshow(array1, cmap=cmap, vmin=vmin, vmax=vmax)
    fig.colorbar(img1, ax=ax1[0])
    img2 = ax1[1].imshow(array2, cmap=cmap, vmin=vmin, vmax=vmax)
    fig.colorbar(img2, ax=ax1[1])

    ax2[0].set_title("Difference")
    array3[array3 == 0.0] = np.nan
    img4 = ax2[0].imshow(array3, cmap="RdBu", vmin=vmin, vmax=vmax)
    fig.colorbar(img4, ax=ax2[0])

    n_bins = 100
    nan_array3 = array3[~np.isnan(array3)]
    ax2[1].hist(nan_array3, density=True, bins=n_bins)

    plt.tight_layout()
    plt.show()


def compare_array(array1, array2, plot=False, **kwargs) -> ArrayComparisonResult:
    if plot:
        plot_array(array1, array2, **kwargs)
    return isclose_array(array1, array2, **kwargs)


def compare_binary(fn1, fn2, shape, dtype, atol=0.0, margin_of_error=0.0, **kwargs) -> list[ArrayComparisonResult]:
    if dtype is None:
        dtype = np.float32
    mmap_kwargs = {"dtype": dtype, "mode": "r"}
    if shape is not None and shape[0] is not None:
        mmap_kwargs["shape"] = shape
    array1 = np.memmap(fn1, **mmap_kwargs)
    array2 = np.memmap(fn2, **mmap_kwargs)

    array_comparison = compare_array(array1, array2, atol=atol, margin_of_error=margin_of_error, **kwargs)
    flat_array_comparison = FlatArrayComparisonResult(
        **array_comparison.__dict__, shape1=array1.shape, shape2=array2.shape, dtype1=array1.dtype, dtype2=array2.dtype
    )
    return [flat_array_comparison]


def compare_geotiff(gtiff_fn1, gtiff_fn2, atol=0.0, margin_of_error=0.0, **kwargs) -> list[ArrayComparisonResult]:
    """Compare 2 single banded geotiff files.

    .. note::

        The binary arrays will be converted to 32-bit floats before
        comparison.

    """
    array1 = _get_geotiff_array(gtiff_fn1, dtype=np.float32)
    array2 = _get_geotiff_array(gtiff_fn2, dtype=np.float32)
    arr_compare = compare_array(array1, array2, atol=atol, margin_of_error=margin_of_error, **kwargs)
    if arr_compare.failed:
        return [arr_compare]

    # array data are equal, but
    cmap1 = _get_geotiff_colormap(gtiff_fn1)
    cmap2 = _get_geotiff_colormap(gtiff_fn2)
    cmap_result = _compare_gtiff_colormaps(cmap1, cmap2, atol=atol, **kwargs)
    # only return colormap results if there was actually a colormap
    if cmap_result.total_pixels:
        return [arr_compare, cmap_result]
    return [arr_compare]


def _get_geotiff_array(gtiff_fn, dtype=None):
    import rasterio

    band_arrays = []
    with rasterio.open(gtiff_fn, "r") as gtiff_file:
        for band_idx in range(gtiff_file.count):
            arr = gtiff_file.read(band_idx + 1)
            if dtype is not None:
                arr = arr.astype(dtype)
            band_arrays.append(arr)
    return np.concatenate(band_arrays)


def _get_geotiff_colormap(gtiff_fn, band_idx=1):
    import rasterio

    with rasterio.open(gtiff_fn, "r") as gtiff_file:
        try:
            return gtiff_file.colormap(band_idx)
        except ValueError:
            return None


def _compare_gtiff_colormaps(cmap1: dict, cmap2: dict, **kwargs) -> VariableComparisonResult:
    if cmap1 is None and cmap2 is None:
        return VariableComparisonResult(True, 0, 0, False, "colormap", True)
    len1 = len(cmap1) if cmap1 is not None else 0
    len2 = len(cmap2) if cmap2 is not None else 0
    if len1 != len2:
        return VariableComparisonResult(False, abs(len2 - len1), max(len1, len2), True, "colormap", False)
    arr1 = np.array([[control_point] + list(color) for control_point, color in cmap1.items()])
    arr2 = np.array([[control_point] + list(color) for control_point, color in cmap2.items()])
    array_result = compare_array(arr1, arr2, **kwargs)
    return VariableComparisonResult(**array_result.__dict__, variable="colormap", variable_missing=False)


def compare_netcdf(
    nc1_name, nc2_name, variables, atol=0.0, margin_of_error=0.0, **kwargs
) -> list[VariableComparisonResult]:
    nc1 = xr.open_dataset(nc1_name)
    nc2 = xr.open_dataset(nc2_name)

    if variables is None:
        # TODO: Handle groups
        variables = list(nc1.variables.keys())
    results = []
    for v in variables:
        image1_var = nc1[v].data
        image2_var = nc2[v].data
        LOG.debug("Comparing data for variable '{}'".format(v))
        array_result = compare_array(image1_var, image2_var, atol=atol, margin_of_error=margin_of_error, **kwargs)
        var_result = VariableComparisonResult(**array_result.__dict__, variable=v, variable_missing=False)
        results.append(var_result)
    return results


def _get_hdf5_variables(variables, name, obj):
    import h5py

    if isinstance(obj, h5py.Group):
        return
    variables.append(name)


def compare_hdf5(h1_name, h2_name, variables, atol=0.0, margin_of_error=0.0, **kwargs) -> list[ArrayComparisonResult]:
    import h5py

    h1 = h5py.File(h1_name, "r")
    h2 = h5py.File(h2_name, "r")
    if variables is None:
        from functools import partial

        variables = []
        cb = partial(_get_hdf5_variables, variables)
        h1.visititems(cb)

    results = []
    for v in variables:
        LOG.debug("Comparing data for variable '{}'".format(v))
        image1_var = h1[v]
        if v not in h2:
            total_pixels = image1_var.size
            var_result = VariableComparisonResult(False, total_pixels, total_pixels, True, v, True)
        else:
            image2_var = h2[v]
            array_result = compare_array(
                image1_var[:], image2_var[:], atol=atol, margin_of_error=margin_of_error, **kwargs
            )
            var_result = VariableComparisonResult(**array_result.__dict__, variable=v, variable_missing=False)
        results.append(var_result)
    return results


def compare_image(im1_name, im2_name, atol=0.0, margin_of_error=0.0, **kwargs) -> list[ArrayComparisonResult]:
    img1 = _get_image_array(im1_name)
    img2 = _get_image_array(im2_name)
    return [compare_array(img1, img2, atol=atol, margin_of_error=margin_of_error, **kwargs)]


def _get_image_array(
    img_filename: str, variable: str = None, shape: Optional[tuple] = None, dtype: Optional[np.dtype] = None
) -> Optional[np.ndarray]:
    from PIL import Image

    if variable is not None:
        # NotImplementedError (geotiff colormap)
        return None

    # we may be dealing with large images that look like decompression bombs
    # let's turn off the check for the image size in PIL/Pillow
    Image.MAX_IMAGE_PIXELS = None

    img = Image.open(img_filename)
    if "P" in img.mode:
        img = img.convert("RGB" if img.mode == "P" else "RGBA")
    return np.array(img)


def _get_netcdf_array(
    input_filename: str, variable: str, shape: Optional[tuple], dtype: Optional[np.dtype]
) -> Optional[np.ndarray]:
    import xarray as xr

    ds = xr.open_dataset(input_filename)
    if variable not in ds:
        return None
    arr = ds[variable].data
    if not arr.shape:
        return None
    arr = _tranpose_for_thumbnail_if_multiband_array(arr)
    return arr


def _get_hdf5_array(
    input_filename: str, variable: str, shape: Optional[tuple], dtype: Optional[np.dtype]
) -> Optional[np.ndarray]:
    import h5py

    h = h5py.File(input_filename, "r")
    if variable is None or variable not in h:
        return None
    arr = np.array(h[variable][:])
    arr = _tranpose_for_thumbnail_if_multiband_array(arr)
    return arr


def _tranpose_for_thumbnail_if_multiband_array(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 3 and arr.shape[0] in (3, 4):
        # assume RGB/RGBA with band dimension first
        # need to transpose for PIL image RGB
        arr = arr.transpose((1, 2, 0))
    return arr


def _get_binary_array(
    input_filename: str,
    variable: str,
    shape: Optional[tuple],
    dtype: np.dtype,
) -> Optional[np.ndarray]:
    if variable is not None:
        return None
    mmap_kwargs = {"dtype": dtype, "mode": "r"}
    if shape is not None and shape[0] is not None:
        mmap_kwargs["shape"] = shape
    array1 = np.memmap(input_filename, **mmap_kwargs)
    return array1


type_name_to_compare_func = {
    "binary": compare_binary,
    "gtiff": compare_geotiff,
    "geotiff": compare_geotiff,
    "netcdf": compare_netcdf,
    "hdf5": compare_hdf5,
    "png": compare_image,
}

file_ext_to_compare_func = {
    ".dat": compare_binary,
    ".tif": compare_geotiff,
    ".tiff": compare_geotiff,
    ".nc": compare_netcdf,
    ".h5": compare_hdf5,
    ".png": compare_image,
    ".jpg": compare_image,
    ".jpeg": compare_image,
}

file_ext_to_array_func = {
    ".dat": _get_binary_array,
    ".nc": _get_netcdf_array,
    ".h5": _get_hdf5_array,
    ".tif": _get_image_array,
    ".png": _get_image_array,
    ".jpg": _get_image_array,
    ".jpeg": _get_image_array,
}


def _file_type(str_val):
    str_val = str_val.lower()
    if str_val in type_name_to_compare_func:
        return type_name_to_compare_func[str_val]

    print("ERROR: Unknown file type '%s'" % (str_val,))
    print("Possible file types: \n\t%s" % ("\n\t".join(type_name_to_compare_func.keys())))
    raise ValueError("Unknown file type '%s'" % (str_val,))


class CompareHelper:
    """Wrapper around various comparison operations."""

    def __init__(self, atol: float = 0.0, rtol: float = 0.0, margin_of_error: float = 0.0, create_plot: bool = False):
        self.atol = atol
        self.rtol = rtol
        self.margin_of_error = margin_of_error
        self.create_plot = create_plot

    def compare_files(self, file1, file2, file_type=None, **kwargs):
        if file_type is None:
            # guess based on file extension
            ext = os.path.splitext(file1)[-1]
            file_type = file_ext_to_compare_func.get(ext)
        if file_type is None:
            LOG.error(f"Could not determine how to compare file type (extension not recognized): {file1}.")
            return FileComparisonResults(file1, file2, False, True)
        LOG.info(f"Comparing {file2!r} to known valid file {file1!r}.")
        comparison_results = file_type(
            file1,
            file2,
            atol=self.atol,
            rtol=self.rtol,
            margin_of_error=self.margin_of_error,
            plot=self.create_plot,
            **kwargs,
        )
        return FileComparisonResults(file1, file2, False, False, comparison_results)

    def compare_dirs(self, dir1, dir2, **kwargs) -> list[FileComparisonResults]:
        results = []
        for expected_path in sorted(glob(os.path.join(dir1, "*"))):
            if expected_path.endswith(".log"):
                continue
            test_path = os.path.join(dir2, os.path.basename(expected_path))
            if not os.path.isfile(test_path):
                LOG.error(f"File from first directory is not present in second directory: {test_path}")
                results.append(FileComparisonResults(expected_path, test_path, True, False))
                continue

            file_comparison_results = self.compare(expected_path, test_path, **kwargs)
            results.extend(file_comparison_results)
        return results

    def compare(self, input1, input2, **kwargs) -> list[FileComparisonResults]:
        if os.path.isdir(input1) and os.path.isdir(input2):
            return self.compare_dirs(input1, input2, **kwargs)
        elif os.path.isfile(input1) and os.path.isfile(input2):
            return [self.compare_files(input1, input2, **kwargs)]
        elif not os.path.exists(input1):
            LOG.error("Could not find input directory or file {}".format(input1))
            return [FileComparisonResults(input1, input2, True, False)]
        elif not os.path.exists(input2):
            LOG.error("Could not find input directory or file {}".format(input2))
            return [FileComparisonResults(input1, input2, True, False)]
        else:
            LOG.error("Inputs are not both files or both directories.")
            return [FileComparisonResults(input1, input2, True, False)]


def num_failed_files(file_comparison_results: list[FileComparisonResults]) -> int:
    return sum(int(fc.any_failed) for fc in file_comparison_results)


HTML_TEMPLATE = """
<html lang="en">
<head>
<title>{title}</title>
</head>

<h1>{title}</h1>

<table>
<tr>
    <th>Filename</th>
    <th>Status</th>
    <th>Variable</th>
    <th>Expected</th>
    <th>Actual</th>
    <th>Diff. Pixels (%)</th>
    <th>Notes</th>
</tr>
{rows}
</table>

<body>
</body>
</html>
"""


def _generate_html_summary(output_filename, file_comparison_results):
    filename = os.path.basename(output_filename)
    row_html = "\n\t" + "\n\t".join(_generate_table_rows(output_filename, file_comparison_results))
    LOG.info(f"Creating HTML file {output_filename}")
    dst_dir = os.path.dirname(output_filename)
    if dst_dir:
        os.makedirs(dst_dir, exist_ok=True)
    with open(output_filename, "w") as html_file:
        html_text = HTML_TEMPLATE.format(
            title=filename,
            rows=row_html,
        )
        html_file.write(html_text)


def _generate_table_rows(
    output_filename: str,
    file_comparison_results: list[FileComparisonResults],
) -> list[str]:
    img_dst_dir = os.path.join(os.path.dirname(output_filename), "_images")
    os.makedirs(img_dst_dir, exist_ok=True)
    row_infos = []
    for fc in file_comparison_results:
        exp_filename = os.path.basename(fc.file1)
        if fc.files_missing or fc.unknown_file_type:
            row_info = ROW_TEMPLATE.format(
                filename=exp_filename,
                status="FAILED",
                variable="N/A",
                expected_img="N/A",
                actual_img="N/A",
                diff_percent=100.0,
                notes="Missing file" if fc.files_missing else "Unknown file type",
            )
            row_infos.append(row_info)
            continue

        for sub_result in fc.sub_results:
            row_info = _generate_subresult_table_row(img_dst_dir, fc, sub_result)
            row_infos.append(row_info)
    return row_infos


ROW_TEMPLATE = """
<tr>
    <td>{filename}</td>
    <td>{status}</td>
    <td>{variable}</td>
    <td>{expected_img}</td>
    <td>{actual_img}</td>
    <td>{diff_percent:0.02f}%</td>
    <td>{notes}</td>
</tr>
"""


def _generate_subresult_table_row(
    img_dst_dir: str,
    file_comparison_result: FileComparisonResults,
    sub_result: ArrayComparisonResult,
) -> str:
    status = "FAILED" if sub_result.failed else "PASSED"
    notes = ""
    diff_percent = sub_result.diff_percentage
    if sub_result.different_shape:
        notes = "Different array shapes"
    elif sub_result.failed:
        notes = "Too many differing pixels"

    variable = getattr(sub_result, "variable", None)
    exp_tn_html = _generate_thumbnail_html(
        file_comparison_result.file1,
        variable,
        img_dst_dir,
        "expected",
        getattr(sub_result, "shape1", None),
        getattr(sub_result, "dtype1", None),
    )
    act_tn_html = _generate_thumbnail_html(
        file_comparison_result.file2,
        variable,
        img_dst_dir,
        "actual",
        getattr(sub_result, "shape2", None),
        getattr(sub_result, "dtype2", None),
    )
    exp_filename = os.path.basename(file_comparison_result.file1)
    row_info = ROW_TEMPLATE.format(
        filename=exp_filename,
        status=status,
        variable=variable or "N/A",
        actual_img=act_tn_html,
        expected_img=exp_tn_html,
        diff_percent=diff_percent,
        notes=notes,
    )
    return row_info


def _generate_thumbnail_html(
    data_pathname: str,
    variable: Optional[str],
    img_dst_dir: str,
    tn_suffix: str,
    shape: Optional[tuple],
    dtype: Optional[np.dtype],
) -> str:
    data_arr = _get_thumbnail_array(data_pathname, variable, shape, dtype)
    if data_arr is None:
        return "N/A"
    data_filename = os.path.basename(data_pathname)
    file_ext = os.path.splitext(data_filename)[1]
    var_name = variable.replace("/", "-") if variable is not None else "None"
    exp_tn_fn = data_filename.replace(file_ext, f".{var_name}.{tn_suffix}.png")
    try:
        _generate_thumbnail(data_arr, os.path.join(img_dst_dir, exp_tn_fn), max_width=512)
    except (RuntimeError, ValueError):
        return "Failed to generate thumbnail"
    exp_tn_html = IMG_ENTRY_TMPL.format("_images/" + exp_tn_fn)
    return exp_tn_html


def _get_thumbnail_array(
    input_data_path: str, variable: Optional[str], shape: Optional[tuple], dtype: Optional[np.dtype]
) -> Optional[np.ndarray]:
    input_ext = os.path.splitext(input_data_path)[1]
    if input_ext not in file_ext_to_array_func:
        return None
    input_arr = file_ext_to_array_func[input_ext](input_data_path, variable, shape, dtype)
    return input_arr


IMG_ENTRY_TMPL = '<img src="{}"></img>'


def _generate_thumbnail(input_arr, output_thumbnail_path, max_width=512) -> bool:
    if input_arr.ndim == 1:
        return _generate_matplotlib_1d_thumbnail(input_arr, output_thumbnail_path, max_width)
    if input_arr.dtype == np.uint8:
        return _generate_pillow_thumbnail(input_arr, output_thumbnail_path, max_width)
    return _generate_matplotlib_thumbnail(input_arr, output_thumbnail_path, max_width)


def _generate_matplotlib_1d_thumbnail(input_arr, output_thumbnail_path, max_width) -> bool:
    import matplotlib.pyplot as plt

    figsize = _get_mpl_figsize(input_arr.shape, max_width)
    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(input_arr, bins=10)
    fig.savefig(output_thumbnail_path)
    plt.close(fig)
    return True


def _generate_matplotlib_thumbnail(input_arr, output_thumbnail_path, max_width=512) -> bool:
    import matplotlib.pyplot as plt

    figsize = _get_mpl_figsize(input_arr.shape, max_width)
    fig, ax = plt.subplots(figsize=figsize)
    img = ax.imshow(input_arr)
    fig.colorbar(img, ax=ax)
    fig.savefig(output_thumbnail_path)
    plt.close(fig)
    return True


def _get_mpl_figsize(input_shape, max_width) -> tuple[int, int]:
    # dpi 100 => 51
    fig_width = max_width / 100.0
    if len(input_shape) == 1:
        fig_height = fig_width
    else:
        fig_height = input_shape[0] * (fig_width / input_shape[1])
    return fig_width, fig_height


def _generate_pillow_thumbnail(input_arr, output_thumbnail_path, max_width=512) -> bool:
    from PIL import Image

    # we may be dealing with large images that look like decompression bombs
    # let's turn off the check for the image size in PIL/Pillow
    Image.MAX_IMAGE_PIXELS = None

    full_img = Image.fromarray(input_arr)
    full_size = full_img.size
    max_width = min(full_size[0], max_width)
    width_ratio = full_size[0] // max_width
    new_size = (max_width, full_size[1] // width_ratio)
    scaled_img = full_img.resize(new_size)
    scaled_img.save(output_thumbnail_path, format="PNG")
    return True


def main(argv=sys.argv[1:]):
    from argparse import ArgumentParser

    from polar2grid.core.dtype import str_to_dtype

    parser = ArgumentParser(description="Compare two files per pixel")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=0,
        help="each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default ERROR)",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="specify threshold for comparison differences (see numpy.isclose 'atol' parameter)",
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=0.0,
        help="specify relative tolerance for comparison (see numpy.isclose 'rtol' parameter)",
    )
    parser.add_argument(
        "--shape",
        dest="shape",
        type=int,
        nargs=2,
        default=(None, None),
        help="'rows cols' for binary file comparison only",
    )
    parser.add_argument("--dtype", type=str_to_dtype, help="Data type for binary file comparison only")
    parser.add_argument(
        "--variables",
        nargs="+",
        help="NetCDF/HDF5 variables to read and compare. If not provided all variables will be compared.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Show a plot of the two arrays instead of checking equality. Used for debugging.",
    )
    parser.add_argument(
        "--html",
        nargs="?",
        default=False,
        help="Generate an HTML page summarizing comparison status and save it to this filename. "
        "If specified with no argument then defaults to 'comparison_summary.html'. All additional "
        "files (images, CSS, etc) will be placed in the same directory.",
    )
    parser.add_argument("--margin-of-error", type=float, default=0.0, help="percent of total pixels that can be wrong")
    parser.add_argument(
        "file_type",
        type=_file_type,
        nargs="?",
        help="Type of files being compare. If not provided it will be determined based on file extension.",
    )
    parser.add_argument("input1", help="First filename or directory to compare. This is typically the expected output.")
    parser.add_argument("input2", help="Second filename or directory to compare. This is typicall the actual output.")
    args = parser.parse_args(argv)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(3, args.verbosity)])
    compare_kwargs = {
        "shape": tuple(args.shape),
        "dtype": args.dtype,
        "variables": args.variables,
        "file_type": args.file_type,
    }

    comparer = CompareHelper(
        atol=args.atol, rtol=args.rtol, margin_of_error=args.margin_of_error, create_plot=args.plot
    )
    file_comparison_results = comparer.compare(args.input1, args.input2, **compare_kwargs)
    num_files = num_failed_files(file_comparison_results)

    if args.html is None:
        args.html = "comparison_summary.html"
    if args.html:
        _generate_html_summary(args.html, file_comparison_results)

    if num_files == 0:
        print("All files passed")
        print("SUCCESS")
    else:
        print(f"ERROR: {num_files} files were found to be unequal")

    # 0 if successful, otherwise number of failed files
    return num_files


if __name__ == "__main__":
    sys.exit(main())
