# Changelog

## 2026-08-27

- `.github/workflows/claude-review.yml` — Pass the built-in GitHub token explicitly so API-key reviews no longer require caller branches to grant OIDC; prevents pre-job `startup_failure` runs on long-lived branches.
- `tests/test_claude_review_workflow.py` — Pin the no-OIDC reusable-workflow compatibility contract.
