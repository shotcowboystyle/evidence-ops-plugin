# ExifTool for Metadata Inspection

ExifTool is a command-line application used to read, write, and edit embedded metadata across a vast array of file formats. An operator needs ExifTool to thoroughly investigate the provenance of digital evidence, extracting device details, timestamps, and application histories from images, PDFs, videos, and documents without altering the file's visible content.

## Why it matters

Embedded metadata carries the hidden history of a file. It can corroborate a stated timeline, reveal the software used to manipulate a document, or expose the precise GPS coordinates where an image was captured. Because metadata structures are complex and often deeply nested, a robust parser is mandatory to extract these facts accurately and safely. ExifTool provides consistent, scriptable access to these nested facts.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `exiftool` | both | The industry standard for metadata extraction. |

## Practical recipes

### Reading all tags with group names

To get a comprehensive view, instruct ExifTool to show duplicate tags (`-a`) which might otherwise be hidden, include the metadata group name (`-G1`), and preserve the internal structure (`-struct`).

```bash
exiftool -a -G1 -struct /path/to/evidence.jpg
```

### Formatting output

For script parsing or human readability, output format can be heavily controlled.

```bash
# Short output (tag names and values only, no verbose descriptions)
exiftool -s -s /path/to/evidence.pdf

# JSON output for structured logging and piping to jq
exiftool -j -a -G1 /path/to/evidence.jpg > evidence_metadata.json

# Batch export to CSV for a whole directory, recursively (-r)
exiftool -csv -r /path/to/evidence_folder > batch_metadata.csv
```

### Extracting specific elements

Isolating specific data blocks helps when dealing with massive metadata payloads.

```bash
# Extract GPS coordinates specifically
exiftool -a -gps:all /path/to/evidence.jpg

# Extract embedded thumbnails to a binary file (-b)
exiftool -b -ThumbnailImage /path/to/evidence.jpg > thumbnail.jpg
```

### Stripping and writing tags (Working Copies Only)

**CRITICAL RULE:** Never strip or modify metadata on an original acquisition. Only apply these commands to derived working copies. When redacting metadata before disclosure, you must operate on a copy.

```bash
# Strip all standard metadata from a working copy
exiftool -all= /path/to/working_copy.jpg

# ExifTool automatically creates an '_original' backup (e.g., working_copy.jpg_original).
# To overwrite the file in place without creating a backup, use:
exiftool -all= -overwrite_original /path/to/working_copy.jpg
```

### Copying tags between files

Useful when restoring baseline metadata to a redacted derivative, though this must be meticulously documented in the custody log.

```bash
exiftool -TagsFromFile /path/to/source.jpg /path/to/destination.jpg
```

## Pitfalls

*   **Modifying originals:** Using `-overwrite_original` on the `originals/` directory destroys evidence integrity permanently. Always work on `derived/` files.
*   **Assuming completeness:** Some proprietary maker notes or encrypted metadata blocks may not be fully parsed by ExifTool, leaving hidden data behind even after a strip operation.
*   **Trusting metadata implicitly:** EXIF data is trivial to spoof. It is a claim made by the file, not cryptographic proof of origin.
*   **Duplicate tag masking:** Without the `-a` flag, ExifTool hides duplicate tags. A malicious actor might inject a duplicate timestamp that an incomplete read fails to surface.

## See also

*   [MediaInfo](mediainfo.md)
*   [Anomaly Signals](anomaly-signals.md)
*   [Redaction by media type](../redaction/by-media-type.md)
*   [Photo and video provenance](../capture/photo-video-provenance.md)

## Advanced Operational Scenarios

### Bulk Metadata Correlation
In investigations involving thousands of photos, manually reviewing ExifTool output is impossible. Operators must script ExifTool to extract specific pivoting tags (e.g., `GPSPosition`, `CreateDate`, `SerialNumber`) into a unified CSV. This CSV is then ingested into a data visualization tool like Maltego or a SIEM platform like Splunk to geographically map the evidence and identify exactly when and where a specific device was operating.

### Dealing with Corrupted MakerNotes
Proprietary MakerNotes are notoriously fragile. A simple rotation in an older image viewer can corrupt the MakerNote offsets, causing ExifTool to throw severe warnings. When this occurs, an operator must carefully determine if the corruption is the result of malicious tampering or just a badly written software library. Hexadecimal analysis of the EXIF block is often required to manually extract the fragmented data that ExifTool's automated parser skipped.
