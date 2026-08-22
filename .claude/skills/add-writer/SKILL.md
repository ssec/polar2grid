---
name: add-writer
description: Add a new writer to Polar2Grid or Geo2Grid — the wrapper module, default output filenames, the CLI registration, and the documentation page. Use when asked to add, wrap, or expose a Satpy writer in P2G/G2G, or when a writer exists in Satpy but is not selectable with the -w flag.
---

# Adding a Writer

Read `AGENTS.md` first for the writer contract and the P2G/G2G split. There is no prose dev-guide
page for writers — this file and the existing modules are the reference.

## 1. Decide whether a Satpy writer already fits

Most Polar2Grid writers wrap a Satpy writer unchanged and only add CLI arguments and filename
defaults (`geotiff.py`, `awips_tiled.py`, `cf.py`). Write a new Satpy `Writer` subclass only when
the output format does not exist in Satpy at all (`hdf5.py`, `binary.py`).

If a new format would be broadly useful, it belongs in Satpy first.

## 2. Create `polar2grid/writers/<satpy_writer_name>.py`

The filename must equal the Satpy writer name — that is the discovery mechanism
(`polar2grid/utils/dynamic_imports.py`).

Required pieces:

- The SSEC GPLv3 header block copied from any existing module.
- A module docstring describing the output format for users; Sphinx `automodule`s it.
- `DEFAULT_OUTPUT_FILENAMES` — a two-level dict:

  ```python
  DEFAULT_OUTPUT_FILENAMES = {
      "polar2grid": {
          None: "{platform_name!l}_{sensor!l}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.ext",
      },
      "geo2grid": {
          None: "{platform_name!u}_{sensor!u}_{p2g_name}_{start_time:%Y%m%d_%H%M%S}_{area.area_id}.ext",
      },
  }
  ```

  Both project keys must exist (a contract test asserts it). The inner keys are reader names, with
  `None` as the fallback; add a reader-specific entry only when that reader needs a different
  pattern (see `geotiff.py`, which special-cases `abi_l1b` and `clavrx`). Use `{p2g_name}`, not
  `{name}` — the Polar2Grid name is stamped onto each DataArray before saving.

- `def add_writer_argument_groups(parser, group=None)`. These arguments are passed straight into
  `scn.save_datasets(**wargs)`, so their `dest` must match the Satpy writer's keyword arguments.
  Give the group a `title` like `"<Format> Writer"`. Use
  `type=convert_p2g_pattern_to_satpy` (from `polar2grid.utils.legacy_compat`) on
  `--output-filename` so legacy Polar2Grid filename tokens keep working. Hide options users should
  not touch with `help=argparse.SUPPRESS`.

`polar2grid/core/dtype.py` has `NUMPY_DTYPE_STRS`, `str_to_dtype`, and `int_or_float` for common
argument types; `polar2grid/core/script_utils.py` has `NumpyDtypeList`.

## 3. Add a Satpy writer class and YAML (only if the format is new)

Put the `Writer` / `ImageWriter` subclass in the same module and register it with
`polar2grid/etc/writers/<name>.yaml`:

```yaml
writer:
  name: <name>
  writer: !!python/name:polar2grid.writers.<module>.<Class>
```

See `HDF5Writer` in `polar2grid/writers/hdf5.py` + `etc/writers/hdf5.yaml`, and
`FlatBinaryWriter` in `polar2grid/writers/binary.py` + `etc/writers/binary.yaml`. A YAML file can also extend a Satpy
writer with Polar2Grid-specific settings without a new class — `etc/writers/awips_tiled.yaml`
points at Satpy's `AWIPSTiledWriter` but supplies its own `templates:` blocks.

## 4. Register the writer for `--help`

Add the name to the correct list in `_supported_writers()` (`polar2grid/_glue_argparser.py`).
Add a legacy short name to `WRITER_ALIASES` in the same file if one is needed.

## 5. Add the documentation page

`doc/source/writers/<name>.rst`, following `doc/source/writers/geotiff.rst`:

```rst
<Name> Writer
=============

.. automodule:: polar2grid.writers.<module>
    :noindex:

Command Line Arguments
----------------------

.. argparse::
    :module: polar2grid.writers.<module>
    :func: add_writer_argument_groups
    :prog: polar2grid.sh -r <reader> -w <name>
    :passparser:
```

Then:

- `doc/source/writers/index.rst` — add it to the `toctree-filt` with the right
  `:polar2grid:` / `:geo2grid:` prefix. For a writer both projects ship, either drop the prefix
  (unprefixed entries are always included) or list it once per prefix — the repo does the latter
  for `geotiff`.
- `doc/source/conf.py` — add `writers/<name>.rst` to the **opposite** project's
  `exclude_patterns`, but **only if the writer is project-specific**. A dual-project page must be
  in neither exclude list. Getting this wrong fails CI's `-W` build.
- `doc/source/summary_table.rst` and/or `summary_table_geo2grid_writers.rst`.
- `NEWS.rst` and/or `NEWS_GEO2GRID.rst`.

## Verify

```bash
pytest polar2grid/tests/test_writers polar2grid/tests/test_configs.py
pytest polar2grid/tests
cd doc && make clean && make html SPHINXOPTS="-W --keep-going"
cd doc && make clean && make html POLAR2GRID_DOC=geo SPHINXOPTS="-W --keep-going"
pre-commit run --files polar2grid/writers/<name>.py doc/source/writers/<name>.rst
```

`tests/test_writers/test_base.py` globs every writer module and asserts the
`DEFAULT_OUTPUT_FILENAMES` and `add_writer_argument_groups` contract.
`polar2grid/tests/test_writers/test_binary.py` and `test_hdf5.py` are the models for testing a
writer end-to-end through `polar2grid.glue.main`.
