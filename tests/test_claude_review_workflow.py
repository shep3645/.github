from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "claude-review.yml"
CHECKOUT_V5_SHA = "08c6903cd8c0fde910a37f88322edcfb5dd907a8"
CLAUDE_CODE_ACTION_V1_SHA = "70fec183852c4f82f3f1969faed7dd60c5149ca7"
CONTRACT_WORKFLOW = (
    Path(__file__).parents[1]
    / ".github"
    / "workflows"
    / "reusable-workflow-contracts.yml"
)


class ClaudeReviewCompatibilityTests(unittest.TestCase):
    def test_reusable_workflow_supports_callers_without_oidc_permission(self):
        """Static API-key callers must not be forced to grant OIDC."""
        text = WORKFLOW.read_text(encoding="utf-8")
        permissions = re.search(
            r"(?m)^permissions:\n(?P<body>(?:^[ \t]+[^\n]*\n)*)", text
        )
        self.assertIsNotNone(permissions)
        self.assertNotIn("id-token:", permissions.group("body"))
        self.assertRegex(text, r"(?m)^\s+github_token: \$\{\{ github\.token \}\}$")

    def test_reusable_workflow_uses_node24_checkout(self):
        """GitHub-hosted runners must not force deprecated Node 20 actions."""
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(f"uses: actions/checkout@{CHECKOUT_V5_SHA}", text)
        self.assertNotIn("uses: actions/checkout@v5", text)
        self.assertNotIn("uses: actions/checkout@v4", text)

    def test_pr_discovery_fetch_uses_the_read_only_workflow_token(self):
        """Claude's head-branch fetch needs checkout's persisted auth."""
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("persist-credentials: true", text)
        self.assertRegex(text, r"(?m)^  contents: read$")
        self.assertRegex(text, r"(?m)^  pull-requests: write$")
        self.assertNotRegex(text, r"(?m)^\s+contents: write$")

    def test_reusable_workflow_pins_claude_action(self):
        """A secret-bearing review action must use an immutable commit."""
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            f"uses: anthropics/claude-code-action@{CLAUDE_CODE_ACTION_V1_SHA}",
            text,
        )
        self.assertNotIn("uses: anthropics/claude-code-action@v1", text)

    def test_contracts_are_checked_on_changes_and_weekly(self):
        text = CONTRACT_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("schedule:", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("actionlint", text)
        self.assertIn(f"uses: actions/checkout@{CHECKOUT_V5_SHA}", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn(
            "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8",
            text,
        )
        self.assertIn("./actionlint", text)
        self.assertNotIn("*.yml", text)



def explain_script() -> str:
    """The `run:` body of the failure-explanation step, as the runner sees it."""
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^      - name: Explain a failed Claude run\n.*?^        run: \|\n"
        r"(?P<body>(?:^          [^\n]*\n|^\n)*)",
        text,
    )
    if match is None:
        raise AssertionError("no 'Explain a failed Claude run' step with a run block")
    return textwrap.dedent(match.group("body"))


API_ERROR = (
    'API Error: 400 {"type":"error","error":{"type":"invalid_request_error",'
    '"message":"Your credit balance is too low to access the Anthropic API."}}'
)


def sdk_messages(result_text: str = API_ERROR) -> list:
    return [
        {"type": "system", "subtype": "init", "model": "claude-opus-5[1m]",
         "apiKeySource": "ANTHROPIC_API_KEY", "session_id": "s"},
        {"type": "user", "message": {"content": "REPO_FILE_CONTENT_MUST_NOT_PRINT"}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "TRANSCRIPT_TEXT_MUST_NOT_PRINT"}]}},
        {"type": "result", "subtype": "success", "is_error": True, "num_turns": 1,
         "duration_ms": 166, "total_cost_usd": 0, "result": result_text},
    ]


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "needs jq and bash")
class ExplainFailedRunTests(unittest.TestCase):
    def run_explain(self, messages=None, raw: str | None = None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claude-execution-output.json"
            if raw is not None:
                path.write_text(raw, encoding="utf-8")
            elif messages is not None:
                path.write_text(json.dumps(messages), encoding="utf-8")
            proc = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", explain_script()],
                env={**os.environ, "EXECUTION_FILE": str(path)},
                capture_output=True, text=True, timeout=30,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_prints_the_api_error_and_model_but_not_the_transcript(self):
        out = self.run_explain(sdk_messages())
        self.assertIn("init: model=claude-opus-5[1m] apiKeySource=ANTHROPIC_API_KEY", out)
        self.assertIn("result: subtype=success is_error=true turns=1 duration_ms=166 cost_usd=0", out)
        self.assertIn("result text: API Error: 400", out)
        self.assertIn("credit balance is too low", out)
        self.assertNotIn("REPO_FILE_CONTENT_MUST_NOT_PRINT", out)
        self.assertNotIn("TRANSCRIPT_TEXT_MUST_NOT_PRINT", out)

    def test_output_cannot_issue_workflow_commands(self):
        out = self.run_explain(sdk_messages("boom\n::warning::injected\r\n::add-mask::x"))
        lines = out.splitlines()
        opener = re.fullmatch(r"::stop-commands::(claude-explain-[0-9a-f]{16})", lines[0])
        self.assertIsNotNone(opener, lines[0])
        self.assertEqual(lines[-1], f"::{opener.group(1)}::")
        for line in lines[1:-1]:
            self.assertFalse(line.startswith("::"), line)
        self.assertIn("result text: boom ::warning::injected ::add-mask::x", out)

    def test_long_result_text_is_truncated(self):
        out = self.run_explain(sdk_messages("x" * 5000))
        line = next(l for l in out.splitlines() if l.startswith("result text: "))
        self.assertEqual(len(line), len("result text: ") + 600)

    def test_a_missing_or_unreadable_file_does_not_fail_the_step(self):
        self.assertIn("failed before Claude started", self.run_explain())
        self.assertIn("Could not read", self.run_explain(raw="not json"))


class FailureExplanationContractTests(unittest.TestCase):
    def test_failed_runs_explain_themselves_without_the_transcript(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        step = text.split("- name: Explain a failed Claude run", 1)
        self.assertEqual(len(step), 2, "the failure-explanation step is missing")
        self.assertIn("if: failure()", step[1])
        self.assertIn("claude-execution-output.json", step[1])
        self.assertIn("::stop-commands::", step[1])
        self.assertIn('select(.type == "result")', step[1])
        # Full output prints every message, tool results included.
        self.assertNotRegex(text, r"(?m)^\s+show_full_output:\s*[\"']?true")


if __name__ == "__main__":
    unittest.main()
