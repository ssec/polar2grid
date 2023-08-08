Readers
=======

Readers are the first component used in |project| processing. Their main
responsibility is to extract input satellite imager data and the associated
metadata from user provided input files.
The data that readers distribute to other |project| components are called
"products" ("datasets" in SatPy terminology).

The number and type of products that can be created is dependent upon
the input datasets that are provided. Composites, such as RGBs, require a
specific set of band combinations to be present. All products that
can be created for a given input dataset can be determined by
using the  ``--list-products`` option.

.. toctree-filt::
    :maxdepth: 1

    :polar2grid:viirs_sdr
    :polar2grid:viirs_l1b
    :polar2grid:modis_l1b
    :polar2grid:avhrr
    :polar2grid:amsr2_l1b
    :polar2grid:nucaps
    :polar2grid:mirs
    :polar2grid:acspo
    :polar2grid:clavrx
    :polar2grid:viirs_edr_active_fires
    :polar2grid:viirs_edr
    :polar2grid:mersi2_l1b
    :geo2grid:abi_l1b
    :geo2grid:abi_l2_nc
    :geo2grid:agri_fy4a_l1
    :geo2grid:agri_fy4b_l1
    :geo2grid:ahi_hsd
    :geo2grid:ahi_hrit
    :geo2grid:ami_l1b
    :geo2grid:glm_l2
