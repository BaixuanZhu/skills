import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import tempfile


class DeliveryError(ValueError):
    pass


def _need(condition, message):
    if not condition:
        raise DeliveryError(message)


def _fields(value, required, optional="", label="object"):
    _need(isinstance(value, dict), f"{label} must be an object")
    required, allowed = set(required.split()), set((required + " " + optional).split())
    _need(required <= value.keys() <= allowed, f"{label}: missing or unknown fields")


def _text(value, label):
    _need(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")


def _id(value, label):
    _text(value, label)
    _need(len(value) <= 100 and all(c.isascii() and (c.isalnum() or c in "-_") for c in value),
          f"{label} must be 1..100 ASCII letters, digits, - or _")


def _strings(value, label, ids=False, nonempty=False, unique=False):
    _need(isinstance(value, list) and (not nonempty or bool(value)), f"{label} must be a list")
    for entry in value:
        (_id if ids else _text)(entry, label)
    if unique:
        _need(len(value) == len(set(value)), f"{label} contains duplicates")


def _version(value):
    _need(type(value.get("schema")) is int and value["schema"] == 1, "schema must be integer 1")
    if "revision" in value:
        _need(type(value["revision"]) is int and value["revision"] > 0, "revision must be a positive integer")


def _relative(value):
    _text(value, "context path")
    normalized = value.replace("\\", "/")
    _need(not PureWindowsPath(value).drive and not normalized.startswith("/")
          and ".." not in normalized.split("/") and "\x00" not in value
          and Path(normalized).suffix.lower() == ".md", f"unsafe relative .md context path: {value}")
    return normalized


def _inside(root, path):
    _need("\x00" not in str(path), "path must not contain NUL")
    _need(path.resolve().is_relative_to(root.resolve()), f"path escapes HUB: {path}")
    return path


def _file(root, name):
    return _inside(root, root / "agile-docs" / name)


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _parent(item):
    return {key: item[key] for key in ("id", "title", "type", "detail", "refs", "acceptance") if key in item}


def _digest(plan, snapshots, parents):
    return _hash(_canonical({"plan": plan, "snapshots": snapshots, "parents": parents}).encode("utf-8"))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise DeliveryError(f"invalid JSON constant: {value}")


def _read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs, parse_constant=_constant)


def _paths(plan):
    return sorted(set(plan["context"] + [p for pkg in plan["packages"] for p in pkg.get("context", [])]))


def _plan(raw):
    _fields(raw, "schema project_id sprint revision goal context packages", label="plan")
    _version(raw)
    for key in ("project_id", "sprint"):
        _id(raw[key], key)
    _text(raw["goal"], "goal")
    _strings(raw["context"], "context", unique=True)
    _need(isinstance(raw["packages"], list) and raw["packages"], "packages must be a nonempty list")
    packages = {}
    for pkg in raw["packages"]:
        _fields(pkg, "id item repo title instructions acceptance depends_on deliverables", "context", "package")
        for key in ("id", "item", "repo"):
            _id(pkg[key], "package " + key)
        _need(pkg["id"] not in packages, f"duplicate package ID: {pkg['id']}")
        packages[pkg["id"]] = pkg
        _text(pkg["title"], "package title")
        for key in ("instructions", "acceptance", "context"):
            _strings(pkg.get(key, []), "package " + key, nonempty=key != "context")
        _strings(pkg["depends_on"], "depends_on", ids=True, unique=True)
        _strings(pkg["deliverables"], "deliverables", unique=True)
    for path in _paths(raw):
        _relative(path)
    pending = {key: set(pkg["depends_on"]) for key, pkg in packages.items()}
    for key, deps in pending.items():
        _need(key not in deps and deps <= packages.keys(), f"{key}: self or unknown dependency")
    while pending:
        ready = {key for key, deps in pending.items() if not deps}
        _need(ready, "package dependency cycle")
        pending = {key: deps - ready for key, deps in pending.items() if key not in ready}


def _snapshot(root, raw, items):
    result = []
    for relative in _paths(raw):
        path = _inside(root, root / _relative(relative))
        data = path.read_bytes()
        result.append({"path": relative, "sha256": _hash(data), "content": data.decode("utf-8")})
    ids = sorted({pkg["item"] for pkg in raw["packages"]})
    _need(all(ident in items for ident in ids), "plan parent item missing")
    parents = [_parent(items[ident]) for ident in ids]
    return {"plan": raw, "snapshots": result, "parents": parents, "digest": _digest(raw, result, parents)}


def _fresh(root, entry, items):
    for snap in entry["snapshots"]:
        path = _inside(root, root / _relative(snap["path"]))
        _need(path.is_file() and _hash(path.read_bytes()) == snap["sha256"],
              f"context drift: {snap['path']}; revise plan or close and carry unfinished work forward")
    for parent in entry["parents"]:
        _need(parent["id"] in items and _parent(items[parent["id"]]) == parent,
              f"parent requirement drift: {parent['id']}; revise plan or close and carry unfinished work forward")


def _receipt(raw):
    _fields(raw, "schema id project_id sprint revision plan_digest package_id repo result summary evidence artifacts", label="receipt")
    _version(raw)
    for key in ("id", "project_id", "sprint", "package_id", "repo"):
        _id(raw[key], "receipt " + key)
    _text(raw["plan_digest"], "plan_digest")
    _need(raw["result"] in ("completed", "partial", "blocked"), "invalid receipt result")
    _text(raw["summary"], "receipt summary")
    _strings(raw["evidence"], "receipt evidence", nonempty=raw["result"] == "completed")
    _need(isinstance(raw["artifacts"], list), "artifacts must be a list")
    names = set()
    for artifact in raw["artifacts"]:
        _fields(artifact, "name source content", label="artifact")
        _text(artifact["name"], "artifact name")
        _text(artifact["source"], "artifact source")
        _text(artifact["content"], "artifact content")
        _need(artifact["name"] not in names, "duplicate artifact name")
        names.add(artifact["name"])


def _packages(entry):
    return {pkg["id"]: pkg for pkg in entry["plan"]["packages"]}


def _current(state):
    return {entry["plan"]["sprint"]: entry for entry in state["plans"]}


def _accepted(state, entry):
    return {record["receipt"]["package_id"]: record for record in state["receipts"]
            if record["receipt"]["plan_digest"] == entry["digest"] and record["acceptance"] is not None}


def _dependencies(state, entry, pkg):
    missing = set(pkg["depends_on"]) - _accepted(state, entry).keys()
    _need(not missing, f"{pkg['id']}: unresolved dependencies: {', '.join(sorted(missing))}")


def _match_receipt(raw, entry, project):
    plan = entry["plan"]
    for key, expected in (("project_id", project), ("sprint", plan["sprint"]),
                          ("revision", plan["revision"]), ("plan_digest", entry["digest"])):
        _need(raw[key] == expected, f"receipt {key} does not match plan")
    pkg = _packages(entry).get(raw["package_id"])
    _need(pkg is not None, "unknown receipt package_id")
    _need(raw["repo"] == pkg["repo"], "receipt repo does not match package")
    if raw["result"] == "completed":
        names = {artifact["name"] for artifact in raw["artifacts"]}
        _need(set(pkg["deliverables"]) <= names, f"{pkg['id']}: completed receipt lacks declared deliverables")
    return pkg


def _state(root):
    path = _file(root, "delivery.json")
    if not path.exists():
        return None
    state = _read(path)
    _fields(state, "schema project_id plans receipts", label="delivery.json")
    _version(state)
    _id(state["project_id"], "project_id")
    _need(isinstance(state["plans"], list) and isinstance(state["receipts"], list), "plans/receipts must be lists")
    versions, entries = {}, {}
    for entry in state["plans"]:
        _fields(entry, "plan snapshots parents digest", label="stored plan")
        raw = entry["plan"]
        _plan(raw)
        _need(raw["project_id"] == state["project_id"], "plan project_id differs from HUB")
        _need(raw["revision"] > versions.get(raw["sprint"], 0), "stored revisions must strictly increase per Sprint")
        versions[raw["sprint"]] = raw["revision"]
        _need(isinstance(entry["snapshots"], list), "snapshots must be a list")
        paths = []
        for snap in entry["snapshots"]:
            _fields(snap, "path sha256 content", label="snapshot")
            _relative(snap["path"])
            _need(isinstance(snap["content"], str), "snapshot content must be text")
            _need(snap["sha256"] == _hash(snap["content"].encode("utf-8")), "snapshot sha256 mismatch")
            paths.append(snap["path"])
        _need(paths == _paths(raw), "snapshot paths do not match selected context")
        _need(isinstance(entry["parents"], list), "parent snapshots must be a list")
        for parent in entry["parents"]:
            _fields(parent, "id title", "type detail refs acceptance", "parent snapshot")
            _id(parent["id"], "parent ID")
            _text(parent["title"], "parent title")
        _need([p["id"] for p in entry["parents"]] == sorted({p["item"] for p in raw["packages"]}),
              "parent snapshots must cover plan items exactly")
        _need(entry["digest"] == _digest(raw, entry["snapshots"], entry["parents"]), "plan digest mismatch")
        entries[(raw["sprint"], raw["revision"])] = entry
    seen, accepted = set(), set()
    for record in state["receipts"]:
        _fields(record, "receipt acceptance", label="stored receipt")
        raw = record["receipt"]
        _receipt(raw)
        _need(raw["id"] not in seen, "duplicate receipt ID")
        seen.add(raw["id"])
        entry = entries.get((raw["sprint"], raw["revision"]))
        _need(entry is not None, "receipt refers to unknown plan revision")
        _match_receipt(raw, entry, state["project_id"])
        if record["acceptance"] is not None:
            _fields(record["acceptance"], "reviewer note", label="receipt acceptance")
            for key in ("reviewer", "note"):
                _text(record["acceptance"][key], "acceptance " + key)
            _need(raw["result"] == "completed", "only completed receipts may be accepted")
            key = (entry["digest"], raw["package_id"])
            _need(key not in accepted, "multiple accepted receipts for one package/revision")
            accepted.add(key)
    for record in state["receipts"]:
        raw = record["receipt"]
        entry = entries[(raw["sprint"], raw["revision"])]
        _dependencies(state, entry, _packages(entry)[raw["package_id"]])
    return state


def _backlog(root, validate=None):
    data = _read(_file(root, "backlog.json"))
    _need(isinstance(data, dict) and isinstance(data.get("phases"), list), "backlog.json needs phases list")
    if validate:
        errors, _warnings = validate(data)
        _need(not errors, "invalid backlog: " + "; ".join(errors))
    items = {}
    for phase in data["phases"]:
        _need(isinstance(phase, dict) and isinstance(phase.get("items"), list), "invalid backlog phase")
        for item in phase["items"]:
            _need(isinstance(item, dict), "invalid backlog item")
            _id(item.get("id"), "backlog item ID")
            _need(item["id"] not in items, "duplicate backlog item ID")
            items[item["id"]] = item
    return data, items


def _completion(state, entry, item):
    ident = item["id"]
    record = item.get("delivery_acceptance")
    _fields(record, "project_id sprint revision plan_digest receipts reviewer evidence", label=f"{ident} delivery_acceptance")
    _text(record["reviewer"], "overall reviewer")
    _strings(record["evidence"], "overall evidence", nonempty=True)
    _strings(record["receipts"], "accepted receipt IDs", ids=True, nonempty=True, unique=True)
    _need(type(record["revision"]) is int, "delivery_acceptance revision must be integer")
    plan, accepted = entry["plan"], _accepted(state, entry)
    packages = [pkg for pkg in plan["packages"] if pkg["item"] == ident]
    _need(packages, f"{ident}: no packages in completion plan")
    _need(all(pkg["id"] in accepted for pkg in packages), f"{ident}: all current packages must be accepted")
    for pkg in packages:
        _dependencies(state, entry, pkg)
    expected = {"project_id": state["project_id"], "sprint": plan["sprint"],
                "revision": plan["revision"], "plan_digest": entry["digest"],
                "receipts": sorted(accepted[pkg["id"]]["receipt"]["id"] for pkg in packages)}
    _need(all(record[key] == value for key, value in expected.items()), f"{ident}: completion provenance mismatch")
    _need(item.get("status") == "已完成", f"{ident}: delivery acceptance requires status 已完成")


def _provenance(state, items):
    current = _current(state)
    for item in items.values():
        if "delivery_acceptance" in item:
            record = item["delivery_acceptance"]
            _need(isinstance(record, dict) and isinstance(record.get("sprint"), str),
                  f"{item['id']}: invalid delivery_acceptance")
            entry = current.get(record["sprint"])
            _need(entry is not None, f"{item['id']}: completion has no plan")
            _completion(state, entry, item)


def _active(root, stem, scan, allow_closed=False):
    _id(stem, "sprint")
    rows = [row for row in scan(root) if row[1] == stem]
    _need(len(rows) == 1, f"{stem}: expected exactly one active parsed Sprint")
    row = rows[0]
    _inside(root, Path(row[0]))
    _need(allow_closed or not str(row[2].get("状态", row[2].get("state", ""))).startswith("已关闭"), f"{stem}: Sprint is closed")
    return row


def _coverage(entry, row, items):
    ids = [ident for ident, _points in row[3]]
    planned = {pkg["item"] for pkg in entry["plan"]["packages"]}
    _need(len(ids) == len(set(ids)) and set(ids) == planned, "packages must cover exactly current Sprint task IDs")
    for ident in planned:
        _need(ident in items and items[ident].get("confirmed") is True, f"{ident}: confirmed backlog item required")


def _live(item):
    _need(item.get("confirmed") is True and item.get("status") not in ("已完成", "已撤回")
          and "delivery_acceptance" not in item, f"{item['id']}: live unfinished confirmed item required")


def _closure_paths(root, stem):
    for folder in ("sprints", "agile-docs/sprints"):
        for archive in ("", "archive"):
            for suffix in (".done.yaml", ".done.processed.yaml"):
                path = _inside(root, root / folder / archive / (stem + suffix))
                if path.exists() or path.is_symlink():
                    yield path


def _open_delivery(root, stem):
    _need(not any(_closure_paths(root, stem)), f"{stem}: closure already started; no new delivery mutations")


def _ready_entry(root, state, stem, scan, items, allow_closed=False, allow_stale=False):
    entry = _current(state).get(stem)
    _need(entry is not None, f"{stem}: no delivery plan")
    row = _active(root, stem, scan, allow_closed)
    _coverage(entry, row, items)
    if not allow_closed:
        _open_delivery(root, stem)
    if not allow_stale:
        _fresh(root, entry, items)
    return entry, row


@contextmanager
def _lock(root):
    path = _file(root, ".delivery.lock")
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise DeliveryError(f"delivery lock exists: {path}; another writer may own it") from None
    identity = os.fstat(fd)
    try:
        yield
    finally:
        os.close(fd)
        try:
            if os.path.samestat(identity, path.lstat()):
                path.unlink()
        except FileNotFoundError:
            pass


def _write(path, content):
    fd, name = tempfile.mkstemp(prefix=".delivery-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, str(path))
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _save(path, value):
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def _import_plan(root, args, state, scan, items):
    raw = _read(Path(args.plan).resolve())
    _plan(raw)
    _need(state is None or state["project_id"] == raw["project_id"], "project_id is bound to this HUB")
    state = state or {"schema": 1, "project_id": raw["project_id"], "plans": [], "receipts": []}
    entry, previous = _snapshot(root, raw, items), _current(state).get(raw["sprint"])
    if entry in state["plans"]:
        return "plan unchanged"
    _open_delivery(root, raw["sprint"])
    if previous:
        _need(raw["revision"] > previous["plan"]["revision"], "changed plan requires a strictly higher revision")
    related = {pkg["item"] for old in state["plans"] if old["plan"]["sprint"] == raw["sprint"]
               for pkg in old["plan"]["packages"]} | {pkg["item"] for pkg in raw["packages"]}
    _need(not any("delivery_acceptance" in items.get(ident, {}) for ident in related),
          "cannot revise a Sprint after related item delivery_acceptance; completed history is immutable")
    row = _active(root, raw["sprint"], scan)
    _coverage(entry, row, items)
    for ident in {pkg["item"] for pkg in raw["packages"]}:
        _live(items[ident])
    state["plans"].append(entry)
    _save(_file(root, "delivery.json"), state)
    return f"plan imported: {raw['sprint']} revision {raw['revision']}"


def _export(root, args, state, scan, items):
    entry, _row = _ready_entry(root, state, args.sprint, scan, items)
    pkg = _packages(entry).get(args.package)
    _need(pkg is not None, "unknown package")
    _dependencies(state, entry, pkg)
    _live(items[pkg["item"]])
    plan = entry["plan"]
    parent = next(item for item in entry["parents"] if item["id"] == pkg["item"])
    identity = {"schema": 1, "project_id": state["project_id"], "sprint": plan["sprint"],
                "revision": plan["revision"], "plan_digest": entry["digest"], "package_id": pkg["id"], "repo": pkg["repo"]}
    receipt = dict(identity, id="receipt-" + _hash((entry["digest"] + pkg["id"]).encode())[:24],
                   result="completed", summary="", evidence=[],
                   artifacts=[{"name": name, "source": "", "content": ""} for name in pkg["deliverables"]])
    accepted = _accepted(state, entry)
    dependencies = []
    for ident in pkg["depends_on"]:
        raw = accepted[ident]["receipt"]
        dependencies.append({"package_id": ident, "repo": raw["repo"], "receipt_id": raw["id"],
                             "evidence": raw["evidence"], "artifacts": raw["artifacts"]})
    paths = set(plan["context"] + pkg.get("context", []))
    result = dict(identity, goal=plan["goal"], title=pkg["title"],
                  item={"id": parent["id"], "title": parent.get("title", ""),
                        "detail": parent.get("detail", []), "acceptance": parent.get("acceptance", [])},
                  context=[snap for snap in entry["snapshots"] if snap["path"] in paths],
                  instructions=pkg["instructions"], acceptance=pkg["acceptance"], deliverables=pkg["deliverables"],
                  dependencies=dependencies, receipt_template=receipt,
                  receipt_instructions="Fill summary, evidence and artifact source/content; use a new receipt ID for changed results. "
                  "Return independent receipt JSON for central import. Evidence is not executed or fetched; reviewer must verify semantic truth.")
    return json.dumps(result, ensure_ascii=False, indent=2)


def _submit(root, args, state, scan, items):
    raw = _read(Path(args.receipt).resolve())
    _receipt(raw)
    existing = next((r for r in state["receipts"] if r["receipt"]["id"] == raw["id"]), None)
    if existing:
        _need(existing["receipt"] == raw, "receipt ID already exists with different payload")
        return "receipt unchanged"
    entry, _row = _ready_entry(root, state, raw["sprint"], scan, items)
    pkg = _match_receipt(raw, entry, state["project_id"])
    _live(items[pkg["item"]])
    _dependencies(state, entry, pkg)
    _need(pkg["id"] not in _accepted(state, entry), "package is already accepted; new submissions refused")
    state["receipts"].append({"receipt": raw, "acceptance": None})
    _save(_file(root, "delivery.json"), state)
    return f"receipt submitted: {raw['id']}; reviewer verification required"


def _accept(root, args, state, scan, items):
    record = next((r for r in state["receipts"] if r["receipt"]["id"] == args.receipt_id), None)
    _need(record is not None, "unknown receipt ID")
    raw = record["receipt"]
    approval = {"reviewer": args.reviewer, "note": args.note}
    for key, value in approval.items():
        _text(value, key)
    if record["acceptance"] is not None:
        _need(record["acceptance"] == approval, "existing acceptance is immutable")
        return "acceptance unchanged"
    entry, _row = _ready_entry(root, state, raw["sprint"], scan, items)
    pkg = _match_receipt(raw, entry, state["project_id"])
    _need(raw["result"] == "completed", "only completed receipts can be accepted")
    _dependencies(state, entry, pkg)
    _live(items[pkg["item"]])
    _need(pkg["id"] not in _accepted(state, entry), "package already has an accepted receipt")
    record["acceptance"] = approval
    _save(_file(root, "delivery.json"), state)
    return f"receipt accepted: {raw['id']}"


def _finish(root, args, state, scan, data, items):
    entry = _current(state).get(args.sprint)
    _need(entry is not None, "no delivery plan")
    _text(args.reviewer, "reviewer")
    _strings(args.evidence, "overall evidence", nonempty=True)
    packages = [pkg for pkg in entry["plan"]["packages"] if pkg["item"] == args.item]
    _need(packages and args.item in items, "unknown plan item")
    accepted = _accepted(state, entry)
    _need(all(pkg["id"] in accepted for pkg in packages), "all item packages must be accepted before finish")
    for pkg in packages:
        _dependencies(state, entry, pkg)
    approval = {"project_id": state["project_id"], "sprint": args.sprint, "revision": entry["plan"]["revision"],
                "plan_digest": entry["digest"], "receipts": sorted(accepted[p["id"]]["receipt"]["id"] for p in packages),
                "reviewer": args.reviewer, "evidence": args.evidence}
    item = items[args.item]
    if "delivery_acceptance" in item or item.get("status") == "已完成":
        _need(item.get("delivery_acceptance") == approval and item.get("status") == "已完成",
              "completed history differs or lacks delivery_acceptance; cannot overwrite")
        return "item completion unchanged"
    _ready_entry(root, state, args.sprint, scan, items)
    _live(item)
    item["status"], item["delivery_acceptance"] = "已完成", approval
    _save(_file(root, "backlog.json"), data)
    return f"item finished: {args.item}; Sprint remains open"


def _done_text(completed, moved, feedback):
    lines = []
    for key, values in (("completed", completed), ("moved_next", moved)):
        lines.append(key + (":" if values else ": []"))
        lines.extend("  - " + value for value in values)
    lines.append("feedback:" if feedback else "feedback: []")
    for ident, note in feedback:
        lines.extend(["  - item: " + ident, "    type: reason", "    note: " + json.dumps(note, ensure_ascii=False)])
    return "\n".join(lines) + "\n"


def _close(root, args, state, scan, items):
    entry, row = _ready_entry(root, state, args.sprint, scan, items, allow_closed=True, allow_stale=True)
    planned = {pkg["item"] for pkg in entry["plan"]["packages"]}
    completed = sorted(ident for ident in planned if "delivery_acceptance" in items[ident])
    for ident in completed:
        _completion(state, entry, items[ident])
    moved = sorted(planned - set(completed))
    _strings(args.move, "--move", ids=True, unique=True)
    _need(set(args.move) == set(moved), "--move must explicitly name EXACT unfinished set: " + ", ".join(moved))
    for ident in moved:
        _need(items[ident].get("status") != "已完成", f"{ident}: completed status lacks delivery acceptance")
    latest = {r["receipt"]["package_id"]: r["receipt"] for r in state["receipts"]
              if r["receipt"]["plan_digest"] == entry["digest"]}
    feedback = []
    for pkg in entry["plan"]["packages"]:
        receipt = latest.get(pkg["id"])
        if pkg["item"] in moved and receipt and receipt["result"] in ("blocked", "partial"):
            feedback.append((pkg["item"], f"{pkg['id']} {receipt['result']}: {receipt['summary']}"))
    path = _inside(root, Path(row[0]).parent / (args.sprint + ".done.yaml"))
    directories = {path.parent, root / "sprints", root / "agile-docs" / "sprints"}
    counterparts = [_inside(root, folder / suffix / (args.sprint + ".done.processed.yaml"))
                    for folder in directories for suffix in ("", "archive")]
    _need(not any(p.exists() or p.is_symlink() for p in counterparts), "processed done counterpart already exists")
    text = _done_text(completed, moved, feedback)
    if path.exists() or path.is_symlink():
        _need(path.read_bytes() == text.encode("utf-8"), "different done file already exists; refusing overwrite")
        return "done file unchanged"
    _active(root, args.sprint, scan)
    _write(path, text)
    return f"done file generated: {path}; existing closure pipeline must process it"


def _status(state, entry, pkg):
    accepted = _accepted(state, entry)
    if pkg["id"] in accepted:
        return "accepted"
    if not set(pkg["depends_on"]) <= accepted.keys():
        return "blocked"
    receipts = [r["receipt"] for r in state["receipts"]
                if r["receipt"]["plan_digest"] == entry["digest"] and r["receipt"]["package_id"] == pkg["id"]]
    return ("submitted" if receipts[-1]["result"] == "completed" else "blocked") if receipts else "ready"


def _status_lines(root, state, scan, items):
    lines = []
    for _path, stem, meta, _tasks in scan(root):
        if stem not in _current(state) or str(meta.get("状态", meta.get("state", ""))).startswith("已关闭"):
            continue
        closing = any(_closure_paths(root, stem))
        entry, _row = _ready_entry(root, state, stem, scan, items, allow_closed=closing, allow_stale=closing)
        lines.extend(f"{stem} {pkg['id']} {pkg['repo']} {pkg['item']}: "
                     + ("closing" if closing else _status(state, entry, pkg))
                     for pkg in entry["plan"]["packages"])
    return "\n".join(lines) or "No active work packages"


def cli(argv, scan_sprints, validate_backlog):
    parser = argparse.ArgumentParser(prog="agile.py work")
    parser.add_argument("--root", default=os.getcwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "status", "export", "submit", "accept", "finish", "close"):
        child = commands.add_parser(command)
        child.add_argument("--root", default=argparse.SUPPRESS)
        if command == "plan":
            child.add_argument("plan", metavar="PLAN_JSON")
        elif command == "submit":
            child.add_argument("receipt", metavar="RECEIPT_JSON")
        elif command == "accept":
            child.add_argument("receipt_id", metavar="RECEIPT_ID")
            child.add_argument("--reviewer", required=True)
            child.add_argument("--note", required=True)
        elif command in ("export", "finish", "close"):
            child.add_argument("sprint", metavar="SPRINT")
            if command == "export":
                child.add_argument("package", metavar="PACKAGE")
            elif command == "finish":
                child.add_argument("item", metavar="ITEM")
                child.add_argument("--reviewer", required=True)
                child.add_argument("--evidence", action="append", required=True)
            else:
                child.add_argument("--move", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        if args.command in ("status", "export"):
            state = _state(root)
            if state is None and args.command == "status":
                print("No delivery plan")
                return 0
            _need(state is not None, "no delivery plan; import one first")
            _data, items = _backlog(root, validate_backlog)
            _provenance(state, items)
            print(_export(root, args, state, scan_sprints, items) if args.command == "export"
                  else _status_lines(root, state, scan_sprints, items))
        else:
            with _lock(root):
                state = _state(root)
                _need(state is not None or args.command == "plan", "no delivery plan; import one first")
                data, items = _backlog(root, validate_backlog)
                if state is not None:
                    _provenance(state, items)
                if args.command == "plan":
                    result = _import_plan(root, args, state, scan_sprints, items)
                elif args.command == "finish":
                    result = _finish(root, args, state, scan_sprints, data, items)
                elif args.command == "close":
                    result = _close(root, args, state, scan_sprints, items)
                else:
                    result = {"submit": _submit, "accept": _accept}[args.command](root, args, state, scan_sprints, items)
            print(result)
        return 0
    except Exception as error:
        print(f"work error: {error}")
        return 1


def check(root, scan_sprints, validate_backlog, parse_done):
    try:
        root = Path(root).resolve()
        state = _state(root)
        if state is None:
            return []
        _data, items = _backlog(root, validate_backlog)
        _provenance(state, items)
        scanned = list(scan_sprints(root))
        rows = {row[1]: row for row in scanned}
        _need(len(rows) == len(scanned), "duplicate Sprint stems")
        for entry in state["plans"]:
            for pkg in entry["plan"]["packages"]:
                _need(pkg["item"] in items, f"{pkg['item']}: plan parent item missing")
        for stem, entry in _current(state).items():
            row = rows.get(stem)
            _need(row is not None or any(_inside(root, root / folder / "archive" / (stem + ".md")).is_file()
                                        for folder in ("sprints", "agile-docs/sprints")), f"{stem}: plan Sprint missing")
            closures = list(_closure_paths(root, stem))
            closed = row is None or str(row[2].get("状态", "")).startswith("已关闭")
            _need(not closed or closures, f"{stem}: closed delivery Sprint lacks retained closure evidence")
            if not closed:
                _coverage(entry, row, items)
                if not closures:
                    _fresh(root, entry, items)
                for ident in {pkg["item"] for pkg in entry["plan"]["packages"]}:
                    if items[ident].get("status") == "已完成":
                        _completion(state, entry, items[ident])
            for path in closures:
                historical = path.name.endswith(".done.processed.yaml") or path.parent.name == "archive"
                _check_done(state, entry, items, parse_done(path.read_text(encoding="utf-8-sig")), historical)
        return []
    except Exception as error:
        return [f"delivery: {error}"]


def summary(root, scan_sprints):
    try:
        root = Path(root).resolve()
        state = _state(root)
        if state is None:
            return []
        counts = dict.fromkeys(("ready", "blocked", "submitted", "accepted", "closing"), 0)
        current = _current(state)
        for _path, stem, meta, _tasks in scan_sprints(root):
            entry = current.get(stem)
            if entry is not None and not str(meta.get("状态", "")).startswith("已关闭"):
                closing = any(_closure_paths(root, stem))
                for pkg in entry["plan"]["packages"]:
                    counts["closing" if closing else _status(state, entry, pkg)] += 1
        return ["Work: " + " / ".join(f"{key} {value}" for key, value in counts.items()) + " — agile.py work status"]
    except Exception:
        return ["Work: invalid delivery state — run agile.py work status / agile.py check"]


def _check_done(state, entry, items, done, historical=False):
    _need(isinstance(done, dict), "done must be an object")
    completed, moved = done.get("completed"), done.get("moved_next")
    _strings(completed, "done.completed", ids=True, unique=True)
    _strings(moved, "done.moved_next", ids=True, unique=True)
    planned = {pkg["item"] for pkg in entry["plan"]["packages"]}
    _need(not set(completed) & set(moved) and set(completed) | set(moved) == planned,
          "done must cover exactly all plan items without contradictory IDs")
    feedback = done.get("feedback", [])
    _need(isinstance(feedback, list) and all(isinstance(f, dict) and f.get("item") in planned for f in feedback),
          "done.feedback must reference only plan items")
    for ident in planned:
        _need(ident in items, f"{ident}: missing backlog parent")
        if ident in completed:
            _completion(state, entry, items[ident])
        elif historical:
            acceptance = items[ident].get("delivery_acceptance", {})
            _need(acceptance.get("sprint") != entry["plan"]["sprint"],
                  f"{ident}: this Sprint accepted an item recorded as moved_next")
        else:
            _need("delivery_acceptance" not in items[ident] and items[ident].get("status") != "已完成",
                  f"{ident}: completed item cannot be moved_next")


def done_problems(root, sprint_stem, done):
    try:
        root = Path(root).resolve()
        state = _state(root)
        if state is None or sprint_stem not in _current(state):
            return []
        entry = _current(state)[sprint_stem]
        _data, items = _backlog(root)
        _provenance(state, items)
        _check_done(state, entry, items, done)
        return []
    except Exception as error:
        return [f"delivery {sprint_stem}: {error}"]
