Common Glue Script Options
--------------------------

The following command line options are available for all glue scripts
regardless of the frontend or backend.

.. cmdoption:: -h
               --help

    Print usage and command line option information.

.. cmdoption:: -v
               --verbose

    Print detailed log messages. Increases in level from
    ERROR -> WARNING -> INFO -> DEBUG. The default for companion scripts
    is INFO and for the python script the default is ERROR. To increase the
    level of detail add more ``-v`` to the command line.

.. cmdoption:: -d <data-directory>

    Specify the directory to search for data files. Glue scripts will use
    every data file in that directory that they know how to handle. For
    example, a glue script using the VIIRS frontend will use all SVM, SVI,
    and SVDNB files located in the directory specified. This is the
    alternative to the ``-f`` option.

    .. versionchanged:: 1.0.0
        The -d flag replaced the positional argument for the data directory.

.. cmdoption:: -f <data-file> [<data-file> ...]

    Specify a space separated list of data files to process. This option is
    useful for specifying only certain bands or time ranges of data to
    process. Using shell path expansion to accomplish this type of filtering
    with VIIRS data files can look something like this::
    
        -f /path/to/data/SVM{01,02,12,15}*t18[1,2,3]*.h5
    
    This path would pass only the VIIRS M bands 01, 02, 12, 15 between the
    time range 18:10:00Z - 18:39:59Z.  The ``-f`` flag is the alternative to
    the ``-d`` option.

.. cmdoption:: -R

    This is a special flag that will remove conflicting files from the current
    working directory.  Conflicting files are files that were created by a
    previous call to a glue script and may cause the glue script being called
    to fail.  Specifying this flag on the command line will **NOT** continue
    on processing after conflicting files have been removed.

