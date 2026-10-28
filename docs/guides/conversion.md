# Conversion guide: SRT, VTT, ASS

How to move subtitles between the three formats studios already have and IAC, in both directions, without inventing a centisecond or losing a colour channel. Normative time rules are spec §6; this guide is about the seams.

The reference linter ships one converter: `from-srt`. There are no flags on it, and no exporter — export mappings below are documented for you to implement, because an exporter's right behaviour depends on the target player.

## The five things that go wrong

1. **Rounding** milliseconds to centiseconds by truncation, which drags every cue earlier.
2. **Interval convention**: treating a closed end as exclusive (or the reverse), which moves boundaries by 1 cs and, at a touching boundary, renders two cues at once.
3. **ASS colour order**: `&HAABBGGRR` read as if it were `#RRGGBB`, which swaps red and blue.
4. **Multi-line text**: IAC has no newline inside a cue, and silently joining lines changes the reading of a sentence.
5. **Encoding**: SRT in the wild is not always UTF-8, and IAC only accepts UTF-8.

## Timestamps: round once, half up

IAC times are `HH:MM:SS:CC`, integer centiseconds. Convert from a source duration in seconds to centiseconds with **round half up**, on each endpoint independently:

```text
cs(ms) = (ms + 5) // 10              # SRT: milliseconds
cs(s)  = floor(s * 100 + 0.5)        # only if you must go through float seconds
cs(fr) = round_half_up(frames * 100 / fps)
```

For a frame-based source, do it in integers to avoid float error:

```text
cs = (frames * 100 * 2 + fps) // (2 * fps)
```

Two traps:

- **Language `round()` is usually half-to-even.** Python's `round(2.5)` is `2`, not `3`; C#'s `Math.Round(2.5)` is also `2` by default. Write half-up explicitly, as above, and test with `…5` endpoints.
- **Never round the duration and add it to the start.** Round start and stop, then check the interval. Rounding the length accumulates error across a cue list.

Then, and only then, apply the interval convention and clamp:

```text
if stop_cs <= start_cs: stop_cs = start_cs + 1
```

The clamp follows from spec §6.3–§6.4. It lengthens a degenerate cue by one centisecond rather than dropping it — a 4 ms cue becomes 10 ms. Report it: a source with sub-centisecond cues is usually broken upstream, and silently clamping hides that.

### Closed versus half-open: the 1 cs problem

IAC intervals are half-open: `[start, stop)`. A cue is visible at `start` and not at `stop`. Whether a source agrees depends on the tool, not the file extension:

| Source behaviour | What its end timestamp means | Conversion |
|---|---|---|
| End-exclusive — VTT by specification; SRT and ASS by common player behaviour | cue gone at `end` | copy: `stop = cs(end)` |
| End-closed — some in-house tools, frame-based pipelines, "last displayed frame" | cue visible at `end` | `stop = cs(end) + 1` |
| End is the last *displayed* frame at rate `fps` | visible through `end + 1/fps` | `stop = cs(end + 1/fps)` |

Getting this wrong costs exactly one centisecond per cue: cues end early (clipping the tail of a word) or end late (overlapping the next line that starts on the same boundary). At a touching boundary the late case produces two simultaneously visible cues — the symptom that gets reported as "double subtitles on fast dialogue".

Decide per source, not per file type: check one cue with a known audio transient. If you cannot determine it, prefer end-exclusive, which matches IAC's own semantics and every well-behaved player, and record the assumption in the converter's README.

## SRT → IAC

```text
1
00:00:01,000 --> 00:00:04,000
Hello there.

2
00:00:04,000 --> 00:00:06,250
Second line
```

- **Timing**: `HH:MM:SS,mmm` with a comma. Some files use a dot, some omit the hours — accept both, then normalise. Round to centiseconds.
- **Blocks**: index line optional in the wild; blank line separates cues. Text may span several lines.
- **Markup**: `<i>`, `<b>`, `<u>`, `<font color=...>`, and ASS leftovers such as `{\an8}` appear in real SRT files. All of it is markup, not text: strip it, and count stripping as loss.
- **Encoding**: SRT has no declared encoding. UTF-8 is common; Windows-1252, Shift-JIS, and GB18030 are all in circulation. Decode with a declared codec, never with a silent fallback. Output UTF-8 without BOM.
- **Grouping**: SRT has no tracks, so the importer must choose an `AudioName` per record. One record for the whole file is the minimal choice; one record per speaker is better if the file encodes speakers (usually it does not).

```bash
python tools/iac_lint.py from-srt dialogue.srt dialogue.iac
```

What the reference importer does, concretely: it reads UTF-8 (a BOM is tolerated), joins a multi-line cue's text with a single space, strips `<...>` tags, sorts cues by start, and writes one record named after the source filename with anything outside `A–Z a–z 0–9 _ -` replaced by `_`, colour `[#FFFFFF]`, and a `#!iac 1.0` marker. It decodes no legacy encodings — convert those to UTF-8 first. It has no grouping or colour options, so inspect the output and rename the track before shipping.

## VTT → IAC

```text
WEBVTT

intro
00:00:01.000 --> 00:00:04.000 line:85% align:center
<c.yellow>Hello</c> there.
```

- **Timing**: `HH:MM:SS.mmm`, hours optional, dot before milliseconds.
- **Header**: the first line must be `WEBVTT`; it is not part of the content. `NOTE`, `STYLE`, and `REGION` blocks are metadata, dropped.
- **Cue settings** (`line:`, `position:`, `size:`, `align:`, `region:`) and **cue identifiers** (`intro`) have no IAC equivalent. Dropped.
- **Markup**: `<c.class>`, `<i>`, `<b>`, `<v Speaker>`, `<ruby>`, and entities. Decode entities (`&amp;`, `&lt;`, `&gt;`, `&nbsp;`), strip tags. A `<v Speaker>` voice span is the one piece of structure worth keeping: use the speaker name as the `AudioName` when you split into tracks, since 1.0 has no separate speaker field.
- **Cue order**: VTT does not require cues in time order, while IAC requires non-decreasing starts within a record (E019). Sort on import, and do not assume the file was sorted.

## ASS / SSA → IAC

```text
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,Alice,0,0,0,,{\i1}Hello{\i0}\Nthere
```

- **Timing**: `H:MM:SS.cc` — one-digit hour, **already centiseconds**. Pad the hour to two digits and copy the rest; no rounding at all. ASS is the one source where IAC gains nothing in precision.
- **Text**: strip `{...}` override blocks. `\N` and `\n` are hard and soft line breaks, `\h` is a non-breaking space. `\k`, `\kf`, `\ko` carry per-syllable karaoke timing, which IAC cannot represent — dropped, loudly.
- **Fields**: `Layer` is z-order, dropped; `Style` and `Name` (actor) are the useful grouping keys; `Margin*` and `Effect` are layout and karaoke, dropped.
- **`Comment:` events**: an ASS file carries two event kinds, `Dialogue:` and `Comment:`. A `Comment:` event is retained-but-hidden, which is exactly what `#!cut` is: import it as a `#!cut` line and the round trip survives. Losing it is a silent content loss, not a formatting detail.
- **Grouping**: one record per `Name` when it is non-empty and unique, otherwise per `Style`, otherwise one record for the file. Pick one policy and document it — the choice is not recoverable from the output, so make it visible in the track names.

### Colour

ASS stores `&HAABBGGRR`: alpha, then blue, green, red — the reverse of CSS. Split the hex into pairs, drop the alpha pair, then reverse what is left:

```text
&H00FF8040
  AA BB GG RR
  00 FF 80 40
  discard AA -> FF 80 40
  reverse pairs -> 40 80 FF
  -> #4080FF
```

So `#RRGGBB` is built as `RR = last pair`, `GG = middle pair`, `BB = first pair`.

- **Alpha**: `00` is fully opaque and `FF` fully transparent (inverted from CSS). 1.0 has no alpha (E021 rejects `#RRGGBBAA`), so a translucent subtitle cannot be represented. Dropping alpha silently changes what the viewer sees; warn on any `AA != 00` and let the author decide whether to pick the nearest opaque colour.
- **Back to ASS**: reverse it — `&H00` + `BB` + `GG` + `RR`, uppercase hex, no `#`.

## IAC → SRT / VTT / ASS

The reference tool does not export. If you write one, these are the decisions it should make explicitly, next to a comment saying it made them.

- **Flatten tracks.** SRT and VTT have no track concept: emit every recorded cue into one list, sorted by start. Two records that overlap in time become two overlapping blocks in the output. If your target player cannot stack cues, you have to choose which track wins — that is a product decision, not a format one.
- **Target shapes.** Each format wants a different skeleton, and getting it wrong is the usual reason an export "does not load":
  - *SRT*: a numeric index, then `HH:MM:SS,mmm --> HH:MM:SS,mmm`, then text lines, then a blank line.
  - *VTT*: `WEBVTT`, a blank line, then optional cue id and `HH:MM:SS.mmm --> HH:MM:SS.mmm`, then text. A text line break becomes either a second cue line (VTT allows it) or a space; pick the one that matches your master.
  - *ASS*: `[Script Info]` with `ScriptType: v4.00+`, a `[V4+ Styles]` block with one style per record carrying its colour in `PrimaryColour` as `&H00BBGGRR`, and `[Events]` with a `Format:` line and one `Dialogue:` per cue, times written `H:MM:SS.cc`.
- **Retired lines are not cues.** A `#!cut` line must never render and is not part of a subtitle export. SRT and VTT have no hidden construct, so drop retired lines there. ASS does: write them as `Comment:` events, which players ignore and which the ASS importer in this guide maps back to `#!cut`. If you drop them instead, the `.iac` file stays the master.
- **Colour**: SRT/VTT can carry it as `<font color="#RRGGBB">`, which is not standard but is widely honoured. ASS needs a style, not an inline colour. Default to dropping colour and say so; an export that silently repaints dialogue is worse than one that loses the colour.
- **`Type`**: no target field. Dropping it loses the distinction between lyrics and dialogue; if the consumer needs it, encode it in the track name or the style name, and document the convention.
- **Text**: decode IAC escapes (`\"` → `"`, `\\` → `\`), emit the target's markup as plain text. SRT needs no escaping. VTT needs `&` `<` `>` as entities. ASS treats `{` and `}` as override syntax, so literal braces in dialogue need the target's own escaping or a styling-free fallback — check it in the player you ship to, not in the format documentation.
- **Interval**: if the target is end-exclusive, copy the stop; if the target renders the stop frame inclusively, subtract one centisecond. Test at a touching boundary, not in the middle of a cue.

## Lossiness table

| Feature | SRT → IAC | IAC → SRT | VTT → IAC | IAC → VTT | ASS → IAC | IAC → ASS |
|---|---|---|---|---|---|---|
| Text content | kept | kept | kept after entity decode | needs re-escaping | kept after tag strip | kept |
| Per-cue timing | 1 cs, rounded | exact | 1 cs, rounded | exact | exact (cs) | exact |
| Half-open boundaries | depends on source | direct | depends on source | direct | depends on source | direct |
| Track grouping | collapsed to one | flattened | collapsed / by voice | flattened | by Name or Style | per-record styles |
| Colour | rarely present | optional `<font>` | not present | optional `<font>` | `&HAABBGGRR`, alpha lost | via styles |
| Multi-line text | joined or split | joined | joined or split | joined | joined (`\N`) | from multiple cues |
| Inline styling (italic, bold) | lost | not emitted | lost | not emitted | lost | lost |
| Position and layout | lost | not emitted | lost (settings) | lost (settings) | lost | lost |
| Speaker / voice | lost | not emitted | lost unless used as track name | not emitted | lost unless used as track name | not emitted |
| Karaoke syllable timing | — | — | — | — | lost | lost |
| Retired lines (`#!cut`) | — | dropped | — | dropped | `Comment:` → `#!cut` | `Comment:` or dropped |
| Cue identifiers | lost | not emitted | lost | not emitted | lost | lost |
| Comments and directives | — | dropped | — | — | — | — |

Reading the table: the "kept" rows are why IAC is a good master format, and the "lost" rows are why it is not a rendering format. If you need styling or layout, keep it in ASS/VTT and treat IAC as the text-and-timing master. Two masters in one pipeline is a known failure mode; choose one and generate the other.

## What round-trips

Exactly: text, centisecond timing, half-open intervals, track names, and retired `#!cut` lines — the last only when the other end has a hidden construct, which in practice means ASS `Comment:` events and IAC itself. Through SRT or VTT, everything in the "lost" rows is gone; a round trip is a one-way quality gate, not a fidelity test.

## Draft-era files

Records written against the 1.0-draft carry a fourth boolean field. The rewrite is mechanical and total:

| Old | New |
|---|---|
| `NAME : {…} : [#RRGGBB] : true` | `NAME : {…} : [#RRGGBB]` |
| `NAME : {…} : [#RRGGBB] : true : Music` | `NAME : {…} : [#RRGGBB] : Music` |
| `NAME : {…} : [#RRGGBB] : false` | `#!cut NAME : {…} : [#RRGGBB]` |
| `NAME : {…} : [#RRGGBB] : false : Music` | `#!cut NAME : {…} : [#RRGGBB] : Music` |

```bash
python tools/iac_lint.py migrate old-draft.iac
python tools/iac_lint.py migrate content/
```

The command rewrites in place, only touches records whose fourth field is the literal `true` or `false`, and is idempotent: run it twice and the second run reports nothing to do. It then re-parses and canonicalises the result when the file is clean; if errors remain, it keeps the migrated text and prints them so you can fix and `fmt`.

`true` and `false` are also valid `Type` tokens, so the old field and a new type are syntactically identical. Migrate resolves that in favour of the old field; if a file genuinely used `Type` = `true`, rename that type before migrating.

Test the seams with [examples/multi-subtitles.iac](../../examples/multi-subtitles.iac) (touching cues, a retired line) and [examples/music.iac](../../examples/music.iac) (chained lyric cues) rather than with a file you wrote yourself — those two were authored for exactly these boundaries. Conformance cases in [testdata/](../../testdata/) cover the interval rule directly.
