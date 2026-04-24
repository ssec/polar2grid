#!/usr/bin/env python3
"""Glob for VIIRS SDR objects in NOAA NESDIS S3 buckets.

Example usage:
  # Single band
  python glob_viirs_s3.py --satellite n20 --band I05 \
      --start-time 2026-04-24T01:10 --end-time 2026-04-24T01:12

  # Multiple bands
  python glob_viirs_s3.py --satellite n20 --band I04 --band I05 --band M15 \
      --start-time 2026-04-24T00:00 --end-time 2026-04-24T01:00

  # All bands
  python glob_viirs_s3.py --satellite n20 --band ALL \
      --start-time 2026-04-24T00:00 --end-time 2026-04-24T23:59 \
      --no-sign-request
"""

from __future__ import annotations

import argparse
from glob import fnmatch
import os
import re
import sys
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone

import s3fs

BUCKET_FORMAT_STR = os.environ.get("BUCKET_FORMAT_STR", "noaa-nesdis-{satellite}-pds")
GRANULE_DURATION_SECONDS = 90

# ---------------------------------------------------------------------------
# Band helpers
# ---------------------------------------------------------------------------

VALID_BANDS = (
    ["I01", "I02", "I03", "I04", "I05"]
    + [f"M{n:02d}" for n in range(1, 17)]
    # non-terrain corrected geolocation is not available from NOAA buckets
    + ["DNB", "GITCO", "GMTCO", "GDNBO"]  # + ["GIMGO", "GMODO"]
)
DEFAULT_BANDS = VALID_BANDS

# Special token accepted by --band that expands to every band
ALL_BANDS_TOKEN = "ALL"


def parse_band(value: str) -> list[str]:
    """Validate a single --band value and return the list of bands it represents.

    "ALL" expands to every band; otherwise the value must be a known band name.

    """
    upper = value.upper()
    if upper == ALL_BANDS_TOKEN:
        return list(DEFAULT_BANDS)
    if upper not in VALID_BANDS:
        raise argparse.ArgumentTypeError(
            f"Invalid band {value!r}. Choose from {', '.join(VALID_BANDS)} or '{ALL_BANDS_TOKEN}'."
        )
    return [upper]


def band_to_prefix(band: str) -> str:
    """Convert a band name to the SDR or GEO product-prefix segment used in the S3 key.

    For example, the I01 SDR band is converted to "VIIRS-I1-SDR". The geolocation
    "band" GITCO is converted to "VIIRS-IMG-GEO-TC".

    """
    if band.startswith("G"):
        # M-band and I-band geolocation are only available for terrain-corrected (TC)
        band_type = "GEO" if band[1] == "D" else "GEO-TC"
    else:
        band_type = "SDR"

    if band == "DNB":
        prefix_id = band
    elif band[0] == "G":
        prefix_id = {
            "D": "DNB",
            "I": "IMG",
            "M": "MOD",
        }[band[1]]
    else:
        letter = band[0]  # 'I' or 'M'
        number = int(band[1:])  # strip leading zero
        prefix_id = f"{letter}{number}"

    return f"VIIRS-{prefix_id}-{band_type}"


# ---------------------------------------------------------------------------
# Date/time helpers
# ---------------------------------------------------------------------------


def parse_datetime(s: str) -> datetime:
    """Parse date/times from the command line.

    Accept ISO-8601-ish strings: YYYY-MM-DDTHH:MM[:SS]

    """
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"Cannot parse datetime {s!r}. Use YYYY-MM-DDTHH:MM[:SS] or YYYY-MM-DD.")


def iter_day_prefixes(start: datetime, end: datetime):
    """Yield every unique date/time between start and end (inclusive) at hour resolution."""
    curr_time = start.replace(minute=0, second=0, microsecond=0)
    if start.hour == 0 and (start - curr_time).total_seconds() < GRANULE_DURATION_SECONDS:
        # if we might get a partial granule on the midnight boundary, then search the 23rd hour of the previous day
        curr_time = curr_time - timedelta(hours=1)
    end_day = end.replace(minute=0, second=0, microsecond=0)
    if end_day.hour == 23 and ((end_day + timedelta(hours=1)) - end).total_seconds() < GRANULE_DURATION_SECONDS:
        # if we might get a partial granule on the end of the day over midnight
        # then search the first hour of the next day
        end_day = end_day + timedelta(hours=1)
    while curr_time <= end_day:
        yield curr_time
        curr_time += timedelta(hours=1)


# ---------------------------------------------------------------------------
# Filename time extraction
# ---------------------------------------------------------------------------

_FNAME_RE = re.compile(
    r"_d(?P<date>\d{8})"  # dYYYYMMDD
    r"_t(?P<tstart>\d{7})"  # tHHMMSSd  (tenths digit after seconds)
    r"_e(?P<tend>\d{7})"  # eHHMMSSd
)


def file_start_end_time(filename: str) -> tuple[datetime, datetime] | tuple[None, None]:
    """Parse the granule start time from a VIIRS SDR filename."""
    if (m := _FNAME_RE.search(filename)) is None:
        print(f"Unexpected filename scheme discovered: {filename}", file=sys.stderr)
        return None, None

    try:
        return _convert_file_times_to_datetimes(
            m.group("date"),  # YYYYMMDD
            m.group("tstart")[:6],  # HHMMSS (drop microseconds)
            m.group("tend")[:6],
        )
    except ValueError:
        print(f"Could not parse time information: {filename}", file=sys.stderr)
        return None, None


def _convert_file_times_to_datetimes(date_str: str, tstart: str, tend: str) -> tuple[datetime, datetime]:
    start_dt = datetime.strptime(date_str + tstart, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(date_str + tend, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Glob VIIRS SDR files in a NOAA NESDIS public S3 bucket.")
    p.add_argument(
        "-s",
        "--satellite",
        required=True,
        help="Satellite identifier, e.g. n20, n21, snpp.",
    )
    p.add_argument(
        "-b",
        "--band",
        required=True,
        action="append",
        dest="bands",
        type=parse_band,
        metavar="BAND",
        help=(
            "VIIRS band to search for. May be specified multiple times. "
            f"Individual choices: {', '.join(VALID_BANDS)}. "
            f"Use '{ALL_BANDS_TOKEN}' to select every band plus terrain-corrected geolocation."
        ),
    )
    p.add_argument(
        "--start-time",
        required=True,
        type=parse_datetime,
        metavar="YYYY-MM-DDTHH:MM[:SS]",
        help="Earliest granule start time (UTC).",
    )
    p.add_argument(
        "--end-time",
        required=True,
        type=parse_datetime,
        metavar="YYYY-MM-DDTHH:MM[:SS]",
        help="Latest granule end time (UTC).",
    )
    p.add_argument(
        "--print-urls",
        action="store_true",
        help="Print HTTPS URLs instead of s3:// paths.",
    )
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.start_time > args.end_time:
        parser.error("--start-time must be before --end-time")
    if (args.end_time - args.start_time).total_seconds() >= 60 * 60:
        parser.error("Time range can't be more than 60 minutes.")

    # Flatten the list-of-lists produced by action="append" + type=parse_band,
    # then deduplicate while preserving the canonical VALID_BANDS order.
    requested = {band for group in args.bands for band in group}
    bands = [b for b in VALID_BANDS if b in requested]
    satellite = args.satellite.lower()

    fs = s3fs.S3FileSystem(anon=True)
    found = []
    for glob_pattern in _generate_glob_patterns(bands, args.start_time, args.end_time, satellite):
        glob_matches = _glob_s3_fs(fs, glob_pattern)
        found.extend(_filter_by_start_end(glob_matches, args.start_time, args.end_time))

    if not found:
        print("No matching objects found.", file=sys.stderr)
        sys.exit(1)
    _print_uris(found, args.print_urls)


def _generate_glob_patterns(
    bands: Iterable[str], start_time: datetime, end_time: datetime, satellite: str
) -> Iterator[str]:
    fn_platform = {
        "snpp": "npp",
        "n20": "j01",
        "n21": "j02",
        "n22": "j03",
        "n23": "j04",
    }[satellite]
    bucket = BUCKET_FORMAT_STR.format(satellite=satellite)

    for band in bands:
        prefix_code = band_to_prefix(band)  # e.g. "I5", "M3", "DNB"
        fn_band_id = f"SV{band}" if band[0] in ("M", "I", "D") else band

        for glob_datetime in iter_day_prefixes(start_time, end_time):
            day_path = glob_datetime.strftime("%Y/%m/%d")
            fn_day_str = day_path.replace("/", "")
            fn_time_hour = glob_datetime.strftime("%H")
            # e.g. noaa-nesdis-n20-pds/VIIRS-I5-SDR/2026/04/24/
            prefix = f"{bucket}/{prefix_code}/{day_path}/"
            # later process (see _glob_s3_fs) is very particular about how many wildcards are used
            glob_pattern = f"{prefix}{fn_band_id}_{fn_platform}_d{fn_day_str}_t{fn_time_hour}*.h5"
            yield glob_pattern


def _glob_s3_fs(fs: s3fs.S3FileSystem, glob_pattern: str) -> Iterator[str]:
    # At the time of writing fs.glob is slow because it iterates over all
    # objects in the bucket instead of using a prefix
    # yield from fs.glob(glob_pattern)
    # return

    uri_path, uri_fn = glob_pattern.rsplit("/", 1)
    uri_fn = uri_fn.rstrip("/")
    static_fn_prefix = uri_fn.split("*", 1)[0]
    for result in fs.find(uri_path, prefix=static_fn_prefix):
        res_fn = result.rsplit("/", 1)[1]
        if not fnmatch.fnmatch(res_fn, uri_fn):
            continue
        yield result


def _filter_by_start_end(possible_paths: Iterable[str], start_time: datetime, end_time: datetime) -> Iterator[str]:
    for path in possible_paths:
        fname = path.rsplit("/", 1)[-1]
        if _overlaps_time_range(fname, start_time, end_time):
            yield path


def _overlaps_time_range(fname: str, start_time: datetime, end_time: datetime) -> bool:
    t_start, t_end = file_start_end_time(fname)

    return t_start is not None and t_end is not None and not (t_end < start_time or t_start > end_time)


def _print_uris(paths: Iterable[str], print_urls: bool) -> None:
    for path in paths:
        if print_urls:
            # s3://bucket/key  ->  https://bucket.s3.amazonaws.com/key
            parts = path.split("/", 1)
            bkt, key = parts[0], parts[1] if len(parts) > 1 else ""
            print(f"https://{bkt}.s3.amazonaws.com/{key}")
        else:
            print(f"s3://{path}")


if __name__ == "__main__":
    main()
