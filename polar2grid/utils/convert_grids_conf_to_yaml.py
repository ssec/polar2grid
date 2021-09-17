import logging
import os
import sys
import warnings

import yaml
from pyproj import CRS, Proj
from polar2grid.grids import GridManager
from polar2grid.grids.manager import read_grids_config

logger = logging.getLogger(__name__)


def _conf_to_yaml_dict(grids_filename: str) -> str:
    overall_yaml_dict = {}
    gm = GridManager(grids_filename)
    grids_information = read_grids_config(grids_filename, convert_coords=False)
    for grid_name, grid_info in grids_information.items():
        crs = CRS.from_proj4(grid_info["proj4_str"])
        if crs.to_epsg() is not None:
            proj_dict = {"EPSG": crs.to_epsg()}
        else:
            proj_dict = crs.to_dict()
        area_dict = {}
        area_dict["description"] = ""
        area_dict["projection"] = proj_dict
        width = grid_info["grid_width"]
        height = grid_info["grid_height"]
        if width is not None and height is not None:
            area_dict["shape"] = {"height": height, "width": width}
        dx = abs(grid_info["pixel_size_x"])
        dy = abs(grid_info["pixel_size_y"])
        if dx is not None and dy is not None:
            area_dict["resolution"] = {"dy": dy, "dx": dx}
        ox = grid_info["grid_origin_x"]
        oy = grid_info["grid_origin_y"]
        if ox is not None and dx is None:
            logger.error("Can't convert grid with origin but no pixel resolution: %s", grid_name)
            continue
        if ox is not None and oy is not None:
            convert_to_meters = not crs.is_geographic and grid_info["grid_origin_units"] == "degrees"
            ox_m, oy_m = Proj(crs)(ox, oy) if convert_to_meters else (ox, oy)
            # convert center-pixel coordinates to outer edge extent
            ox_m = ox_m - dx / 2.0
            oy_m = oy_m + dy / 2.0
            ox, oy = Proj(crs)(ox_m, oy_m, inverse=True) if convert_to_meters else (ox_m, oy_m)
            area_dict["upper_left_extent"] = {"x": ox, "y": oy, "units": grid_info["grid_origin_units"]}
        overall_yaml_dict[grid_name] = area_dict
    return overall_yaml_dict


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    """Dump the data to YAML in ordered fashion."""

    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items(), flow_style=False)

    OrderedDumper.add_representer(dict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


def main():
    from argparse import ArgumentParser

    prog = os.getenv("PROG_NAME", sys.argv[0])
    parser = ArgumentParser(
        description="Convert legacy grids.conf format to Pyresample YAML format.",
        usage="""
To write to a file:
    %(prog)s input_file.conf > output_file.yaml
""",
    )
    parser.add_argument("grids_filename", help="Input grids.conf-style file to convert to YAML.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    warnings.filterwarnings("ignore", module="pyproj", category=UserWarning)
    yaml_dict = _conf_to_yaml_dict(args.grids_filename)
    yml_str = ordered_dump(yaml_dict, default_flow_style=None)
    print(yml_str)


if __name__ == "__main__":
    sys.exit(main())
