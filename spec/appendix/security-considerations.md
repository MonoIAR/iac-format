# Security Considerations

- **Status:** Informative
- **Applies to:** IAC 1.0

This appendix expands §13 of `spec/iac-1.0.md`. It describes the threat model, the
properties that make IAC safe to parse, the resource limits an implementation must
enforce, and the residual risks that are outside the format.

## 1. Threat model

| Item | Assumption |
|---|---|
| Asset at risk | The application build, the user's device, the CI runner, and any system that displays the subtitle. |
| Attacker | Anyone who can supply an `.iac` file: a mod author, a localisation vendor, a user importing a file, a compromised asset pipeline. |
| Trust boundary | The file is untrusted. The parser and renderer are trusted code. |
| Attacker capability | Full control of file bytes, line order, field contents, sizes, encodings, and line endings. |
| Attacker goal | Code execution, file or network access, memory exhaustion, crash, or misleading displayed text. |

A conforming implementation MUST assume that every byte of every file is hostile.

## 2. Why the format cannot execute anything

IAC is a text format with no executable surface:

- There is no script, expression, template, macro, or interpolation syntax.
- There is no markup. Text is opaque and is displayed as stored (§10.5).
- There is no entity, character reference, or escape that resolves to another resource.
- There is no include, import, link, or attachment.
- There is no file path, URL, URI, protocol handler, or identifier that a parser must
  resolve. `AudioName` names an audio track for the application to map; the parser MUST
  NOT open a file for it.
- There is no metadata that selects a parser feature, codec, font, or renderer plugin.

Consequently, parsing an IAC file cannot by itself execute code, read a local file, make
a network request, or load a remote resource. The format has no mechanism for any of
those actions, so an implementation does not need a sandbox to parse it. This is a
property of the grammar, not a policy that implementations must remember.

## 3. External references and identifier resolution

The format deliberately contains no external references.

- `AudioName` is an opaque label. Applications that map it to an asset MUST validate it
  against their own allow-list; the format does not define a path, and a name is not a
  path. See §7.
- `#@language` is a BCP 47 tag used for informational purposes. It is not a locale
  file, a translation lookup, or a font selector.
- Unknown directives MUST be ignored (W006). A parser MUST NOT interpret an unknown
  directive as a request to load anything.
- Comments are ignored and MUST NOT be interpreted as configuration.

A parser therefore needs no filesystem or network access at all. An implementation that
opens a file or socket while parsing has introduced a capability the format does not
require.

## 4. Denial of service and resource limits

The limits in §9 exist to bound parser work and memory. They are the minimum a
conforming implementation must accept; an implementation may impose lower limits only
if it documents them, and must not reject a file within the minimum.

| Vector | Why it is bounded | Required mitigation |
|---|---|---|
| Huge file | 8 MiB accepted minimum | Enforce the limit while reading, not after buffering the whole file. |
| Very long line | 64 KiB accepted minimum | Reject at the limit. Do not build a token list from an unbounded line. |
| Many records | 10 000 accepted minimum | Bound the record table. |
| Many entries in one record | 4 096 accepted minimum | Bound the entry list; do not recurse per entry. |
| Long text | 4 096 code points per text | Bound after escape processing. |
| Long AudioName | 256 code points | Bound before duplicate detection. |

Specific attacks:

- **Long line without a separator.** The tokenizer must scan the whole line before it
  can conclude that the line has one field. With the 64 KiB line limit, this is bounded.
  An implementation MUST NOT scan a line repeatedly for each field; the tokenizer is
  single-pass.
- **Quadratic tokenization.** A naive implementation that splits on ` : `, then rescans
  each field, can be quadratic on adversarial lines. The required tokenizer is one
  left-to-right pass with three counters and a quote flag.
- **Backtracking regular expressions.** A regex that tries to match a full record with
  nested groups can be exponential on crafted text. Implementations SHOULD use the
  explicit state machine of §3.5 rather than a backtracking regex.
- **Duplicate detection.** A file with 10 000 records forces 10 000 AudioName
  comparisons if implemented naively. Use a hash set bounded by the record limit.
- **Diagnostic amplification.** One malformed line can produce many candidate errors.
  A Parser MAY stop at the first error per line; a linter SHOULD cap the number of
  diagnostics per file.
- **Log injection.** Text and AudioName may contain `\r`, `\n` is impossible, but other
  control characters and Unicode bidi characters are possible. A tool that echoes input
  in diagnostics SHOULD escape control characters before writing logs or terminals.

## 5. Parser implementation checklist

An implementation that claims Parser conformance SHOULD verify all of the following.

1. Decode UTF-8 with strict error handling; report E001 on any invalid sequence.
2. Reject `NUL` anywhere (E001).
3. Accept at most one leading BOM, ignore it, and report W001; a BOM elsewhere is data.
4. Strip exactly one line terminator per line; accept LF, CRLF, and CR.
5. Enforce the file, line, record, entry, text, and AudioName limits of §9.
6. Tokenize with the §3.5 state machine. Never split on a plain textual ` : `; treat a
   `#!cut` line as a comment and never as a record.
7. Bound brace and bracket depth, and require it to return to 0 at end of line; do not
   recurse.
8. Never resolve, open, fetch, or execute anything found in a field.
9. Validate field order and types before allocating large structures.
10. Preserve unknown Type values and retired records; never render a retired record.
11. Emit only the codes of §8 and do not leak stack traces or host paths in messages.
12. Apply the diagnostic order of §8.2 so results are deterministic.
13. A linter that parses `#!cut` payloads applies the same limits and state machine to
    each payload; a malformed payload is W008, not an exception or an error.

## 6. Renderer considerations

- Text is displayed as data. If the renderer embeds text in HTML, rich text, or a native
  UI markup language, it MUST escape it for that target. This is a renderer obligation,
  not a property of IAC: the format has no markup to interpret.
- A renderer MUST NOT fetch anything to display a cue. Fonts, images, and audio are
  application resources, not references from the file.
- A renderer MUST NOT display retired records (`#!cut` lines), including in debug
  overlays that a user can capture.
- Timing values are bounded by `99:59:59:99` = 359 999 999 cs, which fits in a signed
  32-bit integer; implementations SHOULD use 64-bit arithmetic when converting to
  seconds or nanoseconds.
- Overlapping entries MUST all be displayed; an attacker cannot hide a cue by
  overlapping it, and a renderer cannot use overlap to select one arbitrarily.

## 7. Residual risks

These are outside IAC 1.0 and must be handled by the application.

- **Asset mapping.** An application that turns `AudioName` into a file path, database
  key, or script event must treat it as untrusted key material. The format does not
  define the mapping and cannot make it safe.
- **Display of hostile text.** IAC can carry misleading or abusive text. Curation,
  moderation, and rate limiting are application concerns.
- **Localisation tooling.** A translation pipeline that rewrites the file must preserve
  the grammar; the format does not authenticate the producer.
- **Memory pressure from many valid files.** Limits are per file. A process that loads
  thousands of files must impose its own aggregate limit.
- **Side channels.** Parsing time can reveal the content of a file to an observer with
  fine-grained timing. This is not a practical concern for subtitles, but it is a
  general property of parsers.

None of these residual risks requires a capability inside the format, and none changes
the conclusion that an IAC file cannot execute anything.
