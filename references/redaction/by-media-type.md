# Redaction by Media Type

This document defines the strict methodologies required for the secure redaction and sanitization of digital evidence prior to public release, legal discovery, or inter-agency sharing. It addresses the different techniques required for plain text, complex documents, images, and audio/video streams, emphasizing the physical removal of data over superficial visual masking.

## Why it matters

Improper redaction is a catastrophic operational failure. Drawing a black box over text in a standard PDF editor often only modifies the visual presentation layer; the underlying text remains selectable, searchable, and extractable. Similarly, cropping an image in a modern non-destructive photo editor often leaves the original pixel data intact in the file history, allowing the crop to be easily reversed by a malicious recipient. True redaction requires the irreversible destruction of the target data, meaning the physical bits must be overwritten, rasterized, or stripped from the file container.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `mat2` | both | The Metadata Anonymisation Toolkit. Essential for stripping metadata across all file types. |
| `qpdf` | both | Used to analyze PDF structures and ensure text layers are truly removed. |
| `pdftotext` | both | Used to verify that redacted text is no longer machine-readable. |
| `ffmpeg` | both | The primary engine for re-encoding and explicitly destroying cropped/blurred audio and video data. |

## Practical recipes

### Plain Text and Markdown
Redacting plain text (`.txt`, `.md`) is straightforward as there are no hidden layers. Replace the sensitive data with explicit markers (e.g., `[REDACTED]`).

```bash
# Basic stream editing for redaction (ensure you output to a new file)
sed 's/Confidential Informant/\[REDACTED\]/g' statement.txt > statement_redacted.txt
```

### The Iron Rule of PDF Redaction
Text-layer PDF redaction (drawing black boxes in a PDF editor) is NOT visual redaction. True visual redaction requires either a specialized, purpose-built redaction tool (like Adobe Acrobat's explicit "Sanitize" and "Apply Redaction" features) or full rasterisation.

If you lack a trusted PDF redaction tool, the only mathematically secure fallback is rasterising the document to images, burning the black boxes into the pixels, and then recombining them into a new PDF.

```bash
# Verify a PDF is redacted by attempting to extract the text
pdftotext purportedly_redacted.pdf verify_text.txt
grep -i "Sensitive Term" verify_text.txt
```
*If the grep command finds the term, the redaction failed and merely masked the text visually.*

### Images: Reversible Cropping
Cropping or blurring an image on a smartphone or in a tool like Apple Preview often saves the edit non-destructively, embedding the original image in the EXIF MakerNotes or as a secondary hidden layer. To guarantee a crop is permanent, you must export the image to a flat format, stripping all metadata.

```bash
# Strip all metadata from an image after cropping/blurring to ensure the original is not hidden inside
mat2 --inplace cropped_evidence.jpg
```

### Video and Audio Redaction
Applying a blur to a face in a video editor and saving the project file does not redact the source footage. The video must be re-encoded, meaning the blurred pixels are baked into a brand new video stream, and the original file is excluded from the transfer.

```bash
# Example: stripping the audio track entirely from a video to redact spoken names
ffmpeg -i interview.mp4 -c:v copy -an interview_no_audio.mp4
```

### Universal Metadata Scrubbing
Before any redacted file is shared, its metadata must be scrubbed. Office documents (`.docx`), PDFs, and media files often contain author names, revision histories, and original unredacted thumbnails.

```bash
# Safely scrub metadata from all files in a directory using mat2
mat2 ./redacted_exports/*
```

## Pitfalls

*   **The Black Highlighter Fallacy:** Drawing black lines over text in a standard PDF viewer or word processor is purely cosmetic. The underlying text string remains fully intact in the document structure.
*   **Non-Destructive Edits:** Modern OS photo apps (like iOS Photos) allow users to "Revert to Original" after an edit. Sharing the file directly from the device often sends the unredacted original alongside the edit instructions. Always export and strip using `mat2`.
*   **Revision History Leaks:** Microsoft Office documents maintain deep revision histories. If you delete a sensitive paragraph and hit save, the deleted text may still be recoverable from the file's internal XML structure. Always export to a flattened PDF and rasterize, or use the "Inspect Document" sanitization tools.
*   **Unintended Metadata Spillage:** Redacting a video by blurring a face, but leaving the GPS coordinates of the safehouse embedded in the `.mp4` container, defeats the purpose of the redaction. Total sanitization requires addressing both the payload and the metadata.

## See also

*   [ExifTool Guide](../metadata/exiftool.md)
*   [Anomaly Signals](../metadata/anomaly-signals.md)

## Advanced Operational Scenarios

### Audio Spectral Redaction
Muting the audio track to redact a sensitive conversation is often insufficient. if the background noise (e.g., a siren, a distinct machine hum) is legally critical, a flat mute destroys the surrounding context. advanced operators utilize spectral audio editing tools (like izotope rx) to visually isolate the specific frequency bands of the spoken words and delete only those vocal frequencies, leaving the ambient background noise intact and unredacted.

### Defeating OCR and AI Reconstruction
When rasterizing text to redact it, drawing a black box over the pixels is no longer sufficient against advanced adversaries. Modern AI reconstruction models can sometimes infer the redacted text by analyzing the microscopic pixel bleeding around the edges of the redaction box or the exact width of the redacted space. Operators must add "noise" to the rasterized redaction box and scramble the surrounding pixel boundaries to mathematically defeat advanced Optical Character Recognition (OCR) and AI inference attacks.
