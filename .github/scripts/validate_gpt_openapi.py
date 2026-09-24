"""Validate the generated GPT Action specs against ChatGPT's import rules and their GPT.md.

Offline check (no network) — runs in CI. For every gpts/<name>/ it checks that:
  1. openapi.yaml parses, every operation has an operationId (unique) and a description of
     1..300 chars (ChatGPT GPT Actions hard limit).
  2. Every `type: object` schema has `properties` (ChatGPT rejects e.g. a bare Map_String).
  3. Every local `$ref` resolves.
  4. The operations in openapi.yaml are exactly GPT_OPERATIONS[<name>] from
     generate_gpt_openapi.py, none is deprecated (in the spec or the edge-operations catalog).
  5. Every Edge action GPT.md names (`operationId` or `mcp-tool-name` in backticks) is in its
     openapi.yaml. A deprecated action may only be named on a line that says it is deprecated
     or replaced. Verb-style names that are not real operationIds (e.g. `listWorkspaces`) fail.

Run:  python .github/scripts/validate_gpt_openapi.py
Fix failures by editing GPT_OPERATIONS / GPT.md and re-running generate_gpt_openapi.py.
"""

import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_gpt_openapi import (  # noqa: E402
    CATALOG, DESCRIPTION_LIMIT, GPT_OPERATIONS, GPTS_DIR, OPERATION_EXTENSION,
)

HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}
ACTION_VERB = re.compile(
    r"^(list|get|create|update|delete|find|search|read|add|remove|cancel|export|fetch|mark|"
    r"attach|detach|activate|deactivate)[A-Z][A-Za-z0-9]*$")
DEPRECATION_CONTEXT = re.compile(r"deprecat|replaced|removed", re.IGNORECASE)
BACKTICKED = re.compile(r"`([A-Za-z][A-Za-z0-9-]*)`")


def walk_schemas(node, where, errors):
    if isinstance(node, dict):
        t = node.get("type")
        if (t == "object" or (isinstance(t, list) and "object" in t)) and "properties" not in node:
            errors.append(f"{where}: object schema missing `properties`")
        for k, v in node.items():
            walk_schemas(v, f"{where}.{k}", errors)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_schemas(v, f"{where}[{i}]", errors)


def collect_refs(node, found):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str):
                found.add(v)
            else:
                collect_refs(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, found)


def collect_names(node, found):
    """Property and parameter names, so field names in GPT.md are not mistaken for actions."""
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            found.update(props)
        if "in" in node and isinstance(node.get("name"), str):
            found.add(node["name"])
        for v in node.values():
            collect_names(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_names(v, found)


def load_catalog(errors):
    if not os.path.isfile(CATALOG):
        errors.append(f"{os.path.relpath(CATALOG)} missing (run generate_gpt_openapi.py)")
        return {}
    with open(CATALOG, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("operations", {})


def validate_spec(gpt, doc, catalog, errors):
    """Returns {mcp-tool-name: operationId} for the ops in the spec."""
    ops, seen_ids = {}, set()
    for path, item in (doc.get("paths") or {}).items():
        for method, op in (item or {}).items():
            if method not in HTTP_METHODS or not isinstance(op, dict):
                continue
            where = f"{gpt}: {method.upper()} {path}"
            oid = op.get("operationId")
            if not oid:
                errors.append(f"{where}: missing operationId")
            elif oid in seen_ids:
                errors.append(f"{where}: duplicate operationId {oid}")
            seen_ids.add(oid)
            desc = op.get("description") or ""
            if not desc.strip():
                errors.append(f"{where} ({oid}): empty description")
            elif len(desc) > DESCRIPTION_LIMIT:
                errors.append(f"{where} ({oid}): description has {len(desc)} chars > {DESCRIPTION_LIMIT}")
            name = op.get(OPERATION_EXTENSION)
            if not name:
                errors.append(f"{where} ({oid}): missing {OPERATION_EXTENSION} (regenerate)")
                continue
            if op.get("deprecated") or catalog.get(name, {}).get("deprecated"):
                repl = catalog.get(name, {}).get("replacement", "?")
                errors.append(f"{where}: {name} is deprecated (use {repl})")
            ops[name] = oid
    walk_schemas(doc.get("components", {}).get("schemas", {}), f"{gpt}: components.schemas", errors)
    walk_schemas(doc.get("paths", {}), f"{gpt}: paths", errors)
    schemas = doc.get("components", {}).get("schemas", {}) or {}
    refs = set()
    collect_refs(doc, refs)
    for ref in sorted(refs):
        if not ref.startswith("#/components/schemas/") or ref.rsplit("/", 1)[1] not in schemas:
            errors.append(f"{gpt}: unresolved $ref {ref}")
    expected = GPT_OPERATIONS.get(gpt)
    if expected is None:
        errors.append(f"{gpt}: not listed in GPT_OPERATIONS (generate_gpt_openapi.py)")
    else:
        for name in expected:
            if name not in ops:
                errors.append(f"{gpt}: GPT_OPERATIONS op {name} missing from openapi.yaml (regenerate)")
            elif catalog and name not in catalog:
                errors.append(f"{gpt}: GPT_OPERATIONS op {name} not in the Edge catalog")
        for name in ops:
            if name not in expected:
                errors.append(f"{gpt}: openapi.yaml op {name} not in GPT_OPERATIONS (regenerate)")
    return ops


def validate_gpt_md(gpt, text, ops, doc, catalog, errors):
    by_id = {e["operationId"]: n for n, e in catalog.items()}
    in_spec = set(ops) | set(ops.values())
    fields = set()
    collect_names(doc, fields)
    mentioned = {by_id.get(t, t) for t in BACKTICKED.findall(text)}
    for lineno, line in enumerate(text.splitlines(), 1):
        for token in BACKTICKED.findall(line):
            name = by_id.get(token) or (token if token in catalog else None)
            where = f"{gpt}/GPT.md:{lineno}"
            if name:
                if token in in_spec or name in ops:
                    continue
                repl = catalog[name].get("replacement")
                if (catalog[name].get("deprecated") and DEPRECATION_CONTEXT.search(line)
                        and (repl is None or (repl in ops and repl in mentioned))):
                    continue  # documented as "don't use"; its replacement is in the spec and named too
                hint = " (deprecated, use " + catalog[name]["replacement"] + ")" \
                    if catalog[name].get("replacement") else ""
                errors.append(f"{where}: `{token}` is not in openapi.yaml{hint}")
            elif ACTION_VERB.match(token) and token not in fields:
                errors.append(f"{where}: `{token}` looks like an action but is not an Edge operationId")


def main():
    errors = []
    catalog = load_catalog(errors)
    gpts = sorted(d for d in os.listdir(GPTS_DIR) if os.path.isdir(os.path.join(GPTS_DIR, d)))
    for gpt in gpts:
        spec_path = os.path.join(GPTS_DIR, gpt, "openapi.yaml")
        md_path = os.path.join(GPTS_DIR, gpt, "GPT.md")
        if not os.path.isfile(spec_path):
            errors.append(f"{gpt}: openapi.yaml missing")
            continue
        try:
            with open(spec_path, encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            errors.append(f"{gpt}: openapi.yaml does not parse: {e}")
            continue
        ops = validate_spec(gpt, doc, catalog, errors)
        if os.path.isfile(md_path):
            with open(md_path, encoding="utf-8") as f:
                validate_gpt_md(gpt, f.read(), ops, doc, catalog, errors)
    for gpt in GPT_OPERATIONS:
        if gpt not in gpts:
            errors.append(f"{gpt}: in GPT_OPERATIONS but gpts/{gpt}/ does not exist")

    if errors:
        print("GPT Actions validation FAILED:\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"✓ All {len(gpts)} GPT Action specs are ChatGPT-importable and match their GPT.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
