JSON and Binary Input
=====================

.. warning::

    This feature is not finalized and will likely change with more user
    feedback and as collaboration with the PyTroll team evolves.

Polar2Grid supports many types of input files, but supporting all possible
formats and schemes would be impossible to keep up with. The simple solution
is to provide an intermediate file format that can be easily created by anyone
with little to no programming experience. Polar2Grid's solution for this is
a combination of a `JSON <https://en.wikipedia.org/wiki/JSON>`_ text file
describing the data going in to Polar2Grid and flat binary files (binary
files with only data and no header information).

The following sections will describe what has to be done to process these
files through Polar2Grid.

Create the binary files
-----------------------

Each swath of data that you would like processed must be saved to a file
on disk as a flat binary file. A flat binary file is a binary file with
no header or other metadata; it is just the binary swath data. The data
must be in row-major order (all of row 0, followed by row 1, etc).
Currently 32-bit floats are the only supported data type for these files.
Polar2Grid normally names its flat binary files with a ".dat" extension.

In addition to the observation data being written to a flat binary file
the longitude and latitude data must also be written flat binary files.
That's a total of 3 files. Geolocation files can be reused when processing
multiple bands/products that share the same geolocation (no need to make
copies).
Place all of your flat binary files in the same directory and then create
your JSON description file (see below).

Create the JSON file
--------------------

JSON is a simple text format that can be read and written by many modern
programming languages. It is recommended that you create one text file
with a ".json" suffix. A simple use case describing one product to be
processed is shown below.

After creating a 32-bit float flat binary file named "my_swath_scene.dat",
a 32-bit float flat binary file named "lon.dat" and one named "lat.dat"
for the geolocation, create a text file named "my_json.json".
These filenames are arbitrary
and can be whatever you want. In the JSON file enter the
following information::

    {
        "vis01": {
            "product_name": "vis01",
            "instrument": "fakeinst",
            "satellite": "fakesat",
            "data_kind": "reflectance",
            "begin_time": "2015-10-23T20:47:16.990000",
            "end_time": "2015-10-23T20:57:13.820000",
            "fill_value": NaN,
            "swath_columns": 2048,
            "swath_rows": 3582,
            "rows_per_scan": 3582,
            "swath_data": "my_data.dat",
            "data_type": "real4",
            "description": "",
            "units": "",
            "swath_definition": {
                "swath_name": "nav",
                "latitude": "lat.dat",
                "longitude": "lon.dat",
                "data_type": "real4",
                "fill_value": NaN,
                "swath_columns": 2048,
                "swath_rows": 3582,
                "rows_per_scan": 3582
            }
        }
    }

Most of the fields in this text should be fairly self explanatory, but further
details can be found in the table below. The order of the key/value pairs
relative to one another does not matter, however, they must always be
comma-separated. One important thing to note is that
the "vis01" near the top of the file should match the "vis01" specified for
the "product_name". The "vis01" near the top is the "key" in the JSON
dictionary and is described in more detail in later sections.

+---------------------+-----------------------------------------------------+
| JSON Key            | Description                                         |
+=====================+=====================================================+
| product_name        | Unique name used to identify this product           |
+---------------------+-----------------------------------------------------+
| instrument          | Lowercase name for the associated instrument. It is |
|                     | best to use the name already in Polar2Grid if this  |
|                     | instrument is supported by a builtin Front End.     |
+---------------------+-----------------------------------------------------+
| satellite           | Lowercase name for the associated satellite         |
|                     | similar to 'instrument'.                            |
+---------------------+-----------------------------------------------------+
| data_kind           | Type of observation: 'radiance', 'reflectace',      |
|                     | 'brightness_temperature', or other arbitrary name.  |
+---------------------+-----------------------------------------------------+
| rows_per_scan       | If applicable, number of rows of data that makes up |
|                     | one scanline of data (equal to 'swath_rows' if not  |
|                     | a scan based product). This can affect remapping.   |
+---------------------+-----------------------------------------------------+
| swath_name          | Unique name to identify one set of geolocation data |
|                     | from another.                                       |
+---------------------+-----------------------------------------------------+


Remap the JSON
--------------

Now that you have binary files and a JSON text file describing them you can run
the data through Polar2Grid's remapping. To do so run the following command::

    $POLAR2GRID_HOME/ShellB3/bin/p2g_remap -vv --method ewa -g wgs84_fit --scene my_swath_scene.json -o my_grid_scene.json

This will remap the input data creating new gridded binary files and will
output the JSON description of this gridded data in to "my_grid_scene.json".
Information about other command line options can be printed with the "-h"
flag.

.. note::

    You may get "WARNING" log messages about missing "__class__" definitions.
    The commands should still complete successfully regardless.

Create Geotiffs from remapped JSON
----------------------------------

Once you have a gridded scene, you can run any Polar2Grid writer on that
data. Here is an example of creating a geotiff::

    $POLAR2GRID_HOME/ShellB3/bin/p2g_backend gtiff -vv --scene my_grid_scene.json

This will create a geotiff file for each product in the gridded scene. Further
command line option descriptions are printed with the "-h" flag.

Processing multiple products
----------------------------

The above sections described the simple case of processing a single band or
product of swath data. The JSON description for multiple products gets a
little more complicated and requires more of an understanding of the
JSON file structure.

The simplest but longer method for specifying multiple bands is
to just list each "product definition" mapping multiple times like
this (ellipses used for brevity)::

    {
        "vis01": {
            "product_name": "vis01",
            ...
            "swath_definition": {
                "swath_name": "nav",
                ...
            },
        },
        "vis02": {
            "product_name": "vis02",
            ...
            "swath_definition": {
                "swath_name": "nav",
                ...
            },
        }
    }

As you can see this requires repeating the "swath_definition" mapping multiple
times. Another way to reduce the amount of typing is to put the swath
definition in a separate JSON file, "my_swath_def.json" for example::

    {
    "swath_name": "nav",
    "latitude": "lat.dat",
    "longitude": "lon.dat",
    "data_type": "real4",
    "fill_value": NaN,
    "rows_per_scan": 3582,
    "swath_columns": 2048,
    "swath_rows": 3582
    }

Then in the product definitions file specify that swath definition file::

    {
        "vis01": {
            "product_name": "vis01",
            ...
            "swath_definition": "my_swath_def.json",
        },
        "vis02": {
            "product_name": "vis02",
            ...
            "swath_definition": "my_swath_def.json",
        }
    }

The Polar2Grid commands to process this JSON file are the same as before.
