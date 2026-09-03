"""Consistency checks for the documentation configuration.

One source tree builds both the Polar2Grid and the Geo2Grid site, and which pages belong
to which project is expressed by hand in ``conf.py``. These checks run on ``config-inited``
and fail the build when those hand-maintained lists drift away from the files on disk.

Sphinx already errors on a page that references a missing image, so the half of
:func:`check_example_images_used` that earns its keep is the other direction: entries that
no built page uses. The example image list carried 29 such leftovers before it was split
per project.
"""

import fnmatch
import glob
import os
import re
from pathlib import Path

from sphinx.errors import ConfigError

#: Captures the file name from a ``_static/example_images/<name>`` reference.
_EXAMPLE_IMAGE_RE = re.compile(r"_static/example_images/([A-Za-z0-9_.\-]+)")

#: Characters that make an ``exclude_patterns`` entry a glob rather than a literal path.
_GLOB_CHARS = "*?["


def check_excluded_pages_exist(app, config):
    """Fail if a literal ``exclude_patterns`` entry names a file that does not exist.

    Both projects' lists are checked, not just the one being built, so a page that is
    renamed or removed is caught by whichever site builds first.
    """
    srcdir = Path(app.srcdir)
    all_excludes = set(config.exclude_patterns) | set(config.geo2grid_excludes) | set(config.polar2grid_excludes)
    missing = sorted(
        pattern
        for pattern in all_excludes
        if not any(glob_char in pattern for glob_char in _GLOB_CHARS) and not (srcdir / pattern).exists()
    )
    if missing:
        raise ConfigError("'exclude_patterns' names files that do not exist: " + ", ".join(missing))


def check_example_images_used(app, config):
    """Fail if this project's example image list and the pages being built disagree."""
    referenced = _referenced_example_images(Path(app.srcdir), config.exclude_patterns)
    listed = {os.path.basename(image_url) for image_url in config.example_images}
    if unused := sorted(listed - referenced):
        raise ConfigError("example image list has entries no built page uses: " + ", ".join(unused))
    if unlisted := sorted(referenced - listed):
        raise ConfigError("example image list is missing images used by pages: " + ", ".join(unlisted))


def _referenced_example_images(srcdir, exclude_patterns):
    """Collect the example image file names referenced by the pages this build includes."""
    referenced = set()
    for rel_path in glob.glob("**/*.rst", root_dir=srcdir, recursive=True):
        if any(fnmatch.fnmatch(rel_path, pattern) for pattern in exclude_patterns):
            continue
        with open(srcdir / rel_path) as rst_file:
            referenced.update(_EXAMPLE_IMAGE_RE.findall(rst_file.read()))
    return referenced


def setup(app):
    """Declare the per-project page lists and connect the checks."""
    # Declares the `example_images` configuration value that check_example_images_used
    # reads. Its downloader deliberately runs at a later priority than these checks.
    app.setup_extension("_ext.example_images")
    app.add_config_value("polar2grid_excludes", [], "env")
    app.add_config_value("geo2grid_excludes", [], "env")
    app.connect("config-inited", check_excluded_pages_exist)
    app.connect("config-inited", check_example_images_used)
    return {"version": "1.0.0", "parallel_read_safe": True, "parallel_write_safe": True}
