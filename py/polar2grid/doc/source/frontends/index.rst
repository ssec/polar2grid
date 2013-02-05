Frontends
=========

Frontends are the input readers of polar2grid. Their main responsibility is
to convert input satellite imager data into binary files. By using frontends,
polar2grid can easily read data from multiple sources regardless of format.
Besides converting the imager data, frontends may also create additional
bands that weren't provided in the incoming formats, called
:term:`pseudobands`. Psuedoband creation is only meant to be used if it
requires simple and quick calculations to create. More complex calculations
should be done in a separate piece of software and provided to polar2grid
through another frontend. Frontends may also scale data before providing it to
other polar2grid components, this is known as :term:`prescaling`. See the
documentation for specific frontends for examples of pseudobands and
prescaling.

Below is a list of currently available frontends for polar2grid.

.. toctree::
    :maxdepth: 1

    viirs

