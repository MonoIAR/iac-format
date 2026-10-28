# Quickstart

**Answers:** how do I get a validated `.iac` file in five minutes?
**Does not answer:** the rules themselves ([../spec/iac-1.0.md](../spec/iac-1.0.md)) or
why they exist ([../spec/rationale.md](../spec/rationale.md)).

You need a checkout of this repository and a Python 3 interpreter. There is no
install step and no published package: the linter is
[`tools/iac_lint.py`](../tools/iac_lint.py).

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

- One line is one audio track: `AudioName : {cues} : [#RRGGBB] [: Type]`.
- A cue is `"text"|HH:MM:SS:CC-HH:MM:SS:CC|`, and the interval is half-open:
  visible at the start, gone at the stop.
- `#!iac 1.0` declares the version; `#@language en-US` is informational. Both are
  optional, and both are comments to a reader that predates them.
- `#!cut ...` is a retired line: a comment holding a whole record. It stays in the
  file, the linter still checks it, and nothing renders it.

## 2. Validate it

```bash
python tools/iac_lint.py validate lines.iac
```

A clean run prints nothing and exits `0`: silence is success. When there is a
finding, each line is `<file>:<line>:<column>: <severity> <CODE> <message>`,
followed by a summary.

```bash
python tools/iac_lint.py validate lines.iac --json
```

`--json` prints a machine-readable array. Directory arguments work too and are
walked recursively for `*.iac`:

```bash
python tools/iac_lint.py validate examples/
```

## 3. Break it, then fix it

Change the first cue's interval so the stop is before the start:

```iac
"Chapter : The Fall"|00:00:01:00-00:00:00:50|
```

The run exits `2` and reports **E010** — a stop that is not strictly after its
start. Restore `00:00:03:50` and it exits `0` again.

Another one you will meet while editing: delete a closing quote and you get **E002**
(unterminated quoted string). [errors.md](errors.md) lists every code with its fix.

## 4. Format it

The first record carries an explicit `: Voice`, which canonical form omits because
`Voice` is the default:

```bash
python tools/iac_lint.py fmt lines.iac
```

`fmt` rewrites the file in place and prints the path only when something changed.
It normalises field spacing, sorts cues by start time, drops `: Voice`, and leaves
comments, directives, and `#!cut` payloads in canonical form. To check without
writing, which is what CI should do:

```bash
python tools/iac_lint.py fmt --check examples
```

Both `fmt` and `--check` accept files or directories. Exit `0` means every file
is canonical; exit `2` means at least one is not, or does not parse.

## 5. Use it in CI

One command is the gate:

```bash
python tools/iac_lint.py validate content/subtitles
```

| Exit | Meaning | Typical CI decision |
|---|---|---|
| `0` | No findings | Pass |
| `1` | Warnings only | Pass or warn, your call |
| `2` | At least one error | Fail |

Warnings are non-zero by design, so a pipeline that fails on any non-zero exit also
fails on W003 (missing trailing newline) or W008 (a `#!cut` payload that no longer
parses). Decide deliberately rather than discovering it.

## Where next

- Writing content: [authoring.md](authoring.md).
- Converting existing subtitles, including draft-era files: [conversion.md](conversion.md).
- Implementing a parser: [parsing.md](parsing.md), then the corpus in
  [../testdata/](../testdata/).
- A code you do not recognise: [errors.md](errors.md).
- The rules themselves: [../spec/iac-1.0.md](../spec/iac-1.0.md).
