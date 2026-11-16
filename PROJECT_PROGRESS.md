# Project Progress

## Current milestone
- Day 10 — Automated testing and GitHub Actions.

## Completed
- Project structure created.
- Flask app configured.
- SQLite database and seed data added.
- Homepage and category selection implemented.
- Quiz logic, scoring, and result page added.
- Question management with search and filter added.
- Quiz history and score summary implemented.
- Responsive frontend styling added.
- End-to-end checks completed for categories, scoring, unanswered answers, history, search/filter, and question add/edit/delete.
- Invalid question category and answer inputs are validated before saving.
- App code integrated into the repository's default `main` branch.
- Automated regression tests and a GitHub Actions workflow added locally.
- All 6 automated tests pass locally.

## Next steps
- Confirm the GitHub Actions check passes after the test/CI changes are pushed.
- Finish Day 11 documentation/collaboration practice and Day 12 release steps.

## Application status
- Flask and SQLite features are implemented and covered by automated tests.
- No known application bugs; GitHub Actions has not run yet for the new workflow.

## Files created or modified in this milestone
- `tests/test_app.py`
- `.github/workflows/tests.yml`
- `README.md`
- `PROJECT_PROGRESS.md`

## Git commands practised
- The app was pushed to GitHub and both `main` and `master` were synchronized in earlier work.
- Branch and push workflows were used for the previous GitHub sync; the CI update is the current GitHub practice.

## Commits
- `2426ba3` — Initial quiz app setup
- `3d60cea` — Merge app into the default `main` branch
- `25a249c` — Validate quiz management inputs
