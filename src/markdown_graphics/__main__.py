"""The command line: markdown-graphics banner, icon and pictures.

Start:  markdown-graphics <command> …, or python3 -m markdown_graphics <command> …
Needs:  Python 3.13 or newer; run it in the project's root, where markdown-graphics.toml lives
"""

import argparse
import sys
from pathlib import Path

from console_look import FAILURE, SUCCESS, frame, heading, note

from markdown_graphics import banners, pictures
from markdown_graphics.project import SETTINGS_FILE, Project, Stop, load

# MARK: Commands


def command_line() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markdown-graphics",
        description=f"Banners, icons and pictures for Markdown files; settings in {SETTINGS_FILE}.")
    commands = parser.add_subparsers(dest="command", required=True)
    banner = commands.add_parser("banner", help="a banner for the top of a Markdown file")
    banner.add_argument("file_name", nargs="?",
                        help="written to <assets>/banner-<file name>.svg; left out, it asks")
    banner.add_argument("title", nargs="?")
    banner.add_argument("subtitle", nargs="?")
    banner.add_argument("--eyebrow", help="the small line above (default: <name> · Documentation)")
    banner.add_argument(
        "--theme", choices=banners.THEMES,
        help="app: blue with the project's icon; claude: Claude's ivory and clay "
             "(default: the banner's own, or app for a new one)")
    icon = commands.add_parser("icon", help="an icon in front of a section heading")
    icon.add_argument("name", help="written to <assets>/icons/<name>.svg")
    icon.add_argument("color", choices=banners.COLORS)
    icon.add_argument("glyph", help="a glyph name the pictures know, such as shield, or white SVG "
                                    "shapes in a 24-point grid")
    for command in (banner, icon):
        command.add_argument("--overwrite", action="store_true", help="replace a file that exists")
    drawn = commands.add_parser("pictures", help="light and dark pictures from descriptions")
    drawn.add_argument("names", nargs="*", help="only these pictures (<pictures>/<name>.json)")
    drawn.add_argument("--shots", type=Path,
                       help="the folder with screenshots for slideshows (default: <shots>)")
    return parser


def drawn_banner(project: Project, parser: argparse.ArgumentParser,
                 arguments: argparse.Namespace) -> Path:
    texts = [arguments.file_name, arguments.title, arguments.subtitle]
    if not any(texts):
        return banners.banner_by_questions(project)
    if not all(texts):
        parser.error("name the file, the title and the subtitle, or none of them to be asked")
    eyebrow = arguments.eyebrow or banners.default_eyebrow(project)
    problems = [
        banners.name_problem(arguments.file_name),
        banners.too_long(banners.EYEBROW_LIMIT)(eyebrow),
        banners.too_long(banners.TITLE_LIMIT)(arguments.title),
        banners.too_long(banners.SUBTITLE_LIMIT)(arguments.subtitle),
    ]
    if problem := next((problem for problem in problems if problem), ""):
        parser.error(problem)
    path = banners.banner_path(project, arguments.file_name)
    heading(f"{project.name} · banner", project.relative(path))
    # Without --theme, a banner drawn again keeps the theme it has, and a new one gets the app's.
    theme_name = arguments.theme or (
        banners.banner_theme(project, arguments.file_name) if path.exists() else "app")
    return banners.banner(project, arguments.file_name, arguments.title, arguments.subtitle,
                          eyebrow, arguments.overwrite, theme_name)


def run(project: Project, parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> None:
    if arguments.command == "pictures":
        out = project.path(project.pictures_out)
        heading(f"{project.name} · pictures", project.relative(out))
        shots = arguments.shots or project.path(project.shots)
        written = [path for description in pictures.descriptions(project, arguments.names)
                   for path in pictures.draw(project, description, shots)]
        frame("Drawn", [f"{len(written)} pictures in {project.relative(out)}"], SUCCESS)
        return
    if arguments.command == "icon":
        heading(f"{project.name} · icon", f"{project.assets.as_posix()}/icons/{arguments.name}.svg")
        drawn = banners.icon(project, arguments.name, arguments.color,
                             pictures.glyph_shapes(arguments.glyph), arguments.overwrite)
    else:
        drawn = drawn_banner(project, parser, arguments)
    details = [project.relative(drawn)]
    guides = project.root.glob("*.md")
    if drawn.parent == project.path(project.assets) and not any(
            drawn.name in guide.read_text() for guide in guides):
        details.append("No Markdown file in the root shows it yet; put it at the top of one.")
    frame("Drawn", details, SUCCESS)


# MARK: Run


def main(arguments: list[str] | None = None) -> int:
    parser = command_line()
    parsed = parser.parse_args(arguments)
    try:
        run(load(), parser, parsed)
    except (KeyboardInterrupt, EOFError):  # Ctrl-C or Ctrl-D while it asks; not a failure
        note("Cancelled, nothing written.")
    except Stop as problem:
        frame("Nothing drawn", [problem.problem, problem.hint], FAILURE)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
