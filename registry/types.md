# Type Registry

- **Status:** Normative registry for IAC 1.0
- **Registry version:** 1.0
- **Specification:** `spec/iac-1.0.md` §5.5

`Type` is an optional, per-record styling hint. The registered values below are the
interoperable set. Matching is case-insensitive; a serializer MUST emit the canonical
spelling. A parser MUST preserve a well-formed but unregistered value and MUST NOT treat
it as an error; a linter SHOULD report W005 and a renderer MUST fall back to default
styling for it.

## 1. Registered values

| Canonical spelling | Meaning | Rendering guidance |
|---|---|---|
| `Voice` | Spoken dialogue from a character in the scene. This is the default when field 4 is absent. | Default subtitle styling. Most records should omit the field rather than write `Voice`. |
| `Music` | Sung lyrics or diegetic music whose words are subtitled. | Distinguish from dialogue, for example with italics or a music-specific colour chosen by the application. Do not alter timing or text. |
| `SFX` | A description of a sound effect, not speech: `"[door slams]"`. The brackets, if any, are part of the text and are not syntax. | Subdued styling, for example a smaller or secondary style. Do not add brackets that are not in the file. |
| `Narration` | A narrator or voice-over that is not in-scene dialogue. | Distinct from `Voice`, for example a different weight or colour. Do not alter timing or text. |
| `UI` | Interface text, prompts, tutorial lines, or system messages. | UI-oriented styling; an application MAY suppress these when the interface renders the same string itself. Do not alter timing or text. |

All values match the token grammar of §5.5: an ASCII letter followed by ASCII letters,
digits, `-`, or `_`.

## 2. Case-insensitivity

- Comparison is ASCII case-insensitive: `music`, `Music`, and `MUSIC` all match `Music`.
  The token grammar admits ASCII letters only, so no Unicode case folding is involved.
- A Producer MUST emit the canonical spelling for a registered value. It MUST NOT emit
  `music` or `MUSIC` for a value it matched as `Music`.
- A parser MUST accept any casing of a registered value and MUST NOT report an error
  merely for casing. A linter MAY report W004 when the input spelling is not canonical.
- A well-formed value that is not in this registry is not a casing variant of a
  registered value: it is unregistered. It is preserved with the spelling received and
  reported as W005 by a linter.

Examples:

```
level1_vo1 : {"Line"|00:00:00:00-00:00:01:00|} : [#FFFFFF]
music_theme : {"Lyric"|00:00:01:00-00:00:03:00|} : [#FFFFFF] : Music
sfx_door : {"[door slams]"|00:00:03:00-00:00:04:00|} : [#FFFFFF] : SFX
ambient_mix : {"Crowd murmur"|00:00:04:00-00:00:05:00|} : [#FFFFFF] : Ambient
```

The first record defaults to `Voice`. The last record carries an unregistered value; a
conforming parser preserves `Ambient`, a linter reports W005, and a renderer styles it
as it styles `Voice`.

## 3. Rules that apply to every Type

- Type MUST NOT affect timing, text, or colour (§5.5).
- A Renderer MAY style by Type and MUST NOT change timing or text while doing so (§10.4).
- An unknown Type MUST fall back to default styling (§10.4).
- A field 4 that is not a token at all is E023, not an unregistered value. The distinction
  is lexical: `!Music` is malformed; `Ambient` is unregistered.
- A valid token followed by whitespace and further content is trailing content (E027),
  not a Type value.

## 4. Registering a new value

New values are added by an RFC in `rfcs/`. A proposal MUST include:

1. the canonical spelling, matching `type` and not colliding case-insensitively with an
   existing value;
2. a one-sentence meaning that does not duplicate an existing value;
3. rendering guidance that only styles content and never changes timing or text;
4. a statement that the value is ignorable by a 1.0 parser and does not change the record
   grammar.

Registration is a minor-version change because a 1.0 parser preserves the value and
renders it with default styling. Removing or renaming a registered value is a breaking
change and requires a major version with a deprecation cycle of at least one minor
release.

Registry ownership and the review process are described in `GOVERNANCE.md`.
