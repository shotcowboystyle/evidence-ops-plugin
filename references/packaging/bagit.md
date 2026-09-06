# Packaging with BagIt

The BagIt specification (RFC 8493) defines a structured, self-describing directory format for packaging and transferring digital content safely. An operator needs BagIt when bundling a set of evidence files for archival, transfer to another party, or long-term preservation, ensuring that the bundle includes a built-in cryptographic manifest that travels alongside the payload.

## Why it matters

Digital evidence frequently spans multiple files and directories that must stay together to provide full context. Without a standardized container, moving a complex directory structure across file systems or object stores risks silent corruption or missing files. BagIt solves this by isolating the payload in a `data/` directory and placing checksum manifests at the root (such as `manifest-sha256.txt` and `tagmanifest-sha256.txt`), alongside descriptive metadata in `bag-info.txt` and `bagit.txt`. This makes the entire package verifiable as a single logical unit.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `bagit.py` | both | Official Python CLI implementation of the BagIt standard. |
| `shasum` | macOS | macOS native tool for computing hashes. |
| `sha256sum` | Linux | GNU coreutils equivalent for hashing on Linux. |

## Practical recipes

### Creating a bag in place

To convert an existing directory containing evidence into a bag, use `bagit.py`. This moves the existing contents into a `data/` subdirectory and generates the required manifests.

```bash
# Create a bag using SHA-256 for the manifests
bagit.py --sha256 /path/to/evidence_bundle
```

### Adding bag-info metadata

You can embed descriptive metadata directly into `bag-info.txt` during creation. This is useful for recording the handler, case reference, or origin.

```bash
bagit.py --sha256 \
  --contact-name "C. Blanton" \
  --external-identifier "CASE-2026-09-06" \
  --organization "Evidence Ops" \
  /path/to/evidence_bundle
```

### Validating a bag

Validation checks both the structure (ensuring all required files exist in `data/` according to the manifest) and the payload (recomputing hashes and comparing them against `manifest-sha256.txt`).

```bash
bagit.py --validate /path/to/evidence_bundle
```

### Creating holey bags

Holey bags contain the manifests and metadata but omit the actual payload files, providing a `fetch.txt` file with URLs to retrieve the data. This is useful when the metadata needs to be shared or anchored without distributing massive files immediately. 

```bash
# Holey bags are often created programmatically. If generating manually, 
# a fetch.txt line looks like:
# https://storage.example.com/item.pdf 184203 data/item.pdf
# Standard bagit.py focuses on local creation, but validating a holey bag works via:
bagit.py --validate --fast /path/to/holey_bag
```
*(Note: standard `bagit.py` lacks a direct CLI flag for auto-generating `fetch.txt` URLs during creation; this is typically handled by custom archival scripts before validation).*

### Pairing with timestamping

A bag's integrity can be anchored in time by timestamping its tag manifest. Because `tagmanifest-sha256.txt` contains the hash of `manifest-sha256.txt`, which in turn contains the hashes of the payload in `data/`, a single timestamp covers the entire package.

```bash
ots stamp /path/to/evidence_bundle/tagmanifest-sha256.txt
```

## Pitfalls

*   **In-place modification risks:** Running `bagit.py` alters the target directory structure by moving files into `data/`. Do not run this directly on read-only original acquisitions; create the bag from a staged copy.
*   **Hidden files omission:** If tools or scripts build bags manually without `bagit.py`, they sometimes miss hidden files (like `.DS_Store` on macOS), leading to validation failures if those files are moved into the payload but missed in the manifest.
*   **Incomplete validation:** A fast validation (`--fast`) only checks structure and file sizes. Always ensure full payload validation is performed when receiving a bag to prove integrity.
*   **Algorithm mismatches:** Using an algorithm unsupported by the recipient's tools can prevent validation. SHA-256 is the standard baseline; avoid using older algorithms like MD5.

## See also

*   [Algorithms and manifests](../hashing/algorithms-and-manifests.md)
*   [macOS vs Linux tooling](../hashing/macos-vs-linux-tooling.md)
*   [OpenTimestamps](../timestamping/opentimestamps.md)

## Advanced Operational Scenarios

### Updating an Existing Bag (Holey Bags)
Occasionally, an operator needs to add new analysis reports to an already finalized bag. Modifying the `data/` directory directly invalidates the bag. The correct procedure involves creating a "Holey Bag" (using `fetch.txt`) or formally unbagging the evidence, adding the new files, and re-running the complete `bagit.py` process to generate new cryptographic manifests that encompass both the original evidence and the new additions.

### Network Transfer Resiliency
When transferring massive bags over unstable network connections, standard HTTP or FTP transfers often fail, requiring a complete restart. Operators should use robust transfer protocols like `rsync` or cloud-specific multipart upload APIs (e.g., `aws s3 cp`). Because BagIt maintains independent manifests, if the transfer dies halfway, the operator can resume the `rsync` command, and once finished, run `bagit.py --validate` on the destination to confirm the transfer succeeded.
