# Textizo AI Guide

For **Textizo 1.0** (Clipizo) in DaVinci Resolve's Fusion page. Give this file to any AI chat, such as ChatGPT, Claude, Gemini or Copilot, and it can write ready-to-use animated text presets for you. Textizo is available at clipizo.com.

---

## Quick start (for you)

1. **Give this file to your AI.** Open the chat and attach this file (or paste all of its text). Then say what you want. For example: *"Make a Textizo preset: the word SALE pops in letter by letter, red with a black outline, then flies away. My clip is 5 seconds at 30 fps."*
2. **Copy the code.** The AI answers with one block of code. Copy all of it; most chats have a Copy button on the block.
3. **Paste it into Resolve.** On the Fusion page, click an empty spot in the **Nodes** area and press **Ctrl+V** (Mac: **Cmd+V**). A new Textizo node appears with the animation.
4. **Connect it.**
   - For a title on its own, connect the Textizo node to **MediaOut1**.
   - For text over a video clip, add a **Merge** node. Connect MediaIn1 to the Merge's yellow background input, Textizo to its green foreground input, and the Merge to MediaOut1.

   You can type your own text in the Inspector at any time.

**To keep a preset for later**, ask the AI for a `.setting` file, or save the code in a plain text file with the short name the AI gave it, for example `Textizo-01A.setting`. Put that file in Resolve's Settings folder (see section 13). After that, you can apply it to any Textizo node: right-click the node, then choose **Settings > Load…**.

---

## Instructions for the AI

You are making a **preset for the Textizo node**: plain text in Fusion's settings format that the user pastes into Resolve's Fusion page or saves as a `.setting` file. Everything you need is in this guide. **Only use input names (IDs) that appear in this guide, and do not guess others.** A misspelled ID, or an ID in the wrong capitals, is silently ignored by Resolve.

**How to answer:**

1. **Ask only if something essential is missing,** and ask everything in one short message. The things you may need are:
   - the text;
   - the style or mood;
   - colours or font (optional);
   - how long the clip is and its frame rate.

   If the user says "just do it", use these defaults: 5 seconds at 24 fps, white Arial, and a clean blur-in reveal.
2. **Start from the closest example and change it.** Example 1 (section 11) is clean, and example 2 (section 12) is fun. Follow every rule in the checklist below.
3. **Reply in three parts:**
   - one or two sentences describing the animation;
   - the whole preset in **one** code block marked `lua`, with nothing else in it;
   - the usage steps from section 13 (paste, connect, type your text), in 3 or 4 short lines.
4. **Give every preset a short name:** `Textizo-` followed by a two-digit number and a capital letter, for example `Textizo-01A`.
   - Each new look gets the next number (`Textizo-01A`, `Textizo-02A`, …).
   - A variation of a look keeps its number and takes the next letter (`Textizo-01B`, `Textizo-01C`).
   - Use no spaces and no descriptive words in the name; describe the look in your reply instead.
   - If the user mentions presets they already have, continue after their highest number.

   Put the name in the first line of the reply. If you can create files, also offer the preset as a download named after it, for example `Textizo-01A.setting`, in the last line of the reply.
5. **When the user asks for changes,** send the whole preset again, not just the changed lines.

**Checklist (check every item before you answer):**

- [ ] **One node, written exactly like the template.** The file contains exactly one node, `Textizo1 = Fuse.Textizo { Inputs = { ... } }`, inside `{ Tools = ordered() { ... } }`, with the same structure as the examples. It has no comments and no other nodes.
- [ ] **Required inputs:**
  - `StateVersion` is 11 and `InEnable` is 1;
  - `UseFrameFormatSettings` is 1, with `Width` 1920 and `Height` 1080. Without them, a node made from the preset is only 320x240 pixels;
  - `StyledText` holds the text, with `TextEdited` set to 1;
  - `Font`, `Style`, `Size`, `Center`, `Tracking`, `LineSpacing`, `Alignment`, `Rotation`, `Red`, `Green`, `Blue` and `Alpha` are all set.
- [ ] **Every animation row:**
  - All 14 rows have their `...Enable` written, as 0 or 1. There are 7 rows on In and 7 on Out.
  - Each row that is on has all of its fields (section 4).
  - `...CurvePreset` and `...CurvePresetID` name the same ease.
  - Out rows have no `...StartValue`.
- [ ] **Timing:**
  - It is computed with the formula in section 5.
  - The entrance finishes before the exit starts.
  - The exit ends before the last frame of the clip.
- [ ] **Shading:**
  - `ShadingActiveElement` is `element_1`.
  - Element 1 is written twice, as `ShadingProxy...` and as `ShadingElement1...`, with **identical** values.
  - Elements 2 to 8 each have `Enable` set to 0, or their full block.
- [ ] **Explosion:** in every Explosion row, Spin X/Y/Z (`...RotationX`, `...RotationY`, `...Rotation`) are 0. Make letters turn with the Rotation row instead.
- [ ] **Fonts:** use one from the safe list in section 3, unless the user named another font.
- [ ] **Leave these out:** do not write `GlobalIn` or `GlobalOut`.
- [ ] **Name:** the preset has a short name like `Textizo-01A` (step 4 above).

---

## 1. How Textizo works

Textizo is a text generator node. Its Inspector has these pages:

- **Text:** the text, font, size, position and alignment.
- **In:** the entrance animation.
- **Out:** the exit animation.
- **Shading:** the look. It has up to 8 layers, for example fill, outline, shadow and box.
- **Motion Blur.**

The In and Out pages each have **seven animation rows**: Opacity, Blur, Position, Size, Tracking, Rotation and Explosion. A row animates one property of each **letter**, each **word** or each **line**, from a Start Value to an End Value:

- It runs between a **Start Frame** and an **End Frame**.
- Its **Stagger %** spreads the pieces out in time.
- Its **Ease** shapes the motion.

Rows that are on all play at once and add up. For example, Opacity, Blur and Position together give a "fade up into focus".

Text that does not move is cached, so a still hold between the In and Out plays back fast.

## 2. The preset file

A preset is Fusion settings text. Every input is written like this:

```
                <InputID> = Input { Value = <value>, },
```

Value formats:

| Kind | Write it as | Example |
|---|---|---|
| number | plain decimal number (use a dot, not a comma) | `2.4`, `-0.06`, `0` |
| text | in double quotes. Write a new line as `\n`, a quote as `\"`, and a backslash as `\\` | `"Hello\nWorld"` |
| choice ID | `FuID { "id" }` | `FuID { "letters" }` |
| point | `{ x, y }` | `{ 0.5, 0.5 }` |
| gradient | see section 7 | |

The order of the inputs does not matter. Do not write the same input twice.

**Why write everything out:**

- A preset pasted as a new node takes Textizo's defaults for anything you leave out.
- A preset loaded onto an *existing* node can keep that node's old values for anything you leave out.

So always write every row's `Enable`, every element's `Enable`, and the full set of fields for every row and element that is on. Example 1 shows the complete minimum. Copy it as your template.

## 3. Text controls

| ID | What it does | Values |
|---|---|---|
| `StateVersion` | the preset format | always `11` |
| `InEnable` | the node is on | always `1` |
| `StyledText` | the text | `"Hello"`, `"Two\nlines"` |
| `TextEdited` | marks the text as set | always `1` |
| `Font` | font family | `"Arial"` |
| `Style` | font style | `"Regular"`, `"Bold"`, `"Italic"`, `"Bold Italic"`. Arial Black and Impact have only `"Regular"`; Tahoma has `"Regular"` and `"Bold"` |
| `Size` | text size. 1 is the same as a Text+ node at 0.08 | usually 0.6 to 2.8 (see section 9) |
| `Center` | where the **first line's baseline** sits. 0 to 1 across the frame; y goes up (0 is the bottom) | `{ 0.5, 0.5 }` |
| `Alignment` | how lines sit around Center X | `0` left (text starts at Center X), `1` center, `2` right |
| `Tracking` | extra space between letters, in frame widths (0.01 is about 19 px at 1920 wide) | `0`. Tight Apple look: `-0.003` |
| `LineSpacing` | distance between lines (multiplier) | `1` |
| `Rotation` | turns the whole text, in degrees | `0` |
| `Red`, `Green`, `Blue` | tints Shading element 1. **Keep them at 1** and set colours on the Shading elements | `1` |
| `Alpha` | opacity of the whole text, all layers | `1` |
| `UseFrameFormatSettings` | 1 makes the node follow the timeline's resolution (1080p, 4K, vertical) | always `1` |
| `Width`, `Height` | fallback image size, written the way Resolve saves its own nodes | always `1920` and `1080` |

**Fonts that work on both Windows and Mac:** Arial, Arial Black, Verdana, Tahoma, Trebuchet MS, Georgia, Times New Roman, Courier New, Impact and Comic Sans MS.

- If the user names another font, use it, and tell them it must be installed on every computer that opens the project.
- Bold looks: `"Arial"` + `"Bold"`, or `"Arial Black"` + `"Regular"`.

## 4. Animation rows

Each row's ID is the page, then the row, then the field. For example, `In` + `opacity` + `Enable` gives `InopacityEnable`.

- Pages: `In` and `Out`.
- Rows, as written in IDs: `opacity`, `blur`, `center` (shown as "Position" in the Inspector), `size`, `tracking`, `rotation`, `explosion`.

**Fields of a row:**

| Field | Meaning | Write it as |
|---|---|---|
| `Enable` | row on or off | `1` or `0` |
| `Follower` | what moves separately | `FuID { "letters" }`, `FuID { "words" }` or `FuID { "lines" }` |
| `AnimationStart` | Start Frame, counted from the first frame of the clip (0) | whole number |
| `AnimationEnd` | End Frame. The **last** piece finishes exactly here | whole number, after the Start Frame |
| `Stagger` | Stagger % (section 5) | number, 0 or more |
| `StartValue` | value at the start. **In rows only** | see the table below |
| `EndValue` | value at the end | see the table below |
| `CurveMode` | always preset | `FuID { "preset" }` |
| `CurvePreset` | the ease (section 6) | `FuID { "out_cubic" }` |
| `CurvePresetID` | the same ease as text | `"out_cubic"` |

**What the values mean:**

| Row | Value | In default (Start to End) | Notes |
|---|---|---|---|
| `opacity` | 0 (invisible) to 1 | 0 to 1 | |
| `blur` | extra softness: 0.1 is about 11 px of blur at 1080p | 0.1 to 0 | Typical 0.08 to 0.15. Values above about 0.27 add nothing at 1080p. It also blurs outlines and shadows. |
| `center` | **offset** from where the text sits, `{ x, y }`. x is in frame widths and y in frame heights; +y is up | `{ 0, 0 }` to `{ 0, 0 }` | `{ 0, -0.06 }` starts 6% of the frame height lower |
| `size` | scale around each piece's own centre: 1 is normal and 0 is gone | 0 to 1 | 1.1 to 1 gives a gentle settle; 0 to 1 is a pop |
| `tracking` | spreads letters (or words) apart. The value is the step between neighbours, in frame widths. `Pivot` sets what stays put (see "Tracking extra" below) | 0 to 0 | 0.05 to 0 gives letters that gather in |
| `rotation` | degrees around each piece's centre | 0 to 0 | -120 to 0 gives a spin in |
| `explosion` | distance each piece flies, in frame widths, along its own random direction (any direction, up and down included). Each piece goes 0.45 to 1.25 times the value | 0 to 1 | Textizo's default of 0 to 1 blows the letters apart *during* the entrance. For an entrance, use 0.3 to 0.6 down to 0. To fly away on Out, use 1 to 1.5 and fade out with an Opacity row too |

**Out rows (the exit).** An Out row's `EndValue` is where that property ends up, in the same units as on the In page. For example:

- `OutopacityEndValue` 0 fades out.
- `OutcenterEndValue` `{ 0, 0.1 }` rises 10% of the frame height.
- `OutsizeEndValue` 0 shrinks away.

The exit always starts from wherever the In row ended. If that row has no In, it starts from the neutral value: 1 for opacity and size, 0 for the others.

Do **not** write `...StartValue` on Out rows. Textizo ignores it.

**Out defaults:** Start Frame 100 and End Frame 130. The End Values are opacity 0, blur 0.1, size 0 and explosion 1; all others are 0.

**Tracking extra.** A Tracking row can also have `Pivot`: what stays put while the pieces spread or close up.

- `FuID { "center" }`: the middle of each line (the default).
- `FuID { "left" }`: the first letter or word of each line, so the text grows or gathers to the right.
- `FuID { "right" }`: the last one.

For example, `IntrackingPivot = Input { Value = FuID { "left" }, },`. Leave it out for Center. Lines rows don't spread sideways, so Pivot changes nothing there.

**Explosion extras.** An Explosion row that is on also needs these 7 fields:

| Field | Inspector | Use |
|---|---|---|
| `Damping` | Damping (0 to 8) | `0` follows the ease exactly. With 1 to 3 the pieces wait, then rush (in on the In page, away on the Out page) |
| `Speed` | Variance (0 to 1) | random speed per piece. `0.3` is lively |
| `RotationX`, `RotationY`, `Rotation` | Spin X/Y/Z | **always `0`**. Explosion spin jumps when a letter lands or overshoots; turn letters with the Rotation row instead |
| `Offset` | Pre-Roll (frames) | `0`. Above 0, the pieces are already in flight at the Start Frame |
| `Reverse` | Reverse | `0`. With 1, the last piece goes first; on the In page it also swaps Start and End |

A complete Explosion row (this one is an entrance: 7 letters fly in, each for 14 frames, 2 frames apart):

```
                InexplosionEnable = Input { Value = 1, },
                InexplosionFollower = Input { Value = FuID { "letters" }, },
                InexplosionAnimationStart = Input { Value = 0, },
                InexplosionAnimationEnd = Input { Value = 26, },
                InexplosionStagger = Input { Value = 14.3, },
                InexplosionStartValue = Input { Value = 0.4, },
                InexplosionEndValue = Input { Value = 0, },
                InexplosionDamping = Input { Value = 0, },
                InexplosionSpeed = Input { Value = 0.3, },
                InexplosionRotationX = Input { Value = 0, },
                InexplosionRotationY = Input { Value = 0, },
                InexplosionRotation = Input { Value = 0, },
                InexplosionOffset = Input { Value = 0, },
                InexplosionReverse = Input { Value = 0, },
                InexplosionCurveMode = Input { Value = FuID { "preset" }, },
                InexplosionCurvePreset = Input { Value = FuID { "out_back" }, },
                InexplosionCurvePresetID = Input { Value = "out_back", },
```

An Out Explosion row uses the same 17 inputs with `Out` instead of `In` (`OutexplosionEnable`, `OutexplosionDamping`, `OutexplosionSpeed`, …), minus `OutexplosionStartValue`.

**Never write any other row input** (apart from a Tracking row's `Pivot`). The hidden legacy inputs and the curve inputs are not needed.

## 5. Timing

Frames count from the clip's first frame (frame 0). A row fits completely between its Start Frame and End Frame: the first piece starts at the Start Frame, and the last piece lands exactly on the End Frame.

**Stagger %** says how far one piece is into its own move when the next one starts:

- 0: all pieces move together.
- 50: the next piece starts halfway.
- 100: one piece after another.
- Above 100: gaps between pieces.

**Design with per-piece numbers.** Choose S, how many frames each piece moves, and D, how many frames apart the pieces start. N is the number of pieces in that row. Then:

```
End Frame = Start Frame + S + D x (N - 1)      (round to a whole frame)
Stagger % = 100 x D / S                        (use 0 when N is 1)
```

**Counting N:**

- **letters:** every character except spaces, tabs and line breaks. Punctuation counts.
- **words:** pieces separated by spaces.
- **lines:** lines that are not empty.

**Example.** For "HELLO" (N = 5) with each letter moving 8 frames, 2 frames apart: End Frame = 0 + 8 + 2 x 4 = 16, and Stagger % = 25.

Stagger % can have decimals (for example 14.3); one decimal is enough.

**Frame rate.** Numbers in this guide assume 24 fps. At other rates, multiply every frame count, S and D included, by fps / 24: 1.25 at 30 fps, 2.5 at 60 fps. 25 fps is about the same as 24.

**Clip length.** End the exit a few frames before the clip ends:

```
last frame      = seconds x fps - 1
Out End Frame   = last frame - about 5
Out Start Frame = Out End Frame - (S + D x (N - 1))
```

For example, a 5-second clip at 24 fps has frames 0 to 119, so the exit starts around 100 and ends around 112 to 116. If the user changes the clip length later, they move every Out row's Start and End Frame by the same amount.

All rows of one page usually start on the same frame. Give rows slightly different S values to layer them, for example opacity 10 frames, blur 14 and position 14.

## 6. Eases

The ease IDs are:

- `linear`
- `in_`, `out_` or `in_out_` followed by one of: `quad`, `cubic`, `quart`, `quint`, `sine`, `expo`, `circ`, `back`, `elastic`, `bounce`.

For example: `out_cubic`, `in_back`, `in_out_sine`.

| Use | Good eases |
|---|---|
| entrances: fast start, soft landing | `out_cubic`, `out_quart`, `out_expo` |
| a little overshoot | `out_back` |
| wobble | `out_elastic` (pops, Size or Rotation) |
| drop and bounce | `out_bounce` (a Position drop) |
| exits: slow start, fast end | `in_quad`, `in_cubic`, `in_back` (winds up first) |
| fades | `in_out_sine`, `out_quad` |

## 7. Look: shading elements

Shading has **8 layers (elements)**:

- Element 1 is drawn on top, and higher numbers are drawn behind it.
- Element 1 is the text fill.
- Each element has an **Appearance**: `0` Normal (filled letters), `1` Outline, `2` Border Fill (a box behind each letter, word or line) or `3` Border Stroke (the outline of that box).

**The selected-element rule (important).** `ShadingActiveElement` chooses which element the Shading page shows. Textizo draws that element from the visible `ShadingProxy...` controls. So:

- always write `ShadingActiveElement = Input { Value = FuID { "element_1" }, },`;
- write **element 1 twice**, once as `ShadingProxy<Field>` and once as `ShadingElement1<Field>`, with identical values.

Elements 2 to 8 are written once, as `ShadingElement<N><Field>`. For an element that is not used, write only its `Enable` as 0.

**Element fields (write all 24 for every element that is on):**

| Field | Meaning |
|---|---|
| `Enable` | 1 on, 0 off |
| `Appearance` | 0 Normal, 1 Outline, 2 Border Fill, 3 Border Stroke |
| `Opacity` | 0 to 1 |
| `Thickness` | outline width in frame widths (0.004 is about 8 px at 1920 wide). The outline is centred on the letter edge, so half of it lies outside the letter. It does **not** follow Size: use about 0.00375 x Size for a bold sticker outline |
| `Offset` | `{ x, y }` shift: x in frame widths, y in frame heights, +y up. Hard shadow: about `{ 0.0025 x Size, -0.005 x Size }` |
| `SoftnessX`, `SoftnessY` | blur of this layer: 0.05 is about 5 px at 1080p. The effect stops growing at about 0.13; for a wider glow, see the recipes |
| `BorderLevel` | the box is around each 0 letter, 1 word or 2 line |
| `BorderExtendX`, `BorderExtendY` | box padding on each side, in frame widths (0.005 is about 10 px at 1920). Both are in frame widths |
| `BorderRound` | box corner radius, in frame widths |
| `ColorMode` | 0 solid colour, 1 gradient |
| `Red`, `Green`, `Blue`, `Alpha` | colour, 0 to 1 each (for #FF3D8B: 1, 0.24, 0.545) |
| `EndRed`, `EndGreen`, `EndBlue`, `EndAlpha` | "Color 2". Keep 1, or set the gradient's last colour |
| `GradientAngle` | gradient direction in degrees: 0 bottom to top, -90 left to right, 90 right to left, 180 top to bottom |
| `MappingLevel` | the gradient spans each 0 letter, 1 word, 2 line or 3 whole text |
| `MappingSize` | gradient length relative to that span. Default 1.5; 1 reaches the edges |
| `MappingAspect` | vertical stretch of the gradient (default 1) |

**Defaults, in case you leave a field out:**

- All elements: opacity 1, thickness 0.02, offset `{ 0, 0 }`, softness 0, border level 0, extend 0, round 0, solid colour, gradient angle 0, mapping size 1.5, aspect 1, mapping level 0, Color 2 white.
- Except:
  - element 1 is on and white;
  - element 2 is an Outline, red (1, 0, 0), thickness 0.004;
  - element 3 is black with softness 0.01;
  - element 4 is a Border Fill, blue (0, 0, 1), extend 0.02.
- Elements 2 to 8 are off by default.

**Recipes:**

- **Sticker:**
  - element 1: bright fill;
  - element 2: Outline, black, thickness 0.00375 x Size;
  - element 3: Normal, black, offset `{ 0.0025 x Size, -0.005 x Size }`, softness 0, opacity 0.85.
- **Soft shadow:** element 3 Normal, black, offset `{ 0.002 x Size, -0.004 x Size }`, softness 0.05, opacity 0.6. With an outline on element 2, add half the outline thickness to the offset so the shadow still shows.
- **Glow:** element 3 Normal, in the fill colour or a brighter one, offset `{ 0, 0 }`, softness 0.08 to 0.12, opacity 0.8.
  - For a wider glow, add element 4 as an **Outline** (Appearance 1) in the same colour, Thickness 0.01 to 0.02, softness 0.13, opacity 0.5. Softness alone stops growing at about 0.13, and the outline makes the glowing shape bigger.
  - Always give element 4 an Appearance: it starts as a Border Fill box.
- **Boxes need room.** Measure box sizes in **em = 0.064 x Size** (frame widths). Padding under about 0.2 em looks cramped, and a round under about 0.15 em looks like a square corner.
- **Caption pill behind the line** (best for lower thirds and calls to action such as "Subscribe for more"):
  - element 2 Border Fill, `BorderLevel` 2, extend about 0.6 em / 0.28 em;
  - round 1 em or more, for round ends (Textizo limits the rounding to half the box height);
  - optional shadow: element 3, the same box in black, offset `{ 0.002, -0.006 }`, softness 0.05, opacity 0.45;
  - animate the pill with an In Size row by `lines` (0 to 1, `out_back`, S 12), and the words with Opacity and Position rows by `words` that start about 4 frames later.

  Example at Size 0.8 (em = 0.0512): extend `0.031` / `0.0143`, round `0.05`.
- **Word chips** (one box per word): a single space between words leaves room for only about 0.1 em of padding, so the boxes look cramped and almost touch. Put 2 or 3 spaces between the words in the text (`"Subscribe   for   more"`), then use extend about 0.3 em / 0.22 em and round 1 em. Animate by `words`.
- **Dark plate behind a title:** the pill in a dark colour at opacity 0.7, with extend about 0.8 em / 0.4 em. For a full-frame dark background, the user adds a Background node in Fusion and merges Textizo over it. Textizo itself renders on a transparent background.

**How boxes behave** (Border Fill and Border Stroke):

- **What they follow.** A box follows only the rows animated at its own level or above:
  - a word box follows `words` and `lines` rows;
  - a line box follows `lines` rows;
  - a letter box follows everything.

  So if the letters animate by `letters` inside word boxes, the boxes are already on screen before their letters arrive. Add an In (and Out) Opacity row by `words`, or animate everything by `words`.
- **Size.** Every box is the font's full line height (the same for every word, with or without ascenders) plus its extend. Its width runs from the first to the last letter of the word or line.
- **Neighbours.** Neighbouring word boxes touch once `BorderExtendX` reaches half the gap between the words. One space is only about 0.28 em, so word boxes need 2 or 3 spaces between the words (see Word chips).
- **Gradient fill (on element 1):**
  - set `ColorMode` to 1 and `GradientAngle` to -90;
  - set `MappingLevel` to 3 (whole text) and `MappingSize` to 1;
  - set Color and Color 2 to the first and last colours;
  - add the gradient itself, on both `ShadingProxyGradient` and `ShadingElement1Gradient`:

```
                ShadingElement1Gradient = Input {
                    Value = Gradient {
                        Colors = {
                            [0] = { 1, 0.24, 0.55, 1 },
                            [1] = { 0.2, 0.4, 1, 1 }
                        }
                    },
                },
```

  Positions go from 0 to 1, and each colour is `{ r, g, b, a }`. You can add more stops, such as `[0.5] = ...`.

  Gradients render more slowly than solid colours, so use them for short words.

## 8. Motion blur

| ID | Use |
|---|---|
| `MotionBlurEnable` | `1` for fast, big moves (pops, drops, spins). `0` for calm fades |
| `MotionBlurShutterAngle` | `180` |
| `MotionBlurSamples` | Quality, 1 to 10. Use `2`; higher looks smoother but renders slower |
| `MotionBlurBias` | `0` |
| `MotionBlurSampleSpread` | `1` |

When `MotionBlurEnable` is 1, also write the other four.

## 9. Size and placement

**Size.**

- Size 1 is the same as Text+ at 0.08.
- Capital letters are about **0.08 x Size of the frame height** (in 16:9). Size 1 gives capitals about 88 px tall at 1080p.

**Width.** Estimate each line's width as a fraction of the frame width:

1. Add up its characters in ems. Spaces count.
   - narrow (i, j, l, t, f, r, I, space, and . , ! ' : ;): 0.28
   - most lower-case: 0.55
   - most capitals and digits: 0.67
   - wide (m, w, M, W, @): 0.9
2. Multiply by the font factor:
   - Arial 1; Arial Bold 1.07; Arial Black 1.2
   - Verdana 1.17; Tahoma 1; Trebuchet MS 0.98; Georgia 1.05
   - Times New Roman 0.88; Impact 0.85; Comic Sans MS 1.05
   - Courier New: every character is 0.6, with no factor
3. Multiply by 0.064 x Size.

Keep every line under about 0.85 of the frame width. For example:

- "TEXTIZO!" in Arial Black is about 4.5 ems x 1.2 x 0.064 x 2.4 = 0.83, so Size 2.4 fits.
- "Designed to move" in Arial Bold is about 8.1 x 1.07 x 0.064 x 1.5 = 0.83, so Size 1.5.
- A 30-character sentence: about Size 0.8, or split the text into two lines.

**Position.** `Center` is the **baseline of the first line** (where the letters stand), not the middle of the text block.

- At `{ 0.5, 0.5 }`, one line sits a little above the middle. That often looks fine for big titles.
- To centre a block exactly in a 16:9 frame:

```
Center Y = 0.5 - 0.04 x Size + 0.065 x Size x LineSpacing x (lines - 1)
```

  For example: Size 2 with one line gives 0.42; Size 2 with two lines gives 0.55.

- For vertical 9:16 video, multiply the Size terms by 0.32.
- Lower third: Center Y about 0.15 to 0.2.
- Keep text inside the middle 90% of the frame.

## 10. What looks good

These are the house style that Textizo's own presets follow.

**Fast and crisp.**

- Entrances: about 15 to 26 frames in total at 24 fps.
- Gap between letters: about 1.5 to 2 frames.
- Each letter moves for 6 to 14 frames.
- Exits: 12 to 16 frames.

**Move only during In and Out.** The hold in between should stay perfectly still, with no slow drifts or constant zooms. It looks calmer and plays back smoothly.

**Short moves:**

- position offsets of 0.04 to 0.12 of the frame height;
- size 1.1 to 1 for a settle, or 0 to 1 for a pop;
- rotation of 15 to 30 degrees for a tilt, or 120 to 360 for a spin.

**Premium reveals.** Combine opacity 0 to 1, blur 0.1–0.12 to 0, and a small rise or settle. White Arial Bold with `Tracking` -0.003 gives an Apple-like look.

**Fun.** Use the sticker look (a bright Arial Black fill, a black outline and a hard shadow). Pair it with `out_elastic` or `out_back` pops, the Rotation row, and motion blur on. Fun pops can use up to 6 rows per page, as example 2 does; clean looks need only 3 or 4.

**Calm and elegant** (weddings, documentaries, luxury). Roughly double the timings:

- letters move for 20 to 28 frames, 3 to 4 frames apart;
- the entrance takes up to about 2 seconds;
- exits run 14 to 16 frames per letter;
- use soft eases (`in_out_sine`, `out_cubic`) and no overshoot;
- keep moves small (0.03 to 0.04) and motion blur off;
- a serif font such as Georgia, in a warm colour, suits this look.

**Avoid:**

- long sideways slides;
- linear moves on positions;
- more than about 6 rows per page;
- text bigger than the frame.

**Ideas** (all S and D values are per letter or per word):

| Look | In rows | Out rows |
|---|---|---|
| Blur reveal | opacity 0 to 1 (S 10, `in_out_sine`); blur 0.12 to 0 (S 14, `out_cubic`); size 1.1 to 1 (S 13, `out_quart`). D 2 | opacity to 0 (`in_out_sine`), blur to 0.12 and size to 0.95 (`in_quad`); S 5, D 1.2 |
| Rise | as Blur reveal, plus position `{ 0, -0.05 }` to `{ 0, 0 }` (S 14, `out_quart`) | position to `{ 0, 0.04 }`, opacity to 0 (S 6, D 1.2, `in_quad`) |
| Elegant fade-up | opacity 0 to 1 (S 20, `in_out_sine`); blur 0.1 to 0 (S 24, `out_cubic`); position `{ 0, -0.04 }` to `{ 0, 0 }` (S 28, `out_cubic`). D 4 | opacity to 0 (S 14, `in_out_sine`); blur to 0.1 and position to `{ 0, 0.03 }` (S 16, `in_quad`); D 2 |
| Drop and bounce | opacity 0 to 1 (S 4); position `{ 0, 0.45 }` to `{ 0, 0 }` (S 12, `out_bounce`); rotation -25 to 0 (S 14, `out_elastic`) | position to `{ 0, 0.7 }`, rotation to 120, opacity to 0 (S 7, `in_back`) |
| Zoom slam | opacity (S 4); blur 0.2 to 0 (S 9); size 4 to 1 (S 10, `out_back`); rotation 25 to 0 (S 10, `out_back`) | size to 3.5, blur to 0.2, opacity to 0 (S 8, `in_cubic`) |
| Jelly | opacity (S 4); position `{ 0, -0.22 }` to `{ 0, 0 }`, size 0.3 to 1, rotation 20 to 0 (S 16, `out_elastic`) | position to `{ 0, -0.7 }`, rotation to -60, opacity to 0 (S 10, `in_quad`) |
| Scatter | opacity (S 4); blur 0.12 to 0; explosion 0.4 to 0 (S 14, `out_back`, Variance (`...Speed`) 0.3); rotation -360 to 0 and size 0.4 to 1 (S 14) | explosion to 0.5, rotation to 360, opacity to 0, blur to 0.12 (S 10, `in_cubic`) |
| Word lift | by `words`: opacity, blur 0.1 to 0, position `{ 0, -0.06 }` to `{ 0, 0 }` (S 14, D 4) | by `words`: opacity to 0, position to `{ 0, 0.05 }` (S 8, D 2) |
| Line rise | by `lines`, as Word lift with D 6 | by `lines` |
| Fiesta snap (a favourite) | sticker look; every letter row in one window (frames 0 to 24) with Stagger above 100%, so the letters pop in one after another, each in about 1.5 frames with short pauses between them: opacity (`out_quad`), blur 0.12 to 0 (`out_cubic`), position `{ 0, -0.12 }` to `{ 0, 0 }` (`out_back`), size 0 to 1 (`out_elastic`), rotation -120 to 0 (`out_back`); plus tracking 0.05 to 0 over frames 0 to 18 with Stagger 0, so the line tightens as it fills. Motion blur on | opacity, blur to 0.1, position to `{ 0, 0.1 }`, size to 0, rotation to 180 (S 6, D 1, `in_back` / `in_cubic`) |
| Neon glow | letters: opacity (S 2, `out_quad`), blur 0.2 to 0 (S 7, `out_cubic`), size 1.35 to 1 (S 9, `out_cubic`), D 2. Near-white fill; element 3 Normal cyan, softness 0.08; element 4 Outline cyan, Thickness 0.014, softness 0.13, opacity 0.6. Motion blur off | opacity to 0 and blur to 0.2 (S 5, D 1, `in_quad`) |
| Glitch split | letters: opacity (S 2), explosion 0.12 to 0 (S 10, `out_expo`, Variance 0.8), blur 0.15 to 0 (S 8); D 1.5. White fill; element 3 Normal cyan at offset `{ -0.004, 0 }` and element 4 Normal magenta at `{ 0.004, 0 }`, opacity 0.85 | explosion to 0.25 (`in_expo`), opacity to 0, blur to 0.15 (S 8, D 1) |
| Word slam | by `words`: opacity (S 2), size 4 to 1 (S 8, `out_back`), blur 0.2 to 0 (S 6); D 6. Impact, sticker outline and shadow | by `words`: size to 3.5 (`in_cubic`), blur to 0.2, opacity to 0 (S 7, D 3) |
| Spin flip | letters: opacity (S 3), rotation -360 to 0 (S 16, `out_back`), size 0 to 1 (S 14, `out_back`); D 2. Sticker look | rotation to 360 and size to 0 (S 10, D 1.5, `in_back`) |
| Stamp pill | by `lines`: opacity (frames 0 to 3), size 3 to 1 (0 to 9, `out_back`), blur 0.2 to 0 (0 to 7). The text on a pill (section 7) with a shadow pill; Text page `Rotation` -6 for a tilt | by `lines`: size and opacity to 0 (frames 105 to 114, `in_back` / `in_quad`) |
| Rainbow wave | letters: opacity (S 3), position `{ 0, -0.15 }` to `{ 0, 0 }` (S 14, `out_elastic`), size 0.5 to 1 (S 12, `out_back`); D 2. Element 1 rainbow gradient across the text (6 stops, angle -90, span text, scale 1), black outline, hard shadow | position to `{ 0, 0.15 }` (`in_back`) and opacity to 0 (S 8, D 1.5) |
| Typewriter | letters: opacity (S 2, `linear`) and blur 0.06 to 0 (S 3); D 2.5. Courier New Bold, light fill, soft shadow, no motion | opacity to 0 (S 4, D 0.8, `in_quad`) |
| Word drop | by `words`: opacity (S 3), position `{ 0, 0.5 }` to `{ 0, 0 }` (S 16, `out_bounce`), rotation -8 to 0 (S 16, `out_elastic`); D 6. Sticker look | by `words`: position to `{ 0, -0.6 }` (`in_back`), opacity to 0 (S 9, D 2) |
| Caption pill | size by `lines` 0 to 1 (S 12, `out_back`); opacity by `words` (start 4, S 5, D 4); position by `words` `{ 0, -0.02 }` to `{ 0, 0 }` (start 4, S 10, D 4, `out_cubic`). Pill on element 2 (see section 7) | size and opacity by `lines` to 0 (S 9, `in_back` / `in_quad`) |

## 11. Example 1: Apple Reveal (clean)

White Arial Bold. Each letter fades in, comes into focus, and settles from 110% size, with 2 frames between letters. The text holds still, then blurs away quickly from frame 100.

**Use this as your template.** It contains every input a preset needs: every row and element `Enable`, element 1 written twice, and the text controls.

<!-- example: Textizo - Apple Reveal -->
```lua
{
	Tools = ordered() {
		Textizo1 = Fuse.Textizo {
			Inputs = {
				StateVersion = Input { Value = 11, },
				InEnable = Input { Value = 1, },
				Width = Input { Value = 1920, },
				Height = Input { Value = 1080, },
				UseFrameFormatSettings = Input { Value = 1, },
				StyledText = Input { Value = "Textizo", },
				TextEdited = Input { Value = 1, },
				Font = Input { Value = "Arial", },
				Style = Input { Value = "Bold", },
				Size = Input { Value = 2.4, },
				Center = Input { Value = { 0.5, 0.5 }, },
				Tracking = Input { Value = -0.003, },
				LineSpacing = Input { Value = 1, },
				Alignment = Input { Value = 1, },
				Rotation = Input { Value = 0, },
				Red = Input { Value = 1, },
				Green = Input { Value = 1, },
				Blue = Input { Value = 1, },
				Alpha = Input { Value = 1, },
				InopacityEnable = Input { Value = 1, },
				InopacityFollower = Input { Value = FuID { "letters" }, },
				InopacityAnimationStart = Input { Value = 0, },
				InopacityAnimationEnd = Input { Value = 22, },
				InopacityStagger = Input { Value = 20, },
				InopacityStartValue = Input { Value = 0, },
				InopacityEndValue = Input { Value = 1, },
				InopacityCurveMode = Input { Value = FuID { "preset" }, },
				InopacityCurvePreset = Input { Value = FuID { "in_out_sine" }, },
				InopacityCurvePresetID = Input { Value = "in_out_sine", },
				InblurEnable = Input { Value = 1, },
				InblurFollower = Input { Value = FuID { "letters" }, },
				InblurAnimationStart = Input { Value = 0, },
				InblurAnimationEnd = Input { Value = 26, },
				InblurStagger = Input { Value = 15, },
				InblurStartValue = Input { Value = 0.12, },
				InblurEndValue = Input { Value = 0, },
				InblurCurveMode = Input { Value = FuID { "preset" }, },
				InblurCurvePreset = Input { Value = FuID { "out_cubic" }, },
				InblurCurvePresetID = Input { Value = "out_cubic", },
				IncenterEnable = Input { Value = 0, },
				InsizeEnable = Input { Value = 1, },
				InsizeFollower = Input { Value = FuID { "letters" }, },
				InsizeAnimationStart = Input { Value = 0, },
				InsizeAnimationEnd = Input { Value = 25, },
				InsizeStagger = Input { Value = 15, },
				InsizeStartValue = Input { Value = 1.1, },
				InsizeEndValue = Input { Value = 1, },
				InsizeCurveMode = Input { Value = FuID { "preset" }, },
				InsizeCurvePreset = Input { Value = FuID { "out_quart" }, },
				InsizeCurvePresetID = Input { Value = "out_quart", },
				IntrackingEnable = Input { Value = 0, },
				InrotationEnable = Input { Value = 0, },
				InexplosionEnable = Input { Value = 0, },
				OutopacityEnable = Input { Value = 1, },
				OutopacityFollower = Input { Value = FuID { "letters" }, },
				OutopacityAnimationStart = Input { Value = 100, },
				OutopacityAnimationEnd = Input { Value = 112, },
				OutopacityStagger = Input { Value = 25, },
				OutopacityEndValue = Input { Value = 0, },
				OutopacityCurveMode = Input { Value = FuID { "preset" }, },
				OutopacityCurvePreset = Input { Value = FuID { "in_out_sine" }, },
				OutopacityCurvePresetID = Input { Value = "in_out_sine", },
				OutblurEnable = Input { Value = 1, },
				OutblurFollower = Input { Value = FuID { "letters" }, },
				OutblurAnimationStart = Input { Value = 100, },
				OutblurAnimationEnd = Input { Value = 112, },
				OutblurStagger = Input { Value = 25, },
				OutblurEndValue = Input { Value = 0.12, },
				OutblurCurveMode = Input { Value = FuID { "preset" }, },
				OutblurCurvePreset = Input { Value = FuID { "in_quad" }, },
				OutblurCurvePresetID = Input { Value = "in_quad", },
				OutcenterEnable = Input { Value = 0, },
				OutsizeEnable = Input { Value = 1, },
				OutsizeFollower = Input { Value = FuID { "letters" }, },
				OutsizeAnimationStart = Input { Value = 100, },
				OutsizeAnimationEnd = Input { Value = 112, },
				OutsizeStagger = Input { Value = 25, },
				OutsizeEndValue = Input { Value = 0.95, },
				OutsizeCurveMode = Input { Value = FuID { "preset" }, },
				OutsizeCurvePreset = Input { Value = FuID { "in_quad" }, },
				OutsizeCurvePresetID = Input { Value = "in_quad", },
				OuttrackingEnable = Input { Value = 0, },
				OutrotationEnable = Input { Value = 0, },
				OutexplosionEnable = Input { Value = 0, },
				ShadingActiveElement = Input { Value = FuID { "element_1" }, },
				ShadingProxyEnable = Input { Value = 1, },
				ShadingProxyAppearance = Input { Value = 0, },
				ShadingProxyOpacity = Input { Value = 1, },
				ShadingProxyThickness = Input { Value = 0.02, },
				ShadingProxyOffset = Input { Value = { 0, 0 }, },
				ShadingProxySoftnessX = Input { Value = 0, },
				ShadingProxySoftnessY = Input { Value = 0, },
				ShadingProxyBorderLevel = Input { Value = 0, },
				ShadingProxyBorderExtendX = Input { Value = 0, },
				ShadingProxyBorderExtendY = Input { Value = 0, },
				ShadingProxyBorderRound = Input { Value = 0, },
				ShadingProxyColorMode = Input { Value = 0, },
				ShadingProxyGradientAngle = Input { Value = 0, },
				ShadingProxyMappingSize = Input { Value = 1.5, },
				ShadingProxyMappingAspect = Input { Value = 1, },
				ShadingProxyMappingLevel = Input { Value = 0, },
				ShadingProxyRed = Input { Value = 1, },
				ShadingProxyGreen = Input { Value = 1, },
				ShadingProxyBlue = Input { Value = 1, },
				ShadingProxyAlpha = Input { Value = 1, },
				ShadingProxyEndRed = Input { Value = 1, },
				ShadingProxyEndGreen = Input { Value = 1, },
				ShadingProxyEndBlue = Input { Value = 1, },
				ShadingProxyEndAlpha = Input { Value = 1, },
				ShadingElement1Enable = Input { Value = 1, },
				ShadingElement1Appearance = Input { Value = 0, },
				ShadingElement1Opacity = Input { Value = 1, },
				ShadingElement1Thickness = Input { Value = 0.02, },
				ShadingElement1Offset = Input { Value = { 0, 0 }, },
				ShadingElement1SoftnessX = Input { Value = 0, },
				ShadingElement1SoftnessY = Input { Value = 0, },
				ShadingElement1BorderLevel = Input { Value = 0, },
				ShadingElement1BorderExtendX = Input { Value = 0, },
				ShadingElement1BorderExtendY = Input { Value = 0, },
				ShadingElement1BorderRound = Input { Value = 0, },
				ShadingElement1ColorMode = Input { Value = 0, },
				ShadingElement1GradientAngle = Input { Value = 0, },
				ShadingElement1MappingSize = Input { Value = 1.5, },
				ShadingElement1MappingAspect = Input { Value = 1, },
				ShadingElement1MappingLevel = Input { Value = 0, },
				ShadingElement1Red = Input { Value = 1, },
				ShadingElement1Green = Input { Value = 1, },
				ShadingElement1Blue = Input { Value = 1, },
				ShadingElement1Alpha = Input { Value = 1, },
				ShadingElement1EndRed = Input { Value = 1, },
				ShadingElement1EndGreen = Input { Value = 1, },
				ShadingElement1EndBlue = Input { Value = 1, },
				ShadingElement1EndAlpha = Input { Value = 1, },
				ShadingElement2Enable = Input { Value = 0, },
				ShadingElement3Enable = Input { Value = 0, },
				ShadingElement4Enable = Input { Value = 0, },
				ShadingElement5Enable = Input { Value = 0, },
				ShadingElement6Enable = Input { Value = 0, },
				ShadingElement7Enable = Input { Value = 0, },
				ShadingElement8Enable = Input { Value = 0, },
				MotionBlurEnable = Input { Value = 0, },
			},
		},
	},
}
```

## 12. Example 2: Party Pop (fun sticker)

Lime Arial Black with a black outline (element 2) and a hard shadow (element 3). The letters pop in from size 0 with an elastic bounce: they rise, spin in from -120 degrees and gather together. Motion blur is on. At frame 100, the letters spin away upwards.

<!-- example: Textizo - Party Pop -->
```lua
{
	Tools = ordered() {
		Textizo1 = Fuse.Textizo {
			Inputs = {
				StateVersion = Input { Value = 11, },
				InEnable = Input { Value = 1, },
				Width = Input { Value = 1920, },
				Height = Input { Value = 1080, },
				UseFrameFormatSettings = Input { Value = 1, },
				StyledText = Input { Value = "TEXTIZO!", },
				TextEdited = Input { Value = 1, },
				Font = Input { Value = "Arial Black", },
				Style = Input { Value = "Regular", },
				Size = Input { Value = 2.4, },
				Center = Input { Value = { 0.5, 0.5 }, },
				Tracking = Input { Value = 0, },
				LineSpacing = Input { Value = 1, },
				Alignment = Input { Value = 1, },
				Rotation = Input { Value = 0, },
				Red = Input { Value = 1, },
				Green = Input { Value = 1, },
				Blue = Input { Value = 1, },
				Alpha = Input { Value = 1, },
				InopacityEnable = Input { Value = 1, },
				InopacityFollower = Input { Value = FuID { "letters" }, },
				InopacityAnimationStart = Input { Value = 0, },
				InopacityAnimationEnd = Input { Value = 18, },
				InopacityStagger = Input { Value = 50, },
				InopacityStartValue = Input { Value = 0, },
				InopacityEndValue = Input { Value = 1, },
				InopacityCurveMode = Input { Value = FuID { "preset" }, },
				InopacityCurvePreset = Input { Value = FuID { "out_quad" }, },
				InopacityCurvePresetID = Input { Value = "out_quad", },
				InblurEnable = Input { Value = 1, },
				InblurFollower = Input { Value = FuID { "letters" }, },
				InblurAnimationStart = Input { Value = 0, },
				InblurAnimationEnd = Input { Value = 20, },
				InblurStagger = Input { Value = 33, },
				InblurStartValue = Input { Value = 0.12, },
				InblurEndValue = Input { Value = 0, },
				InblurCurveMode = Input { Value = FuID { "preset" }, },
				InblurCurvePreset = Input { Value = FuID { "out_cubic" }, },
				InblurCurvePresetID = Input { Value = "out_cubic", },
				IncenterEnable = Input { Value = 1, },
				IncenterFollower = Input { Value = FuID { "letters" }, },
				IncenterAnimationStart = Input { Value = 0, },
				IncenterAnimationEnd = Input { Value = 22, },
				IncenterStagger = Input { Value = 25, },
				IncenterStartValue = Input { Value = { 0, -0.12 }, },
				IncenterEndValue = Input { Value = { 0, 0 }, },
				IncenterCurveMode = Input { Value = FuID { "preset" }, },
				IncenterCurvePreset = Input { Value = FuID { "out_back" }, },
				IncenterCurvePresetID = Input { Value = "out_back", },
				InsizeEnable = Input { Value = 1, },
				InsizeFollower = Input { Value = FuID { "letters" }, },
				InsizeAnimationStart = Input { Value = 0, },
				InsizeAnimationEnd = Input { Value = 26, },
				InsizeStagger = Input { Value = 17, },
				InsizeStartValue = Input { Value = 0, },
				InsizeEndValue = Input { Value = 1, },
				InsizeCurveMode = Input { Value = FuID { "preset" }, },
				InsizeCurvePreset = Input { Value = FuID { "out_elastic" }, },
				InsizeCurvePresetID = Input { Value = "out_elastic", },
				IntrackingEnable = Input { Value = 1, },
				IntrackingFollower = Input { Value = FuID { "letters" }, },
				IntrackingAnimationStart = Input { Value = 0, },
				IntrackingAnimationEnd = Input { Value = 18, },
				IntrackingStagger = Input { Value = 0, },
				IntrackingStartValue = Input { Value = 0.05, },
				IntrackingEndValue = Input { Value = 0, },
				IntrackingCurveMode = Input { Value = FuID { "preset" }, },
				IntrackingCurvePreset = Input { Value = FuID { "out_back" }, },
				IntrackingCurvePresetID = Input { Value = "out_back", },
				InrotationEnable = Input { Value = 1, },
				InrotationFollower = Input { Value = FuID { "letters" }, },
				InrotationAnimationStart = Input { Value = 0, },
				InrotationAnimationEnd = Input { Value = 22, },
				InrotationStagger = Input { Value = 25, },
				InrotationStartValue = Input { Value = -120, },
				InrotationEndValue = Input { Value = 0, },
				InrotationCurveMode = Input { Value = FuID { "preset" }, },
				InrotationCurvePreset = Input { Value = FuID { "out_back" }, },
				InrotationCurvePresetID = Input { Value = "out_back", },
				InexplosionEnable = Input { Value = 0, },
				OutopacityEnable = Input { Value = 1, },
				OutopacityFollower = Input { Value = FuID { "letters" }, },
				OutopacityAnimationStart = Input { Value = 100, },
				OutopacityAnimationEnd = Input { Value = 115, },
				OutopacityStagger = Input { Value = 30, },
				OutopacityEndValue = Input { Value = 0, },
				OutopacityCurveMode = Input { Value = FuID { "preset" }, },
				OutopacityCurvePreset = Input { Value = FuID { "in_cubic" }, },
				OutopacityCurvePresetID = Input { Value = "in_cubic", },
				OutblurEnable = Input { Value = 1, },
				OutblurFollower = Input { Value = FuID { "letters" }, },
				OutblurAnimationStart = Input { Value = 100, },
				OutblurAnimationEnd = Input { Value = 116, },
				OutblurStagger = Input { Value = 25, },
				OutblurEndValue = Input { Value = 0.1, },
				OutblurCurveMode = Input { Value = FuID { "preset" }, },
				OutblurCurvePreset = Input { Value = FuID { "in_quad" }, },
				OutblurCurvePresetID = Input { Value = "in_quad", },
				OutcenterEnable = Input { Value = 1, },
				OutcenterFollower = Input { Value = FuID { "letters" }, },
				OutcenterAnimationStart = Input { Value = 100, },
				OutcenterAnimationEnd = Input { Value = 116, },
				OutcenterStagger = Input { Value = 25, },
				OutcenterEndValue = Input { Value = { 0, 0.1 }, },
				OutcenterCurveMode = Input { Value = FuID { "preset" }, },
				OutcenterCurvePreset = Input { Value = FuID { "in_back" }, },
				OutcenterCurvePresetID = Input { Value = "in_back", },
				OutsizeEnable = Input { Value = 1, },
				OutsizeFollower = Input { Value = FuID { "letters" }, },
				OutsizeAnimationStart = Input { Value = 100, },
				OutsizeAnimationEnd = Input { Value = 116, },
				OutsizeStagger = Input { Value = 25, },
				OutsizeEndValue = Input { Value = 0, },
				OutsizeCurveMode = Input { Value = FuID { "preset" }, },
				OutsizeCurvePreset = Input { Value = FuID { "in_back" }, },
				OutsizeCurvePresetID = Input { Value = "in_back", },
				OuttrackingEnable = Input { Value = 0, },
				OutrotationEnable = Input { Value = 1, },
				OutrotationFollower = Input { Value = FuID { "letters" }, },
				OutrotationAnimationStart = Input { Value = 100, },
				OutrotationAnimationEnd = Input { Value = 116, },
				OutrotationStagger = Input { Value = 25, },
				OutrotationEndValue = Input { Value = 180, },
				OutrotationCurveMode = Input { Value = FuID { "preset" }, },
				OutrotationCurvePreset = Input { Value = FuID { "in_back" }, },
				OutrotationCurvePresetID = Input { Value = "in_back", },
				OutexplosionEnable = Input { Value = 0, },
				ShadingActiveElement = Input { Value = FuID { "element_1" }, },
				ShadingProxyEnable = Input { Value = 1, },
				ShadingProxyAppearance = Input { Value = 0, },
				ShadingProxyOpacity = Input { Value = 1, },
				ShadingProxyThickness = Input { Value = 0.02, },
				ShadingProxyOffset = Input { Value = { 0, 0 }, },
				ShadingProxySoftnessX = Input { Value = 0, },
				ShadingProxySoftnessY = Input { Value = 0, },
				ShadingProxyBorderLevel = Input { Value = 0, },
				ShadingProxyBorderExtendX = Input { Value = 0, },
				ShadingProxyBorderExtendY = Input { Value = 0, },
				ShadingProxyBorderRound = Input { Value = 0, },
				ShadingProxyColorMode = Input { Value = 0, },
				ShadingProxyGradientAngle = Input { Value = 0, },
				ShadingProxyMappingSize = Input { Value = 1.5, },
				ShadingProxyMappingAspect = Input { Value = 1, },
				ShadingProxyMappingLevel = Input { Value = 0, },
				ShadingProxyRed = Input { Value = 0.75, },
				ShadingProxyGreen = Input { Value = 1, },
				ShadingProxyBlue = Input { Value = 0, },
				ShadingProxyAlpha = Input { Value = 1, },
				ShadingProxyEndRed = Input { Value = 1, },
				ShadingProxyEndGreen = Input { Value = 1, },
				ShadingProxyEndBlue = Input { Value = 1, },
				ShadingProxyEndAlpha = Input { Value = 1, },
				ShadingElement1Enable = Input { Value = 1, },
				ShadingElement1Appearance = Input { Value = 0, },
				ShadingElement1Opacity = Input { Value = 1, },
				ShadingElement1Thickness = Input { Value = 0.02, },
				ShadingElement1Offset = Input { Value = { 0, 0 }, },
				ShadingElement1SoftnessX = Input { Value = 0, },
				ShadingElement1SoftnessY = Input { Value = 0, },
				ShadingElement1BorderLevel = Input { Value = 0, },
				ShadingElement1BorderExtendX = Input { Value = 0, },
				ShadingElement1BorderExtendY = Input { Value = 0, },
				ShadingElement1BorderRound = Input { Value = 0, },
				ShadingElement1ColorMode = Input { Value = 0, },
				ShadingElement1GradientAngle = Input { Value = 0, },
				ShadingElement1MappingSize = Input { Value = 1.5, },
				ShadingElement1MappingAspect = Input { Value = 1, },
				ShadingElement1MappingLevel = Input { Value = 0, },
				ShadingElement1Red = Input { Value = 0.75, },
				ShadingElement1Green = Input { Value = 1, },
				ShadingElement1Blue = Input { Value = 0, },
				ShadingElement1Alpha = Input { Value = 1, },
				ShadingElement1EndRed = Input { Value = 1, },
				ShadingElement1EndGreen = Input { Value = 1, },
				ShadingElement1EndBlue = Input { Value = 1, },
				ShadingElement1EndAlpha = Input { Value = 1, },
				ShadingElement2Enable = Input { Value = 1, },
				ShadingElement2Appearance = Input { Value = 1, },
				ShadingElement2Opacity = Input { Value = 1, },
				ShadingElement2Thickness = Input { Value = 0.009, },
				ShadingElement2Offset = Input { Value = { 0, 0 }, },
				ShadingElement2SoftnessX = Input { Value = 0, },
				ShadingElement2SoftnessY = Input { Value = 0, },
				ShadingElement2BorderLevel = Input { Value = 0, },
				ShadingElement2BorderExtendX = Input { Value = 0, },
				ShadingElement2BorderExtendY = Input { Value = 0, },
				ShadingElement2BorderRound = Input { Value = 0, },
				ShadingElement2ColorMode = Input { Value = 0, },
				ShadingElement2GradientAngle = Input { Value = 0, },
				ShadingElement2MappingSize = Input { Value = 1.5, },
				ShadingElement2MappingAspect = Input { Value = 1, },
				ShadingElement2MappingLevel = Input { Value = 0, },
				ShadingElement2Red = Input { Value = 0, },
				ShadingElement2Green = Input { Value = 0, },
				ShadingElement2Blue = Input { Value = 0, },
				ShadingElement2Alpha = Input { Value = 1, },
				ShadingElement2EndRed = Input { Value = 1, },
				ShadingElement2EndGreen = Input { Value = 1, },
				ShadingElement2EndBlue = Input { Value = 1, },
				ShadingElement2EndAlpha = Input { Value = 1, },
				ShadingElement3Enable = Input { Value = 1, },
				ShadingElement3Appearance = Input { Value = 0, },
				ShadingElement3Opacity = Input { Value = 0.85, },
				ShadingElement3Thickness = Input { Value = 0.02, },
				ShadingElement3Offset = Input { Value = { 0.006, -0.012 }, },
				ShadingElement3SoftnessX = Input { Value = 0, },
				ShadingElement3SoftnessY = Input { Value = 0, },
				ShadingElement3BorderLevel = Input { Value = 0, },
				ShadingElement3BorderExtendX = Input { Value = 0, },
				ShadingElement3BorderExtendY = Input { Value = 0, },
				ShadingElement3BorderRound = Input { Value = 0, },
				ShadingElement3ColorMode = Input { Value = 0, },
				ShadingElement3GradientAngle = Input { Value = 0, },
				ShadingElement3MappingSize = Input { Value = 1.5, },
				ShadingElement3MappingAspect = Input { Value = 1, },
				ShadingElement3MappingLevel = Input { Value = 0, },
				ShadingElement3Red = Input { Value = 0, },
				ShadingElement3Green = Input { Value = 0, },
				ShadingElement3Blue = Input { Value = 0, },
				ShadingElement3Alpha = Input { Value = 1, },
				ShadingElement3EndRed = Input { Value = 1, },
				ShadingElement3EndGreen = Input { Value = 1, },
				ShadingElement3EndBlue = Input { Value = 1, },
				ShadingElement3EndAlpha = Input { Value = 1, },
				ShadingElement4Enable = Input { Value = 0, },
				ShadingElement5Enable = Input { Value = 0, },
				ShadingElement6Enable = Input { Value = 0, },
				ShadingElement7Enable = Input { Value = 0, },
				ShadingElement8Enable = Input { Value = 0, },
				MotionBlurEnable = Input { Value = 1, },
				MotionBlurShutterAngle = Input { Value = 180, },
				MotionBlurSamples = Input { Value = 2, },
				MotionBlurBias = Input { Value = 0, },
				MotionBlurSampleSpread = Input { Value = 1, },
			},
		},
	},
}
```

## 13. Using a preset in Resolve

**As a new node.** Copy the whole code block. On the Fusion page, click an empty spot in the Nodes area and press Ctrl+V (Mac: Cmd+V).

**Connect it.** A new node shows nothing until it is connected.

- For a title on its own, connect Textizo to MediaOut1.
- Over video, add a Merge node: MediaIn1 goes to its yellow background input, Textizo to its green foreground input, and the Merge to MediaOut1.

**On an existing Textizo node.**

1. Save the code as a plain text file with the preset's short name, for example `Textizo-01A.setting`. In Notepad, choose "Save as type: All files".
2. Right-click the node and choose **Settings > Load…**, then pick the file.

**Keep it in Resolve's Settings folder.** Settings > Load… opens this folder, and presets saved there are listed in a Textizo node's right-click Settings menu. Create the folder if it does not exist.

| System | Folder | Notes |
|---|---|---|
| Windows | `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Settings` | the same as `C:\Users\<you>\AppData\Roaming\...`. AppData is hidden: paste the path into File Explorer's address bar |
| Mac | `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Settings` | in Finder, use Go > Go to Folder… |
| Linux | `~/.local/share/DaVinciResolve/Fusion/Settings` | |

**Drag and drop.** Dragging a `.setting` file from File Explorer or Finder onto the Nodes area also adds the node.

After loading a preset, type your own text in the Inspector (Text page). The animation adapts to any text length, because Stagger % keeps the timing between the Start and End Frames.

## 14. Troubleshooting

- **Nothing happens when pasting.**
  - Copy the whole block, from the first `{` to the last `}`.
  - Click in the Nodes area before pressing Ctrl+V.
- **No animation.**
  - Check that the row's `Enable` is 1.
  - Check that the playhead is between the Start and End Frames. Frames count from the clip's first frame.
- **The text sits too high or too low.** `Center` is the first line's baseline (see section 9).
- **Letters are cut off at the sides.** Lower `Size` (see the width rule in section 9) or split the text into lines.
- **The exit comes too early or too late.** Move every Out row's Start and End Frames by the same number of frames.
- **Letters jump when they land in an Explosion.** Set Spin X/Y/Z (`...RotationX`, `...RotationY`, `...Rotation`) to 0.
- **The colour is wrong or doesn't change.** Element 1 must be written as `ShadingProxy...` *and* `ShadingElement1...`, with the same values. Keep the Text page `Red`, `Green` and `Blue` at 1.
- **The text looks blurry or pixelated, and the viewer says 320x240.** The preset has no image size. Add `UseFrameFormatSettings = 1` with `Width` 1920 and `Height` 1080, or tick "Use Frame Format Settings" on the node's Image tab.
- **Slow playback.** Turn motion blur off while you edit, prefer solid colours to gradients, and keep the hold still.
- **A font looks different on another computer.** Use a font from the safe list.
