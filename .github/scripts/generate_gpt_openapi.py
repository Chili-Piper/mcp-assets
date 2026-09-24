"""Generate self-contained GPT Action OpenAPI specs from the live Chili Piper Edge API spec.

Each ChatGPT GPT in gpts/<name>/ gets an openapi.yaml containing ONLY the endpoints that
GPT uses, with the transitive closure of referenced component schemas, the correct production
server URL, and Bearer (apiKeyAuth) security — extracted from the canonical Edge API OpenAPI
document so the GPTs never drift from reality, then adapted to ChatGPT's GPT Actions import
constraints (see CHATGPT CONSTRAINTS below).

Source of truth (public): https://fire.chilipiper.com/api/fire-edge/public/org/docs/swagger/docs.yaml
Run:  python .github/scripts/generate_gpt_openapi.py [path-to-local-docs.yaml]
Then: python .github/scripts/validate_gpt_openapi.py   (also runs in CI)

WHY THIS EXISTS
  ChatGPT GPT Actions call the REST API directly with an API key, so each GPT needs a real,
  accurate OpenAPI spec. This script produces those specs from the canonical Edge API document,
  so the GPT Actions always reflect the real endpoints, request bodies, and response schemas —
  no hand-editing, no placeholder URLs, no drift from the API.

  This keeps the GPTs in sync with the *API*. Keeping the GPTs in sync with the *Claude skills*
  is a separate concern, enforced in CI by check_gpt_sync.py (every skill must have a paired GPT
  at a matching version). This script does NOT touch the Claude skills in skills/.

CHATGPT CONSTRAINTS (the GPT Actions importer rejects the spec otherwise)
  - Operation `description` must be <= 300 chars. The Edge descriptions are long MCP-tool
    prose, so each operation gets a short one: access label (READ-ONLY / MUTATING ...) +
    `summary` + the one-line blurb + parameter names, whatever fits in 300 chars.
  - Every `type: object` schema must have `properties` (even `{}`), e.g. Map_String.
  - Deprecated operations are refused: point GPT_OPERATIONS at the replacement instead.

WHEN TO RE-RUN
  - The Edge API changes (new/renamed fields, schemas, or endpoints) → re-run to refresh specs.
  - A GPT should start (or stop) using an operation → first edit GPT_OPERATIONS below, then re-run.
    GPT_OPERATIONS is the one manual step: it maps each GPT to the Edge operations it uses, and
    should mirror the matching skill's tools (references/api-reference.md) and every action the
    GPT.md names. The Edge spec tags every operation with `[operation: <name>]` (matching the
    Chili Piper MCP tool names); use those names here.
  The script also writes gpts/edge-operations.yaml — a catalog of all live Edge operations
  (name, operationId, deprecation) that validate_gpt_openapi.py uses offline to check GPT.md.
"""

import copy
import os
import re
import sys
import urllib.request

import yaml

SPEC_URL = "https://fire.chilipiper.com/api/fire-edge/public/org/docs/swagger/docs.yaml"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GPTS_DIR = os.path.join(REPO_ROOT, "gpts")
CATALOG = os.path.join(GPTS_DIR, "edge-operations.yaml")

DESCRIPTION_LIMIT = 300  # ChatGPT GPT Actions hard limit for an operation description
OPERATION_EXTENSION = "x-mcp-tool"  # the Edge/MCP operation name, kept on each generated op

# GPT -> the Edge operations (== MCP tool names) it needs. Mirror each skill's tools and GPT.md.
GPT_OPERATIONS = {
    "meeting-inspector": ["meeting-get", "meeting-list-put", "concierge-list-routers", "concierge-logs", "workspace-list"],
    "no-show-analyzer": ["meeting-list-put", "concierge-list-routers", "concierge-logs", "workspace-list", "user-find-by-ids"],
    "org-meeting": ["meeting-list-put", "workspace-list", "user-find-by-ids"],
    "user-meetings": ["user-find", "meeting-export-v2-put", "workspace-list"],
    "routing-audit": ["workspace-list", "concierge-list-routers", "rule-list", "concierge-logs", "distribution-list-put"],
    "concierge-debugger": ["concierge-list-routers", "concierge-logs", "rule-list", "workspace-list", "user-find-by-ids"],
    "availability-inspector": ["user-find", "user-read", "availability-slots-v2"],
    "user-details": ["user-find", "user-read", "workspace-list", "team-list-put",
                     "scheduling-link-list-personal-v2", "scheduling-link-list-round-robin",
                     "scheduling-link-list-admin-one-on-one", "scheduling-link-list-group",
                     "scheduling-link-list-ownership", "meeting-export-v2-put"],
    "user-copy": ["user-find", "user-read", "workspace-list", "workspace-list-users", "team-list-put",
                  "workspace-add-users", "team-add-users", "team-create", "user-update-licenses"],
    "user-offboarding": ["user-find", "user-read", "meeting-export-v2-put", "workspace-list", "workspace-list-users",
                         "workspace-remove-users", "team-list-put", "team-remove-users", "team-create", "team-delete",
                         "meeting-cancel-post", "distribution-list-put"],
    "distribution-analysis": ["workspace-list", "distribution-list-put", "distribution-workspace-settings-get",
                              "user-find-by-ids", "meeting-list-put"],
    "distro-debugger": ["workspace-list", "distro-list-routers", "distro-logs", "distro-log-get", "distribution-list-put"],
    "chat-conversation-inspector": ["workspace-list", "chat-logs", "chat-transcript", "user-find-by-ids"],
    "meeting-type-management": ["workspace-list", "meeting-type-list", "meeting-type-get", "meeting-type-create",
                                "meeting-type-update", "meeting-type-delete", "meeting-type-attach-reminder",
                                "meeting-type-detach-reminder", "meeting-type-reminder-list", "meeting-type-reminder-create",
                                "meeting-type-reminder-update", "meeting-type-reminder-delete",
                                "personal-meeting-type-list", "personal-meeting-type-get", "personal-meeting-type-create",
                                "personal-meeting-type-update", "personal-meeting-type-delete"],
    "distro-router-configuration": ["workspace-list", "distro-list-routers", "distro-router-get", "distro-router-create",
                                    "distro-router-update", "distro-router-delete", "distro-router-activate",
                                    "distro-router-deactivate", "rule-list", "distribution-list-put",
                                    "campaign-list", "campaign-search"],
    "handoff-router-configuration": ["workspace-list", "handoff-router-list", "handoff-router-get", "handoff-router-create",
                                     "handoff-router-update", "handoff-router-delete", "rule-list", "distribution-list-put",
                                     "meeting-type-list", "user-find", "campaign-list", "campaign-search"],
    "concierge-router-configuration": ["workspace-list", "concierge-list-routers", "concierge-router-get",
                                       "concierge-router-create", "concierge-router-update", "concierge-router-delete",
                                       "rule-list", "distribution-list-put", "meeting-type-list", "user-find",
                                       "campaign-list", "campaign-search", "data-field-list", "data-field-get",
                                       "data-field-create", "data-field-update", "data-field-delete",
                                       "enrichment-waterfall-list"],
    "concierge-router-builder": ["tenant-get", "workspace-list", "concierge-list-routers", "user-find",
                                 "team-create", "team-add-users", "meeting-type-create", "meeting-type-list",
                                 "meeting-type-update", "rule-create", "rule-list", "distribution-create",
                                 "distribution-list-put", "concierge-router-create", "concierge-router-get",
                                 "data-field-create", "campaign-list", "campaign-search", "enrichment-waterfall-list"],
    "scheduling-link-management": ["workspace-list", "scheduling-link-list-personal-v2", "scheduling-link-list-round-robin",
                                   "scheduling-link-list-admin-one-on-one", "scheduling-link-list-group",
                                   "scheduling-link-list-ownership", "scheduling-link-create-round-robin",
                                   "scheduling-link-update-round-robin", "scheduling-link-delete-round-robin",
                                   "scheduling-link-create-admin-one-on-one", "scheduling-link-update-admin-one-on-one",
                                   "scheduling-link-delete-admin-one-on-one", "scheduling-link-create-group",
                                   "scheduling-link-update-group", "scheduling-link-delete-group",
                                   "scheduling-link-create-ownership", "scheduling-link-update-ownership",
                                   "scheduling-link-delete-ownership", "meeting-type-list", "distribution-list-put",
                                   "user-find"],
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
    "handoff-router-configuration": "Chili Piper — Handoff Router Configuration Actions",
    "concierge-router-configuration": "Chili Piper — Concierge Router Configuration Actions",
    "concierge-router-builder": "Chili Piper — Concierge Router Builder Actions",
    "scheduling-link-management": "Chili Piper — Scheduling Link Management Actions",
}

ACCESS_LABEL = re.compile(r"^(READ-ONLY|MUTATING\b.*)$")
REPLACEMENT = re.compile(r"\bUse\s+(\S+?)\s+instead", re.IGNORECASE)


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


def _paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]


def replacement_of(op):
    """The operation named in a 'DEPRECATED ... Use <x> instead.' banner, if any."""
    m = REPLACEMENT.search(op.get("description", "") or "")
    return m.group(1).rstrip(".") if m else None


def _sentence(text):
    text = " ".join(text.split())
    return text if text.endswith((".", "!", "?")) else text + "."


def _truncate(text, limit):
    """Cut at a word boundary and mark the cut; used only when nothing shorter fits."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return cut + "…"


def gpt_description(op, limit=DESCRIPTION_LIMIT):
    """Short GPT Actions description: [deprecation] + access label + summary [+ blurb] [+ params]."""
    paras = _paragraphs(op.get("description"))
    access = next((p for p in paras if ACCESS_LABEL.match(p)), None)
    blurb = None
    if access is not None:
        i = paras.index(access)
        if i + 1 < len(paras) and "\n" not in paras[i + 1]:
            blurb = _sentence(paras[i + 1])
    summary = _sentence(op.get("summary") or "")

    head = []
    if op.get("deprecated"):
        repl = replacement_of(op)
        head.append(f"DEPRECATED — use {repl}." if repl else "DEPRECATED.")
    if access:
        head.append(_sentence(access))
    if summary != ".":
        head.append(summary)
    text = " ".join(head)

    params = [p.get("name") + (" (required)" if p.get("required") else "")
              for p in op.get("parameters", []) or [] if isinstance(p, dict) and p.get("name")]
    extras = []
    if blurb and blurb.rstrip(".").lower() != summary.rstrip(".").lower():
        extras.append(blurb)
    if params:
        extras.append("Params: " + ", ".join(params) + ".")
    if op.get("requestBody"):
        extras.append("Takes a JSON body.")
    for extra in extras:
        if len(text) + 1 + len(extra) <= limit:
            text = f"{text} {extra}"
    return _truncate(text, limit)


def ensure_object_properties(node):
    """ChatGPT rejects `type: object` schemas without `properties` — add an empty map (no-op semantically)."""
    if isinstance(node, dict):
        t = node.get("type")
        is_object = t == "object" or (isinstance(t, list) and "object" in t)
        if is_object and "properties" not in node:
            node["properties"] = {}
        for v in node.values():
            ensure_object_properties(v)
    elif isinstance(node, list):
        for v in node:
            ensure_object_properties(v)


def generate(spec, index, gpt, operations):
    all_schemas = spec.get("components", {}).get("schemas", {})
    sec = spec.get("components", {}).get("securitySchemes", {})
    paths, refs = {}, set()
    missing, deprecated = [], []
    for name in operations:
        if name not in index:
            missing.append(name)
            continue
        method, path, op = index[name]
        if op.get("deprecated"):
            deprecated.append(f"{name} (use {replacement_of(op) or '?'})")
            continue
        op = copy.deepcopy(op)
        op["operationId"] = op_id(name)
        op["description"] = gpt_description(op)
        op["security"] = [{"apiKeyAuth": []}]
        op[OPERATION_EXTENSION] = name
        collect_refs(op, refs)
        paths.setdefault(path, {})[method] = op
    if missing:
        raise SystemExit(f"{gpt}: operations not found in spec: {missing}")
    if deprecated:
        raise SystemExit(f"{gpt}: deprecated operations in GPT_OPERATIONS: {deprecated}")
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
            "schemas": copy.deepcopy(closure(refs, all_schemas)),
        },
    }
    ensure_object_properties(doc)
    return doc


def catalog(spec, index):
    """All live Edge operations, for offline validation of GPT.md references."""
    ops = {}
    for name in sorted(index):
        method, path, op = index[name]
        entry = {"operationId": op_id(name), "method": method, "path": path}
        if op.get("deprecated"):
            entry["deprecated"] = True
            repl = replacement_of(op)
            if repl:
                entry["replacement"] = repl
        ops[name] = entry
    return {"edgeVersion": spec.get("info", {}).get("version"), "operations": ops}


HEADER = ("# Generated from the Chili Piper Edge API OpenAPI spec by\n"
          "# .github/scripts/generate_gpt_openapi.py — do not edit by hand.\n")


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
            f.write(HEADER)
            yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True, width=100)
        print(f"✓ {gpt}: {len(doc['paths'])} paths, {len(doc['components']['schemas'])} schemas -> {out}")
    with open(CATALOG, "w", encoding="utf-8") as f:
        f.write(HEADER)
        yaml.safe_dump(catalog(spec, index), f, sort_keys=False, allow_unicode=True, width=100)
    print(f"✓ catalog: {len(index)} operations -> {CATALOG}")


if __name__ == "__main__":
    main()
