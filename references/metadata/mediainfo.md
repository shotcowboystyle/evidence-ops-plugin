# MediaInfo for Container and Stream Analysis

MediaInfo is a specialized utility for analyzing the technical characteristics, container structures, and multiplexed streams of audio and video files. An operator needs MediaInfo when examining multimedia evidence to understand the precise codecs used, bitrates, channel layouts, and container-level metadata that general tools might overlook or misinterpret.

## Why it matters

Video and audio files are complex wrappers (containers) holding encoded tracks (streams). An anomaly in how these layers interact—such as a container timestamp radically differing from a stream timestamp, or a codec profile that the alleged recording device does not support—is a primary signal for investigation. MediaInfo dissects these layers cleanly, separating container facts from stream realities so analysts can trace the file's encoding history.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `mediainfo` | both | Dedicated multimedia metadata extractor. |
| `ffprobe` | both | Companion tool from ffmpeg suite for deep stream-level frame analysis. |

## Practical recipes

### Basic and full inspection

By default, MediaInfo provides a abbreviated summary. The `--Full` flag reveals all extracted parameters, which is mandatory for forensic inspection.

```bash
# Basic summary (often insufficient for evidence)
mediainfo /path/to/video.mp4

# Full technical extraction
mediainfo --Full /path/to/video.mp4
```

### Structured output

JSON is preferred for custody logs, automated anomaly detection, and cross-referencing against ExifTool output.

```bash
mediainfo --Output=JSON --Full /path/to/video.mp4 > video_metadata.json
```

### Inspecting specific layers

MediaInfo categorizes data into General (container), Video, Audio, Text (subtitles), and Menu. You can query these individually to separate container reporting from stream reporting.

```bash
# View only the General (container) metadata
mediainfo --Inform="General" /path/to/video.mp4

# View only the Video stream metadata
mediainfo --Inform="Video" /path/to/video.mp4
```

### Tracking encoded vs. tagged dates

Pay strict attention to the difference between encoded dates (when the stream was generated) and tagged dates (when the container was last updated). 

```bash
# Example extraction focusing on dates using standard grep against full output
mediainfo --Full /path/to/video.mp4 | grep -i "date"
```

### Pairing with ffprobe

While MediaInfo excels at container and header metadata, `ffprobe` is necessary to inspect individual frames, packet structures, or dynamic stream details that MediaInfo abstracts away.

```bash
# Use ffprobe to show detailed per-stream characteristics in JSON
ffprobe -v quiet -print_format json -show_streams /path/to/video.mp4
```

## Pitfalls

*   **Confusing container and stream:** A file might have an `.mp4` container with an encoded date of today, but hold an `h264` stream encoded years ago. Failing to read the stream metadata misses the history.
*   **Over-relying on tagged dates:** "Tagged date" is easily rewritten by basic editing software when saving a project, and does not reliably indicate the actual moment of capture.
*   **Format ambiguity:** Some raw streams (like elementary `.h264` files) lack containers entirely, causing MediaInfo to report sparse data. 
*   **Performance metrics estimation:** Do not invent statistics or assume a specific processing cost. Measure on your own data when running MediaInfo against large directories of massive video files.

## See also

*   [ExifTool](exiftool.md)
*   [Anomaly Signals](anomaly-signals.md)
*   [Photo and video provenance](../capture/photo-video-provenance.md)

## Advanced Operational Scenarios

### Detecting Frame Rate Manipulation
A sophisticated deepfake or manipulated video might seamlessly alter the visual content, but the attacker might accidentally export the final video at a subtly different frame rate (e.g., exactly 30.000 fps instead of the smartphone standard 29.970 fps). MediaInfo's precision frame rate extraction allows operators to immediately flag these microscopic discrepancies, providing the technical basis for a full forensic frame-by-frame analysis.

### Validating Audio Stream Properties
When dealing with purported wiretap or covert recording evidence, the audio stream properties must exactly match the known capabilities of the recording device. If a device is only physically capable of recording 16-bit mono audio at 8kHz, but MediaInfo reveals the evidence file contains a 24-bit stereo stream at 48kHz, the operator can prove the audio was re-encoded, upscaled, or fabricated in a digital audio workstation.
