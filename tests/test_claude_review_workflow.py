from pathlib import Path
import re
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


if __name__ == "__main__":
    unittest.main()
