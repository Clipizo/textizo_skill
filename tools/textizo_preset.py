#!/usr/bin/env python3
"""Textizo preset helper (Python 3, standard library only).

Commands:
  check   <file.setting> [--frames N]     check a preset and print its timing
  build   <spec.json> <out.setting>        write a complete preset from a short JSON spec
  to-spec <file.setting> [<out.json>]      turn an existing preset into a spec to edit
  timing  --text "..." --span S --delay D  Start/End Frame and Stagger % for a row
  where                                    print the folders presets can go to
  install <file.setting>... --to resolve|downloads|<folder> [--overwrite]

The rules this tool applies are written out in "Textizo AI Guide.md".
"""
import argparse
import json
import math
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
INPUTS_PATH = os.path.join(KIT, "reference", "inputs.json")

PAGES = ("In", "Out")
ROWS = ("opacity", "blur", "center", "size", "tracking", "rotation", "explosion")
ROW_ALIASES = {"position": "center", "pos": "center", "scale": "size", "spin": "rotation"}
ROW_FIELDS = ("Follower", "AnimationStart", "AnimationEnd", "Stagger", "StartValue", "EndValue",
              "CurveMode", "CurvePreset", "CurvePresetID")
EXPLOSION_FIELDS = ("Damping", "Speed", "RotationX", "RotationY", "Rotation", "Offset", "Reverse")
ELEMENT_FIELDS = ("Enable", "Appearance", "Opacity", "Thickness", "Offset", "SoftnessX", "SoftnessY",
                  "BorderLevel", "BorderExtendX", "BorderExtendY", "BorderRound", "ColorMode",
                  "GradientAngle", "MappingSize", "MappingAspect", "MappingLevel",
                  "Red", "Green", "Blue", "Alpha", "EndRed", "EndGreen", "EndBlue", "EndAlpha")
EASES = ["linear"] + ["%s_%s" % (kind, curve)
                      for curve in ("quad", "cubic", "quart", "quint", "sine", "expo", "circ", "back", "elastic", "bounce")
                      for kind in ("in", "out", "in_out")]
OVERSHOOT_EASES = {e for e in EASES if e.endswith(("back", "elastic", "bounce"))}
FOLLOWERS = ("letters", "words", "lines")
APPEARANCES = {"normal": 0, "fill": 0, "outline": 1, "stroke_only": 1, "stroke": 1,
               "border_fill": 2, "box": 2, "border_stroke": 3, "box_outline": 3}
APPEARANCE_NAMES = ["normal", "outline", "border_fill", "border_stroke"]
LEVELS = {"letters": 0, "letter": 0, "words": 1, "word": 1, "lines": 2, "line": 2}
MAPPING_LEVELS = {"letters": 0, "letter": 0, "words": 1, "word": 1, "lines": 2, "line": 2, "text": 3}
ALIGN = {"left": 0, "center": 1, "centre": 1, "right": 2}
SAFE_FONTS = ("Arial", "Arial Black", "Verdana", "Tahoma", "Trebuchet MS", "Georgia",
              "Times New Roman", "Courier New", "Impact", "Comic Sans MS")
STATE_VERSION = 11
BLUR_CAP_1080 = 30.0 / (1080 * 0.10)  # the Blur row stops growing above this at 1080p
SOFTNESS_CAP_1080 = 14.0 / (1080 * 0.10)  # shading softness stops growing above this at 1080p

# Rough layout estimates (Textizo Size 1 = Text+ 0.08: one em is 0.064 x Size of the
# frame width). Arial advance widths per 1000 em; other fonts scale them.
ARIAL_WIDTHS = dict(zip(
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 +
    [278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722,
     778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 333, 556, 556, 500,
     556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500,
     500, 500, 334, 260, 334, 584]))
FONT_WIDTH_FACTOR = {"Arial": 1.0, "Arial Black": 1.2, "Verdana": 1.17, "Tahoma": 1.0, "Trebuchet MS": 0.98,
                     "Georgia": 1.05, "Times New Roman": 0.88, "Impact": 0.85, "Comic Sans MS": 1.05}
EM_PER_SIZE = 0.064
CAP_HEIGHT_EM = 0.716
LINE_HEIGHT_EM = 1.15
DESCENT_EM = 0.21


# --------------------------------------------------------------------------- reading Fusion settings

class Table:
    """A Lua table from a settings file; `kind` is the constructor name (Input, FuID, ...)."""

    def __init__(self, kind=None):
        self.kind = kind
        self.fields = {}
        self.items = []
        self.duplicates = []

    def get(self, key, default=None):
        return self.fields.get(key, default)


class Ref:
    def __init__(self, name):
        self.name = name


TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<comment>--\[(?P<ceq>=*)\[.*?\](?P=ceq)\]|--[^\n]*)
  | (?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<longstr>\[(?P<leq>=*)\[.*?\](?P=leq)\])
  | (?P<num>-?(?:0[xX][0-9a-fA-F]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?))
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<sym>[{}\[\]=,;().])
""", re.S | re.X)


def unescape_lua(body):
    out, i = [], 0
    simple = {"n": "\n", "t": "\t", "r": "\r", "a": "\a", "b": "\b", "f": "\f", "v": "\v",
              "\\": "\\", '"': '"', "'": "'", "\n": "\n"}
    raw = body.encode("utf-8")
    data = bytearray()
    while i < len(raw):
        c = raw[i:i + 1]
        if c != b"\\":
            data += c
            i += 1
            continue
        nxt = raw[i + 1:i + 2].decode("latin-1")
        if nxt in simple:
            data += simple[nxt].encode("utf-8")
            i += 2
        elif nxt.isdigit():
            m = re.match(rb"\d{1,3}", raw[i + 1:])
            data.append(int(m.group(0)) & 0xFF)
            i += 1 + len(m.group(0))
        elif nxt == "x":
            data.append(int(raw[i + 2:i + 4], 16))
            i += 4
        elif nxt == "z":
            i += 2
            while i < len(raw) and raw[i:i + 1].isspace():
                i += 1
        else:
            data += raw[i + 1:i + 2]
            i += 2
    out.append(data.decode("utf-8", "replace"))
    return "".join(out)


def tokenize(text):
    pos, tokens = 0, []
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            line = text.count("\n", 0, pos) + 1
            raise ValueError("cannot read the settings text at line %d: %r" % (line, text[pos:pos + 20]))
        pos = m.end()
        kind = m.lastgroup
        if kind in ("ws", "comment"):
            continue
        if kind in ("ceq", "leq"):
            kind = "longstr" if m.group("longstr") else "comment"
            if kind == "comment":
                continue
        value = m.group(kind)
        if kind == "str":
            tokens.append(("str", unescape_lua(value[1:-1])))
        elif kind == "longstr":
            eq = len(m.group("leq"))
            body = value[2 + eq:-(2 + eq)]
            tokens.append(("str", body[1:] if body.startswith("\n") else body))
        elif kind == "num":
            tokens.append(("num", float(int(value, 16)) if "x" in value.lower() else float(value)))
        else:
            tokens.append((kind, value))
    return tokens


class Parser:
    def __init__(self, text):
        self.tokens = tokenize(text)
        self.i = 0

    def peek(self, offset=0):
        j = self.i + offset
        return self.tokens[j] if j < len(self.tokens) else ("eof", None)

    def take(self, kind=None, value=None):
        tok = self.peek()
        if (kind and tok[0] != kind) or (value is not None and tok[1] != value):
            raise ValueError("expected %s but found %r" % (value or kind, tok[1]))
        self.i += 1
        return tok

    def value(self):
        kind, val = self.peek()
        if kind == "sym" and val == "{":
            return self.table(None)
        if kind == "str":
            self.i += 1
            return val
        if kind == "num":
            self.i += 1
            return int(val) if val.is_integer() and abs(val) < 1e15 else val
        if kind == "name":
            self.i += 1
            if val in ("true", "false"):
                return val == "true"
            if val == "nil":
                return None
            name = val
            while self.peek() == ("sym", "."):
                self.i += 1
                name += "." + self.take("name")[1]
            if self.peek() == ("sym", "("):
                self.take("sym", "(")
                self.take("sym", ")")
                name += "()"
            if self.peek() == ("sym", "{"):
                return self.table(name)
            return Ref(name)
        raise ValueError("unexpected %r" % (val,))

    def table(self, kind):
        t = Table(kind)
        self.take("sym", "{")
        while self.peek() != ("sym", "}"):
            kind_, val = self.peek()
            if kind_ == "name" and self.peek(1) == ("sym", "="):
                self.i += 2
                key = val
                if key in t.fields:
                    t.duplicates.append(key)
                t.fields[key] = self.value()
            elif kind_ == "sym" and val == "[":
                self.i += 1
                key = self.value()
                self.take("sym", "]")
                self.take("sym", "=")
                t.fields[key] = self.value()
            else:
                t.items.append(self.value())
            if self.peek()[0] == "sym" and self.peek()[1] in (",", ";"):
                self.i += 1
        self.take("sym", "}")
        return t


def read_setting(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        text = handle.read()
    parser = Parser(text)
    root = parser.value()
    if not isinstance(root, Table):
        raise ValueError("the file does not start with {")
    return root


def find_textizo_tools(root):
    tools = root.get("Tools")
    if not isinstance(tools, Table):
        raise ValueError("no Tools = ordered() { ... } block")
    found, others = [], []
    for name, tool in tools.fields.items():
        if isinstance(tool, Table) and tool.kind == "Fuse.Textizo":
            found.append((name, tool))
        elif isinstance(tool, Table):
            others.append((name, tool.kind))
    return found, others


def input_value(entry):
    """Value of `X = Input { Value = ... }`; Ref for connections."""
    if not isinstance(entry, Table) or entry.kind != "Input":
        return None
    if "SourceOp" in entry.fields:
        return Ref("connected to " + str(entry.fields.get("SourceOp")))
    return entry.fields.get("Value")


# --------------------------------------------------------------------------- the Textizo control list

def load_inputs():
    with open(INPUTS_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def fuid(value):
    if isinstance(value, Table) and value.kind == "FuID" and value.items:
        return str(value.items[0])
    return None


def point(value):
    if isinstance(value, Table) and value.kind is None and len(value.items) == 2 and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in value.items):
        return (float(value.items[0]), float(value.items[1]))
    return None


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def same_value(a, b):
    if is_number(a) and is_number(b):
        return abs(float(a) - float(b)) <= 1e-6
    if fuid(a) is not None or fuid(b) is not None:
        return fuid(a) == fuid(b)
    if point(a) is not None or point(b) is not None:
        pa, pb = point(a), point(b)
        return pa is not None and pb is not None and all(abs(x - y) <= 1e-6 for x, y in zip(pa, pb))
    if isinstance(a, Table) and isinstance(b, Table):
        return gradient_stops(a) == gradient_stops(b)
    return a == b


def gradient_stops(value):
    if not isinstance(value, Table) or value.kind != "Gradient":
        return None
    colors = value.get("Colors")
    if not isinstance(colors, Table):
        return None
    stops = []
    for pos, color in colors.fields.items():
        if not is_number(pos) or not isinstance(color, Table) or len(color.items) < 3:
            return None
        stops.append((round(float(pos), 6), tuple(round(float(c), 6) for c in color.items)))
    return sorted(stops)


def plain_default(value):
    """An inputs.json default as a settings value (points become a point table)."""
    if isinstance(value, list) and len(value) == 2:
        t = Table(None)
        t.items = list(value)
        return t
    return value


def describe(value):
    if isinstance(value, Ref):
        return value.name
    if fuid(value) is not None:
        return fuid(value)
    if point(value) is not None:
        return "(%s, %s)" % tuple(fmt_num(v) for v in point(value))
    if gradient_stops(value) is not None:
        return "gradient %d stops" % len(gradient_stops(value))
    if is_number(value):
        return fmt_num(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


# --------------------------------------------------------------------------- timing (as the node computes it)

def count_groups(text, by):
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    letters = words = lines = 0
    for line in text.split("\n"):
        in_word = has_glyph = False
        for ch in line:
            if ch in " \t":
                in_word = False
            else:
                letters += 1
                has_glyph = True
                if not in_word:
                    words += 1
                    in_word = True
        if has_glyph:
            lines += 1
    return max(1, {"letters": letters, "words": words, "lines": lines}.get(by, letters))


def round_int(x):
    return int(math.floor(float(x) + 0.5))


def row_window(start, end, stagger, groups):
    """(frames each group moves, frames between groups) for a row."""
    window = max(1, round_int(end) - max(0, round_int(start)))
    groups = max(1, int(groups))
    fraction = max(0.0, float(stagger)) / 100.0
    delay = 0.0
    if groups > 1:
        delay = min(fraction * window / (1.0 + fraction * (groups - 1)), (window - 1) / (groups - 1))
    span = max(1.0, window - delay * (groups - 1))
    return span, delay


def plan_row(start, span, delay, groups):
    """Start Frame, End Frame and Stagger % that give each group `span` frames, `delay` apart."""
    if groups <= 1 or delay <= 0:
        return start, start + max(1, round_int(span)), 0.0
    return start, start + max(1, round_int(span + delay * (groups - 1))), round(delay / span * 100.0, 1)


# --------------------------------------------------------------------------- check

class Report:
    def __init__(self):
        self.errors, self.warnings, self.notes, self.info = [], [], [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def note(self, msg):
        self.notes.append(msg)


def check_type(spec, value):
    """None when `value` fits the input's data type, else a short reason."""
    dtype = spec.get("type")
    if isinstance(value, Ref):
        return None if dtype == "LookUpTable" else "is connected to another node"
    if dtype == "Number":
        if not is_number(value):
            return "needs a number"
        options = spec.get("options")
        control = spec.get("control")
        if control == "CheckboxControl" and value not in (0, 1):
            return "is a checkbox: use 0 or 1"
        if options and control in ("ComboControl", "MultiButtonControl"):
            if not float(value).is_integer() or not 0 <= value < len(options):
                return "must be one of 0..%d (%s)" % (len(options) - 1, ", ".join(
                    "%d %s" % (i, o.get("label") or o.get("id")) for i, o in enumerate(options)))
        lo, hi = spec.get("min"), spec.get("max")
        if lo is not None and value < lo or hi is not None and value > hi:
            return "must be between %s and %s" % (fmt_num(lo) if lo is not None else "-inf", fmt_num(hi) if hi is not None else "inf")
        return None
    if dtype == "Text":
        return None if isinstance(value, str) else 'needs text in quotes, like "Hello"'
    if dtype == "FuID":
        fid = fuid(value)
        if fid is None:
            return 'needs FuID { "..." }'
        ids = [o.get("id") for o in spec.get("options") or [] if o.get("id")]
        if ids and fid not in ids:
            return "must be one of: " + ", ".join(ids)
        return None
    if dtype == "Point":
        return None if point(value) is not None else "needs a point { x, y }"
    if dtype == "Gradient":
        return None if gradient_stops(value) else "needs Gradient { Colors = { [0] = { r, g, b, a }, [1] = { r, g, b, a } } }"
    if dtype == "LookUpTable":
        return None
    return None


def em_widths(text, font, style):
    """Advance width of `text` in ems (rough: Arial metrics scaled per font)."""
    if font == "Courier New":
        return 0.6 * len(text)
    factor = FONT_WIDTH_FACTOR.get(font, 1.0)
    if "bold" in (style or "").lower() and font != "Arial Black":
        factor *= 1.07
    return sum(ARIAL_WIDTHS.get(ch, 556) for ch in text) / 1000.0 * factor


def check_layout(values, spec_inputs, report, aspect):
    """Rough resting layout: line widths, frame edges, word boxes touching."""
    def get(input_id):
        v = values.get(input_id)
        return spec_inputs.get(input_id, {}).get("default") if v is None else v

    text = (values.get("StyledText") or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return None
    font, style = get("Font") or "Arial", get("Style") or "Regular"
    size = float(get("Size") or 1.0)
    tracking = float(get("Tracking") or 0.0)
    line_spacing = float(get("LineSpacing") or 1.0)
    align = int(get("Alignment") if is_number(get("Alignment")) else 1)
    center = point(values.get("Center")) or (0.5, 0.5)
    em_w = EM_PER_SIZE * size              # frame widths
    em_h = em_w * aspect                   # frame heights
    lines = text.split("\n")
    widths = [em_widths(line, font, style) * em_w + tracking * max(0, len(line) - 1) for line in lines]
    widest = max(widths)
    if widest > 0.95:
        report.warn("the longest line is about %.2f frame widths wide, wider than the frame: use Size about %s or split the text "
                    "into more lines" % (widest, fmt_num(round(size * 0.85 / widest, 2))))
    elif widest > 0.86:
        report.note("the longest line is about %.2f frame widths wide, close to the frame edges" % widest)
    if widest <= 0.95:
        left = center[0] - {0: 0.0, 1: widest / 2.0, 2: widest}.get(align, widest / 2.0)
        right = left + widest
        top = center[1] + CAP_HEIGHT_EM * em_h
        bottom = center[1] - (len(lines) - 1) * LINE_HEIGHT_EM * em_h * line_spacing - DESCENT_EM * em_h
        outside = [name for name, bad in (("left", left < 0.02), ("right", right > 0.98),
                                          ("top", top > 0.98), ("bottom", bottom < 0.02)) if bad]
        if outside:
            report.warn("at rest the text reaches past the %s edge of the frame (text spans x %.2f to %.2f, y %.2f to %.2f "
                        "in a %s frame); move Center or lower Size" % (
                            " and ".join(outside), left, right, bottom, top, "16:9" if abs(aspect - 16 / 9.0) < 0.01 else "%.2f:1" % aspect))
    return {"em_w": em_w, "font": font, "style": style}


def check_tool(tool_name, tool, spec_inputs, report, clip_frames=None, aspect=16.0 / 9.0):
    inputs_table = tool.get("Inputs")
    if not isinstance(inputs_table, Table):
        report.error("%s has no Inputs = { ... } block" % tool_name)
        return
    for dup in inputs_table.duplicates:
        report.warn("%s is written twice; the last one wins" % dup)
    values = {}
    internal = []
    for input_id, entry in inputs_table.fields.items():
        if not isinstance(entry, Table) or entry.kind != "Input":
            report.error("%s must be written as %s = Input { Value = ..., }," % (input_id, input_id))
            continue
        spec = spec_inputs.get(input_id)
        value = input_value(entry)
        if spec is None:
            report.error("unknown input %s (not a Textizo control; check the spelling and capitals)" % input_id)
            continue
        role = spec.get("role")
        if role == "internal":
            internal.append(input_id)
        reason = check_type(spec, value)
        if reason:
            report.error("%s %s (it is %s)" % (input_id, reason, describe(value)))
            continue
        values[input_id] = value

    def num(input_id):
        v = values.get(input_id)
        if is_number(v):
            return float(v)
        return float(spec_inputs.get(input_id, {}).get("default") or 0)

    def has(input_id):
        return input_id in values

    # Whole-node inputs.
    if not has("StateVersion"):
        report.warn("add StateVersion = Input { Value = %d, }, (tells Textizo the preset uses the current row format)" % STATE_VERSION)
    elif num("StateVersion") != STATE_VERSION:
        report.error("StateVersion must be %d (older numbers make Textizo convert the rows as an old comp)" % STATE_VERSION)
    if has("InEnable") and num("InEnable") < 0.5:
        report.warn("InEnable = 0 switches the whole node off (it renders nothing)")
    text = values.get("StyledText")
    if text is None:
        report.warn("no StyledText: a new node shows no text until the user types some")
        text = ""
    elif text.strip() and not (has("TextEdited") and num("TextEdited") >= 0.5):
        report.note("add TextEdited = Input { Value = 1, }, next to StyledText (marks the text as the user's)")
    font = values.get("Font")
    if isinstance(font, str) and font not in SAFE_FONTS:
        report.note('font "%s" must be installed on the computer that opens the preset (safe on Windows and Mac: %s)' % (font, ", ".join(SAFE_FONTS)))
    if any(is_number(values.get(c)) and float(values.get(c)) < 0.999 for c in ("Red", "Green", "Blue")):
        report.note("the Text page Color (Red/Green/Blue) is not white: it tints Shading element 1 (colour them on the Shading element instead)")
    frame_format = input_value(inputs_table.fields.get("UseFrameFormatSettings"))
    if frame_format is None:
        report.warn("UseFrameFormatSettings is missing, so a new node made from this preset is only 320x240 (Fusion's "
                    "fallback size). Write UseFrameFormatSettings = 1 with Width 1920 and Height 1080, as Resolve "
                    "does, so the node follows the timeline's resolution")
    elif is_number(frame_format) and frame_format < 0.5:
        size = "x".join(describe(input_value(inputs_table.fields.get(k))) for k in ("Width", "Height"))
        report.note("UseFrameFormatSettings 0 pins the node to %s; 1 follows the timeline's resolution" % size)
    for fid in ("GlobalIn", "GlobalOut"):
        if fid in inputs_table.fields:
            report.warn("remove %s: it changes the node's time range" % fid)
    for fid in ("FrameRenderScript", "StartRenderScript", "EndRenderScript"):
        if isinstance(input_value(inputs_table.fields.get(fid)), str) and input_value(inputs_table.fields.get(fid)).strip():
            report.warn("%s holds a script that Fusion runs while rendering; presets never need one, so remove it "
                        "unless you wrote it yourself" % fid)
    if internal:
        report.note("%d internal inputs kept as saved by Resolve (%s%s)" % (
            len(internal), ", ".join(internal[:4]), ", ..." if len(internal) > 4 else ""))
    layout = check_layout(values, spec_inputs, report, aspect)

    # Animation rows.
    rows_out = []
    missing_enables = []
    left_out = []
    snappy_rows = []
    in_done = None
    out_start = None
    last_frame = None
    rows_per_page = {"In": 0, "Out": 0}
    followers_with_opacity = {"In": set(), "Out": set()}
    followers_used = {"In": set(), "Out": set()}
    for page in PAGES:
        for row in ROWS:
            prefix = page + row
            if not has(prefix + "Enable"):
                missing_enables.append(prefix + "Enable")
                continue
            if num(prefix + "Enable") < 0.5:
                continue
            needed = [f for f in ROW_FIELDS if not (page == "Out" and f == "StartValue")]
            if row == "explosion":
                needed += list(EXPLOSION_FIELDS)
            left_out.extend(prefix + f for f in needed if not has(prefix + f))
            by = fuid(values.get(prefix + "Follower")) or "letters"
            start = num(prefix + "AnimationStart")
            end = num(prefix + "AnimationEnd")
            stagger = num(prefix + "Stagger")
            groups = count_groups(text, by)
            if round_int(end) <= round_int(start):
                report.warn("%s: End Frame (%s) must be after Start Frame (%s)" % (prefix, fmt_num(end), fmt_num(start)))
            span, delay = row_window(start, end, stagger, groups)
            if groups > 1 and stagger > 0:
                fraction = stagger / 100.0
                wanted = fraction * max(1, round_int(end) - round_int(start)) / (1.0 + fraction * (groups - 1))
                if wanted - delay > 1e-6:
                    report.note("%s: the gap between %s was shortened to %.2f frames so every one gets at least 1 frame" % (prefix, by, delay))
            if span < 1.0 + 1e-6:
                report.warn("%s: each %s jumps in a single frame; make End Frame later or Stagger %% smaller" % (prefix, by[:-1]))
            elif span < 2.0:
                snappy_rows.append("%s (%.1f frames)" % (prefix, span))
            ease = fuid(values.get(prefix + "CurvePreset")) or "linear"
            mirror = values.get(prefix + "CurvePresetID")
            if isinstance(mirror, str) and mirror and mirror != ease:
                report.error('%sCurvePresetID ("%s") must match %sCurvePreset ("%s")' % (prefix, mirror, prefix, ease))
            if fuid(values.get(prefix + "CurveMode")) == "custom":
                report.warn("%sCurveMode is custom: the Ease preset is ignored and a hand-drawn curve is used; use preset" % prefix)
            if page == "Out" and has(prefix + "StartValue"):
                report.note("%sStartValue is ignored: an Out row starts from where the In row ended" % prefix)
            sv, ev = values.get(prefix + "StartValue"), values.get(prefix + "EndValue")
            if row == "opacity":
                for label, v in (("StartValue", sv), ("EndValue", ev)):
                    if is_number(v) and not 0 <= v <= 1:
                        report.warn("%s%s %s: opacity is 0..1" % (prefix, label, fmt_num(v)))
            if row in ("size", "blur", "explosion"):
                for label, v in (("StartValue", sv), ("EndValue", ev)):
                    if is_number(v) and v < 0:
                        report.warn("%s%s %s: negative values count as 0" % (prefix, label, fmt_num(v)))
            if row == "blur":
                for label, v in (("StartValue", sv), ("EndValue", ev)):
                    if is_number(v) and v > BLUR_CAP_1080:
                        report.note("%s%s %s: blur stops growing at about %.2f in 1080p" % (prefix, label, fmt_num(v), BLUR_CAP_1080))
            if row == "explosion":
                spins = [num(prefix + f) for f in ("RotationX", "RotationY", "Rotation")]
                if any(abs(s) > 1e-6 for s in spins):
                    report.warn("%s: Spin X/Y/Z are not 0; explosion spin jumps when a letter lands or overshoots. "
                                "Set them to 0 and turn letters with the Rotation row" % prefix)
                if ease in OVERSHOOT_EASES and page == "In" and num(prefix + "Damping") > 0:
                    report.note("%s: Damping above 0 delays the landing; 0 keeps the ease as chosen" % prefix)
            last_end = start + delay * (groups - 1) + span
            if page == "In":
                in_done = last_end if in_done is None else max(in_done, last_end)
            else:
                out_start = start if out_start is None else min(out_start, start)
            last_frame = last_end if last_frame is None else max(last_frame, last_end)
            if clip_frames is not None and last_end > clip_frames - 1 + 1e-6:
                report.warn("%s ends on frame %s, after the clip's last frame (%d)" % (prefix, fmt_num(last_end), clip_frames - 1))
            # House style (guide section 10): notes only.
            rows_per_page[page] += 1
            followers_used[page].add(by)
            if row == "opacity":
                followers_with_opacity[page].add(by)
            if row == "center":
                if ease == "linear":
                    report.note("%s: a linear ease on a position move looks mechanical; use an out_ ease (In) or in_ ease (Out)" % prefix)
                offset = point(sv if page == "In" else ev)
                if offset and abs(offset[0]) > 0.12:
                    report.note("%s: a sideways move of %s frame widths; the house style avoids long sideways slides" % (
                        prefix, fmt_num(round(abs(offset[0]), 3))))
            if page == "In" and span > 30:
                report.note("%s: each %s moves for %.0f frames; the house style keeps moves under about 14-16 frames at 24 fps" % (
                    prefix, by[:-1], span))
            rows_out.append((page, row, by, groups, round_int(start), round_int(end), stagger, span, delay, ease,
                             describe(sv) if page == "In" else "", describe(ev)))
    if snappy_rows:
        report.note("very snappy rows, each piece pops in under 2 frames (fine for a one-after-another pop): %s"
                    % ", ".join(snappy_rows))
    if missing_enables:
        report.warn("these rows have no Enable value, so a node that already has them on keeps them on: %s "
                    "(write each as 0 or 1)" % ", ".join(missing_enables))
    if in_done is not None and out_start is not None and out_start < in_done - 1e-6:
        report.warn("the Out rows start on frame %s, before the In rows finish (frame %s); the exit cuts the entrance short"
                    % (fmt_num(out_start), fmt_num(in_done)))
    if in_done is None:
        report.note("no In rows are on: the text is there from the first frame")
    if out_start is None:
        report.note("no Out rows are on: the text stays until the clip ends")
    for page in PAGES:
        if rows_per_page[page] > 6:
            report.note("%d rows are on the %s page; the house style uses about 3-4 (up to 6 for fun pops)" % (rows_per_page[page], page))
    if in_done is not None and in_done > 40:
        report.note("the entrance ends on frame %s: fine for a calm look; punchy titles finish in about 15-26 frames at 24 fps" % fmt_num(round(in_done)))
    if clip_frames is not None and last_frame is not None and clip_frames - 4 < last_frame <= clip_frames - 1 + 1e-6:
        report.note("the last row ends on frame %s, right at the end of the clip (last frame %d); leave a few frames" % (
            fmt_num(round(last_frame, 1)), clip_frames - 1))

    # Shading: the selected element is drawn from the ShadingProxy... controls.
    active = fuid(values.get("ShadingActiveElement"))
    if active is None:
        report.warn('add ShadingActiveElement = Input { Value = FuID { "element_1" }, }, (the element the Shading page shows)')
        active_index = 1
    else:
        active_index = int(active.split("_")[-1])
    fields = list(ELEMENT_FIELDS) + ["Gradient"]
    for field in fields:
        proxy_id = "ShadingProxy" + field
        element_id = "ShadingElement%d%s" % (active_index, field)
        if has(element_id) and not has(proxy_id):
            proxy_default = spec_inputs.get(proxy_id, {}).get("default")
            if field == "Gradient" or not same_value(values[element_id], plain_default(proxy_default)):
                report.error("%s is %s but %s is left out: element %d is the selected element, and Textizo draws it "
                             "from the ShadingProxy... controls. Write %s with the same value" % (
                                 element_id, describe(values[element_id]), proxy_id, active_index, proxy_id))
            else:
                left_out.append(proxy_id)
        elif has(proxy_id) and not has(element_id):
            element_default = spec_inputs.get(element_id, {}).get("default")
            if field == "Gradient" or not same_value(values[proxy_id], plain_default(element_default)):
                report.error("%s is %s but %s is left out: write %s with the same value (the Shading page reloads "
                             "element %d from it when the user switches elements)" % (
                                 proxy_id, describe(values[proxy_id]), element_id, element_id, active_index))
            else:
                left_out.append(element_id)
        elif has(proxy_id) and has(element_id) and not same_value(values[proxy_id], values[element_id]):
            report.error("%s (%s) must equal %s (%s): element %d is drawn from the ShadingProxy... controls" % (
                proxy_id, describe(values[proxy_id]), element_id, describe(values[element_id]), active_index))
    shading_lines = []
    missing_elements = []
    for index in range(1, 9):
        def eget(field, use_proxy=(index == active_index)):
            key = ("ShadingProxy" + field) if use_proxy and has("ShadingProxy" + field) else "ShadingElement%d%s" % (index, field)
            return values.get(key, spec_inputs.get("ShadingElement%d%s" % (index, field), {}).get("default"))
        enable_key = "ShadingElement%dEnable" % index
        if index != active_index and not has(enable_key):
            missing_elements.append(enable_key)
        enabled = eget("Enable")
        if not (is_number(enabled) and enabled >= 0.5):
            continue
        appearance = eget("Appearance")
        appearance = APPEARANCE_NAMES[int(appearance)] if is_number(appearance) and 0 <= appearance < 4 else "?"
        color = tuple(fmt_num(eget(c) if is_number(eget(c)) else 1) for c in ("Red", "Green", "Blue"))
        label = "element %d" % index
        for field, low, high in (("Opacity", 0, 1), ("Thickness", 0, None), ("SoftnessX", 0, None), ("SoftnessY", 0, None),
                                 ("BorderExtendX", 0, None), ("BorderExtendY", 0, None), ("BorderRound", 0, None)):
            v = eget(field)
            if is_number(v) and (v < low or (high is not None and v > high)):
                report.warn("%s %s is %s; it must be %s" % (label, field, fmt_num(v), "0 to 1" if high else "0 or more"))
        soft = eget("SoftnessX")
        if is_number(soft) and soft > SOFTNESS_CAP_1080 + 0.005:
            report.note("%s softness %s: softness stops growing at about %.2f in 1080p; for a wider glow use an Outline "
                        "with Thickness plus softness" % (label, fmt_num(soft), SOFTNESS_CAP_1080))
        extra = []
        if appearance in ("outline", "border_stroke"):
            extra.append("thickness %s" % describe(eget("Thickness")))
        if appearance in ("border_fill", "border_stroke"):
            level = eget("BorderLevel")
            level_name = ["letters", "words", "lines"][int(level)] if is_number(level) and 0 <= level <= 2 else "letters"
            extra.append("box per %s, extend (%s, %s), round %s" % (level_name[:-1], describe(eget("BorderExtendX")),
                                                                   describe(eget("BorderExtendY")), describe(eget("BorderRound"))))
            if appearance == "border_fill" and is_number(soft) and soft > 0 and level_name == "letters" and index > 1:
                report.note("%s is a Border Fill box behind every letter (with softness it looks like a soft panel); "
                            "for a glow use Appearance 0 (Normal)" % label)
            if level_name in ("words", "lines"):
                own = {"words": ("words", "lines"), "lines": ("lines",)}[level_name]
                for page in PAGES:
                    if followers_used[page] & {"letters"} and not followers_with_opacity[page] & set(own):
                        report.warn("%s: a box per %s only follows rows animated by %s, so on the %s page it %s while "
                                    "the letters animate. Add an %s Opacity row by %s" % (
                                        label, level_name[:-1], " or ".join(own), page,
                                        "is already there" if page == "In" else "stays",
                                        page, level_name))
            if level_name == "words" and layout:
                # The narrowest run of spaces between two words on a line sets the room for padding.
                runs = [len(m.group(0)) for line in text.replace("\r", "").split("\n")
                        for m in re.finditer(r"(?<=\S)[ \t]+(?=\S)", line)]
                space = em_widths(" ", layout["font"], layout["style"]) * layout["em_w"]
                gap = min(runs) * space if runs else None
                extend_x = eget("BorderExtendX")
                if gap is not None and is_number(extend_x) and 2 * extend_x >= gap * 0.9:
                    report.warn("%s: boxes of neighbouring words touch or overlap (2 x BorderExtendX %s >= the space between "
                                "words, about %s). Put 2-3 spaces between the words, or use BorderExtendX below about %s" % (
                                    label, fmt_num(round(2 * extend_x, 4)), fmt_num(round(gap, 4)), fmt_num(round(gap * 0.35, 4))))
            if layout:
                em = layout["em_w"]
                pad_x, pad_y, rnd = eget("BorderExtendX"), eget("BorderExtendY"), eget("BorderRound")
                if is_number(pad_x) and is_number(pad_y) and min(pad_x, pad_y) < 0.15 * em:
                    report.note("%s: the box hugs the text (padding %s / %s = %.2f / %.2f em of the text size); about 0.3-0.6 em "
                                "across and 0.2-0.3 em up and down looks better" % (
                                    label, fmt_num(pad_x), fmt_num(pad_y), pad_x / em, pad_y / em))
                if is_number(rnd) and rnd < 0.15 * em:
                    report.note("%s: the corners are almost square (round %s = %.2f em); use about 0.25 em for soft corners "
                                "or 1 em for round pill ends" % (label, fmt_num(rnd), rnd / em))
        offset = eget("Offset")
        if point(offset) and any(abs(v) > 1e-9 for v in point(offset)):
            extra.append("offset %s" % describe(offset))
        soft = eget("SoftnessX")
        if is_number(soft) and soft > 0:
            extra.append("softness %s" % fmt_num(soft))
        opacity = eget("Opacity")
        if is_number(opacity) and opacity < 0.999:
            extra.append("opacity %s" % fmt_num(opacity))
        mode = eget("ColorMode")
        colour_text = "gradient" if is_number(mode) and mode >= 0.5 else "colour (%s, %s, %s)" % color
        shading_lines.append("element %d %s, %s%s" % (index, appearance, colour_text, (", " + ", ".join(extra)) if extra else ""))
    if left_out:
        report.warn("%d values are left out, so loading the preset onto an existing node keeps that node's values "
                    "for them (a new node uses the defaults): %s%s" % (
                        len(left_out), ", ".join(left_out[:6]), ", ..." if len(left_out) > 6 else ""))
    if missing_elements:
        report.warn("these shading elements have no Enable value, so a node that already uses them keeps them: %s "
                    "(write each as 0 or 1)" % ", ".join(missing_elements))
    report.info.append(("rows", rows_out))
    report.info.append(("shading", shading_lines))
    report.info.append(("text", (text, values.get("Font"), values.get("Style"), values.get("Size"), values.get("Center"))))
    report.info.append(("timeline", (in_done, out_start)))


def print_report(path, report, tool_name=None, count=None, others=None):
    print("Textizo preset check: %s" % os.path.basename(path))
    if tool_name:
        print("  node: %s, %d inputs" % (tool_name, count))
    for name, kind in others or []:
        print("  other node in the file: %s (%s)" % (name, kind))
    info = dict(report.info)
    if "text" in info:
        text, font, style, size, center = info["text"]
        print("  text: %s  font: %s %s  size: %s  center: %s" % (
            json.dumps(text, ensure_ascii=True), font or "(node's)", style or "", describe(size) if size is not None else "(node's)",
            describe(center) if center is not None else "(node's)"))
    if info.get("rows"):
        print("  rows (frames from the clip start; each = frames one group moves, gap = frames between groups):")
        for page, row, by, groups, start, end, stagger, span, delay, ease, sv, ev in info["rows"]:
            values = ("%s -> %s" % (sv, ev)) if page == "In" else ("-> %s" % ev)
            print("    %-3s %-9s %-7s x%-3d frames %3d-%-3d stagger %5s%%  each %5.1f  gap %4.1f  %-12s %s" % (
                page, "position" if row == "center" else row, by, groups, start, end, fmt_num(stagger), span, delay,
                ease, values))
    if "timeline" in info:
        in_done, out_start = info["timeline"]
        parts = []
        if in_done is not None:
            parts.append("entrance done on frame %s" % fmt_num(round(in_done, 1)))
        if out_start is not None:
            parts.append("exit starts on frame %s" % fmt_num(out_start))
        if parts:
            print("  " + ", ".join(parts))
    for line in info.get("shading", []):
        print("  shading: " + line)
    for title, items in (("ERRORS", report.errors), ("WARNINGS", report.warnings), ("NOTES", report.notes)):
        if items:
            print("%s (%d):" % (title, len(items)))
            for item in items:
                print("  - " + item)
    ok = not report.errors
    print("Result: %s (%d errors, %d warnings)" % ("OK" if ok else "FAILED", len(report.errors), len(report.warnings)))
    return ok


def cmd_check(args):
    data = load_inputs()
    all_ok = True
    for path in args.files:
        report = Report()
        try:
            root = read_setting(path)
            tools, others = find_textizo_tools(root)
        except (OSError, ValueError) as exc:
            print("Textizo preset check: %s\nERRORS (1):\n  - %s\nResult: FAILED" % (os.path.basename(path), exc))
            all_ok = False
            continue
        if not tools:
            print("Textizo preset check: %s\nERRORS (1):\n  - no Fuse.Textizo node in the file\nResult: FAILED" % os.path.basename(path))
            all_ok = False
            continue
        for name, tool in tools:
            check_tool(name, tool, data["inputs"], report, args.frames, args.aspect)
            all_ok = print_report(path, report, name, len(tool.get("Inputs").fields) if isinstance(tool.get("Inputs"), Table) else 0, others) and all_ok
            report = Report()
        print()
    return 0 if all_ok else 1


# --------------------------------------------------------------------------- writing presets

def fmt_num(value):
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, int):
        return str(value)
    value = float(value)
    if value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    text = ("%.6f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def lua_string(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'


class Fu:
    """A value written as Fusion settings text."""

    def __init__(self, text):
        self.text = text


def fu_value(value):
    if isinstance(value, Fu):
        return value.text
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return fmt_num(value)
    if isinstance(value, str):
        return lua_string(value)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return "{ %s, %s }" % (fmt_num(value[0]), fmt_num(value[1]))
    raise ValueError("cannot write %r" % (value,))


def fu_id(name):
    return Fu('FuID { "%s" }' % name)


class Gradient:
    """Colour stops [(position 0-1, (r, g, b, a)), ...], written the way Fusion writes gradients."""

    def __init__(self, stops):
        self.stops = stops

    def input_lines(self, input_id):
        t = "\t\t\t\t"
        lines = [t + "%s = Input {" % input_id, t + "\tValue = Gradient {", t + "\t\tColors = {"]
        for i, (pos, color) in enumerate(self.stops):
            lines.append(t + "\t\t\t[%s] = { %s }%s" % (
                fmt_num(pos), ", ".join(fmt_num(c) for c in color), "," if i < len(self.stops) - 1 else ""))
        lines += [t + "\t\t}", t + "\t},", t + "},"]
        return lines


def fu_gradient(stops):
    return Gradient(stops)


def parse_color(value, where):
    if isinstance(value, str):
        m = re.fullmatch(r"#?([0-9a-fA-F]{6})([0-9a-fA-F]{2})?", value.strip())
        if not m:
            raise ValueError('%s: colour "%s" must be [r, g, b] (0-1) or "#RRGGBB"' % (where, value))
        rgb = [int(m.group(1)[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        alpha = int(m.group(2), 16) / 255.0 if m.group(2) else 1.0
        return [round(c, 4) for c in rgb] + [round(alpha, 4)]
    if isinstance(value, (list, tuple)) and len(value) in (3, 4) and all(is_number(c) for c in value):
        if any(c > 1.0 for c in value[:3]):
            raise ValueError("%s: colour values are 0-1 (divide 0-255 values by 255)" % where)
        return [float(c) for c in value[:3]] + [float(value[3]) if len(value) == 4 else 1.0]
    raise ValueError('%s: colour must be [r, g, b] (0-1) or "#RRGGBB"' % where)


def pair(value, where):
    if is_number(value):
        return [float(value), float(value)]
    if isinstance(value, (list, tuple)) and len(value) == 2 and all(is_number(v) for v in value):
        return [float(value[0]), float(value[1])]
    raise ValueError("%s must be a number or [x, y]" % where)


def expect_keys(obj, allowed, where):
    if not isinstance(obj, dict):
        raise ValueError("%s must be an object { ... }" % where)
    unknown = sorted(set(obj) - set(allowed))
    if unknown:
        raise ValueError("%s: unknown key(s) %s (allowed: %s)" % (where, ", ".join(unknown), ", ".join(sorted(allowed))))


def auto_center_y(size, lines, line_spacing, aspect):
    """Center Y that puts the text block in the middle (the first baseline sits on Center)."""
    em = 0.064 * size * aspect  # em height in frame heights (Text+ rule: 0.8 x 0.08 x Size x width)
    cap = 0.716 * em
    line = 1.15 * em * line_spacing
    return round(0.5 - cap / 2.0 + (lines - 1) * line / 2.0, 4)


ROW_KEYS = {"by", "start", "end", "stagger", "span", "delay", "from", "to", "ease",
            "variance", "damping", "spin_x", "spin_y", "spin_z", "pre_roll", "reverse", "pivot"}
PIVOTS = ("left", "center", "right")
ELEMENT_KEYS = {"enabled", "appearance", "color", "opacity", "thickness", "offset", "softness",
                "border_level", "extend", "round", "gradient"}
SPEC_KEYS = {"name", "text", "font", "style", "size", "center", "align", "tracking", "line_spacing", "rotation",
             "alpha", "color", "motion_blur", "in", "out", "elements", "inputs", "aspect", "notes"}
BY_ALIASES = {"letter": "letters", "word": "words", "line": "lines"}


def british(obj):
    """Accept "colour" for "color" (the guide's prose uses both spellings)."""
    if isinstance(obj, dict) and "colour" in obj:
        obj = dict(obj)
        if "color" in obj:
            raise ValueError('give either "color" or "colour", not both')
        obj["color"] = obj.pop("colour")
    return obj


def build_preset(spec, data):
    spec_inputs = data["inputs"]
    spec = british(spec)
    expect_keys(spec, SPEC_KEYS, "spec")

    def default(input_id):
        return spec_inputs[input_id].get("default")

    out = []  # (id, value) in writing order

    def put(input_id, value):
        if input_id not in spec_inputs:
            raise ValueError("internal: %s is not a Textizo input" % input_id)
        out.append((input_id, value))

    text = spec.get("text", "Textizo")
    size = float(spec.get("size", 1.0))
    line_spacing = float(spec.get("line_spacing", 1.0))
    aspect = float(spec.get("aspect", 16.0 / 9.0))
    center = spec.get("center", [0.5, 0.5])
    if center == "auto":
        center = [0.5, "auto"]
    if not (isinstance(center, (list, tuple)) and len(center) == 2):
        raise ValueError('center must be [x, y] or "auto"')
    cy = center[1]
    if cy == "auto":
        cy = auto_center_y(size, len(text.replace("\r\n", "\n").split("\n")), line_spacing, aspect)
    align = spec.get("align", "center")
    if align not in ALIGN:
        raise ValueError("align must be left, center or right")

    put("StateVersion", STATE_VERSION)
    put("InEnable", 1)
    # As Resolve saves its own nodes: follow the timeline's resolution (1920x1080 is only
    # the fallback). Without these, a node made from the file is 320x240.
    put("Width", 1920)
    put("Height", 1080)
    put("UseFrameFormatSettings", 1)
    put("StyledText", text)
    put("TextEdited", 1)
    put("Font", spec.get("font", "Arial"))
    put("Style", spec.get("style", "Regular"))
    put("Size", size)
    put("Center", [float(center[0]), float(cy)])
    put("Tracking", float(spec.get("tracking", 0.0)))
    put("LineSpacing", line_spacing)
    put("Alignment", ALIGN[align])
    put("Rotation", float(spec.get("rotation", 0.0)))
    put("Red", 1)
    put("Green", 1)
    put("Blue", 1)
    put("Alpha", float(spec.get("alpha", 1.0)))

    # Animation rows.
    for page, key in (("In", "in"), ("Out", "out")):
        rows = spec.get(key, {}) or {}
        if not isinstance(rows, dict):
            raise ValueError('"%s" must be an object like {"opacity": {...}, "position": {...}}' % key)
        resolved = {}
        for name, row in rows.items():
            row_key = ROW_ALIASES.get(name, name)
            if row_key not in ROWS:
                raise ValueError('%s: unknown row "%s" (rows: opacity, blur, position, size, tracking, rotation, explosion)' % (key, name))
            resolved[row_key] = row
        for row_key in ROWS:
            prefix = page + row_key
            row = resolved.get(row_key)
            if row is None:
                put(prefix + "Enable", 0)
                continue
            where = "%s.%s" % (key, row_key)
            expect_keys(row, ROW_KEYS, where)
            by = BY_ALIASES.get(row.get("by", "letters"), row.get("by", "letters"))
            if by not in FOLLOWERS:
                raise ValueError("%s: by must be letters, words or lines" % where)
            groups = count_groups(text, by)
            start = row.get("start", 0 if page == "In" else 100)
            if "span" in row or "delay" in row:
                if "end" in row or "stagger" in row:
                    raise ValueError("%s: give either span + delay, or end + stagger, not both (delete end and stagger "
                                     "to keep the per-letter timing when the text changes)" % where)
                span = float(row.get("span", 12))
                delay = float(row.get("delay", 0))
                start, end, stagger = plan_row(int(start), span, delay, groups)
            else:
                end = row.get("end", int(start) + 30)
                stagger = float(row.get("stagger", 10 if groups > 1 else 0))
            ease = row.get("ease", "linear")
            if ease not in EASES:
                raise ValueError("%s: ease %s is not one of %s" % (where, ease, ", ".join(EASES)))
            if page == "Out" and "from" in row:
                raise ValueError("%s: an Out row has no \"from\"; it starts where the In row ended" % where)
            put(prefix + "Enable", 1)
            put(prefix + "Follower", fu_id(by))
            put(prefix + "AnimationStart", int(start))
            put(prefix + "AnimationEnd", int(end))
            put(prefix + "Stagger", stagger)
            for field, spec_key in (("StartValue", "from"), ("EndValue", "to")):
                if page == "Out" and field == "StartValue":
                    continue
                value = row.get(spec_key, default(prefix + field))
                if row_key == "center":
                    value = pair(value, "%s.%s" % (where, spec_key))
                elif not is_number(value):
                    raise ValueError("%s.%s must be a number" % (where, spec_key))
                put(prefix + field, value)
            if row_key == "explosion":
                put(prefix + "Damping", float(row.get("damping", 0.0)))
                put(prefix + "Speed", float(row.get("variance", 0.3)))
                put(prefix + "RotationX", float(row.get("spin_x", 0.0)))
                put(prefix + "RotationY", float(row.get("spin_y", 0.0)))
                put(prefix + "Rotation", float(row.get("spin_z", 0.0)))
                put(prefix + "Offset", int(row.get("pre_roll", 0)))
                put(prefix + "Reverse", 1 if row.get("reverse") else 0)
            if "pivot" in row:
                if row_key != "tracking":
                    raise ValueError("%s: pivot is only for tracking rows" % where)
                if row["pivot"] not in PIVOTS:
                    raise ValueError("%s: pivot must be left, center or right" % where)
                put(prefix + "Pivot", fu_id(row["pivot"]))
            put(prefix + "CurveMode", fu_id("preset"))
            put(prefix + "CurvePreset", fu_id(ease))
            put(prefix + "CurvePresetID", ease)

    # Shading elements (element 1 is the selected one, so it is written to the proxy controls too).
    elements = dict(spec.get("elements", {}) or {})
    if "color" in spec:
        elements.setdefault("1", {})
        elements["1"] = dict(elements["1"], color=spec["color"])
    for key in elements:
        if str(key) not in [str(i) for i in range(1, 9)]:
            raise ValueError('elements: keys are "1" to "8"')
    put("ShadingActiveElement", fu_id("element_1"))
    element_values = {}
    for index in range(1, 9):
        e = elements.get(str(index), elements.get(index))
        prefix = "ShadingElement%d" % index
        if e is None and index > 1:
            element_values[index] = None
            continue
        e = british(e or {})
        where = "elements.%d" % index
        expect_keys(e, ELEMENT_KEYS, where)
        if index > 1 and "appearance" not in e and e.get("enabled", True):
            raise ValueError("%s: give an appearance (normal, outline, border_fill or border_stroke); element %d "
                             "otherwise starts as %s" % (where, index,
                                                         APPEARANCE_NAMES[int(default(prefix + "Appearance") or 0)]))
        vals = {field: default(prefix + field) for field in ELEMENT_FIELDS}
        vals["Offset"] = list(vals["Offset"])
        vals["Enable"] = 1 if e.get("enabled", True) else 0
        if "appearance" in e:
            name = str(e["appearance"]).lower().replace(" ", "_")
            if name not in APPEARANCES:
                raise ValueError("%s.appearance must be normal, outline, border_fill or border_stroke" % where)
            vals["Appearance"] = APPEARANCES[name]
        if "color" in e:
            r, g, b, a = parse_color(e["color"], where + ".color")
            vals.update(Red=r, Green=g, Blue=b, Alpha=a)
        if "opacity" in e:
            vals["Opacity"] = float(e["opacity"])
        if "thickness" in e:
            vals["Thickness"] = float(e["thickness"])
        if "offset" in e:
            vals["Offset"] = pair(e["offset"], where + ".offset")
        if "softness" in e:
            vals["SoftnessX"], vals["SoftnessY"] = pair(e["softness"], where + ".softness")
        if "border_level" in e:
            if e["border_level"] not in LEVELS:
                raise ValueError("%s.border_level must be letters, words or lines" % where)
            vals["BorderLevel"] = LEVELS[e["border_level"]]
        if "extend" in e:
            vals["BorderExtendX"], vals["BorderExtendY"] = pair(e["extend"], where + ".extend")
        if "round" in e:
            vals["BorderRound"] = float(e["round"])
        if not 0 <= vals["Opacity"] <= 1:
            raise ValueError("%s.opacity must be 0 to 1" % where)
        for field, key in (("Thickness", "thickness"), ("SoftnessX", "softness"), ("SoftnessY", "softness"),
                           ("BorderExtendX", "extend"), ("BorderExtendY", "extend"), ("BorderRound", "round")):
            if vals[field] < 0:
                raise ValueError("%s.%s must be 0 or more" % (where, key))
        gradient = None
        if "gradient" in e:
            g_spec = e["gradient"]
            expect_keys(g_spec, {"colors", "angle", "span", "scale", "aspect"}, where + ".gradient")
            colors = g_spec.get("colors")
            if isinstance(colors, dict):
                stops = sorted((float(pos), parse_color(c, where + ".gradient")) for pos, c in colors.items())
            elif isinstance(colors, list) and len(colors) >= 2:
                stops = [(i / (len(colors) - 1.0), parse_color(c, where + ".gradient")) for i, c in enumerate(colors)]
            else:
                raise ValueError("%s.gradient.colors needs at least two colours" % where)
            gradient = fu_gradient(stops)
            vals["ColorMode"] = 1
            vals["GradientAngle"] = float(g_spec.get("angle", 0.0))
            span = g_spec.get("span", "text")
            if span not in MAPPING_LEVELS:
                raise ValueError("%s.gradient.span must be letters, words, lines or text" % where)
            vals["MappingLevel"] = MAPPING_LEVELS[span]
            vals["MappingSize"] = float(g_spec.get("scale", 1.5))
            vals["MappingAspect"] = float(g_spec.get("aspect", 1.0))
            first, last = stops[0][1], stops[-1][1]
            vals.update(Red=first[0], Green=first[1], Blue=first[2], Alpha=first[3],
                        EndRed=last[0], EndGreen=last[1], EndBlue=last[2], EndAlpha=last[3])
        element_values[index] = (vals, gradient)
    for index in range(1, 9):
        if element_values[index] is None:
            put("ShadingElement%dEnable" % index, 0)
            continue
        vals, gradient = element_values[index]
        prefixes = ["ShadingProxy", "ShadingElement1"] if index == 1 else ["ShadingElement%d" % index]
        for prefix in prefixes:
            for field in ELEMENT_FIELDS:
                put(prefix + field, vals[field])
            if gradient is not None:
                put(prefix + "Gradient", gradient)

    # Motion blur.
    mb = spec.get("motion_blur", False)
    if mb:
        mb = {} if mb is True else mb
        expect_keys(mb, {"shutter", "quality", "bias", "spread"}, "motion_blur")
        put("MotionBlurEnable", 1)
        put("MotionBlurShutterAngle", float(mb.get("shutter", 180)))
        put("MotionBlurSamples", int(mb.get("quality", 2)))
        put("MotionBlurBias", float(mb.get("bias", 0)))
        put("MotionBlurSampleSpread", float(mb.get("spread", 1)))
    else:
        put("MotionBlurEnable", 0)

    # Raw overrides (advanced): {"InputID": number | "text" | [x, y] | {"fuid": "id"}}.
    raw = spec.get("inputs", {}) or {}
    for input_id, value in raw.items():
        if input_id not in spec_inputs:
            raise ValueError("inputs: unknown input %s" % input_id)
        if spec_inputs[input_id].get("role") != "public":
            raise ValueError("inputs: %s is not a preset control (role %s in reference/inputs.json)" % (
                input_id, spec_inputs[input_id].get("role")))
        if isinstance(value, dict) and set(value) == {"fuid"}:
            value = fu_id(value["fuid"])
        out = [(k, v) for k, v in out if k != input_id]
        out.append((input_id, value))

    lines = ["{", "\tTools = ordered() {", "\t\tTextizo1 = Fuse.Textizo {", "\t\t\tInputs = {"]
    for input_id, value in out:
        if isinstance(value, Gradient):
            lines += value.input_lines(input_id)
        else:
            lines.append("\t\t\t\t%s = Input { Value = %s, }," % (input_id, fu_value(value)))
    lines += ["\t\t\t},", "\t\t},", "\t},", "}", ""]
    return "\n".join(lines)


MY_PRESETS = os.path.join(KIT, "my-presets")


# Preset names are short: Textizo-<two-digit number><letter>, for example Textizo-07A. The
# number is a new look, the letter a variation of it (07A, 07B). No spaces: browsers turn
# them into %20 when a chat offers the file as a download.
SHORT_NAME_RE = re.compile(r"^(?:textizo[-_ ]?)?(\d{1,3})([a-z])$", re.I)
SHORT_FILE_RE = re.compile(r"^Textizo-(\d{2,3})([A-Z])\.setting$", re.I)


def preset_file_name(name):
    name = (name or "").strip()
    m = SHORT_NAME_RE.match(name)
    if m:
        return "Textizo-%02d%s.setting" % (int(m.group(1)), m.group(2).upper())
    if not name:
        return "Textizo-01A.setting"
    return (name if name.lower().startswith("textizo") else "Textizo - " + name) + ".setting"


def used_preset_names(folders):
    """{number: set(letters)} of Textizo-NNL presets in the folders."""
    used = {}
    for folder in folders:
        if os.path.isdir(folder):
            for file_name in os.listdir(folder):
                m = SHORT_FILE_RE.match(file_name)
                if m:
                    used.setdefault(int(m.group(1)), set()).add(m.group(2).upper())
    return used


def cmd_next_name(args):
    folders = [MY_PRESETS]
    for target in args.to or []:
        folders.append(os.path.expanduser({"resolve": resolve_settings_dir(), "downloads": downloads_dir()}.get(target, target)))
    used = used_preset_names(folders)
    if args.variant is not None:
        letters = used.get(args.variant, set())
        free = [ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch not in letters]
        if not free:
            print("all letters of %02d are used; start a new number" % args.variant)
            return 1
        print("Textizo-%02d%s" % (args.variant, free[0]))
        return 0
    print("Textizo-%02dA" % (max(used) + 1 if used else 1))
    return 0


def cmd_build(args):
    data = load_inputs()
    try:
        with open(args.spec, "r", encoding="utf-8-sig") as handle:
            spec = json.load(handle)
    except json.JSONDecodeError as exc:
        print("spec error: invalid JSON at line %d, column %d: %s (look for a missing or extra comma or quote)" % (
            exc.lineno, exc.colno, exc.msg))
        return 1
    try:
        text = build_preset(spec, data)
    except ValueError as exc:
        print("spec error: %s" % exc)
        return 1
    out_path = args.out or os.path.join(MY_PRESETS, preset_file_name(spec.get("name")))
    inside_work = os.path.normcase(os.path.abspath(out_path)).startswith(os.path.normcase(MY_PRESETS) + os.sep)
    if os.path.exists(out_path) and not (args.overwrite or inside_work):
        print("%s already exists; pass --overwrite to replace it (files in my-presets/ are replaced without asking)" % out_path)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote %s" % out_path)
    report = Report()
    tools, others = find_textizo_tools(read_setting(out_path))
    name, tool = tools[0]
    check_tool(name, tool, data["inputs"], report, args.frames, float(spec.get("aspect", 16.0 / 9.0)))
    if not SHORT_FILE_RE.match(os.path.basename(out_path)):
        report.note("presets get short names: Textizo-<number><letter>, for example Textizo-07A "
                    "(python tools/textizo_preset.py next-name --to <folder>)")
    ok = print_report(out_path, report, name, len(tool.get("Inputs").fields), others)
    return 0 if ok else 1


# --------------------------------------------------------------------------- preset -> spec

def preset_to_spec(path, data):
    """A spec (as build takes it) with everything a preset sets that changes the look."""
    spec_inputs = data["inputs"]
    tools, _ = find_textizo_tools(read_setting(path))
    if not tools:
        raise ValueError("no Fuse.Textizo node in %s" % path)
    _, tool = tools[0]
    values = {k: input_value(v) for k, v in tool.get("Inputs").fields.items()}

    def get(input_id):
        v = values.get(input_id)
        return spec_inputs.get(input_id, {}).get("default") if v is None else v

    def plain(v):
        if fuid(v) is not None:
            return fuid(v)
        if point(v) is not None:
            return [round(x, 6) for x in point(v)]
        if is_number(v):
            return float(fmt_num(v)) if not float(v).is_integer() else int(v)
        return v

    align_names = {0: "left", 1: "center", 2: "right"}
    spec = {"name": os.path.splitext(os.path.basename(path))[0], "text": get("StyledText") or "",
            "font": get("Font"), "style": get("Style"), "size": plain(get("Size")), "center": plain(get("Center")),
            "align": align_names.get(int(get("Alignment") if is_number(get("Alignment")) else 1), "center"),
            "tracking": plain(get("Tracking")),
            "line_spacing": plain(get("LineSpacing")), "rotation": plain(get("Rotation")), "alpha": plain(get("Alpha"))}
    for page, key in (("In", "in"), ("Out", "out")):
        rows = {}
        for row in ROWS:
            prefix = page + row
            if not (is_number(get(prefix + "Enable")) and get(prefix + "Enable") >= 0.5):
                continue
            by = plain(get(prefix + "Follower")) or "letters"
            start = plain(get(prefix + "AnimationStart"))
            groups = count_groups(get("StyledText") or "", by)
            r = {"by": by, "start": start}
            if groups > 1:
                # Per-piece numbers keep the feel when the text changes length.
                span, delay = row_window(start, get(prefix + "AnimationEnd"), get(prefix + "Stagger") or 0, groups)
                r.update(span=round(span, 3), delay=round(delay, 3))
            else:
                r.update(end=plain(get(prefix + "AnimationEnd")), stagger=plain(get(prefix + "Stagger")))
            if page == "In":
                r["from"] = plain(get(prefix + "StartValue"))
            r["to"] = plain(get(prefix + "EndValue"))
            r["ease"] = plain(get(prefix + "CurvePreset")) or "linear"
            if row == "explosion":
                r.update(variance=plain(get(prefix + "Speed")), damping=plain(get(prefix + "Damping")),
                         spin_x=plain(get(prefix + "RotationX")), spin_y=plain(get(prefix + "RotationY")),
                         spin_z=plain(get(prefix + "Rotation")), pre_roll=plain(get(prefix + "Offset")),
                         reverse=bool(get(prefix + "Reverse")))
            if row == "tracking" and plain(get(prefix + "Pivot")) in ("left", "right"):
                r["pivot"] = plain(get(prefix + "Pivot"))
            rows["position" if row == "center" else row] = r
        spec[key] = rows
    active = fuid(values.get("ShadingActiveElement")) or "element_1"
    active_index = int(active.split("_")[-1])
    elements = {}
    for index in range(1, 9):
        def eget(field):
            if index == active_index and values.get("ShadingProxy" + field) is not None:
                return values["ShadingProxy" + field]
            return get("ShadingElement%d%s" % (index, field))
        if not (is_number(eget("Enable")) and eget("Enable") >= 0.5):
            continue
        e = {"appearance": APPEARANCE_NAMES[int(eget("Appearance") or 0)],
             "color": [plain(eget("Red")), plain(eget("Green")), plain(eget("Blue"))],
             "opacity": plain(eget("Opacity"))}
        if plain(eget("Alpha")) not in (1, 1.0):
            e["color"].append(plain(eget("Alpha")))
        # Written out even at 0: the builder starts each element from its own defaults
        # (element 3's softness is 0.01, element 2's thickness 0.004, ...).
        e["thickness"] = plain(eget("Thickness"))
        e["offset"] = plain(eget("Offset")) or [0, 0]
        sx, sy = plain(eget("SoftnessX")), plain(eget("SoftnessY"))
        e["softness"] = sx if sx == sy else [sx, sy]
        if e["appearance"] in ("border_fill", "border_stroke"):
            e["border_level"] = ["letters", "words", "lines"][int(eget("BorderLevel") or 0)]
            e["extend"] = [plain(eget("BorderExtendX")), plain(eget("BorderExtendY"))]
            e["round"] = plain(eget("BorderRound"))
        if is_number(eget("ColorMode")) and eget("ColorMode") >= 0.5:
            stops = gradient_stops(eget("Gradient")) or []
            e["gradient"] = {"colors": {fmt_num(pos): list(color) for pos, color in stops} or
                             [e["color"], [plain(eget("EndRed")), plain(eget("EndGreen")), plain(eget("EndBlue"))]],
                             "angle": plain(eget("GradientAngle")),
                             "span": ["letters", "words", "lines", "text"][int(eget("MappingLevel") or 0)],
                             "scale": plain(eget("MappingSize")), "aspect": plain(eget("MappingAspect"))}
        elements[str(index)] = e
    spec["elements"] = elements
    tint = {c: plain(get(c)) for c in ("Red", "Green", "Blue") if is_number(get(c)) and get(c) < 0.999}
    if tint:
        spec["inputs"] = tint
    if is_number(get("MotionBlurEnable")) and get("MotionBlurEnable") >= 0.5:
        spec["motion_blur"] = {"shutter": plain(get("MotionBlurShutterAngle")), "quality": plain(get("MotionBlurSamples")),
                               "bias": plain(get("MotionBlurBias")), "spread": plain(get("MotionBlurSampleSpread"))}
    else:
        spec["motion_blur"] = False
    return spec


def cmd_to_spec(args):
    try:
        spec = preset_to_spec(args.file, load_inputs())
    except (OSError, ValueError) as exc:
        print(exc)
        return 1
    text = json.dumps(spec, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
        print("wrote %s" % args.out)
    else:
        print(text)
    return 0


# --------------------------------------------------------------------------- timing, folders, install

def cmd_timing(args):
    groups = args.groups or count_groups(args.text or "", args.by)
    print("groups: %d %s" % (groups, args.by))
    if args.span is not None:
        start, end, stagger = plan_row(args.start, args.span, args.delay or 0.0, groups)
        print("Start Frame %d, End Frame %d, Stagger %% %s" % (start, end, fmt_num(stagger)))
    else:
        end, stagger = args.end, args.stagger
        if end is None or stagger is None:
            print("give --span and --delay, or --end and --stagger")
            return 2
        start = args.start
    span, delay = row_window(start, end, stagger, groups)
    print("each %s moves for %.2f frames; the next starts %.2f frames later; the last one lands on frame %s"
          % (args.by[:-1], span, delay, fmt_num(round(start + delay * (groups - 1) + span, 2))))
    return 0


def resolve_settings_dir():
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(base, "Blackmagic Design", "DaVinci Resolve", "Support", "Fusion", "Settings")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "Blackmagic Design", "DaVinci Resolve", "Fusion", "Settings")
    return os.path.join(home, ".local", "share", "DaVinciResolve", "Fusion", "Settings")


def downloads_dir():
    return os.path.join(os.path.expanduser("~"), "Downloads", "Textizo Presets")


def cmd_where(_args):
    for label, path in (("resolve", resolve_settings_dir()), ("downloads", downloads_dir())):
        print("%-9s %s  (%s)" % (label, path, "exists" if os.path.isdir(path) else "will be created"))
    return 0


def cmd_install(args):
    data = load_inputs()
    target = {"resolve": resolve_settings_dir(), "downloads": downloads_dir()}.get(args.to, args.to)
    target = os.path.expanduser(target)
    status = 0
    for path in args.files:
        report = Report()
        try:
            tools, _ = find_textizo_tools(read_setting(path))
        except (OSError, ValueError) as exc:
            print("not installed: %s (%s)" % (path, exc))
            status = 1
            continue
        for name, tool in tools:
            check_tool(name, tool, data["inputs"], report)
        if not tools or report.errors:
            print("not installed: %s has errors; run the check command" % path)
            status = 1
            continue
        os.makedirs(target, exist_ok=True)
        dest = os.path.normpath(os.path.join(target, os.path.basename(path)))
        if os.path.exists(dest) and not args.overwrite:
            print("not installed: %s already exists (pass --overwrite or rename the preset)" % dest)
            status = 1
            continue
        shutil.copyfile(path, dest)
        print("installed: %s" % dest)
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Textizo preset helper: check, build, to-spec, timing, where, install.")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("check", help="check presets and print their timing")
    p.add_argument("files", nargs="+")
    p.add_argument("--frames", type=int, help="clip length in frames, to warn about rows that end after it")
    p.add_argument("--aspect", type=float, default=16.0 / 9.0, help="frame width / height (default 16:9; 0.5625 for 9:16)")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("build", help="write a complete preset from a JSON spec")
    p.add_argument("spec")
    p.add_argument("out", nargs="?", help='default: my-presets/"Textizo - <name>.setting"')
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--frames", type=int)
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("to-spec", help="turn a preset into a JSON spec")
    p.add_argument("file")
    p.add_argument("out", nargs="?")
    p.set_defaults(func=cmd_to_spec)
    p = sub.add_parser("timing", help="row timing calculator")
    p.add_argument("--text")
    p.add_argument("--groups", type=int)
    p.add_argument("--by", default="letters", choices=FOLLOWERS)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--span", type=float, help="frames each letter/word/line moves")
    p.add_argument("--delay", type=float, help="frames between one letter/word/line and the next")
    p.add_argument("--end", type=int)
    p.add_argument("--stagger", type=float)
    p.set_defaults(func=cmd_timing)
    p = sub.add_parser("where", help="print the folders presets can go to")
    p.set_defaults(func=cmd_where)
    p = sub.add_parser("next-name", help="the next free short preset name, like Textizo-07A")
    p.add_argument("--to", action="append", help="also look in resolve, downloads or a folder (repeat for several)")
    p.add_argument("--variant", type=int, help="number of an existing look: print its next free letter instead")
    p.set_defaults(func=cmd_next_name)
    p = sub.add_parser("install", help="copy checked presets to a folder")
    p.add_argument("files", nargs="+")
    p.add_argument("--to", required=True, help="resolve, downloads, or a folder path")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(func=cmd_install)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
