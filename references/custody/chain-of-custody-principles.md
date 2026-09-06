# Chain of Custody Principles

This document outlines the foundational principles of the Chain of Custody (CoC) as it applies specifically to digital evidence. It defines the conceptual framework required to document the lifecycle of a digital artifact from the exact moment of acquisition, through analysis and storage, to its final disposition, ensuring its integrity remains unquestioned by any party.

## Why it matters

The Chain of Custody is the chronological documentation or paper trail that records the sequence of custody, control, transfer, analysis, and disposition of physical or electronic evidence. In legal and forensic contexts, if the chain of custody is broken—meaning there is an undocumented gap in time where the evidence cannot be accounted for—the opposing counsel can argue that the evidence may have been tampered with, swapped, or altered. For digital evidence, where alteration leaves no physical marks, cryptographic hashing and rigorous documentation are the only mechanisms available to prove that the file presented in court is the exact same file seized at the scene.

## Core Principles

### 1. Cryptographic Baseline (The Digital Fingerprint)
Unlike a physical gun in an evidence bag, a digital file can be cloned. The Chain of Custody for digital evidence relies on generating a cryptographic hash (preferably SHA-256) at the earliest possible moment of acquisition. This hash acts as the digital fingerprint. Every subsequent transfer of the evidence must include a verification of this hash.

### 2. Comprehensive Documentation
Every interaction with the evidence must be logged in a detailed manner. A proper CoC log for a digital artifact must include:
*   **Who:** The specific operator interacting with the data.
*   **What:** The exact cryptographic hash of the files involved.
*   **When:** The precise, verified time of the interaction (ideally anchored by a TSA or OpenTimestamps).
*   **Where:** The physical and network locations (e.g., copied from Field Laptop A to Secure Server B).
*   **Why:** The purpose of the interaction (e.g., "Copied for malware analysis in isolated sandbox").

### 3. Work on Copies, Never Originals
The most critical rule of digital forensics is to never conduct analysis on the original evidence. The original physical media or the primary digital acquisition must be hashed, locked in WORM storage, and secured. All subsequent processing, metadata extraction, and redaction must be performed on bit-for-bit verified copies. 

### 4. Secure and Verifiable Transfer
When digital evidence is moved between entities (e.g., from an investigator to a prosecutor), the transfer must be structurally sound. This means utilizing standardized packaging formats like BagIt, which encapsulate the data, the metadata, and the cryptographic manifests into a single logical unit, allowing the recipient to instantly mathematically verify the entire package upon receipt.

### 5. Documenting the Environment
Digital evidence does not exist in a vacuum. The CoC must document the tools used to acquire and process the data. Noting that a hard drive was imaged using `dd` on macOS version 14.2, or that hashes were generated using `shasum -a 256`, provides necessary context for future auditors who may need to replicate the process or understand potential tool-specific idiosyncrasies.

## Pitfalls

*   **Delayed Hashing:** Waiting to hash files until they are uploaded to the cloud creates a massive window of vulnerability where files could be altered by local malware, user error, or failing hardware without detection. Hash immediately at the point of capture.
*   **Assuming Cloud Storage Logs are Sufficient:** Relying solely on a cloud provider's internal access logs (like AWS CloudTrail) is dangerous. While useful, these logs do not provide cryptographic proof of file integrity, only network access history. They augment, but do not replace, the cryptographic manifest.
*   **Poorly Defined Handoffs:** When evidence is emailed, placed on a generic shared network drive, or handed over on an unencrypted USB stick without a signed manifest receipt, the chain is broken. Handoffs must be explicit and verified by both parties.
*   **Ignoring Metadata Spoliation:** Opening an original evidence document in Microsoft Word to "read it" will alter the file's internal "Last Accessed" and "Last Modified" metadata, changing its cryptographic hash and severely compromising the evidence. Always use read-only viewers on copies.

## See also

*   [Algorithms and Manifests](../hashing/algorithms-and-manifests.md)
*   [BagIt Standard](../packaging/bagit.md)
*   [WORM and Object Lock](../storage/worm-and-object-lock.md)

## Advanced Operational Scenarios

### Zero-Trust Handoffs
In adversarial environments, no transfer of evidence can be assumed safe. When an operator hands off a digital evidence package (e.g., a BagIt archive) to another department, a Zero-Trust handoff protocol must be executed. This means the receiving operator physically sits with the transferring operator, independently calculates the SHA-256 hashes on their own isolated workstation, and signs a digital receipt proving that the hashes matched before the transferring operator leaves the room.

### Multi-Signature Disposition
The final destruction of digital evidence (disposition) is the most critical phase of the lifecycle. A single rogue operator could maliciously delete evidence to sabotage a case. To prevent this, advanced CoC systems implement multi-signature requirements. Before a WORM lock can be lifted (if in Governance mode) or a storage array wiped, the system technically requires the independent digital signatures of at least two authorized personnel (e.g., the Lead Investigator and the Legal Counsel) to authorize the destructive action.

### The Role of Automation
Modern CoC logs are no longer physical clipboards. They are automated, cryptographically signed ledger entries. When a script executes `rclone` to move evidence, the script itself should automatically generate a JSON-formatted log entry containing the timestamp, the user ID, the file hashes, and the exact command executed, and immediately commit that log to an append-only, immutable database, removing human error from the documentation process.

## The Role of Evidence Lockers (Digital and Physical)
Even digital evidence requires physical security. The hard drives, USB tokens, or hardware security modules (HSMs) storing the digital artifacts must be physically secured.
*   **Access Control Logs:** The physical door to the server room or the evidence locker must have its own chain of custody (e.g., RFID badge swipes, biometric logs). If the physical access log contradicts the digital CoC log (e.g., the digital log says Operator B hashed the file at 2 AM, but the physical log shows Operator B wasn't in the building), the entire evidence chain is compromised.
*   **Faraday Isolation:** When acquiring mobile devices, the physical CoC must document the use of Faraday bags. If a device is seized but left connected to the cellular network, the defense will argue that the suspect or a remote actor could have remotely wiped or altered the device's contents while it was in police custody.

## Disposition and Destruction
The Chain of Custody does not end when the trial is over. It ends when the evidence is formally destroyed.
*   **Legal Mandates:** Many jurisdictions mandate the return or destruction of seized data (especially PII) once the legal mandate for its retention expires.
*   **Cryptographic Wiping:** Deleting the file or lifting the WORM lock is insufficient. The storage media must be cryptographically wiped (e.g., DoD 5220.22-M standard or ATA Secure Erase) and this exact wiping process, along with the verifying operator's signature, forms the absolute final entry in the CoC log.

## Glossary of Terms
*   **Disposition:** The final stage of the evidence lifecycle, typically resulting in the permanent, cryptographically secure destruction of the data once all legal holds are released.
*   **Spoliation:** The intentional or negligent withholding, hiding, altering, or destroying of evidence relevant to a legal proceeding.
*   **Hash Collision:** A situation where two different inputs produce the exact same cryptographic hash output, a theoretical risk that necessitates the use of modern algorithms like SHA-256 over MD5.
*   **Faraday Bag:** A physical enclosure used to block electromagnetic fields, preventing a seized mobile device from connecting to cellular or Wi-Fi networks and receiving remote wipe commands.
*   **Air-Gap:** A physical security measure where a secure computer network is physically isolated from unsecured networks, such as the public Internet or an unsecured local area network.

## Frequently Asked Questions
**Q: Can a broken Chain of Custody be repaired?**
A: Generally, no. A broken chain introduces reasonable doubt. If you cannot mathematically prove where a file was between Tuesday and Thursday, any claim that it wasn't altered during that window is speculative and vulnerable in court.

**Q: Does encrypting the evidence drive break the Chain of Custody?**
A: No, encryption is encouraged for transport security. The Chain of Custody relies on the hashes of the plaintext evidence files inside the encrypted volume, not the ciphertext. You document the encryption tool (e.g., FileVault or LUKS) and the key exchange mechanism in the CoC log.

**Q: What is the most common failure point?**
A: Simple human error during file transfer, such as dragging and dropping via a GUI instead of using a hashing transfer tool, silently altering the filesystem timestamps.
