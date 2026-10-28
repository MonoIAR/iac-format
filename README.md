# IAC subtitle format

IAC (Inline Annotation Container) is a line-oriented plain-text subtitle format that keeps cue timing inline with the text it belongs to, one audio track per line.

**Status:** 1.0.0 — stable, released 2026-10-29. Normative spec: [spec/iac-1.0.md](spec/iac-1.0.md).

## A real record

The first record of [examples/music.iac](examples/music.iac) (one record, one physical line in the file; shown wrapped and cut after three cues — the record has 19):

```iac
music_KnewBefore : {"I've forgot the way to be myself"|00:00:08:58-00:00:17:20|,
                    "I don't know who I was the night before"|00:00:17:20-00:00:25:99|,
                    "The shadows in the air, they haunt me still"|00:00:25:99-00:00:40:62|,
                    ...,
                    "The one I knew before"|00:02:17:84-00:03:12:02|} : [#FFFFFF] : Music

# Song "Knew Before" from game BONELAB
# Copyright: Michael Wyckoff, Stress Level Zero
```

Field order is `<AudioName> : {<cue>, <cue>, ...} : [#RRGGBB][ : <Type>]` — three required fields and an optional track type. Times are `HH:MM:SS:CC` with `CC` in centiseconds, and an interval is half-open: `[start, stop)`. A file may open with `#!iac 1.0`; being a comment, it costs nothing to readers that predate it.

## Why

- **Timing lives with the text.** A line carries its own cues, so translating one line is one edit and the timing stays attached to the sentence it belongs to. There is no separate timing track to keep in sync.
- **No escaping hell.** Records split on ` : ` only at top level, outside quotes and braces, so `"Chapter : The Fall"` and `"他说 : 你好"` are ordinary text. Dialogue needs no encoding to survive the format.
- **Plain text that diffs.** One record per line, deterministic canonical form, no binary blobs and no markup soup. A localisation review is a readable diff, and `iac_lint.py fmt` makes it a stable one. A cut line is a `#!cut` comment — it stays in the file, keeps being checked by the linter, and never renders, with no boolean in the record to get wrong.

## Quickstart — 60 seconds

```bash
python tools/iac_lint.py validate examples/single-subtitle.iac
```

Exit `0` means no findings, `1` warnings only, `2` errors. Add `--json` for machine-readable diagnostics. A clean run prints nothing, so silence is success.

```bash
python tools/iac_lint.py validate examples/
python tools/iac_lint.py fmt examples/multi-subtitles.iac
python tools/iac_lint.py from-srt in.srt out.iac
python tools/iac_lint.py migrate old-draft.iac
```

`fmt` rewrites one file into canonical form; `from-srt` converts an SRT file; `migrate` rewrites draft-era records that still carry a `: true` / `: false` field. Full walkthrough: [docs/quickstart.md](docs/quickstart.md).

## Where things live

| What | Where |
|---|---|
| Normative spec | [spec/iac-1.0.md](spec/iac-1.0.md) |
| Grammar (ABNF) | [spec/iac.abnf](spec/iac.abnf) |
| Registry | [registry/types.md](registry/types.md), [registry/directives.md](registry/directives.md) |
| Docs | [docs/index.md](docs/index.md) — quickstart, authoring, parser and conversion guides, error codes |
| RFC process | [rfcs/0000-template.md](rfcs/0000-template.md), [GOVERNANCE.md](GOVERNANCE.md) |
| Governance | [GOVERNANCE.md](GOVERNANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md) |
| Conformance suite | [testdata/](testdata/), reference linter [tools/iac_lint.py](tools/iac_lint.py) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |

## Compatibility promise

A parser implementing minor version `x` MUST read any conforming file from minor version `y <= x` without loss of meaning. A parser that meets a file declaring a *newer* minor version does not fail on the version line: it reports W007 and continues as best it can. Only a newer **major** version is fatal (E024). Breaking changes require a major bump and at least one minor release of deprecation — see [GOVERNANCE.md](GOVERNANCE.md).

New in 1.0 relative to the draft: exclusive stop times, the `#!iac` version line, registered `Type` values, a defined error taxonomy, and a three-field record — the draft's fourth boolean field is gone, and a cut line is now the `#!cut` comment. `python tools/iac_lint.py migrate` rewrites draft-era files mechanically.

## License

| Part | License |
|---|---|
| Specification text (`spec/`, `docs/`, `registry/`, RFCs, this README) | CC BY 4.0 |
| Reference code (`tools/`, future libraries) | Apache-2.0 |
| Example `.iac` files (`examples/`) | CC0-1.0 |

CC0 on examples is deliberate: paste them into a proprietary build without attribution friction. The per-artefact split, including the copyright line, is in [LICENSE](LICENSE).

## Status and roadmap

1.0.0 is the first stable release. Nothing is published to npm, PyPI, or IANA yet: the linter runs from a checkout, `text/x-iac` is an interim unregistered media type, and there are no third-party implementations to point at. 1.1 candidates are listed in [RFC 0001 §4](rfcs/0001-standardize-iac-1.0.md#4-deferred-work); the rollout plan is in [docs/adoption.md](docs/adoption.md) and the dated work list in [ROADMAP.md](ROADMAP.md). Release history: [CHANGELOG.md](CHANGELOG.md).

中文文档：[README.zh-CN.md](README.zh-CN.md)
