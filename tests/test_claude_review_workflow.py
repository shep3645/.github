from pathlib import Path
import re
import unittest


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "claude-review.yml"


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


if __name__ == "__main__":
    unittest.main()
