ABI L1B Reader
==============

.. automodule:: polar2grid.readers.abi_l1b

Command Line Usage
------------------

.. argparse::
    :module: polar2grid.readers.abi_l1b
    :func: add_reader_argument_groups
    :prog: geo2grid.sh -r abi_l1b -w <writer>
    :passparser:

Examples:

.. code-block:: bash

    geo2grid.sh -r abi_l1b -h 

    geo2grid.sh -r abi_l1b -w geotiff --list-products -f /goes16/abi

    geo2grid.sh -r abi_l1b -w geotiff --num-workers 8 -f /data/goes16/abi

    geo2grid.sh -r abi_l1b -w geotiff -p C02 C03 C04 C05 C06 true_color -f OR_ABI-L1b-RadC*.nc

    geo2grid.sh -r abi_l1b -w geotiff --ll-bbox -95.0 40.0 -85.0 50.0 -f OR_ABI-L1b-RadC*.nc

    geo2grid.sh -r abi_l1b -w geotiff -p airmass dust --num-workers 4 --grid-configs=/home/g2g/my_grid.conf -g madison --method nearest -f /data/goes17/abi/

.. only:: html

    Product Explanation
    -------------------

    True Color
    ^^^^^^^^^^

    The ABI L1b "true_color" composite produced by Geo2Grid provides a view
    of the Earth as the human eye would see it; or as close as we can come
    to with satellite data and the channels we have available. This means
    things like trees and grass are green, water is blue, deserts are
    red/brown, and clouds are white. The True Color
    image is an :ref:`RGB (Red, Green, Blue) image <explain_rgb_composite>`
    consisting of the ABI C02 reflectance channel, a
    pseudo-green reflectance channel, and the ABI C01 reflectance channel. Each
    channel goes through a series of modifications to produce the final high
    quality image output by Geo2Grid.

    The pseudo-green channel is a simple combination of 46.5% of C01, 46.5% of
    C02, and 7% of C03. While it is impossible to completely reproduce what a
    dedicated "green" channel on the ABI instrument would see, this method
    provides a good approximation while also limiting the computational
    requirements to produce it.

    All bands involved in the true color composite have the
    :ref:`sunz_correction` and
    :ref:`Rayleigh Scattering Correction <psp_rayleigh_correction>` applied,
    except for C03 in the pseudo-green band where rayleigh correction is not
    applied due to the minimal effect it would have at that wavelength.

    To improve the general spatial quality of the image, a
    :ref:`self_ratio_sharpening` is also applied. Lastly, a
    :ref:`Non-linear enhancement <nonlinear_true_color_scaling>` is applied.

    Night Microphysics
    ^^^^^^^^^^^^^^^^^^

    The Cooperative Institute for Research in the Atmosphere (CIRA) hosts
    various Quick Guides for common GOES-R ABI RGB recipes. Kevin Fuell of
    NASA SPoRT has put together a guide on the Night Microphysics RGB image.
    You can access the PDF
    `here <http://rammb.cira.colostate.edu/training/visit/quick_guides/QuickGuide_GOESR_NtMicroRGB_Final_20191206.pdf>`_.

    C01 through C06
    ^^^^^^^^^^^^^^^

    The Channel 1 through Channel 6 products are all reflectance channels
    on the ABI instrument. Besides the basic calibration necessary to
    convert the radiance values to reflectances, the data is passed through
    a square root function before being written to a grayscale image. The
    square root operation has the effect of brightening dark regions of the
    image.

    For a more detailed explanation of these bands on the instrument, see the
    `ABI Bands Quick Information Guides <https://www.goes-r.gov/mission/ABI-bands-quick-info.html>`_.

    C07 and C11 through C16
    ^^^^^^^^^^^^^^^^^^^^^^^

    These channels are all brightness temperature (infrared/IR) channels. To
    produce a grayscale image with dark land and white clouds, the data is
    inverted and scaled linearly in two segments. The first segment is from
    163K to 242K, the second 242K to 330K. This is a common scaling used by
    the National Weather Service (NWS) for their AWIPS visualization clients.

    For a more detailed explanation of these bands on the instrument, see the
    `ABI Bands Quick Information Guides <https://www.goes-r.gov/mission/ABI-bands-quick-info.html>`_.

    C08 through C10
    ^^^^^^^^^^^^^^^

    These channels are also brightness temperature (infrared/IR) channels,
    but are scaled differently than those above. These are scaled linearly
    between 180K and 280K and then inverted. The inversion has the same
    effect of making land dark and clouds white.

    For a more detailed explanation of these bands on the instrument, see the
    `ABI Bands Quick Information Guides <https://www.goes-r.gov/mission/ABI-bands-quick-info.html>`_.



