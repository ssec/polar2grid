#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script manually called to generate the summary table in the documentation.

The Polar2Grid summary table contains the possible input and output, reader
and writer combinations.

Example output:

    .. list-table::
        :header-rows: 1

        * - Input Source
          - Example Filename Pattern
          - Output Type
          - Polar2Grid Execution
        * - 1
          - 2
          - 3
          - 4

"""

import os
import sys
from collections import namedtuple

script_dir = os.path.realpath(os.path.dirname(__file__))
output_pathname = os.path.join(script_dir, "summary_table.rst")

COLUMN_ORDER = ["source", "input_patterns", "output_type", "reader", "writer", "legacy_script"]
COLUMN_TITLE = {
    "source": "Input Source",
    "input_patterns": "Input Filename Pattern",
    "output_type": "Output Type",
    "reader": "Reader Name",
    "writer": "Writer Name",
    "legacy_script": "Legacy Script",
}


class TableRow(
    namedtuple("TableRow", ("source", "input_patterns", "output_type", "reader", "writer", "legacy_script"))
):
    def __new__(cls, *args):
        if len(args) < 6:
            args = args + ("{reader}2{writer}.sh".format(reader=args[3], writer=args[4]),)
        return super(TableRow, cls).__new__(cls, *args)


summary_table = [
    TableRow(
        "Suomi-NPP VIIRS Sensor Data Records",
        ["SVI01_npp_*.h5", "GITCO_npp_*.h5"],
        "8-bit single band GeoTIFF",
        "viirs_sdr",
        "gtiff",
        "viirs2gtiff.sh",
    ),
    TableRow(
        '"',
        '"',
        "AWIPS NetCDF3",
        "viirs_sdr",
        "awips",
        "viirs2awips.sh",
    ),
    TableRow(
        '"',
        '"',
        "HDF5",
        "viirs_sdr",
        "hdf5",
        "viirs2hdf5.sh",
    ),
    TableRow(
        '"',
        '"',
        "Binary",
        "viirs_sdr",
        "binary",
        "viirs2binary.sh",
    ),
    TableRow(
        '"',
        '"',
        "24-bit true and false color GeoTIFF",
        "crefl",
        "gtiff",
    ),
    TableRow(
        "Aqua and Terra MODIS Level 1b (IMAPP or NASA archive files)",
        ["MOD021KM*.hdf", "MOD03*.hdf", "", "or", "", "t1.*1000m.hdf", "t1.*.geo.hdf"],
        "8 bit single band GeoTIFF",
        "modis",
        "gtiff",
    ),
    TableRow(
        '"',
        '"',
        "AWIPS NetCDF3",
        "modis",
        "awips",
    ),
    TableRow(
        '"',
        '"',
        "HDF5",
        "modis",
        "hdf5",
    ),
    TableRow(
        '"',
        '"',
        "Binary",
        "modis",
        "binary",
    ),
    TableRow(
        '"',
        '"',
        "24-bit true and false color GeoTIFF",
        "crefl",
        "gtiff",
    ),
    TableRow(
        "NOAA-18, NOAA-19, Metop-A and Metop-B AVHRR AAPP Level 1b",
        ["hrpt_noaa18_*.l1b"],
        "8 bit single band GeoTIFF",
        "avhrr",
        "gtiff",
    ),
    TableRow(
        '"',
        '"',
        "AWIPS NetCDF3",
        "avhrr",
        "awips",
    ),
    TableRow(
        '"',
        '"',
        "HDF5",
        "avhrr",
        "hdf5",
    ),
    TableRow(
        '"',
        '"',
        "Binary",
        "avhrr",
        "binary",
    ),
    TableRow(
        "GCOM-W1 ASMR2 L1B",
        ["GW1AM2*L1DLBTBR*.h5"],
        "8 bit single band GeoTIFF",
        "amsr2_l1b",
        "gtiff",
        "N/A",
    ),
    TableRow(
        '"',
        '"',
        "AWIPS NetCDF3",
        "amsr2_l1b",
        "awips",
        "N/A",
    ),
    TableRow(
        '"',
        '"',
        "HDF5",
        "amsr2_l1b",
        "hdf5",
        "N/A",
    ),
    TableRow(
        '"',
        '"',
        "Binary",
        "amsr2_l1b",
        "binary",
        "N/A",
    ),
]


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.parse_args()

    out_file = open(output_pathname, "w")

    s = """.. File auto-generated by ``generate_summary_table.py``

.. list-table:: Reader/Writer Summary Table
    :header-rows: 1

"""

    header_row = "    * - " + "\n      - ".join([COLUMN_TITLE[n] for n in COLUMN_ORDER]) + "\n"
    s += header_row

    for entry in summary_table:
        items = []
        for n in COLUMN_ORDER:
            item = getattr(entry, n)
            if isinstance(item, (list, tuple)):
                item = "\n        ".join(item)
            items.append(item)
        s += "    * - " + "\n      - ".join(items) + "\n"

    out_file.write(s)


if __name__ == "__main__":
    sys.exit(main())
