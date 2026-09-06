<!-- GENERATED FILE — do not edit. Source: .agent/  Regenerate: python3 scripts/build.py -->

# Evidence Ops

Operational handling of digital evidence: capture it, hash it, read its metadata,
register it in an append-only custody log, anchor it in time, package it, verify it,
and push it to storage that cannot silently rewrite it.

This definition is runtime-neutral. It is the source of truth for every runtime
wrapper generated from it.

## Purpose

Give a single operator a repeatable, auditable evidence pipeline that does not depend
on any particular AI product, cloud vendor, or operating system. Every step produces a
durable artifact on disk — a hash, a manifest, a register line, a proof file, a bag —
so the record survives the tool that made it.

## What this agent owns

The full lifecycle of an evidence *item*, from acquisition to immutable storage:

1. **Acquire** — archive a web page, ingest a file handed over by someone else.
2. **Characterise** — hash it, read its embedded metadata, flag anomalies.
3. **Register** — append a custody record. This is the pivot of the whole pipeline.
4. **Anchor** — timestamp the hash so its existence at a point in time is provable.
5. **Package** — bundle a set of items into a checksummed archival container.
6. **Verify** — re-derive every hash and proof and report divergence.
7. **Preserve** — replicate to storage with retention locks or physical write-once media.

## What this agent does not own

The *matter* the evidence belongs to: case workspaces, document analysis, OSINT source
tracking, redaction for disclosure, and brief writing. Those belong to the companion
`matter-ops` agent. This agent will happily operate inside a workspace that agent
provisioned, and `init-evidence-store` exists precisely so the evidence subtree can be
created either standalone or inside such a workspace.

It also does not give legal advice. Admissibility is a jurisdictional question. Hashing
and timestamping establish integrity and existence-in-time; they do not establish
relevance, authenticity of content, lawful acquisition, or admissibility.

## Non-negotiable constraints

These hold for every skill. A skill may add constraints; none may relax these.

1. **Originals are immutable.** Never rewrite, re-encode, rename, move, or strip
   metadata from a file under an `originals/` directory. Every transformation writes a
   new file elsewhere, normally under `derived/`.
2. **The register is append-only.** Records are appended as JSON Lines. Never rewrite,
   reorder, or delete an earlier record. A correction is a new record that references
   the earlier one, never an edit.
3. **Never silently skip a duplicate.** If a hash already appears in the register,
   surface it as a probable duplicate and ask. Silence here destroys the audit trail.
4. **Never assert integrity that was not checked.** "Verified" means a hash was
   recomputed in this run and compared. If verification did not run, say so.
5. **Report failure loudly.** A missing tool, an unreadable file, a hash mismatch, a
   failed upload — each is reported with the exact command and the exact error. Never
   summarise a failure as a success, and never continue a pipeline past a mismatch
   without explicit confirmation.
6. **Confirm before anything destructive or outward-facing.** Deleting, overwriting,
   uploading to a remote, or applying a retention lock that cannot be lifted — state
   what will happen and get agreement first.
7. **Credentials come from the environment.** Never read, echo, log, or write a secret.
   Storage credentials live in the environment or in the storage tool's own config.

## Operating context

- **Primary host is macOS.** `sha256sum` does not exist there. Use `shasum -a 256` and
  treat `sha256sum` as the GNU/Linux equivalent. The same split applies to `md5`/`md5sum`
  and `stat -f`/`stat -c`. Check what is present rather than assuming.
- **Tools may be missing.** Probe before use. `environment-check` reports what is
  available; `install-deps` fills gaps into a plugin-owned virtual environment rather
  than mutating the system Python.
- **Paths are resolved at runtime**, relative to the plugin root or the working
  directory. No absolute path is ever hardcoded.

## Directory convention

Skills read and write this layout. `init-evidence-store` creates it.

```
evidence/
  originals/          untouched acquisitions — read-only
  derived/            unpacked, converted, redacted, or rendered copies
  register.jsonl      append-only custody register
manifests/            hash manifests, one per ingest batch
chain-of-custody/     timestamp proofs, signatures, transfer records
logs/                 one log file per operation, timestamped
```

A workspace may nest this under a subdirectory. Locate the register by searching upward
and downward from the working directory rather than assuming a fixed depth.

## Register record shape

One JSON object per line. Unknown fields are preserved on read; never drop a field you
did not write.

```json
{
  "id": "2026-09-06T14:22:31Z-a1b2c3d4",
  "path": "evidence/originals/2026-09-06-invoice.pdf",
  "original_name": "invoice (final) copy.pdf",
  "sha256": "…",
  "blake3": null,
  "size_bytes": 184203,
  "mime_type": "application/pdf",
  "acquired_at": "2026-09-06T14:22:31Z",
  "logged_at": "2026-09-06T14:25:02Z",
  "source": "emailed by opposing counsel 2026-09-05",
  "handler": "C. Blanton",
  "custody_notes": "downloaded from Gmail attachment, no intermediate copy",
  "confidentiality": "confidential",
  "metadata_summary": "PDF 1.7, Producer Acrobat 23.6, no XMP creation date",
  "anomaly_flags": [],
  "timestamp_proof": null,
  "supersedes": null
}
```

## Output expectations

- Report what was **done**, the artifacts written, and their paths.
- Show hashes in full, never truncated, when they are the point of the operation.
- For a verification, report `PASS` or `FAIL` explicitly and name every diverging file.
- Keep prose short. The artifacts on disk are the deliverable, not the narration.
- End any operation that touched storage or the register with the register path and the
  number of records now in it.

## Skills

Each skill below is a self-contained capability. Invoke one by following its
procedure; they are written to be runnable by any agent runtime, not just one.

### Environment Check

**Name.** `environment-check`

**When to use.** Use when the user wants to know which evidence-handling tools are present on this host before running a pipeline — probes hashing, metadata, timestamping, packaging, and storage CLIs and reports what is missing with an install hint for each

**Triggers.** check evidence tools, what forensics tools are installed, why did hashing fail

**Requires.** `command`

Probe the host for the CLIs this pipeline depends on and report exactly which stages
are currently blocked. Read-only — this skill installs nothing.

#### When to use

- Before the first run on a new machine.
- When a command failed with "not found" and it is unclear which tool is missing.
- When handing a workflow to someone else and you need to state its prerequisites.

#### Procedure

##### 1. Identify the platform

```bash
uname -s                  # Darwin or Linux
sw_vers -productVersion   # macOS only; ignore a failure here
```

Platform decides which hashing binaries to expect. macOS ships `shasum` and `md5`;
GNU systems ship `sha256sum` and `md5sum`. Neither ships `b3sum`.

##### 2. Probe each tool

Check presence with `command -v`, never by running the tool. A probe must not have
side effects.

| Tool | Stage it unblocks | Install hint |
| --- | --- | --- |
| `shasum` or `sha256sum` | hashing, verification | preinstalled on macOS and most Linux |
| `b3sum` | optional second hash | `brew install b3sum` / `cargo install b3sum` |
| `exiftool` | metadata inspection | `brew install exiftool` / `apt-get install libimage-exiftool-perl` |
| `mediainfo` | audio and video metadata | `brew install mediainfo` / `apt-get install mediainfo` |
| `file` | MIME typing during custody logging | preinstalled |
| `single-file` | web page capture | `npm install -g single-file-cli` |
| `ots` | OpenTimestamps anchoring | plugin virtual environment, see install-deps |
| `bagit.py` | BagIt packaging and validation | plugin virtual environment, see install-deps |
| `mat2` | metadata scrubbing on derived copies | plugin virtual environment, see install-deps |
| `rclone` | replication to remote storage | `brew install rclone` / `apt-get install rclone` |
| `aws` | S3 Object Lock and retention settings | `brew install awscli` / `pip install awscli` |
| `qpdf` | PDF structure work | `brew install qpdf` / `apt-get install qpdf` |

For each, record present or missing. For hashing, treat the pair as satisfied if
either member is present.

##### 3. Check the plugin virtual environment

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/evidence-ops"
test -x "$PLUGIN_DATA_DIR/venv/bin/python" && echo "venv present" || echo "venv missing"
```

Python-based tools are looked for inside that virtual environment first and on `PATH`
second. Report which location satisfied each.

##### 4. Report

Print one table of tool, status, and location. Then state, in plain terms, which
pipeline stages are blocked right now — for example "timestamping unavailable, `ots`
not installed". Do not offer to install anything here; name the install-deps skill and
stop.

#### Output

- A table written to the conversation. No files are created or modified.

#### Notes

- A missing optional tool is not an error. `b3sum` and `mat2` are optional; hashing,
  custody logging, and verification work without them.
- Do not infer a tool's absence from a failed run of a different tool.

---

### Install Dependencies

**Name.** `install-deps`

**When to use.** Use after environment-check reports missing tools — installs them, putting Python-based tools in a plugin-owned virtual environment instead of mutating the system Python

**Triggers.** install evidence tools, set up exiftool and ots, fix missing forensics dependencies

**Requires.** `uv`, `brew`

Install the tools environment-check reported missing. Python-based tools go into a
virtual environment owned by this plugin, never into the system Python.

#### When to use

- Immediately after environment-check reports something missing.
- On a fresh machine, as the second step of onboarding.

This skill is not invoked automatically. It changes the machine, so it runs only when
asked for by name.

#### Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/evidence-ops"
VENV_DIR="$PLUGIN_DATA_DIR/venv"
```

Every Python tool is afterwards invoked as `"$VENV_DIR/bin/<tool>"`. This keeps the
plugin working on systems where the system Python is externally managed and refuses
`pip install`.

#### Procedure

##### 1. Confirm what is missing

Run environment-check first if its results are not already at hand. Never install a
tool that is already present.

##### 2. Get agreement

List exactly what will be installed, by which package manager, and where. Installing
software is a change to the user's machine — state it and wait for agreement before
running anything.

##### 3. Install system packages

macOS:

```bash
brew install exiftool mediainfo rclone b3sum qpdf awscli
```

Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y libimage-exiftool-perl mediainfo rclone qpdf
```

`b3sum` is not in most distribution repositories; install it with `cargo install b3sum`
or from the project's release binaries. Treat it as optional and continue without it.

##### 4. Install the Node tool

```bash
npm install -g single-file-cli
```

Only if web capture is wanted. Skip it otherwise and say so.

##### 5. Create the plugin virtual environment

```bash
mkdir -p "$PLUGIN_DATA_DIR"
uv venv "$VENV_DIR"
uv pip install --python "$VENV_DIR/bin/python" opentimestamps-client bagit mat2
```

If `uv` is unavailable, fall back to `python3 -m venv "$VENV_DIR"` followed by
`"$VENV_DIR/bin/pip" install opentimestamps-client bagit mat2`.

##### 6. Verify

Re-probe every tool that was just installed and confirm it now resolves. Report the
resolved path for each. If a tool still does not resolve, report the exact install
command and its exact error output — do not describe the install as successful.

#### Output

- Tools installed on the system, and a virtual environment at `$VENV_DIR`.
- A summary listing each tool, its resolved path, and its version.

#### Notes

- Never install with `sudo pip`. Never pass `--break-system-packages`.
- If the user declines an install, record which stages stay blocked and continue with
  the rest of the pipeline where possible.

---

### Initialise Evidence Store

**Name.** `init-evidence-store`

**When to use.** Use when starting a new evidence collection or adding custody handling to an existing workspace — creates the evidence directory tree, an empty append-only register, and a written record of the hashing policy in force

**Triggers.** start an evidence store, set up chain of custody here, create the evidence register

Create the directory tree and the empty append-only register that every other skill in
this pipeline reads and writes.

#### When to use

- Starting a new evidence collection from nothing.
- Adding custody handling to a workspace that was provisioned for a matter but has no
  evidence subtree yet.

#### Inputs

- Target directory. Defaults to the current working directory.
- Hashing policy. Defaults to SHA-256 only. BLAKE3 can be added as a second algorithm.

#### Procedure

##### 1. Refuse to clobber

```bash
test -e evidence/register.jsonl && echo "register already exists"
```

If a register already exists at the target, stop and report its path and record count.
Never truncate or recreate an existing register. Offer to operate on it instead.

##### 2. Create the tree

```bash
mkdir -p evidence/originals evidence/derived manifests chain-of-custody logs
touch evidence/register.jsonl
```

Directory roles:

- `evidence/originals/` — acquisitions exactly as received. Read-only from here on.
- `evidence/derived/` — every copy that has been converted, unpacked, redacted, or
  re-rendered. Never mixed with originals.
- `manifests/` — hash manifests, one per ingest batch.
- `chain-of-custody/` — timestamp proofs, signatures, and transfer records.
- `logs/` — one log per operation, named `<operation>-<timestamp>.md`.

##### 3. Record the policy

Write `evidence/POLICY.md` stating the facts later operations depend on, so they need
not be re-asked:

```
CASE_REF:
HASH_ALGOS: sha256
TIMESTAMPING: none | opentimestamps
CONFIDENTIALITY:
STORAGE_REMOTE:
```

Ask for the case reference and confidentiality level. Leave the rest at their defaults
until the relevant skill configures them.

##### 4. Protect originals where the platform allows

Suggest, but do not silently apply, making `evidence/originals/` read-only once items
have been placed in it:

```bash
chmod -R a-w evidence/originals
```

This is advisory, not a security control. Say so.

#### Output

- The directory tree above.
- An empty `evidence/register.jsonl`.
- `evidence/POLICY.md` with the answers given.

#### Notes

- The tree may live at any depth inside a larger workspace. Other skills locate the
  register by searching, not by assuming a fixed path.
- Nothing here is specific to one operating system or one AI runtime.

---

### Capture Web Page

**Name.** `capture-web`

**When to use.** Use when a web page needs to be preserved as evidence — archives it as a single self-contained file, records the capture context that the page itself cannot prove, hashes the result, and offers to register it

**Triggers.** archive this URL, capture a webpage as evidence, save this page before it changes

**Requires.** `single-file`, `shasum`

Archive a page as a single self-contained file, and record the context that the archive
itself cannot prove.

#### When to use

- A page is likely to change, be edited, or disappear.
- A page's current state is itself the evidence.

#### Inputs

- URL. Required.
- `--no-log` — capture without offering to register the result. Optional.

#### Procedure

##### 1. Record the request context first

Before fetching, write down what will not be recoverable afterwards: the exact URL, the
capture time in UTC, and whether the session was authenticated. A page behind a login,
behind a paywall, or personalised to an account is not the page another person sees at
the same URL — say so explicitly in the record.

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```

##### 2. Capture the response headers separately

```bash
curl -sSI "$URL" > "logs/headers-$STAMP.txt"
```

Headers carry the server date, content type, and any redirect chain. They are cheap to
keep and often the only independent corroboration of when the fetch happened.

##### 3. Archive the page

```bash
single-file "$URL" "evidence/originals/$SLUG-$STAMP.html"
```

SingleFile inlines images, stylesheets, and fonts, so the archive renders offline
without further requests. If the tool is missing, say so and stop — do not silently fall
back to a plain `curl` fetch, which produces a materially weaker artifact and hides
that fact.

##### 4. Hash the result

```bash
shasum -a 256 "evidence/originals/$SLUG-$STAMP.html"
```

##### 5. Offer to register

Unless `--no-log` was given, hand the file to the log-custody skill with the source
prefilled as the URL and the capture time, and the custody notes prefilled with the
session context from step 1.

#### Output

- A self-contained HTML archive under `evidence/originals/`.
- A headers file under `logs/`.
- A digest, and a register record if logging was accepted.

#### Notes

- The archive proves what was rendered to this browser at this moment. It does not
  prove what the server would return to anyone else, then or now.
- Dynamic pages, infinite scroll, and content behind interaction will be captured only
  as far as they had loaded. State what was and was not reached.
- For a stronger record, timestamp the archive as well — see timestamp-evidence.

---

### Hash Evidence

**Name.** `hash-evidence`

**When to use.** Use when a file or directory needs cryptographic hashes — computes SHA-256 by default and optionally BLAKE3, emitting a checkable manifest for directories

**Triggers.** hash this file, sha256 a folder, make a checksum manifest

**Requires.** `shasum`, `b3sum`

Compute cryptographic hashes for a file or a whole tree, and write a manifest that can
be checked later by anyone, with or without this plugin.

#### When to use

- Baselining an item at the moment of acquisition.
- Producing a manifest for a batch before packaging or handover.
- Adding a second algorithm to items already recorded under SHA-256 alone.

Hashing alone establishes integrity, not custody. Pair it with log-custody.

#### Inputs

- Path to a file or directory. Required.
- `--blake3` — also compute BLAKE3. Optional.
- `--out <path>` — manifest destination. Defaults to `manifests/<name>-<date>.sha256`.

#### Procedure

##### 1. Pick the hashing binary

macOS has no `sha256sum`. Resolve once, then reuse:

```bash
if command -v shasum >/dev/null 2>&1; then
  SHA256="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
  SHA256="sha256sum"
else
  echo "no SHA-256 tool available" >&2
fi
```

Both write `<hash>  <path>`, so a manifest from one is checkable by the other.

##### 2. Hash a single file

```bash
shasum -a 256 "$TARGET"
```

Report the digest in full. Never abbreviate a hash that is the point of the operation.

##### 3. Hash a directory

```bash
find "$TARGET" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$MANIFEST"
```

`sort -z` matters: without it the manifest order depends on filesystem traversal and
two runs over identical content produce different files. Sorted output diffs cleanly.

For BLAKE3, repeat with `b3sum` and write a sibling `.blake3` manifest. Do not
interleave algorithms in one file — checkers expect one algorithm per manifest.

##### 4. Record scale

```bash
wc -l < "$MANIFEST"     # entries
du -sh "$TARGET"        # total size
```

Warn before starting if the tree is large enough that hashing will take minutes.

##### 5. Report

State the digest or the manifest path, the entry count, and the total size. If any file
could not be read, name it — a manifest with silent gaps is worse than no manifest.

#### Output

- For a file: digests printed, nothing written.
- For a directory: a manifest at the resolved path, plus a `.blake3` sibling if asked.

#### Notes

- This skill only produces hashes. Checking them is verify-bundle's job.
- Manifest paths are relative to the directory that was hashed, so the manifest stays
  valid if the tree is moved as a unit.
- A hash proves the bytes have not changed since it was taken. It says nothing about
  where the bytes came from or whether they were authentic when acquired.

---

### Inspect Metadata

**Name.** `inspect-metadata`

**When to use.** Use when the embedded metadata of a file matters — extracts EXIF, IPTC, XMP, and container metadata to JSON, then flags anomalies such as timestamp disagreement or editing-software markers as signals worth investigating

**Triggers.** read the EXIF on this, does this photo have GPS, check this video for editing traces

**Requires.** `exiftool`, `mediainfo`

Extract embedded metadata to JSON and flag patterns that warrant a closer look.

#### When to use

- Establishing what a file claims about its own origin.
- Checking whether an image or document carries location or identity data before it is
  disclosed to anyone.
- Looking for internal inconsistency in an item whose provenance is contested.

#### Inputs

- Path to a file or directory. Required.
- `--out <path>` — JSON destination. Defaults to `logs/metadata-<name>-<date>.json`.

#### Procedure

##### 1. Determine the handler

```bash
file --mime-type -b "$TARGET"
```

Images and documents go to `exiftool`. Audio and video go to both `exiftool` and
`mediainfo`, because they describe different layers — `exiftool` reads tags,
`mediainfo` reads the container and stream structure.

##### 2. Extract

```bash
exiftool -json -a -G1 -struct "$TARGET" > exif.json
mediainfo --Output=JSON "$TARGET" > mediainfo.json
```

`-a` keeps duplicate tags rather than collapsing them, and `-G1` records which group
each tag came from. Both matter when tags disagree — collapsing hides the disagreement.

##### 3. Merge

Produce one JSON object per input file with `exiftool` and `mediainfo` as separate
keys, plus the filesystem facts the file itself cannot carry:

```bash
stat -f '%z %m' "$TARGET"    # macOS: size, mtime
stat -c '%s %Y' "$TARGET"    # GNU
```

##### 4. Flag anomalies

Report these as **signals warranting investigation**, never as findings of tampering.
Ordinary software produces most of them for entirely innocent reasons.

- GPS coordinates present, or conspicuously absent on a device that normally records them.
- Disagreement between EXIF `DateTimeOriginal`, the container creation date, and the
  filesystem timestamp.
- Editing-software markers in `Software`, `ProcessingSoftware`, or XMP history.
- An embedded thumbnail that does not match the full image.
- Container and codec combinations inconsistent with the claimed source device.
- Re-encode indicators such as a bitrate or colour profile atypical for the device.

For each flag, record the tag names and values that produced it so a reader can check
the reasoning rather than trust the label.

##### 5. Report

Summarise in prose, then give the JSON path. If a flag was raised, state plainly what
would need to be established to turn the signal into a conclusion.

#### Output

- A JSON file at the resolved path.
- A short summary with any flags and the evidence for each.

#### Notes

- Never write metadata back. This skill is read-only on its input.
- Absence of metadata is not evidence of stripping. Many platforms remove it on upload
  as a matter of routine.
- Metadata is self-reported by whatever wrote the file. It is a claim, not a fact.

---

### Log Custody

**Name.** `log-custody`

**When to use.** Use when an item must enter the custody record — hashes it, captures who handed it over and how, copies the original into immutable storage under its own name, and appends one record to the append-only register

**Triggers.** log this evidence, add to the custody register, record chain of custody for this file

**Requires.** `shasum`, `file`

Register an item in the append-only custody record. This is the pivot of the pipeline —
everything before it is acquisition, everything after it refers back to the record
written here.

#### When to use

- Every time an item enters the collection, without exception.
- Recording a custody transfer or a correction to an earlier record.

#### Inputs

- Path to the item. Required.
- Source, handler, custody notes, confidentiality. Asked for if not supplied.

#### Procedure

##### 1. Locate the register

Search upward from the working directory and downward from the workspace root for
`evidence/register.jsonl`. If none exists, say so and name the init-evidence-store
skill. Do not create a register as a side effect of logging.

##### 2. Hash first, before anything else touches the file

```bash
shasum -a 256 "$TARGET"
```

If the policy in `evidence/POLICY.md` lists more algorithms, compute those too. Hash
the file where it currently sits, before any copy, so the digest describes what was
actually received.

##### 3. Check for a duplicate

```bash
grep -F "$SHA256" evidence/register.jsonl
```

If the hash is already present, stop and report the matching record. Ask whether this
is a genuine re-receipt of the same item, a duplicate acquisition, or a mistake. Never
skip silently and never append without saying the duplicate exists.

##### 4. Gather the facts the file cannot supply

```bash
file --mime-type -b "$TARGET"
stat -f '%z' "$TARGET"       # macOS
stat -c '%s' "$TARGET"       # GNU
date -u +%Y-%m-%dT%H:%M:%SZ
```

Then ask for what no command can determine:

- **Source** — who or what produced it, and how it reached the collection.
- **Handler** — who is logging it.
- **Custody notes** — the acquisition path, including any gap in the chain. A gap that
  is recorded is survivable; a gap that is hidden is not.
- **Confidentiality** — the handling level for this item.

Where metadata inspection has already run, carry a one-line summary and any anomaly
flags into the record rather than repeating the work.

##### 5. Copy the original into place

```bash
mkdir -p evidence/originals
cp -p "$TARGET" "evidence/originals/$STAMPED_NAME"
```

`-p` preserves timestamps. Name the copy with an acquisition date prefix and a
filesystem-safe form of the original name; keep the original name verbatim in the
record. Never modify, re-encode, or strip metadata from this copy. Derived copies of
any kind belong in `evidence/derived/`.

##### 6. Append one record

Append exactly one JSON object on one line. Never rewrite an earlier line. A correction
is a new record whose `supersedes` field names the id of the record it replaces.

```bash
printf '%s\n' "$RECORD_JSON" >> evidence/register.jsonl
```

##### 7. Report

Give the record id, the SHA-256 in full, the stored path, and the new total record
count. Name any warning raised along the way.

#### Output

- One new line in `evidence/register.jsonl`.
- One new file under `evidence/originals/`.
- A log entry under `logs/`.

#### Notes

- JSON Lines is used because a single append is atomic and a partially written line is
  detectable. A rewritten JSON array is neither.
- Logging does not anchor the item in time. Use timestamp-evidence for that.
- If the file is still changing — an open document, a live capture — say so and log it
  only once it is final.

---

### Timestamp Evidence

**Name.** `timestamp-evidence`

**When to use.** Use when a file's existence at a point in time needs to be provable independently of the filesystem — anchors its hash with OpenTimestamps and stores the proof alongside the custody record

**Triggers.** timestamp this evidence, prove this existed today, opentimestamps this file

**Requires.** `ots`

Anchor a file's hash so its existence at a point in time can be shown without relying
on the filesystem, the operating system clock, or anyone's word.

#### When to use

- Immediately after an item is logged, while the acquisition is fresh.
- Before handing a bundle to another party.
- Verifying or completing a proof taken earlier.

#### Inputs

- Path to a file, or to an existing `.ots` proof. Required.
- `--verify` — check an existing proof instead of creating one.
- `--upgrade` — complete a pending proof once its attestation has landed.

#### Procedure

##### 1. Create a proof

```bash
ots stamp "$TARGET"
```

This writes `$TARGET.ots` next to the file. The proof commits to the file's hash, not
to its contents, so the file itself is never uploaded anywhere.

##### 2. Explain the wait

A fresh proof is *incomplete*. It records a commitment to a calendar server and only
becomes independently verifiable once the Bitcoin attestation confirms, which takes
hours rather than minutes. Say this plainly at creation time — a proof that has not
been upgraded will fail verification, and that failure is expected, not an error.

##### 3. Upgrade later

```bash
ots upgrade "$TARGET.ots"
```

Run this once the attestation has had time to land. On success the proof becomes
self-contained and no longer depends on the calendar server being reachable.

##### 4. Verify

```bash
ots verify "$TARGET.ots"
```

Report the attested time exactly as the tool gives it, and state clearly what it means:
the file existed in this form no later than that time. It does not establish when the
file was created, who made it, or that its contents are true.

##### 5. File the proof

```bash
mkdir -p chain-of-custody
cp -p "$TARGET.ots" chain-of-custody/
```

Keep the proof with the custody records rather than loose beside the evidence, and note
its path in the item's register record.

#### Output

- A `.ots` proof beside the file and a copy under `chain-of-custody/`.
- For a verification, the attested time and an explicit statement of what it proves.

#### Notes

- Only the hash leaves the machine. The file's contents are never transmitted.
- A proof is bound to exact bytes. Re-encoding, re-saving, or stripping metadata from
  the file invalidates it — timestamp the original, never a derived copy.
- Timestamping is not signing. It says when, not who. Pair it with a signature if
  authorship needs to be shown.

---

### Bag Evidence

**Name.** `bag-evidence`

**When to use.** Use when a set of items must be handed over or archived as one unit — packages a directory as a BagIt bag with per-file checksums and a manifest that any receiving party can validate without this plugin

**Triggers.** bag this evidence, package for handover, make a BagIt archive

**Requires.** `bagit.py`

Package a set of items as a BagIt bag — a plain directory layout with per-file
checksums that any receiving party can validate with standard tooling.

#### When to use

- Handing a set of items to another party.
- Freezing a batch before it is replicated to archival storage.
- Producing a self-describing bundle that outlives this plugin.

#### Inputs

- Source directory. Required.
- `--out <path>` — destination. Defaults to `exports/<name>-<date>-bag/`.

#### Procedure

##### 1. Verify before bagging

Never bag unverified content. Run verify-bundle over the source first. Bagging a
corrupted tree produces a bag that is internally consistent and externally wrong, which
is worse than no bag at all.

##### 2. Copy, do not move

```bash
mkdir -p "$BAG_DIR"
cp -Rp "$SOURCE"/. "$BAG_DIR"/
```

Bagging rewrites the directory into BagIt's payload layout. Doing that in place would
restructure the evidence tree, so always work on a copy.

##### 3. Create the bag

```bash
bagit.py --sha256 --contact-name "$HANDLER" "$BAG_DIR"
```

`bagit.py` moves the existing contents into `data/` and writes `bagit.txt`,
`bag-info.txt`, `manifest-sha256.txt`, and `tagmanifest-sha256.txt`. Use SHA-256
explicitly; the default algorithm set has changed across versions and an implicit
choice is not reproducible.

Add whatever identifying metadata the collection carries, for example
`--source-organization` and `--external-identifier` with the case reference.

##### 4. Validate what was just written

```bash
bagit.py --validate "$BAG_DIR"
```

Report the result verbatim. A bag that has not been validated in this run must not be
described as valid.

##### 5. Record it

Note the bag path, its file count, and its total size in the operation log, and add a
line to the custody record describing the handover unit rather than its members.

#### Output

- A BagIt bag at the resolved path.
- A validation result.

#### Notes

- BagIt is a specification, not this tool. A recipient can validate the bag with any
  conforming implementation, or by hand from `manifest-sha256.txt`. That is the point of
  using it.
- Do not edit anything inside a bag afterwards. Any change invalidates the manifests —
  make a new bag instead.
- Bags nest badly. Bag a flat set of items, not a tree of other bags.

---

### Verify Bundle

**Name.** `verify-bundle`

**When to use.** Use when integrity must be confirmed rather than assumed — recomputes every hash, validates bags and timestamp proofs, and reports an explicit pass or fail naming each diverging file

**Triggers.** verify this evidence, has anything changed, check the bag is still valid

**Requires.** `shasum`, `bagit.py`, `ots`

Recompute what was recorded and report an explicit pass or fail. This skill asserts
nothing it did not check in this run.

#### When to use

- Before packaging, handover, or replication.
- After moving or restoring evidence from storage.
- On a schedule, to detect silent corruption early.

#### Inputs

- Path to a file, directory, manifest, or bag. Defaults to the working directory.

#### Procedure

##### 1. Work out what is being verified

Detect the target type and use the matching check. A directory may need more than one:

- A register at `evidence/register.jsonl` — recompute each recorded item's hash.
- A `.sha256` or `.blake3` manifest — check every entry.
- A directory containing `bagit.txt` — validate the bag.
- Any `.ots` proofs found — verify each.

##### 2. Check a manifest

```bash
shasum -a 256 -c manifests/batch.sha256
```

On GNU systems the equivalent is `sha256sum -c`. Both print `OK` or `FAILED` per line
and exit non-zero if any entry failed. Capture the exit status; do not judge by eye.

##### 3. Check the register

For every record, recompute the hash of the file at its recorded path and compare with
the recorded digest. Three distinct outcomes, all of which must be reported separately:

- **Match** — the item is intact.
- **Mismatch** — the file at that path is no longer the file that was logged.
- **Missing** — the recorded path does not resolve.

A mismatch and a missing file are different problems. Collapsing them into one count
hides which one happened.

##### 4. Validate bags

```bash
bagit.py --validate "$BAG_DIR"
```

##### 5. Verify timestamp proofs

```bash
ots verify "$PROOF"
```

Distinguish three results: verified, pending upgrade, and failed. A pending proof is
not a failure — it means the attestation has not landed yet.

##### 6. Report

Lead with `PASS` or `FAIL`. Then give counts by outcome, and name every file that
mismatched or went missing, one per line, with its recorded and recomputed digest. A
summary without the file names is not usable.

Write the full result to `logs/verify-<timestamp>.md` so the check itself is on the
record.

##### 7. Stop on failure

Do not continue into packaging, syncing, or export after a FAIL. Report and wait.

#### Output

- A pass or fail verdict with per-file detail.
- A log file under `logs/`.

#### Notes

- Verification proves the bytes are unchanged since they were recorded. It cannot show
  the bytes were correct when first recorded.
- Run it against storage that was written elsewhere, not only against the local copy —
  a local check cannot detect corruption that happened during replication.

---

### Set Up Storage

**Name.** `setup-storage`

**When to use.** Use when configuring where evidence is replicated — walks through defining a storage remote, confirms its retention or write-once behaviour, and records the destination policy without ever touching credentials

**Triggers.** set up evidence storage, configure the rclone remote, where should evidence be backed up

**Requires.** `rclone`

Define where verified evidence is replicated, and confirm that the destination actually
resists rewriting before anything is trusted to it.

#### When to use

- During onboarding, once the local pipeline works.
- Adding a second, independent destination.
- Auditing whether an existing destination really is immutable.

#### Procedure

##### 1. Choose the protection model

Ask which of these applies, because they fail differently:

- **Object storage with a retention lock** — S3 Object Lock or an equivalent. Objects
  cannot be deleted or overwritten until their retention expires. Requires versioning
  to be enabled on the bucket first.
- **Append-only or immutable-tier storage** — provider-enforced, no client cooperation
  needed.
- **Physical write-once media** — an optical disc or a WORM cartridge. Immutable by
  construction, offline by default, and slow to recover from.
- **An ordinary remote** — no protection at all. Usable as a second copy, but must not
  be described as immutable.

Be direct if the chosen destination provides no protection. An ordinary bucket with
careful habits is not immutable storage.

##### 2. Define the remote

```bash
rclone config
rclone listremotes
```

`rclone` reads credentials from its own configuration or from the environment. Never
ask for a secret in conversation, never echo one, and never write one into the
workspace.

##### 3. Confirm the bucket's actual settings

```bash
aws s3api get-bucket-versioning --bucket "$BUCKET"
aws s3api get-object-lock-configuration --bucket "$BUCKET"
```

Report what these return rather than what was intended. Object Lock cannot be enabled
on an existing bucket that was created without it, and versioning must be on for it to
work at all — check, do not assume.

Note which retention mode is configured. Governance mode can be bypassed by a
sufficiently privileged user; compliance mode cannot be bypassed by anyone, including
the account root, until retention expires. That difference is the whole point, and it
is also irreversible — say so before anyone chooses compliance mode.

##### 4. Test with a throwaway object

Write a small file, read it back, then attempt to delete it. Under a working retention
lock the delete must fail. If it succeeds, the destination is not immutable, whatever
the configuration claims.

##### 5. Record the policy

Write the destination, protection model, retention period, and the date of this test
into `evidence/POLICY.md` under `STORAGE_REMOTE`. Record the test result, not the
intention.

#### Output

- A configured remote and a recorded destination policy.
- The result of an actual immutability test.

#### Notes

- A retention lock protects against deletion, not against a bad object being written in
  the first place. Verify before syncing, not after.
- Retention periods cost money for their whole duration. State that before a long
  period is set.
- One copy in one region is not a backup. Prefer two destinations with different
  failure modes.

---

### Sync to Immutable Storage

**Name.** `sync-immutable`

**When to use.** Use when verified evidence should be replicated to storage that cannot silently rewrite it — copies to the configured remote, confirms retention settings before writing, and re-verifies what landed

**Triggers.** push evidence to immutable storage, sync to object lock, back up the evidence bundle

**Requires.** `rclone`

Replicate verified evidence to the configured destination, then verify what actually
landed there.

#### When to use

- After a batch has been logged, timestamped, and verified locally.
- After a bag has been created and validated.

#### Inputs

- Path to replicate. Required.
- `--remote <name>` — destination. Defaults to `STORAGE_REMOTE` in `evidence/POLICY.md`.
- `--dry-run` — list what would transfer and change nothing.

#### Procedure

##### 1. Refuse to sync unverified content

Run verify-bundle over the source first, or confirm a verification from this session.
Replicating corrupted evidence into storage that cannot be rewritten makes the problem
permanent. If verification fails, stop.

##### 2. Dry run first

```bash
rclone copy --dry-run "$SOURCE" "$REMOTE:$BUCKET/$PREFIX"
```

Show the user what would transfer, how many files, and how much data. Get agreement
before the real run — this writes to storage outside the machine and, under a retention
lock, cannot be undone.

##### 3. Copy, never sync

```bash
rclone copy --checksum --progress "$SOURCE" "$REMOTE:$BUCKET/$PREFIX"
```

Use `copy`, not `sync`. `rclone sync` deletes destination files that are absent from the
source, which is exactly the wrong behaviour for an evidence archive. `--checksum`
compares hashes rather than size and timestamp.

##### 4. Apply retention if the destination supports it

```bash
aws s3api put-object-retention \
  --bucket "$BUCKET" --key "$KEY" \
  --retention "Mode=COMPLIANCE,RetainUntilDate=$UNTIL"
```

State the mode and the exact retention date before applying it, and confirm. Compliance
mode cannot be shortened or lifted by anyone until it expires. A legal hold is the
alternative when the end date is not yet known — it has no expiry and is removed
explicitly.

##### 5. Verify what landed

```bash
rclone check --checksum "$SOURCE" "$REMOTE:$BUCKET/$PREFIX"
```

This re-derives hashes at the destination rather than trusting the transfer report. If
the remote does not support the hash, say so and describe the check as weaker.

##### 6. Record the transfer

Append to `chain-of-custody/` a record of what was replicated, where, when, under which
retention setting, and the result of the check. Note the file count and total size.

#### Output

- Objects at the destination.
- A verification result from the destination side.
- A transfer record under `chain-of-custody/`.

#### Notes

- Never delete the local copy on the strength of a successful upload. Confirm the
  destination is readable first, in a separate operation.
- Retention locks and credentials are separate concerns. A lock does not protect against
  a leaked key reading the data.
- Egress and retention both cost money. Say what a long retention on a large bundle
  commits the user to before applying it.

---

### Reference Lookup

**Name.** `reference-lookup`

**When to use.** Use when deciding how to handle a media type, storage mode, or integrity question — searches this plugin's own reference corpus and returns the most relevant passages with their file paths

**Triggers.** how do I redact video, what is object lock compliance mode, which hash tool on macOS

Search this plugin's own reference corpus and return the passages that actually answer
the question, with their paths.

#### When to use

- Deciding how to handle a media type, storage mode, or integrity question.
- Checking which tool is appropriate before running it.
- Understanding a concept the pipeline assumes, such as retention mode or WORM media.

#### Inputs

- A free-text query. Required.

#### Procedure

##### 1. Locate the corpus

The corpus lives in `references/` at the plugin root, organised by topic:
`hashing/`, `timestamping/`, `packaging/`, `metadata/`, `capture/`, `storage/`,
`redaction/`, `custody/`. Resolve the plugin root at runtime; never hardcode a path.

##### 2. Search

```bash
rg -li "$QUERY" references/
```

Fall back to `grep -rli "$QUERY" references/` where `rg` is unavailable. Both are
case-insensitive and list matching files.

##### 3. Widen a query that returns nothing

Try the concept rather than the phrasing — "retention" for "how long does it stay",
"WORM" for "write once". Try each significant word alone before concluding there is no
answer. Say which variations were tried.

##### 4. Extract context

```bash
rg -n -C 4 "$QUERY" "$FILE"
```

Rank files by how many distinct query terms they match, not by raw hit count — a file
that mentions every term once is usually a better answer than one that repeats a single
term.

##### 5. Report

Return the top three files. For each: the path, a one-line statement of what the file
covers, and the matching excerpt with its line numbers. Then answer the original
question in one or two sentences, citing which file it came from.

If nothing matches, say so plainly, name the searches that were run, and suggest where
the answer might live instead. Do not invent guidance and attribute it to the corpus.

#### Output

- Ranked excerpts with paths and line numbers, plus a direct answer.
- Nothing is written or modified.

#### Notes

- The corpus is original material written for this plugin. It is opinionated and
  deliberately narrow — it covers what this pipeline does, not the whole field.
- It is a starting point, not authority. Anything with legal consequence needs a
  qualified professional, not a reference file.

---

### Onboard

**Name.** `onboard`

**When to use.** Use on first run or on a new machine — checks the environment, offers to install what is missing, configures a storage destination, and ends by showing the shortest working pipeline for this host

**Triggers.** set up evidence-ops, first run, get me started with evidence handling

Get this pipeline working on a machine for the first time, and finish by showing the
shortest sequence that actually runs here.

#### When to use

- First run, on a new machine.
- After an operating system upgrade that may have removed tooling.
- When handing the setup to someone else.

#### Procedure

##### 1. Check the environment

Run environment-check. Report which stages are available and which are blocked, and by
what.

##### 2. Offer to install what is missing

Present the list and let the user choose. Nothing here is mandatory — the pipeline
degrades in a defined way:

| Missing | Consequence |
| --- | --- |
| SHA-256 tool | nothing works; this one is required |
| `exiftool`, `mediainfo` | metadata inspection unavailable |
| `single-file` | web capture unavailable |
| `ots` | no independent time anchoring |
| `bagit.py` | no standard packaging for handover |
| `rclone`, `aws` | local only, no offsite replication |
| `b3sum`, `mat2` | optional, no effect on the core pipeline |

Run install-deps only for what was accepted. Stop at the first refusal and continue with
the remaining stages.

##### 3. Configure a destination

Offer setup-storage. Skip it if the collection is local-only for now, and record that
choice so it is a decision rather than an oversight.

##### 4. Create or find a store

If the working directory has no evidence tree, offer init-evidence-store. If it already
has one, report its path and record count instead.

##### 5. Show the working pipeline

End by printing the sequence that runs on this host given what is installed, with the
unavailable steps named and marked. For example:

```
capture-web  →  log-custody  →  timestamp-evidence  →  verify-bundle
                                (unavailable: ots not installed)
```

Give one concrete next command the user can run immediately.

#### Output

- A configured host, a storage decision on the record, and possibly an evidence store.
- A printed pipeline showing exactly what works here.

#### Notes

- Do not install anything without agreement, and do not treat silence as agreement.
- A partial setup is a legitimate outcome. Record what was skipped so the gap is
  visible later.

---
