"""Download the example images that the documentation pages reference.

The images are large and are deliberately not stored in git. The list of URLs for the
project being built is the ``example_images`` configuration value, set by ``conf.py``;
this extension fetches whatever is not already on disk into ``_static/example_images``.

See :mod:`_ext.config_checks` for the check that keeps that list and the pages that
reference the images in agreement.
"""

import ftplib
import os
import urllib.request
from pathlib import Path
from shutil import copyfileobj

from sphinx.errors import ConfigError
from sphinx.util import logging

logger = logging.getLogger(__name__)

#: Run after the default priority, so `_ext.config_checks` gets to reject a stale image
#: list before anything is fetched for it.
DOWNLOAD_PRIORITY = 800


def download_example_images(app, config):
    """Download every example image for this project that is not already on disk."""
    image_dst = Path(app.srcdir) / "_static" / "example_images"
    image_dst.mkdir(parents=True, exist_ok=True)

    for image_url in config.example_images:
        image_pathname = image_dst / os.path.basename(image_url)
        if image_pathname.is_file():
            continue
        logger.info("Downloading example image: %s", image_url)
        if image_url.startswith(("http://", "https://")):
            _download_http(image_url, image_pathname)
        elif image_url.startswith("ftp://"):
            _download_ftp(image_url, image_pathname)
        else:
            raise ConfigError(f"Not sure how to download image: {image_url}")


def _download_http(image_url, image_pathname):
    with urllib.request.urlopen(image_url) as remote_img, open(image_pathname, "wb") as local_img:
        copyfileobj(remote_img, local_img)


def _download_ftp(image_url, image_pathname):
    parts = image_url.split("/")
    server = parts[2]
    ftp_fn = "/".join(parts[3:])
    ftp = ftplib.FTP(server, user="ftp")  # hope for anonymous
    with open(image_pathname, "wb") as out_file:
        ftp.retrbinary(f"RETR {ftp_fn}", out_file.write)


def setup(app):
    """Declare the example image list and connect the downloader."""
    app.add_config_value("example_images", (), "env")
    app.connect("config-inited", download_example_images, priority=DOWNLOAD_PRIORITY)
    return {"version": "1.0.0", "parallel_read_safe": True, "parallel_write_safe": True}
