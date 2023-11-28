"""Warnings or utilities for dealing with warnings."""
from __future__ import annotations

import contextlib
import warnings


@contextlib.contextmanager
def ignore_no_georef():
    """Wrap operations that we know will produce a rasterio geolocation warning."""
    from rasterio.errors import NotGeoreferencedWarning

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            "Dataset has no geotransform",
            NotGeoreferencedWarning,
        )
        yield


@contextlib.contextmanager
def ignore_pyproj_proj_warnings():
    """Wrap operations that we know will produce a PROJ.4 precision warning.

    Only to be used internally to Pyresample when we have no other choice but
    to use PROJ.4 strings/dicts. For example, serialization to YAML or other
    human-readable formats or testing the methods that produce the PROJ.4
    versions of the CRS.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            "You will likely lose important projection information",
            UserWarning,
        )
        yield
