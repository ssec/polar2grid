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
`8-bit rescaling configuration <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale.8bit.conf>`_
and
`16-bit rescaling configuration <https://github.com/davidh-ssec/polar2grid/blob/master/py/polar2grid_core/polar2grid/core/rescale_configs/rescale.16bit.conf>`_
for more details.

.. _rescale_square_root_enhancement:

Square Root Enhancement
^^^^^^^^^^^^^^^^^^^^^^^

Common Unsigned 8-bit Parameters:

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * 100.0} * 25.5)

Common Unsigned 16-bit Parameters:

.. math:: \text{rescaled\_data} = \operatorname{round}(\sqrt{\text{data} * 100.0} * 6553.5)

.. _rescale_btemp:

Brightness Temperature
^^^^^^^^^^^^^^^^^^^^^^

Common Unsigned 8-bit Parameters:

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        418 - (1 * \text{temp}) & \text{temp} < 242.0 \\
        660 - (2 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}

Common Unsigned 16-bit Parameters:

.. math::

    \text{rescaled\_data} = 
    \begin{cases} 
        107789.66 - (259.23 * \text{temp}) & \text{temp} < 242.0 \\
        168960.00 - (512.00 * \text{temp}) & \text{temp}\ge 242.0
     \end{cases}

.. _rescale_linear:

Linear
^^^^^^

Common Unsigned 8-bit Parameters:

.. math::

    \text{rescaled\_data} = 255.0 * \text{data} + 0.0
        
Common Unsigned 16-bit Parameters:

.. math::

    \text{rescaled\_data} = 65535.0 * \text{data} + 0.0
        

Unlinear
^^^^^^^^

TODO

Passive
^^^^^^^

A passive function to tell the rescaler "don't do anything".

Miscellaneous Functions
-----------------------

The below functions are not intended for rescaling use, but are more likely to
be used by polar2grid frontends or backends to clip/filter data to a specific
range.

Histogram Equalization
^^^^^^^^^^^^^^^^^^^^^^

Local Histogram Equalization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Unsigned Byte Filter
^^^^^^^^^^^^^^^^^^^^

Unsigned 16-bit Integer Filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

