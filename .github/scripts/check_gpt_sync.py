"""Enforce SKILL <-> GPT parity so the ChatGPT versions never drift from the skills.

For every skill in skills/<name>/ this checks that:
  1. A paired gpts/<name>/ exists with both GPT.md and openapi.yaml.
  2. The GPT.md `version` matches the SKILL.md `version`.

Run:  python .github/scripts/check_gpt_sync.py
Exits non-zero on any mismatch, so it can gate CI. When it fails because a skill
changed, update the paired GPT.md (bump its version, mirror the change) and
regenerate the openapi with generate_gpt_openapi.py.

Skills intentionally without a ChatGPT version can be listed in NO_GPT.
"""

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS, GPTS = os.path.join(REPO, "skills"), os.path.join(REPO, "gpts")

NO_GPT = set()  # skills that deliberately have no ChatGPT counterpart


def version_of(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"version:\s*(\S+)", line)
            if m:
                return m.group(1)
    return None


def main():
    errors = []
    skills = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))
    for name in skills:
        if name in NO_GPT:
            continue
        gpt_dir = os.path.join(GPTS, name)
        gpt_md = os.path.join(gpt_dir, "GPT.md")
        openapi = os.path.join(gpt_dir, "openapi.yaml")
        if not os.path.isdir(gpt_dir):
            errors.append(f"{name}: no paired gpts/{name}/ (add a ChatGPT version or list it in NO_GPT)")
            continue
        if not os.path.isfile(gpt_md):
            errors.append(f"{name}: gpts/{name}/GPT.md missing")
        if not os.path.isfile(openapi):
            errors.append(f"{name}: gpts/{name}/openapi.yaml missing (run generate_gpt_openapi.py)")
        sv, gv = version_of(os.path.join(SKILLS, name, "SKILL.md")), version_of(gpt_md)
        if sv and gv and sv != gv:
            errors.append(f"{name}: version mismatch — SKILL.md {sv} vs GPT.md {gv} "
                          f"(bump the GPT to {sv} and mirror the change)")

    if errors:
        print("SKILL <-> GPT sync check FAILED:\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"✓ All {len(skills)} skills are in sync with their GPTs (paired + version parity).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
