Rescaling
=========

Rescaling is a polar2grid component shared by most backends that rescales
gridded image data in the common case.  The underlying code also holds
scaling functions that may be useful to frontends or glue scripts to equalize
or scale data for other purposes.  The following sections describe each scaling function in the rescaling code.

Backend Scaling Functions
-------------------------

The functions described below are intended for use by polar2grid backends.
These functions ignore any fill/invalid values in the data.  Common values
for the default scaling configurations are listed.  See the
`configuration files <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/>`_
in the source repository for exact values used. The function definitions
below name the positional arguments in the configuration file.

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

Passive
^^^^^^^

A passive function to tell the rescaler "don't do anything".

