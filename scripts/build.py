#!/usr/bin/env python3
"""Generate the Claude Code layer from the portable `.agent/` source of truth.

`.agent/` is hand-edited and tool-neutral. Everything this script writes is
derived from it and must never be edited directly:

    AGENTS.md                     agent definition + every skill body
    skills/<name>/SKILL.md        YAML frontmatter + verbatim body
    commands/<name>.md            thin wrapper
    .claude-plugin/plugin.json    plugin meta + explicit component arrays
    README.md                     the block between the generated markers

Run from the plugin root:

    python3 scripts/build.py            # write
    python3 scripts/build.py --check    # exit 1 if anything on disk is stale
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / ".agent"
MANIFEST = AGENT_DIR / "manifest.json"
AGENT_MD = AGENT_DIR / "agent.md"
SKILL_SRC = AGENT_DIR / "skills"

BEGIN = "<!-- BEGIN GENERATED: components -->"
END = "<!-- END GENERATED: components -->"

BANNER = (
    "<!-- GENERATED FILE — do not edit. Source: .agent/  "
    "Regenerate: python3 scripts/build.py -->"
)


# --------------------------------------------------------------------------
# load
# --------------------------------------------------------------------------

def load():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plugin = data["plugin"]
    skills = data["skills"]

    seen = set()
    for s in skills:
        name = s["name"]
        if name in seen:
            sys.exit(f"error: duplicate skill name: {name}")
        seen.add(name)
        body = SKILL_SRC / f"{name}.md"
        if not body.is_file():
            sys.exit(f"error: manifest lists '{name}' but {body.relative_to(ROOT)} is missing")
        for field in ("summary", "triggers", "tools"):
            if not s.get(field):
                sys.exit(f"error: skill '{name}' is missing required field '{field}'")
        s["body"] = body.read_text(encoding="utf-8").strip()

    orphans = sorted(
        p.stem for p in SKILL_SRC.glob("*.md") if p.stem not in seen
    )
    if orphans:
        sys.exit(
            "error: skill bodies with no manifest entry: " + ", ".join(orphans)
        )

    cmd_names = [s["command"]["name"] for s in skills if s.get("command")]
    dupes = sorted({c for c in cmd_names if cmd_names.count(c) > 1})
    if dupes:
        sys.exit(f"error: duplicate command name(s): {', '.join(dupes)}")

    return plugin, skills


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def description(skill):
    """Assemble the house-style skill description.

    `<summary> Triggers - "a", "b", "c".`

    The trailing `Triggers` clause uses a hyphen, not a colon: a colon inside an
    unquoted YAML scalar would terminate the value.
    """
    triggers = ", ".join(f'"{t}"' for t in skill["triggers"])
    summary = skill["summary"].rstrip()
    if not summary.endswith("."):
        summary += "."
    text = f"{summary} Triggers - {triggers}."
    if ":" in text:
        sys.exit(
            f"error: skill '{skill['name']}' description contains a colon, which "
            f"would break unquoted YAML. Rewrite it without one."
        )
    return text


def demote(markdown, levels):
    """Shift ATX headings deeper by `levels`, leaving fenced code blocks alone.

    Skill bodies are authored to stand alone, so they open at `#`. When they are
    inlined under a heading in AGENTS.md they have to sit below it instead.
    """
    out = []
    fence = None
    for line in markdown.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            out.append(line)
            continue
        if fence is None and stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            rest = stripped[hashes:]
            if rest.startswith(" ") or rest == "":
                out.append("#" * min(hashes + levels, 6) + rest)
                continue
        out.append(line)
    return "\n".join(out)


def skill_md(skill):
    return "\n".join([
        "---",
        f"name: {skill['name']}",
        f"description: {description(skill)}",
        f"disable-model-invocation: {str(bool(skill.get('disableModelInvocation'))).lower()}",
        f"allowed-tools: {', '.join(skill['tools'])}",
        "---",
        "",
        skill["body"],
        "",
    ])


def command_md(plugin, skill):
    cmd = skill["command"]
    for field in ("description", "argumentHint"):
        if ":" in str(cmd.get(field, "")):
            sys.exit(
                f"error: command '{cmd['name']}' has a colon in its {field}, which "
                f"would break unquoted YAML frontmatter."
            )
    lines = ["---", f"description: {cmd['description']}"]
    if cmd.get("argumentHint"):
        lines.append(f"argument-hint: {cmd['argumentHint']}")
    lines += [
        "---",
        "",
        f"Invoke the `{skill['name']}` skill.",
        "",
        cmd.get("body", "").strip() or f"Arguments, if any, arrive in $ARGUMENTS.",
        "",
    ]
    return "\n".join(lines)


def plugin_json(plugin, skills):
    out = {
        "name": plugin["name"],
        "description": plugin["description"],
        "version": plugin["version"],
        "author": plugin["author"],
        "license": plugin["license"],
        "repository": plugin["repository"],
        "commands": [
            f"./commands/{s['command']['name']}.md" for s in skills if s.get("command")
        ],
        "skills": [f"./skills/{s['name']}/" for s in skills],
        "keywords": plugin["keywords"],
    }
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


def split_title(body):
    """Return (title, body-without-its-leading-H1).

    Skill bodies open with their own H1 so they read standalone. AGENTS.md emits
    that title as the section heading instead, so the duplicate has to go.
    """
    lines = body.split("\n")
    if lines and lines[0].startswith("# "):
        rest = lines[1:]
        while rest and not rest[0].strip():
            rest.pop(0)
        return lines[0][2:].strip(), "\n".join(rest)
    return None, body


def agents_md(plugin, skills):
    parts = [
        BANNER,
        "",
        AGENT_MD.read_text(encoding="utf-8").strip(),
        "",
        "## Skills",
        "",
        "Each skill below is a self-contained capability. Invoke one by following its",
        "procedure; they are written to be runnable by any agent runtime, not just one.",
        "",
    ]
    for s in skills:
        requires = s.get("requires") or []
        title, body = split_title(s["body"])
        parts += [
            f"### {title or s['name']}",
            "",
            f"**Name.** `{s['name']}`",
            "",
            f"**When to use.** {s['summary'].rstrip()}",
            "",
            f"**Triggers.** {', '.join(s['triggers'])}",
            "",
        ]
        if requires:
            parts += [f"**Requires.** `{'`, `'.join(requires)}`", ""]
        parts += [demote(body, 2), "", "---", ""]
    return "\n".join(parts).rstrip() + "\n"



def readme_block(plugin, skills):
    lines = [BEGIN, "", "## Commands", ""]
    for s in skills:
        if s.get("command"):
            c = s["command"]
            hint = f" {c['argumentHint']}" if c.get("argumentHint") else ""
            lines.append(f"- `/{plugin['name']}:{c['name']}{hint}` — {c['description']}")
    lines += ["", "## Skills", ""]
    for s in skills:
        lines.append(f"- **{s['name']}** — {s['summary'].rstrip()}")
    lines += ["", END]
    return "\n".join(lines)


def render(plugin, skills):
    """Return {relative path: content} for every generated file."""
    files = {
        "AGENTS.md": agents_md(plugin, skills),
        ".claude-plugin/plugin.json": plugin_json(plugin, skills),
    }
    for s in skills:
        files[f"skills/{s['name']}/SKILL.md"] = skill_md(s)
        if s.get("command"):
            files[f"commands/{s['command']['name']}.md"] = command_md(plugin, s)

    readme = ROOT / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        if BEGIN in text and END in text:
            head, rest = text.split(BEGIN, 1)
            _, tail = rest.split(END, 1)
            files["README.md"] = head + readme_block(plugin, skills) + tail
        else:
            sys.exit(
                f"error: README.md is missing the generated markers.\n"
                f"  Add these two lines where the component index belongs:\n"
                f"    {BEGIN}\n    {END}"
            )
    return files


# --------------------------------------------------------------------------
# write / check
# --------------------------------------------------------------------------

def stale_dirs(skills):
    """Generated skill and command files that no longer have a manifest entry."""
    keep_skills = {s["name"] for s in skills}
    keep_cmds = {s["command"]["name"] for s in skills if s.get("command")}
    stale = []
    for d in sorted((ROOT / "skills").glob("*")):
        if d.is_dir() and d.name not in keep_skills:
            stale.append(d)
    for f in sorted((ROOT / "commands").glob("*.md")):
        if f.stem not in keep_cmds:
            stale.append(f)
    return stale


def main():
    check = "--check" in sys.argv[1:]
    plugin, skills = load()
    files = render(plugin, skills)

    drift = []
    for rel, content in sorted(files.items()):
        path = ROOT / rel
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == content:
            continue
        drift.append(rel)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    stale = stale_dirs(skills)
    for path in stale:
        drift.append(str(path.relative_to(ROOT)) + " (stale)")
        if not check:
            shutil.rmtree(path) if path.is_dir() else path.unlink()

    if check:
        if drift:
            print("stale generated files:", file=sys.stderr)
            for d in drift:
                print(f"  {d}", file=sys.stderr)
            print("\nrun: python3 scripts/build.py", file=sys.stderr)
            return 1
        print(f"up to date — {len(files)} generated files match .agent/")
        return 0

    if drift:
        print(f"wrote {len(drift)} file(s):")
        for d in drift:
            print(f"  {d}")
    else:
        print("nothing to do — already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
