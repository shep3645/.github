# Changelog

## 2026-10-12

- `.github/workflows/claude-review.yml`: accept `CLAUDE_CODE_OAUTH_TOKEN` (optional) next to `ANTHROPIC_API_KEY` (now optional too) and pass it as `claude_code_oauth_token`. When the token is set the API key is withheld, since Claude Code lets `ANTHROPIC_API_KEY` win and the shep3645/utils and code key (set 2026-03-28) fails with "Invalid API key". Without a key, the action's inline-comment classifier posts every buffered comment instead of classifying them.
- `tests/test_claude_review_workflow.py`: pin both secrets optional, the token passed, and the key withheld when a token is set.

- `.github/workflows/claude-review.yml`: add a failure-only step, `Explain a failed Claude run`, that prints the init model and API-key source plus the result record (subtype, turns, cost, error text up to 600 chars) from `$RUNNER_TEMP/claude-execution-output.json`. Every `@claude` review in shep3645/utils that reached Claude (2026-09-14 x3, 2026-10-12) failed with only `result is_error:true`: the action hides its output unless `show_full_output` is on, and that would print the whole transcript. The transcript is never printed. Output is wrapped in `::stop-commands::` so the result text cannot issue workflow commands, and the step never fails itself.
- `tests/test_claude_review_workflow.py`: run the step's script against fixture SDK output (API error, injected `::` commands, a 5,000-char result, a missing and an unreadable file), and pin the contract (`if: failure()`, result record only, no `show_full_output: true`).

## 2026-08-27

- `.github/workflows/claude-review.yml` — Pass the built-in GitHub token explicitly so API-key reviews no longer require caller branches to grant OIDC; prevents pre-job `startup_failure` runs on long-lived branches.
- `tests/test_claude_review_workflow.py` — Pin the no-OIDC reusable-workflow compatibility contract.
