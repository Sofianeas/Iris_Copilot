from pathlib import Path


UI_FILES = [
    "cards.py",
    "badges.py",
    "layout.py",
]


def test_ui_files_exist():
    root = Path("app/ui")

    for file in UI_FILES:
        assert (root / file).exists()