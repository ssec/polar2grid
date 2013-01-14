Frontend to Backend Scripts (Glue Scripts)
==========================================

As mentioned above, the scripts that connect frontend to backend have a lot
of freedom and should be considered the dumping ground for any special case
code. They also follow the convention of placing all intermediate and product
files in the current directory, the directory that the script was executed
from.  Frontends, backends, remapping, and any other polar2grid component
will follow this convention so glue script should do the same.

Glue scripts are the first (and usually the only) python script that should be
called by the user.
They have command line arguments that are relevant to their specific frontends
and backends, as well as those common to all glue scripts (like remapping and
grid determination options).  The main responsibility of a glue script is to
take input data filenames from the command line, separate them by files that
share the navigation data
(usually by filename pattern), and process each set of those files separately.
Processing means calling the frontend to get the data into swaths, calling
the grid determiner to find what grids the data should be mapped to,
calling the remapper to remap/grid the data, and calling the backend to
produce the gridded data in a format useful to others.

Glue scripts may use the metadata dictionary returned from the frontend
as storage for additional metadata.  This makes it easier to manage information
since the metadata dictionary already contains a 'per band' data structure.
This is optional, but may be helpful for implementing the script. Meta-data
keys/values should never be overwritten, only adding new keys should be done.
Overwriting will
make debugging more difficult and will likely result in problems.

