---
name: Lineage manual review
about: Tracks lineage classification updates that require human review
title: "Lineage classification update requires review"
labels: lineage-update, manual-review
---

## Reason for review

- [ ] New lineages need approval
- [ ] QA disagreements present
- [ ] Output validation failed
- [ ] Other

## Files to review

- `pull_hexcodes/pending_additions.csv`
- `pull_hexcodes/qa_disagreements.csv`
- `lineage_update_run_report.md`

## Resolution steps

1. Review pending additions.
2. Enter approval decisions in `approve1`.
3. Resolve QA disagreements, if present.
4. Re-run the GitHub Action manually.
5. Confirm PR opens successfully.