"""Cross-repository delivery CLI regressions in temporary hubs."""

import copy
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[2] / "plugins/agile/scripts/agile.py"
SPRINT = "sprint-001-20261118"
BE_INSTRUCTIONS = "backend-only SECRET_IMPL marker not secret"
FE_INSTRUCTIONS = "frontend-only implementation marker"
CONTRACT = "POST /login actual interface"
REVIEWER = "reviewer-1"
NOTE = "接口与测试证据已人工核验"
OVERALL_EVIDENCE = ["web-app@def end-to-end login tests PASS", "用户确认前后端登录可用"]


def changed(value, path, replacement):
    result = copy.deepcopy(value)
    target = result
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = replacement
    return result


class DeliveryTests(unittest.TestCase):
    maxDiff = 3000

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="agile-delivery-")
        self.addCleanup(temporary.cleanup)
        self.sandbox = Path(temporary.name).resolve()
        self.hub = self.sandbox / "hub with spaces"
        self.docs = self.hub / "agile-docs"
        self.sprints = self.hub / "sprints"
        self.inputs = self.sandbox / "inputs"
        for directory in (self.docs, self.sprints, self.inputs):
            directory.mkdir(parents=True)
        self.workers = [self.sandbox / name for name in ("api-server", "web-app")]
        for worker in self.workers:
            worker.mkdir()
            (worker / "untouched.txt").write_text("real worker sentinel\n", encoding="utf-8")
        self.worker_snapshots = [self.snapshot(worker) for worker in self.workers]
        self.backlog_path = self.docs / "backlog.json"
        self.state_path = self.docs / "delivery.json"
        self.lock_path = self.docs / ".delivery.lock"
        self.sprint_path = self.sprints / f"{SPRINT}.md"
        self.done_path = self.sprints / f"{SPRINT}.done.yaml"
        self.backlog = {
            "schema": 1,
            "phases": [{"id": 1, "title": "基础", "items": [{
                "id": "F-001", "title": "登录", "type": "功能", "points": 3,
                "priority": "Must", "status": "待办", "confirmed": True,
                "created_at": date.today().isoformat(),
                "detail": ["验收：前后端登录可用"],
            }]}],
        }
        self.write_json(self.backlog_path, self.backlog)
        self.sprint_text = (
            "# Sprint 001\n\n- 状态: 规划完成\n"
            "- 周期: 2026-11-18 ~ 2026-12-01\n\n"
            "## 任务清单\n- F-001 登录 (3)\n"
        )
        self.sprint_path.write_text(self.sprint_text, encoding="utf-8")
        self.context = {
            "VISION.md": "GLOBAL_VISION: 前后端共同交付登录能力",
            "PRD.md": "GLOBAL_PRD: 用户可通过前后端登录",
            "ARCHITECTURE.md": "GLOBAL_C4: 浏览器 -> API -> 数据库",
            "ADR.md": "GLOBAL_ADR: 登录协议以实际接口交接",
            "backend.md": "BACKEND_CONTEXT: api-server implementation scope",
            "frontend.md": "FRONTEND_CONTEXT: web-app implementation scope",
        }
        for name, content in self.context.items():
            (self.docs / name).write_text(f"# {name}\n\n{content}\n", encoding="utf-8")
        self.plan = {
            "schema": 1, "project_id": "demo", "sprint": SPRINT, "revision": 1,
            "goal": "登录可用",
            "context": ["agile-docs/PRD.md", "agile-docs/ARCHITECTURE.md", "agile-docs/ADR.md"],
            "packages": [
                {"id": "WP-001", "item": "F-001", "repo": "api-server", "title": "后端接口",
                 "instructions": [BE_INSTRUCTIONS], "acceptance": ["API测试通过"],
                 "depends_on": [], "context": ["agile-docs/backend.md"],
                 "deliverables": ["api-contract"]},
                {"id": "WP-002", "item": "F-001", "repo": "web-app", "title": "前端页面",
                 "instructions": [FE_INSTRUCTIONS], "acceptance": ["登录集成通过"],
                 "depends_on": ["WP-001"], "context": ["agile-docs/frontend.md"],
                 "deliverables": []},
            ],
        }

    def tearDown(self):
        for worker, before in zip(self.workers, self.worker_snapshots):
            self.assertEqual(before, self.snapshot(worker), f"worker repo modified: {worker}")
        for path in self.hub.rglob("*.done*.yaml"):
            self.assertTrue(path.name.startswith("sprint-"), f"unexpected package completion: {path}")
            self.assertIn(path.parent, (self.sprints, self.sprints / "archive"))

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def snapshot(root):
        entries = {}
        for path in sorted(root.rglob("*")):
            name = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries[name] = ("symlink", os.readlink(path))
            elif path.is_dir():
                entries[name] = ("directory",)
            else:
                entries[name] = ("file", path.read_bytes())
        return entries

    def cli(self, *args, ok=True):
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), *(str(arg) for arg in args)],
            cwd=self.sandbox, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=20,
        )
        diagnostic = f"args={args!r}\nexit={result.returncode}\n{result.stdout}\n{result.stderr}"
        if ok:
            self.assertEqual(result.returncode, 0, diagnostic)
        else:
            self.assertNotEqual(result.returncode, 0, diagnostic)
            self.assertTrue((result.stdout + result.stderr).strip(), diagnostic)
        return result

    def work(self, *args, ok=True):
        return self.cli("work", *args, "--root", self.hub, ok=ok)

    def reject(self, *args):
        before = self.snapshot(self.hub)
        result = self.work(*args, ok=False)
        self.assertEqual(before, self.snapshot(self.hub), "rejected command wrote to hub")
        return result

    def check(self, ok=True):
        before = self.snapshot(self.hub)
        result = self.cli("check", self.hub, ok=ok)
        self.assertEqual(before, self.snapshot(self.hub), "check must not mutate hub")
        return result

    def install_plan(self, plan=None):
        path = self.write_json(self.inputs / "plan.json", self.plan if plan is None else plan)
        self.work("plan", path)
        return path

    def export(self, package="WP-001"):
        result = self.work("export", SPRINT, package)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        self.assertIsInstance(payload["plan_digest"], str)
        self.assertTrue(payload["plan_digest"])
        return payload

    def receipt(self, payload, receipt_id="be-1", package="WP-001", result="completed", revision=1):
        backend = package == "WP-001"
        repo = "api-server" if backend else "web-app"
        return {
            "schema": 1, "id": receipt_id, "project_id": "demo", "sprint": SPRINT,
            "revision": revision, "plan_digest": payload["plan_digest"], "package_id": package,
            "repo": repo, "result": result, "summary": "独立仓库执行结果",
            "evidence": [f"{repo}@abc tests PASS"],
            "artifacts": [{"name": "api-contract", "source": "api-server@abc:docs/api.md",
                           "content": CONTRACT}] if backend else [],
        }

    def submit(self, receipt):
        path = self.write_json(self.inputs / "receipt.json", receipt)
        self.work("submit", path)
        return path

    def accept(self, receipt_id):
        self.work("accept", receipt_id, "--reviewer", REVIEWER, "--note", NOTE)

    def finish_args(self):
        return ("finish", SPRINT, "F-001", "--reviewer", REVIEWER,
                "--evidence", OVERALL_EVIDENCE[0], "--evidence", OVERALL_EVIDENCE[1])

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def item(self):
        return json.loads(self.backlog_path.read_text(encoding="utf-8"))["phases"][0]["items"][0]

    def records(self):
        records = self.state()["receipts"]
        by_id = {record["receipt"]["id"]: record for record in records}
        self.assertEqual(len(records), len(by_id), "receipt IDs must be unique")
        return by_id

    def assert_pending(self):
        self.assertEqual(self.item()["status"], "待办")
        self.assertNotIn("delivery_acceptance", self.item())
        self.assertEqual(self.sprint_path.read_text(encoding="utf-8"), self.sprint_text)
        self.assertFalse(self.done_path.exists())

    def accept_both(self):
        self.install_plan()
        backend = self.export()
        self.submit(self.receipt(backend))
        self.accept("be-1")
        frontend = self.export("WP-002")
        self.submit(self.receipt(frontend, "fe-1", "WP-002"))
        self.accept("fe-1")
        return backend

    def done_ids(self, key):
        """Read only the flat ID lists in the existing done-file contract, not general YAML."""
        text = self.done_path.read_text(encoding="utf-8")
        if text.lstrip().startswith("{"):
            return json.loads(text)[key]
        match = re.search(
            rf"(?m)^{re.escape(key)}:[ \t]*(.*(?:\n(?:[ \t]+[^\n]*|-[^\n]*|[ \t]*))*)",
            text,
        )
        self.assertIsNotNone(match, f"missing {key}: {text}")
        return re.findall(r"\b(?:F|T|B|WP)-\d+\b", match.group(1))

    def test_cross_repo_golden_path(self):
        self.check()
        self.install_plan()
        backend = self.export()
        backend_text = json.dumps(backend, ensure_ascii=False)
        # Declared shared PRD/C4/ADR stay present; unrelated worker details do not.
        for name in ("PRD.md", "ARCHITECTURE.md", "ADR.md", "backend.md"):
            self.assertIn(self.context[name], backend_text)
        self.assertIn(BE_INSTRUCTIONS, backend_text)
        self.assertNotIn(FE_INSTRUCTIONS, backend_text)
        self.assertNotIn(self.context["frontend.md"], backend_text)
        self.reject("export", SPRINT, "WP-002")
        self.reject(*self.finish_args())
        self.assert_pending()

        receipt = self.receipt(backend)
        self.submit(receipt)
        self.assertEqual(self.records()["be-1"], {"receipt": receipt, "acceptance": None})
        self.reject("export", SPRINT, "WP-002")
        self.reject(*self.finish_args())
        self.assert_pending()
        self.accept("be-1")
        self.assertEqual(self.records()["be-1"]["acceptance"], {"reviewer": REVIEWER, "note": NOTE})
        frontend = self.export("WP-002")
        frontend_text = json.dumps(frontend, ensure_ascii=False)
        self.assertEqual(backend["plan_digest"], frontend["plan_digest"])
        for name in ("PRD.md", "ARCHITECTURE.md", "ADR.md", "frontend.md"):
            self.assertIn(self.context[name], frontend_text)
        self.assertIn(CONTRACT, frontend_text)
        self.assertIn("api-server@abc:docs/api.md", frontend_text)
        self.assertIn(FE_INSTRUCTIONS, frontend_text)
        self.assertNotIn(BE_INSTRUCTIONS, frontend_text)
        self.assertNotIn(self.context["backend.md"], frontend_text)
        self.reject(*self.finish_args())
        self.submit(self.receipt(frontend, "fe-1", "WP-002"))
        self.reject(*self.finish_args())
        self.accept("fe-1")
        self.assert_pending()
        self.check()

        delivery_before = self.state_path.read_bytes()
        self.work(*self.finish_args())
        self.assertEqual(self.item()["status"], "已完成")
        self.assertEqual(self.item()["delivery_acceptance"], {
            "project_id": "demo", "sprint": SPRINT, "revision": 1,
            "plan_digest": backend["plan_digest"], "receipts": ["be-1", "fe-1"],
            "reviewer": REVIEWER, "evidence": OVERALL_EVIDENCE,
        })
        self.assertEqual(delivery_before, self.state_path.read_bytes(), "finish belongs in backlog only")
        self.assertEqual(self.sprint_path.read_text(encoding="utf-8"), self.sprint_text)
        self.assertFalse(self.done_path.exists())
        self.work("close", SPRINT)
        self.assertEqual(self.done_ids("completed"), ["F-001"])
        self.assertEqual(self.done_ids("moved_next"), [])
        self.assertEqual(self.sprint_path.read_text(encoding="utf-8"), self.sprint_text)
        self.check()

    def test_plan_persists_raw_plan_and_context_snapshots(self):
        self.install_plan()
        exported = self.export()
        state = self.state()
        self.assertEqual(state["schema"], 1)
        self.assertEqual(state["project_id"], "demo")
        self.assertEqual(state["receipts"], [])
        self.assertEqual(len(state["plans"]), 1)
        saved = state["plans"][0]
        self.assertEqual(saved["plan"], self.plan)
        self.assertEqual(saved["parents"], [{key: value for key, value in self.item().items()
                                           if key in ("id", "title", "type", "detail", "refs", "acceptance")}])
        self.assertEqual(saved["digest"], exported["plan_digest"])
        snapshots = {entry["path"]: entry for entry in saved["snapshots"]}
        self.assertEqual(len(snapshots), len(saved["snapshots"]))
        expected_paths = set(self.plan["context"])
        for package in self.plan["packages"]:
            expected_paths.update(package["context"])
        for path in expected_paths:
            self.assertEqual(snapshots[path]["content"], (self.hub / path).read_bytes().decode("utf-8"))
            self.assertRegex(snapshots[path]["sha256"], r"^[0-9a-fA-F]{64}$")
        self.check()

    def test_exact_retries_are_idempotent(self):
        path = self.install_plan()
        before = self.snapshot(self.hub)
        self.work("plan", path)
        self.assertEqual(before, self.snapshot(self.hub))
        backend = self.export()
        receipt_path = self.submit(self.receipt(backend))
        before = self.snapshot(self.hub)
        self.work("submit", receipt_path)
        self.assertEqual(before, self.snapshot(self.hub))
        self.accept("be-1")
        before = self.snapshot(self.hub)
        self.accept("be-1")
        self.assertEqual(before, self.snapshot(self.hub))
        self.submit(self.receipt(self.export("WP-002"), "fe-1", "WP-002"))
        self.accept("fe-1")
        self.work(*self.finish_args())
        before = self.snapshot(self.hub)
        self.work(*self.finish_args())
        self.assertEqual(before, self.snapshot(self.hub))

    def test_receipt_id_cannot_be_reused_for_different_content(self):
        self.install_plan()
        receipt = self.receipt(self.export())
        self.submit(receipt)
        path = self.write_json(self.inputs / "conflict.json", changed(receipt, ("summary",), "different"))
        self.reject("submit", path)
        self.assertEqual(self.records()["be-1"]["receipt"], receipt)

    def test_receipt_identity_and_unknown_fields_are_validated(self):
        self.install_plan()
        receipt = self.receipt(self.export())
        cases = [
            (("project_id",), "other"), (("repo",), "web-app"), (("revision",), 2),
            (("sprint",), "sprint-999-20261118"), (("plan_digest",), "not-the-exported-digest"),
            (("package_id",), "WP-999"), (("schema",), 2), (("revision",), True),
            (("unexpected",), "field"), (("artifacts", 0, "unexpected"), "field"),
        ]
        for path, value in cases:
            with self.subTest(field=path, value=value):
                invalid = self.write_json(self.inputs / "invalid.json", changed(receipt, path, value))
                self.reject("submit", invalid)

    def test_completed_receipt_requires_evidence_and_named_deliverable(self):
        self.install_plan()
        receipt = self.receipt(self.export())
        cases = [
            (("evidence",), []), (("evidence",), [""]), (("evidence",), ["   "]),
            (("artifacts",), []), (("artifacts", 0, "name"), "unrelated-document"),
            (("artifacts", 0, "content"), ""), (("artifacts", 0, "source"), ""),
        ]
        for path, value in cases:
            with self.subTest(field=path, value=value):
                invalid = self.write_json(self.inputs / "invalid.json", changed(receipt, path, value))
                self.reject("submit", invalid)

    def test_partial_and_blocked_receipts_never_release_dependencies(self):
        self.install_plan()
        payload = self.export()
        for result in ("partial", "blocked"):
            with self.subTest(result=result):
                receipt = self.receipt(payload, f"be-{result}", result=result)
                receipt["evidence"] = []
                receipt["artifacts"] = []
                self.submit(receipt)
                self.assertEqual(self.records()[receipt["id"]]["receipt"], receipt)
                self.reject("accept", receipt["id"], "--reviewer", REVIEWER, "--note", NOTE)
                self.reject("export", SPRINT, "WP-002")
                self.reject(*self.finish_args())
                self.assertIsNone(self.records()[receipt["id"]]["acceptance"])
                self.assert_pending()
        self.assertEqual(set(self.records()), {"be-partial", "be-blocked"})
        self.check()

    def test_acceptance_and_finish_require_explicit_review_details(self):
        self.install_plan()
        self.submit(self.receipt(self.export()))
        for args in (
            ("accept", "be-1", "--note", NOTE),
            ("accept", "be-1", "--reviewer", REVIEWER),
            ("accept", "be-1", "--reviewer", " ", "--note", NOTE),
            ("accept", "be-1", "--reviewer", REVIEWER, "--note", " "),
            ("accept", "missing", "--reviewer", REVIEWER, "--note", NOTE),
        ):
            with self.subTest(args=args):
                self.reject(*args)
        self.accept("be-1")
        self.submit(self.receipt(self.export("WP-002"), "fe-1", "WP-002"))
        self.accept("fe-1")
        for args in (
            ("finish", SPRINT, "F-001", "--reviewer", REVIEWER),
            ("finish", SPRINT, "F-001", "--evidence", OVERALL_EVIDENCE[0]),
            ("finish", SPRINT, "F-001", "--reviewer", " ", "--evidence", OVERALL_EVIDENCE[0]),
            ("finish", SPRINT, "F-001", "--reviewer", REVIEWER, "--evidence", " "),
            ("finish", SPRINT, "WP-001", "--reviewer", REVIEWER, "--evidence", OVERALL_EVIDENCE[0]),
        ):
            with self.subTest(args=args):
                self.reject(*args)
        self.assert_pending()

    def test_distinct_receipts_preserve_independent_acceptance(self):
        self.install_plan()
        payload = self.export()
        first = self.receipt(payload)
        second = self.receipt(payload, "be-2")
        second["summary"] = "另一次独立执行，尚未验收"
        second["artifacts"][0]["content"] = "UNACCEPTED_CONTRACT must not be exported"
        self.submit(first)
        self.submit(second)
        self.accept("be-1")
        self.assertEqual(self.records()["be-1"], {
            "receipt": first, "acceptance": {"reviewer": REVIEWER, "note": NOTE},
        })
        self.assertEqual(self.records()["be-2"], {"receipt": second, "acceptance": None})
        exported = json.dumps(self.export("WP-002"), ensure_ascii=False)
        self.assertIn(CONTRACT, exported)
        self.assertNotIn("UNACCEPTED_CONTRACT", exported)
        self.check()

    def test_invalid_plan_dependencies_and_unknown_fields_are_atomic(self):
        cases = [
            (("packages", 0, "depends_on"), ["WP-999"]),
            (("packages", 0, "depends_on"), ["WP-002"]),
            (("packages", 0, "depends_on"), ["WP-001"]),
            (("packages", 1, "id"), "WP-001"),
            (("packages", 0, "item"), "F-999"),
            (("unexpected",), True), (("packages", 0, "unexpected"), True),
            (("schema",), 2), (("revision",), True),
            (("packages", 0, "instructions"), []), (("packages", 0, "acceptance"), []),
        ]
        for path, value in cases:
            with self.subTest(field=path, value=value):
                invalid = self.write_json(self.inputs / "invalid-plan.json", changed(self.plan, path, value))
                self.reject("plan", invalid)
                self.assertFalse(self.state_path.exists())
        self.install_plan()
        self.check()

    def test_plan_contexts_cannot_escape_root(self):
        outside = self.sandbox / "outside.md"
        outside.write_text("OUTSIDE_ROOT", encoding="utf-8")
        for field in (("context",), ("packages", 0, "context")):
            for context in (["../outside.md"], [str(outside)], ["agile-docs/../../outside.md"]):
                with self.subTest(field=field, context=context):
                    path = self.write_json(self.inputs / "escape.json", changed(self.plan, field, context))
                    self.reject("plan", path)
        self.assertEqual(outside.read_text(encoding="utf-8"), "OUTSIDE_ROOT")

    def test_symlink_contexts_cannot_escape_root(self):
        outside = self.sandbox / "external"
        outside.mkdir()
        (outside / "context.md").write_text("OUTSIDE_SYMLINK_TARGET", encoding="utf-8")
        try:
            (self.docs / "linked.md").symlink_to(outside / "context.md")
            (self.docs / "linked-directory").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            if os.environ.get("AGILE_REQUIRE_SYMLINK") == "1":
                self.fail(f"CI requires real symlink coverage: {error}")
            self.skipTest(f"symlinks unavailable: {error}")
        for context in ("agile-docs/linked.md", "agile-docs/linked-directory/context.md"):
            with self.subTest(context=context):
                path = self.write_json(self.inputs / "symlink.json", changed(self.plan, ("context",), [context]))
                self.reject("plan", path)

    def test_changed_context_refuses_export_and_check(self):
        self.install_plan()
        for name in ("PRD.md", "ARCHITECTURE.md", "ADR.md", "backend.md"):
            path = self.docs / name
            original = path.read_bytes()
            with self.subTest(context=name):
                path.write_bytes(original + b"\nCHANGED_AFTER_SNAPSHOT\n")
                self.reject("export", SPRINT, "WP-001")
                self.check(ok=False)
            path.write_bytes(original)
        self.export()
        self.check()

    def test_same_revision_cannot_change_plan(self):
        self.install_plan()
        path = self.write_json(self.inputs / "revision.json", changed(self.plan, ("goal",), "changed goal"))
        self.reject("plan", path)

    def test_new_revision_invalidates_previous_acceptance(self):
        previous = self.accept_both()
        revised = changed(self.plan, ("revision",), 2)
        revised["goal"] = "登录可用，补充会话验收"
        self.install_plan(revised)
        current = self.export()
        self.assertNotEqual(current["plan_digest"], previous["plan_digest"])
        self.assertEqual(set(self.records()), {"be-1", "fe-1"})
        self.reject("export", SPRINT, "WP-002")
        self.reject(*self.finish_args())
        stale = self.write_json(self.inputs / "stale.json", self.receipt(previous, "stale-be"))
        self.reject("submit", stale)
        self.assert_pending()
        self.check()
        self.submit(self.receipt(current, "be-v2", revision=2))
        self.accept("be-v2")
        self.submit(self.receipt(self.export("WP-002"), "fe-v2", "WP-002", revision=2))
        self.accept("fe-v2")
        self.work(*self.finish_args())
        acceptance = self.item()["delivery_acceptance"]
        self.assertEqual(acceptance["revision"], 2)
        self.assertEqual(acceptance["plan_digest"], current["plan_digest"])
        self.assertEqual(set(acceptance["receipts"]), {"be-v2", "fe-v2"})
        self.assertEqual(set(self.records()), {"be-1", "fe-1", "be-v2", "fe-v2"})
        self.check()

    def test_completed_business_item_cannot_be_replanned(self):
        self.accept_both()
        self.work(*self.finish_args())
        path = self.write_json(self.inputs / "revision.json", changed(self.plan, ("revision",), 2))
        self.reject("plan", path)

    def test_incomplete_close_requires_explicit_move_without_finishing(self):
        self.install_plan()
        self.reject("close", SPRINT)
        self.reject("close", SPRINT, "--move", "WP-001")
        self.reject("close", SPRINT, "--move", "F-999")
        self.assert_pending()
        backlog_before = self.backlog_path.read_bytes()
        self.work("close", SPRINT, "--move", "F-001")
        self.assertEqual(self.done_ids("completed"), [])
        self.assertEqual(self.done_ids("moved_next"), ["F-001"])
        self.assertEqual(self.backlog_path.read_bytes(), backlog_before)
        self.assertEqual(self.sprint_path.read_text(encoding="utf-8"), self.sprint_text)
        self.check()

    def test_close_accepts_repeatable_move_for_multiple_items(self):
        second = changed(self.backlog["phases"][0]["items"][0], ("id",), "F-002")
        second["title"] = "退出登录"
        self.backlog["phases"][0]["items"].append(second)
        self.write_json(self.backlog_path, self.backlog)
        self.sprint_text += "- F-002 退出登录 (3)\n"
        self.sprint_path.write_text(self.sprint_text, encoding="utf-8")
        package = copy.deepcopy(self.plan["packages"][1])
        package.update(id="WP-003", item="F-002", depends_on=[])
        self.plan["packages"].append(package)
        self.install_plan()
        self.reject("close", SPRINT, "--move", "F-001")
        backlog_before = self.backlog_path.read_bytes()
        self.work("close", SPRINT, "--move", "F-001", "--move", "F-002")
        self.assertEqual(self.done_ids("completed"), [])
        self.assertEqual(set(self.done_ids("moved_next")), {"F-001", "F-002"})
        self.assertEqual(self.backlog_path.read_bytes(), backlog_before)
        self.check()

    def test_direct_done_file_cannot_bypass_overall_acceptance(self):
        self.accept_both()
        self.done_path.write_text("completed:\n- F-001\nmoved_next: []\n", encoding="utf-8")
        self.check(ok=False)
        # Even a manually forged completed backlog status is not overall acceptance.
        self.backlog["phases"][0]["items"][0]["status"] = "已完成"
        self.write_json(self.backlog_path, self.backlog)
        self.check(ok=False)

    def test_check_validates_overall_acceptance_binding(self):
        self.accept_both()
        self.work(*self.finish_args())
        good = json.loads(self.backlog_path.read_text(encoding="utf-8"))
        for field, value in (("plan_digest", "forged"), ("receipts", ["missing"]), ("reviewer", "")):
            with self.subTest(field=field):
                bad = changed(good, ("phases", 0, "items", 0, "delivery_acceptance", field), value)
                self.write_json(self.backlog_path, bad)
                self.check(ok=False)
        self.write_json(self.backlog_path, good)
        self.check()

    def test_lock_contention_rejects_mutations_without_removing_other_lock(self):
        self.accept_both()
        receipt = self.receipt(self.export(), "be-1")
        receipt_path = self.write_json(self.inputs / "retry-receipt.json", receipt)
        new_receipt = self.write_json(self.inputs / "new-receipt.json", changed(receipt, ("id",), "be-3"))
        new_plan = self.write_json(self.inputs / "new-plan.json", changed(self.plan, ("revision",), 2))
        self.lock_path.write_text("held by another writer\n", encoding="utf-8")
        for args in (
            ("plan", new_plan), ("submit", new_receipt),
            ("accept", "be-2", "--reviewer", REVIEWER, "--note", NOTE),
            self.finish_args(), ("close", SPRINT, "--move", "F-001"),
        ):
            with self.subTest(command=args[0]):
                self.reject(*args)
                self.assertEqual(self.lock_path.read_text(encoding="utf-8"), "held by another writer\n")
        self.lock_path.unlink()
        self.work("submit", receipt_path)
        self.check()

    def test_malformed_delivery_state_fails_visibly_without_reset(self):
        plan_path = self.install_plan()
        good = self.state_path.read_bytes()
        for raw in ("{broken", "null", "[]", '{"schema":1}', '{"schema":99,"plans":[],"receipts":[]}'):
            with self.subTest(raw=raw):
                self.state_path.write_text(raw, encoding="utf-8")
                self.reject("status")
                self.reject("export", SPRINT, "WP-001")
                self.reject("plan", plan_path)
                self.check(ok=False)
        self.state_path.write_bytes(good)
        self.check()

    def test_check_detects_structurally_valid_but_corrupted_delivery_state(self):
        self.accept_both()
        good = self.state()
        cases = [
            (("plans", 0, "digest"), "forged"),
            (("plans", 0, "snapshots", 0, "content"), "tampered snapshot"),
            (("plans", 0, "snapshots", 0, "sha256"), "0" * 64),
            (("receipts", 0, "receipt", "project_id"), "other"),
            (("receipts", 0, "receipt", "repo"), "wrong-repo"),
            (("receipts", 0, "receipt", "plan_digest"), "forged"),
            (("receipts", 0, "receipt", "package_id"), "WP-999"),
            (("receipts", 0, "acceptance", "reviewer"), ""),
        ]
        for path, value in cases:
            with self.subTest(field=path):
                self.write_json(self.state_path, changed(good, path, value))
                self.check(ok=False)
        self.write_json(self.state_path, good)
        self.check()

    def test_status_is_read_only_and_brief_adds_bounded_work_summary(self):
        baseline = self.cli("brief", self.hub).stdout
        self.install_plan()
        before = self.snapshot(self.hub)
        status = self.work("status").stdout
        self.assertIn("WP-001", status)
        self.assertIn("WP-002", status)
        self.assertEqual(before, self.snapshot(self.hub))
        small = self.cli("brief", self.hub).stdout
        self.assertNotEqual(small, baseline, "brief omitted work summary")
        large = copy.deepcopy(self.plan)
        large["revision"] = 2
        for number in range(3, 153):
            package = copy.deepcopy(self.plan["packages"][0])
            package.update(id=f"WP-{number:03d}", title=f"LARGE_PACKAGE_{number}_" + "x" * 200)
            large["packages"].append(package)
        self.install_plan(large)
        summary = self.cli("brief", self.hub).stdout
        # A generous bound avoids binding tests to a particular translated sentence.
        self.assertLessEqual(len(summary.encode("utf-8")), len(small.encode("utf-8")) + 2048)
        self.assertNotIn(BE_INSTRUCTIONS, summary)
        self.assertNotIn(FE_INSTRUCTIONS, summary)
        self.assertNotIn(self.context["backend.md"], summary)

    def test_parent_requirement_drift_invalidates_execution(self):
        self.install_plan()
        exported = self.export()
        receipt_path = self.write_json(self.inputs / "old-receipt.json", self.receipt(exported))
        original = self.backlog_path.read_bytes()
        changed_backlog = copy.deepcopy(self.backlog)
        changed_backlog["phases"][0]["items"][0]["detail"] = ["验收：必须支持双因素认证"]
        self.write_json(self.backlog_path, changed_backlog)
        self.reject("export", SPRINT, "WP-001")
        self.reject("submit", receipt_path)
        self.check(ok=False)
        self.backlog_path.write_bytes(original)
        self.accept_both()
        self.write_json(self.backlog_path, changed_backlog)
        self.reject(*self.finish_args())
        self.install_plan(changed(self.plan, ("revision",), 2))
        current = self.export()
        self.assertNotEqual(exported["plan_digest"], current["plan_digest"])
        self.assertIn("双因素认证", json.dumps(current, ensure_ascii=False))
        self.reject("export", SPRINT, "WP-002")
        self.check()

    def test_pending_closure_blocks_late_mutations_but_allows_retries(self):
        exported = self.accept_both()
        self.work("close", SPRINT, "--move", "F-001")
        self.reject(*self.finish_args())
        self.reject("export", SPRINT, "WP-001")
        revised = self.write_json(self.inputs / "new-plan.json", changed(self.plan, ("revision",), 2))
        self.reject("plan", revised)
        late = self.write_json(self.inputs / "late.json", self.receipt(exported, "late-be"))
        self.reject("submit", late)
        before = self.snapshot(self.hub)
        self.submit(self.receipt(exported))
        self.accept("be-1")
        self.work("close", SPRINT, "--move", "F-001")
        self.assertEqual(before, self.snapshot(self.hub))
        self.assertIn("closing", self.work("status").stdout)
        self.assertEqual(self.item()["status"], "待办")
        self.check()

    def test_design_drift_allows_explicit_partial_closure(self):
        second = copy.deepcopy(self.backlog["phases"][0]["items"][0])
        second.update(id="F-002", title="退出登录")
        self.backlog["phases"][0]["items"].append(second)
        self.write_json(self.backlog_path, self.backlog)
        self.sprint_text += "- F-002 退出登录 (3)\n"
        self.sprint_path.write_text(self.sprint_text, encoding="utf-8")
        package = copy.deepcopy(self.plan["packages"][1])
        package.update(id="WP-003", item="F-002", depends_on=[])
        self.plan["packages"].append(package)
        self.accept_both()
        self.work(*self.finish_args())
        (self.docs / "PRD.md").write_text("# 新的产品要求\n", encoding="utf-8")
        self.reject("export", SPRINT, "WP-003")
        self.check(ok=False)
        revised = self.write_json(self.inputs / "new-plan.json", changed(self.plan, ("revision",), 2))
        self.reject("plan", revised)
        self.work("close", SPRINT, "--move", "F-002")
        self.assertEqual(self.done_ids("completed"), ["F-001"])
        self.assertEqual(self.done_ids("moved_next"), ["F-002"])
        self.check()
        (self.docs / "PRD.md").write_text("# 后续产品设计仍可演进\n", encoding="utf-8")
        self.check()
        self.archive_sprint()
        self.check()

    def archive_sprint(self):
        archive = self.sprints / "archive"
        archive.mkdir(exist_ok=True)
        self.sprint_path.write_text(self.sprint_text.replace("规划完成", "已关闭"), encoding="utf-8")
        self.sprint_path.rename(archive / self.sprint_path.name)
        self.done_path.rename(archive / f"{SPRINT}.done.processed.yaml")

    def test_archived_forged_completion_is_rejected(self):
        self.install_plan()
        self.backlog["phases"][0]["items"][0]["status"] = "已完成"
        self.write_json(self.backlog_path, self.backlog)
        self.done_path.write_text("completed:\n  - F-001\nmoved_next: []\nfeedback: []\n", encoding="utf-8")
        self.sprint_path.write_text(self.sprint_text.replace("规划完成", "已关闭"), encoding="utf-8")
        self.check(ok=False)
        self.archive_sprint()
        self.check(ok=False)
        (self.sprints / "archive" / f"{SPRINT}.done.processed.yaml").unlink()
        self.check(ok=False)

    def test_archived_carryover_can_finish_in_later_sprint(self):
        self.install_plan()
        self.work("close", SPRINT, "--move", "F-001")
        self.archive_sprint()
        self.check()
        next_sprint = "sprint-002-20261119"
        (self.sprints / f"{next_sprint}.md").write_text(self.sprint_text, encoding="utf-8")
        next_plan = changed(self.plan, ("sprint",), next_sprint)
        self.install_plan(next_plan)
        for package_id, receipt_id in (("WP-001", "be-next"), ("WP-002", "fe-next")):
            exported = json.loads(self.work("export", next_sprint, package_id).stdout)
            receipt = self.receipt(exported, receipt_id, package_id)
            receipt["sprint"] = next_sprint
            self.submit(receipt)
            self.accept(receipt_id)
        self.work("finish", next_sprint, "F-001", "--reviewer", REVIEWER,
                  "--evidence", OVERALL_EVIDENCE[0])
        self.assertEqual(self.item()["delivery_acceptance"]["sprint"], next_sprint)
        self.check()

    def test_projects_without_work_are_unchanged(self):
        before = self.snapshot(self.hub)
        self.check()
        self.cli("brief", self.hub)
        self.work("status")
        self.assertEqual(before, self.snapshot(self.hub))
        self.assertFalse(self.state_path.exists())
        self.assertFalse(self.lock_path.exists())
        self.assertFalse(self.done_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
