"""Exercise shipped hook command strings with isolated interpreter names."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


PLUGIN = Path(__file__).resolve().parents[2] / "plugins/agile"
SHELL = shutil.which("sh")


@unittest.skipUnless(os.name == "posix" and SHELL, "POSIX interpreter matrix runs in Linux CI")
class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="agile-launchers-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.hub = self.root / "hub"
        (self.hub / "agile-docs").mkdir(parents=True)
        self.backlog = self.hub / "agile-docs/backlog.json"
        self.backlog.write_text("{broken", encoding="utf-8")
        self.trace = self.root / "calls.txt"
        self.env = dict(os.environ, PATH=str(self.bin), LAUNCH_TRACE=str(self.trace),
                        PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        self.payload = json.dumps({"cwd": str(self.hub), "tool_input": {"file_path": str(self.backlog)}})
        hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.commands = {
            event: entries[0]["hooks"][0]["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN))
            for event, entries in hooks.items()
        }

    def interpreter(self, name, exit_code=None):
        command = (f"exec {shlex.quote(sys.executable)} \"$@\"" if exit_code is None
                   else f"exit {exit_code}")
        path = self.bin / name
        path.write_text(f'#!/bin/sh\nprintf "%s\\n" {shlex.quote(name)} >> "$LAUNCH_TRACE"\n{command}\n',
                        encoding="utf-8")
        path.chmod(0o755)

    def invoke(self, event="PostToolUse"):
        result = subprocess.run([SHELL, "-c", self.commands[event]], input=self.payload,
                                cwd=self.hub, env=self.env, capture_output=True,
                                text=True, encoding="utf-8", timeout=20)
        calls = self.trace.read_text(encoding="utf-8").splitlines() if self.trace.exists() else []
        return result, calls

    def assert_block(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_only_python_executes_hook(self):
        self.interpreter("python")
        result, calls = self.invoke()
        self.assert_block(result)
        self.assertEqual(calls, ["python"])

    def test_only_python3_executes_hook(self):
        self.interpreter("python3")
        result, calls = self.invoke()
        self.assert_block(result)
        self.assertEqual(calls, ["python3"])

    def test_both_names_do_not_duplicate_validation_failure(self):
        self.interpreter("python")
        self.interpreter("python3")
        result, calls = self.invoke()
        self.assert_block(result)
        self.assertEqual(calls, ["python"])

    def test_startup_failure_also_triggers_fallback(self):
        self.interpreter("python", exit_code=7)
        self.interpreter("python3")
        result, calls = self.invoke()
        self.assert_block(result)
        self.assertEqual(calls, ["python", "python3"])

    def test_both_missing_report_launcher_failure(self):
        result, calls = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)
        self.assertEqual(calls, [])

    def test_silent_success_does_not_fall_back(self):
        self.interpreter("python")
        self.interpreter("python3")
        self.payload = "{}"
        result, calls = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(calls, ["python"])

    def test_all_registered_hooks_support_python3_only(self):
        self.interpreter("python3")
        for event in self.commands:
            with self.subTest(event=event):
                if self.trace.exists():
                    self.trace.unlink()
                result, calls = self.invoke(event)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(calls, ["python3"])
                if result.stdout:
                    json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
