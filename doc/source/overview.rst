
.. ifconfig:: not is_geo2grid

	|project| is a set of command line tools for extracting data 
	from earth-observing satellite instrument file formats, 
	remapping it to uniform grids if needed, and writing that 
	gridded data to a new file format.  It provides an easy way 
	to create high quality projected images. |project| was 
	created by scientists and software developers at the 
	`SSEC <http://www.ssec.wisc.edu>`_. It is distributed as 
	part of the `CSPP LEO <http://cimss.ssec.wisc.edu/cspp/>`_ 
        project for processing of data received via direct broadcast 
	antennas. Although |project| was created to serve the direct
	broadcast community, it can be used on most archived data files.

.. ifconfig:: is_geo2grid


        |project| is a set of command line tools for extracting data
        from earth-observing satellite instrument file formats,
        remapping it to uniform grids if needed, and writing that
        gridded data to a new file format.  It provides an easy way
        to create high quality projected images. |project| was
        created by scientists and software developers at the
        `SSEC <http://www.ssec.wisc.edu>`_. It is distributed as
        part of the `CSPP Geo <http://cimss.ssec.wisc.edu/csppgeo/>`_
        project for processing of data received via direct broadcast
        antennas. Although |project| was created to serve the direct
        broadcast community, it can be used on most archived data files.


The features provided by |project| are accessible via bash scripts and binary
command line tools. This is meant to give scientists an easy way to use and
access features that typically involve complicated programming interfaces.
Linux terminal commands included in these instructions assume the bash shell
is used.

.. ifconfig:: not is_geo2grid

    .. note::

        A collaboration between the Polar2Grid and PyTroll team will change a
        majority of the low-level code in future versions of Polar2Grid.
        However, the bash scripts will still be available to provide the same
        functionality with which users are familiar. Polar2Grid terminology
        such as "frontend" and "backend" is now used interchangeably with the
        SatPy terminology "reader" and "writer".

.. only:: not html

    `Documentation Website <http://www.ssec.wisc.edu/software/polar2grid/>`_

`GitHub Repository <https://github.com/ssec/polar2grid>`_

.. ifconfig:: is_geo2grid

    `Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Geo%20Questions>`__

.. ifconfig:: not is_geo2grid

    `Contact Us <http://cimss.ssec.wisc.edu/contact-form/index.php?name=CSPP%20Questions>`__

`CSPP Forum <https://forums.ssec.wisc.edu/>`_
