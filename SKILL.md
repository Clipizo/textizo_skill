---
name: textizo-presets
description: Makes ready-to-use Textizo animated-text presets (.setting files) for DaVinci Resolve's Fusion page from a plain description (for example "a bouncy pink title", "Apple-style reveal", "caption that pops in word by word"). It checks each preset and saves it where the user wants, including Resolve's own Settings folder. Use it whenever the user asks for a Textizo preset, text animation or title look, or for changes to one.
---

# Textizo presets

You make presets for **Textizo**, a text animation node for DaVinci Resolve (Fusion page). A preset is a small `.setting` text file. The user pastes it into Fusion or loads it onto a Textizo node.

## Before you start

- **Read `Textizo AI Guide.md` completely, once per session.** It is the reference for:
  - every control and its units;
  - the timing formula;
  - the shading rules;
  - the house style;
  - how users load presets.

  This file only adds the workflow for agents that can use files.
- **The helper** is `python tools/textizo_preset.py` (use `python3` on Mac and Linux, or `py` on some Windows installs). It needs Python 3 and nothing else. It reads `reference/inputs.json`, the list of Textizo's controls.
- **If Python is not available,** write the preset by hand from the guide's template (example 1), and go through the guide's checklist yourself.

## Workflow

1. **Understand the request.** Ask, in one message and only for what is missing:
   - the text;
   - the style or mood;
   - colours or font (optional);
   - the clip length and frame rate (default 5 s at 24 fps);
   - how many variations.

   Use the house style from guide section 10 unless the user wants something else.
2. **Ask where to save** (once per session; remember the answer). Show the real paths from `python tools/textizo_preset.py where`. The options:
   1. **Resolve's Settings folder** (recommended). Presets there appear in a Textizo node's right-click **Settings** menu, and **Settings > Load…** opens that folder.
      - Windows: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Settings`
      - Mac: `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Settings`
   2. **Downloads/Textizo Presets.** Easy to find. The user loads a preset with Settings > Load…, or drags the file onto the Nodes area.
   3. **A folder the user names.**
   4. **Both 1 and 2.**
3. **Pick a short name.** Presets are named `Textizo-` plus a two-digit number and a capital letter, for example `Textizo-07A`.
   - The number is the look. Get the next free one with `python tools/textizo_preset.py next-name --to resolve` (use the user's folder choice).
   - The letter is a variation of that look. Get the next letter with `next-name --to resolve --variant 7`, which gives `Textizo-07B`.
   - Use no spaces and no descriptive words in the name. Describe the look in your message instead.
4. **Write a spec.** Copy the closest file from `specs/` (one for each preset in `presets/`) to `my-presets/<short name>.json`, then edit it. The format is below.
   - Set `name` to the short name; the file becomes `Textizo-07A.setting`.
   - The specs give timing as `span` + `delay` (frames per letter and the gap between letters). Keep those when you change the text: the tool works out the End Frame and Stagger % for the new text.
   - Use `specs/` or the guide's examples as templates, not the files in `presets/`. Those are full saves from Resolve and contain internal inputs.
5. **Build and check:**
   ```
   python tools/textizo_preset.py build "my-presets/Textizo-07A.json" --frames <clip length in frames>
   ```
   This writes `my-presets/Textizo-07A.setting`. Rebuilding replaces files in `my-presets/` without asking.

   The report lists every row's frames, the time each letter moves, the gap between letters, and the shading layers. It also estimates the layout: line width, frame edges, and word boxes that touch. You cannot see the render, so take its layout warnings seriously.
   - Fix every **ERROR**.
   - Fix every **WARNING** unless the user asked for that look.
   - **NOTES** are house-style hints (guide section 10); follow them unless the request says otherwise.
6. **Install:**
   ```
   python tools/textizo_preset.py install "my-presets/Textizo-07A.setting" --to resolve
   ```
   Use `--to downloads` or `--to "<folder>"` for the other choices. The command refuses to overwrite an existing file; ask the user whether to replace it (`--overwrite`) or use the next free name.
7. **Tell the user:**
   - the preset's short name and what the look is;
   - where the file is;
   - how to use it (guide section 13);
   - that they can type their own text in the Inspector;
   - how to move the exit for a longer clip.

   They have the file, so do not paste the preset code unless they ask for it. You cannot see the animation, so describe it, and never claim you have tested it in Resolve.
8. **Change it on feedback.** A fix to the same preset keeps its name: edit the spec, rebuild, and reinstall with `--overwrite`. When the user wants to keep both versions, give the new one the next letter.

You can also start from an existing preset: `python tools/textizo_preset.py to-spec "<file.setting>" my-presets/Textizo-07A.json`.

## Spec format

```json
{
  "name": "Textizo-07A",
  "text": "NEON\nPOP",
  "font": "Arial Black", "style": "Regular", "size": 2.2,
  "center": [0.5, "auto"], "align": "center",
  "tracking": 0, "line_spacing": 1, "rotation": 0, "alpha": 1,
  "motion_blur": true,
  "in": {
    "opacity":  {"by": "letters", "start": 0, "span": 4,  "delay": 2, "from": 0, "to": 1, "ease": "out_quad"},
    "size":     {"by": "letters", "start": 0, "span": 14, "delay": 2, "from": 0, "to": 1, "ease": "out_elastic"},
    "position": {"by": "letters", "start": 0, "span": 12, "delay": 2, "from": [0, -0.1], "to": [0, 0], "ease": "out_back"}
  },
  "out": {
    "opacity":  {"start": 100, "span": 8, "delay": 1.5, "to": 0, "ease": "in_cubic"},
    "position": {"start": 100, "span": 8, "delay": 1.5, "to": [0, 0.1], "ease": "in_back"}
  },
  "elements": {
    "1": {"color": "#29E0FF"},
    "2": {"appearance": "outline", "color": "#000000", "thickness": 0.0083},
    "3": {"appearance": "normal", "color": "#000000", "offset": [0.0055, -0.011], "softness": 0, "opacity": 0.85}
  }
}
```

**Top level:**

- `name`: the short preset name, for example `Textizo-07A` (`07A` works too); the file becomes `Textizo-07A.setting`.
- `text`, `font`, `style`, `size`: as in guide section 3.
- `center`: `[x, y]`. Setting y to `"auto"` centres the block in a 16:9 frame, using Arial's capital height (close enough for the other safe fonts). For other frame shapes, add `"aspect"` (width / height, for example 0.5625 for 9:16); `check` takes `--aspect` too.
- `align`: `left`, `center` or `right`.
- `tracking`, `line_spacing`, `rotation`, `alpha`.
- `color`: a shortcut for element 1's colour.
- `motion_blur`: `false`, `true`, or `{"shutter", "quality", "bias", "spread"}`.
- `in`, `out`: the animation rows (below).
- `elements`: the shading layers (below).
- `inputs`: optional raw overrides, `{"InputID": number | "text" | [x, y] | {"fuid": "id"}}`. Use only IDs whose `role` is `public` in `reference/inputs.json`.
- `notes`: ignored; use it for your own comments.

**Rows** (the keys of `in` and `out`): `opacity`, `blur`, `position` (written `center` in IDs), `size`, `tracking`, `rotation`, `explosion`. Each row has:

- `by`: `letters` (default), `words` or `lines`.
- `start`: the Start Frame.
- **Either** `span` + `delay` (frames each piece moves, and frames between pieces; the tool works out End Frame and Stagger % from the text) **or** `end` + `stagger`, not both. Prefer `span` + `delay`.
- `from`: In rows only.
- `to`.
- `ease`: one of the ease names in guide section 6.
- Explosion extras: `variance`, `damping`, `spin_x`, `spin_y`, `spin_z` (keep these 0), `pre_roll`, `reverse`.
- Tracking extra: `pivot`, what stays put while the pieces spread or close up: `center` (the middle of each line, the default), `left` (the first letter or word of each line) or `right` (the last).

Rows you leave out are written as off.

**Elements** (`"1"` to `"8"`). Each element can have:

- `enabled`: true by default for listed elements.
- `appearance`: `normal`, `outline`, `border_fill` or `border_stroke`. **Required for elements 2 to 8**, because each starts from its own default; element 4, for example, is a Border Fill box.
- `color`: `[r, g, b]` or `[r, g, b, a]` from 0 to 1, or `"#RRGGBB"`.
- `opacity`, `thickness`.
- `offset`: `[x, y]`.
- `softness`: a number, or `[x, y]`.
- `border_level`: `letters`, `words` or `lines`.
- `extend`: `[x, y]`.
- `round`.
- `gradient`: `{"colors": [c1, c2, ...] or {"0": c, "1": c}, "angle", "span": letters|words|lines|text, "scale", "aspect"}`.

Elements 2 to 8 that you leave out are written as off.

**Each listed element starts from Textizo's own defaults for that element** (guide section 7). For example, element 3 has softness 0.01, so give `softness` and `offset` explicitly.

**Word or line boxes** only follow rows animated at their own level (guide section 7). If letters animate inside a word box, add a `by: "words"` Opacity row on that page, or the box shows before its letters arrive. The checker warns about this.

## Which guide sections you need

When you use the builder, sections 3 to 10 and 13 are the reference. The two full examples (sections 11 and 12) show what the builder writes for you.

## Other commands

```
python tools/textizo_preset.py check "<file.setting>" [--frames N] [--aspect 0.5625]
python tools/textizo_preset.py timing --text "HELLO WORLD" --by letters --span 8 --delay 2
python tools/textizo_preset.py where
python tools/textizo_preset.py next-name --to resolve [--variant 7]
```

## Rules

- **Only write to `my-presets/` and the folder the user chose.** Never delete files. Never overwrite the user's files without asking.
- **Leave the kit unchanged** (`presets/`, `specs/`, `reference/`, `tools/`, the guide, this file) unless the user asks.
- **Use short names:** `Textizo-07A.setting`, with a new number for each look and a new letter for each variation. Never use spaces or descriptive words in the name.
- **Never guess input IDs.** Use the guide, or `reference/inputs.json` with `role: public`.
- **Keep the image size lines.** The builder writes `UseFrameFormatSettings` 1 with `Width` 1920 and `Height` 1080, so the node follows the timeline's resolution; without them a new node is only 320x240.
- **Keep explosion spins at 0.** Animate turning with the Rotation row.
- **If a new preset does not appear in the right-click Settings menu**, tell the user to use Settings > Load… (or restart Resolve).
