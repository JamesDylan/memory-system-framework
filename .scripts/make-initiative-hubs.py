#!/usr/bin/env python3
"""Create a hub note for each initiative: 1_PROJECTS/{{ORG}}/<Name>/<Name>.md

Why: actions set `category: "[[<Name>]]"`. Without a file of that basename the
link is unresolved and Obsidian creates an empty note at the vault root.
The hub gives the link a target and acts as a one-page dashboard.

The hub holds no facts: it only embeds sections of STATE/BRIEF and an inline
base of actions that link to it. Re-run safely: existing hubs are skipped
unless --force. A file of the same name that isn't a hub is never overwritten.

Usage: python3 .scripts/make-initiative-hubs.py [--force] [vault_root]
"""
from __future__ import annotations  # list[str] | None hints on the system python3 (3.9), which launchd seats use
import re
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if not a.startswith("--")]
FORCE = "--force" in sys.argv
ROOT = Path(args[0]) if args else Path(__file__).resolve().parent.parent
ORG_DIR = ROOT / "1_PROJECTS" / "{{ORG}}"

STATE_SECTIONS = ["Right now", "Next decision needed", "Blocker", "Risks"]

BASE = '''```base
filters:
  and:
    - type == "action"
    - file.hasLink(this.file)
formulas:
  status_icon: if(status == "done", "✅ Done", if(status == "in_progress", "🔵 In Progress", if(status == "blocked", "⏸ Blocked", "⚪ Open")))
  priority_icon: if(priority == "now", "🔴 Now", if(priority == "next", "🟡 Next", "⚪ Later"))
  priority_rank: if(priority == "now", 1, if(priority == "next", 2, 3))
  surface_state: if(due < today(), "🔴 Overdue", if(flag_from <= today(), "🟠 Raise now", ""))
properties:
  formula.status_icon:
    displayName: Status
  formula.priority_icon:
    displayName: Priority
  formula.surface_state:
    displayName: Surface
views:
  - type: table
    name: Open
    filters:
      and:
        - status != "done"
    order:
      - file.name
      - formula.priority_icon
      - formula.status_icon
      - owner
      - due
      - formula.surface_state
    sort:
      - property: formula.priority_rank
        direction: ASC
      - property: due
        direction: ASC
  - type: table
    name: Done
    filters:
      and:
        - status == "done"
    order:
      - file.name
      - owner
      - raised
    sort:
      - property: raised
        direction: DESC
```'''


def headings(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [m.group(1).strip() for m in re.finditer(r"^## (.+)$", path.read_text(), re.M)]


def first_match(heads: list[str], wanted: str) -> str | None:
    # "Right now (Q3 C1: ...)" still counts as "Right now"
    for h in heads:
        if h == wanted or h.startswith(wanted + " ("):
            return h
    return None


def build(name: str, folder: Path) -> str:
    rel = "1_PROJECTS/{{ORG}}/" + name  # not an f-string: it would halve the placeholder braces
    docs = [d for d in ["STATE", "BRIEF", "LOG", "OPEN_QUESTIONS", "README", "PCB"]
            if (folder / f"{d}.md").exists()]
    state_heads = headings(folder / "STATE.md")
    brief_heads = headings(folder / "BRIEF.md")

    out = [
        "---",
        "type: initiative-hub",
        f'initiative: "{name}"',
        "---",
        "",
        f"# {name}",
        "",
        "> Dashboard only. Facts live in the files below; edit them, not this page.",
        "",
        "**Docs:** " + " · ".join(f"[[{rel}/{d}|{d}]]" for d in docs),
        "",
    ]
    std = set(docs) | {name, "diff-log"}
    other = sorted(p.stem for p in folder.glob("*.md") if p.stem not in std)
    if other:
        out += ["**Other notes:** " + " · ".join(f"[[{rel}/{o}|{o}]]" for o in other), ""]
    out += [
        "## Open actions",
        "",
        BASE,
        "",
    ]
    state_embeds = [h for h in (first_match(state_heads, s) for s in STATE_SECTIONS) if h]
    if state_embeds:
        out += ["## State", ""]
        out += [f"![[{rel}/STATE#{h}]]\n" for h in state_embeds]
    links = []
    if "Links" in brief_heads:
        links.append(f"![[{rel}/BRIEF#Links]]")
    if first_match(state_heads, "Pointers"):
        links.append(f"![[{rel}/STATE#Pointers]]")
    if links:
        out += ["## Links", ""] + [l + "\n" for l in links]
    return "\n".join(out).rstrip() + "\n"


created, skipped = [], []
for folder in sorted(p for p in ORG_DIR.iterdir() if p.is_dir()):
    name = folder.name
    if not any((folder / f"{d}.md").exists() for d in ["STATE", "BRIEF", "README", "PCB"]):
        continue
    hub = folder / f"{name}.md"
    if hub.exists():
        is_hub = "type: initiative-hub" in hub.read_text()[:200]
        if not is_hub or not FORCE:
            skipped.append(f"{name} ({'not a hub, left alone' if not is_hub else 'exists'})")
            continue
    hub.write_text(build(name, folder))
    created.append(name)

print("Created/updated:", *created, sep="\n  ")
print("Skipped:", *skipped, sep="\n  ")
