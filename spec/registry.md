# Registry

- **Status:** Normative for IAC 1.0
- **Specification:** `spec/iac-1.0.md` §3.3, §3.4, §5.5

This file lists the values IAC 1.0 reserves: the track `Type` values and the line
prefixes that are not plain comments. Everything here is normative.

## 1. Track types

`Type` is an optional, per-record styling hint (§5.5). Matching is
case-insensitive; a producer emits the canonical spelling; a well-formed value that
is not listed here is preserved and reported as W005 by a linter.

| Canonical spelling | Meaning | Rendering guidance |
|---|---|---|
| `Voice` | Spoken dialogue from a character in the scene. The default when field 4 is absent. | Default subtitle styling. Most records should omit the field. |
| `Music` | Sung lyrics or diegetic music whose words are subtitled. | Distinguish from dialogue, for example with italics. Do not alter timing or text. |
| `SFX` | A description of a sound effect, not speech: `"[door slams]"`. | Subdued styling. Do not add brackets that are not in the file. |
| `Narration` | A narrator or voice-over that is not in-scene dialogue. | Distinct from `Voice`. Do not alter timing or text. |
| `UI` | Interface text, prompts, tutorial lines, system messages. | UI styling; an application MAY suppress these when the interface shows the same string. |

Rules:

- Absent field 4 means `Voice`. Writing `: Voice` is valid but not canonical.
- Each value matches `ALPHA *( ALPHA / DIGIT / "-" / "_" )` (§4.4).
- A value that is not a token at all is E014 (`!Music`, `_Music`).
- A valid token followed by whitespace and more content is E018 (`Music extra`).
- A well-formed value that is not in this table is unregistered: preserve it, do
  not reject the file, warn W005, and style it as `Voice`.
- `Type` MUST NOT affect timing, text, or colour.

## 2. Line prefixes

| Prefix | Kind | Position | Handling |
|---|---|---|---|
| `#` | comment | any line | Ignored. A bare `#` is a valid comment. |
| `#@` | directive | any line | `#@<name> <value>`; unknown names are ignored with W006. |
| `#!iac` | version marker | line 1, after an optional BOM | `#!iac <MAJOR>.<MINOR>`. Any other `#!iac` line is a comment. |
| `#!cut` | retired record | any line | `#!cut ` plus a record in canonical form; not a record (§5.4). |

`#@` is the only directive namespace in 1.0. `#!` is reserved for structured
markers, of which `#!iac` and `#!cut` are the only two.

## 3. Directives

IAC 1.0 defines exactly one directive.

| Directive | Value | Scope | Semantics |
|---|---|---|---|
| `#@language` | A BCP 47 language tag (RFC 5646), for example `zh-CN` or `en`. | Whole file. | Informational. It MUST NOT affect timing, text, colour, or `Type`. |

- The value is the rest of the line after exactly one SPACE, with trailing SPACE
  and TAB ignored. An empty value is malformed.
- A second `#@language` is ignored and reported as W006.
- An invalid tag is reported as W006 and the file stays valid.
- A parser MUST NOT use the tag to select a font, resolve a resource, or change
  how it parses a record.

## 4. Adding a value

A new `Type` or directive is a minor-version change, because a 1.0 parser ignores
or preserves it. Propose it through the RFC process in [GOVERNANCE.md](../GOVERNANCE.md);
the proposal names the canonical spelling, its meaning, and the rendering or
parsing guidance. Removing or renaming a registered value is a breaking change and
needs a major version with a deprecation cycle.
