# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

Step-by-step checklists for the recurring multi-file tasks live in `.claude/skills/`:
`add-reader`, `add-writer`, and `build-docs`. Load the relevant one — or just read its `SKILL.md`
— before starting that task. `add-reader` and `add-writer` are also the reference for the reader
and writer contracts generally, not only for adding new ones.

# Core Concepts

Polar2Grid is a high-level wrapper around the Satpy Python library. Its primary use case is as a
set of command line scripts. Targeted users are scientists or data processing technicians who may
not have a lot of programming experience beyond bash commands. Polar2Grid's main workflow is through
the `polar2grid.sh` and `geo2grid.sh` commands which wrap Satpy's reading, compositing, resampling,
and writing features. In addition to making access to this functionality simpler, Polar2Grid also
provides logical sane defaults that users are used to. When users request a higher-level of
customization beyond basic YAML configuration changes, we tend to recommend they use Satpy directly.

Similar to Satpy, Polar2Grid divides configuration between reading, resampling, and writing.

# Polar2Grid versus Geo2Grid

The `polar2grid` python package and this repository contain the code and documentation for two
sibling projects: Polar2Grid and Geo2Grid. Polar2Grid has a long history and existed long before
Satpy existed; Satpy was adopted later. Polar2Grid focuses on processing Low Earth Orbiting (LEO)
satellites, also often called "polar" satellites. Geo2Grid came later and focuses on processing
geostationary (Geo) satellite data. It was decided that having two separate projects made funding
requests and human project-management easier. As such the code, documentation, and build steps have
various conditional branches to determine what should be included or used or defaulted depending on
which project is being used/built. These projects are often abbreviated P2G and G2G.

## How the split is implemented

At runtime there is exactly one switch: the **`USE_POLAR2GRID_DEFAULTS`** environment variable
(`"1"` = Polar2Grid, `"0"` = Geo2Grid, defaulting to Polar2Grid if unset). It is read exactly once
per run by `get_p2g_defaults_env_var()` in `polar2grid/_glue_argparser.py` and then threaded through
the call stack as an explicit `is_polar2grid: bool` argument. Do not re-read the environment
variable deep in the stack; pass the boolean.

Where the boolean branches:

| Location | Difference |
|---|---|
| `_supported_readers()` / `_supported_writers()` (`_glue_argparser.py`) | different reader and writer lists for the `-r` / `-w` help text; P2G additionally offers the `binary` and `hdf5` writers |
| `add_scene_argument_groups()` (`_glue_argparser.py`) | `--filter-day-products` / `--filter-night-products` default to `0.1` (on) for P2G and `False` (off) for G2G |
| `add_resample_argument_groups()` (`_glue_argparser.py`) | P2G offers the `ewa` method and its options; G2G is `native`/`nearest` only and defaults to `native` |
| `get_default_output_filename()` (`_glue_argparser.py`) | selects the `"polar2grid"` or `"geo2grid"` half of each writer's `DEFAULT_OUTPUT_FILENAMES` |
| `_default_grid()` (`resample/_resample_scene.py`) | default target grid is `wgs84_fit` for P2G and `MAX` for G2G (when the resampler is not `native`) |
| `_print_list_products()` (`glue.py`) | the project name in `--list-products` output |

Documentation builds use a *separate* variable, `POLAR2GRID_DOC` (`doc/source/conf.py`), which in
turn sets `USE_POLAR2GRID_DEFAULTS` so the rendered CLI help matches the project being built. The
software bundle build decides from whether the bundle name contains "polar"
(`create_conda_software_bundle.sh`).

Separately, each reader's `ReaderProxy` declares which project(s) it belongs to with the
`is_polar2grid_reader` / `is_geo2grid_reader` class attributes (both default to `False` on
`ReaderProxyBase`). These are close to *informational*: `is_geo2grid_reader` is read only by
`ReaderProxyBase._binary_name` to pick a project name for log messages, and nothing reads
`is_polar2grid_reader` at all. The `--help` lists are maintained by hand instead — see Readers.

## Environment variables

| Variable | Effect |
|---|---|
| `USE_POLAR2GRID_DEFAULTS` | `1` = Polar2Grid, `0` = Geo2Grid. Default `1`. |
| `POLAR2GRID_DOC` | Documentation build only. Contains "geo" → build Geo2Grid docs. Default "polar". |
| `PROG_NAME` | Program name shown in `--help` usage (`polar2grid.sh` / `geo2grid.sh`). |
| `POLAR2GRID_HOME` / `GEO2GRID_HOME` | Software bundle root. Used to expand `$POLAR2GRID_HOME` in enhancement YAML colormap paths. Falls back to `<pkg>/../swbundle` for development installs. |
| `DASK_NUM_WORKERS` | Integer; default for `--num-workers`. |
| `DASK_ARRAY__CHUNK_SIZE` | Dask size string (ex. `128MiB`). If set, overrides the reader's `PREFERRED_CHUNK_SIZE`. |
| `P2G_ALLOW_TRACE` | Truthy enables Satpy's TRACE log level at high verbosity. |
| `P2G_EWA_LEGACY` | `1` adds the deprecated `ewa_legacy` resampler to `--method` (P2G only). |
| `SATPY_CONFIG_PATH`, `SATPY_DATA_DIR`, `PSP_*`, `GSHHS_DATA_ROOT` | Set by `swbundle/env.sh` in a deployed bundle; standard Satpy/pyspectral variables. |
| `OMP_NUM_THREADS` | Set to 2 by the bundle shell scripts. |

# Working with Satpy

Satpy is a Python library for reading, manipulating, and writing data from remote-sensing
earth-observing satellite instruments. The primary access point for these features is a
`Scene` object where data can be read/loaded (`Scene.load`) from data files, resampled to
a different grid of pixels (`Scene.resample`), and written to an on-disk file format.
Satpy uses `xarray.DataArray` objects wrapping **dask arrays**, with metadata stored in the
`.attrs` mapping. The dimensions are typically ("y", "x") but may include a "bands" dimension
representing image bands (ex. ["R", "G", "B"]).

Satpy typically deals with data that is one of:

* Swath: 2D non-uniformly spaced pixels recorded from a polar-orbiting satellite where the `y`
  dimension is along track and `x` is cross track with the scanning pattern of the instrument.
* Area: 2D uniformly spaced grid of pixels. These are usually from a geostationary satellite
  instrument or swath data that was pre-resampled. The `y` and `x` dimension are in the units
  of the Earth projection that the data is resampled/projected to, usually meters or degrees.

Either way geolocation lives in `.attrs["area"]`, as a `SwathDefinition` (swath) or an
`AreaDefinition` (area) from the `pyresample` library.

Each product is identified by a `DataID`; a `DataQuery` is a partial specification of one (ex.
name plus resolution) used when not all the ID keys are known. Satpy's high-level components are
**readers**, **compositors** (combine bands into a new product), **modifiers** (correct a single
band), **enhancements** (scale/colorize before writing), and **writers**. Each is a Python class
plus a YAML config under `satpy/etc/`, and the YAML is what makes the component *discoverable* —
a class with no YAML entry can be called directly but `Scene.load` will never find it.

**Do not guess at Satpy internals — read them.** In rough order of preference:

1. The installed source tree:
   `python -c "import satpy, os; print(os.path.dirname(satpy.__file__))"`
2. An `AGENTS.md` at the root of a local Satpy checkout, if one exists on this machine.
3. https://satpy.readthedocs.io

This project requires `satpy>=0.58.0`; the CI and bundle environments install Satpy and pyresample
from git main, so behavior can be ahead of the latest release.

Satpy rules that Polar2Grid code must also obey:

* **Stay lazy.** Avoid `.compute()`, `.values`, `np.asarray()`, or `bool()` on data in library code.
* Prefer `np.float32`; NaN is the mask for floats, `_FillValue` for ints.
* Never hardcode a dask chunk size. Polar2Grid expresses a per-reader preference through
  `PREFERRED_CHUNK_SIZE` (see Readers).

One place Polar2Grid **differs** from Satpy's conventions: this repository runs `ruff-format`
(see `.pre-commit-config.yaml`). Satpy does not. Formatting changes here are expected.

# Repo Layout

| Path | Purpose |
|---|---|
| `polar2grid/glue.py` | The workflow driver: `main()`, `_GlueProcessor`, scene creation → load → resample → save |
| `polar2grid/_glue_argparser.py` | All top-level CLI arguments; `GlueArgumentParser` splits them into per-component buckets |
| `polar2grid/__main__.py` | `p2g_main()` / `g2g_main()` console-script entry points |
| `polar2grid/readers/` | One wrapper module per Satpy reader, plus `_base.py` (`ReaderProxyBase`) |
| `polar2grid/writers/` | One wrapper module per Satpy writer; some define their own Satpy `Writer` subclass |
| `polar2grid/resample/` | `resample_scene()` and the `ResamplerDecisionTree` |
| `polar2grid/filters/` | Day/night and grid-coverage filtering applied before resampling |
| `polar2grid/grids/` | `grids.yaml` (built-in areas), `manager.py` (legacy `.conf` grids), `config_helper.py` |
| `polar2grid/enhancements/` | P2G enhancement functions referenced from YAML (`shared.py`, `viirs.py`) |
| `polar2grid/composites/` | P2G compositor classes (`enhanced.py`) |
| `polar2grid/core/` | Logging setup, custom argparse actions, dtype helpers, legacy `GridDefinition` |
| `polar2grid/utils/` | Satpy config-path wiring, dynamic imports, the `AliasHandler`, misc scripts |
| `polar2grid/etc/` | Satpy config directory shipped with the package |
| `polar2grid/tests/` | pytest suite (`testpaths` in `pyproject.toml`) |
| `polar2grid/add_coastlines.py`, `add_colormap.py`, `compare.py`, `debug_data.py` | Standalone utility scripts with their own `main()` |
| `swbundle/` | The shell scripts shipped to users, plus `env.sh` and example configs |
| `doc/` | Sphinx documentation for both projects |
| `integration_tests/` | behave (BDD) tests run on SSEC Jenkins against a built bundle |
| `continuous_integration/` | The conda environment used by GitHub Actions |

# How A Run Works

`swbundle/polar2grid.sh` exports `POLAR2GRID_HOME`, `PROG_NAME`, `OMP_NUM_THREADS`, and
`USE_POLAR2GRID_DEFAULTS=1`, then runs `python3 -m polar2grid.glue -vv "$@"`. `geo2grid.sh` is the
mirror image with `USE_POLAR2GRID_DEFAULTS=0`. The pip-installed `polar2grid` / `geo2grid` console
scripts do the same thing from `polar2grid/__main__.py`.

From there, `glue.main()` builds a `_GlueProcessor` (`polar2grid/glue.py`) which:

1. Calls `add_polar2grid_config_paths()` (`polar2grid/utils/config.py`) to append `polar2grid/etc`
   to `satpy.config["config_path"]`.
2. Parses arguments in **two passes** (`GlueArgumentParser`, `polar2grid/_glue_argparser.py`). The
   first pass discovers `-r`/`-w` with `parse_known_args`; the second adds the argument groups that
   the selected reader and writer modules contribute. The resulting flat namespace is then sliced
   back into `_scene_creation`, `_load_args`, `_reader_args`, `_resample_args`, and `_writer_args`.
3. Handles `--extra-config-path` and sets up logging.
4. `_create_scene()` → `satpy.Scene(filenames=..., reader=..., reader_kwargs=...)`.
5. `ReaderProxyBase.from_reader_name(...)` → the reader's `ReaderProxy`, which converts requested
   Polar2Grid product names into Satpy names / `DataQuery` objects.
6. `scn.load(products, generate=False)`, then `_persist_swath_definition_in_scene()` (unless
   `--no-persist-geolocation`) and `scn.generate_possible_composites(True)`.
7. `_resample_scene_to_grids()` — optional `--ll-bbox` crop, then `filter_scene()` for day/night
   filtering, then `resample_scene()`.
8. `_save_scenes()` — rewrites `platform_name` and `sensor` to Polar2Grid's preferred spellings,
   stamps `p2g_name` on every DataArray, then calls `scn.save_datasets(..., compute=False)`.
9. A single `compute_writer_results()` computes the whole graph once.

# Wrapping Satpy

To retain product naming from older versions of Polar2Grid, provide defaults different from Satpy,
or provide additional functionality that doesn't quite fit in Satpy, the Polar2Grid project has
custom code wrapping many of the components of Satpy.

Wrappers are found purely by module name. `polar2grid/utils/dynamic_imports.py` imports
`polar2grid.readers.<name>` / `polar2grid.writers.<name>` and swallows `ModuleNotFoundError`. So if
Polar2Grid does not have a wrapper for a particular Satpy component, that component still works —
it simply gets no product aliases, no default product list, and no extra command line flags.
Readers in that situation fall back to the base `ReaderProxyBase` (`polar2grid/readers/_base.py`),
which logs a warning and lists products under their raw Satpy names. There is no registry and no
plugin entry point.

A component name does appear in a handful of other places, none of which are discovery: the
hardcoded `--help` lists (`_supported_readers()` / `_supported_writers()`), the alias tables
(`READER_ALIASES` / `WRITER_ALIASES`), the per-reader keys in each writer's
`DEFAULT_OUTPUT_FILENAMES`, `reader:` match keys in `polar2grid/etc/resampling.yaml`, and the
documentation pages.

## Readers

Reader modules in `polar2grid/readers/` provide additional command line arguments specific to the
reader, aliases or renamings for Satpy products, the default list of products to load if the user
didn't specify any, and the list of all products the reader knows about.

**The module basename must exactly equal the Satpy reader name.** That is the entire discovery
mechanism. Short names given in `READER_ALIASES` (`modis` → `modis_l1b`,
`avhrr` → `avhrr_l1b_aapp`) are resolved by argparse before the module import, so the module is
always named for the real Satpy reader.

A wrapper module defines a class named exactly `ReaderProxy` (subclassing `ReaderProxyBase`) and a
module-level `add_reader_argument_groups(parser, group=None)`;
`polar2grid/tests/test_readers/test_base.py` globs every module in the directory and enforces both.
Two further module-level names are read directly by the framework and are optional:
`PREFERRED_CHUNK_SIZE` (preferred square dask chunk edge, in pixels) and `FILTERS` (which products
day/night filtering is allowed to drop). The **module docstring is user-facing documentation** —
Sphinx renders it into `doc/source/readers/<name>.rst`, so it should include a table of supported
products. Read `omps_edr.py` for a minimal polar reader, `abi_l1b.py` for a geostationary one, and
`viirs_sdr.py` for the complex case; the field-by-field contract and the full checklist are in
`.claude/skills/add-reader/SKILL.md`.

`_supported_readers(is_polar2grid: bool)` in `polar2grid/_glue_argparser.py` returns a plain
`list[str]` — one hardcoded list per project. It is **only** the `-r` help text: the argument has
no `choices=`, so any Satpy reader name is accepted whether or not it is listed. That makes the
list a **second source of truth** which is not derived from the `is_*_reader` attributes. The two
were reconciled in August 2026 — every module in `polar2grid/readers/` is now advertised exactly
once, on the project its `is_*_reader` flag and its `doc/source/readers/index.rst` entry agree on —
but nothing enforces that, so adding a reader module without editing the list silently leaves it
unadvertised (it still works when named correctly). One disagreement is left on purpose: `clavrx`
sets both `is_polar2grid_reader` and `is_geo2grid_reader` but is listed under Polar2Grid only.

## Product Names and Aliases

Polar2Grid exposes its own product names, which are frequently *not* the Satpy names — this is the
main mechanism for preserving naming from pre-Satpy versions of Polar2Grid. The translation is done
by `AliasHandler` (`polar2grid/utils/legacy_compat.py`), driven by each `ReaderProxy._aliases`
mapping of Polar2Grid name to Satpy name or `DataQuery`. It converts requested Polar2Grid names to
Satpy identifiers before `Scene.load`, and at save time `apply_p2g_name_to_scene()` stamps the
chosen name back onto each DataArray as the `p2g_name` attribute. A product requested by its raw
Satpy name normally keeps that name as its `p2g_name`.

`p2g_name` is **not** guaranteed to exist: `convert_satpy_to_p2g_name()` yields `None` when a name
would be ambiguous (it collides with a different Polar2Grid name, or asking Satpy for it would
return a different `DataID`), and `apply_p2g_name_to_scene()` then leaves the attribute unset and
logs a debug message. Filename patterns using `{p2g_name}` will fail for such a product, so if a
new alias makes an existing product unnamable, that is the bug to look for.

`convert_p2g_pattern_to_satpy()` in the same module translates legacy Polar2Grid filename tokens
into Satpy's, warning about replaced ones. `get_sensor_alias()` and the platform alias table in
`glue.py` do the equivalent for sensor and platform names.

## Resampling and Grids

Polar2Grid provides a `polar2grid/etc/resampling.yaml` configuration file to configure what
resampling method and options should be used for a specific product being resampled. It is loaded
into a `ResamplerDecisionTree` (`polar2grid/resample/resample_decisions.py`) which is queried per
`DataID` and matches on keys like `reader`, `sensor`, `name`, and `area_type`, yielding a
`resampler`, its `kwargs`, and a `default_target` grid.

Target grid names are resolved by `AreaDefResolver` (`polar2grid/resample/_resample_scene.py`) in
this order: `None` means "do not resample", `MAX` means `scn.finest_area()`, `MIN` means
`scn.coarsest_area()`, then YAML areas from `polar2grid/grids/grids.yaml`, then the deprecated
`.conf` grid format via `GridManager` (`polar2grid/grids/manager.py`), then Satpy's built-in areas.

Note that grids are deliberately **not** part of `polar2grid/etc/` and are **not** loaded through
Satpy's config path — `etc/` has no `areas.yaml`. `grids.yaml` is loaded explicitly by the resample
module and can be supplemented with `--grid-configs`.

## Writers

Writer modules in `polar2grid/writers/` provide command line arguments for Satpy writers' keyword
arguments and default output filename format strings. Discovery is by module basename, same as
readers.

A writer module supplies `DEFAULT_OUTPUT_FILENAMES` — a two-level dict keyed `"polar2grid"` /
`"geo2grid"` (both required) then by reader name with a `None` fallback, using `{p2g_name}` in the
pattern — and `add_writer_argument_groups(parser, group=None)`, whose arguments flow straight into
`scn.save_datasets(**wargs)`. `polar2grid/tests/test_writers/test_base.py` enforces both. A writer
may also register its own Satpy `Writer` subclass from `polar2grid/etc/writers/<name>.yaml`; the
`geotiff` writer has no YAML and uses Satpy's unchanged. As with readers, `_supported_writers()` is
a separate hand-maintained list. Full contract and checklist: `.claude/skills/add-writer/SKILL.md`.

## Enhancements, Composites, and `etc/`

`polar2grid/etc/` is a Satpy configuration directory appended to `satpy.config["config_path"]` at
startup. It holds `resampling.yaml` (the decision tree above, Polar2Grid-only), `pyspectral.yaml`,
`colormaps/` (`.cmap` and `.txt` color tables), `enhancements/` (`generic.yaml` first, then
`<sensor>.yaml`), `composites/`, and `writers/`. There is also a nearly-empty `readers/` — it only
declares Satpy `data_files:` auxiliary download lists (`mirs.yaml`), and a new reader normally needs
nothing there.

Polar2Grid's enhancement YAML references its own Python functions via
`!!python/name:polar2grid.enhancements...`, and colormap paths inside that YAML use
`$POLAR2GRID_HOME` / `$GEO2GRID_HOME`, expanded at enhancement time by
`polar2grid/enhancements/shared.py`.

`--extra-config-path` accepts either a directory or a single enhancement YAML file. For a bare file,
a temporary directory containing `enhancements/generic.yaml` is synthesized and cleaned up at exit
(`glue.py`). Multiple paths are applied in the order given, so later paths win.

# Development

```bash
# Environment (see doc/source/dev_guide/dev_env.rst)
conda env create -n p2g_dev --file build_environment.yml
pip install --no-deps -e .

pytest polar2grid/tests                                    # full suite, roughly 3 minutes
pytest polar2grid/tests/test_readers -k viirs              # a subset
pre-commit run -a                                          # ruff-check --fix, ruff-format, shfmt -i 4

cd doc && make html                                        # Polar2Grid documentation
cd doc && make html POLAR2GRID_DOC=geo                     # Geo2Grid documentation

# Exercise the CLI directly -- this is what the .sh wrappers call
python -m polar2grid.glue -r viirs_sdr -w geotiff --help                  # no input data needed
python -m polar2grid.glue -r viirs_sdr -w geotiff --list-products -f DIR  # needs input files
```

There are two environment files and `dev_env.rst` only mentions the first.
`build_environment.yml` is the runtime/bundle environment — it does **not** include `pytest` or
Sphinx. `continuous_integration/environment.yaml` is what CI uses and adds `pytest`,
`pytest-lazy-fixtures`, `pytest-cov`, Sphinx, and the **forked** sphinx-argparse
(`djhoese/sphinx-argparse@bugfix-section-nums`) that `make html` requires. Use the CI file, or
update an existing environment from it, if you intend to run tests or build docs.

`pyproject.toml` declares `requires-python = ">=3.13"`, and CI, the CI conda environment, and the
software bundle environment (`build_environment.yml`) all pin 3.13, so the tested and shipped
version is the same one. The floor is set by Satpy `main`, which requires `>=3.12`.

CI (`.github/workflows/ci.yaml`) builds **both** documentation variants with
`SPHINXOPTS="-W --keep-going"` and runs pytest on Linux/macOS/Windows. Windows runs only the
`--help` smoke tests (not enough memory for the full suite).

**Do not run `integration_tests/`.** Those are behave (BDD) tests that require a software bundle
built by `create_conda_software_bundle.sh`, a `POLAR2GRID_HOME`, and external test data hosted at
SSEC. They run on Jenkins, not in GitHub Actions.

## Testing conventions

* Contract tests auto-parametrize over every module, so a malformed new component fails without you
  writing a test: `tests/test_readers/test_base.py`, `tests/test_writers/test_base.py`, and
  `tests/test_configs.py` (every `polar2grid/etc/**/*.yaml` parses).
* There is no per-reader test module convention. Reader and writer behavior is covered end-to-end
  through the glue: build a fake `Scene` from `tests/_fixture_utils.py` (`_FakeReader`,
  `_TestingScene`) plus the per-instrument fixture modules `_abi_fixtures.py`, `_viirs_fixtures.py`,
  `_avhrr_fixtures.py`, then call `polar2grid.glue.main([...])` and assert the number of dask
  computes with `satpy.tests.utils.CustomScheduler`. `tests/test_glue.py` is the model.
* No binary satellite data goes in the repository. Small static config data lives in
  `polar2grid/tests/etc/`.
* Tests must not hit the network. `tests/conftest.py` forbids pyspectral downloads for the whole
  session, calls `add_polar2grid_config_paths()` at configure time, and clears the filter module's
  caches between tests.
* `pyproject.toml` sets `filterwarnings = ["error", ...]` — any new warning fails the suite.
  `--strict-markers`, `--strict-config`, and `xfail_strict` are on.

## Documentation conventions

One source tree builds both projects (`make html` vs `make html POLAR2GRID_DOC=geo`), so shared
`.rst` must never hardcode a project name:

* Use the `rst_epilog` substitutions from `doc/source/conf.py` — `|project|`, `|script|`,
  `|script_literal|`, `|project_env|`, `|cspp_abbr|`, `|cspp_title|`.
* Use the `toctree-filt` directive with `:polar2grid:` / `:geo2grid:` entry prefixes
  (`doc/source/toctree_filter.py`), and `.. ifconfig:: is_geo2grid` for inline conditionals.
* A new `.rst` must be added to a toctree **and** to the *other* project's `exclude_patterns` in
  `conf.py`, or the CI `-W` build fails with "document isn't included in any toctree". The two
  project lists are the `_GEO2GRID_EXCLUDES` / `_POLAR2GRID_EXCLUDES` constants; a check at the
  bottom of `conf.py` raises if either one names a file that does not exist, so a page that is
  removed must also be removed from the list.

Do not hand-edit `doc/source/grids_list.rst`, `doc/source/dev_guide/api/`, or
`doc/source/_static/example_images/` — all three are generated at build time and gitignored.
`summary_table*.rst` is hand-maintained and committed — despite its name there is no
generator for it; edit it directly.

The root `Makefile` holds documentation targets only: `build_doc_html` / `build_doc_html_geo` wrap
the `doc/` build, and `update_doc` / `update_doc_geo` build and then scp the result to the SSEC web
server. CI and `integration_tests/run.sh` call `doc/Makefile` directly instead.

Anything more involved — build invocations, the forked sphinx-argparse, the generated-file
mechanics — is in `.claude/skills/build-docs/SKILL.md`.

# Gotchas

* Every source file carries the SSEC GPLv3 header block. Copy it into new files.
* Any new `swbundle/*.sh` needs the `# __SWBUNDLE_ENVIRONMENT_INJECTION__` marker comment (the
  bundle build replaces it with a `source .../env.sh`) *and* an entry in
  `[tool.hatch.build.targets.wheel.shared-scripts]` in `pyproject.toml`.
* Changelogs are manual and split: `NEWS.rst` for Polar2Grid, `NEWS_GEO2GRID.rst` for Geo2Grid.
  Each is excluded from the other project's documentation build.
* Images in the repository are Git LFS (`.gitattributes`).
* There are three hand-maintained versions and they are **intentionally not in sync**: the
  `polar2grid` Python package (`pyproject.toml`, no setuptools-scm), the Polar2Grid bundle, and the
  Geo2Grid bundle. Both bundle versions live in `doc/source/conf.py` and track the newest entry of
  `NEWS.rst` / `NEWS_GEO2GRID.rst`; the documentation shows the bundle version, not the package
  version.
* Running the test suite drops `*_fail.log` and timestamped `.log` files in the current working
  directory. The working tree may also already contain large untracked output artifacts (GeoTIFFs,
  logs, unpacked bundles) at the repository root. Never `git add -A`.

Known stale spots — verify before trusting:

* `doc/source/dev_guide/adding_readers.rst` has two empty `TODO` sections and says to register a
  new reader in `polar2grid/glue.py`; the list is actually `_supported_readers()` in
  `polar2grid/_glue_argparser.py`. Prefer the `add-reader` skill.
* `modis_l2`, `omps_edr`, and `virr_l1b` are advertised in `_supported_readers()` but have no page
  under `doc/source/readers/`, so do not use them as the model when adding a reader's
  documentation. (`avhrr_l1b_aapp` is documented as `avhrr.rst`, and `viirs_edr_flood.rst` is
  excluded on purpose.)

# Where to Read More

| Task | Document |
|---|---|
| Add a reader | The `add-reader` skill. `doc/source/dev_guide/adding_readers.rst` covers the same ground but is partly stale (see above). |
| Add a writer | The `add-writer` skill. There is no dev-guide page; read `polar2grid/writers/geotiff.py` and `hdf5.py`. |
| Build or edit documentation | The `build-docs` skill |
| Set up a dev environment | `doc/source/dev_guide/dev_env.rst` |
| Software bundle internals | `doc/source/dev_guide/swbundle.rst`, `create_conda_software_bundle.sh` |
| Architecture overview | `doc/source/design_overview.rst` |
| Resampling and grids | `doc/source/remapping.rst`, `doc/source/grids.rst`, `doc/source/custom_grids.rst` |
| Enhancements and custom config | `doc/source/enhancements.rst`, `doc/source/custom_config.rst` |
| Integration tests / Jenkins | `integration_tests/README.rst`, header comments in `integration_tests/run.sh` |
| Releasing to PyPI | `RELEASING.md`. Bundle releases are driven by git tags and commit-message tokens described in `integration_tests/run.sh`. |
| Contributing | `README.rst` ("Contributing" section) — contact the team before large features, then fork and open a PR. There is no `CONTRIBUTING.md` and no branch-naming convention. |
