import argparse
import csv
import hashlib
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

TIME_COLUMNS = {
    "modified": ["Modified Time"],
    "changed": ["Change Time", "Changed Time"],
    "accessed": ["Access Time", "Accessed Time"],
    "created": ["Created Time"],
}

EXPECTED_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "png": "image/png",
    "txt": "text/plain",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iso_utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def hash_evidence(path, log_path):
    st = os.stat(path)
    row = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "file_name": os.path.basename(path),
        "full_path": os.path.abspath(path),
        "size_bytes": st.st_size,
        "file_modified_utc": iso_utc(st.st_mtime),
        "sha256": sha256_file(path),
    }
    new_log = not os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new_log:
            writer.writeheader()
        writer.writerow(row)
    return row


def parse_time(text, offset_hours):
    """Autopsy shows 0000-00-00 for 'no date'. Return None for those."""
    text = (text or "").strip()
    if not text or text.startswith("0000"):
        return None
    naive = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    source_tz = timezone(timedelta(hours=offset_hours))
    return naive.replace(tzinfo=source_tz)


def first_value(row, names):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return ""


def build_timeline(csv_paths, offset_hours, case_tz):
    local_tz = ZoneInfo(case_tz)
    events = []
    for path in csv_paths:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                name = first_value(row, ["Name", "File"])
                location = first_value(row, ["Location", "File Path"])
                size = row.get("Size", "")
                for kind, columns in TIME_COLUMNS.items():
                    when = parse_time(first_value(row, columns), offset_hours)
                    if when is None:
                        continue
                    events.append({
                        "local_time": when.astimezone(local_tz).isoformat(timespec="seconds"),
                        "utc_time": when.astimezone(timezone.utc).isoformat(timespec="seconds"),
                        "event": kind,
                        "name": name,
                        "path": location,
                        "size": size,
                        "source_csv": os.path.basename(path),
                    })
    events.sort(key=lambda e: e["utc_time"])
    return events


def write_timeline(events, out_path):
    fields = ["local_time", "utc_time", "event", "name", "path", "size", "source_csv"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(events)


def flag_files(csv_paths, offset_hours, case_tz):
    local_tz = ZoneInfo(case_tz)
    flagged = []
    for path in csv_paths:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                name = first_value(row, ["Name", "File"])
                location = first_value(row, ["Location", "File Path"])
                times = {
                    kind: parse_time(first_value(row, cols), offset_hours)
                    for kind, cols in TIME_COLUMNS.items()
                }
                reasons = []

                if "$CarvedFiles" in location:
                    reasons.append("carved from unallocated space")

                if not name.startswith("$") and all(t is None for t in times.values()):
                    reasons.append("no usable timestamps")

                # accessed time is date-only on FAT, so it is not checked here
                for kind in ("modified", "created"):
                    t = times[kind]
                    if t is not None:
                        local = t.astimezone(local_tz)
                        if local.hour < 6:
                            reasons.append(f"{kind} at odd hour ({local.strftime('%H:%M')} local)")

                mime = row.get("MIME Type", "").strip()
                ext = row.get("Extension", "").strip().lower()
                expected = EXPECTED_MIME.get(ext)
                if expected and mime and mime != expected:
                    reasons.append(f"extension .{ext} but content type {mime}")

                if reasons:
                    flagged.append({
                        "name": name,
                        "path": location,
                        "size": row.get("Size", ""),
                        "md5": row.get("MD5 Hash", ""),
                        "reasons": "; ".join(reasons),
                        "source_csv": os.path.basename(path),
                    })
    return flagged


def write_flags(flagged, out_path):
    fields = ["name", "path", "size", "md5", "reasons", "source_csv"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flagged)


def main():
    parser = argparse.ArgumentParser(description="EvidenceLens")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hash = sub.add_parser("hash", help="hash an evidence file and log it")
    p_hash.add_argument("file")
    p_hash.add_argument("--log", default="custody_log.csv")

    p_tl = sub.add_parser("timeline", help="merge Autopsy CSV exports into one timeline")
    p_tl.add_argument("csv_files", nargs="+")
    p_tl.add_argument("--out", default="timeline.csv")
    p_tl.add_argument("--source-offset", type=float, default=4,
                      help="UTC offset (hours) of the times in the Autopsy export; GST = 4")
    p_tl.add_argument("--case-tz", default="America/Chicago")

    p_fl = sub.add_parser("flag", help="flag suspicious entries in Autopsy CSV exports")
    p_fl.add_argument("csv_files", nargs="+")
    p_fl.add_argument("--out", default="flags.csv")
    p_fl.add_argument("--source-offset", type=float, default=4)
    p_fl.add_argument("--case-tz", default="America/Chicago")

    args = parser.parse_args()
    if args.command == "hash":
        row = hash_evidence(args.file, args.log)
        for key, value in row.items():
            print(f"{key}: {value}")
    elif args.command == "timeline":
        events = build_timeline(args.csv_files, args.source_offset, args.case_tz)
        write_timeline(events, args.out)
        print(f"{len(events)} events written to {args.out}")
    elif args.command == "flag":
        flagged = flag_files(args.csv_files, args.source_offset, args.case_tz)
        write_flags(flagged, args.out)
        print(f"{len(flagged)} entries flagged, written to {args.out}")


if __name__ == "__main__":
    main()