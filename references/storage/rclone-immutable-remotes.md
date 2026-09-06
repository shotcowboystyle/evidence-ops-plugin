# Rclone and Immutable Remotes

This reference covers the use of `rclone` to safely transfer digital evidence to storage backends, with a strict focus on immutable remotes. An operator uses this to synchronize local evidence stores with cloud object storage while avoiding destructive operations and ensuring complete cryptographic integrity during the transfer lifecycle.

## Why it matters

Moving digital evidence involves inherent risk. A malformed synchronization command can accidentally delete critical destination files to match a local directory state, destroying historical evidence. By enforcing immutable flags, performing deep checksum validations, and mandating dry-runs, operators ensure that data transfer adheres to the append-only nature of digital evidence preservation.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `rclone` | both | Highly robust command-line tool for cloud and local file synchronization |
| `shasum` | macOS | Baseline hashing to compare against `rclone hashsum` |
| `sha256sum`| Linux | GNU equivalent for baseline hashing |

## The danger of Sync

The fundamental rule of evidence transfer is to append, never overwrite or delete. The `rclone sync` command is inherently destructive; it makes the destination directory exactly match the source. If a file was accidentally deleted locally, `rclone sync` will execute that deletion on the remote server. For evidence operations, operators must exclusively use `rclone copy` paired with the `--immutable` flag, which aborts the transfer if an attempt is made to modify an existing file on the remote.

## Rate Limits and Audit Trails

When dealing with massive evidence batches (e.g., millions of small files or terabyte-scale archives), robust transfer controls are mandatory. 
- **Pacing:** Operators should utilize `--tpslimit` (transactions per second) and `--bwlimit` (bandwidth limits) to prevent saturating investigative networks or triggering cloud provider throttling protocols. 
- **Auditing:** Every transfer must generate a verifiable paper trail. By enforcing `--log-file` and setting `--log-level DEBUG`, operators produce an exhaustive manifest of every byte moved. This log is crucial during cross-examination to prove that the data transfer process was sound and error-free.

## Practical recipes

These commands demonstrate safe transfer protocols. Always assume the remote destination is sensitive and requires extreme care.

```bash
# 1. Perform a dry-run to meticulously preview the transfer operations
# Always run this before touching a production evidence remote
rclone copy ./evidence s3-remote:evidence-bucket/ --immutable --dry-run

# 2. Safely copy files to a remote, refusing to modify existing files
# The --immutable flag ensures existing remote files are treated as WORM
rclone copy ./evidence s3-remote:evidence-bucket/ --immutable

# 3. Securely throttle a large transfer while keeping detailed logs
rclone copy ./evidence s3-remote:evidence-bucket/ \
       --immutable \
       --tpslimit 10 \
       --log-file "logs/transfer-$(date -u +%Y%m%d).log" \
       --log-level DEBUG

# 4. Verify data integrity post-transfer using backend checksums
# This compares local hashes against the hashes stored by the cloud provider
rclone check ./evidence s3-remote:evidence-bucket/ --checksum

# 5. List remote files and their metadata in a structured JSON format
# Excellent for feeding into custody logs or inventory scripts
rclone lsjson s3-remote:evidence-bucket/

# 6. Compute SHA-256 hashes of the remote files directly
# Note: This relies on the backend provider natively supporting SHA-256
rclone hashsum sha256 s3-remote:evidence-bucket/

# 7. Safely copy encrypted data using rclone crypt
# Crypt remotes encrypt data client-side before sending to the backend
rclone copy ./evidence crypt-remote:evidence-bucket/ --immutable
rclone cryptcheck ./evidence crypt-remote:evidence-bucket/
```

## Pitfalls

- **Using `sync` Instead of `copy`:** Using `rclone sync` deletes files on the destination if they are absent locally. This violently breaks the immutability principle of evidence storage. Never use `sync` on an evidence remote.
- **Cryptographic Key Loss:** Using `rclone crypt` without properly and backing up the encryption password and the cryptographic salt. Losing these parameters means the remote evidence is mathematically unrecoverable.
- **Blind Trust in Checksums:** Assuming the `--checksum` flag performs a deep byte-for-byte read on the remote end. For many backends, it merely compares the local hash to a pre-calculated hash stored in the remote file's metadata. If the backend does not store cryptographic hashes, it falls back to modification time and size checks.
- **Omitting Immutability Flags:** Transferring to remotes that lack hardware or backend-level WORM (Object Lock) protections without appending the `--immutable` flag. The CLI is your last line of defense against accidental overwrites.

## See also

- [WORM Storage and Object Lock](worm-and-object-lock.md)
- [Hashing Algorithms](../hashing/algorithms-and-manifests.md)
- [macOS vs Linux Tooling](../hashing/macos-vs-linux-tooling.md)
- [Chain of Custody Principles](../custody/chain-of-custody-principles.md)
