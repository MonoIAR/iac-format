# Rationale

- **Status:** Informative
- **Applies to:** IAC 1.0

This page records why the decisions in RFC 0001 were taken. It is not normative;
`spec/iac-1.0.md` is authoritative. Each section states the problem, the chosen rule,
the alternatives rejected, and the test hook that pins the decision.

## 1. Why the field separator is quote-aware (D1)

**Problem.** The 1.0-draft said "split the line on ` : `" and then tried to forbid the
sequence inside fields. That is an unenforceable constraint on content. A translator who
writes any of the following produces a file that no longer parses:

```
"Chapter : The Fall"
"他说 : 你好"
"Press Start : Continue"
```

Subtitles contain colons. A format that cannot represent its own subject is not a
format.

**Chosen.** Split on ` : ` only at brace depth 0, bracket depth 0, and outside a quoted
string. A parser tokenizes; it never uses a plain string split.

**Why it works.** All delimiters that matter are structural: `{}` delimits the subtitle
set, `[]` delimits the colour, and `"` delimits text. A colon inside any of those is
content. The state machine is three counters and a quote flag, and it is linear in the
line length.

**Rejected.**

- Escape every colon in text. Breaks every existing file and makes dialogue
  unreadable. The draft's own examples contain no escaped colons, so this would be a
  format change, not a clarification.
- Forbid ` : ` in text. Unenforceable at the content level; translators do not read
  grammar specifications.
- Quote only the text and use a different delimiter for fields. Already the case: text
  is quoted. The problem was the splitter, not the quoting.

**Consequence.** The grammar becomes total: every line either parses or has a code.
AudioName loses ` : `, `"`, `{`, `}`, `[`, `]` (it had no legitimate use for them), and
text gains every character. Existing files are a strict subset of valid 1.0.

**Test hooks.** `testdata/valid/colon-in-text.iac` proves the separator is not split;
`testdata/invalid/illegal-audio-name.iac` proves AudioName is still constrained.

## 2. Why intervals are half-open (D2)

**Problem.** The draft never said whether `StopTime` is inclusive. Two implementations
that both "follow the draft" can disagree by one centisecond on every cue, which is
visible as a flicker or a clipped syllable at every boundary.

**Chosen.** `[StartTime, StopTime)`: visible at the start, not visible at the stop, and
`StopTime` MUST be strictly greater than `StartTime`.

**Evidence.** `examples/music.iac` chains nineteen cues whose stop and next start are the
same value, for example `00:00:08:58-00:00:17:20` followed by
`00:00:17:20-00:00:25:99`. Under an inclusive stop, the boundary frame belongs to both
cues and a renderer must choose; under a half-open stop, it belongs to exactly one and
the file is simply correct.

**Consequence.** Concatenating two files cannot create a one-centisecond overlap from
touching boundaries. Cue arithmetic composes. Zero-length cues are impossible, so a
typo that swaps the times is caught (E010) rather than producing an invisible entry.

**Rejected.**

- Inclusive stop: forces every renderer to special-case boundaries and makes file
  concatenation produce overlaps.
- Allow `StopTime == StartTime` for instant events: an event that is never visible is
  not a subtitle. If a format needs instant markers, they are not subtitles.

**Test hooks.** `testdata/valid/touching.iac`, `testdata/invalid/stop-not-after-start.iac`.

## 3. Why centiseconds, not frames (D3)

**Problem.** `HH:MM:SS:FF` is SMPTE timecode, and `FF` means frames. IAC writes
`HH:MM:SS:CC` with a fourth component that looks identical. The draft calls it
"百分秒", but the shape invites every new reader to assume frames.

**Why that is dangerous.** The error is silent and scales with the frame rate. At 24 fps
a value read as frames runs 4% fast; at 30 fps it runs 20% fast; at 60 fps, 40%. The
audio is correct and the subtitles drift, which is the most expensive class of bug to
diagnose after localisation.

**Chosen.** `CC` is centiseconds, `00`–`99`, exactly two digits. It is not tied to any
frame rate, and a parser MUST NOT infer one.

**Conversion.** Importers use `cs = round(frames * 100 / fps)`, then clamp so that
`StopTime > StartTime`. The frame rate is an input to the importer and is not stored in
the file. This keeps one file valid for every display rate.

**Rejected.**

- Frames plus an `fps` field. Adds a second source of truth, invites mismatches between
  files, and forces every renderer to implement rate conversion.
- Milliseconds. Three fractional digits change the established shape and give precision
  no subtitle workflow needs.
- Floating-point seconds. Not deterministic across languages and runtimes; bad for
  golden tests.

**Test hooks.** `testdata/invalid/bad-time-shape.iac` (E008),
`testdata/invalid/time-range.iac` (E009), and the `CC` range in §6.1.

## 4. Why the Type set is open but registered (D6)

**Problem.** Type is a styling hint. A closed enumeration would force every studio that
needs `Ambient`, `Whisper`, or `Radio` to fork the format or mislabel the track. A
completely free-form string would prevent canonical output and cross-tool styling.

**Chosen.** Five registered values with canonical spellings (`Voice`, `Music`, `SFX`,
`Narration`, `UI`), case-insensitive matching, `Voice` as the absent default, and an
explicit rule for unknown values: preserve them, do not error, warn in a linter (W005),
and fall back to default styling in a renderer.

**Why it works.** The set is closed for *interoperability* (every tool understands the
five) and open for *authoring* (a studio can ship a new value today, and a later RFC can
register the ones that prove useful). An unknown Type degrades to default styling rather
than breaking the file, which is the same failure mode as an old parser meeting a new
value.

**Rejected.**

- Closed enumeration: every new value becomes a spec revision, so studios fork.
- Free-form with no registry: no canonical spelling, no shared meaning, no way for a
  renderer to style anything consistently.
- Type as a comment or directive: styling is per record, not per file, and must survive
  formatting.

**Consequence.** Type can never affect timing, text, or colour. It is a hint that a
renderer MAY use and MUST be able to ignore.

**Test hooks.** `testdata/valid/types.iac`, `testdata/valid/unknown-type.iac`,
`testdata/invalid/bad-type.iac`.

## 5. Why there is a magic comment (D7)

**Problem.** A file with no version marker cannot be evolved. Once 1.0 is deployed, any
new syntax is either silently misread by old parsers or rejected by them; neither is a
versioning strategy.

**Chosen.** An optional first line, `#!iac <MAJOR>.<MINOR>`, in the comment namespace.
Because it is a comment, a parser written against the draft ignores it and still reads
the file. A conforming parser reads it, rejects a newer major with E015, and warns but
continues on a newer minor (W007).

**Why the comment namespace.** Any non-comment header would break every existing parser
and every existing file. The comment namespace is the only place where a new line can be
added to a text format without changing what old readers see. The cost is one ignored
line.

**Why not make it required.** Existing files have no marker and are valid. Requiring one
would be a breaking change in a minor version, and would force every author to write
boilerplate before the first cue.

**Consequence.** New syntax can be introduced only through a major version, so old
parsers fail loudly rather than guessing. Minor versions may add only ignorable
constructs: comments, directives, and registry values.

**Test hooks.** `testdata/valid/versioned.iac`, `testdata/invalid/unsupported-major.iac`,
`testdata/valid/newer-minor.iac`.

## 6. Secondary decisions

- **Colour is required and alpha is rejected (D5).** Silently dropping an alpha channel
  produces visibly wrong colours. Rejecting `#RRGGBBAA` with E013 is loud, local, and
  fixable; truncating it would ship the wrong colour.
- **Exactly two escapes (D9).** "Preserve unknown escapes" makes one file mean different
  things in different tools. `\"` and `\\` cover subtitle text; everything else is E003.
- **Directives in `#@` (D8).** The namespace is reserved so file-scoped metadata can be
  added without a syntax change, and unknown directives are ignored with W006 so an old
  parser never fails on new metadata.
- **Deterministic canonical form (D11).** Golden tests, reviewable diffs, and `iac fmt`
  require one output for one input. Sorting cues and omitting `Voice` are the two choices
  that make output stable without reordering records.
- **Role-based conformance with a suite (D14).** "Both implement the spec" is not a
  testable claim. The three roles and `testdata/conformance.json` make disagreement
  visible, including the exact code for each malformed input.
- **Limits (D12).** "Unbounded" is not implementable. The numbers are far above any real
  subtitle file and let a parser size buffers before reading.

## 7. Why there is no `enabled` field

**Problem.** The draft made the fourth field a required boolean. No consumer needs it. A
renderer that must not display a cue cannot distinguish it from a cue that is absent;
localisation needs a workflow decision, not a per-line flag; build inclusion is decided by
which file is built. The field cost every author a separator and a value on every line,
and in practice it held one value.

**Chosen.** Remove the field. The record is
`AudioName : {cues} : [#RRGGBB] [: Type]`. A line kept for reference is marked `#!cut `
and is a comment for parsing and rendering. A linter parses the payload and reports W008
if it is not a valid record, so a cut line cannot rot into invalid syntax or a stale time
range while nobody is looking.

**Why not plain `#`.** A comment cannot be distinguished from prose; the superseded
draft's own examples include `# Format: Audio_name : {...} : [#Color]`, which automatic
detection would flag on every run. **Why not `#@cut`.** `#@` is file-scoped metadata;
`#!cut` is line-scoped and sits beside `#!iac` as "structured, not prose".

**Rejected alternatives.**

- Rename the boolean: no new consumer, still a constant.
- A `status` enum (`live`/`cut`/`alt`/`draft`): useful for a translation pipeline, but it
  keeps a required field that most files set to one value; line-level state belongs in a
  marker, a directive, or a sidecar file.
- Make the field optional: ambiguous with Type; a trailing optional field must be unique
  in kind.
- Reuse the slot as `duration`: duplicates data in the audio asset and invites drift.

**Consequence.** W008 is added, and the migration is mechanical. This changed before
1.0.0 was announced, so no version bump applies.

## 8. Questions people ask

**Why not JSON?** A subtitle file is read and reviewed as text. JSON would add escaping
to every quotation mark, forbid the natural one-line-per-track layout, and make a diff
unreadable. IAC needs no parser library and no schema to be legible.

**Why not a schema-first format?** The grammar is small enough to state in one page and
to test with a corpus. A schema would add a layer that has to be kept in sync with the
text without making any file easier to write.

**Is it only for games?** No. It fits anything where timed text is authored next to an
audio asset: interactive dialogue, cutscene subtitles, lyric tracks, tutorial voice-over.
The example set comes from a game because that is where the format was used first.

**What about right-to-left and vertical text?** The format stores Unicode code points and
says nothing about direction, shaping, or layout. A renderer applies its own bidi and
line-breaking rules; IAC neither encodes nor overrides them.

**Can text contain a newline?** No. LF and CR end the line, so a line break inside quoted
text is E002. Use a second cue when the text needs two display lines.
