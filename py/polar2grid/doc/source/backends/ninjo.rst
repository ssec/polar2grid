NinJo
=====

The NinJo Workstation Project is a meteorological workstation system for
viewing various weather images. NinJo in some ways is like AWIPS is to
the United States Nation Weather Service (NWS), but is used by various
countries around the world.

The NinJo backend for polar2grid was specifically developed to assist the
"Deutscher Wetterdienst" (DWD) in displaying NPP VIIRS data in NinJo.
This partnership between the DWD and |ssec| lead to a fairly specialized
system that creates NinJo compatible TIFF images. NinJo allows for
multiple "readers" or plugins to its system to allow for various formats
to be read. The polar2grid backend is specifically for the TIFF reader
used by the DWD. These files are different
from regular TIFF images in that they have a number of tags for describing
the data and the location of that data to NinJo.

TODO: Rescaling
