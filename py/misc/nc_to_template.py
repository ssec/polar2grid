"""Take a NetCDF file compatible with AWIPS or NCEP grids and replace
all image data with an array of NaNs.  The output file should be used
as a template: copied to a new location and then filled with actual
image data.

Author: David Hoese,davidh,SSEC
"""
import os
import sys
import shutil
import logging
from netCDF4 import Dataset
from numpy import array,repeat,nan

log = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.DEBUG)
    usage = """
Usage: python nc_to_template.py <input nc> <output nc>
"""
    args = sys.argv[1:]
    if len(args) != 2:
        log.error("Requires 2 arguments: input file and output file")
        print usage
        return -1

    input_file = os.path.abspath(args[0])
    output_file = os.path.abspath(args[1])

    if not os.path.exists(input_file):
        log.error("Input file %s does not exist" % input_file)
        return -1

    if os.path.exists(output_file):
        log.error("Output file %s already exists" % output_file)
        return -1

    # Copy the original to the template location
    try:
        log.debug("Copying input file to output file location")
        shutil.copyfile(input_file, output_file)
    except StandardError:
        log.error("Could not move input file to output location", exc_info=1)
        return -1

    # Open the template file
    try:
        log.debug("Opening output file to fill in data")
        nc = Dataset(output_file, "a")#, format="NETCDF3_CLASSIC")
    except StandardError:
        log.error("Error trying to open NC file")
        try:
            log.debug("Trying to remove file that couldn't be opened %s" % output_file)
            os.remove(output_file)
        except StandardError:
            log.warning("Bad output file could not be removed %s" % output_file)
        finally:
            return -1

    if nc.file_format != "NETCDF3_CLASSIC":
        log.warning("Expected file format NETCDF3_CLASSIC got %s" % nc.file_format)

    # Change the data to all NaNs
    if "image" not in nc.variables:
        log.error("NC variable 'image' does not exist in %s" % input_file)
        return -1

    columns,rows = nc.variables["image"].shape
    del nc.variables["image"]
    #nc.variables["image"][:] = repeat(repeat([[nan]], columns, axis=1), rows, axis=0)
    nc.variables["validTime"][:] = 0
    nc.close()

    log.info("Template created successfully")
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
