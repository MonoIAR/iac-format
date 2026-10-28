# Parser implementation guide

**Answers:** how do I write a parser that passes the conformance corpus?
**Does not answer:** the normative rules. Those are [spec §2–§9](../spec/iac-1.0.md);
this page gives the shape of an implementation and the places people get it wrong.

## The six stages

A parser is short if you keep the stages separate. Do not merge them: the order is what
makes the reported code deterministic ([spec §8.2](../spec/iac-1.0.md)).

### Stage 0 — bytes

Read bytes, decode UTF-8 strictly. A decode error, a NUL byte, or a BOM from a producer
is E001. One leading BOM is tolerated and reported as W001. Strip exactly one line
terminator per line; accept LF, CRLF, and CR.

### Stage 1 — classify each line

In this order: version marker (line 1 only), retired record (`#!cut `), directive
(`#@`), comment (`#`), blank, otherwise a record. Classification is on the first
character, not on the trimmed line: `  # indented` is a record line, not a comment.

### Stage 2 — the scanner

The only non-obvious part. Split on ` : ` only when brace depth is 0, bracket depth is
0, and no quoted string is open. `.iac` has no escaping outside quotes, so the scanner
is three counters and a flag:

```text
in_quote = False; escaped = False; brace = 0; bracket = 0
for each character, left to right:
    if in_quote:
        if escaped: escaped = False
        elif ch == "\\": escaped = True
        elif ch == '"': in_quote = False
    elif ch == '"': in_quote = True
    elif ch == "{": brace += 1
    elif ch == "}" and brace > 0: brace -= 1
    elif ch == "[": bracket += 1
    elif ch == "]" and bracket > 0: bracket -= 1
    elif ch == ":" and at top level and line[i-1] == " " and line[i+1] == " ":
        cut a field here
```

Two details matter:

- a closer with no opener **never** makes depth negative — it is a character in the
  current field, and the field rules report it (§3.5);
- an unclosed quote at end of line is E002 and pre-empts field counting, because the
  separators it would have found are not trustworthy.

### Stage 3 — fields

- **Field 1, `AudioName`.** Non-empty (E005). No ` : `, and no `"`, `{`, `}`, `[`, `]`;
  the last group is E006 only when the line still tokenizes, because an unbalanced
  quote or brace is E002 or E004 first. At most 256 code points (E016). Unique among
  live records, exact and case-sensitive (E007).
- **Field 2, the cue set.** Must be `{…}` (E004 when the braces are missing) and
  non-empty (E012). Split entries on `,` at top level, then match `"text"|start-stop|`.
  Per entry: escapes (E003), control
  characters (E017), time shape (E008), time ranges (E009), `stop > start` (E010),
  then order across entries (E011) and overlap (W002).
- **Field 3, colour.** Exactly `[#RRGGBB]` (E013). Preserve the case.
- **Field 4, `Type`.** Optional; absent means `Voice`. A token outside the registry is
  W005, not an error (E014 is only for a non-token). A token followed by more content
  is E018.

### Stage 4 — retired records

`#!cut ` plus a payload is a comment for parsing and rendering. Parse the payload into
a scratch diagnostic list: if it fails, report one W008 naming the first E-code and do
not promote that E-code to a file error. A valid payload keeps its own warnings (W004,
W002, W005). Retired records are excluded from the E007 duplicate check.

### Stage 5 — file level

A file-level duplicate is E007. A declared major above yours is E015 and stops record
processing; a newer minor is W007 and parsing continues. A missing final newline is
W003. Limits are §9 and report E016.

## Five things that trip implementers

1. **Splitting on the raw string.** `"Chapter : The Fall"` is one field. Any
   `line.split(" : ")` passes trivial tests and fails the corpus.
2. **Letting a stray closer unbalance the line.** `VO_1}` is E006 (a bad character in
   the name), not E004 (an unbalanced line).
3. **Treating an empty field 2 as a structural error.** It is an empty cue set, E012.
4. **Reporting E002 from the entry parser.** An unterminated quote is lexical: report
   it before field counting, once.
5. **Forgetting that `#!cut` payloads are checked but do not fail the file.** W008 is
   a warning that names an E-code.

## Canonical serialisation

If you also write files, emit [spec §7](../spec/iac-1.0.md): one record per line,
` : ` between fields, `, ` between entries, entries sorted by start, `Type` omitted
when `Voice`, UTF-8 without BOM, LF, final newline. Comments and directives are written
as they were read. Formatting a canonical file must reproduce it byte for byte.

## Conformance

[../testdata/conformance.json](../testdata/conformance.json) is the contract: each
case names a file, the expected severity (`ok`, `warning`, `error`), and the exact set
of codes. Compare sets, not sequences. The suite is constructed so each invalid case
has exactly one code.

```bash
python tools/run_conformance.py --verbose
```

To test your own implementation, replace `run_parser` in
[../tools/run_conformance.py](../tools/run_conformance.py) with a function that returns
the set of codes your parser produced.

## Migrating draft-era files

A record with `: true` or `: false` in field 4 is a draft file. On its own that parses
as an unregistered `Type` (W005); with a further field (`: true : Music`) the record has
five fields and is E004. Do not hand-edit:

```bash
python tools/iac_lint.py migrate path/to/file.iac
```

It drops `: true`, turns `: false` into `#!cut`, is idempotent, and leaves a record
whose fourth field is a real `Type` alone.
