"""Generate self-contained GPT Action OpenAPI specs from the live Chili Piper Edge API spec.

Each ChatGPT GPT in gpts/<name>/ gets an openapi.yaml containing ONLY the endpoints that
GPT uses, with the transitive closure of referenced component schemas, the correct production
server URL, and Bearer (apiKeyAuth) security — all extracted verbatim from the canonical Edge
API OpenAPI document so the GPTs never drift from reality.

Source of truth (public): https://fire.chilipiper.com/api/fire-edge/public/org/docs/swagger/docs.yaml
Run:  python .github/scripts/generate_gpt_openapi.py [path-to-local-docs.yaml]

WHY THIS EXISTS
  ChatGPT GPT Actions call the REST API directly with an API key, so each GPT needs a real,
  accurate OpenAPI spec. This script produces those specs from the canonical Edge API document,
  so the GPT Actions always reflect the real endpoints, request bodies, and response schemas —
  no hand-editing, no placeholder URLs, no drift from the API.

  This keeps the GPTs in sync with the *API*. Keeping the GPTs in sync with the *Claude skills*
  is a separate concern, enforced in CI by check_gpt_sync.py (every skill must have a paired GPT
  at a matching version). This script does NOT touch the Claude skills in skills/.

WHEN TO RE-RUN
  - The Edge API changes (new/renamed fields, schemas, or endpoints) → re-run to refresh specs.
  - A GPT should start (or stop) using an operation → first edit GPT_OPERATIONS below, then re-run.
    GPT_OPERATIONS is the one manual step: it maps each GPT to the Edge operations it uses, and
    should mirror the matching skill's `tools_required`. The Edge spec tags every operation with
    `[operation: <name>]` (matching the Chili Piper MCP tool names); use those names here.
"""

import os
import re
import sys
import urllib.request

import yaml

SPEC_URL = "https://fire.chilipiper.com/api/fire-edge/public/org/docs/swagger/docs.yaml"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GPTS_DIR = os.path.join(REPO_ROOT, "gpts")

# GPT -> the Edge operations (== MCP tool names) it needs. Mirror each skill's tools_required.
GPT_OPERATIONS = {
    "meeting-inspector": ["meeting-get", "meeting-list-put", "concierge-list-routers", "concierge-logs", "workspace-list"],
    "no-show-analyzer": ["meeting-list-put", "concierge-list-routers", "concierge-logs", "workspace-list", "user-find-by-ids"],
    "org-meeting": ["meeting-list-put", "workspace-list", "user-find-by-ids"],
    "user-meetings": ["user-find", "meeting-export-v2-put", "workspace-list"],
    "routing-audit": ["workspace-list", "concierge-list-routers", "rule-list", "concierge-logs", "distribution-list-put"],
    "concierge-debugger": ["concierge-list-routers", "concierge-logs", "rule-list", "workspace-list", "user-find-by-ids"],
    "availability-inspector": ["user-find", "user-read", "availability-slots"],
    "user-details": ["user-find", "user-read", "workspace-list", "team-list-put",
                     "scheduling-link-list-personal", "scheduling-link-list-round-robin", "meeting-export-v2-put"],
    "user-copy": ["user-find", "workspace-list", "workspace-list-users", "team-list-put",
                  "workspace-add-users", "team-add-users", "team-create", "user-update-licenses"],
    "user-offboarding": ["user-find", "user-read", "meeting-export-v2-put", "workspace-list", "workspace-list-users",
                         "workspace-remove-users", "team-list-put", "team-remove-users", "team-create", "team-delete",
                         "meeting-cancel", "distribution-list-put"],
    "distribution-analysis": ["workspace-list", "distribution-list-put", "user-find-by-ids", "meeting-list-put"],
    "distro-debugger": ["workspace-list", "distro-logs", "distro-log-get", "distribution-list-put"],
    "chat-conversation-inspector": ["workspace-list", "chat-logs", "user-find-by-ids"],
    "meeting-type-management": ["workspace-list", "meeting-type-list", "meeting-type-get", "meeting-type-create",
                                "meeting-type-update", "meeting-type-delete", "meeting-type-attach-reminder",
                                "meeting-type-detach-reminder", "meeting-type-reminder-list", "meeting-type-reminder-create",
                                "meeting-type-reminder-update", "meeting-type-reminder-delete"],
    "distro-router-configuration": ["workspace-list", "distro-list-routers", "distro-router-get", "distro-router-create",
                                    "distro-router-update", "distro-router-delete", "distro-router-activate",
                                    "distro-router-deactivate", "rule-list", "distribution-list-put"],
}

TITLES = {
    "meeting-inspector": "Chili Piper — Meeting Inspector Actions",
    "no-show-analyzer": "Chili Piper — No-Show Analyzer Actions",
    "org-meeting": "Chili Piper — Org Meeting Snapshot Actions",
    "user-meetings": "Chili Piper — User Meetings Actions",
    "routing-audit": "Chili Piper — Routing Audit Actions",
    "concierge-debugger": "Chili Piper — Concierge Debugger Actions",
    "availability-inspector": "Chili Piper — Availability Inspector Actions",
    "user-details": "Chili Piper — User Details Actions",
    "user-copy": "Chili Piper — User Copy Actions",
    "user-offboarding": "Chili Piper — User Offboarding Actions",
    "distribution-analysis": "Chili Piper — Distribution Analysis Actions",
    "distro-debugger": "Chili Piper — Distribution Debugger Actions",
    "chat-conversation-inspector": "Chili Piper — Chat Conversation Inspector Actions",
    "meeting-type-management": "Chili Piper — Meeting Type Management Actions",
    "distro-router-configuration": "Chili Piper — Distro Router Configuration Actions",
}


def load_spec(path=None):
    if path:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    with urllib.request.urlopen(SPEC_URL, timeout=60) as resp:
        return yaml.safe_load(resp.read())


def build_operation_index(spec):
    """operation-name -> (method, path, operation-object)."""
    index = {}
    for path, item in spec.get("paths", {}).items():
        for method, op in item.items():
            if not isinstance(op, dict):
                continue
            m = re.search(r"\[operation:\s*([^\]]+)\]", op.get("description", "") or "")
            if m:
                index[m.group(1).strip()] = (method, path, op)
    return index


def collect_refs(obj, found):
    """Walk obj, collecting all #/components/schemas/<name> references."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str) and v.startswith("#/components/schemas/"):
                found.add(v.rsplit("/", 1)[1])
            else:
                collect_refs(v, found)
    elif isinstance(obj, list):
        for v in obj:
            collect_refs(v, found)


def closure(schema_names, all_schemas):
    """Transitive closure of schema refs."""
    resolved, queue = set(), list(schema_names)
    while queue:
        name = queue.pop()
        if name in resolved or name not in all_schemas:
            resolved.add(name)
            continue
        resolved.add(name)
        nested = set()
        collect_refs(all_schemas[name], nested)
        queue.extend(n for n in nested if n not in resolved)
    return {n: all_schemas[n] for n in resolved if n in all_schemas}


def op_id(operation_name):
    parts = re.split(r"[-_]", operation_name)
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def generate(spec, index, gpt, operations):
    all_schemas = spec.get("components", {}).get("schemas", {})
    sec = spec.get("components", {}).get("securitySchemes", {})
    paths, refs = {}, set()
    missing = []
    for name in operations:
        if name not in index:
            missing.append(name)
            continue
        method, path, op = index[name]
        op = dict(op)
        op["operationId"] = op_id(name)
        op["security"] = [{"apiKeyAuth": []}]
        collect_refs(op, refs)
        paths.setdefault(path, {})[method] = op
    if missing:
        raise SystemExit(f"{gpt}: operations not found in spec: {missing}")
    doc = {
        "openapi": spec.get("openapi", "3.1.0"),
        "info": {
            "title": TITLES.get(gpt, f"Chili Piper — {gpt} Actions"),
            "version": spec.get("info", {}).get("version", "1.0.0"),
            "description": f"GPT Actions for the {gpt} GPT — a subset of the Chili Piper Edge API. "
                           "Authenticate with a Bearer API key (Admin Center → API Keys).",
        },
        "servers": spec.get("servers", [{"url": "https://fire.chilipiper.com/api/fire-edge"}]),
        "security": [{"apiKeyAuth": []}],
        "paths": paths,
        "components": {
            "securitySchemes": {"apiKeyAuth": sec.get("apiKeyAuth", {
                "type": "apiKey", "name": "Authorization", "in": "header",
                "description": "API key as 'Bearer <api-key>' in the Authorization header.",
            })},
            "schemas": closure(refs, all_schemas),
        },
    }
    return doc


def main():
    local = sys.argv[1] if len(sys.argv) > 1 else None
    spec = load_spec(local)
    index = build_operation_index(spec)
    for gpt, operations in GPT_OPERATIONS.items():
        out_dir = os.path.join(GPTS_DIR, gpt)
        os.makedirs(out_dir, exist_ok=True)
        doc = generate(spec, index, gpt, operations)
        out = os.path.join(out_dir, "openapi.yaml")
        with open(out, "w", encoding="utf-8") as f:
            f.write("# Generated from the Chili Piper Edge API OpenAPI spec by\n"
                    "# .github/scripts/generate_gpt_openapi.py — do not edit by hand.\n")
            yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True, width=100)
        print(f"✓ {gpt}: {len(doc['paths'])} paths, {len(doc['components']['schemas'])} schemas -> {out}")


if __name__ == "__main__":
    main()
