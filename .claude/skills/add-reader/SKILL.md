---
name: add-reader
description: Add a new reader to Polar2Grid or Geo2Grid — the wrapper module, the CLI registration, the config, and the documentation pages. Use when asked to add, wrap, or expose a Satpy reader in P2G/G2G, or when a reader exists in Satpy but is not selectable with the -r flag.
---

# Adding a Reader

This file is the reader contract — `AGENTS.md` carries only the concepts (discovery by module
name, the P2G/G2G split, `p2g_name` aliasing) and points here for the field-by-field detail. The
prose version of this checklist is `doc/source/dev_guide/adding_readers.rst`, which covers the same
ground for human contributors.

Work through the steps in order. Steps 1-3, 5, and 6 are always required, and 7 whenever the
reader belongs to only one project; the rest depend on the reader.

## 1. Confirm the Satpy reader exists

```bash
python -c "from satpy.readers.core.config import available_readers; print([r for r in available_readers() if 'NAME' in r])"
```

If it does not exist, it belongs in Satpy first — see
https://satpy.readthedocs.io/en/latest/dev_guide/custom_reader.html. Only keep a reader out of
Satpy if it would be a maintenance burden there or is of no use to general Satpy users.

Note the exact Satpy reader name. Everything below uses it verbatim.

## 2. Create `polar2grid/readers/<satpy_reader_name>.py`

The filename **must** equal the Satpy reader name — that is the whole discovery mechanism
(`polar2grid/utils/dynamic_imports.py`).

Copy the shape of an existing reader: `omps_edr.py` for a simple polar reader, `abi_l1b.py` for a
geostationary one, `viirs_sdr.py` when you need product-group flags or resolution-qualified
aliases. Copy the GPLv3 header block from whichever you start from. Note that `omps_edr.py` has no
documentation page, so use `viirs_sdr.py` or `abi_l1b.py` as the model for the module docstring.

The usual imports:

```python
from __future__ import annotations

from argparse import ArgumentParser, _ArgumentGroup
from typing import Optional

from satpy import DataQuery, Scene

from ._base import ReaderProxyBase
from ..core.script_utils import ExtendConstAction  # only if you need product-group flags
```

### Required

* The SSEC GPLv3 header block copied from any existing module.
* A module docstring containing a table of the products this reader supports. Sphinx `automodule`s
  it into the user documentation, so **write it for users, not developers**.
* `class ReaderProxy(ReaderProxyBase)` — the class must be named exactly `ReaderProxy`.
* `def add_reader_argument_groups(parser, group=None)` returning `(group, None)`. `group` is an
  `argparse._ArgumentGroup`; when `None` the function creates one with
  `parser.add_argument_group(title="<Name> Reader")`. Arguments in the first group become
  `Scene(reader_kwargs=...)`. The second element is for `Scene.load()` keyword arguments and is
  currently always `None`.

`polar2grid/tests/test_readers/test_base.py` globs every module in the directory and asserts the
`ReaderProxy` class and the `add_reader_argument_groups` function, so getting either wrong fails
the suite without you writing a test.

### `ReaderProxy` members

`ReaderProxyBase` is constructed as `ReaderProxy(scn: Scene, user_products: list[str])`. Override:

| Member | Returns | Purpose |
|---|---|---|
| `is_polar2grid_reader` / `is_geo2grid_reader` | `bool` class attributes, both `False` by default | Which project(s) this reader belongs to. Informational only — nothing derives the `-r` help list from them, so set the flag *and* edit the list in step 4. |
| `get_default_products()` | `list[str]` of Polar2Grid names | Loaded when the user gives no `-p`. Names not present in the files are dropped automatically. |
| `get_all_products()` | `list[str]` of Polar2Grid names | Everything this reader could produce. Used to separate "guaranteed" products from raw Satpy ones in `--list-products`. |
| `_aliases` (property) | `dict[str, DataQuery \| str]` | Polar2Grid name → Satpy name or `DataQuery`. |

`ReaderProxyBase` returns `[]` / `[]` / `{}` for these, so a skipped override fails silently — the
reader loads but offers no default products and no aliases, rather than raising.

By convention each of these just returns a module-level constant — `DEFAULT_PRODUCTS`,
`P2G_PRODUCTS`, and `PRODUCT_ALIASES` respectively (geo readers often build `P2G_PRODUCTS` from
`READER_PRODUCTS + COMPOSITE_PRODUCTS`). **Nothing reads those constants automatically**; they exist
so the lists are easy to find and compose. The methods are what the framework calls. Override
`__init__` only if the aliases depend on user arguments — `viirs_sdr.py` does this for
`--dnb-saturation-correction`.

### Optional module-level names (read directly by the framework)

* `PREFERRED_CHUNK_SIZE: int` — the preferred square dask chunk edge in **pixels**. `glue.py`
  converts it to `pixels * pixels * 8 bytes` and sets dask's `array.chunk-size` for the whole run,
  unless `DASK_ARRAY__CHUNK_SIZE` is set. Defaults to 1024 when absent.
* `FILTERS` — which products the day/night filters may drop, matched against DataArray `.attrs`:

  ```python
  FILTERS = {
      "day_only": {"standard_name": ["toa_bidirectional_reflectance", "true_color"]},
      "night_only": {"standard_name": ["temperature_difference"]},
  }
  ```

  Each inner dict maps an attribute name to the values that qualify. A product matching `day_only`
  is dropped when the daytime fraction of the scene falls below `--filter-day-products` (default
  `0.1` for Polar2Grid, off for Geo2Grid); `night_only` is the mirror image. Use empty dicts if the
  reader has nothing to filter — or omit `FILTERS` entirely, which is equivalent (the lookup
defaults to `{}`). Consumed by `polar2grid/filters/_filter_scene.py`.

Custom argparse actions useful for product-group flags live in `polar2grid/core/script_utils.py`
(`ExtendAction`, `ExtendConstAction`, `BooleanFilterAction`).

## 3. Register the reader for `--help`

Add the reader name to the correct list in `_supported_readers()`
(`polar2grid/_glue_argparser.py`). This list is hardcoded and is *not* derived from the
`is_*_reader` class attributes. Without this the reader still works but is invisible in `-r` help.

If the reader needs a short legacy alias, add it to `READER_ALIASES` in the same file.

## 4. Add configuration (only if needed)

- `polar2grid/etc/enhancements/<sensor>.yaml` — scaling/colorizing for new products.
- `polar2grid/etc/resampling.yaml` — a rule keyed on `reader:` / `sensor:` / `name:` /
  `area_type:` if the defaults are wrong for this data.
- `polar2grid/etc/composites/<sensor>.yaml` — Polar2Grid-only composites.
- `polar2grid/etc/readers/<name>.yaml` — rarely needed; currently only used for `data_files:`
  auxiliary download lists.
- `polar2grid/etc/colormaps/` — new `.cmap` files referenced from enhancement YAML.
- Each writer's `DEFAULT_OUTPUT_FILENAMES` in `polar2grid/writers/*.py` — only if this reader needs
  a filename pattern different from the `None` fallback. Nothing warns you if you skip this; you
  just silently get the generic pattern.
- Sensor and platform spellings — if the reader reports names Polar2Grid renames on output, add
  them to `get_sensor_alias()` in `polar2grid/utils/legacy_compat.py` or the platform alias table
  in `polar2grid/glue.py`.

## 5. Add the documentation page

Create `doc/source/readers/<name>.rst`:

```rst
<Reader Name> Reader
====================

.. automodule:: polar2grid.readers.<module>
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.readers.<module>
    :func: add_reader_argument_groups
    :prog: polar2grid.sh -r <reader_name> -w geotiff
    :passparser:

Examples:

.. code-block:: bash

    polar2grid.sh -r <reader_name> -w geotiff -f <path to files>
```

Use `geo2grid.sh` in `:prog:` and the examples for a Geo2Grid reader. `doc/source/readers/viirs_sdr.rst`
and `doc/source/readers/abi_l1b.rst` are the fullest examples, including a "Product Explanation"
section.

## 6. Add it to the reader table of contents

`doc/source/readers/index.rst` — add the document name with the correct `:polar2grid:` or
`:geo2grid:` prefix inside the `toctree-filt` block.

If the reader serves **both** projects, either drop the prefix (unprefixed entries are always
included, see `doc/source/toctree_filter.py`) or list it once per prefix — the repo does the latter
for `geotiff` in `doc/source/writers/index.rst`. Either way skip step 7 entirely. Note
that setting both `is_polar2grid_reader` and `is_geo2grid_reader` does not by itself make a reader
dual-project in the docs — the toctree entry does.

Keep this toctree one-to-one with `_supported_readers()`: everything advertised in the `-r` help
text has a page here, and nothing else does. A reader that is deliberately unadvertised
(`clavrx`, `modis_l2`, `viirs_edr_flood`, `virr_l1b`) gets no entry; if such a reader still has
an `.rst` file, it is excluded from *both* builds via the base `exclude_patterns` list in
`conf.py` rather than a per-project one.

## 7. Exclude it from the other project's build

Single-project readers only. `doc/source/conf.py` — add `readers/<name>.rst` to the **opposite**
project's `exclude_patterns` list. Skipping this breaks CI, which builds both variants with
`-W --keep-going`; the failure reads "document isn't included in any toctree".

## 8. Summary table and changelog

- `doc/source/summary_table.rst` (Polar2Grid) or `doc/source/summary_table_geo2grid_readers.rst`
  (Geo2Grid) — add the input source and filename pattern rows, matching the columns already there.
  These tables are hand-maintained and have no generator; edit the `.rst` directly.
- `NEWS.rst` or `NEWS_GEO2GRID.rst`. A new user-visible reader always warrants an entry.

## 9. Optional extras

- `doc/source/examples/<name>_example.rst` plus its `index.rst` entry and `exclude_patterns` entry.
- A new `Examples:` row in `integration_tests/features/polar2grid.feature` or `geo2grid.feature`.

## Verify

```bash
pytest polar2grid/tests/test_readers polar2grid/tests/test_configs.py
pytest polar2grid/tests
cd doc && make clean && make html SPHINXOPTS="-W --keep-going"
cd doc && make clean && make html POLAR2GRID_DOC=geo SPHINXOPTS="-W --keep-going"
pre-commit run --files polar2grid/readers/<name>.py doc/source/readers/<name>.rst
```

`tests/test_readers/test_base.py` globs every reader module and asserts the `ReaderProxy` and
`add_reader_argument_groups` contract, so it will catch most structural mistakes.

Then exercise the CLI against real files if any are available:

```bash
python -m polar2grid.glue -r <name> -w geotiff --list-products-all -f <files>
```
