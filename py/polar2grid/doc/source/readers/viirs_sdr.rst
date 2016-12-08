VIIRS SDR Frontend
==================

.. automodule:: polar2grid.viirs.swath

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.viirs.swath
    :func: add_frontend_argument_groups
    :prog: polar2grid.sh viirs_sdr <backend>
    :passparser:

.. versionchanged:: 2.1
    The reader name has been changed to ``viirs_sdr`` although ``viirs`` is still
    supported for the time being.
