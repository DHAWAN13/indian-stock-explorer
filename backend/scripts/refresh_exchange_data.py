"""Download, validate, compact, and refresh NSE/BSE equity security masters.

The output retains the dated filenames and columns expected by the existing
NSEProvider and BSEProvider implementations.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import shutil
import sys
import tempfile
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NSE_URL_TEMPLATE = (
    "https://nsearchives.nseindia.com/content/cm/"
    "NSE_CM_security_{date}.csv.gz"
)
BSE_ZIP_URL = "https://www.bseindia.com/downloads/Help/file/scrip.zip"

NSE_COLUMNS = [
    "FinInstrmId",
    "TckrSymb",
    "SctySrs",
    "FinInstrmNm",
    "ISIN",
    "DelFlg",
]
BSE_COLUMNS = [
    "FinInstrmId",
    "TckrSymb",
    "FinInstrmNm",
    "ISIN",
    "SctyTpFlg",
    "FinInstrmTp",
    "Sts",
]

MIN_EQUITY_RECORDS = 1_000
MIN_RETAINED_RATIO = 0.65
MAX_NSE_LOOKBACK_DAYS = 10
MAX_SOURCE_AGE_DAYS = 10
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def log(message: str) -> None:
    print(message, flush=True)


def http_get(url: str, referer: str, attempts: int = 3) -> bytes:
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Accept": "*/*",
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=60) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise RuntimeError(f"HTTP {status} for {url}")
                payload = response.read()
                if not payload:
                    raise RuntimeError(f"Empty response from {url}")
                return payload
        except HTTPError as exc:
            last_error = exc
            # A 404 for a dated NSE file is expected while checking dates.
            if exc.code == 404:
                raise
            log(f"HTTP {exc.code} on attempt {attempt}/{attempts}: {url}")
        except (URLError, TimeoutError, OSError, RuntimeError) as exc:
            last_error = exc
            log(f"Download attempt {attempt}/{attempts} failed: {exc}")

        if attempt < attempts:
            time.sleep(attempt * 2)

    raise RuntimeError(f"Could not download {url}: {last_error}")


def parse_file_date(filename: str, pattern: str) -> date:
    match = re.search(pattern, filename, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot find DDMMYYYY date in filename: {filename}")
    return datetime.strptime(match.group(1), "%d%m%Y").date()


def latest_existing_file(data_dir: Path, pattern: str) -> Path | None:
    candidates: list[tuple[date, Path]] = []
    for path in data_dir.glob(pattern):
        try:
            file_date = parse_file_date(path.name, r"(\d{8})")
        except ValueError:
            continue
        candidates.append((file_date, path))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def read_dict_rows(text_stream: io.TextIOBase, required: set[str]) -> tuple[list[str], Iterable[dict[str, str]]]:
    reader = csv.DictReader(text_stream)
    headers = reader.fieldnames or []
    missing = required.difference(headers)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    return headers, reader


def nonempty(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def validate_record_volume(exchange: str, count: int, previous_count: int | None) -> None:
    if count < MIN_EQUITY_RECORDS:
        raise ValueError(
            f"{exchange} returned only {count} eligible equity rows; "
            f"minimum is {MIN_EQUITY_RECORDS}. Existing files will be kept."
        )
    if previous_count and count < int(previous_count * MIN_RETAINED_RATIO):
        raise ValueError(
            f"{exchange} row count dropped from {previous_count} to {count} "
            f"(below {MIN_RETAINED_RATIO:.0%} of the previous count). "
            "This may indicate an incomplete source file; existing files will be kept."
        )


def count_existing_nse(path: Path | None) -> int | None:
    if path is None:
        return None
    count = 0
    try:
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
            _, rows = read_dict_rows(
                stream,
                {"FinInstrmNm", "TckrSymb", "ISIN", "FinInstrmId", "SctySrs", "DelFlg"},
            )
            for row in rows:
                if nonempty(row, "SctySrs").upper() == "EQ" and nonempty(row, "DelFlg").upper() != "Y":
                    count += 1
        return count
    except (OSError, EOFError, csv.Error, ValueError):
        log(f"WARNING: Could not read previous NSE file for count comparison: {path}")
        return None


def count_existing_bse(path: Path | None) -> int | None:
    if path is None:
        return None
    count = 0
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            _, rows = read_dict_rows(
                stream,
                {"SctyTpFlg", "FinInstrmTp", "Sts", "TckrSymb", "FinInstrmNm", "ISIN", "FinInstrmId"},
            )
            for row in rows:
                symbol = nonempty(row, "TckrSymb")
                if (
                    nonempty(row, "SctyTpFlg").upper() == "EQ"
                    and nonempty(row, "FinInstrmTp").upper() == "E"
                    and nonempty(row, "Sts").upper() == "A"
                    and not symbol.endswith("#")
                ):
                    count += 1
        return count
    except (OSError, csv.Error, ValueError):
        log(f"WARNING: Could not read previous BSE file for count comparison: {path}")
        return None


def find_nse_source(today: date) -> tuple[date, str, bytes]:
    referer = "https://www.nseindia.com/all-reports"
    for offset in range(MAX_NSE_LOOKBACK_DAYS + 1):
        candidate_date = today - timedelta(days=offset)
        date_text = candidate_date.strftime("%d%m%Y")
        url = NSE_URL_TEMPLATE.format(date=date_text)
        log(f"Checking NSE security master: {date_text}")
        try:
            payload = http_get(url, referer)
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        # Validate gzip integrity before returning a candidate.
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as compressed:
                compressed.read(1)
        except (OSError, EOFError) as exc:
            raise ValueError(f"NSE response is not a valid gzip file ({date_text})") from exc
        return candidate_date, url, payload
    raise RuntimeError(
        f"No NSE MII security file found in the last {MAX_NSE_LOOKBACK_DAYS + 1} calendar days."
    )


def compact_nse(payload: bytes, previous_count: int | None) -> tuple[bytes, int]:
    required = set(NSE_COLUMNS)
    output = io.BytesIO()
    count = 0

    with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as source_gzip:
        text = io.TextIOWrapper(source_gzip, encoding="utf-8-sig", newline="")
        _, rows = read_dict_rows(text, required)
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as target_gzip:
            target_text = io.TextIOWrapper(target_gzip, encoding="utf-8", newline="")
            writer = csv.DictWriter(target_text, fieldnames=NSE_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                if nonempty(row, "SctySrs").upper() != "EQ":
                    continue
                if nonempty(row, "DelFlg").upper() == "Y":
                    continue
                if not nonempty(row, "TckrSymb") or not nonempty(row, "FinInstrmNm"):
                    continue
                writer.writerow({column: nonempty(row, column) for column in NSE_COLUMNS})
                count += 1
            target_text.flush()
            target_text.detach()
        text.detach()

    validate_record_volume("NSE", count, previous_count)
    return output.getvalue(), count


def find_bse_source() -> tuple[date, str, bytes, str]:
    url = BSE_ZIP_URL
    payload = http_get(url, "https://www.bseindia.com/")
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise ValueError("BSE response is not a valid ZIP archive") from exc

    with archive:
        candidates: list[tuple[date, str]] = []
        for name in archive.namelist():
            base = Path(name).name
            if re.fullmatch(r"BSE_EQ_SCRIP_\d{8}\.csv", base, flags=re.IGNORECASE):
                candidates.append((parse_file_date(base, r"BSE_EQ_SCRIP_(\d{8})"), name))
        if not candidates:
            raise ValueError("BSE ZIP did not contain BSE_EQ_SCRIP_DDMMYYYY.csv")
        file_date, member_name = max(candidates, key=lambda item: item[0])
        log(f"Selected BSE file inside ZIP: {member_name}")
        csv_payload = archive.read(member_name)
    return file_date, url, csv_payload, member_name


def compact_bse(payload: bytes, previous_count: int | None) -> tuple[bytes, int]:
    required = set(BSE_COLUMNS)
    count = 0
    output = io.StringIO(newline="")
    text = io.TextIOWrapper(io.BytesIO(payload), encoding="utf-8-sig", newline="")
    _, rows = read_dict_rows(text, required)
    writer = csv.DictWriter(output, fieldnames=BSE_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        symbol = nonempty(row, "TckrSymb")
        if (
            nonempty(row, "SctyTpFlg").upper() != "EQ"
            or nonempty(row, "FinInstrmTp").upper() != "E"
            or nonempty(row, "Sts").upper() != "A"
            or not symbol
            or symbol.endswith("#")
            or not nonempty(row, "FinInstrmNm")
        ):
            continue
        writer.writerow({column: nonempty(row, column) for column in BSE_COLUMNS})
        count += 1
    text.detach()
    validate_record_volume("BSE", count, previous_count)
    return output.getvalue().encode("utf-8"), count


def ensure_not_stale(exchange: str, candidate_date: date, current_path: Path | None) -> None:
    if current_path is None:
        return
    current_date = parse_file_date(current_path.name, r"(\d{8})")
    if candidate_date < current_date:
        raise ValueError(
            f"Refusing to replace {exchange} {current_date:%d%m%Y} with older "
            f"{candidate_date:%d%m%Y} data."
        )


def write_compact_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def refresh(data_dir: Path, dry_run: bool = False) -> bool:
    data_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date()
    nse_current = latest_existing_file(data_dir, "NSE_CM_security_*.csv.gz")
    bse_current = latest_existing_file(data_dir, "BSE_EQ_SCRIP_*.csv")

    nse_previous_count = count_existing_nse(nse_current)
    bse_previous_count = count_existing_bse(bse_current)

    nse_date, nse_url, nse_source = find_nse_source(today)
    bse_date, bse_url, bse_source, bse_member = find_bse_source()

    for exchange, candidate_date in (("NSE", nse_date), ("BSE", bse_date)):
        age_days = (today - candidate_date).days
        if age_days < 0 or age_days > MAX_SOURCE_AGE_DAYS:
            raise ValueError(
                f"{exchange} source date {candidate_date} is {age_days} days from "
                f"today; refusing a source older than {MAX_SOURCE_AGE_DAYS} days."
            )

    ensure_not_stale("NSE", nse_date, nse_current)
    ensure_not_stale("BSE", bse_date, bse_current)

    nse_compact, nse_count = compact_nse(nse_source, nse_previous_count)
    bse_compact, bse_count = compact_bse(bse_source, bse_previous_count)

    nse_name = f"NSE_CM_security_{nse_date:%d%m%Y}.csv.gz"
    bse_name = f"BSE_EQ_SCRIP_{bse_date:%d%m%Y}.csv"
    manifest = {
        "schema_version": 1,
        "NSE": {
            "file": nse_name,
            "date": nse_date.isoformat(),
            "eligible_equity_records": nse_count,
            "source_url": nse_url,
        },
        "BSE": {
            "file": bse_name,
            "date": bse_date.isoformat(),
            "eligible_equity_records": bse_count,
            "source_url": bse_url,
            "source_archive_member": bse_member,
        },
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    log("\nValidated security masters:")
    log(f"NSE: {nse_name} — {nse_count:,} eligible equity records")
    log(f"BSE: {bse_name} — {bse_count:,} eligible equity records")
    log(f"NSE compact file size: {len(nse_compact):,} bytes")
    log(f"BSE compact file size: {len(bse_compact):,} bytes")

    if dry_run:
        log("DRY RUN: no repository files were changed.")
        return False

    # Prepare every output before replacing any current data file.
    with tempfile.TemporaryDirectory(prefix="security-master-") as temp_name:
        temp_dir = Path(temp_name)
        temp_nse = temp_dir / nse_name
        temp_bse = temp_dir / bse_name
        temp_manifest = temp_dir / "security_master_manifest.json"
        write_compact_file(temp_nse, nse_compact)
        write_compact_file(temp_bse, bse_compact)
        write_compact_file(temp_manifest, manifest_bytes)

        # Replace new files first. The old dated files remain until both new
        # files and the manifest are safely written to the target directory.
        target_nse = data_dir / nse_name
        target_bse = data_dir / bse_name
        target_manifest = data_dir / "security_master_manifest.json"
        shutil.copy2(temp_nse, target_nse)
        shutil.copy2(temp_bse, target_bse)
        shutil.copy2(temp_manifest, target_manifest)

    # Keep only the newest file for each exchange to prevent repository growth.
    for old in data_dir.glob("NSE_CM_security_*.csv.gz"):
        if old.name != nse_name:
            old.unlink()
    for old in data_dir.glob("BSE_EQ_SCRIP_*.csv"):
        if old.name != bse_name:
            old.unlink()

    log(f"Updated security masters in {data_dir}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "exchange",
        help="Directory containing the dated NSE/BSE security master files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and validate sources without changing local files.",
    )
    args = parser.parse_args()

    try:
        changed = refresh(args.data_dir.resolve(), dry_run=args.dry_run)
        if not args.dry_run and not changed:
            log("No data change detected.")
        return 0
    except Exception as exc:  # Fail closed: leave last known-good data in place.
        log(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
