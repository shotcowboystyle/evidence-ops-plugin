# OpenTimestamps Evidence Validation

This document outlines the use of OpenTimestamps (OTS) for creating decentralized, cryptographically verifiable proofs of existence for digital evidence. It covers how an operator can anchor a file's hash to the Bitcoin blockchain to prove that the file existed prior to a specific block confirmation, without relying on a centralized authority.

## Why it matters

Traditional timestamps typically rely on a central authority's clock (such as a local file system clock or a managed Time Stamping Authority server). If that central authority is compromised, goes offline, or its private keys are leaked, the timestamp is rendered invalid or suspect. OpenTimestamps provides a trustless alternative by embedding the hash of the evidence into the Bitcoin blockchain via a Merkle tree structure. This mathematical proof is globally verifiable, immutable, and removes the need to trust any single party, vendor, or infrastructure. It provides an exceptionally strong defense against claims of evidence backdating or subsequent fabrication by opposing parties.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `ots` | both | The OpenTimestamps client (`opentimestamps-client`). Installed via Python's `pip`. |
| `shasum` | macOS / Linux | Used for preliminary hashing before timestamping to ensure absolute privacy. |
| `bitcoin-cli` | both | Optional. Used for local validation against a full node instead of relying on public calendars. |

## Practical recipes

### Installing the client
The `opentimestamps-client` is Python-based. Ensure you are operating within an appropriate virtual environment or user space to avoid polluting the system Python installation.

```bash
# macOS and Linux
pip3 install opentimestamps-client
```

### Stamping a file
To create a timestamp, you submit the file to the OTS calendar servers. This generates a `.ots` file containing the cryptographic path (the "pending" timestamp) leading up to the server.

```bash
# Create a timestamp for a manifest
ots stamp evidence_manifest.sha256

# The command above produces the sidecar file: evidence_manifest.sha256.ots
```

### Upgrading a timestamp
Initial timestamps are "pending" until the calendar servers aggregate the hashes and submit them in a Bitcoin transaction that gets mined into a block. You must "upgrade" the `.ots` file a few hours later to retrieve the final blockchain proof and complete the path.

```bash
# Upgrade the pending timestamp to a complete proof
ots upgrade evidence_manifest.sha256.ots
```

### Verifying a timestamp
To prove the file existed at the time of the block, verify the upgraded `.ots` file against the original evidence file. This verifies the complete Merkle path down to the block header.

```bash
# Verify the timestamp against the file
ots verify evidence_manifest.sha256.ots -f evidence_manifest.sha256
```

### Info and inspection
You can inspect the contents of an OTS file to see the exact cryptographic path, the calendar servers involved, and the Bitcoin transaction ID that anchors the proof.

```bash
# Inspect the timestamp details
ots info evidence_manifest.sha256.ots
```

## Pitfalls

*   **Losing the original file:** The `.ots` file only contains the cryptographic proofs, not the file data itself. If `evidence_manifest.sha256` is altered by even one single byte, the OTS verification will fail completely.
*   **Forgetting to upgrade:** Failing to run `ots upgrade` after the Bitcoin block is mined leaves you reliant on the calendar server's temporary attestation, defeating the purpose of the blockchain anchor. Always script an automated upgrade routine.
*   **Privacy leaks:** While OTS only uploads the hash (not the file contents), ensure you are stamping a generic manifest or an opaque hash, rather than a file whose exact size/hash combination could inadvertently leak sensitive information if matched against a known database.
*   **Time resolution constraints:** Bitcoin block times average roughly 10 minutes. OTS proves a file existed *before* the block was mined, not the precise second it was created. It provides an upper-bound timestamp, not a high-resolution, second-accurate one.
*   **Network dependencies:** The `ots stamp` command requires internet access to reach the calendar servers. Completely air-gapped forensic workstations cannot stamp files natively without proxying the hashes out.

## See also

*   [RFC 3161 TSA](rfc3161-tsa.md)
*   [Algorithms and Manifests](../hashing/algorithms-and-manifests.md)
*   [Chain of Custody Principles](../custody/chain-of-custody-principles.md)

## Advanced Operational Scenarios

### Handling Prolonged Mempool Congestion
During periods of extreme Bitcoin network congestion, a transaction containing the OTS commitments might remain in the mempool (unconfirmed) for days. If an operator requires an immediate, court-ready proof, OTS will be insufficient during this gap. In these scenarios, operators must dual-stamp the evidence: utilizing OTS for the long-term, decentralized proof, and an RFC 3161 TSA for the immediate, short-term attestation.

### Air-Gapped Timestamping
True forensic workstations are air-gapped from the internet. To use OpenTimestamps in this environment, the operator must generate the SHA-256 hashes locally, export only the hashes via a secure one-way transfer mechanism (like a data diode or a sterilized USB drive) to an internet-connected terminal, run the `ots stamp` process on the hashes, and then import the resulting `.ots` files back into the air-gapped environment.
