# markdown-graphics: working notes for Claude

## Toolchain

- Python 3.13 or newer; the only dependency is console-look (pinned to a tag in `pyproject.toml`).
- `sips` (macOS) only for screenshots in slideshows and comparisons.
- Lines at most 100 characters (`.editorconfig`).

## Commands

- Install for work: `pip install -e .`
- Tests: `python3 -m unittest discover -s Tests`
- Redraw this repo's own graphics: `markdown-graphics pictures` (and `banner` / `icon`), in the root

## Hard rules

- No dependency beyond the standard library and console-look.
- Nothing names a project: names, icons and folders come from `markdown-graphics.toml`.
- A change to how a kind draws must keep existing pictures byte for byte the same, unless the
  CHANGELOG says what changed and why.
- Every picture's words go into its `label`, so the alt text can hold them all.

## Where things go

- Settings and the `Stop` error: `src/markdown_graphics/project.py`
- Banners and section icons: `src/markdown_graphics/banners.py`
- Pictures and glyphs: `src/markdown_graphics/pictures.py`; flags: `flags.py`
- Command line: `src/markdown_graphics/__main__.py`
- This README's own pictures: `docs/pictures/` → `assets/pictures/`

## Before every commit

Run the tests, redraw this repo's pictures if a kind changed, and add a line to `CHANGELOG.md`
under a new version for anything a user notices.

## Git

- English everywhere; commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:` …).
- Work on a branch and merge into `main` through a pull request with green CI.
- A release is a tag `vX.Y.Z` that matches `pyproject.toml` and `CHANGELOG.md`.
