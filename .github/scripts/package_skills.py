"""Package each skill into an upload-ready .zip for Claude Desktop / Claude.ai.

Claude's Customize → Skills panel installs a skill from a .zip whose ROOT contains
SKILL.md (plus a references/ subfolder for multi-file skills). This script builds one
such .zip per skill in skills/, so non-CLI users (Claude Desktop, claude.ai) can add
them as Personal skills — or admins can upload them as Organization skills.

Run:  python .github/scripts/package_skills.py
Output: dist/skills/<skill>.zip  (dist/ is gitignored; attach these to a GitHub Release:
        gh release upload v1.0.0 dist/skills/*.zip --clobber)

These zips are the Desktop/claude.ai equivalent of the Claude Code plugin — same skills,
different delivery surface. Re-run after changing any skill, then re-upload to the release.
"""

import os
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(REPO, "skills")
OUT_DIR = os.path.join(REPO, "dist", "skills")


def package(skill_dir, out_zip):
    """Zip the CONTENTS of skill_dir (SKILL.md at the archive root, references/ preserved)."""
    file_count = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(skill_dir):
            for name in sorted(files):
                if name == ".DS_Store":
                    continue
                abs_path = os.path.join(root, name)
                arcname = os.path.relpath(abs_path, skill_dir)  # SKILL.md, references/foo.md
                zf.write(abs_path, arcname)
                file_count += 1
    return file_count


def main():
    if not os.path.isdir(SKILLS_DIR):
        print(f"No '{SKILLS_DIR}' directory.")
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    skills = sorted(
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
        and os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))
    )
    for name in skills:
        out_zip = os.path.join(OUT_DIR, f"{name}.zip")
        n = package(os.path.join(SKILLS_DIR, name), out_zip)
        print(f"✓ {name}.zip ({n} file{'s' if n != 1 else ''})")
    print(f"\nPackaged {len(skills)} skills → {os.path.relpath(OUT_DIR, REPO)}/")
    print("Attach to the release:  gh release upload v1.0.0 dist/skills/*.zip --clobber")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
