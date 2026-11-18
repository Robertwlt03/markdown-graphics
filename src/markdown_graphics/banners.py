"""Draws banners and section icons for Markdown files in one shared style.

Start:  markdown-graphics banner (asks for everything), or
        markdown-graphics banner <file name> <title> <subtitle> [--eyebrow <small line>]
        markdown-graphics icon <name> <color> '<svg shapes in a 24-point grid>'
        (--overwrite replaces a file that exists)
Needs:  Python 3.13 or newer
A banner (<assets>/banner-<file name>.svg) shows the project's icon, a small line, the title and a
subtitle; an icon (<assets>/icons/<name>.svg) is a rounded tile in one color with a white glyph.
Asked without texts, the command first offers to replace a banner (picked from a list), then asks
for the file name of a new one, the title and the subtitle.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path

from console_look import ask_choice, ask_text, ask_yes_no, can_ask, heading

from markdown_graphics.project import Project, Stop

# MARK: Settings

FONT = (
    "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', "
    "Helvetica, Arial, sans-serif"
)
# The footer that every banner in the Claude theme draws again; never replaced by hand.
CLAUDE_FOOTER = "claude-footer"
FOOTER_WIDTH, FOOTER_HEIGHT = 480, 120
FOOTER_TILE_LEFT, FOOTER_TILE_TOP, FOOTER_TILE_SIZE = 36, 24, 72
FOOTER_TEXT_LEFT = 130
# The footer's two lines: baseline, size, weight and color.
FOOTER_NAME_LINE = (58, 28, 700, "#141413")
FOOTER_CAPTION_LINE = (86, 16, 400, "#5E5D59")
BANNER_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")  # the <file name> in banner-<file name>.svg
TEXT_ELEMENT = re.compile(r"<text [^>]*>(.*?)</text>")  # a drawn banner's three lines of text
THEME_MARK = re.compile(r'data-theme="(?P<theme>[a-z]+)"')  # the design a banner was drawn in
VIEW_BOX = re.compile(r'viewBox="([^"]+)"')
# An id and every way to point at one: id="x", url(#x), href="#x" and xlink:href="#x".
REFERENCED_ID = re.compile(r'((?<![\w-])id="|url\(#|href="#)([^")]+)')
FILE_NAME_LIMIT = 40
# How many characters of usual text fit between the text's start and the banner's right margin,
# measured in the system font at each line's size and weight.
# ponytail: counts characters, not their width; a line of only wide letters (W, M) may still run
# out, which a look at the drawn banner shows. Measure with the font itself if that happens often.
EYEBROW_LIMIT, TITLE_LIMIT, SUBTITLE_LIMIT = 60, 24, 50

# Top and bottom of each tile gradient, in the spirit of System Settings.
COLORS = {
    "blue": ("#5AA9FF", "#0A6CF0"),
    "sky": ("#62CBFA", "#1A86D9"),
    "indigo": ("#8389FF", "#4B4FD8"),
    "purple": ("#C58BFF", "#8B3FE0"),
    "pink": ("#FF7AA2", "#E0336B"),
    "red": ("#FF6B61", "#D92C20"),
    "orange": ("#FFB340", "#F07800"),
    "brown": ("#E7A764", "#A8641F"),
    "green": ("#5BD27A", "#1E9B45"),
    "teal": ("#56DBBE", "#12957B"),
    "gray": ("#76767F", "#2C2C31"),
    "slate": ("#A2A2AB", "#6A6A74"),
    # Claude's colors (claude.com and its app icon), vivid like Claude's own: for CLAUDE.md.
    "clay": ("#D97757", "#D8653F"),
    "dusk": ("#6FA2DA", "#4A86CC"),
    "mineral": ("#5FA88F", "#3F8A70"),
    "plum": ("#8A84D1", "#6660BE"),
    "ink": ("#4D4C48", "#141413"),
    "kraft": ("#DDA174", "#C9844F"),
    "cactus": ("#E5B84F", "#C9952B"),
    "heather": ("#DD84A6", "#C45A84"),
    "peach": ("#EF9A72", "#E07A4C"),
    "olive": ("#86A05E", "#66843C"),
    "stone": ("#8F8D86", "#5E5D59"),
}

# The banner, in pixels: the mark on the left, the three lines of text to its right.
BANNER_WIDTH, BANNER_HEIGHT = 1280, 300
MARK_SIZE, MARK_LEFT, MARK_TOP = 168, 96, 66
TEXT_LEFT = 320
# Each line of text: where it stands (its baseline), its size and its weight; the theme colors it.
EYEBROW_LINE = (112, 22, 600)
TITLE_LINE = (176, 60, 700)
SUBTITLE_LINE = (224, 28, 400)
# The tile mark, when the project has no icon of its own and in the Claude theme: a terminal
# prompt ">_" in a 24-point grid, drawn as a light stroke on a colored tile. Our own symbol;
# Claude's logo is Anthropic's and is not used here.
TILE_MARK = '<path d="M5 7l5 5-5 5"/><path d="M12.5 17h6.5"/>'
TILE_MARK_UNITS = 24
TILE_MARK_SHARE = 0.56  # how much of the tile the mark fills
TILE_CORNER = 0.225  # the corner radius of a macOS app icon's tile, as a share of its size

# The banner's background and decoration.
BANNER_BACKGROUND = """<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{deep}"/></linearGradient>
<filter id="sh" x="-20%" y="-20%" width="140%" height="150%">
  <feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="{shadow}" flood-opacity=".28"/>
</filter></defs>
<rect {size} rx="32" fill="url(#bg)"/>
<circle cx="1180" cy="30" r="200" fill="{large_circle}" fill-opacity=".10"/>
<circle cx="80" cy="300" r="160" fill="{shadow}" fill-opacity=".06"/>"""

# A section icon: a 45-pixel tile with a faint white edge, the glyph drawn in white on top.
ICON_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="60" height="56"
  viewBox="0 0 60 56" aria-hidden="true">
<defs><linearGradient id="t" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>
</linearGradient></defs>
<rect x="1.5" y="1.5" width="45" height="45" rx="11" fill="url(#t)"/>
<rect x="2" y="2" width="44" height="44" rx="10.5" fill="none" stroke="#fff"
  stroke-opacity=".25"/>
<g transform="translate(12 12)" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"
  stroke-linejoin="round">{glyph}</g>
</svg>
"""


# MARK: Drawing


@dataclass(frozen=True)
class Theme:
    """How a banner looks; the shape stays the same in every theme."""
    light: str  # the background, from the top left
    deep: str  # to the bottom right
    large_circle: str  # the decoration top right
    shadow: str  # the shadow under the mark, and the decoration bottom left
    text_colors: tuple[str, str, str]  # the small line, the title, the subtitle
    mark: Callable[[Project], str]  # what stands on the left


def banner(project: Project, file_name: str, title: str, subtitle: str, eyebrow: str,
           overwrite: bool, theme_name: str = "app") -> Path:
    if file_name in project.hand_drawn | {CLAUDE_FOOTER}:
        raise Stop(f"banner-{file_name}.svg is not drawn by this command",
                   f"Edit it in {project.assets.as_posix()}/ instead.")
    theme = THEMES[theme_name]
    size = f'width="{BANNER_WIDTH}" height="{BANNER_HEIGHT}"'
    theme_mark = "" if theme_name == "app" else f' data-theme="{theme_name}"'
    eyebrow_color, title_color, subtitle_color = theme.text_colors
    svg = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" {size}',
        f'  viewBox="0 0 {BANNER_WIDTH} {BANNER_HEIGHT}" role="img"{theme_mark}',
        f'  aria-label="{escape(f"{project.name} – {title}. {subtitle}")}">',
        BANNER_BACKGROUND.format(size=size, light=theme.light, deep=theme.deep,
                                 large_circle=theme.large_circle, shadow=theme.shadow),
        f'<g filter="url(#sh)">{theme.mark(project)}</g>',
        text_line(EYEBROW_LINE, eyebrow, eyebrow_color),
        text_line(TITLE_LINE, title, title_color),
        text_line(SUBTITLE_LINE, subtitle, subtitle_color),
        "</svg>",
        "",
    ])
    drawn = write(project, banner_path(project, file_name), svg, overwrite)
    if theme_name == "claude":  # only once the banner itself was written
        write(project, banner_path(project, CLAUDE_FOOTER), claude_footer(project), overwrite=True)
    return drawn


def claude_footer(project: Project) -> str:
    """The footer of CLAUDE.md, with the same mark as its banner."""
    size = f'width="{FOOTER_WIDTH}" height="{FOOTER_HEIGHT}"'
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" {size} viewBox="0 0 {FOOTER_WIDTH} '
        f'{FOOTER_HEIGHT}" role="img" '
        f'aria-label="{escape(project.name)}, built with Claude Code">',
        '<defs><linearGradient id="fbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" '
        'stop-color="#FAF9F5"/><stop offset="1" stop-color="#F0EEE6"/></linearGradient></defs>',
        f'<rect {size} rx="24" fill="url(#fbg)"/>',
        tile(FOOTER_TILE_LEFT, FOOTER_TILE_TOP, FOOTER_TILE_SIZE, "clay", "#FAF9F5"),
        footer_text(FOOTER_NAME_LINE, project.name),
        footer_text(FOOTER_CAPTION_LINE, "Built with Claude Code"),
        "</svg>",
        "",
    ])


def footer_text(style: tuple, text: str) -> str:
    baseline, font_size, font_weight, color = style
    return (
        f'<text x="{FOOTER_TEXT_LEFT}" y="{baseline}" font-family="{FONT}" font-size="{font_size}" '
        f'font-weight="{font_weight}" fill="{color}" text-anchor="start">{escape(text)}</text>'
    )


def embedded(path: Path, left: float, top: float, width: float) -> str:
    """Another SVG drawn inside this one at the given width, its height kept in proportion."""
    source = path.read_text().strip()
    view = view_box(path, source)
    # After the <svg> tag itself, so an XML declaration or a comment before it stays out.
    inner = source[source.index(">", source.index("<svg")) + 1:source.rindex("</svg>")]
    # Its ids get the file's name in front, so they cannot meet the ids of the picture around it.
    prefix = re.sub(r"[^A-Za-z0-9_-]", "-", path.stem) + "-"
    inner = REFERENCED_ID.sub(lambda found: found[1] + prefix + found[2], inner)
    return (f'<svg x="{left:g}" y="{top:g}" width="{width:g}" '
            f'height="{svg_height(view, width):.1f}" viewBox="{view}">{inner}</svg>')


def view_box(path: Path, source: str) -> str:
    """The viewBox of an SVG, which scaling it needs."""
    view = VIEW_BOX.search(source)
    if not view:
        raise Stop(f"{path.name} has no viewBox", "Give its <svg> a viewBox to draw it scaled.")
    return view[1]


def svg_height(view_box: str, width: float) -> float:
    _, _, view_width, view_height = map(float, view_box.split())
    return width * view_height / view_width


def app_mark(project: Project) -> str:
    """The project's own icon, or a blue tile with the prompt mark when it has none."""
    if project.icon:
        return embedded(project.path(project.icon), MARK_LEFT, MARK_TOP, MARK_SIZE)
    return tile(MARK_LEFT, MARK_TOP, MARK_SIZE, "blue", "#FFFFFF")


def claude_mark(_: Project) -> str:
    return tile(MARK_LEFT, MARK_TOP, MARK_SIZE, "clay", "#FAF9F5")


def tile(left: float, top: float, size: float, color: str, stroke: str) -> str:
    """A tile in one of COLORS with the prompt mark on it, drawn at any size (banner, footer)."""
    mark_size = size * TILE_MARK_SHARE
    offset = (size - mark_size) / 2
    scale = mark_size / TILE_MARK_UNITS
    top_color, bottom_color = COLORS[color]
    return (
        f'<defs><linearGradient id="tile-{color}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{top_color}"/><stop offset="1" stop-color="{bottom_color}"/>'
        f'</linearGradient></defs>'
        f'<rect x="{left}" y="{top}" width="{size}" height="{size}" rx="{size * TILE_CORNER:.1f}" '
        f'fill="url(#tile-{color})"/>'
        f'<g transform="translate({left + offset:.1f} {top + offset:.1f}) scale({scale:.4f})" '
        f'fill="none" stroke="{stroke}" stroke-width="2.25" stroke-linecap="round" '
        f'stroke-linejoin="round">{TILE_MARK}</g>'
    )


THEMES = {
    "app": Theme("#F7FAFF", "#DCE7FF", "#5C9EFF", "#1F52DB",
                 ("#1F52DB", "#1D1D1F", "#3A3A3C"), app_mark),
    # Claude's ivory, clay and slate (claude.com); the small line in a deeper clay for 4.5:1
    "claude": Theme("#FAF9F5", "#F0EEE6", "#D97757", "#C46849",
                    ("#A85536", "#141413", "#3D3D3A"), claude_mark),
}


def text_line(style: tuple, text: str, color: str) -> str:
    baseline, font_size, font_weight = style
    return (
        f'<text x="{TEXT_LEFT}" y="{baseline}" font-family="{FONT}" text-anchor="start" '
        f'font-size="{font_size}" font-weight="{font_weight}" fill="{color}">{escape(text)}</text>'
    )


def icon(project: Project, name: str, color: str, glyph: str, overwrite: bool) -> Path:
    top, bottom = COLORS[color]
    path = project.path(project.assets) / "icons" / f"{name}.svg"
    return write(project, path, ICON_TEMPLATE.format(top=top, bottom=bottom, glyph=glyph),
                 overwrite)


def write(project: Project, path: Path, svg: str, overwrite: bool) -> Path:
    if path.exists() and not overwrite:
        raise Stop(f"{project.relative(path)} already exists",
                   "Add --overwrite to replace it, or pick it from the list of the banner command.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    return path


def banner_path(project: Project, file_name: str) -> Path:
    return project.path(project.assets) / f"banner-{file_name}.svg"


def default_eyebrow(project: Project) -> str:
    return f"{project.name} · Documentation"


# MARK: Questions


def banner_by_questions(project: Project) -> Path:
    """First whether to replace a banner and which one, then the texts of the banner."""
    heading(f"{project.name} · banner", "Ctrl-C cancels")
    if not can_ask():
        raise Stop("no terminal to ask in", "Name the texts instead: "
                   "markdown-graphics banner <file name> <title> <subtitle>")
    protected = project.hand_drawn | {CLAUDE_FOOTER}
    replaceable = sorted(  # only the banners with this command's three lines of text
        name for path in project.path(project.assets).glob("banner-*.svg")
        if (name := path.stem.removeprefix("banner-")) not in protected
        and len(banner_texts(project, name)) == 3
    )
    if replaceable and ask_yes_no("Replace an existing banner?"):
        file_name = replaceable[ask_choice("Which banner?", banner_list(project, replaceable))]
        eyebrow, title, subtitle = banner_texts(project, file_name)
        theme_name = banner_theme(project, file_name)
    else:
        file_name = new_banner_name(project)
        eyebrow, title, subtitle = default_eyebrow(project), "", ""
        theme_name = "app"
    title = ask_text("Title", f"large line, up to {TITLE_LIMIT} characters", title,
                     too_long(TITLE_LIMIT))
    subtitle = ask_text("Subtitle", f"one sentence below, up to {SUBTITLE_LIMIT} characters",
                        subtitle, too_long(SUBTITLE_LIMIT))
    return banner(project, file_name, title, subtitle, eyebrow, overwrite=True,
                  theme_name=theme_name)


def banner_theme(project: Project, file_name: str) -> str:
    """The theme a banner was drawn in, so replacing it keeps its look."""
    mark = THEME_MARK.search(banner_path(project, file_name).read_text())
    return mark["theme"] if mark else "app"


def banner_list(project: Project, file_names: list[str]) -> list[str]:
    """Each banner as its title and, after it, its file."""
    titles = [banner_texts(project, name)[1] for name in file_names]
    width = max(len(title) for title in titles)
    return [
        f"{title.ljust(width)}  {banner_path(project, name).name}"
        for title, name in zip(titles, file_names, strict=True)
    ]


def banner_texts(project: Project, file_name: str) -> list[str]:
    """The small line, the title and the subtitle of a banner this command drew; another banner
    may hold any number of texts, which is how the list of banners to replace leaves it out."""
    texts = TEXT_ELEMENT.findall(banner_path(project, file_name).read_text())
    return [unescape(text) for text in texts]


def new_banner_name(project: Project) -> str:
    return ask_text(
        "File name", f"{project.assets.as_posix()}/banner-<name>.svg, such as release-notes", "",
        lambda file_name: name_problem(file_name) or exists_problem(project, file_name))


# MARK: Checking the texts
# Each returns what is wrong with a text, or nothing when it fits.


def too_long(limit: int) -> Callable[[str], str]:
    def problem(text: str) -> str:
        if len(text) > limit:
            return f"{len(text)} characters; at most {limit} fit on the banner."
        return ""
    return problem


def name_problem(file_name: str) -> str:
    if not BANNER_NAME.fullmatch(file_name):
        return "Small letters, digits and hyphens only, such as release-notes."
    if len(file_name) > FILE_NAME_LIMIT:
        return f"{len(file_name)} characters; at most {FILE_NAME_LIMIT} for a file name."
    return ""


def exists_problem(project: Project, file_name: str) -> str:
    if file_name in project.hand_drawn | {CLAUDE_FOOTER}:
        return "That name belongs to a banner this command does not draw; choose another."
    if banner_path(project, file_name).exists():
        return "That banner exists; answer y to the first question to replace it."
    return ""

