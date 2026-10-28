# Parser implementation guide

How to read IAC, in the order a parser meets the problem. The normative rules are in [spec/iac-1.0.md](../../spec/iac-1.0.md) — this guide is the implementation shape, not a second source of truth. Acceptance is the suite in [testdata/](../../testdata/), not agreement with this document.

A parser runs through the stages below in order: **bytes → lines → records → retired lines → file-level checks**. Each stage owns a different set of codes.

## Stage 0 — bytes

Read the whole file, then:

1. **BOM.** A leading `EF BB BF` is allowed on read and reported as W001. In producer mode — a converter, a formatter — emitting one is E001.
2. **UTF-8.** Decode strictly; invalid sequences are E001. Do not fall back to Latin-1 or CP936. A UTF-16 file with a `.iac` extension lands here, which is the common case.
3. **NUL.** Any `U+0000` is E001, BOM or not.
4. **Size.** More than 8 MiB is E025 in strict mode. Check before decoding if you want to bound memory.

Decode once, keep a flag for "BOM was present"; do not rewrite the string.

## Stage 1 — lines

Split on `LF`, `CRLF`, or a lone `CR`. All three are legal input; serializers emit `LF`. Do not `splitlines()` if your language's version also splits on `U+2028`, `U+0085`, or form feed — those must not become line boundaries (form feed inside text is E026).

A trailing empty element after a final terminator is not a line. Track whether the last physical line had a terminator; if not, W003.

Each line is then classified **in this order** (§2.3):

| Order | Test | Action |
|---|---|---|
| 1 | line 1, after an optional BOM, begins `#!iac` | version marker (§3.3) |
| 2 | begins `#!cut` | retired record (§5.4): a comment, not a record |
| 3 | begins `#@` | directive (§3.4), W006 on unknown or duplicate |
| 4 | begins `#` | comment, skip |
| 5 | empty, or SPACE/TAB only | blank line, skip |
| 6 | anything else | record line |

Order matters only where the tests overlap: every marker, retired line, and directive also begins `#`, and a `#!iac` line that is not on line 1 is an ordinary comment. The whitespace test comes after the `#` test so that a comment containing only spaces is still a comment.

The version marker is only a version marker on the first line after an optional BOM. A `#!iac` line anywhere else is a comment — a parser must not reject the file, but a linter SHOULD report W006, because a misplaced marker is almost certainly a mistake. If `MAJOR` is greater than yours, fail the file with E024; if `MINOR` is greater, warn W007 and continue (§3.3, §11).

`#!cut` is a line construct, not a directive: it does not live in the `#@` namespace and takes no name. Test it before the generic comment branch, or every retired line silently becomes prose.

## Stage 2 — the quote-aware scanner

A record is split on ` : ` **only when brace depth is 0, bracket depth 0, and no quote is open** (§3.5). `"Chapter : The Fall"` produces one field, not two. A plain `line.split(" : ")` is wrong in a way that only shows up on real dialogue, so implement the scanner and test it against quoted colons before anything else.

### States

| State | Entered by | Meaning |
|---|---|---|
| `DEFAULT` | start; `"` closed; `}`/`]` back to depth 0 | top level, separator is active |
| `IN_TEXT` | `"` at depth 0 or inside braces | between quotes; every character is content |
| `ESCAPE` | `\` inside `IN_TEXT` | exactly one character follows |
| `IN_BRACES` | `{` at depth 0 | inside the subtitle set; `brace` ≥ 1 |
| `IN_BRACKETS` | `[` at depth 0 | inside the colour field; `bracket` ≥ 1 |

`IN_TEXT` is shared: a quote can open inside `IN_BRACES`, and returning from it must restore the previous state, not `DEFAULT`. Keep a small stack or two booleans (`in_braces`, `in_brackets`) plus `in_text`; the "state" is just the tuple.

Depth is tracked even though the 1.0 grammar does not nest braces or brackets. It exists so that a malformed line cannot desynchronise the split: a stray `{` inside the cue set increments rather than swallows the rest of the line.

### `split_fields(line)`

```text
fields   = []
start    = 0
i        = 0
in_text  = false
escaped  = false
braces   = 0
brackets = 0

while i < len(line):
    ch = line[i]

    if in_text:
        if escaped:
            if ch != '"' and ch != '\\':
                fail(E011, at i)
            escaped = false
        elif ch == '\\':
            escaped = true
        elif ch == '"':
            in_text = false
        # every other character, including ':', is content
        i += 1
        continue

    if ch == '"':
        in_text = true
    elif ch == '{':
        braces += 1
    elif ch == '}':
        braces = max(braces - 1, 0)
    elif ch == '[':
        brackets += 1
    elif ch == ']':
        brackets = max(brackets - 1, 0)
    elif not braces and not brackets and line.startswith(' : ', i):
        fields.append(line[start:i])
        i += 3
        start = i
        continue

    i += 1

if in_text:
    fail(E010)
fields.append(line[start:])
return fields
```

Then:

```text
if len(fields) not in (3, 4):   fail(E012)
if braces or brackets:          fail(E012)   # structural failure; see note
```

An unbalanced `{` or `[` at end of line means the line never returned to top level, so the split is not trustworthy. Reporting E012 is honest — the fields you would report are not fields. If the split succeeded but a brace is unbalanced, the field-level parser (E020 for the cue set, E021 for colour) will catch it; either way, do not accept the line.

Note what the scanner does **not** do: it does not validate. `AudioName` containing `[` is E014 at the field stage, not a scanner error. ` : ` inside a track name silently becomes a field boundary — which is exactly why `AudioName` may not contain it.

## Stage 3 — fields

### Field 1, `AudioName`

Rules in §4.2 and §5.1. Validate: non-empty (E013); no ` : `, `"`, `{`, `}`, `[`, `]` (E014); does not start with `#` (E014, though such a line is a comment first — see [errors.md](../reference/errors.md)); at most 256 code points (E025).

Check uniqueness across the whole file, not per line: a second record with the same name is E015.

### Field 2, the cue set

Strip exactly one outer `{` and `}` — but verify they are the outer pair, not two characters inside text. Because the scanner already tracked depth, field 2 either begins and ends with matching braces or the file is malformed.

- Empty or whitespace-only body is E020 — `{}` and `{ }` are both empty.
- Split entries on `,` **outside text**, then skip surrounding spaces. Canonical input has exactly one space after the comma; a lenient parser may accept any run of spaces or tabs and report W004.
- Each entry: `"` text `"` `|` start `-` stop `|`. Parse the quoted text with the same escape rules (E010, E011). Reject the control characters listed in §9 in text with E026 — tab is allowed.
- Times: exactly `HH:MM:SS:CC`, each component two ASCII digits, three colons. A mismatch is E016. Then range-check `HH` 00–99, `MM` 00–59, `SS` 00–59, `CC` 00–99 — E017.
- `stop > start` is E018.
- Cue starts must be non-decreasing within the record (E019). Equal is fine.
- Overlaps (`stop` of cue *n* > `start` of cue *n+1*) are legal; report W002 if you are a linter.

Convert times to integer centiseconds immediately: `cs = ((HH * 60 + MM) * 60 + SS) * 100 + CC`. Never parse to float seconds; never keep a `(hh, mm, ss, cc)` tuple as the value you compare.

### Field 3, colour

Must match `[#RRGGBB]`: brackets, `#`, exactly six hex digits, case-insensitive. Everything else is E021, including `[#FFF]` and `[#RRGGBBAA]`. Store the digits as written — §5.3 says the value is compared case-insensitively and preserved, so do not normalise case on read.

### Field 4, `Type`

Optional. Absent means `Voice` (§5.5). Match case-insensitively against [registry/types.md](../../registry/types.md); serialise the canonical spelling. A well-formed unknown value is **not** an error: preserve it, warn W005. An empty token or one that cannot be a token at all — a trailing ` : `, a value containing a space — is E023.

A draft-era record that still carries the removed boolean looks like a record whose `Type` is `true` or `false`, because both match the type token grammar. It parses, with W005; it does not fail. Convert such files with `migrate` rather than by hand.

## Stage 4 — retired records

A line beginning `#!cut` followed by exactly one space and a record is a **retired record**. It is a comment for every purpose of parsing and rendering, but it is a comment the toolchain keeps checking.

```
#!cut Level1VO2 : {"A deleted line"|00:00:00:29-00:00:00:92|} : [#FFFFFF]
```

- A Parser MUST NOT yield it as a record, and a Renderer MUST NOT display it.
- A Linter SHOULD parse the payload as a record and, if that fails, report **W008** naming the underlying E-code — for example `W008 … (E018: …)`. The payload's E-codes must not be reported as file errors: a retired line cannot make an otherwise valid file invalid.
- `#!cut` **without** the space is an ordinary comment, not a malformed marker. `#!cut ` followed by a payload that is not a record is W008, and a payload that is a valid record but not canonical is W004.
- Retired records are **excluded from E015**. Cutting a line and later recording a new line under the same `AudioName` is a normal workflow, so the name may be reused.
- A formatter preserves a retired line in place: a valid payload is canonicalised, an invalid one is preserved verbatim rather than silently dropped.
- For the limits in §9, a retired line counts as a comment: it does not consume a record slot, but the file-size and line-length limits still apply.

If your parser exposes a data model, keep retired records in a separate list. Folding them into the record list gives you duplicate names, phantom tracks, and a renderer that has to re-check a flag that no longer exists.

## Stage 5 — file-level

After all records are parsed:

- duplicate `AudioName` → E015, exact and case-sensitive, checked here if you want a single pass over the record list, and **live records only**: retired records are exempt;
- zero records → legal (§2.3); a Producer SHOULD NOT emit such a file, but a parser must not reject it, and a file containing nothing but `#!cut` lines is still a file with zero records;
- limits (§9) → E025: 10 000 records, 64 KiB per line, 8 MiB per file, counted as §9 defines them (bytes for file and line, code points after escape processing for text).

`E027` — trailing content after the last field — is field 4 (`Type`) followed by whitespace and more content: `Music extra`, or a comment glued to the record. It is not what you get for a fifth separator: five or more fields is E012, and a token that is not a type token at all, such as `!Music`, is E023.

## Time model

An interval is half-open: **`[start, stop)`** (§6.3).

```text
visible(t) := start <= t < stop
```

Consequences worth encoding in a test:

- Chained cues at a touching boundary work: cue A `[100, 300)`, cue B `[300, 600)`. At `t = 300`, B is visible and A is not. No overlap, no gap, no `+1` fudge.
- Concatenating two files cannot invent an overlap, because the last cue's stop and the next file's first start are compared with `<`.
- A zero-length interval is impossible: E018 forbids it.
- Duration is `stop - start` in centiseconds, integer.

From frame-based sources (§6.4): `cs = round(frames * 100 / fps)`, then clamp so `stop > start`. Use round-half-up, not truncation — truncating drifts a cue earlier by up to a centisecond per conversion, and conversion chains compound it. See [conversion.md](conversion.md).

## Canonical serialisation

`fmt` output must be byte-identical to what §7 describes, or golden tests and diffs are worthless:

- `#!iac` and directives and comments pass through verbatim and in order; records are rewritten;
- one record per line: `AudioName : {cues} : [#RRGGBB][ : Type]`;
- `#!cut` lines preserved as `#!cut ` + the canonical record, so a retired line stays retired and stays valid;
- exactly ` : ` between fields, exactly `, ` between cues;
- no leading or trailing whitespace, and none adjacent to a separator;
- cues sorted by start, non-decreasing, stable for equal starts;
- records in their original order — sorting records is not part of canonical form;
- `Type` omitted when it is `Voice`; registered values in canonical spelling; unregistered values preserved as received;
- escape only `\` and `"`; never escape anything else, never leave an avoidable escape in place;
- times re-rendered from centiseconds, zero-padded, `CC` never rounded;
- colour digits preserved as read;
- UTF-8, no BOM, `LF` endings, exactly one trailing newline.

Sort is a stability requirement, not a nicety: two cues with the same start must not swap between runs, or every `fmt` produces a diff. Record order is the opposite rule: reordering records would reorder somebody's script, so it is forbidden.

## Error mapping

| Where | Condition | Code |
|---|---|---|
| bytes | invalid UTF-8, NUL, BOM in producer mode | E001 |
| bytes | BOM tolerated on read | W001 |
| scanner | end of line inside text | E010 |
| scanner | `\` + anything but `"` or `\` | E011 |
| scanner | field count not 3 or 4; unbalanced braces/brackets | E012 |
| field 1 | empty | E013 |
| field 1 | structure character, or leading `#` | E014 |
| file | duplicate `AudioName` among live records | E015 |
| cue | time is not `HH:MM:SS:CC` | E016 |
| cue | component out of range | E017 |
| cue | `stop <= start` | E018 |
| cue | start order decreasing | E019 |
| cue set | empty `{}` | E020 |
| field 3 | colour malformed or 8-digit | E021 |
| field 4 | `Type` token malformed | E023 |
| lines | `#!iac` major unsupported | E024 |
| any | §9 limit exceeded | E025 |
| cue | forbidden control character in text | E026 |
| record | trailing content after last field | E027 |
| cue set | overlapping cues (legal) | W002 |
| file | missing final newline | W003 |
| any | non-canonical casing/whitespace accepted | W004 |
| field 4 | unknown `Type` | W005 |
| directives | unknown or duplicate `#@` | W006 |
| lines | newer minor version | W007 |
| retired line | `#!cut` marker or payload malformed | W008 |

When one line has several defects, report the first stage that fails for it, in the order §8.2 fixes. Continuing to report later codes is allowed, but a cascade of secondary codes from one structural error is worse than one accurate code.

## Migrating draft-era files

The 1.0-draft had a fourth boolean field. `python tools/iac_lint.py migrate <file-or-dir>` performs the rewrite: `: true` is dropped, `: false` becomes a `#!cut` line, and a trailing `Type` moves up into field 4. The four mappings are tabulated in [conversion.md](conversion.md#draft-era-files).

Two properties matter if you implement it yourself:

- **Idempotent.** It rewrites a record only when field 4 is the literal `true` or `false`; a record whose fourth field is already a type token is left alone, so a second run changes nothing.
- **Ambiguous by nature.** `true` and `false` are valid `Type` tokens, so the old boolean and a new `Type` are syntactically identical. Migrate treats the literal boolean as the old field, which is the only reading that helps; a file that genuinely used `Type` = `true` must have that value renamed first.

After migration the tool re-parses and, when the file is clean, rewrites it in canonical form. If errors remain, the migrated text is kept and the errors are reported — fix them, then run `fmt`.

## Conformance

`testdata/conformance.json` is normative (spec §1.2, RFC 0001 §D14). Each case names a file, an `expect` value — `ok`, `warning`, or `error` — and the exact set of codes a Parser must produce, compared as a set without regard to order. Claim conformance per role: **Producer**, **Parser**, **Renderer**. A tool that passes as Parser and fails as Producer is a formatter with a bug.

To claim Parser conformance:

1. Every case with `expect: ok` must parse with no code at all.
2. Every case with `expect: warning` must produce exactly its warning set, and no E code.
3. Every case with `expect: error` must produce exactly its code set. A different code is a failure — the codes are the contract, and the suite is built so each invalid case has one code.
4. Do not special-case the corpus: if a case looks wrong, that is a spec bug. Open an RFC rather than editing the case. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

Producer conformance additionally requires byte-identical canonical output (§7) for every valid case — format it, format it again, and the second pass must change nothing. Renderer conformance cannot be established by this corpus at all: it needs an independent test of §10, because a renderer can display nothing and still "pass" a parse test.
