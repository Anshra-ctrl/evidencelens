# EvidenceLens Case Report: Rhino Hunt (RH-001)

**Author:** Anshra
**Tools:** Autopsy 4.23.1, Python 3.14 (`evidencelens.py`)
**Evidence source:** not recorded (public Rhino Hunt practice case)

> Built by Anshra. I ran the investigation in Autopsy myself and used Claude (an AI assistant) to guide the steps and help write the script.

## 1. Summary

I examined a practice disk image of a USB flash drive (`RHINOUSB.dd`) from the public Rhino Hunt training case. The drive holds two visible text files and 132 files recovered from unallocated space. I bookmarked 5 of the recovered files: four rhino images and one Word document. I then built a small Python tool that logs evidence hashes, merges timestamps into one timeline, and flags files that need a manual look.

## 2. Evidence handling

| Item | Value |
|---|---|
| Image | `RHINOUSB.dd` |
| Size | 259,506,176 bytes |
| Type (per Autopsy) | Flash drive, FAT file system |
| SHA-256 | `ce550424200a997c61b413941c8ef4df9619a2f96579674952294a176a32be65` |
| Hash recorded by hand | 2026-10-29 (PowerShell `Get-FileHash`) |
| Hash re-checked | 2026-10-30 (`evidencelens.py hash`), identical |
| Case time zone | America/Chicago |

- Analysis was done in Autopsy on the image file. The image was opened read-only by Autopsy.
- **Limitation:** I did not record a hash when I first downloaded the image. The baseline hash was taken on 2026-10-29, after Autopsy had opened it. The two later hashes match, so the image was unchanged between 10/29 and 10/30. I cannot show it was unchanged before 10/29.
- Ingest modules included File Type Identification, Extension Mismatch Detector, Embedded File Extractor, Keyword Search, Interesting Files Identifier, PhotoRec Carver, Recent Activity and Hash Lookup.

## 3. Timeline

Autopsy exported times in the computer's zone, which I took to be GST (UTC+4). This is an assumption based on my computer's setting. The script converts them to America/Chicago.

| Local time (Chicago) | Event | File |
|---|---|---|
| 2004-04-30 (date only) | Accessed | gumbo1.txt, gumbo2.txt |
| 2004-04-30 19:11:20 | Modified, created | gumbo1.txt |
| 2004-04-30 19:11:24 | Modified, created | gumbo2.txt |

- FAT stores only a date for access time, so the clock part of those entries is padding and not real.
- All other entries, including the carved files, have no timestamps (`0000-00-00`) and are not in the timeline.
- gumbo1.txt contains a recipe credited to June 2005, but its file dates are in 2004. I did not resolve this. It may be a wrong clock, altered dates, or how the practice case was built.

## 4. Findings

**Visible files.** `gumbo1.txt` and `gumbo2.txt` are plain-text recipes. A hex view of gumbo2.txt showed no hidden data after the text. Autopsy's "METADATA" line at the end of the Text tab comes from the viewer, not from the file.

**Carved files.** PhotoRec recovered 132 files from unallocated space. They have no names, paths or dates. Nine are images (rhino pictures, reptiles, and a hand holding a spotted animal). I bookmarked five items:

| File | Size (bytes) | MD5 | Note |
|---|---|---|---|
| f0105848.jpg | 6,809 | ca03f2eed3db06a82a8a31b3a3defa24 | Photo, adult rhino |
| f0105864.jpg | 230,665 | ed870202082ea4fd8f5488533a561b35 | Photo, rhino with calf |
| f0106320.gif | 11,407 | 76610b7bdb85e5f65e96df3f7e417a74 | Sketch of a rhino |
| f0106344.gif | 4,105 | d03dc23d4ec39e4d16da3c46d2932d62 | Cartoon rhino |
| f0334472_...doc | 30,720 | 68059d3355f0138c9fdd7eaa75e7bc16 | Word document (see below) |

**Recovered Word document.** Most of the text is unrelated personal writing mixed in from other fragments. The last paragraph discusses rhino pictures, says a small number of photos is "no big deal," and describes wiping a hard drive, discarding it in a river, and planning to reformat a USB key. Because the text was carved from unallocated space, it has no author, date or file name. It does not prove who wrote it or when.

## 5. Tool: EvidenceLens

`evidencelens.py` has three commands:

- `hash`: SHA-256 of an evidence file, appended to `custody_log.csv`
- `timeline`: merges Autopsy CSV exports into one sorted timeline, converts to the case time zone, skips `0000-00-00` dates
- `flag`: marks carved files, files with no timestamps, odd-hour timestamps, and extension/content-type mismatches

Sample outputs are in `sample_output/`. Flags are a screening aid. A carved file is not suspicious by itself, it only means "check this by hand." On this case the flag list was the 5 bookmarked carved files, because only those were exported.

## 6. Limitations

- No hash from before analysis began.
- Source time zone (GST) was inferred, not confirmed.
- Only the 5 bookmarked files were screened by the tool, not all 132 carved files.
- Carved content cannot be tied to a person or date.

## 7. Conclusion

The drive's contents and the recovered text are consistent with the Rhino Hunt scenario of someone handling rhino images and trying to remove evidence, but the carved material alone cannot establish who did what or when. A stronger conclusion would need dated artifacts, which this image largely lacks.

## Reproduce

1. Obtain `RHINOUSB.dd` from the public source above. It is not included in this repository.
2. Open it in Autopsy, set the time zone, and export the file listing as CSV.
3. Run `python evidencelens.py hash <image>`, then `timeline` and `flag` on the CSV exports.
