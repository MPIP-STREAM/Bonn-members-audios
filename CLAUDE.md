# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A tiny **static GitHub Pages site** where members of the Bonn group can hear how
each name is pronounced. No build step, no dependencies, no framework — just open
`index.html` in a browser. Live at https://mpip-stream.github.io/Bonn-members-audios/

## Layout

```
audios/         # one audio clip per person, named firstname_lastname.ext
to_add/         # staging area (to_upload/ also works): drop new clips here, then run add_members.py
index.html      # the whole site: HTML + inline CSS + inline JS audio player
names.md        # markdown table mirroring the member list
add_members.py  # interactive helper to publish clips from to_add/ or to_upload/
README.md       # human-facing instructions
```

There are three places a member is represented and they must stay in sync:
1. the audio file in `audios/`
2. a `.card` block inside `#grid` in `index.html`
3. a table row in `names.md`

## Key conventions

- **Ordering is alphabetical by FIRST name** in both `index.html` and `names.md`.
  (The existing data has a few out-of-order spots, e.g. Shengjie before Qiqi —
  don't bother "fixing" those unless asked; just insert new entries in the
  correct first-name position.)
- **Filenames** are `firstname_lastname.ext`, lowercase. Any audio extension
  works — the JS uses an `Audio` element, not `<source>` type hints. Existing
  files mix `.ogg .mp3 .m4a .mp4 .aac`.
- A card block looks like:
  ```html
  <div class="card" data-name="Full Name">
    <span class="name">Full Name</span>
    <button class="play-btn" data-src="audios/firstname_lastname.ext" aria-label="Play Full Name"></button>
  </div>
  ```
  New cards go before the `<!-- ADD MORE MEMBERS ABOVE THIS LINE -->` marker.
- A names.md row looks like: `| Full Name | [Full Name](audios/firstname_lastname.ext) |`
- The footer in `index.html` carries a version + date:
  `vX.Y.Z &mdash; last updated YYYY-MM-DD`. Patch-bump it when adding members.

## The add_members.py workflow (preferred way to add people)

```
python3 add_members.py
```

For every audio file in `to_add/` and `to_upload/` (or directories passed as arguments) it: prompts for a display name (default
derived from the filename), moves the file into `audios/` renamed to `firstname_lastname.ext` (lowercase ASCII, umlauts → ae/oe/ue), inserts an
alphabetically-placed card + names.md row, and patch-bumps the footer
version/date. It leaves all changes **unstaged** for review — it does not
`git add` or commit. Skips non-audio files and asks before overwriting.

Reusable functions in the script: `bump_footer()`, `insert_index_card()`,
`insert_names_row()`, `first_name_key()`, `default_display_name()`.

## Working agreements

- Don't stage or commit unless explicitly asked.
- When adding members manually, update all three locations + the footer.
- This is `main`-branch / PR-merge driven (see README); a GitHub Action
  publishes Pages on merge.
