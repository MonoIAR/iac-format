#!/usr/bin/env python3
"""Reference implementation of the IAC subtitle format, version 1.0.

Normative sources:
    rfcs/0001-standardize-iac-1.0.md   (decisions)
    spec/iac-1.0.md                    (normative text)

The point of this file is to be small enough that another implementer can read
it end to end and reproduce the behaviour. It is stdlib-only on purpose.

CLI:
    python tools/iac_lint.py validate <path>... [--json]
    python tools/iac_lint.py fmt <path>... [--check] [--stdout]
    python tools/iac_lint.py from-srt <input.srt> <output.iac> [--name NAME]
    python tools/iac_lint.py migrate <path>... [--check]

`validate` and `migrate` accept files or directories. `fmt` accepts files or
directories too: it rewrites them in place, `--check` reports without writing,
and `--stdout` prints a single file's canonical text instead of writing.

Exit codes: 0 clean, 1 warnings only, 2 errors.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

# --- Limits (spec §9) -------------------------------------------------------

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_LINE_CHARS = 64 * 1024
MAX_RECORDS = 10_000
MAX_TEXT_CHARS = 4_096
MAX_NAME_CHARS = 256
MAX_CS = 99 * 360000 + 59 * 6000 + 59 * 100 + 99  # 99:59:59:99

SUPPORTED_MAJOR = 1
SUPPORTED_MINOR = 0

REGISTERED_TYPES = {
    "voice": "Voice",
    "music": "Music",
    "sfx": "SFX",
    "narration": "Narration",
    "ui": "UI",
}
DEFAULT_TYPE = "Voice"

FORBIDDEN_TEXT_CHARS = set(
    [chr(c) for c in range(0x00, 0x09)]
    + [chr(0x0B), chr(0x0C)]
    + [chr(c) for c in range(0x0E, 0x20)]
    + [chr(0x7F)]
)

TIME_RE = re.compile(r"\A(\d{2}):(\d{2}):(\d{2}):(\d{2})\Z")
COLOR_RE = re.compile(r"\A\[#([0-9A-Fa-f]{6})\]\Z")
ENTRY_RE = re.compile(
    r'\A"((?:[^"\\]|\\.)*)"\|([^|]+)-([^|]+)\|\Z',
    re.DOTALL,
)
TYPE_RE = re.compile(r"\A[A-Za-z][A-Za-z0-9_-]*\Z")
TRAILING_RE = re.compile(r"\A([A-Za-z][A-Za-z0-9_-]*)[ \t]+(\S.*)\Z")
MAGIC_RE = re.compile(r"\A#!iac (\d+)\.(\d+)\s*\Z")
DIRECTIVE_RE = re.compile(r"\A#@([A-Za-z0-9_-]+) (.*?)\s*\Z")
LANGUAGE_RE = re.compile(r"\A[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*\Z")
SRT_TIME_RE = re.compile(
    r"\A(\d{1,3}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,3}):(\d{2}):(\d{2})[,.](\d{3})"
)

SEVERITY = {}


def _register_severities() -> None:
    for code in (
        "E001 E002 E003 E004 E005 E006 E007 E008 E009 E010 E011 E012 "
        "E013 E014 E015 E016 E017 E018"
    ).split():
        SEVERITY[code] = "error"
    for code in "W001 W002 W003 W004 W005 W006 W007 W008".split():
        SEVERITY[code] = "warning"


_register_severities()


# --- Model ------------------------------------------------------------------


@dataclass
class Diagnostic:
    code: str
    line: int
    column: int
    message: str

    @property
    def severity(self) -> str:
        return SEVERITY.get(self.code, "error")

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "line": self.line,
            "column": self.column,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"{self.line}:{self.column}: {self.severity} {self.code} {self.message}"


@dataclass
class Entry:
    text: str
    start: int  # centiseconds
    stop: int  # centiseconds

    def render(self) -> str:
        return f'"{escape_text(self.text)}"|{fmt_time(self.start)}-{fmt_time(self.stop)}|'


@dataclass
class Record:
    name: str
    entries: List[Entry]
    color: str
    type: str = DEFAULT_TYPE

    def render(self) -> str:
        # Canonical form sorts cues by StartTime (D11); parsing keeps source
        # order so that out-of-order input is still reported as E011.
        ordered = sorted(self.entries, key=lambda e: e.start)
        body = ", ".join(e.render() for e in ordered)
        line = f"{self.name} : {{{body}}} : [#{self.color}]"
        if self.type != DEFAULT_TYPE:
            line += f" : {self.type}"
        return line


@dataclass
class Document:
    records: List[Record] = field(default_factory=list)
    diagnostics: List[Diagnostic] = field(default_factory=list)
    # Preserved for `fmt`: ("comment"|"directive"|"record"|"blank", payload)
    blocks: List[Tuple[str, object]] = field(default_factory=list)

    @property
    def errors(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "error"]

    @property
    def warnings(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


# --- Time helpers -----------------------------------------------------------


def parse_time(raw: str) -> int:
    """Return centiseconds. Raises ValueError with a code-bearing message."""
    m = TIME_RE.match(raw)
    if not m:
        raise ValueError("E008")
    hh, mm, ss, cc = (int(g) for g in m.groups())
    if mm > 59 or ss > 59:
        raise ValueError("E009")
    return ((hh * 60 + mm) * 60 + ss) * 100 + cc


def fmt_time(cs: int) -> str:
    if cs < 0:
        raise ValueError("negative time")
    cc = cs % 100
    total = cs // 100
    ss = total % 60
    mm = (total // 60) % 60
    hh = total // 3600
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{cc:02d}"


# --- Text helpers -----------------------------------------------------------


def escape_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def check_text(text: str) -> Optional[str]:
    """Return an error code for the text payload, or None."""
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\":
            if i + 1 >= n:
                return "E003"
            nxt = text[i + 1]
            if nxt not in ('"', "\\"):
                return "E003"
            i += 2
            continue
        if ch in FORBIDDEN_TEXT_CHARS:
            return "E017"
        i += 1
    return None


def unescape_text(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n and text[i + 1] in ('"', "\\"):
            out.append(text[i + 1])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# --- Scanner ----------------------------------------------------------------


def split_top_level(line: str, sep_char: str) -> Tuple[List[str], str]:
    """Split on `sep_char` only outside quotes/braces/brackets.

    The record separator is the three-character sequence ` : `; the entry
    separator is `,` followed by optional spaces.

    Returns (parts, state) where state is one of:
        "ok"         the line was balanced and fully tokenized
        "quote"      a quoted string was never closed   -> E002
        "unbalanced" braces or brackets do not balance  -> E004
    """
    parts: List[str] = []
    start = 0
    i = 0
    n = len(line)
    in_quote = False
    escaped = False
    brace = 0
    bracket = 0

    while i < n:
        ch = line[i]
        if in_quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_quote = False
            i += 1
            continue
        if ch == '"':
            in_quote = True
            i += 1
            continue
        # A closer with no opener never makes depth negative (§3.5): it is a
        # character in the current field, handled by the field rules.
        if ch == "{":
            brace += 1
        elif ch == "}" and brace > 0:
            brace -= 1
        elif ch == "[":
            bracket += 1
        elif ch == "]" and bracket > 0:
            bracket -= 1
        elif ch == sep_char and brace == 0 and bracket == 0:
            if sep_char == ":":
                if i > 0 and i + 1 < n and line[i - 1] == " " and line[i + 1] == " ":
                    parts.append(line[start : i - 1])
                    start = i + 2
                    i += 2
                    continue
            else:
                parts.append(line[start:i])
                start = i + 1
                while start < n and line[start] == " ":
                    start += 1
                i = start
                continue
        i += 1

    parts.append(line[start:])
    if in_quote:
        state = "quote"
    elif brace != 0 or bracket != 0:
        state = "unbalanced"
    else:
        state = "ok"
    return parts, state


# --- Record parsing ---------------------------------------------------------


def parse_entries(raw: str, line_no: int, diags: List[Diagnostic]) -> List[Entry]:
    body = raw.strip()
    if not body:
        # An empty field 2 is an empty set, not a structural error (§4.1).
        diags.append(Diagnostic("E012", line_no, 1, "subtitle set is empty"))
        return []
    if not (body.startswith("{") and body.endswith("}")):
        diags.append(Diagnostic("E004", line_no, 1, "subtitle set must be wrapped in { }"))
        return []
    inner_raw = body[1:-1]
    inner = inner_raw.strip()
    if not inner:
        diags.append(Diagnostic("E012", line_no, 1, "subtitle set is empty"))
        return []
    if inner_raw != inner:
        diags.append(
            Diagnostic("W004", line_no, 1, "non-canonical whitespace inside the subtitle set")
        )

    chunks, state = split_top_level(inner, ",")
    if state == "quote":
        diags.append(Diagnostic("E002", line_no, 1, "unterminated quoted string"))
        return []
    if state == "unbalanced":
        diags.append(Diagnostic("E004", line_no, 1, "unbalanced braces or brackets"))
        return []
    canonical_inner = ", ".join(chunk.strip() for chunk in chunks)
    if inner != canonical_inner:
        diags.append(Diagnostic("W004", line_no, 1, "non-canonical spacing around an entry separator"))

    entries: List[Entry] = []
    for chunk in chunks:
        item = chunk.strip()
        if not item:
            diags.append(Diagnostic("E004", line_no, 1, "empty subtitle entry"))
            continue
        m = ENTRY_RE.match(item)
        if not m:
            if '"' in item and item.count('"') % 2 == 1:
                diags.append(Diagnostic("E002", line_no, 1, "unterminated quoted string"))
            elif re.match(r'\A"((?:[^"\\]|\\.)*)"\|[^|]*\|\Z', item, re.DOTALL):
                # Quoted text with a single region but no "-" separator: the
                # time region is missing or malformed (§4.3).
                diags.append(Diagnostic("E008", line_no, 1, "malformed time, expected HH:MM:SS:CC-HH:MM:SS:CC"))
            else:
                diags.append(
                    Diagnostic(
                        "E004",
                        line_no,
                        1,
                        'entry must be "text"|HH:MM:SS:CC-HH:MM:SS:CC|',
                    )
                )
            continue
        raw_text, raw_start, raw_stop = m.group(1), m.group(2), m.group(3)
        problem = check_text(raw_text)
        if problem == "E003":
            diags.append(Diagnostic("E003", line_no, 1, "invalid escape sequence in text"))
            continue
        if problem == "E017":
            diags.append(Diagnostic("E017", line_no, 1, "forbidden control character in text"))
            continue
        try:
            start = parse_time(raw_start)
            stop = parse_time(raw_stop)
        except ValueError as exc:
            code = str(exc)
            if code == "E009":
                diags.append(Diagnostic("E009", line_no, 1, "time component out of range"))
            else:
                diags.append(Diagnostic("E008", line_no, 1, "malformed time, expected HH:MM:SS:CC"))
            continue
        if stop <= start:
            diags.append(Diagnostic("E010", line_no, 1, "StopTime must be greater than StartTime"))
            continue
        text = unescape_text(raw_text)
        if len(text) > MAX_TEXT_CHARS:
            diags.append(Diagnostic("E016", line_no, 1, f"text longer than {MAX_TEXT_CHARS} characters"))
            continue
        entries.append(Entry(text=text, start=start, stop=stop))
    return entries


def parse_record(line: str, line_no: int, diags: List[Diagnostic]) -> Optional[Record]:
    fields, state = split_top_level(line, ":")
    if state == "quote":
        diags.append(Diagnostic("E002", line_no, 1, "unterminated quoted string"))
        return None
    if state == "unbalanced":
        diags.append(Diagnostic("E004", line_no, 1, "unbalanced braces or brackets"))
        return None
    if len(fields) < 3:
        diags.append(
            Diagnostic("E004", line_no, 1, f"expected 3 or 4 fields, found {len(fields)}")
        )
        return None
    if len(fields) > 4:
        # A fifth field is a structural error, not trailing content (§8.2).
        diags.append(
            Diagnostic("E004", line_no, 1, f"expected 3 or 4 fields, found {len(fields)}")
        )
        return None

    if any(f != f.strip() for f in fields):
        diags.append(Diagnostic("W004", line_no, 1, "non-canonical whitespace around a field"))

    name = fields[0].strip()
    if not name:
        diags.append(Diagnostic("E005", line_no, 1, "AudioName is empty"))
        return None
    if name.startswith("#"):
        diags.append(Diagnostic("E006", line_no, 1, "AudioName must not start with '#'"))
        return None
    for bad in '"{}[]':
        if bad in name:
            diags.append(Diagnostic("E006", line_no, 1, f"illegal character {bad!r} in AudioName"))
            return None
    if len(name) > MAX_NAME_CHARS:
        diags.append(Diagnostic("E016", line_no, 1, f"AudioName longer than {MAX_NAME_CHARS} characters"))
        return None

    entries = parse_entries(fields[1], line_no, diags)

    color_raw = fields[2].strip()
    if color_raw.startswith("[") and color_raw.endswith("]"):
        inner = color_raw[1:-1]
        if inner != inner.strip():
            diags.append(
                Diagnostic("W004", line_no, 1, "non-canonical whitespace inside the colour")
            )
            color_raw = "[" + inner.strip() + "]"
    m = COLOR_RE.match(color_raw)
    if not m:
        diags.append(Diagnostic("E013", line_no, 1, "colour must be [#RRGGBB]"))
        return None
    color = m.group(1)

    track_type = DEFAULT_TYPE
    if len(fields) == 4:
        type_raw = fields[3].strip()
        if not TYPE_RE.match(type_raw):
            if TRAILING_RE.match(type_raw):
                diags.append(
                    Diagnostic("E018", line_no, 1, "trailing content after the Type field")
                )
            else:
                diags.append(Diagnostic("E014", line_no, 1, "malformed Type token"))
            return None
        canonical = REGISTERED_TYPES.get(type_raw.lower())
        if canonical is None:
            diags.append(Diagnostic("W005", line_no, 1, f"unregistered Type {type_raw!r}"))
            track_type = type_raw
        else:
            if type_raw != canonical:
                diags.append(Diagnostic("W004", line_no, 1, f"non-canonical Type spelling {type_raw!r}"))
            track_type = canonical

    # Ordering and overlap, only over entries that parsed.
    ordering_failed = False
    for prev, cur in zip(entries, entries[1:]):
        if cur.start < prev.start:
            diags.append(Diagnostic("E011", line_no, 1, "entries are not ordered by StartTime"))
            ordering_failed = True
            break
    if not ordering_failed:
        for prev, cur in zip(entries, entries[1:]):
            if cur.start < prev.stop:
                diags.append(Diagnostic("W002", line_no, 1, "overlapping entries"))
                break

    return Record(name=name, entries=entries, color=color, type=track_type)


# --- Document parsing -------------------------------------------------------


def parse_text(text: str) -> Document:
    doc = Document()
    diags = doc.diagnostics

    size = len(text.encode("utf-8", errors="replace"))

    if text.startswith("\ufeff"):
        text = text[1:]
        diags.append(Diagnostic("W001", 1, 1, "file starts with a byte order mark"))

    # Encoding/content is stage 1 and the size limit is stage 12 (§8.2), so
    # E001 wins when a file trips both.
    if "\x00" in text:
        diags.append(Diagnostic("E001", 1, 1, "file contains a NUL byte"))
        return doc

    if size > MAX_FILE_BYTES:
        diags.append(Diagnostic("E016", 1, 1, "file exceeds 8 MiB"))
        return doc

    if text and not text.endswith(("\n", "\r")):
        diags.append(Diagnostic("W003", 1, 1, "file does not end with a newline"))

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    names = {}
    record_count = 0
    language_seen = False
    fatal = False

    for index, raw_line in enumerate(lines, start=1):
        if len(raw_line.encode("utf-8")) > MAX_LINE_CHARS:
            diags.append(Diagnostic("E016", index, 1, "line exceeds 64 KiB"))
            continue
        stripped = raw_line.strip()
        if not stripped:
            doc.blocks.append(("blank", None))
            continue

        # Line classification is on the first character, not on the trimmed
        # line (§2.3): an indented '#' is a record line, not a comment.
        if not raw_line.startswith("#"):
            if fatal:
                continue
            record_count += 1
            if record_count > MAX_RECORDS:
                diags.append(Diagnostic("E016", index, 1, f"more than {MAX_RECORDS} records"))
                break
            record = parse_record(raw_line, index, diags)
            if record is None:
                doc.blocks.append(("comment", raw_line))
                continue
            if record.name in names:
                diags.append(
                    Diagnostic(
                        "E007",
                        index,
                        1,
                        f"duplicate AudioName {record.name!r} (first seen on line {names[record.name]})",
                    )
                )
            else:
                names[record.name] = index
            doc.records.append(record)
            doc.blocks.append(("record", record))
            continue

        if raw_line.startswith("#!cut "):
            # A retired record: a comment that must still be a valid record
            # (§5.4). Parsed into a scratch list so its E-codes cannot
            # invalidate the file; a bare `#!cut` with no payload is just a
            # comment.
            payload = raw_line[len("#!cut ") :]
            scratch: List[Diagnostic] = []
            retired = parse_record(payload, index, scratch)
            fatal_errors = [d for d in scratch if d.severity == "error"]
            if retired is None or fatal_errors:
                code = fatal_errors[0].code if fatal_errors else "E004"
                message = fatal_errors[0].message if fatal_errors else "not a record"
                diags.append(
                    Diagnostic("W008", index, 1, f"retired record does not parse ({code}: {message})")
                )
                doc.blocks.append(("comment", raw_line))
            else:
                # A valid but non-canonical payload keeps its own warnings
                # (W004/W002/W005) instead of being reported as broken.
                for finding in scratch:
                    diags.append(Diagnostic(finding.code, index, finding.column, finding.message))
                doc.blocks.append(("retired", retired))
            continue

        if raw_line.startswith("#!iac"):
            m = MAGIC_RE.match(stripped)
            if index != 1:
                diags.append(Diagnostic("W006", index, 1, "version marker is not the first line"))
                doc.blocks.append(("comment", raw_line))
                continue
            if not m:
                # A first line that starts with "#!iac" but does not parse is an
                # ordinary comment, with no diagnostic (§3.3).
                doc.blocks.append(("comment", raw_line))
                continue
            major, minor = int(m.group(1)), int(m.group(2))
            if major != SUPPORTED_MAJOR:
                diags.append(
                    Diagnostic(
                        "E015",
                        index,
                        1,
                        f"file declares version {major}.{minor}, this parser supports {SUPPORTED_MAJOR}.x",
                    )
                )
                fatal = True
            elif minor > SUPPORTED_MINOR:
                diags.append(
                    Diagnostic(
                        "W007",
                        index,
                        1,
                        f"file declares newer minor version {major}.{minor}",
                    )
                )
            doc.blocks.append(("directive", raw_line))
            continue

        if raw_line.startswith("#@"):
            m = DIRECTIVE_RE.match(stripped)
            if not m:
                diags.append(Diagnostic("W006", index, 1, "malformed directive, ignored"))
                doc.blocks.append(("comment", raw_line))
                continue
            name, value = m.group(1), m.group(2)
            if name == "language":
                if language_seen:
                    diags.append(Diagnostic("W006", index, 1, "duplicate #@language directive"))
                elif not LANGUAGE_RE.match(value):
                    diags.append(Diagnostic("W006", index, 1, "invalid BCP-47 language tag"))
                language_seen = True
            else:
                diags.append(Diagnostic("W006", index, 1, f"unknown directive {name!r}, ignored"))
            doc.blocks.append(("directive", raw_line))
            continue

        # Remaining lines start with '#' and are plain comments (§3.2).
        doc.blocks.append(("comment", raw_line))

    return doc


def parse_file(path: str) -> Document:
    with open(path, "rb") as handle:
        data = handle.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        doc = Document()
        doc.diagnostics.append(
            Diagnostic("E001", 1, 1, f"file is not valid UTF-8 ({exc.reason} at byte {exc.start})")
        )
        return doc
    return parse_text(text)


# --- Rendering --------------------------------------------------------------


def render_canonical(doc: Document) -> str:
    """Serialise a parsed document in canonical form (§7).

    Comments and directives are written as they were read; blank lines keep
    their positions; only record lines are rewritten.
    """
    out: List[str] = []
    for kind, payload in doc.blocks:
        if kind in ("blank", "comment", "directive"):
            out.append("" if kind == "blank" else str(payload))
        elif kind == "record":
            out.append(payload.render())  # type: ignore[union-attr]
        elif kind == "retired":
            out.append("#!cut " + payload.render())  # type: ignore[union-attr]
    if not out:
        return ""
    return "\n".join(out) + "\n"


# --- SRT import -------------------------------------------------------------


def sanitize_name(stem: str) -> str:
    cleaned = "".join(ch if (ch.isalnum() or ch in "_ -") else "_" for ch in stem)
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        cleaned = "track"
    return cleaned[:MAX_NAME_CHARS]


def srt_timestamp_to_cs(hh: str, mm: str, ss: str, ms: str) -> int:
    return ((int(hh) * 3600 + int(mm) * 60 + int(ss)) * 1000 + int(ms) + 5) // 10


def from_srt(text: str, name: str) -> Record:
    """Convert SRT cues into a single IAC record.

    Text spanning several lines is joined with a single space; that loss is
    documented in docs/conversion.md.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    cues: List[Entry] = []
    blocks = re.split(r"\n\s*\n", normalized)
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        time_line_index = 0
        if "-->" not in lines[0]:
            time_line_index = 1
        if time_line_index >= len(lines):
            continue
        m = SRT_TIME_RE.match(lines[time_line_index].strip())
        if not m:
            continue
        start = srt_timestamp_to_cs(*m.group(1, 2, 3, 4))
        stop = srt_timestamp_to_cs(*m.group(5, 6, 7, 8))
        if start > MAX_CS or stop > MAX_CS:
            raise ValueError(
                f"cue {lines[time_line_index].strip()!r} is outside IAC's 00:00:00:00-99:59:59:99 range"
            )
        if stop <= start:
            stop = start + 1
        payload = " ".join(ln.strip() for ln in lines[time_line_index + 1 :])
        if not payload:
            continue
        payload = re.sub(r"<[^>]+>", "", payload)
        cues.append(Entry(text=payload, start=start, stop=stop))
    cues.sort(key=lambda e: e.start)
    return Record(name=name, entries=cues, color="FFFFFF")


# --- CLI --------------------------------------------------------------------


def iter_iac_paths(paths: Iterable[str]) -> Iterable[str]:
    for path in paths:
        if os.path.isdir(path):
            for root, _dirs, files in os.walk(path):
                for filename in sorted(files):
                    if filename.endswith(".iac"):
                        yield os.path.join(root, filename)
        else:
            yield path


def cmd_validate(paths: List[str], as_json: bool) -> int:
    results = []
    worst = 0
    errors = 0
    warnings = 0
    for path in iter_iac_paths(paths):
        doc = parse_file(path)
        severity = 0
        if doc.warnings:
            severity = max(severity, 1)
        if doc.errors:
            severity = 2
        worst = max(worst, severity)
        errors += len(doc.errors)
        warnings += len(doc.warnings)
        results.append(
            {
                "file": path,
                "ok": doc.ok,
                "records": len(doc.records),
                "diagnostics": [d.as_dict() for d in sorted(doc.diagnostics, key=lambda d: (d.line, d.column, d.code))],
            }
        )
        if not as_json:
            for diag in sorted(doc.diagnostics, key=lambda d: (d.line, d.column, d.code)):
                print(f"{path}:{diag}")
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif worst:
        # A clean run prints nothing: silence is success, and CI stays readable.
        print(f"{len(results)} file(s) checked: {errors} error(s), {warnings} warning(s)")
    return 2 if worst == 2 else worst


def cmd_fmt(paths: List[str], check: bool, to_stdout: bool) -> int:
    targets = list(iter_iac_paths(paths))
    if not targets:
        print("no .iac files found", file=sys.stderr)
        return 2
    if to_stdout and len(targets) != 1:
        print("--stdout needs exactly one file", file=sys.stderr)
        return 2
    worst = 0
    for path in targets:
        doc = parse_file(path)
        if doc.errors:
            for diag in doc.diagnostics:
                if diag.severity == "error":
                    print(f"{path}:{diag}", file=sys.stderr)
            worst = 2
            continue
        canonical = render_canonical(doc)
        with open(path, "r", encoding="utf-8", newline="") as handle:
            original = handle.read()
        if original == canonical:
            if to_stdout:
                sys.stdout.write(canonical)
            continue
        if check:
            print(f"{path}: not canonical")
            worst = 2
            continue
        if to_stdout:
            sys.stdout.write(canonical)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical)
        print(f"{path}: rewritten")
    return worst


def cmd_from_srt(source: str, target: str, name: Optional[str]) -> int:
    with open(source, "r", encoding="utf-8-sig") as handle:
        text = handle.read()
    track = sanitize_name(name or os.path.splitext(os.path.basename(source))[0])
    try:
        record = from_srt(text, track)
    except ValueError as exc:
        print(f"{source}: {exc}", file=sys.stderr)
        return 2
    if not record.entries:
        print(f"{source}: no cues found", file=sys.stderr)
        return 2
    output = "#!iac 1.0\n" + record.render() + "\n"
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(output)
    print(f"{source}: {len(record.entries)} cues -> {target}")
    return 0


def migrate_text(text: str) -> Tuple[str, int]:
    """Rewrite the pre-1.0 four/five field record into the current grammar.

    `: true` is dropped, `: false` becomes a `#!cut` retired record. Idempotent:
    a record whose fourth field is a Type token is left alone.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out: List[str] = []
    changed = 0
    for raw in lines:
        if not raw.strip() or raw.startswith("#"):
            out.append(raw)
            continue
        fields, state = split_top_level(raw, ":")
        if state != "ok" or not 4 <= len(fields) <= 5:
            out.append(raw)
            continue
        marker = fields[3].strip()
        if marker not in ("true", "false"):
            out.append(raw)
            continue
        kept = [field.strip() for field in fields[:3] + fields[4:]]
        line = " : ".join(kept)
        if marker == "false":
            line = "#!cut " + line
        out.append(line)
        changed += 1
    return "\n".join(out) + "\n", changed


def cmd_migrate(paths: List[str], check: bool) -> int:
    total = 0
    for path in iter_iac_paths(paths):
        with open(path, "rb") as handle:
            data = handle.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            print(f"{path}: not valid UTF-8, skipped", file=sys.stderr)
            continue
        new_text, changed = migrate_text(text)
        if not changed:
            print(f"{path}: nothing to migrate")
            continue
        total += changed
        if check:
            print(f"{path}: {changed} record(s) would be migrated")
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(new_text)
        doc = parse_file(path)
        if doc.errors:
            print(f"{path}: migrated {changed} record(s); the result still has errors:", file=sys.stderr)
            for diag in doc.errors:
                print(f"  {path}:{diag}", file=sys.stderr)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(render_canonical(doc))
            print(f"{path}: migrated {changed} record(s)")
    if check and total:
        return 2
    return 0


def usage() -> int:
    print(__doc__)
    return 2


def main(argv: List[str]) -> int:
    if not argv:
        return usage()
    command, rest = argv[0], argv[1:]
    if command == "validate":
        as_json = "--json" in rest
        paths = [a for a in rest if not a.startswith("--")]
        if not paths:
            return usage()
        return cmd_validate(paths, as_json)
    if command == "fmt":
        check = "--check" in rest
        to_stdout = "--stdout" in rest
        paths = [a for a in rest if not a.startswith("--")]
        if not paths:
            return usage()
        return cmd_fmt(paths, check, to_stdout)
    if command == "from-srt":
        name = None
        args = []
        i = 0
        while i < len(rest):
            if rest[i] == "--name" and i + 1 < len(rest):
                name = rest[i + 1]
                i += 2
                continue
            args.append(rest[i])
            i += 1
        if len(args) != 2:
            return usage()
        return cmd_from_srt(args[0], args[1], name)
    if command == "migrate":
        check = "--check" in rest
        paths = [a for a in rest if not a.startswith("--")]
        if not paths:
            return usage()
        return cmd_migrate(paths, check)
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
