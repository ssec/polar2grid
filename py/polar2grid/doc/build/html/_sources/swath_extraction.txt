Swath Extraction
================

Swath extraction is the process of combining imager data granules into one
swath.  This is usually the first major step in the polar2grid remapping
process, which means that it is also responsible for providing all
the meta data to the rest of the polar2grid "chain".  The very basic
responsibility of the swath extraction step is to make flat binary
swath files for latitude, longitude, and image data.

From a developer stand point, there is no required series of steps or
order to any steps for the swath extraction process.  It is only required that
at least the 3 swath files and a meta data dictionary are provided
to allow for further processing.  As an example the VIIRS swath extractor
takes these steps:

    1. Parse meta data from the image filepaths
    2. Parse meta data from the geonav filepaths
    3. Read in latitude and longitude data and append it to a flat binary file
    4. Read in image data and append it to a flat binary file


