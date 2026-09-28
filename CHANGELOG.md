# Changelog

## 2026-09-28

- `prompts/es_trend_day_research.yaml` — Add a research prompt for classifying and predicting ES trend days (ground-truth labels and subtypes, decision-time features including an MI ablation, no-look-ahead validation, e-ratio trigger evaluation).

## 2026-08-27

- `.github/workflows/claude-review.yml` — Pass the built-in GitHub token explicitly so API-key reviews no longer require caller branches to grant OIDC; prevents pre-job `startup_failure` runs on long-lived branches.
- `tests/test_claude_review_workflow.py` — Pin the no-OIDC reusable-workflow compatibility contract.
