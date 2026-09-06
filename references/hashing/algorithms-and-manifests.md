# Cryptographic Algorithms and Manifests

This guide details the selection of cryptographic hash functions and the structuring of manifest files when handling digital evidence. It provides operators with standard practices for generating collision-resistant identifiers for datasets, allowing later validation to mathematically confirm that no bits have flipped or been tampered with since the moment of acquisition.

## Why it matters

Hash values serve as the digital fingerprints of your evidence. A cryptographic manifest is a mathematical guarantee of a dataset's state at a specific point in time. If the chosen algorithm is cryptographically weak (such as MD5 or SHA-1), well-resourced malicious actors might theoretically engineer a collision, substituting tampered evidence that produces the exact same hash. Furthermore, if the manifest format is non-standard, automated ingestion tools will fail to parse it, disrupting the chain of custody, causing systemic verification failures, and potentially rendering the evidence unusable in formal legal settings.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `shasum` | macOS / Linux | The primary tool for generating SHA-256 hashes on macOS. Ships natively and is standard. |
| `b3sum` | both | High-speed BLAKE3 hashing utility. Must be installed via a package manager. |
| `sha256sum` | Linux | GNU coreutils standard for SHA-256. Not natively available on macOS. |
| `md5` | macOS | Legacy BSD utility. Included only for mandatory compatibility with older requirements. |

## Practical recipes

### Generating a standard SHA-256 manifest
The baseline standard for modern digital evidence is SHA-256. On macOS, this is accomplished using the `-a 256` flag with the native `shasum` utility. Do not use GNU-specific commands natively.

```bash
# macOS and Linux (standardized cross-platform approach)
# Generate a manifest for all files in an evidence directory
find ./evidence-drive -type f -exec shasum -a 256 {} + > evidence_manifest.sha256
```

### Validating a manifest
To check files against an existing manifest, the tool must read the expected hash from the text file, re-calculate the hash of the target physical file, and compare them.

```bash
# Verify the manifest against the current files
shasum -a 256 -c evidence_manifest.sha256
```

### High-throughput hashing with BLAKE3
When processing massive datasets (terabytes of video or full disk images) where SHA-256 constitutes an unacceptable CPU bottleneck, BLAKE3 provides superior cryptographic security at much higher speeds. The `b3sum` binary must be installed first. Note that speed is dependent on underlying disk IO. Measure on your own data before assuming hashing is the primary bottleneck.

```bash
# macOS (installation via Homebrew)
brew install b3sum

# Generate a BLAKE3 manifest for a massive dataset
find ./massive-dataset -type f -exec b3sum {} + > dataset.b3

# Verify the BLAKE3 manifest
b3sum -c dataset.b3
```

### Handling legacy requirements
If an older protocol or legacy ingestion system requires MD5, use it alongside a modern algorithm. Never rely on MD5 as the sole proof of integrity for new evidence. Ensure macOS outputs a GNU-compatible format.

```bash
# macOS - Outputting GNU-compatible format for legacy ingestion
md5 -r ./legacy-evidence.img > legacy-evidence.md5
```

## Pitfalls

*   **Relying on deprecated algorithms:** Never use MD5 or SHA-1 as the sole cryptographic proof for new evidence collections due to well-documented collision vulnerabilities.
*   **Assuming Linux tooling:** Scripts containing `sha256sum` will fail out of the box on macOS. Always default to `shasum -a 256` for cross-platform compatibility.
*   **Pathing issues in manifests:** Absolute paths in manifests (e.g., `/Users/admin/evidence/file.txt`) will fail validation when the directory is moved or processed on another machine. Always run hashing commands from a relative root directory.
*   **File permission errors:** Attempting to hash a directory without proper read access will silently skip files if standard error output is suppressed. Always review stderr or ensure proper privileges.
*   **Encoding problems:** Manifests generated with unexpected text encodings (UTF-16 vs UTF-8) or unusual newline characters can cause validation failures when processed on different operating systems.
*   **Assuming throughput guarantees:** Do not invent or guess hash speeds; always measure on your own data. Storage IO is frequently the actual bottleneck rather than CPU hashing performance.

## See also

*   [macOS vs Linux Tooling](macos-vs-linux-tooling.md)
*   [BagIt Standard](../packaging/bagit.md)
*   [Chain of Custody Principles](../custody/chain-of-custody-principles.md)

## Advanced Operational Scenarios

### Parallel Hashing for Massive Datasets
When dealing with multi-terabyte evidence drives (e.g., full disk images from a RAID array), single-threaded hashing algorithms like SHA-256 will bottleneck the acquisition process. Operators should utilize parallel hashing strategies where appropriate. While `b3sum` handles this natively for BLAKE3, if SHA-256 is required, operators can chunk the files and pipe them through parallel utilities like `xargs -P` or GNU `parallel`.

### Handling Hash Collisions
While a SHA-256 collision has never been publicly demonstrated, legacy systems still relying on MD5 or SHA-1 frequently encounter intentional collisions (e.g., SHAttered attack). If an operator receives a legacy dataset with MD5 manifests and suspects tampering, they must immediately re-hash the entire dataset using SHA-256 and cross-reference the file structures using byte-level differential analysis to confirm the payload's integrity before proceeding.
