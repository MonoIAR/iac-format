# Comparison

IAC sits next to SRT, WebVTT, ASS/SSA, CSV, and JSON in the same pipeline, and it is worse than all of them at something. The table is deliberately unflattering about the ecosystem; the prose after it says where IAC should not be used.

| | IAC | SRT | WebVTT | ASS/SSA | CSV | JSON |
|---|---|---|---|---|---|---|
| **Cue-level timing** | Per cue, inline: `"text"\|start-stop\|` | Per cue | Per cue | Per cue, plus layer | Per row, by convention | Per object, by convention |
| **Inline per-cue metadata** | Text and interval per cue; colour and `Type` per record | None standard; `<i>`/`<font>` are extensions | Cue settings (`line:`, `position:`, `align:`), CSS classes | Extensive: style, actor, layer, margins, override tags | Arbitrary columns, no schema | Arbitrary keys, no shared schema |
| **Escaping dialogue** | Two escapes (`\"`, `\\`); ` : ` safe inside quotes | None; `-->` in text can break naive parsers | HTML entities plus tag syntax | `{...}` override syntax collides with literal braces | RFC 4180 quoting; spreadsheets reinterpret values | Full escaping; quotes and backslashes on every line |
| **Diffability** | High: one record per line, deterministic canonical form | Medium: multi-line blocks | Medium: blocks plus settings | Low: style tables, override tags | Medium: wide rows, quoting noise | Low: punctuation-dominated |
| **Tooling maturity** | Reference linter only; no third-party implementations | Universal | Strong in browsers and web players | Mature in players and subtitling tools | Universal, via spreadsheets | Excellent libraries; no subtitle schema |
| **Localisation-vendor support** | None yet | Universally accepted handoff | Sometimes accepted | Common in subtitling houses | Common in game localisation | Rare as a handoff; pipeline-internal |
| **Colour** | Required per record, `[#RRGGBB]` | Not standard | Via CSS classes | Primary/outline/shadow colours | A column, if you add one | A key, if you add one |
| **Cut lines kept** | `#!cut` comment, retained and hidden | Delete the block | Delete the cue | Comment the `Dialogue:` line | An extra column | An extra key |
| **Multiple tracks per file** | Yes, one record each | No | One file; `<v>` voices | Styles, layers, actors | Columns or rows | Top-level array |
| **Version marker** | `#!iac 1.0`, forward compatible | None | `WEBVTT` header | `[Script Info]` fields | None | `$schema`, if you use one |

## Where IAC loses

**Ecosystem.** This is the honest headline. SRT has decades of players, converters, QA tools, and vendor acceptance. IAC has one reference linter, a conformance corpus, and no third-party implementations. For anything shipping this quarter, converting to SRT is still the safe last mile.

**Rendering.** No positioning, no styles, no karaoke, no multi-line layout, no fonts. If it needs to look like anything other than coloured text at a fixed position, IAC is the wrong file to hand to a player.

**Precision.** Centiseconds are coarser than SRT's milliseconds. Irrelevant for subtitles (a frame is 17–42 ms at 24–60 fps) but real if you are using the format to drive something frame-locked.

**Organisational cost.** A new format means converters, training, and a vendor conversation. The compatibility promise and the conformance suite reduce the technical risk; they do not reduce the social cost.

## Where IAC wins

**Review.** One record per line with inline timing: editing one sentence changes one line, without the index-and-timestamp scaffolding of an SRT block or the quoting noise of a CSV row. Canonical form makes that diff stable across tools.

**Dialogue safety.** Quote-aware splitting means `"Chapter : The Fall"` and `"他说 : 你好"` are ordinary text. SRT has no escape mechanism, VTT needs entities, ASS needs brace awareness, CSV needs quoting — all of them put the burden on whoever types the line.

**Retained decisions.** A `#!cut` comment keeps a cut line, its translation, and its timing in the file, and the linter keeps checking it. The alternatives are deletion (loses history) or a plain comment (invisible to tools that build track lists).

**Machine contract.** A version marker, a stable error taxonomy, registered `Type` values, and a normative conformance suite are things none of the other five have together. That is what makes a second implementation reviewable rather than folkloric.

## Choosing

| Situation | Use |
|---|---|
| Master copy of game dialogue with VO, cuts, and lyrics | IAC |
| Delivery to a subtitling house or broadcaster | Their spec: usually SRT or ASS |
| Web playback | WebVTT |
| Spreadsheet handoff to translators | CSV/Excel, or XLIFF if the vendor takes it |
| Internal service-to-service payload | JSON |
| Frame-locked, per-syllable karaoke | ASS — and keep the master elsewhere |

XLIFF is the localisation industry's exchange format; IAC does not compete with it. The realistic pipeline is IAC as the master, generated SRT/ASS/VTT for the delivery targets, and XLIFF for translation — each format doing the one thing it is good at. [conversion.md](guides/conversion.md) documents the seams, including what each hop loses.
