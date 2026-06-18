"""Validate skill frontmatter AND progressive-disclosure structure.

Run from the repo root:  python .github/scripts/validate_skill_frontmatter.py

Two classes of check (see docs/methodology.md for the why):

  ERRORS (exit non-zero — gate CI):
    - SKILL.md exists with well-formed, complete frontmatter
    - frontmatter `name` matches the directory
    - every `references:` entry has a matching references/<name>.md  (and vice versa,
      so a reference is never orphaned or unlisted — canonical, one-way wiring)
    - no references/*.md exceeds the 200-line load budget

  WARNINGS (printed, do NOT fail — they flag structural debt to pay down):
    - SKILL.md over 200 lines (push deep detail into references/)
    - frontmatter `description` over 280 chars (it's a discovery line, one sentence)
"""

import os
import sys
import yaml

SKILLS_DIR = "skills"

REQUIRED_FIELDS = [
    "name",          # must match the directory name (kebab-case)
    "description",   # one sentence, used by agents to decide whether to load
    "version",       # semver, e.g. 0.3.0
    "tools_required",  # MCP names the skill needs
    "writes_to",     # where outputs go, or "Nothing — read-only"
]

# Progressive-disclosure file budgets (docs/methodology.md "File budgets")
REFERENCE_MAX_LINES = 200   # hard — a reference must load whole
SKILL_MAX_LINES = 200       # soft — over this, split into references/
DESCRIPTION_MAX_CHARS = 280  # soft — the description is a router, not a summary


def parse_frontmatter(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}")


def line_count(filepath):
    with open(filepath, encoding="utf-8") as f:
        return sum(1 for _ in f)


def validate_skill(skill_dir):
    """Return (errors, warnings) for one skill directory."""
    errors, warnings = [], []
    name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isfile(skill_md):
        return [f"{name}: missing SKILL.md"], warnings

    try:
        fm = parse_frontmatter(skill_md)
    except ValueError as exc:
        return [f"{name}/SKILL.md: {exc}"], warnings

    if fm is None:
        return [f"{name}/SKILL.md: missing or unterminated YAML frontmatter"], warnings

    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] in (None, "", []):
            errors.append(f"{name}/SKILL.md: missing required field '{field}'")

    if fm.get("name") and fm["name"] != name:
        errors.append(
            f"{name}/SKILL.md: frontmatter name '{fm['name']}' does not match directory '{name}'"
        )

    # --- progressive-disclosure structure: references <-> frontmatter consistency ---
    declared = fm.get("references") or []
    if not isinstance(declared, list):
        errors.append(f"{name}/SKILL.md: 'references' must be a list of basenames")
        declared = []
    declared = [str(r) for r in declared]

    ref_dir = os.path.join(skill_dir, "references")
    on_disk = sorted(
        f[:-3] for f in os.listdir(ref_dir)
        if f.endswith(".md")
    ) if os.path.isdir(ref_dir) else []

    for ref in declared:
        if ref not in on_disk:
            errors.append(
                f"{name}/SKILL.md: references lists '{ref}' but references/{ref}.md does not exist"
            )
    for ref in on_disk:
        if ref not in declared:
            errors.append(
                f"{name}: references/{ref}.md exists but is not listed in SKILL.md frontmatter 'references'"
            )

    # --- file budgets ---
    for ref in on_disk:
        ref_path = os.path.join(ref_dir, f"{ref}.md")
        n = line_count(ref_path)
        if n > REFERENCE_MAX_LINES:
            errors.append(
                f"{name}/references/{ref}.md: {n} lines exceeds the {REFERENCE_MAX_LINES}-line budget"
            )

    n_skill = line_count(skill_md)
    if n_skill > SKILL_MAX_LINES:
        warnings.append(
            f"{name}/SKILL.md: {n_skill} lines (> {SKILL_MAX_LINES}) — consider moving detail into references/"
        )

    desc = fm.get("description") or ""
    if len(desc) > DESCRIPTION_MAX_CHARS:
        warnings.append(
            f"{name}/SKILL.md: description is {len(desc)} chars (> {DESCRIPTION_MAX_CHARS}) — tighten to one routing sentence"
        )

    return errors, warnings


def main():
    if not os.path.isdir(SKILLS_DIR):
        print(f"No '{SKILLS_DIR}/' directory found — nothing to validate.")
        return 0

    all_errors, all_warnings = [], []
    skill_dirs = sorted(
        os.path.join(SKILLS_DIR, d)
        for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
    )

    for skill_dir in skill_dirs:
        errs, warns = validate_skill(skill_dir)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    if all_warnings:
        print("Progressive-disclosure warnings (not failing):\n")
        for w in all_warnings:
            print(f"  ! {w}")
        print()

    if all_errors:
        print("Skill validation FAILED:\n")
        for err in all_errors:
            print(f"  ✗ {err}")
        return 1

    print(f"✓ All {len(skill_dirs)} skills have valid frontmatter and structure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
