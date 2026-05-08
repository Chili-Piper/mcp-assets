"""Validates that recipe markdown files contain required frontmatter fields."""

import os
import sys
import yaml

REQUIRED_FIELDS = [
    "title",
    "contributor",
    "stage",
    "persona",
    "stack",
    "humans_in_loop",
    "agent_does",
    "human_decision_points",
    "data_sources",
    "data_handling",
    "revenue_impact",
    "measurement",
    "maturity",
]

REQUIRED_DATA_HANDLING = ["pii_present", "storage", "outputs_go_to"]
REQUIRED_REVENUE_IMPACT = ["optimizes_for", "expected_lift", "evidence_strength", "measurement_horizon"]
REQUIRED_MEASUREMENT = ["writes_to", "attribution_signal", "optimization_loop"]

VALID_STAGES = [
    "awareness", "education", "selection", "onboarding",
    "impact", "expansion", "orchestration", "measurement", "leverage"
]

VALID_MATURITY = ["idea", "draft", "tested", "proven"]
VALID_EVIDENCE = ["anecdotal", "one-team", "multi-team", "benchmarked"]


def parse_frontmatter(filepath):
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    return yaml.safe_load(content[3:end])


def validate(filepath):
    errors = []
    fm = parse_frontmatter(filepath)
    if fm is None:
        return [f"{filepath}: missing YAML frontmatter"]

    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"{filepath}: missing required field '{field}'")

    if "stage" in fm and fm["stage"] not in VALID_STAGES:
        errors.append(f"{filepath}: invalid stage '{fm['stage']}' — must be one of {VALID_STAGES}")

    if "maturity" in fm and fm["maturity"] not in VALID_MATURITY:
        errors.append(f"{filepath}: invalid maturity '{fm['maturity']}' — must be one of {VALID_MATURITY}")

    if "data_handling" in fm and isinstance(fm["data_handling"], dict):
        for f in REQUIRED_DATA_HANDLING:
            if f not in fm["data_handling"]:
                errors.append(f"{filepath}: data_handling missing '{f}'")

    if "revenue_impact" in fm and isinstance(fm["revenue_impact"], dict):
        for f in REQUIRED_REVENUE_IMPACT:
            if f not in fm["revenue_impact"]:
                errors.append(f"{filepath}: revenue_impact missing '{f}'")

    if "measurement" in fm and isinstance(fm["measurement"], dict):
        for f in REQUIRED_MEASUREMENT:
            if f not in fm["measurement"]:
                errors.append(f"{filepath}: measurement missing '{f}'")

    return errors


def main():
    all_errors = []
    for root, _, files in os.walk("recipes"):
        for filename in files:
            if filename.endswith(".md") and filename != "README.md":
                path = os.path.join(root, filename)
                all_errors.extend(validate(path))

    if all_errors:
        print("Frontmatter validation failed:\n")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("All recipe frontmatter valid.")


if __name__ == "__main__":
    main()
