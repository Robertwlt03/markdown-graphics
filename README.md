<p align="center">
  <img src="assets/banner-readme.svg" alt="markdown-graphics: banners, icons and pictures for Markdown files." width="100%">
</p>

Draws the graphics that make a README or a guide easy to read, in one shared style: a banner on top, a colored icon
in front of each section, and pictures of lists, terminals, flows and layers, each in a light and a dark version so
GitHub shows the one that fits the reader. The pictures are drawn from small JSON files, so they stay in version
control and change with a single line.

## <img src="assets/icons/features.svg" height="33" align="absmiddle" alt="">What it does

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pictures/features-dark.svg">
  <img src="assets/pictures/features-light.svg" alt="Banners: your icon, a small line, a title and a subtitle on top of every Markdown file. Section icons: a colored tile with a white glyph in front of each heading. Pictures: grids, terminals, flows, layers, chips, buttons and slideshows from JSON. Light and dark: every picture twice, so GitHub shows the one that fits the reader. No dependencies: Python's standard library and console-look, nothing else. Accessible: every picture carries its words for screen readers." width="100%">
</picture>

## <img src="assets/icons/install.svg" height="33" align="absmiddle" alt="">Install

Python 3.13 or newer, on macOS or Linux. Screenshots in slideshows and comparisons need macOS (`sips`).

```bash
pip install git+https://github.com/Robertwlt03/markdown-graphics@v0.1.0
```

## <img src="assets/icons/use.svg" height="33" align="absmiddle" alt="">Use

Run the commands in your project's root. A `markdown-graphics.toml` there names your project; every setting is
optional:

```toml
name = "My Project"          # on banners and in their text for screen readers (default: the folder's name)
icon = "assets/icon.svg"     # your icon on banners (default: a blue tile with a prompt mark)
assets = "assets"            # banners, and icons/ for the section icons
pictures = "docs/pictures"   # one <name>.json per picture
pictures_out = "assets/pictures"
shots = "snapshots/current"  # screenshots for slideshows and comparisons
hand_drawn = ["footer"]      # banners the command never replaces
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pictures/terminal-dark.svg">
  <img src="assets/pictures/terminal-light.svg" alt="A terminal: markdown-graphics pictures draws 12 pictures in assets/pictures; markdown-graphics icon install green download draws assets/icons/install.svg." width="100%">
</picture>

```bash
markdown-graphics banner
```

```bash
markdown-graphics banner release-notes "Release notes" "What changed in each version."
```

```bash
markdown-graphics icon install green download
```

```bash
markdown-graphics pictures
```

- `banner` without texts asks for everything and offers to replace an existing banner. `--theme claude` draws it in
  Claude's ivory and clay, together with a matching footer, which suits a CLAUDE.md.
- `icon` takes a color (`blue`, `green`, `orange`, `clay` … see `--help`) and a glyph name such as `download`, or
  your own SVG shapes in a 24-point grid.
- `pictures` draws every description, or only the ones you name.

Show a picture with `<picture>`, so the dark version appears in dark mode, and put all of its words in the alt text:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pictures/features-dark.svg">
  <img src="assets/pictures/features-light.svg" alt="Every word of the picture" width="100%">
</picture>
```

## <img src="assets/icons/kinds.svg" height="33" align="absmiddle" alt="">How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pictures/flow-dark.svg">
  <img src="assets/pictures/flow-light.svg" alt="1 Describe: docs/pictures/<name>.json names a kind and its items. 2 Draw: markdown-graphics pictures writes a light and a dark SVG. 3 Show: <picture> in the Markdown file picks the right one." width="100%">
</picture>

Every description names its `kind`. Most kinds take a list of `items`, each with a glyph, a title and a sentence;
the descriptions in [`docs/pictures`](docs/pictures) drew every picture on this page.

| Kind | Draws |
|---|---|
| `button` | a macOS push button with a glyph and a title; `"style": "primary"` fills it |
| `grid` | items in columns; with `"code": true` the title is a command or path in a monospace chip |
| `chips` | a flag (`"flag": "DE"`) or a short code with a name and a second name, such as languages |
| `terminal` | a window that types its commands; lines are `[kind, text]` with `command`, `output`, `result`, `note` and `cursor` (the prompt waiting, its cursor blinking); an output's text may be pieces such as `["Made at ", ["accent", "ACME"]]`; `"width"` narrows it, such as for a phone |
| `flow` | numbered steps from left to right with arrows |
| `layers` | stacked rows for parts that build on each other, the top one first |
| `slideshow` | SVGs or screenshots that fade into each other with a caption |
| `compare` | one screenshot light and dark, with a divider that slides between them |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pictures/layers-dark.svg">
  <img src="assets/pictures/layers-light.svg" alt="Command line: markdown-graphics banner, icon and pictures. Kinds: button, grid, chips, terminal, flow, layers, slideshow, compare. markdown-graphics.toml: your project's name, icon and folders." width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/pictures/languages-dark.svg">
  <img src="assets/pictures/languages-light.svg" alt="English, Deutsch (German), Français (French), 日本語 (Japanese), each with its flag." width="100%">
</picture>

<p>
  <picture><source media="(prefers-color-scheme: dark)" srcset="assets/pictures/button-install-dark.svg"><img src="assets/pictures/button-install-light.svg" alt="Install markdown-graphics with pip" height="40"></picture>
</p>

No picture paints a background, so each sits on the page like text; slideshows, comparisons and terminals move with
SVG's own animation, which GitHub plays.

## <img src="assets/icons/contribute.svg" height="33" align="absmiddle" alt="">Contribute

Issues and pull requests are welcome. Install it editable, then run the tests:

```bash
pip install -e .
```

```bash
python3 -m unittest discover -s Tests
```

## <img src="assets/icons/license.svg" height="33" align="absmiddle" alt="">License

[MIT](LICENSE)
