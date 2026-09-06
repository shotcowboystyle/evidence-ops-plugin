# macOS vs Linux Hashing Tooling

This guide covers the critical operational differences between cryptographic hashing utilities provided natively on macOS (the primary host platform, which is BSD-derived) and those found on GNU/Linux systems. Operators must deeply understand these distinctions to maintain cross-platform verification workflows without generating false negative corruption alerts due to manifest format mismatches.

## Why it matters

Digital evidence frequently moves across operational boundaries; it may be captured on a macOS field workstation and subsequently verified on a Linux backend server, or vice versa. The default hashing utilities on BSD-derived systems (like macOS) differ significantly in naming, default output format, and flag availability compared to GNU coreutils. Failure to account for these architectural differences leads to broken verification scripts, stalled ingestion pipelines, and potentially invalidated evidence chains in legal settings. An operator cannot assume a command that works flawlessly on Debian will function on Darwin.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `shasum` | macOS / Linux | Perl-based script; ships native on macOS, widely available on Linux. Recommended for cross-platform scripts. |
| `sha256sum` | Linux | GNU coreutils standard. Not available natively on macOS. |
| `md5` | macOS | BSD utility. Different default output format than `md5sum`. |
| `md5sum` | Linux | GNU coreutils standard. Not available natively on macOS. |
| `b3sum` | both | Requires installation via package manager (e.g., Homebrew/apt) on both platforms. |
| `stat` | both | Core metadata reader. BSD (`stat -f`) and GNU (`stat -c`) use entirely incompatible format flags. |

## Practical recipes

### Generating a SHA-256 manifest cross-platform
The safest cross-platform hashing command relies on `shasum`, which is pre-installed on all macOS versions and commonly available on Linux distributions via Perl packages.

```bash
# macOS and Linux (when shasum is available)
shasum -a 256 /path/to/evidence.raw > evidence.sha256
```

### Checking a standard manifest natively on macOS
If you receive a standard GNU/Linux manifest (e.g., created elsewhere with the GNU utility), you can still easily verify it natively on macOS using `shasum`:

```bash
# macOS verification of any standard GNU manifest format
shasum -a 256 -c evidence.sha256
```

### Dealing with BSD md5 format mismatch
By default, the macOS `md5` command outputs a format incompatible with Linux's standard verifiers. To output a GNU-compatible format on macOS, you must use the `-r` flag:

```bash
# macOS - generating GNU-compatible MD5 output
md5 -r /path/to/evidence.raw > evidence.md5
```
*(Note: As emphasized elsewhere, MD5 should not be used for evidence integrity alone, but may be required for legacy system compatibility).*

### Portable find and hash
When hashing large directories, `find -exec` syntax requires care. Using `+` is generally portable and much faster than `\;` because it passes multiple arguments to a single process:

```bash
# macOS and Linux portable directory hashing
find /path/to/evidence -type f -exec shasum -a 256 {} + > manifest.sha256
```

### File stat differences
When recording file timestamps or sizes, do not rely on `stat` in cross-platform scripts without checking the OS type first. They are incompatible.

```bash
# macOS (BSD stat)
stat -f "%z bytes, modified %Sm" evidence.raw

# Linux (GNU stat)
stat -c "%s bytes, modified %y" evidence.raw
```

## Pitfalls

*   **Missing tools:** Writing scripts that rely on `sha256sum` will fail immediately on vanilla macOS systems. Always default to `shasum -a 256`.
*   **Format mismatches:** Standard BSD `md5` outputs `MD5 (file) = hash`, which GNU utilities on Linux cannot parse, resulting in immediate script failure.
*   **Newline handling:** macOS and Linux handle filenames with embedded newlines differently. Manifests containing such malformed filenames can break strict checking parameters.
*   **Find portability:** While the `-print0` and `xargs -0` pipeline is widely supported, subtle edge cases in BSD vs GNU `find` primitives (like exact `-mtime` behavior) can cause files to be silently skipped during collection.
*   **b3sum installation:** While BLAKE3 is excellent for performance, the tooling (`b3sum`) is not native to either OS out-of-the-box and must be provisioned on both ends before use.

## See also

*   [Algorithms and Manifests](algorithms-and-manifests.md)
*   [Chain of Custody Principles](../custody/chain-of-custody-principles.md)

## Advanced Operational Scenarios

### Script Normalization Workflows
To prevent brittle scripts, advanced operators utilize abstraction layers. Instead of calling `shasum` or `sha256sum` directly in a 1000-line bash script, the script should invoke a custom wrapper function (e.g., `generate_hash()`) that detects the host OS at runtime via `uname -s` and dynamically selects the correct binary and flag structure.

### Cross-Platform Line Ending Nightmares
Manifests generated on older systems or specific Windows environments may contain CRLF (`
`) line endings. When a macOS or Linux utility attempts to parse this manifest, it may interpret the carriage return as part of the filename, resulting in a failed validation. Operators should normalize manifest line endings using `dos2unix` or `tr -d '
'` before executing the `-c` check command.
