# IAC subtitle format

IAC (Inline Annotation Container) is a line-oriented plain-text subtitle format that
keeps cue timing inline with the text it belongs to, one audio track per line.

**Status:** 1.0.0 — stable, tagged 2026-10-29, not yet publicly announced. The normative
specification is [spec/iac-1.0.md](spec/iac-1.0.md).

## The shape of a record

```text
AudioName : { "text"|HH:MM:SS:CC-HH:MM:SS:CC|, ... } : [#RRGGBB] [ : Type ]
```

Three required fields, one optional. Times are `HH:MM:SS:CC` with `CC` in
centiseconds, never frames, and an interval is half-open: `[start, stop)`.

A real record — the first line of [examples/music.iac](examples/music.iac), wrapped
here and cut after three of its nineteen cues:

```iac
music_KnewBefore : {"I've forgot the way to be myself"|00:00:08:58-00:00:17:20|,
                    "I don't know who I was the night before"|00:00:17:20-00:00:25:99|,
                    "The shadows in the air, they haunt me still"|00:00:25:99-00:00:40:62|,
                    ...,
                    "The one I knew before"|00:02:17:84-00:03:12:02|} : [#FFFFFF] : Music
```

## Why

- **Timing lives with the text.** A line carries its own cues, so translating one line
  is one edit and the timing stays attached to the sentence it belongs to.
- **No escaping hell.** Records split on ` : ` only at top level, outside quotes and
  braces, so `"Chapter : The Fall"` and `"他说 : 你好"` are ordinary text.
- **Plain text that diffs.** One record per line, deterministic canonical form, no
  binary blobs. A cut line is a `#!cut` comment: it stays in the file, keeps being
  checked, and never renders.

## 60 seconds

```bash
python tools/iac_lint.py validate examples/single-subtitle.iac
python tools/iac_lint.py validate examples/          # directories are walked
python tools/iac_lint.py fmt --check examples        # is every file canonical?
```

Exit `0` means no findings and prints nothing; `1` is warnings only; `2` is errors.
Add `--json` for machine-readable output. There is no install step and no published
package: the linter is one stdlib-only file that runs from a checkout.

## Where things live

| Path | What it is |
|---|---|
| [spec/](spec/) | Normative: [the specification](spec/iac-1.0.md), [the grammar](spec/iac.abnf), [the registry](spec/registry.md), plus [rationale](spec/rationale.md) and [security notes](spec/security.md) |
| [testdata/](testdata/) | 38 conformance cases and [conformance.json](testdata/conformance.json), which maps each case to its expected codes |
| [tools/](tools/) | Reference linter: validate, format, SRT import, draft migration |
| [docs/](docs/) | Five guides: [quickstart](docs/quickstart.md), [authoring](docs/authoring.md), [parsing](docs/parsing.md), [conversion](docs/conversion.md), [errors](docs/errors.md) |
| [rfcs/](rfcs/) | [RFC 0001](rfcs/0001-standardize-iac-1.0.md): why the format looks like this |
| [examples/](examples/) | Three canonical samples: a song, multiple tracks with a cut line, one Chinese dialogue |

## When not to use IAC

IAC describes **what is said and when**, not how it looks. Choose something else if you
need:

- positioning, fonts, styling spans, or animation — use ASS or WebVTT with CSS;
- karaoke or word-level timing — use ASS;
- per-entry colour or transparency — IAC has one colour per track, no alpha;
- lossless interchange with an existing subtitle pipeline — IAC is a source format, and
  converting out of it is lossy by design ([spec §1.1](spec/iac-1.0.md)).

## Compatibility

A parser implementing minor version `x` reads any conforming file from minor `y <= x`
without loss of meaning. A file that declares a newer minor is not fatal: the parser
reports W007 and continues. Only a newer major version is fatal (E015). Breaking changes
require a major bump and at least one minor release of deprecation; the process is in
[GOVERNANCE.md](GOVERNANCE.md).

## Licence

| Part | Licence |
|---|---|
| Specification, docs, registry, RFCs, this README | CC BY 4.0 |
| Reference code in `tools/` | Apache-2.0 |
| Example and conformance `.iac` files | CC0-1.0 |

The per-artefact split is in [LICENSE](LICENSE).

中文文档：[README.zh-CN.md](README.zh-CN.md)
