# FAQ

Short answers to the questions that come up in every format discussion. Where an answer is a decision, it links to the RFC that made it.

## Why not JSON?

Because the primary consumer is a person editing one line and a reviewer reading a diff, not a program. JSON puts one cue across a dozen lines, requires `\"` escaping for ordinary dialogue, and produces diffs dominated by braces and commas rather than by the sentence that changed. It also has no comment syntax, so the version marker and directives would need a schema rather than a comment namespace.

IAC is not a data-interchange format. Turning a record into an object is a five-field mapping; turning a JSON cue tree back into readable subtitles is where the work is. If your pipeline is machine-to-machine, by all means use JSON — and convert at the boundary.

## Why not SRT or ASS?

SRT is a fine delivery format and a weak source-of-truth format: no tracks, no standard colour, no way to mark a cut line as retained-but-hidden, no version marker, and a parser landscape where every tool guesses differently. ASS is a rendering format with positioning, styles, and per-syllable karaoke — excellent at playback, poor at review, and its text handling is a markup language of its own.

IAC is meant to be the master you edit and translate, with SRT/ASS generated from it. It is not trying to replace them at playback; see [comparison.md](comparison.md) for where that costs it.

## Why ` : ` as the separator?

It is the separator the format already had, so changing it would break every existing file, and it is visually distinct from the colons inside `HH:MM:SS:CC` because times carry no spaces. Its real problem was never the sequence itself — it was that the draft split on it blindly, then tried to forbid it in content. 1.0 splits only at top level, outside quotes and braces ([RFC 0001 §D1](../rfcs/0001-standardize-iac-1.0.md#d1--the-separator-is-quote-aware-not-textual)), so ` : ` inside dialogue is just text.

## Why centiseconds and not milliseconds?

Because 10 ms is already finer than a frame at any practical rate (24–60 fps is 17–42 ms), so milliseconds would add two digits of precision that subtitle timing does not have. Shorter fields mean shorter lines, clearer diffs, and no pretence of accuracy that no one measured. It also keeps `CC` a two-digit field, which makes the time token fixed-width and cheap to validate.

The fourth component is not a frame count and must never be read as one — [spec §6](../spec/iac-1.0.md) states this as a requirement, not a convention.

## Does it support frames?

No. Nothing in the format carries or infers a frame rate. From a frame-based source, convert once:

```text
cs = round_half_up(frames * 100 / fps)
```

then clamp so the stop is after the start. The formula and the rounding rules are in [conversion.md](guides/conversion.md#timestamps-round-once-half-up). Authoring frame-exact cue points belongs in your animation or audio tool, not in the text file.

## Why not a schema-first format?

The interesting rules here are lexical and temporal: quote-aware field splitting, two escapes, half-open intervals, component ranges. A schema language models data shape, not scanning, so it would have to hand those rules back to prose anyway. What is left — three required fields, one optional one, one entry shape — fits in ABNF, which is at [spec/iac.abnf](../spec/iac.abnf), with the registered values in [registry/types.md](../registry/types.md).

The trade-off is real: a schema would give generated bindings in more languages. With three fields and one entry type, generating a parser costs more than reading [the parser guide](guides/parsing.md).

## Is it only for games?

It was designed in game dialogue: an `AudioName` per recorded line, `#!cut` comments for cut lines, and a `Music` track for lyrics. That origin is why tracks are named after audio assets rather than after scenes.

Nothing in the format is game-specific. Any production with several audio tracks, a script that keeps changing, and a localisation handoff fits — film, series, e-learning, live events with pre-rendered captions. What is game-specific is the ecosystem: the reference tooling and the published examples come from one game codebase, and no non-game adopters exist yet.

## Can I put newlines in text?

No. A record is one physical line; `\n` is not an escape (only `\"` and `\\` are), and `CR`/`LF` are line terminators. Control characters other than a tab are forbidden in text entirely (E026).

For a two-line subtitle, choose deliberately:

- **Join with a space** — one cue, faithful wording, flattened layout.
- **Split into two cues** — separate entries, with overlapping intervals if they must show together. Overlap is legal: renderers must display every entry of a record, and linters warn W002 so you know it was intentional.

What you cannot do is paste the line break and hope a renderer reflows it. Line wrapping is a rendering decision that IAC does not carry; the trade-off is discussed in [conversion.md](guides/conversion.md).

## Why is colour required?

It was already required in the draft, and 1.0 kept it: field order is positional, so a required third field is what lets the optional fourth be unambiguous. Making colour optional would need a placeholder anyway, and a placeholder in a positional grammar is a worse answer than a boring default.

The format has no styling language, so colour is the single presentation attribute it carries, and requiring it removes the question "what does absent mean?". Teams that do not care write `[#FFFFFF]`. Alpha (`#RRGGBBAA`) is rejected rather than truncated (E021) — silently dropping it repaints dialogue, which is the one failure mode worse than a parse error.

## What about right-to-left and vertical text?

Text is stored as logical-order Unicode with no direction field. A renderer applies the Unicode bidirectional algorithm, or its platform's equivalent, using the text and the user's locale. That is the correct division: direction belongs to presentation, and inserting directional control characters into the text would make the string differ between locales and break translation matching.

Vertical layout is not representable in 1.0 — there is no writing-mode or layout field, and it is not on the 1.1 list. A consumer that needs vertical subtitles has to decide it at render time. If vertical text is a hard requirement for you, that is an RFC, not a workaround.

## What happens to a cut line?

It becomes a `#!cut` comment: the marker, one space, then the record exactly as it was. A parser must not yield it as a record, no renderer can display it, and the linter still checks it ([RFC 0002 §D4″](../rfcs/0002-remove-enabled-field.md#d4--a-retired-line-is-a-marked-comment-not-a-record)). It is the recording of a decision — the line was cut, but the translation, the timing, and the reason still exist, and restoring it is deleting one marker.

Practically:

- `fmt` keeps `#!cut` lines and rewrites their payload in canonical form.
- The payload must still be valid. A retired line with `stop <= start` is reported as W008, which names the underlying E018 — a warning on the line, not a broken file. That is deliberate: a retired line should not fail a build, and it should not silently rot either.
- Retired lines are exempt from the duplicate-`AudioName` check (E015), so cutting a line frees its name for a new recording.
- Exporters drop them, except to ASS, where a `#!cut` line can be written as a `Comment:` event that players ignore. Whether a retired line goes to translation is a studio decision, not a format rule.
- If you need to count them: `grep -c '^#!cut'`.

Why not a field? Because a line that does not render is indistinguishable from a line that is absent, so a required boolean was a value every consumer had to branch on and every author had to keep canonical. The comment keeps the same information, is greppable, and stays checked.
