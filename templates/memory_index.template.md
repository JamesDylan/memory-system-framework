# Memory System — Master Guide
**Version:** 1.0
**Last Updated:** {{TODAY}}
**Owner:** {{OWNER_NAME}}

---

## What This Is

An external working memory for {{OWNER_NAME}}'s role at {{ORG}} ({{PRODUCT}}). It lets an agent give specific advice from real metrics, relationships, projects and decisions.

**Two vaults:** this folder is the shared vault. Private material lives in a separate private vault mounted at `_private/`. Operating rules are in `AGENTS.md`; the full rules in `docs/doctrine.md`.

---

## Loading model — read only what you need

**Default first read:** `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md`, then `1_PROJECTS/Actions/` (shared) and `_private/1_PROJECTS/Actions/` (yours) for open actions.

| Question | Also read |
|---|---|
| Project deep-dive | `1_PROJECTS/{{ORG}}/[Project]/STATE.md`, then `BRIEF.md` |
| Strategy, prioritisation | `2_AREAS/{{ORG}}/context/strategic_context.md`, `metrics_dashboard.md` |
| People outside the team | `2_AREAS/{{ORG}}/context/stakeholder_map.md` |
| Coaching, team | `_private/2_AREAS/{{ORG}}/My Team/Direct Reports.md` |
| Catch-up after a gap | `CHANGELOG.md` first |

Do not read `_private/0_INBOX/` or `4_ARCHIVE/` unless asked or checking a cited source.

---

## Single Sources of Truth — Hard Rule

Each fact type has one file. Edit that file. Never copy the fact elsewhere.

| Fact type | Canonical file |
|---|---|
| Current cycle, project health, owners | `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md` |
| Status of one project | `1_PROJECTS/{{ORG}}/[Project]/STATE.md` |
| Why and scope of one project | `1_PROJECTS/{{ORG}}/[Project]/BRIEF.md` |
| History of one project | `1_PROJECTS/{{ORG}}/[Project]/LOG.md` |
| Open actions | `1_PROJECTS/Actions/` for initiatives, `_private/1_PROJECTS/Actions/` for your own (one file each) |
| Metric values | `2_AREAS/{{ORG}}/_metrics/registry.yaml` |
| Strategy, targets | `2_AREAS/{{ORG}}/context/strategic_context.md` |
| Stakeholders | `2_AREAS/{{ORG}}/context/stakeholder_map.md` |
| Systems and concepts | `3_RESOURCES/{{ORG}}/concepts/` |
| Uncommitted ideas | `2_AREAS/{{ORG}}/_H2 Roadmap/CANDIDATES.md` |
| Direct reports, coaching | `_private/2_AREAS/{{ORG}}/My Team/Direct Reports.md` |
| Organisation values for skills | `ORG.md` |
| Owner values for skills | `_private/ME.md` |

---

## Quick Reference — File Map

Register every new canonical file and every skill here. Lint reports skills that are on disk and not listed.

### AI Skills

| Skill | Use |
|---|---|
| `AI Skills/setup/SKILL.md` | First-run interview that builds the vaults (already run for this vault) |
| `AI Skills/second-brain/SKILL.md` | Start of any conversation needing work context |
| `AI Skills/daily-slack-review/SKILL.md` | Daily capture from chat |
| `AI Skills/ingest/SKILL.md` | Process the inbox |
| `AI Skills/diff-propose/SKILL.md` | Propose STATE changes for review |
| `AI Skills/lint/SKILL.md` | Health check |
| `AI Skills/challenge/SKILL.md`, `emerge`, `connect`, `calibrate`, `review-prep`, `debloat`, `watch`, `memory-system-upgrade` | See each file |

---

## Update Rules

| Trigger | Update |
|---|---|
| New raw input | Drop in `_private/0_INBOX/`, then run `ingest` |
| Project health change | `_ACTIVE_CYCLE.md` and the project's `STATE.md` |
| Decision made | The project's `LOG.md` and `CHANGELOG.md` |
| New metric data | The metrics registry |
| Structural change to the vault | `CHANGELOG.md` and this file's `Last Updated`, in the same pass |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | {{TODAY}} | Created from the framework. |
