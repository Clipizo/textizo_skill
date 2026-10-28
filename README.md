# Textizo AI Kit

Let your AI make **Textizo** presets: animated text for DaVinci Resolve, ready to load. Describe what you want in plain words, for example *"a bouncy pink title"* or *"an Apple-style reveal for 'Coming soon'"*. The AI writes the preset, checks it, and saves it where you want.

This kit is made for Textizo 1.0 (Clipizo).

## Two ways to use it

**1. With any AI chat** (ChatGPT, Claude, Gemini, Copilot):

1. Give the chat the file **`Textizo AI Guide.md`**.
2. Describe the animation you want.
3. Copy the code it gives you, click in Fusion's Nodes area, and press Ctrl+V (Mac: Cmd+V).

The guide's first section explains this step by step.

**2. With an AI agent that can open folders** (Claude Code, OpenAI Codex, Gemini CLI, Cursor, VS Code with Copilot):

1. Open this folder in the agent.
2. Ask for a preset.

The agent reads `AGENTS.md` and `SKILL.md`, asks you a few questions (including where to save), then writes and checks the `.setting` file.

For Claude, you can also upload this folder, zipped, as a custom skill.

## Where presets can go

| Choice | What you get |
|---|---|
| Resolve's Settings folder | The preset is listed in a Textizo node's right-click **Settings** menu, and **Settings > Load…** opens this folder. |
| Downloads/Textizo Presets | Easy to find. Load a preset with Settings > Load…, or drag the file onto the Nodes area. |
| Any folder you name | |

Resolve's Settings folder is in these places:

- **Windows:** `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Settings`
- **Mac:** `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Settings`
- **Linux:** `~/.local/share/DaVinciResolve/Fusion/Settings`

## What is inside

| File or folder | Contents |
|---|---|
| `Textizo AI Guide.md` | Everything an AI needs to know about Textizo's controls, timing and looks. |
| `SKILL.md`, `AGENTS.md` | Instructions for AI agents. `CLAUDE.md` and `GEMINI.md` point to them. |
| `presets/` | 22 ready presets: Apple Reveal, Rise, Drop, Word Lift, Line Rise, Party Pop, Bounce Drop, Zoom Slam, Jelly Wave, Scatter Spin, and Textizo-01A to Textizo-10A. Those are: fiesta snap pops (01A, 01B, 01C), neon glow (02A), word slam (03A), glitch split (04A), spin flip (05A), stamp pill (06A), gold elegance (07A), rainbow wave (08A), typewriter (09A) and word drop (10A). New presets get short names like `Textizo-11A`: a number for each look and a letter for each variation. |
| `specs/` | The same presets as short, editable descriptions. |
| `tools/textizo_preset.py` | Builds, checks and installs presets. Needs Python 3 and nothing else. |
| `reference/inputs.json` | The list of Textizo's controls, which the checker uses. |
| `my-presets/` | Where the agent keeps your presets while it works on them. |

## Using a preset in Resolve

- **As a new node:** paste the code into the Nodes area, or drag the `.setting` file onto it.
- **On an existing Textizo node:** right-click the node and choose **Settings > Load…**.
- **Your own text:** type it in the Inspector afterwards. The animation adapts to any length of text.

## License

Free of charge, under the Clipizo product license in `LICENSE.txt`. Use the kit and its presets in your own projects, personal or commercial, including client work and monetized videos. Please don't re-upload or redistribute the files; to recommend Textizo, link to its page on clipizo.com.
