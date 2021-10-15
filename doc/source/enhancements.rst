:orphan:

Enhancements
============

Enhancing is the process where data is scaled to prepare the data for
an output image format. These "enhancements" range from basic linear
scaling for the data to fit in the output image format (ex. unsigned 8-bit
integers), but can also scale the data to bring out certain areas of the
data (ex. brighten dark regions of the image). The enhancement step is
typically embedded as part of the writing process. They are configured
in their own YAML configuration files with logical defaults to produce
high quality images.

Customizing enhancements is considered an advanced feature. You can find more
information on customizing enhancements in the :doc:`custom_config` section.
For more information on what Python enhancement functions are available see
the :doc:`satpy:enhancements` documentation from Satpy.

There are additionally some |project| specific enhancements that are used
in special cases or for special products. The enhancements that |project|
actually ends up using is dependent on the builtin YAML configuration files
and any customizations made by the user.

.. currentmodule:: polar2grid.enhancements

.. autosummary::

    ~shared.temperature_difference
