# Documentation

The normative text is [spec/iac-1.0.md](../spec/iac-1.0.md). Everything in `docs/` is explanatory: it may paraphrase, give examples, and recommend practice, but where it disagrees with the spec, the spec wins and the doc is a bug — please [report it](../CONTRIBUTING.md).

## Map

| Document | Read it when |
|---|---|
| [quickstart.md](quickstart.md) | You want a validated file in five minutes. |
| [guides/authoring.md](guides/authoring.md) | You write or review `.iac` content: naming, timing, escapes, `#!cut` retired lines, `Type`, canonical form, and the eight mistakes that account for most broken files. |
| [guides/parsing.md](guides/parsing.md) | You are implementing a parser: the quote-aware scanner as a state machine, the half-open interval rule, canonical serialisation, error mapping, and what the conformance suite demands. |
| [guides/conversion.md](guides/conversion.md) | You are moving subtitles between SRT, VTT, ASS and IAC, or writing a converter: rounding, interval semantics, ASS colour order, lossiness. |
| [reference/errors.md](reference/errors.md) | A tool reported a code and you want the cause and the fix. |
| [faq.md](faq.md) | You want to know why the format is the way it is — JSON, centiseconds, frames, newlines, colours, right-to-left text. |
| [comparison.md](comparison.md) | You are choosing a format and need the trade-offs stated honestly, including where IAC is weaker. |
| [adoption.md](adoption.md) | You are rolling IAC out inside a studio or tool chain: order of work, integrations, 90-day plan, success metrics. |

Project documents sit at the repository root: [GOVERNANCE.md](../GOVERNANCE.md) (stewardship, RFC process, versioning), [CONTRIBUTING.md](../CONTRIBUTING.md) (changes, conformance cases, DCO), [CHANGELOG.md](../CHANGELOG.md), [ROADMAP.md](../ROADMAP.md), [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md), [LICENSE](../LICENSE), and the decision records [RFC 0001](../rfcs/0001-standardize-iac-1.0.md) and [RFC 0002](../rfcs/0002-remove-enabled-field.md).

## Reference material

- [spec/iac-1.0.md](../spec/iac-1.0.md) — normative rules, RFC 2119 keywords.
- [spec/iac.abnf](../spec/iac.abnf) — grammar.
- [spec/appendix/media-type.md](../spec/appendix/media-type.md) — media type and extension registration package: interim `text/x-iac`, proposed `text/vnd.iac`.
- [registry/types.md](../registry/types.md), [registry/directives.md](../registry/directives.md) — registered values.
- [testdata/](../testdata/) — conformance corpus; `conformance.json` maps each case to its expected code set.
- [tools/iac_lint.py](../tools/iac_lint.py) — reference validator, formatter, SRT importer.

## Reading paths

**Writer or localisation engineer.** [quickstart.md](quickstart.md) → [guides/authoring.md](guides/authoring.md) → [reference/errors.md](reference/errors.md) when the linter complains.

**Parser implementer.** [spec/iac-1.0.md](../spec/iac-1.0.md) end to end, then [guides/parsing.md](guides/parsing.md), then run the corpus in [testdata/](../testdata/) and make `conformance.json` pass.

**Pipeline owner.** [guides/conversion.md](guides/conversion.md) → [comparison.md](comparison.md) → [adoption.md](adoption.md).

**Decision maker.** [comparison.md](comparison.md) → [adoption.md](adoption.md) → [GOVERNANCE.md](../GOVERNANCE.md) (licensing, versioning, change control).

## Conventions

- `HH:MM:SS:CC` — the last component is **centiseconds**, never frames. See [spec/iac-1.0.md](../spec/iac-1.0.md).
- Intervals are half-open: `[start, stop)`. A cue is visible from its start, not at its stop.
- A record has three required fields and an optional `Type`; a cut line is a `#!cut` comment, not a record.
- Error and warning codes (`E001`, `E010`–`E027` except the retired `E022`, `W001`–`W008`) are stable identifiers shared by the spec, the linter, and future tooling. They are catalogued in [reference/errors.md](reference/errors.md).
- Examples are CC0-1.0; copy them freely.
