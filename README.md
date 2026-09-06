[Part of the shotcowboystyle marketplace](https://github.com/shotcowboystyle/ai-plugins)

## Evidence Ops Plugin

**Version:** 0.1.0

Operational handling of digital evidence — capture, hash, inspect metadata, register in
an append-only custody log, anchor in time, package, verify, and replicate to storage
that cannot silently rewrite it.

Pairs with [`matter-ops`](https://github.com/shotcowboystyle/matter-ops-plugin), which
owns the matter around the evidence — workspaces, document analysis, OSINT sourcing,
redaction for disclosure, and brief writing. Each works on its own.

## Portable by construction

This plugin is generated from a runtime-neutral source of truth in `.agent/`:

```
.agent/agent.md          the agent definition — identity, constraints, conventions
.agent/manifest.json     plugin metadata and per-skill metadata
.agent/skills/<name>.md  one skill body each, with no runtime-specific syntax
.agent/mcp.json          MCP server declarations, credentials by environment variable
```

`AGENTS.md` is generated from those files and can be used verbatim by any agent runtime.
The Claude Code layer — `skills/`, `commands/`, and `.claude-plugin/plugin.json` — is
generated too, and must not be hand-edited.

```bash
python3 scripts/build.py           # regenerate after editing .agent/
python3 scripts/build.py --check   # fail if anything on disk is stale
```

## Installation

```
/plugin marketplace add shotcowboystyle/ai-plugins
/plugin install evidence-ops@shotcowboystyle
```

Then run `/evidence-ops:onboard`.

<!-- BEGIN GENERATED: components -->

## Commands

- `/evidence-ops:check` — Probe this host for evidence-handling CLIs and report what is present, missing, and how to install it.
- `/evidence-ops:init [target-dir]` — Create the evidence directory tree and an empty append-only custody register in the current workspace.
- `/evidence-ops:capture <url> [--no-log]` — Archive a URL as a self-contained file, hash it, and record the capture context.
- `/evidence-ops:hash <path> [--blake3] [--out <manifest>]` — Compute SHA-256 (and optionally BLAKE3) for a file or directory and write a checkable manifest.
- `/evidence-ops:metadata <path> [--out <json>]` — Extract EXIF, IPTC, XMP, and container metadata to JSON and flag anomalies worth investigating.
- `/evidence-ops:log <path> [--source <text>] [--handler <name>]` — Hash an item, capture its custody metadata, and append one record to the append-only evidence register.
- `/evidence-ops:timestamp <path> [--verify] [--upgrade]` — Anchor a file's hash with OpenTimestamps, or upgrade and verify an existing proof.
- `/evidence-ops:bag <dir> [--out <bag-dir>]` — Package a directory as a BagIt bag with per-file checksums and a validatable manifest.
- `/evidence-ops:verify [path]` — Recompute hashes, validate bags and timestamp proofs, and report an explicit pass or fail.
- `/evidence-ops:sync <path> [--remote <name>] [--dry-run]` — Replicate verified evidence to immutable storage and re-verify what landed.
- `/evidence-ops:lookup <query>` — Search this plugin's reference corpus and return the most relevant passages with their paths.
- `/evidence-ops:onboard` — First-run setup — environment check, dependency install, and storage configuration.

## Skills

- **environment-check** — Use when the user wants to know which evidence-handling tools are present on this host before running a pipeline — probes hashing, metadata, timestamping, packaging, and storage CLIs and reports what is missing with an install hint for each
- **install-deps** — Use after environment-check reports missing tools — installs them, putting Python-based tools in a plugin-owned virtual environment instead of mutating the system Python
- **init-evidence-store** — Use when starting a new evidence collection or adding custody handling to an existing workspace — creates the evidence directory tree, an empty append-only register, and a written record of the hashing policy in force
- **capture-web** — Use when a web page needs to be preserved as evidence — archives it as a single self-contained file, records the capture context that the page itself cannot prove, hashes the result, and offers to register it
- **hash-evidence** — Use when a file or directory needs cryptographic hashes — computes SHA-256 by default and optionally BLAKE3, emitting a checkable manifest for directories
- **inspect-metadata** — Use when the embedded metadata of a file matters — extracts EXIF, IPTC, XMP, and container metadata to JSON, then flags anomalies such as timestamp disagreement or editing-software markers as signals worth investigating
- **log-custody** — Use when an item must enter the custody record — hashes it, captures who handed it over and how, copies the original into immutable storage under its own name, and appends one record to the append-only register
- **timestamp-evidence** — Use when a file's existence at a point in time needs to be provable independently of the filesystem — anchors its hash with OpenTimestamps and stores the proof alongside the custody record
- **bag-evidence** — Use when a set of items must be handed over or archived as one unit — packages a directory as a BagIt bag with per-file checksums and a manifest that any receiving party can validate without this plugin
- **verify-bundle** — Use when integrity must be confirmed rather than assumed — recomputes every hash, validates bags and timestamp proofs, and reports an explicit pass or fail naming each diverging file
- **setup-storage** — Use when configuring where evidence is replicated — walks through defining a storage remote, confirms its retention or write-once behaviour, and records the destination policy without ever touching credentials
- **sync-immutable** — Use when verified evidence should be replicated to storage that cannot silently rewrite it — copies to the configured remote, confirms retention settings before writing, and re-verifies what landed
- **reference-lookup** — Use when deciding how to handle a media type, storage mode, or integrity question — searches this plugin's own reference corpus and returns the most relevant passages with their file paths
- **onboard** — Use on first run or on a new machine — checks the environment, offers to install what is missing, configures a storage destination, and ends by showing the shortest working pipeline for this host

<!-- END GENERATED: components -->

## Dependencies

Probed by `environment-check`, installed by `install-deps`. None is required except a
SHA-256 tool, which every supported platform already has.

| Tool | Purpose |
| --- | --- |
| `shasum` (macOS) / `sha256sum` (GNU) | hashing and verification |
| `b3sum` | optional second hash algorithm |
| `exiftool`, `mediainfo` | metadata extraction |
| `single-file` | web page capture |
| `ots` | OpenTimestamps anchoring |
| `bagit.py` | BagIt packaging and validation |
| `rclone`, `aws` | replication and retention settings |
| `mat2`, `qpdf` | metadata scrubbing and PDF structure work |

Python tools install into a plugin-owned virtual environment at
`${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/evidence-ops/venv`
rather than the system Python.

## Conventions

- **Originals are immutable.** Nothing under `evidence/originals/` is ever rewritten,
  renamed, re-encoded, or stripped. Every transformation writes to `evidence/derived/`.
- **The register is append-only.** JSON Lines, one record per line. A correction is a
  new record that supersedes an earlier one, never an edit.
- **Duplicates are never skipped silently.** A hash already in the register is surfaced
  and asked about.
- **Integrity is never asserted without a check.** "Verified" means recomputed in this
  run. Verification failures stop the pipeline.
- **macOS first.** `sha256sum` does not exist there; every hashing path uses
  `shasum -a 256` and treats the GNU tools as the alternative.
- **Credentials come from the environment.** Never read, echoed, logged, or written into
  a workspace.
- **Every operation logs.** One file per run under `logs/`.

## Reference corpus

`references/` is original material written for this plugin, searched by the
`reference-lookup` skill. It covers hashing, timestamping, packaging, metadata,
capture, storage, redaction, and chain-of-custody practice.

## Disclaimer

This plugin is a workflow aid, not legal advice. Hashing and timestamping establish
integrity and existence in time; they do not establish authenticity, lawful acquisition,
relevance, or admissibility. Admissibility depends on jurisdiction and on process
discipline well beyond anything a tool can supply. Consult counsel.

## Author

Curtis Blanton — [shotcowboystyle.com](https://shotcowboystyle.com)

## License

MIT
