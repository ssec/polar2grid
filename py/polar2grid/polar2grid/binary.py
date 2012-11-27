"""Simple backend to just passively 'produce' the binary files that are
provided.

FUTURE: Provide rescaled binaries.

"""

from polar2grid.core import roles
from polar2grid.core.constants import GRIDS_ANY

class Backend(roles.BackendRole):
    def __init__(self):
        pass

    def can_handle_inputs(self, sat, instrument, kind, band, data_kind):
        return GRIDS_ANY

    def create_product(self, sat, instrument,
            kind, band, data_kind, data):
        pass

