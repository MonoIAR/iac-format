# RFC 0002 — Remove the `enabled` field; retired records are marked with `#!cut`

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-10-29
- **Supersedes:** RFC 0001 D4, and the `enabled` references in RFC 0001 D11, D13, D15 and §6
- **Target release:** 1.0.0 (not yet publicly announced)

## Abstract

RFC 0001 made the fourth field of a record a required boolean named `enabled`.
This RFC removes it. A record carries what is said and when; whether a line is
"active" is not information a consumer needs, because a line that does not render
is indistinguishable from a line that is absent. The slot is removed, the record
gets shorter, and the production state it encoded moves to an explicit,
machine-checkable comment form: `#!cut`.

## 1. Why the field is dead weight

The fourth field was introduced by the original draft as `Enabled`, described as
"自定义布尔值", and RFC 0001 gave it a definition without asking whether anything
consumes it.

Three consumers exist, and none of them needs the field:

| Consumer | What it actually needs | Does the field help? |
|---|---|---|
| Renderer | "do not display this cue" | No. A cue that is not displayed is equivalent to a cue that is not there. The renderer must branch on a constant. |
| Localisation tooling | which lines to translate | Only if cut lines must stay visible to the translator — a workflow question, not a format question. |
| Build pipeline | whether to include the line | No. Inclusion is decided by which file is built, not by a per-line flag. |

Meanwhile the field costs every author something on every line: one more ` : `,
one more value to keep canonical, one more thing a formatter must rewrite. A
required field that only ever holds `true` is a tax on the format.

The draft's own justification — "禁用（如已删除或暂不使用的台词）" — is a statement
about the *working file*, and the draft already had the right mechanism for it:
comments. RFC 0001 should have deleted the field then. This RFC corrects that.

## 2. Decision

### D4′ — The record has three required fields and one optional field

```
record = audio-name " : " subtitle-set " : " color [ " : " type ]
```

- Fields: `AudioName`, `Subtitles`, `Color`, and optionally `Type`. Three or four
  fields; any other count is E012.
- `Type` is now field 4 (was field 5) and keeps every rule from RFC 0001 D6:
  default `Voice`, registered values, case-insensitive match, unknown values
  preserved with W005.
- Nothing else moves. `AudioName`, subtitle sets, the half-open interval, the
  colour field, canonical form and the limits are unchanged.

### D4″ — A retired line is a marked comment, not a record

A line that is kept for reference but must never render is written as:

```
#!cut Level1VO2 : {"A deleted line"|00:00:00:29-00:00:00:92|} : [#FFFFFF]
```

- `#!cut` followed by exactly one SPACE, then a record in canonical form.
- A **Parser MUST NOT** treat it as a record. It is a comment for every purpose
  of parsing and rendering.
- A **Linter SHOULD** parse the payload as a record and report **W008** when it
  is not a valid one, naming the underlying E-code. This is the point of the
  marker: a retired line keeps being checked, so it cannot rot into invalid
  syntax or a stale time range while nobody is looking.
- Retired records are excluded from the duplicate-`AudioName` check (E015).
  Cutting a line and later recording a new one under the same asset name is a
  normal workflow, not a conflict.
- Retired records are preserved by formatters and serialised in canonical form.

**Why not plain `#`?** Because a comment cannot be distinguished from prose. The
superseded draft's own examples contain `# Format: Audio_name : {...} : [#Color]`
— auto-detecting "commented-out records" would flag that line on every run. The
marker makes intent explicit and costs one word.

**Why not `#@cut`?** The `#@` namespace is for file-scoped metadata. `#!cut` is a
line-scoped construct, and it sits next to `#!iac` as "structured, not prose".

## 3. Error taxonomy changes

| Change | Code | Effect |
|---|---|---|
| Retired | E022 | No longer emitted. The number MUST NOT be reused; a gap is cheaper than a renumber. |
| Added | W008 | A `#!cut` line whose payload is not a valid record. Severity: warning. |

Every other code keeps its number and meaning.

## 4. Compatibility and migration

Nothing has been publicly announced, so 1.0.0 ships with the shorter record and
there is no version bump. The compatibility promise in RFC 0001 D16 is unaffected
because there is no earlier published grammar to be compatible with.

Existing files — including everything derived from the original draft — migrate
mechanically:

| Old line | New line |
|---|---|
| `NAME : {…} : [#RRGGBB] : true` | `NAME : {…} : [#RRGGBB]` |
| `NAME : {…} : [#RRGGBB] : true : Music` | `NAME : {…} : [#RRGGBB] : Music` |
| `NAME : {…} : [#RRGGBB] : false` | `#!cut NAME : {…} : [#RRGGBB]` |
| `NAME : {…} : [#RRGGBB] : false : Music` | `#!cut NAME : {…} : [#RRGGBB] : Music` |

`tools/iac_lint.py migrate <file>…` performs exactly this rewrite. It is
idempotent and refuses to touch a file that already has a 3-or-4-field record.

## 5. Impact

| Artefact | Change |
|---|---|
| `spec/iac-1.0.md` | §1.3, §3.5, §4.1–§4.4, §5.4, §7, §8, §10 lose the field; new §5.4 defines retired records |
| `spec/iac.abnf` | `record` loses one optional field; `retired` production added |
| `spec/appendix/rationale.md` | the `enabled` rationale is replaced by the argument in §1 above |
| `registry/directives.md` | unchanged; `#!cut` is not a directive |
| `testdata/` | every case rewritten to the new field layout; `bad-enabled.iac` removed; `cut-record.iac` and `cut-record-broken.iac` added |
| `tools/iac_lint.py` | field count 3–4, `#!cut` parsing, W008, `migrate` subcommand, E022 removed |
| `examples/` | field removed; the disabled line becomes `#!cut` |
| `README*`, `docs/` | every example and every mention of the field |
| `CHANGELOG.md` | recorded in the 1.0.0 entry as removed before the announcement |

## 6. Rejected alternatives

**Keep the boolean, rename it.** Renaming does not create a consumer. The field
would still be a constant.

**Turn it into a `status` enum (`live` / `cut` / `alt` / `draft`).** This was the
closest call. It is genuinely useful for a translation pipeline that must not
translate cut lines. It was rejected because it keeps a required field that most
files set to one value, and because a line-level marker expresses the same thing
without touching the record grammar. If a pipeline needs per-line state in
machine-readable form later, it belongs in a directive or a sidecar file, not in
the fourth slot.

**Make the field optional.** Impossible without ambiguity: `NAME : {…} : [#FFF] :
Music` would have to mean either "status omitted, Type is Music" or "status is
Music". A trailing optional field must be unique in kind.

**Turn the slot into `duration` for validation.** Duplicates data that already
lives in the audio asset, and invites drift between the two.

## 7. What this buys

- A record line is 12 characters shorter and has one fewer thing to get wrong.
- The grammar has one optional field instead of one optional and one required.
- "This line is cut" becomes greppable (`grep -c '^#!cut'`) and checkable by the
  same linter run that checks everything else.
- The format states what it is: what is said, and when.
