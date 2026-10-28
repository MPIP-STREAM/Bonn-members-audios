#!/usr/bin/env python3
"""Interactive helper to publish name-pronunciation audios.

Walks every audio file in ``to_add/`` and ``to_upload/`` (or the directories
given as arguments) and, for each one:
  1. asks for the member's display name (a sensible default is derived from
     the filename, e.g. ``runda_li.m4a`` or ``Runda Li.m4a`` -> ``Runda Li``);
  2. moves the file into ``audios/``, renamed to ``firstname_lastname.ext``
     (lowercase, ASCII, e.g. ``Hansjörg Menges.mp3`` -> ``hansjoerg_menges.mp3``);
  3. inserts an alphabetically-placed (by first name) card in ``index.html``
     and a row in ``names.md``.

Nothing is staged or committed -- review the changes yourself afterwards.
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
STAGING_DIRS = [REPO / "to_add", REPO / "to_upload"]
AUDIOS = REPO / "audios"
INDEX_HTML = REPO / "index.html"
NAMES_MD = REPO / "names.md"

AUDIO_EXTS = {".ogg", ".mp3", ".m4a", ".mp4", ".aac", ".wav", ".webm", ".oga"}

# Marker that always sits just after the last card in index.html.
GRID_END_MARKER = "<!-- ADD MORE MEMBERS ABOVE THIS LINE -->"
# Line that follows the last table row in names.md.
NAMES_END_MARKER = "> **How to add yourself:**"


def first_name_key(display_name: str) -> str:
    """Sort key: lower-cased first token of the display name."""
    parts = display_name.strip().split()
    return parts[0].lower() if parts else display_name.lower()


def default_display_name(filename_stem: str) -> str:
    """``runda_li`` -> ``Runda Li``."""
    return " ".join(word.capitalize() for word in re.split(r"[_\s]+", filename_stem) if word)


def audio_filename_for(display_name: str, suffix: str) -> str:
    """``Hansjörg Menges`` + ``.MP3`` -> ``hansjoerg_menges.mp3``."""
    text = display_name.lower()
    for umlaut, repl in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(umlaut, repl)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    stem = "_".join(re.findall(r"[a-z0-9]+", text))
    return f"{stem}{suffix.lower()}"


def prompt(text: str, default: str) -> str:
    try:
        answer = input(f"{text} [{default}]: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def ask_yes_no(text: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{text} {suffix}: ").strip().lower()
    except EOFError:
        answer = ""
    if not answer:
        return default
    return answer in ("y", "yes")


def insert_index_card(name: str, audio_filename: str) -> None:
    """Insert a card into index.html before the first card whose first name
    sorts after ``name`` (falling back to the grid-end marker)."""
    lines = INDEX_HTML.read_text(encoding="utf-8").splitlines(keepends=True)
    new_key = first_name_key(name)

    esc = html.escape(name)
    card = (
        f'  <div class="card" data-name="{esc}">\n'
        f'    <span class="name">{esc}</span>\n'
        f'    <button class="play-btn" data-src="audios/{audio_filename}" '
        f'aria-label="Play {esc}"></button>\n'
        f"  </div>\n\n"
    )

    card_open = re.compile(r'<div class="card" data-name="([^"]*)"')
    insert_at = None
    for i, line in enumerate(lines):
        m = card_open.search(line)
        if m:
            # Prefer the visible span name when present on the next line.
            existing = m.group(1)
            if i + 1 < len(lines):
                span = re.search(r'<span class="name">([^<]*)</span>', lines[i + 1])
                if span:
                    existing = span.group(1)
            if first_name_key(html.unescape(existing)) > new_key:
                insert_at = i
                break

    if insert_at is None:
        for i, line in enumerate(lines):
            if GRID_END_MARKER in line:
                insert_at = i
                break

    if insert_at is None:
        raise RuntimeError("Could not find an insertion point in index.html")

    lines.insert(insert_at, card)
    INDEX_HTML.write_text("".join(lines), encoding="utf-8")


def insert_names_row(name: str, audio_filename: str) -> None:
    """Insert a markdown table row before the first row whose first name sorts
    after ``name`` (falling back to the how-to-add marker)."""
    lines = NAMES_MD.read_text(encoding="utf-8").splitlines(keepends=True)
    new_key = first_name_key(name)

    row = f"| {name} | [{name}](audios/{audio_filename}) |\n"

    # A data row looks like "| Something | [..](..) |"; skip header/separator.
    data_row = re.compile(r"^\|\s*([^|]+?)\s*\|.*\|")
    insert_at = None
    seen_separator = False
    for i, line in enumerate(lines):
        if re.match(r"^\|\s*-+", line):
            seen_separator = True
            continue
        if not seen_separator:
            continue
        m = data_row.match(line)
        if m and first_name_key(m.group(1)) > new_key:
            insert_at = i
            break

    if insert_at is None:
        for i, line in enumerate(lines):
            if line.startswith(NAMES_END_MARKER):
                insert_at = i
                break

    if insert_at is None:
        raise RuntimeError("Could not find an insertion point in names.md")

    # Avoid leaving a stray blank line directly before the inserted row.
    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, row)
    NAMES_MD.write_text("".join(lines), encoding="utf-8")


def bump_footer() -> str | None:
    """Bump the patch version and set the 'last updated' date in index.html.

    Returns the new version string, or None if the footer wasn't found.
    """
    text = INDEX_HTML.read_text(encoding="utf-8")
    pattern = re.compile(r"v(\d+)\.(\d+)\.(\d+)\s*&mdash;\s*last updated\s*\d{4}-\d{2}-\d{2}")
    m = pattern.search(text)
    if not m:
        return None

    major, minor, patch = (int(g) for g in m.groups())
    new_version = f"{major}.{minor}.{patch + 1}"
    today = date.today().isoformat()
    replacement = f"v{new_version} &mdash; last updated {today}"
    INDEX_HTML.write_text(text[: m.start()] + replacement + text[m.end():], encoding="utf-8")
    return new_version


def main() -> int:
    if len(sys.argv) > 1:
        staging_dirs = [Path(arg).resolve() for arg in sys.argv[1:]]
    else:
        staging_dirs = STAGING_DIRS
    staging_dirs = [d for d in staging_dirs if d.is_dir()]
    if not staging_dirs:
        print("No staging directory found (looked for to_add/ and to_upload/)", file=sys.stderr)
        return 1
    where = ", ".join(f"{d.name}/" for d in staging_dirs)

    AUDIOS.mkdir(exist_ok=True)

    candidates = sorted(
        p for d in staging_dirs for p in d.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )

    if not candidates:
        print(f"Nothing to do: no audio files in {where}.")
        return 0

    print(f"Found {len(candidates)} audio file(s) in {where}.\n")
    added = 0

    for src in candidates:
        print(f"── {src.name} ──────────────────────────────")
        name = prompt("Display name", default_display_name(src.stem))
        if not name:
            print("  Skipped (empty name).\n")
            continue

        dest = AUDIOS / audio_filename_for(name, src.suffix)
        if dest.exists():
            if not ask_yes_no(f"  audios/{dest.name} already exists. Overwrite?"):
                print("  Skipped.\n")
                continue

        # Move the audio first, then update the text files.
        src.replace(dest)
        insert_index_card(name, dest.name)
        insert_names_row(name, dest.name)

        print(f"  Added '{name}' -> audios/{dest.name}\n")
        added += 1

    print(f"Done. {added} member(s) added.")
    if added:
        new_version = bump_footer()
        if new_version:
            print(f"Footer bumped to v{new_version} (last updated {date.today().isoformat()}).")
        else:
            print("Warning: could not find the footer version line to bump.")
        print("Review with `git status` / `git diff`, then commit when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
