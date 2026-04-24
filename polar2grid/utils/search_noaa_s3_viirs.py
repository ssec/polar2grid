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
    """Convert a band name to the SDR product-prefix segment used in the S3 key.

    I01 -> I1   I05 -> I5
    M01 -> M1   M16 -> M16
    DNB -> DNB

    GITCO -> GITCO   GMTCO -> GMTCO
    GDNBO -> GDNBO
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
    """Yield every unique YYYY/MM/DD string between start and end (inclusive)."""
    day = start.replace(hour=0, minute=0, second=0, microsecond=0)
    if (start - day).total_seconds() < GRANULE_DURATION_SECONDS:
        # if we might get a partial granule on the midnight boundary, then search the previous day
        day = day - timedelta(days=1)
    end_day = end.replace(hour=0, minute=0, second=0, microsecond=0)
    if ((end_day + timedelta(days=1)) - end).total_seconds() < GRANULE_DURATION_SECONDS:
        # if we might get a partial granule on the end of the day over midnight then search the next day too
        end_day = end_day + timedelta(days=1)
    while day <= end_day:
        yield day.strftime("%Y/%m/%d")
        day += timedelta(days=1)


# ---------------------------------------------------------------------------
# Filename time extraction
# ---------------------------------------------------------------------------

_FNAME_RE = re.compile(
    r"_d(?P<date>\d{8})"  # dYYYYMMDD
    r"_t(?P<tstart>\d{7})"  # tHHMMSSd  (tenths digit after seconds)
    r"_e(?P<tend>\d{7})"  # eHHMMSSd
)


def file_start_time(filename: str) -> datetime | None:
    """Parse the granule start time from a VIIRS SDR filename."""
    m = _FNAME_RE.search(filename)
    if not m:
        return None
    date_str = m.group("date")  # YYYYMMDD
    tstart = m.group("tstart")[:6]  # HHMMSS (drop tenths digit)
    try:
        return datetime.strptime(date_str + tstart, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def file_end_time(filename: str) -> datetime | None:
    """Parse the granule end time from a VIIRS SDR filename."""
    m = _FNAME_RE.search(filename)
    if not m:
        return None
    date_str = m.group("date")
    tend = m.group("tend")[:6]
    try:
        dt = datetime.strptime(date_str + tend, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        # Granules that cross midnight: end time can be earlier than start
        # on the same calendar day -- advance by one day when that happens.
        tstart = file_start_time(filename)
        if tstart and dt < tstart:
            dt += timedelta(days=1)
        return dt
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


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
        "--profile",
        default=None,
        help="AWS profile name to use for authenticated access.",
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

    if args.profile is None:
        fs = s3fs.S3FileSystem(anon=True)
    else:
        fs = s3fs.S3FileSystem(anon=False, profile=args.profile)

    found = []
    for glob_pattern in _generate_glob_patterns(bands, args.start_time, args.end_time, satellite):
        try:
            # TODO: Use fs.find and then filter with glob/fnmatch. Might be faster
            matches = fs.glob(glob_pattern)
        except FileNotFoundError:
            # Prefix doesn't exist yet -- no data for that day/band
            continue
        except Exception as exc:
            print(f"Warning: error listing {glob_pattern}: {exc}", file=sys.stderr)
            continue

        found.extend(_filter_by_start_end(matches, args.start_time, args.end_time))

    if not found:
        print("No matching objects found.", file=sys.stderr)
        sys.exit(1)

    for path in sorted(found):
        if args.print_urls:
            # s3://bucket/key  ->  https://bucket.s3.amazonaws.com/key
            parts = path.split("/", 1)
            bkt, key = parts[0], parts[1] if len(parts) > 1 else ""
            print(f"https://{bkt}.s3.amazonaws.com/{key}")
        else:
            print(f"s3://{path}")


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

        for day_path in iter_day_prefixes(start_time, end_time):
            # e.g. noaa-nesdis-n20-pds/VIIRS-I5-SDR/2026/04/24/
            prefix = f"{bucket}/{prefix_code}/{day_path}/"
            fn_day_str = day_path.replace("/", "")
            # TODO: Also iterate by hour, half orbit is ~51 minutes
            glob_pattern = f"{prefix}{fn_band_id}_{fn_platform}_d{fn_day_str}_t*.h5"
            yield glob_pattern


def _filter_by_start_end(possible_paths: Iterable[str], start_time: datetime, end_time: datetime) -> Iterator[str]:
    for path in possible_paths:
        fname = path.rsplit("/", 1)[-1]
        t_start = file_start_time(fname)
        t_end = file_end_time(fname)

        # Filter: granule must overlap [args.start_time, args.end_time]
        if t_start is not None and t_end is not None:
            if t_end < start_time or t_start > end_time:
                continue
        elif t_start is not None:
            if t_start > end_time:
                continue

        yield path


if __name__ == "__main__":
    main()
