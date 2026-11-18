"""Tests markdown-graphics in a throwaway project folder.

Start:  PYTHONPATH=src python3 -m unittest discover -s Tests
Needs:  Python 3.13 or newer and console-look (pip install -e .)
"""

import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from markdown_graphics import banners, pictures
from markdown_graphics.__main__ import main
from markdown_graphics.project import SETTINGS_FILE, Project, Stop, load

ICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle r="5"/></svg>'
GRID = {"kind": "grid", "columns": 2, "items": [
    {"glyph": "shield", "title": "Private", "text": "Sends nothing."},
    {"glyph": "bolt", "title": "Fast", "text": "Starts at once."}]}


class ProjectFolder(unittest.TestCase):
    """Every test runs in an empty project folder of its own, as its current folder."""

    def setUp(self) -> None:
        self.here = Path.cwd()
        self.root = Path(tempfile.mkdtemp()).resolve()
        os.chdir(self.root)

    def tearDown(self) -> None:
        os.chdir(self.here)
        shutil.rmtree(self.root)

    def settings(self, text: str) -> Project:
        (self.root / SETTINGS_FILE).write_text(text)
        return load()

    def describe(self, name: str, spec: dict) -> None:
        folder = self.root / "docs" / "pictures"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.json").write_text(json.dumps(spec))


class SettingsTests(ProjectFolder):
    def test_defaults_without_a_file(self) -> None:
        project = load()
        self.assertEqual(project.name, self.root.name)
        self.assertEqual(project.assets, Path("assets"))

    def test_a_typo_is_named(self) -> None:
        with self.assertRaises(Stop):
            self.settings('nmae = "Typo"\n')

    def test_a_text_for_a_list_is_named(self) -> None:
        with self.assertRaises(Stop):
            self.settings('hand_drawn = "footer"\n')

    def test_broken_toml_is_named(self) -> None:
        with self.assertRaises(Stop):
            self.settings('name = "unclosed\n')


class BannerTests(ProjectFolder):
    def draw(self, project: Project, theme: str = "app") -> str:
        path = banners.banner(project, "guide", "Guide", "One line below.", "Demo · Docs",
                              overwrite=False, theme_name=theme)
        return path.read_text()

    def test_without_an_icon_a_tile_stands_on_the_left(self) -> None:
        svg = self.draw(self.settings('name = "Demo"\n'))
        self.assertIn('fill="url(#tile-blue)"', svg)
        self.assertIn('aria-label="Demo – Guide. One line below."', svg)

    def test_the_project_icon_is_embedded_scaled(self) -> None:
        (self.root / "icon.svg").write_text(ICON)
        svg = self.draw(self.settings('name = "Demo"\nicon = "icon.svg"\n'))
        self.assertIn('width="168" height="168.0" viewBox="0 0 10 10"><circle r="5"/>', svg)

    def test_an_exported_icon_keeps_apart_from_the_banner(self) -> None:
        (self.root / "icon.svg").write_text(
            '<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
            '<defs><linearGradient id="bg"/></defs><rect fill="url(#bg)"/></svg>')
        svg = self.draw(self.settings('icon = "icon.svg"\n'))
        self.assertEqual(svg.count("<svg"), 2)  # the banner and the icon, nothing more
        self.assertIn('<linearGradient id="icon-bg"/></defs><rect fill="url(#icon-bg)"/>', svg)

    def test_claude_theme_draws_its_footer_too(self) -> None:
        project = self.settings('name = "Demo"\n')
        self.assertIn('data-theme="claude"', self.draw(project, "claude"))
        footer = banners.banner_path(project, banners.CLAUDE_FOOTER)
        self.assertIn("Demo, built with Claude Code", footer.read_text())
        footer.unlink()
        with self.assertRaises(Stop):  # the banner exists; nothing at all is written
            self.draw(project, "claude")
        self.assertFalse(footer.exists())

    def test_existing_and_hand_drawn_banners_are_kept(self) -> None:
        project = self.settings('hand_drawn = ["footer"]\n')
        self.draw(project)
        with self.assertRaises(Stop):
            self.draw(project)
        with self.assertRaises(Stop):
            banners.banner(project, "footer", "T", "S", "E", overwrite=True)

    def test_an_icon_without_view_box_is_named(self) -> None:
        (self.root / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        with self.assertRaises(Stop):
            self.draw(self.settings('icon = "icon.svg"\n'))


class PictureTests(ProjectFolder):
    def test_a_grid_is_drawn_light_and_dark(self) -> None:
        self.describe("promises", GRID)
        project = load()
        drawn = pictures.draw(project, *pictures.descriptions(project, []), project.root)
        self.assertEqual([path.name for path in drawn], ["promises-light.svg", "promises-dark.svg"])

    def test_unknown_kind_and_missing_description_are_named(self) -> None:
        self.describe("odd", {"kind": "pie"})
        project = load()
        with self.assertRaises(Stop):
            pictures.draw(project, *pictures.descriptions(project, ["odd"]), project.root)
        with self.assertRaises(Stop):
            pictures.descriptions(project, ["absent"])

    def test_broken_descriptions_are_named_and_write_nothing(self) -> None:
        broken = {
            "empty": {"kind": "flow", "items": []},
            "no-columns": {**GRID, "columns": 0},
            "no-glyph": {"kind": "grid", "items": [{"title": "A", "text": "B"}]},
        }
        for name, spec in broken.items():
            self.describe(name, spec)
        (self.root / "docs" / "pictures" / "not-json.json").write_text("{kind: grid")
        project = load()
        for description in pictures.descriptions(project, [*broken, "not-json"]):
            with self.subTest(description.name), self.assertRaises(Stop):
                pictures.draw(project, description, project.root)
        self.assertFalse(project.path(project.pictures_out).exists())

    def terminal(self, name: str, **settings) -> list[Path]:
        self.describe(name, {"kind": "terminal", "title": "~", "label": "L",
                             "lines": [["command", "ls"], ["output", "a"]], **settings})
        project = load()
        return pictures.draw(project, *pictures.descriptions(project, [name]), project.root)

    def test_a_terminal_takes_a_width(self) -> None:
        phone = self.terminal("phone", width=400)[0].read_text()
        self.assertIn('width="400" height="132" viewBox="0 0 400 132"', phone)
        self.assertIn('<text x="200" y="25"', phone)
        self.assertIn('width="900" height="132"', self.terminal("wide")[0].read_text())

    def test_a_width_that_is_no_number_or_too_small_is_named(self) -> None:
        for width in ("400", 120):
            with self.subTest(width=width), self.assertRaises(Stop):
                self.terminal("odd", width=width)

    def test_a_missing_screenshot_is_named(self) -> None:
        self.describe("tour", {"kind": "slideshow", "pictures": [
            {"file": "{shots}/overview-{theme}.png", "caption": "Overview", "line": "All"}]})
        project = load()
        with self.assertRaises(Stop):
            pictures.draw(project, *pictures.descriptions(project, []), self.root / "shots")


class CommandLineTests(ProjectFolder):
    def run_quietly(self, *arguments: str) -> int:
        with redirect_stdout(io.StringIO()):
            return main(list(arguments))

    def test_banner_icon_and_pictures(self) -> None:
        self.describe("promises", GRID)
        self.assertEqual(self.run_quietly("banner", "guide", "Guide", "One line below."), 0)
        self.assertEqual(self.run_quietly("icon", "about", "blue", "<circle r='4'/>"), 0)
        self.assertEqual(self.run_quietly("pictures"), 0)
        self.assertTrue((self.root / "assets" / "icons" / "about.svg").exists())

    def test_a_stop_ends_with_status_one(self) -> None:
        self.assertEqual(self.run_quietly("pictures", "absent"), 1)


if __name__ == "__main__":
    unittest.main()
