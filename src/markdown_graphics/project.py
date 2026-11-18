"""The project the graphics are drawn for: its name, its folders and its own icon.

Start:  imported by the other modules, not started on its own
Needs:  Python 3.13 or newer
Everything comes from markdown-graphics.toml in the current folder; without that file, or for a
setting it leaves out, the defaults below apply. The current folder is the project's root.
Stop is how every module says that nothing can be drawn; the command line shows it in a frame.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# MARK: Settings

SETTINGS_FILE = "markdown-graphics.toml"


class Stop(Exception):
    """Nothing can be drawn: what is wrong, and what to do about it."""

    def __init__(self, problem: str, hint: str) -> None:
        super().__init__(problem)
        self.problem, self.hint = problem, hint


@dataclass(frozen=True)
class Project:
    root: Path
    name: str  # on banners, in their text for screen readers, and in headings of the command
    icon: Path | None = None  # an SVG drawn on banners in the app theme; without one, a tile mark
    assets: Path = Path("assets")  # banners and, in icons/, the section icons
    pictures: Path = Path("docs/pictures")  # one <name>.json per picture
    pictures_out: Path = Path("assets/pictures")  # <name>-light.svg and <name>-dark.svg
    shots: Path = Path("snapshots/current")  # screenshots for slideshows and comparisons
    hand_drawn: frozenset[str] = field(default_factory=frozenset)  # banners never replaced

    def path(self, folder: Path) -> Path:
        """A folder or file from the settings, as a full path below the project's root."""
        return self.root / folder

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()


# MARK: Reading

FOLDERS = ("icon", "assets", "pictures", "pictures_out", "shots")


def load(root: Path | None = None) -> Project:
    """The project in `root` (the current folder by default), with its settings file if any.
    A setting the file does not know is an error, so a typo does not go unnoticed."""
    root = (root or Path.cwd()).resolve()
    settings_file = root / SETTINGS_FILE
    try:
        settings = tomllib.loads(settings_file.read_text()) if settings_file.exists() else {}
    except tomllib.TOMLDecodeError as error:
        raise Stop(f"{SETTINGS_FILE} cannot be read: {error}", "Fix its TOML syntax.") from error
    unknown = set(settings) - {"name", "hand_drawn", *FOLDERS}
    if unknown:
        raise Stop(f"{SETTINGS_FILE}: unknown setting {', '.join(sorted(unknown))}",
                   f"Known: name, hand_drawn, {', '.join(FOLDERS)}")
    texts = {key: value for key, value in settings.items() if key != "hand_drawn"}
    hand_drawn = settings.get("hand_drawn", [])
    if not all(isinstance(value, str) for value in texts.values()) or not (
            isinstance(hand_drawn, list) and all(isinstance(name, str) for name in hand_drawn)):
        raise Stop(f"{SETTINGS_FILE}: every setting is a text in quotes",
                   'hand_drawn is a list of texts, such as hand_drawn = ["footer"]')
    folders = {key: Path(texts[key]) for key in FOLDERS if key in texts}
    return Project(root=root, name=texts.get("name", root.name),
                   hand_drawn=frozenset(hand_drawn), **folders)
