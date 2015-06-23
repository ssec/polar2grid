Compositors
===========

Compositors are optional components of Polar2Grid that can be used after
:doc:`remapping <../remapping>`, but before a :doc:`backend <../backends/index>`.
A compositor can be used to combine multiple Polar2Grid bands to create a new product.
Normally these types of operations would be done in a :doc:`frontend <../frontends/index>`
to create a :term:`secondary product`. However, sometimes calculations require combining
products of different sizes and resolutions or creating a product with multiple levels like
RGB images. These operations are much easier to handle after remapping, which is where
compositors come in.

Compositors can be specified on the command line for the :term:`glue script` or can be
called from within python. Compositors can be used from the CSPP software bundle by
specifying their names as the first arguments to a glue script, but the usual case of
creating true color images is already the default for the ``crefl2gtiff.sh`` script.

Compositors can be used from the python command line access by either calling the glue
script::

    p2g_glue <frontend> <backend> [<compositor> ...] ...

What compositors are available can be customized with a configuration file specified
with the ``--compositor-configs`` flag.

.. note::

    Compositor's require a specific set of products to complete their calculations. If any required information
    is missing then the compositor will fail.

Compositors that come with Polar2Grid are described below. For information on creating your own
custom RGB see the :doc:`Developer's Guide <dev_guide/compositors>`.

.. note::

    Compositors and the way they are implemented will change in future releases after collaboration with the PyTroll
    team.

.. automodule:: polar2grid.compositors.rgb

