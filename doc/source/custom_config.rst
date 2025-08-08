:orphan:

Custom Configuration Directories
================================

|project| allows users to customize various parts of its configuration. This
allows for changing existing default behavior all the way to adding completely
new functionality. The configuration mechanism used by |project| is borrowed
from the Satpy project. It controls every component like readers, writers,
composites, resampling, and enhancements that can be applied and when they are
applied. The below sections will describe how custom configuration can be
provided to |project| and how different parts can be customized.

Configuration Directories
-------------------------

Satpy and therefore |project| use a series of directories to configure
themselves and the components they use. Most files are in the YAML text
format. Satpy comes with its own builtin directory and allows users to
specify additional external directories to replace or supplement the builtin
configuration. Each user directory is the "root" directory for YAML files and
sub-component directories with YAML files. These directories will typically
look like:

.. code-block:: text

    /path/to/my_custom_dir/
        readers/
            my_custom_reader.yaml
        writers/
            my_custom_writer.yaml
        enhancements/
        composites/

|project| takes advantage of this Satpy feature and provides its own directory
in the ``etc/polar2grid/`` directory in |project_env|. The configuration in
this directory is required for |project| to work properly and work as expected.

.. warning::

    Any changes to |project|'s configuration directory could lead to unexpected
    output or even make it impossible for |project| to run properly. Care
    should be taken when customizing files in ``etc/polar2grid/``.

Users of |project| can create your own configuration directories and specify them
to |project| (see below). This makes sure that your |project| installation stays
in its original state.

Additional Directories
----------------------

As mentioned above, users can create their own configuration directories and
tell |project| to use them. This allows for |project| to stay in its original
state while allowing full customization of the underlying Satpy functionality.
To tell |project| about your directories add
``--extra-config-path /path/to/root_config_dir`` to your |script_literal| call.
You can specify this flag multiple times to add additional directories.
This directory must be the root directory of configuration. So it should have
sub-directories for the components you are customizing (ex. 'readers',
'composites'). You only need to have the configuration files that you are
customizing.

Directories are loaded in reverse order that they are specified, but this means
that the earlier directories have priority. For example,

.. code-block:: bash

    polar2grid.sh ... --extra-config-path /path/to/root1 --extra-config-path /path/to/root2 ...

This call will result in Satpy loading Satpy's builtin configuration first, it
will then load and apply |project|'s builtin configuration on top of this, then
the "root2" directory will be loaded, and lastly "root1". Every time
configuration is loaded it overwrites and adds on to any configuration that was
already loaded.

Satpy Configuration
-------------------

Satpy allows for :doc:`additional configuration <satpy:config>` via
environment variables. In most cases this is not recommended when working with
|project| as most of these values are already customized to keep Satpy's
searches for information internal to the |project| installation rather than
the rest of your system. Change these environment variables at your own risk.

Custom Composites
-----------------

Satpy provides information on creating your own custom composites
`here <https://satpy.readthedocs.io/en/stable/composites.html#creating-composite-configuration-files>`_.
This documentation includes information on some of the builtin Python
compositor classes provided by the library that can be combined to make
complex products.

Resampling Configuration
------------------------

|project| uses a special ``resampling.yaml`` configuration file not used by
Satpy at the time of writing. This is because the implementation has not been
finalized for Satpy and currently only lives in |project|. It still follows
the same configuration rules described above and is a "decision tree" based
file like enhancements (see below).

Decision Tree Configuration
---------------------------

Most configuration files used by Satpy are relatively straight forward; what
you see is what you get. You give something a name and define various
properties. The interconnection between the configuration sections in the YAML
is relatively explicit or doesn't exist at all. This is not true for
enhancement and resampling configuration which describe a series of "decisions"
that can be taken.

In decision tree configuration files you specify a "decision" (a.k.a "rule")
that Satpy will match against when determining how to process the current data.
For example here is a section of an enhancement configuration file:

.. code-block:: yaml

    brightness_temperature_default_celsius:
      standard_name: toa_brightness_temperature
      units: celsius
      operations:
      - name: btemp_threshold
        method: !!python/name:satpy.enhancements.contrast.btemp_threshold
        kwargs:
          threshold: -31.15
          min_in: -110.15
          max_in: 56.85

The name of this section is "brightness_temperature_default_celsius". It has no
purpose other than to provide a unique and understandable summary of what the
contained configuration is used for. The first two elements are part of the
"decision" and say that if the current data has "standard_name" metadata equal
to "toa_brightness_temperature" and has "units" of "celsius" then we should use
the enhancement defined in "operations". The standard name and units are two of
many other options we can use in our rule. Others include **name**, **reader**,
**platform_name**, and **sensor**. Resampling configuration has the additional
**area_type** parameter. When |project| is processing some data it will try to
find the section of configuration that matches the most (**name** has
priority).
