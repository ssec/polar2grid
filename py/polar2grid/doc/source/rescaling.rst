Rescaling
=========

Rescaling is a polar2grid component shared by most backends that rescales
gridded image data via the ``Rescaler`` object. The underlying code also
holds scaling functions that may be useful to frontends or glue scripts
to equalize or scale data for other purposes.
The following sections describe each scaling function in the rescaling code.

Backend Scaling Functions
-------------------------

The functions described below are intended for use by polar2grid backends via
the ``Rescaler`` object, but can be used elsewhere if needed.
These functions ignore any fill/invalid values in the data. Common values
for an 8-bit (0-255) output are shown as an example. The ``Rescaler``
object uses `configuration files <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/>`_
to set how bands are scaled. The function definitions
below name the positional arguments in the configuration file.

**Special Note On Auto-Incrementing:**

One thing to note about the default behavior of rescaling in polar2grid is
that it will automatically increment the data after one of the below
rescaling functions is called. This
is to assist the user in the common case that fill values should be their own
unique value (a valid value should not equal a fill value anywhere in the
data). This incrementing is the default behavior in most glue scripts, but
most provide a flag to turn this off (:option:`viirs2gtiff --dont_inc`).

As an
example, if the geotiff backend was given data and then it scaled that
data to a 0-255 range, the default fill value of -999.0 would be set to 0
due to clipping for a specific :term:`data type`.  This means that in
the end product fill/error values would be indistinguishable from valid data
values. Incrementing gets around this; by scaling data to 0-254 and then
incrementing the data you get 0 as the fill value and valid data in the
1-255 range. Of course, data ranges depend on the rescaling decisions of the
backend where most depend on the :term:`data type` of the output.

.. _rescale_square_root_enhancement:

Square Root Enhancement
^^^^^^^^^^^^^^^^^^^^^^^

:rescale_kind: sqrt
:argument 1: inner_mult
:argument 2: outer_mult

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * inner\_mult} * outer\_mult)

Example (0-255 from 0-1 data):

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * 100.0} * 25.5)

.. _rescale_btemp:

Brightness Temperature
^^^^^^^^^^^^^^^^^^^^^^

:rescale_kind: btemp
:argument 1: threshold
:argument 2: high_max
:argument 3: high_mult
:argument 4: low_max
:argument 5: low_mult
:argument 6: clip_min
:argument 7: clip_max

.. note::

    If ``clip_min`` and ``clip_max`` are provided the data is clipped before
    being returned.

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        low\_max - (low\_mult * \text{temp}) & \text{temp} < threshold \\
        high\_max - (high\_mult * \text{temp}) & \text{temp}\ge threshold
     \end{cases}

Example (0-255 from brightness temperature data):

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        418 - (1 * \text{temp}) & \text{temp} < 242.0 \\
        660 - (2 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}

.. _rescale_fog:

Fog (Temperature Difference)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:rescale_kind: fog
:argument 1: m
:argument 2: b
:argument 3: floor
:argument 4: floor_val
:argument 5: ceil
:argument 6: ceil_val

.. math::

    \text{tmp} = m * \text{temp} + b 

    \text{rescaled\_data} = 
    \begin{cases}
        floor\_val & \text{tmp} < floor \\
        ceil\_val & \text{tmp} > ceil \\
        \text{tmp} & \text{otherwise}
    \end{cases}

Example (0-255 from -10-10 degree temperature differences):

.. math::

    \text{tmp} = 10.0 * \text{temp} + 105.0

    \text{rescaled\_data} = 
    \begin{cases}
        4 & \text{tmp} < 5 \\
        206 & \text{tmp} > 205 \\
        \text{tmp} & \text{otherwise}
    \end{cases}

.. _rescale_linear:

Linear
^^^^^^

:rescale_kind: linear
:argument 1: m
:argument 2: b

.. math::

    \text{rescaled\_data} = m * \text{data} + b

Example (0-255 from 0-1 data):

.. math::

    \text{rescaled\_data} = 255.0 * \text{data} + 0.0

Unlinear
^^^^^^^^

:rescale_kind: unlinear
:argument 1: m
:argument 2: b

.. math::

    \text{rescaled\_data} = (\text{data} - b) / m

Example (0-255 from 0-1 data):

.. math::

    \text{rescaled\_data} = (\text{data} - 0.0) / 0.00392

Lookup
^^^^^^

:rescale_kind: lookup
:argument 1: m
:argument 2: b
:argument 3: table_idx
                        
.. note::

    The ``table_idx`` argument is optional. The options for ``table_idx`` are
    hardcoded in the software. Currently, only ``0`` (default) is an option.

.. math::

    \text{rescaled\_data} = \text{available\_lookup\_tables}[table\_idx][ \operatorname{round}(m * \text{data} + b) ]

Example (0-255 from 0-1 data):

.. math::

    \text{rescaled\_data} = \text{available\_lookup\_tables}[0][ \operatorname{round}(229.83 * \text{data} + 2.2983) ]

Brightness Temperature (Celsius)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:rescale_kind: btemp_c
:argument 1: threshold
:argument 2: high_max
:argument 3: high_mult
:argument 4: low_max
:argument 5: low_mult

.. math::

    \text{temp} = \text{temp} + 273.15

    \text{rescaled\_data} = 
    \begin{cases} 
        low\_max - (low\_mult * \text{temp}) & \text{temp} < threshold \\
        high\_max - (high\_mult * \text{temp}) & \text{temp}\ge threshold
     \end{cases}

Example (0-255 from brightness temperature data):

.. math::

    \text{temp} = \text{temp} + 273.15

    \text{rescaled\_data} = 
    \begin{cases} 
        418 - (1 * \text{temp}) & \text{temp} < 242.0 \\
        660 - (2 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}

Linear Brightness Temperature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:rescale_kind: btemp_lin
:argument 1: max_in
:argument 2: min_in
:argument 3: min_out
:argument 4: max_out

.. note::

    ``min_out`` is optional and defaults to 1.0. ``max_out`` is optional and
    defaults to 255.0

.. math::

    \text{old\_range} = max\_in - min\_in

    \text{new\_range} = max\_out - min\_out

    \text{rescaled\_data} = \text{temp} * -(new\_range / old\_range) + new\_range + min\_out

Example (0-255 from brightness temperature data):

.. math::

    \text{old\_range} = 330 - 260

    \text{new\_range} = 255 - 0

    \text{rescaled\_data} = \text{temp} * -(new\_range / old\_range) + new\_range + 0

Land Surface Temperature
^^^^^^^^^^^^^^^^^^^^^^^^

:rescale_kind: lst
:argument 1: min_before
:argument 2: max_before
:argument 3: min_after
:argument 4: max_after

.. note::

    Values outside of ``min_after`` and ``max_after`` are replaced with fill
    values.

.. math::

    \text{old\_range} = max\_in - min\_in

    \text{new\_range} = max\_out - min\_out

    \text{rescaled\_data} = \text{temp} * -(new\_range / old\_range) + new\_range + min\_out

Example (0-255 from temperature data):

.. math::

    \text{old\_range} = 330 - 260

    \text{new\_range} = 255 - 0

    \text{rescaled\_data} = \text{temp} * -(new\_range / old\_range) + new\_range + 0

NDVI
^^^^

:rescale_kind: ndvi
:argument 1: low_section_multiplier
:argument 2: high_section_multiplier
:argument 3: high_section_offset
:argument 4: min_before
:argument 5: max_before
:argument 6: min_after
:argument 7: max_after

.. note::

    Input data is clipped to ``min_before`` and ``max_before``

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        (1 - \operatorname{abs}(\text{data})) * low\_section\_multiplier & \text{data} < 0 \\
        \text{data} * high\_section\_multiplier + high\_section\_offset & \text{data}\ge 0
     \end{cases}

Example (0-255 from NDVI data):

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        (1 - \operatorname{abs}(\text{data})) * 49.0 & \text{data} < 0 \\
        \text{data} * 200.0 + 50.0 & \text{data}\ge 0
     \end{cases}


Passive
^^^^^^^

:rescale_kind: raw

A passive function to tell the rescaler "don't do anything".

