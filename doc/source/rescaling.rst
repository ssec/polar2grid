Rescaling
=========

.. warning::

    This page refers to legacy implementations of "enhancement" in Polar2Grid.
    It does not necessarily reflect how Polar2Grid and Geo2Grid currently work
    and may be outdated. It is kept here for reference, but may be removed in
    the future.

Rescaling is a polar2grid component shared by most writers that rescales
gridded image data via the ``Rescaler`` object. Rescaling provides simple
enhancement capabilities to prepare the product data for an image format.
The following sections describe each scaling function in the rescaling code.
The defaults provided by Polar2Grid will create nice looking images suitable
for most users.

The functions described below are intended for use by polar2grid writers via
the ``Rescaler`` object, but can be used elsewhere if needed.
These functions ignore any fill/invalid values in the data. Common values
for an 8-bit (0-255) output are shown as an example. The ``Rescaler``
object uses `configuration files <https://github.com/ssec/polar2grid/blob/master/polar2grid/core/rescale_configs/rescale.ini>`_
to set how bands are scaled. The function keyword arguments are passed
from the configuration file values.

.. note::

    Rescaling configuration files will change in future versions due to Pytroll
    collaboration and merging. Please contact us if you have a custom configuration
    that you need converted to the new (similar) format.

There is a shared `clip` configuration parameter that defaults to `True` that will
clip data after scaling to the output data limits.

Linear
------

:method: linear
:min_in: Minimum value for linear parameter calculations
:max_in: Maximum value for linear parameter calculations
:flip: Use an inverse linear calculation on the input data

.. note::

    If ``min_in`` and ``max_in`` aren't specified they are calculated on the fly from the provided data.

.. note::

    In the default configuration file this method is used as the default rescaling method

.. math::

    \text{m} = (max\_out - min\_out) / (max\_in - min\_in)

    \text{b} = min\_out - m * min\_in

    \text{rescale\_data} = \text{data} * m + b

Example (10-255 from 173-300):

.. math::

    \text{m} = (255.0 - 10.0) / (300.0 - 173.0) = 1.9291338

    \text{b} = 10.0 - 1.9291338 * 173.0 = -323.74014

    \text{rescale\_data} = 1.9291338 * \text{data} + -323.74014

.. _rescale_square_root_enhancement:

Square Root Enhancement
-----------------------

:method: sqrt
:min_in: Minimum input value (default: 0.0)
:max_in: Maximum input value (default: 1.0)
:inner_mult: Multiplier before calling sqrt (default: 100.0 / max_in)
:outer_mult: Multiplier after calling sqrt (default: max_out / sqrt(inner_mult * max_in))

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * inner\_mult} * outer\_mult)

Example (0-255 from 0-1 data):

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * 100.0} * 25.5)

.. _rescale_btemp:

Brightness Temperature
----------------------

:method: btemp
:threshold: Temperature threshold in Kelvin when to do high or low piecewise operations (default: 176/255.0 * max_out)
:min_in: Minimum input value
:max_in: Maximum input value

.. math::

    \text{rescaled\_data} =
    \begin{cases}
        \text{linear\_scaling}(\text{data}, min\_in, threshold) & \text{temp} < threshold \\
        \text{linear\_scaling}(\text{data}, threshold, max\_in) & \text{temp}\ge threshold
     \end{cases}

Example (0-255 from brightness temperature data):

.. math::

    \text{rescaled\_data} =
    \begin{cases}
        418 - (1 * \text{temp}) & \text{temp} < 242.0 \\
        660 - (2 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}

Fog (Temperature Difference)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:method: temperature_difference
:min_in: Minimum input value (default: -10.0)
:max_in: Maximum input value (default: 10.0)

.. math::

    \text{clip\_min} = min\_out + 5

    \text{clip\_max} = 0.8 * (max\_out - min\_out)

    \text{rescaled\_data} = \text{linear\_scaling}(\text{data}, clip\_min, clip\_max, min\_in, max\_in)

    \text{rescale\_data}[\text{rescale\_data} < clip\_min] = clip\_min - 1

    \text{rescale\_data}[\text{rescale\_data} > clip\_max] = clip\_max + 1

Inverse Linear
--------------

:method: unlinear
:m: Factor in linear equation
:b: Offset in linear equation

.. math::

    \text{rescaled\_data} = (\text{data} - b) / m

Example (0-255 from 0-1 data):

.. math::

    \text{rescaled\_data} = (\text{data} - 0.0) / 0.00392

Lookup
------

:method: lookup
:min_in: Same as Linear scaling
:max_in: Same as Linear scaling
:table_name: Name of lookup table to use (default: crefl)

.. note::

    The ``table_name`` argument is optional. The choices are currently hardcoded
    in the software. Default is useful for True Color and False Color images.

.. math::

    \text{rescaled\_data} = \text{available\_lookup\_tables}[table\_name][ {linear\_scaling}(\text{data}) ]

Land Surface Temperature
------------------------

:method: lst

Same as Linear scaling, but 5 is added to ``min_out`` and 5 is subtracted from ``max_out`` and data is clipped to these
new limits after scaling.

Cloud Top Temperature
---------------------

:method: ctt

Same as linear scaling, but 10 is added to ``min_out`` and 5 is subtracted from ``max_out`` and data is clipped to these
new limits after scaling.

NDVI
----

:method: ndvi
:min_in: Minimum input value (default: -1.0)
:max_in: Maximum input value (default: 1.0)
:threshold: Threshold between 'low' and 'high' operations (default: 0.0)
:threshold_out: Output maximum for 'low' operations and minimum for 'high' operations (default: 49 / 255.0 * max_out)

.. math::

    \text{rescaled\_data} =
    \begin{cases}
        \text{linear\_scaling}(\text{data}, min\_out, threshold\_out, min\_in, threshold) & \text{data} < threshold \\
        \text{linear\_scaling}(\text{data}, threshold\_out, max\_out, threshold, max\_in) & \text{data}\ge threshold
     \end{cases}

Passive
-------

:method: raw

A passive function to tell the rescaler "don't do anything".

Palettize
---------

:method: palettize
:min_in: Minimum input value
:max_in: Maximum input value
:colormap: Colormap file (ex. ``$POLAR2GRID_HOME/colormaps/amsr2_36h.cmap``) or builtin colormaps from `trollimage <https://trollimage.readthedocs.io/en/latest/colormap.html#default-colormaps>`_.
:alpha: Include Alpha band in final image instead of using 0 as fill value (default: True)

Map input values linearly between ``min_in`` and ``max_in`` and map to
colors from ``colormap``. If ``alpha`` is ``True`` (default) then all colors
will be used for valid data points and a separate alpha channel will make
GeoTIFFs transparent where values are invalid. If ``alpha`` is ``False`` then
the color associated with value ``0`` will be used for invalid values.
