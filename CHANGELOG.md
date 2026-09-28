# Changelog

## 2026-09-28

- `prompts/es_trend_day_research.yaml` — Add a staged research prompt for classifying, recognizing and predicting ES trend days (axis-based labels, remaining-move targets and baselines, decision-time features including an MI ablation, no-look-ahead validation with a hypothesis budget, e-ratio and fade-veto tests).

## 2026-08-27

- `.github/workflows/claude-review.yml` — Pass the built-in GitHub token explicitly so API-key reviews no longer require caller branches to grant OIDC; prevents pre-job `startup_failure` runs on long-lived branches.
- `tests/test_claude_review_workflow.py` — Pin the no-OIDC reusable-workflow compatibility contract.
