
import collections

# http://geospatialmethods.org/documents/ppgc/ppgc.html#projection_names

ALBERS = "Albers Conic Equal-Area"
AZIMUTHAL = "Azimuthal Equal-Area"
AZIMUTHAL_ELLIPSOID = "Azimuthal Equal-Area (ellipsoid)"
CYLINDRICAL = "Cylindrical Equal-Area"
CYLINDRICAL_ELLIPSOID = "Cylindrical Equal-Area (ellipsoid)"
CYLINDRICAL_EQUIDISTANT = "Cylindrical Equidistant"
INTEGERIZED_SINUSOIDAL = "Integerized Sinusoidal"
HOMOLOSINE = "Interrupted Homolosine Equal-Area"
LAMBERT_CONFORMAL = "Lambert Conic Conformal (ellipsoid)"
MERCATOR = "Mercator"
MOLLWEIDE = "Mollweide"
ORTHOGRAPHIC = "Orthographic"
POLAR_STEREOGRAPHIC = "Polar Stereographic"
POLAR_STEREOGRAPHIC_ELLIPSOID = "Polar Stereographic (ellipsoid)"
SINUSOIDAL = "Sinusoidal"
TRANSVERSE_MERCATOR = "Transverse Mercator"
TRANSVERSE_MERCATOR_ELLIPSOID = "Transverse Mercator (ellipsoid)"
UNIVERSAL_TRANSVERSE_MERCATOR = "Universal Transverse Mercator"


MAP_PARAMETERS = collections.OrderedDict()
MAP_PARAMETERS["projection"] = str
MAP_PARAMETERS["reference_latitude"] = float
MAP_PARAMETERS["reference_longitude"] = float
MAP_PARAMETERS["second_reference_latitude"] = float
MAP_PARAMETERS["rotation"] = float
MAP_PARAMETERS["scale"] = float
MAP_PARAMETERS["origin_latitude"] = float
MAP_PARAMETERS["origin_longitude"] = float
MAP_PARAMETERS["origin_x"] = float
MAP_PARAMETERS["origin_y"] = float
MAP_PARAMETERS["false_easting"] = float
MAP_PARAMETERS["false_northing"] = float
MAP_PARAMETERS["eccentricity"] = float
MAP_PARAMETERS["eccentricity_squared"] = float
MAP_PARAMETERS["equatorial_radius"] = float
MAP_PARAMETERS["polar_radius"] = float
MAP_PARAMETERS["center_scale"] = float
MAP_PARAMETERS["maximum_error"] = float



# For spherical projections, the eccentricity should not be specified, and the default equatorial radius is 6371.228,
SPHERICAL_RADIUS = 6371.228

# For elliptical projections, the default eccentricity is 0.082271673 and the default equatorial radius is 6378.2064
ELLIPTICAL_ECCENTRICITY = 0.082271673
ELLIPTICAL_RADIUS = 6378.2064

# WGS-84 ellipsoid in meters, use 0.081819190843 for the eccentricity and 6378137.0 for the equatorial radius.
WGS84_ECCENTRICITY = 0.081819190843
WGS84_RADIUS = 6378137.0


def _munge(key):
    words = ['map'] + key.split('_')
    return '_'.join((x[0].upper() + x[1:]) for x in words)


def text(mppdict):
    for k,v in mppdict.items():
        yield '%s:%s' % (_munge(k), v)


def is_valid(mppdict):
    return set(mppdict.keys()).issubset(set(MAP_PARAMETERS.keys()))


def lambert_conformal(lon1, lat1, lon2, lat2):
    return dict(
        projection = LAMBERT_CONFORMAL,
        reference_latitude = lat1,
        reference_longitude = lon1,
        second_reference_

    )
    zult = MAP_PARAMETERS.copy()
