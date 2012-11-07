"""Abstract Base Classes for polar2grid components
"""

from .constants import DKIND_REFLECTANCE,DKIND_RADIANCE,DKIND_BTEMP, \
        DKIND_FOG,NOT_APPLICABLE

import os
import sys
import logging
from abc import ABCMeta,abstractmethod,abstractproperty

log = logging.getLogger(__name__)

class RescalerRole(object):
    __metaclass__ = ABCMeta

    # Fill values in the input and to set in the output
    DEFAULT_FILL_IN = -999.0
    DEFAULT_FILL_OUT = -999.0

    # Dictionary mapping of data identifier to rescaling function and its
    # arguments
    config = {}

    @abstractproperty
    def default_config_dir(self):
        """Return the default search path to find a configuration file if
        the configuration file provided is not an absolute path and the
        configuration filename was not found in the current working
        directory.

        This does not work in subclasses since they will be called the
        function that 'lives' in this file.  Copying and pasting this
        function is the simplest solution until pkg_resources.
        """
        return os.path.split(os.path.realpath(__file__))[0]

    @abstractproperty
    def known_rescale_kinds(self):
        """Return a dictionary mapping data_kind constants to scaling
        function.  This will be used by the configuration file parser
        to decide what scaling function goes with each data_kind.

        The dictionary should at least have a key for each data_kind constant,
        but it may also have some common data_kind equivalents that may appear
        in a configuration file.  For instance, brightness temperatures may be
        written in the configuration file as 'btemp', 'brightness temperature',
        'btemperature', etc.  So the dictionary could have one key for each of
        these variations as well as the constant DKIND_BTEMP, all mapping to
        the same scaling function.

        A good strategy is to define the dictionary outside this
        function/property and return a pointer to that class attribute.
        This way the dictionary isn't created everytime it is accessed, but
        the property is still read only.
        """
        return {}

    # Define the dictionary once so it doesn't have to be
    # allocated/instantiated every time it's used
    _known_data_kinds = {
            'reflectance' : DKIND_REFLECTANCE,
            'radiance'    : DKIND_RADIANCE,
            'btemp'       : DKIND_BTEMP,
            'fog'         : DKIND_FOG,
            # if they copy the constants, like they should
            DKIND_REFLECTANCE : DKIND_REFLECTANCE,
            DKIND_RADIANCE    : DKIND_RADIANCE,
            DKIND_BTEMP       : DKIND_BTEMP,
            DKIND_FOG         : DKIND_FOG
            }

    @property
    def known_data_kinds(self):
        # Used in configuration reader
        return self._known_data_kinds

    def __init__(self, config=None, fill_in=None, fill_out=None):
        """Load the initial configuration file and any other information
        needed for later rescaling.
        """
        if config is not None:
            self.load_config(config)

        self.fill_in = fill_in or self.DEFAULT_FILL_IN
        self.fill_out = fill_out or self.DEFAULT_FILL_OUT

    def _create_config_id(self, sat, instrument, kind, band, data_kind):
        return "_".join([sat.lower(), instrument.lower(), kind.lower(), (band or "").lower(), data_kind.lower()])

    def load_config_str(self, config_str):
        """Just in case I want to have a config file stored as a string in
        the future.

        """
        # Get rid of trailing new lines and commas
        config_lines = [ line.strip(",\n") for line in config_str.split("\n") ]
        # Get rid of comment lines and blank lines
        config_lines = [ line for line in config_lines if line and not line.startswith("#") and not line.startswith("\n") ]
        # Check if we have any useful lines
        if not config_lines:
            log.warning("No non-comment lines were found in rescaling configuration")
            return False

        try:
            # Parse config lines
            for line in config_lines:
                parts = line.split(",")
                if len(parts) < 6:
                    log.error("Rescale config line needs at least 6 columns : '%s'" % (line))
                    raise ValueError("Rescale config line needs at least 6 columns : '%s'" % (line))

                # Verify that each identifying portion is valid
                for i in range(6):
                    assert parts[i],"Field %d can not be empty" % i
                    # polar2grid demands lowercase fields
                    parts[i] = parts[i].lower()

                # Convert band if none
                if parts[3] == '' or parts[3] == "none":
                    parts[3] = NOT_APPLICABLE
                # Make sure we know the data_kind
                if parts[4] not in self.known_data_kinds:
                    log.error("Rescaling doesn't know the data kind '%s'" % parts[4])
                    raise ValueError("Rescaling doesn't know the data kind '%s'" % parts[4])
                parts[4] = self.known_data_kinds[parts[4]]
                # Make sure we know the scale kind
                if parts[5] not in self.known_rescale_kinds:
                    log.error("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
                    raise ValueError("Rescaling doesn't know the rescaling kind '%s'" % parts[5])
                parts[5] = self.known_rescale_kinds[parts[5]]
                # TODO: Check argument lengths and maybe values per rescale kind 

                # Enter the information into the configs dict
                line_id = self._create_config_id(*parts[:5])
                config_entry = (parts[5], tuple(float(x) for x in parts[6:]))
                self.config[line_id] = config_entry
        except StandardError:
            # Clear out the bad config
            log.warning("Rescaling configuration file could be in a corrupt state")
            raise

        return True

    def load_config(self, config_filename):
        """
        Load a rescaling configuration file for later use by the `__call__`
        function.

        If the config isn't an absolute path, it checks the current directory,
        and if the config can't be found there it is assumed to be relative to
        the package structure. So entering just the filename will look in the
        default rescaling configuration location (the package root) for the
        filename provided.
        """
        if not os.path.isabs(config_filename):
            cwd_config = os.path.join(os.path.curdir, config_filename)
            if os.path.exists(cwd_config):
                config_filename = cwd_config
            else:
                config_filename = os.path.join(self.default_config_dir, config_filename)
        config = os.path.realpath(config_filename)

        log.debug("Using rescaling configuration '%s'" % (config,))

        config_file = open(config, 'r')
        config_str = config_file.read()
        return self.load_config_str(config_str)

    @abstractmethod
    def __call__(self, sat, instrument, kind, band, data_kind, data):
        raise NotImplementedError("This function has not been implemented")

class BackendRole(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def can_handle_inputs(self, sat, instrument, kind, band, data_kind):
        """Function that returns the grids that it will be able to handle
        for the data described by the arguments passed.  It returns either
        a list of grid names (that must be defined in grids.conf) or it
        returns a constant defined in `polar2grid.core.constants` for grids.
        Possible constants are:
            - GRIDS_ANY: Any gpd or proj4 grid
            - GRIDS_ANY_GPD: Any gpd grid
            - GRIDS_ANY_PROJ4: Any proj4 grid

        """
        return []

    @abstractmethod
    def create_product(self, sat, instrument, kind, band, data_kind,
            start_time=None, end_time=None, grid_name=None,
            output_filename=None):
        raise NotImplementedError("This function has not been implemented")

class FrontendRole(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def make_swaths(self, filepaths, **kwargs):
        raise NotImplementedError("This function has not been implemented")

def main():
    """Run some tests on the interfaces/roles
    """
    # TODO
    pass

if __name__ == "__main__":
    sys.exit(main())

