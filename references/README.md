# Digital Evidence Plugin Reference Corpus

This reference corpus provides a comprehensive suite of standard operating procedures, tool guides, and conceptual overviews for handling digital evidence. It is intended for operators collecting, preserving, and analyzing digital artifacts, ensuring adherence to forensic best practices and platform-specific constraints. The primary target environment for these operations is macOS (darwin), with specific accommodations provided for GNU/Linux workflows where evidence is moved, processed, or stored in server environments. 

## Why it matters

Digital evidence requires rigorous, error-free handling to maintain its probative value and authenticity. Standardized documentation ensures that all operators use consistent commands, tools, and methodologies across investigations, eliminating variables that opposing counsel could exploit. A single mistake in hashing, timestamping, or packaging can render an entire dataset legally useless or technically corrupted. This corpus serves as the ground truth for the plugin's automated routines and manual operator guidance, ensuring that operations are mathematically verifiable, repeatable, and forensically sound from the moment of acquisition to final disposition.

## Core Principles

The documentation within this corpus is built upon several foundational principles of digital forensics:
1.  **Immutability First:** Evidence should never be altered post-collection. Cryptographic hashing and external timestamping must be prioritized immediately after acquisition to establish a baseline state.
2.  **Platform Awareness:** Differences between macOS (BSD-derived) and Linux (GNU-based) are addressed. Using the wrong hashing tool or `stat` flag can break automated ingestion pipelines.
3.  **Verifiability:** All operations must leave a verifiable audit trail, whether through cryptographic manifests, detailed execution logs, or blockchain signatures.
4.  **Least Privilege Modification:** Tools used for analysis must be invoked in read-only modes whenever possible to prevent accidental spoliation of the original artifact.

## Index of Topics

### Capture
* [Web Pages](capture/web-pages.md) - Techniques for capturing dynamic web content as durable evidence, avoiding common SPA and DOM manipulation pitfalls.
* [Photo and Video Provenance](capture/photo-video-provenance.md) - Understanding modern provenance standards like C2PA, Content Credentials, and device-signed media.

### Custody
* [Chain of Custody Principles](custody/chain-of-custody-principles.md) - Core concepts for maintaining evidential integrity from acquisition, through analysis, to disposition.
* [Legal Considerations](custody/legal-considerations.md) - General overview of legal concepts related to digital evidence, noting that jurisdiction dictates admissibility specifics.

### Hashing
* [Algorithms and Manifests](hashing/algorithms-and-manifests.md) - Best practices for selecting and using cryptographic hashes for collision resistance and ingestion speed.
* [macOS vs Linux Tooling](hashing/macos-vs-linux-tooling.md) - Navigating the differences in hashing utilities across platforms, specifically the absolute reliance on `shasum` on macOS.

### Metadata
* [Anomaly Signals](metadata/anomaly-signals.md) - Identifying suspicious markers in file metadata that warrant deeper technical investigation rather than immediate trust.
* [ExifTool Guide](metadata/exiftool.md) - Using ExifTool for extracting, formatting, and analyzing metadata safely without altering the payload.
* [MediaInfo Guide](metadata/mediainfo.md) - Leveraging MediaInfo for deep multimedia file analysis without trusting superficial file extensions.

### Packaging
* [BagIt Standard](packaging/bagit.md) - Packaging digital evidence using the BagIt specification to ensure massive dataset completeness during network transfer.

### Redaction
* [Redaction by Media Type](redaction/by-media-type.md) - Proper techniques for sanitizing various file formats to prevent inadvertent data leakage through hidden layers.

### Storage
* [rclone Immutable Remotes](storage/rclone-immutable-remotes.md) - Configuring immutable remote storage using rclone for safe off-site backups without risk of accidental syncing/deletion.
* [WORM and Object Lock](storage/worm-and-object-lock.md) - Leveraging Object Lock for compliance, governance, and ransomware protection in cloud storage environments.

### Timestamping
* [OpenTimestamps](timestamping/opentimestamps.md) - Using blockchain-based timestamping for immutable, decentralized evidence validation.
* [RFC 3161 TSA](timestamping/rfc3161-tsa.md) - Utilizing Time Stamping Authority servers for trusted timestamps and traditional regulatory compliance.

## Integration Note
This corpus is original work created specifically for this plugin. It is designed to be searched dynamically by the `reference-lookup` skill via `grep` to assist operators and automated agents in real-time. Do not remove or heavily alter the heading structure without updating the plugin's internal parsing logic, as automated retrieval depends on the consistent layout of these files.

## See also
*   [Chain of Custody Principles](custody/chain-of-custody-principles.md)
*   [macOS vs Linux Tooling](hashing/macos-vs-linux-tooling.md)
*   [Algorithms and Manifests](hashing/algorithms-and-manifests.md)

## Advanced Operational Scenarios

### Multi-Jurisdictional Investigations
When operating across multiple legal jurisdictions, the baseline standards outlined in this corpus must be elevated to meet the most stringent requirements. For example, if a dataset is captured in a jurisdiction that permits basic MD5 hashing but will be analyzed in a jurisdiction mandating SHA-256 and RFC 3161 timestamps, the collection team must default to the higher standard immediately upon acquisition. 

### Automated Ingestion Pipelines
This corpus is designed to be machine-readable by internal CI/CD and MLOps pipelines. Automated evidence ingestion agents use the tool tables and practical recipes to construct their validation scripts. Therefore, any updates to these documents must preserve the strict Markdown formatting (e.g., fenced bash blocks) so that regex parsers can continue to extract the expected command flags without breaking the ingestion logic.

## Tooling Prerequisites
Operators must ensure their environment is properly configured before executing the scripts referenced in this corpus.
On macOS, this typically involves installing Xcode Command Line Tools (`xcode-select --install`) and Homebrew. Certain utilities like `exiftool`, `mediainfo`, `b3sum`, and `mat2` are not native to Darwin and must be maintained via `brew`. Python 3 is required for BagIt and OpenTimestamps. Operating in a contained `virtualenv` is recommended to prevent dependency conflicts with system-level Python.

## Version Control
This reference corpus is heavily version-controlled. Operators must execute a `git pull` before commencing any major forensic operation to ensure they are relying on the most up-to-date methodologies, as cryptographic standards and legal precedents evolve rapidly.

## Glossary of Terms
*   **WORM (Write Once, Read Many):** A data storage method in which information, once written, cannot be modified or deleted until a specific retention period expires.
*   **C2PA:** The Coalition for Content Provenance and Authenticity, the open technical standard defining cryptographic provenance for media.
*   **Object Lock:** A cloud storage feature that implements WORM policies at the API level, preventing even root administrators from altering evidence.
*   **TSA (Time Stamping Authority):** A trusted third party that provides cryptographically secure attestations of time using standard PKI infrastructure.
*   **OpenTimestamps (OTS):** A decentralized architecture for mathematically proving the existence of a file by anchoring its hash into the Bitcoin blockchain.

## Frequently Asked Questions
**Q: Why is there so much emphasis on macOS tooling when our servers run Linux?**
A: Field investigators and initial collection operators primarily use macOS laptops (MacBooks) on-site. If the collection scripts fail on Darwin, the evidence is never properly hashed at the point of origin, breaking the chain before the servers ever touch it.

**Q: Can we replace `shasum` with a faster algorithm internally?**
A: While BLAKE3 (`b3sum`) is recommended for internal throughput, SHA-256 remains the universal legal standard. Always generate a SHA-256 manifest for the official court submission, even if you use BLAKE3 for your internal caching and processing pipelines.
