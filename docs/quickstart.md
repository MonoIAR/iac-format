# Quickstart

Zero to a validated file in five minutes. You need a checkout of this repository and a `python` that runs Python 3. There is no install step and no published package: the linter is [tools/iac_lint.py](../tools/iac_lint.py) and runs from the checkout.

## 1. Write a file

Create `lines.iac` at the repository root:

```iac
#!iac 1.0
#@language en-US

chapter1_vo1 : {"Chapter : The Fall"|00:00:01:00-00:00:03:50|, "He said \"go\" and left."|00:00:04:00-00:00:06:25|} : [#FFFFFF] : Voice
#!cut chapter1_vo2 : {"Cut line kept for reference"|00:00:07:00-00:00:07:80|} : [#FFD166]
chapter1_music : {"I meant to say goodbye"|00:00:08:00-00:00:12:00|} : [#FFFFFF] : Music
chapter2_vo1 : {"他说 : 你好"|00:00:13:00-00:00:14:20|} : [#FFFFFF]
```

Read it as: one line = one audio track. The track name comes first, then its cues in braces, then the display colour, and optionally the track's `Type`.

- `chapter1_vo1` — an audio track named after a scene and voice slot.
- `{"text"|HH:MM:SS:CC-HH:MM:SS:CC|, ...}` — cues, each pairing text with a half-open interval.
- `[#FFFFFF]` — colour for every cue on the track.
- `: Music` — optional track type; omitted means `Voice`.
- `#!cut ...` — a retired line: a comment holding a whole record. It stays in the file, is checked by the linter, and never renders.

`#!iac 1.0` declares the version; `#@language en-US` is an informational directive. Both are optional, and both are ignored as comments by older readers.

## 2. Validate it

```bash
python tools/iac_lint.py validate lines.iac
```

Exit code `0`: no findings. Nothing is printed for a clean file, so silence is success.

Add `--json` when a machine consumes the result:

```bash
python tools/iac_lint.py validate lines.iac --json
```

Directory arguments work too, and are walked recursively for `*.iac` files:

```bash
python tools/iac_lint.py validate examples/
```

A diagnostic prints as `<file>:<line>:<column>: <severity> <CODE> <message>`, followed by a one-line summary when anything is found. A clean file prints nothing at all.

## 3. Break it, then fix it

Change the first cue's interval so the stop is before the start:

```iac
"Chapter : The Fall"|00:00:01:00-00:00:00:50|
```

```bash
python tools/iac_lint.py validate lines.iac
```

The run now exits `2` and reports **E018** — a stop time that is not strictly after its start. Put the interval back to `00:00:01:00-00:00:03:50` and it exits `0` again.

Another one you will meet while editing: delete a closing quote and you get **E010** (unterminated quoted string). A raw `"` cannot appear inside text at all — that is what `\"` is for. [reference/errors.md](reference/errors.md) lists every code with its fix.

## 4. Format it

The first record carries an explicit `: Voice`, which canonical form omits because `Voice` is the default:

```bash
python tools/iac_lint.py fmt lines.iac
```

`fmt` rewrites the file in place. The only visible change is that `: Voice` is gone, because `Voice` is the default `Type`; comments, directives, and `#!cut` lines pass through with their payloads in canonical form. Canonical form also fixes field spacing (` : `, `, `), strips leading and trailing whitespace, sorts cues by start time, and keeps one record per line. That is what makes reviews and golden tests stable.

Validate again to confirm the file still parses:

```bash
python tools/iac_lint.py validate lines.iac
```

## 5. Put it in CI

A single command is the gate:

```bash
python tools/iac_lint.py validate content/subtitles
```

Exit codes are fixed and shared across tools:

| Code | Meaning | Typical CI decision |
|---|---|---|
| `0` | Clean | Pass |
| `1` | Warnings only | Pass or warn, your call |
| `2` | Errors | Fail |

Warnings are non-zero by design, so a pipeline that fails on any non-zero exit will fail on W003 (missing trailing newline) or W008 (a `#!cut` line whose payload no longer parses) too. Decide deliberately rather than discovering it.

## Where next

- Writing content: [guides/authoring.md](guides/authoring.md).
- Migrating existing subtitles: [guides/conversion.md](guides/conversion.md).
- Coming from a draft-era file with a `: true` / `: false` field: run `python tools/iac_lint.py migrate <file>...` first — see [conversion.md](guides/conversion.md#draft-era-files).
- Implementing your own parser: [guides/parsing.md](guides/parsing.md), then the corpus in [testdata/](../testdata/).
- Rules themselves: [spec/iac-1.0.md](../spec/iac-1.0.md).
