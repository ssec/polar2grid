"""Generate ``grids_list.rst`` from Polar2Grid's built-in grid definitions.

The page is written into the source directory before the build reads any sources and is
gitignored. It is listed in ``exclude_patterns`` because ``grids.rst`` pulls it in with an
``include`` directive rather than a toctree entry, which is why this runs at a lower
priority than the checks in :mod:`_ext.config_checks` -- those verify that every literal
exclude entry names a file that exists.
"""

import warnings
from pathlib import Path

import yaml
from pyproj import CRS

import polar2grid

#: Run ahead of the default priority so the page exists before anything looks for it.
GENERATE_PRIORITY = 100

#: The grids to document, and the title to give each one. A grid that is missing here is
#: left out of the generated page.
GRID_TITLES = {
    "wgs84_fit": "WGS84 Dynamic Fit",
    "wgs84_fit_250": "WGS84 Dynamic Fit 250m",
    "lcc_fit": "Lambert Conic Conformal Dynamic Fit",
    "lcc_fit_hr": "High Resolution Lambert Conic Conformal Dynamic Fit",
    "lcc_sa": "Lambert Conic Conformal - South America Centered",
    "lcc_eu": "Lambert Conic Conformal - Europe Centered",
    "lcc_south_africa": "Lambert Conic Conformal - South Africa Centered",
    "lcc_aus": "Lambert Conic Conformal - Australia Centered",
    "lcc_asia": "Lambert Conic Conformal - Asia Centered",
    "polar_north_pacific": "Polar-Stereographic North Pacific",
    "polar_south_pacific": "Polar-Stereographic South Pacific",
    "polar_alaska": "Polar-Stereographic Alaska",
    "polar_canada": "Polar-Stereographic Canada",
    "polar_russia": "Polar-Stereographic Russia",
    "eqc_fit": "Equirectangular Fit",
    "goes_east_1km": "GOES-East 1km",
    "goes_east_4km": "GOES-East 4km",
    "goes_east_8km": "GOES-East 8km",
    "goes_east_10km": "GOES-East 10km",
    "goes_west_1km": "GOES-West 1km",
    "goes_west_4km": "GOES-West 4km",
    "goes_west_8km": "GOES-West 8km",
    "goes_west_10km": "GOES-West 10km",
}


def write_grids_list(app, config):
    """Write ``grids_list.rst`` describing each documented built-in grid."""
    builtin_areas_filename = Path(polar2grid.__file__).parent / "grids" / "grids.yaml"
    with open(builtin_areas_filename) as yaml_file:
        areas_dict = yaml.load(yaml_file, Loader=yaml.SafeLoader)

    with warnings.catch_warnings(), open(Path(app.srcdir) / "grids_list.rst", "w") as grids_list_file:
        warnings.filterwarnings("ignore", module="pyproj", category=UserWarning)
        for area_name, area_dict in areas_dict.items():
            area_title = GRID_TITLES.get(area_name)
            if area_title is None:
                continue
            grids_list_file.write(_grid_rst(area_name, area_title, area_dict))


def _grid_rst(area_name, area_title, area_dict):
    """Render the reStructuredText section describing a single grid."""
    proj = area_dict["projection"]
    crs = CRS.from_user_input(proj.get("EPSG", proj))
    title_underline = "^" * len(area_title)
    rst_str = f"""
.. _grid_{area_name}:

{area_title}
{title_underline}

:Grid Name: {area_name}
:Description: {area_dict["description"]}
:Projection: {crs.to_string()}
"""

    if "resolution" in area_dict:
        res = area_dict["resolution"]
        xres = res["dx"]
        yres = res["dy"]
        def_units = "degrees" if crs.is_geographic else "meters"
        units = res.get("units", def_units)
        if xres != yres:
            rst_str += f":Resolution (X): {xres} {units}\n"
            rst_str += f":Resolution (Y): {yres} {units}\n"
        else:
            rst_str += f":Resolution: {xres} {units}\n"
    if "area_extent" in area_dict:
        rst_str += f":Extent: {area_dict['area_extent']}\n"
    return rst_str


def setup(app):
    """Connect the generator early enough that the page exists for the rest of the build."""
    app.connect("config-inited", write_grids_list, priority=GENERATE_PRIORITY)
    return {"version": "1.0.0", "parallel_read_safe": True, "parallel_write_safe": True}
