---
name: build-docs
description: Build, check, and edit the Polar2Grid / Geo2Grid Sphinx documentation. Use when asked to build the docs, fix a Sphinx warning or CI docs failure, add or move an .rst page, or work out why a page appears in one project's site but not the other.
---

# Building and Editing the Documentation

One Sphinx source tree in `doc/source/` builds **two** websites. Nearly every documentation
mistake in this repository comes from forgetting that.

## Build

```bash
cd doc
make clean && make html                                        # Polar2Grid
make clean && make html POLAR2GRID_DOC=geo                     # Geo2Grid
```

Output lands in `doc/build/html`. CI (`.github/workflows/ci.yaml`) builds both with
`SPHINXOPTS="-W --keep-going"`, so **any warning is a failure**. Reproduce CI exactly with:

```bash
cd doc && make clean && make html SPHINXOPTS="-W --keep-going"
cd doc && make clean && make html POLAR2GRID_DOC=geo SPHINXOPTS="-W --keep-going"
```

The root `Makefile` holds documentation targets only (its packaging targets were deleted):
`build_doc_html` and `build_doc_html_geo` wrap the `doc/` build, and `update_doc` /
`update_doc_geo` build and then upload a tarball of `doc/build/html` to the SSEC web server
(`webaccess.ssec.wisc.edu`). A bare `make` runs `build_doc_html`.

Requirements: Sphinx >= 8.2.0 and a **forked** sphinx-argparse
(`git+https://github.com/djhoese/sphinx-argparse.git@bugfix-section-nums`, see
`continuous_integration/environment.yaml`). The stock conda package is deliberately not used.

## The project switch

`doc/source/conf.py:40`:

```python
is_geo2grid = "geo" in os.getenv("POLAR2GRID_DOC", "polar").lower()
```

`conf.py` also exports `USE_POLAR2GRID_DEFAULTS` from that flag, so the `argparse` directives
render each project's real CLI defaults.

Three mechanisms select content:

1. **Substitutions** (`rst_epilog`, `conf.py:151` and `conf.py:235`). Never hardcode a project
   name or script name in a shared page. Available: `|project|`, `|script|` (`polar2grid.sh` /
   `geo2grid.sh`), `|script_literal|`, `|project_env|` (`$POLAR2GRID_HOME` / `$GEO2GRID_HOME`),
   `|cspp_abbr|`, `|cspp_title|`, plus `|ssec|`, `|cspp|`, `|viirs|`.
2. **`toctree-filt`** (`doc/source/_ext/toctree_filter.py`). Prefix entries with `:polar2grid:` or
   `:geo2grid:`; `toc_filter_exclude` (`conf.py:252`) drops the other project's. It also accepts
   `:excludebuilder: latex`. A page shared by both projects gets no prefix, or is listed once per
   prefix.
3. **`exclude_patterns`** (`conf.py:266`). A hand-maintained per-project list of files dropped
   from the build entirely, held in the `geo2grid_excludes` and `polar2grid_excludes` values.
   Inline conditionals use `.. ifconfig:: is_geo2grid`.

## Adding a page

1. Write `doc/source/<area>/<name>.rst` using the substitutions, not literal project names.
2. Add it to the nearest `toctree-filt` with the correct prefix.
3. Add it to the **other** project's `exclude_patterns` list in `conf.py` if it is
   project-specific.

Skipping step 3 is the most common CI break. The error reads:

```
WARNING: document isn't included in any toctree
```

That means the file is present in a build where nothing references it — add it to that project's
`exclude_patterns`.

The reverse mistake is caught eagerly: `check_excluded_pages_exist()` in
`doc/source/_ext/config_checks.py` validates **both** projects' lists on `config-inited` and
raises `ConfigError` before the build starts if either names a file that does not exist. So
deleting or renaming a page means updating the list in the same commit.

## Generated versus hand-maintained

Generated at build time, gitignored, **do not edit**:

- `doc/source/grids_list.rst` — built from `polar2grid/grids/grids.yaml` by
  `doc/source/_ext/grids_list.py`. A new built-in grid also needs an entry in that module's
  `GRID_TITLES` dict, or it is silently omitted.
- `doc/source/dev_guide/api/` — `sphinx.ext.apidoc` output (`apidoc_modules` in `conf.py`).
- `doc/source/_static/example_images/` — images downloaded from `bin.ssec.wisc.edu` at build time
  by `doc/source/_ext/example_images.py`. A new documentation image means adding a URL to
  `_POLAR2GRID_IMAGES` or `_GEO2GRID_IMAGES` near the top of `conf.py`; `check_example_images_used()`
  in `_ext/config_checks.py` fails the build if a listed image is unused or a used one is unlisted.

Generated from Python at build time (edit the Python, not the `.rst`): reader and writer pages use
`.. automodule::` for the module docstring and the `sphinxarg.ext` `.. argparse::` directive for
the CLI reference. Changing a reader's docstring or its `add_reader_argument_groups` changes the
rendered page.

Looks generated but is **not**: `doc/source/summary_table.rst`,
`summary_table_geo2grid_readers.rst`, and `summary_table_geo2grid_writers.rst` are hand-maintained
and committed. There is no generator for them (`generate_summary_table.py` was deleted — it had
diverged by several releases and overwrote `summary_table.rst` in place). Edit the
`.rst` files directly.

## Known stale spots

- Some readers listed in `_supported_readers()` have no documentation page at all
  (`modis_l2`, `omps_edr`, `virr_l1b`), as does the `cf` writer.
- `doc/source/dev_guide/adding_readers.rst` has two empty `TODO` sections and points at
  `polar2grid/glue.py` for the supported-reader list; it is `_supported_readers()` in
  `polar2grid/_glue_argparser.py`.

## Other notes

- Repository images are Git LFS (`.gitattributes`); CI checks out with `lfs: true`.
- `conf.py`'s `version` / `release` are the **bundle** versions (Polar2Grid `3.2`, Geo2Grid `1.3`),
  tracking `NEWS.rst` / `NEWS_GEO2GRID.rst`. They are meant to differ from the `polar2grid` package
  version in `pyproject.toml` — do not "sync" them.
- `doc/source/_ext/doi_role.py` provides a `:doi:` role.
- PDF output is built with `make latexpdf`; `latex_documents`, `latex_logo`, and
  `latex_appendices` are also project-conditional in `conf.py`.
