# EvidenceLens

A digital forensics case and a small Python tool, built on the public **Rhino Hunt** practice case.

I examined a USB flash drive image in Autopsy, recovered 132 files from unallocated space, and wrote a tool to make the work repeatable.

**Read the case report:** [REPORT.md](REPORT.md) (also as [REPORT.pdf](REPORT.pdf))

## What the tool does

`evidencelens.py` has three commands:

| Command | What it does |
|---|---|
| `hash` | SHA-256 of an evidence file, appended to a chain-of-custody log |
| `timeline` | Merges Autopsy CSV exports into one sorted timeline, converted to the case time zone |
| `flag` | Marks carved files, files with no timestamps, odd-hour timestamps, and extension mismatches |

Example output is in [`sample_output/`](sample_output/).

## Usage

```
pip install tzdata
python evidencelens.py hash path\to\image.dd
python evidencelens.py timeline export1.csv export2.csv --out timeline.csv
python evidencelens.py flag export1.csv export2.csv --out flags.csv
```

Autopsy exports times in the computer's time zone. Use `--source-offset` to set the UTC offset of your export (default 4).

## Notes

- The evidence image is not included. It comes from a public training dataset, so get it from the original source.
- Flags are a screening aid, not findings. A carved file is not suspicious by itself.
- Only public practice data is used. No real person's data.

## Author

Anshra. I ran the investigation in Autopsy myself and used Claude (an AI assistant) to guide the steps and help write the script.
