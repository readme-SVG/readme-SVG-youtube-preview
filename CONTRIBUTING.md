# Contributing Guide

First off: huge thanks for considering a contribution. You’re helping make this project more useful for everyone shipping README tooling, and that absolutely matters.

This document is the contributor playbook for `readme-SVG-youtube-preview`: how to ask things, report issues, ship clean PRs, and avoid common review friction.

## Introduction

Contributions are welcome in all forms:

- bug fixes
- feature additions
- docs improvements
- refactors with measurable DX/runtime wins
- test coverage upgrades

If you plan to invest non-trivial effort, opening an issue/discussion first is strongly recommended so we can align early and avoid wasted cycles.

## I Have a Question

Please do **not** use GitHub Issues for general usage/support questions.

Issues are reserved for:

- reproducible bugs
- actionable enhancements
- concrete project tasks

For questions, use one of these channels:

- GitHub Discussions (preferred, if enabled)
- maintainer social channels listed in `README.md`
- relevant dev communities where markdown/svg tooling is discussed

When asking, include context that helps others answer fast:

- what you’re trying to build
- what you already tried
- actual URL/params used (sanitize sensitive details)
- expected output vs what you got

## Reporting Bugs

High-signal bug reports get fixed faster. Low-signal reports usually stall.

### 1) Check for duplicates first

Before opening a new bug, scan existing issues (open + recently closed) and search by:

- endpoint (`/badge`, `/info`)
- parameter name (`title_position`, `embed`, etc.)
- error text/status code

### 2) Include environment details

Please include:

- OS + version (e.g., Ubuntu 22.04, macOS 14)
- Python version
- dependency state (`pip freeze` or at least Flask/Gunicorn versions)
- deployment target (local Flask, Vercel, etc.)
- browser version (if UI issue)

### 3) Provide exact reproduction steps

Use a deterministic, step-by-step script. Example:

```text
1. Start app with: flask --app api.index run --debug
2. Call: /badge?id=<id>&width=600&title_position=outside_top
3. Observe generated SVG in browser / file output
```

### 4) Expected vs actual behavior

State both explicitly:

- expected: what should have happened
- actual: what really happened

Attach evidence when possible:

- failing URL
- response body/status
- screenshot/GIF for UI issues
- logs/tracebacks

## Suggesting Enhancements

Feature requests are welcome, but please frame them as an engineering problem with context.

A strong enhancement proposal includes:

- **Problem statement:** what pain point exists right now
- **Why now:** why this change is worth project complexity
- **Proposed solution:** API/design sketch
- **Use cases:** real scenarios that benefit
- **Trade-offs:** compatibility/performance/maintenance impact

Good examples:

- adding optional font size controls with sane clamping
- adding themes while preserving current URL contract
- adding deterministic test fixtures for SVG snapshots

Weak examples:

- “add more customization” with no concrete scope
- “make it better/faster” without measurable target

## Local Development / Setup

### Fork and clone

```bash
# 1) Fork on GitHub, then clone your fork
git clone https://github.com/<your-username>/readme-SVG-youtube-preview.git
cd readme-SVG-youtube-preview

# 2) Add upstream remote
git remote add upstream https://github.com/readme-SVG/readme-SVG-youtube-preview.git
```

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment configuration

At the moment, this project does not require mandatory `.env` variables for core functionality.

If your contribution introduces env-based config:

1. add `.env.example`
2. document each variable in `README.md`
3. keep sensible defaults for local dev when possible

### Run locally

```bash
flask --app api.index run --debug
# open http://127.0.0.1:5000
```

### Quick smoke checks

```bash
curl "http://127.0.0.1:5000/info?id=dQw4w9WgXcQ"
curl "http://127.0.0.1:5000/badge?id=dQw4w9WgXcQ" -o /tmp/card.svg
```

## Pull Request Process

### Branching strategy

Use clear branch names:

- `feature/<short-description>`
- `bugfix/<issue-or-short-description>`
- `docs/<scope>`
- `chore/<scope>`

Examples:

- `feature/custom-font-size`
- `bugfix/title-wrap-outside-top`
- `docs/readme-rewrite`

### Commit message format

Use **Conventional Commits**.

Examples:

- `feat: add embed=false mode for external thumbnail links`
- `fix: clamp border width to prevent invalid SVG stroke`
- `docs: expand usage examples for shorts URLs`
- `refactor: isolate svg text wrapping helper`

### Sync with upstream before PR

Keep your branch fresh to reduce merge pain:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git checkout <your-branch>
git rebase main
```

### PR description checklist

Your PR description should include:

- summary of what changed and why
- linked issue(s), if applicable (`Closes #123`)
- testing evidence (commands + outputs)
- screenshots for any visible UI changes
- breaking-change note (if API/behavior changed)

Keep PRs focused. Massive mixed-scope PRs are slower to review and harder to merge safely.

## Styleguides

### Code quality expectations

- Keep patches surgical and relevant to the stated problem.
- Preserve backward compatibility unless explicitly discussed.
- Avoid unnecessary dependency creep.
- Prefer readable, boring code over clever-but-fragile tricks.

### Formatting and linting

Current repo does not enforce a strict linter/formatter pipeline yet. Recommended baseline:

```bash
python -m compileall api
```

If you introduce tooling (e.g., `ruff`, `black`, `flake8`, `prettier`), do it in a dedicated PR or clearly isolate formatting-only commits from logic changes.

### Architecture conventions

- `api/index.py`: request parsing, validation, route composition
- `api/card.py`: SVG/rendering internals and thumbnail embedding
- `app.js` + `index.html`: client-side generator UX

Try to keep concerns separated accordingly.

## Testing

All non-trivial changes should include validation.

Minimum bar before opening PR:

```bash
python -m compileall api
flask --app api.index run --debug
curl "http://127.0.0.1:5000/info?id=dQw4w9WgXcQ"
curl "http://127.0.0.1:5000/badge?id=dQw4w9WgXcQ" -o /tmp/card.svg
```

If you add new logic paths, add tests where practical and include the exact execution command in the PR.

## Code Review Process

- Maintainers review incoming PRs for correctness, scope, and regressions.
- Typical expectation: at least one maintainer approval before merge.
- Reviewers may request changes; please respond with follow-up commits (or a clean rebase if requested).
- If feedback is unclear, ask directly in the PR thread instead of guessing.
- Once approved, maintainers handle final merge strategy (squash/rebase/merge commit).

Thanks again for contributing and helping keep the project sharp.
