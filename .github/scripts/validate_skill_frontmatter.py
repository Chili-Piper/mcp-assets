"""Validates that every skills/<name>/SKILL.md has well-formed, complete frontmatter.

Run from the repo root:  python .github/scripts/validate_skill_frontmatter.py
Exits non-zero if any skill is malformed, so it can gate CI.
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


def validate_skill(skill_dir):
    errors = []
    name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isfile(skill_md):
        return [f"{name}: missing SKILL.md"]

    try:
        fm = parse_frontmatter(skill_md)
    except ValueError as exc:
        return [f"{name}/SKILL.md: {exc}"]

    if fm is None:
        return [f"{name}/SKILL.md: missing or unterminated YAML frontmatter"]

    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] in (None, "", []):
            errors.append(f"{name}/SKILL.md: missing required field '{field}'")

    if fm.get("name") and fm["name"] != name:
        errors.append(
            f"{name}/SKILL.md: frontmatter name '{fm['name']}' does not match directory '{name}'"
        )

    return errors


def main():
    if not os.path.isdir(SKILLS_DIR):
        print(f"No '{SKILLS_DIR}/' directory found — nothing to validate.")
        return 0

    all_errors = []
    skill_dirs = sorted(
        os.path.join(SKILLS_DIR, d)
        for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
    )

    for skill_dir in skill_dirs:
        all_errors.extend(validate_skill(skill_dir))

    if all_errors:
        print("Skill frontmatter validation FAILED:\n")
        for err in all_errors:
            print(f"  ✗ {err}")
        return 1

    print(f"✓ All {len(skill_dirs)} skills have valid frontmatter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
