# Directive and Version-Marker Registry

- **Status:** Normative registry for IAC 1.0
- **Registry version:** 1.0
- **Specification:** `spec/iac-1.0.md` §3.3, §3.4

## 1. Reserved line prefixes

| Prefix | Kind | Position | Handling |
|---|---|---|---|
| `#` | comment | any line | Ignored unless the line is `#@`, a version marker, or `#!cut`. A bare `#` is a valid comment. |
| `#@` | directive | any line | Parsed as `#@<name> <value>`. Unknown names are ignored with W006. |
| `#!iac` | version marker | line 1 only, after an optional BOM | Parsed as `#!iac <MAJOR>.<MINOR>`. Any other `#!iac` line is a comment. |
| `#!cut` | retired-record marker (not a directive) | any line | `#!cut ` followed by a record in canonical form; a parser treats it as a comment (§5.4). |

`#@` is the only directive namespace in 1.0. It is reserved so that future file-scoped
metadata does not require a syntax change. A line beginning `#` that is not `#@`, not a
valid first-line version marker, and not a `#!cut` retired record is a comment.

## 2. Version marker

```
#!iac <MAJOR>.<MINOR>
```

- It MUST be the first line of the file, after an optional BOM.
- Exactly one SPACE separates `#!iac` from the version.
- `MAJOR` and `MINOR` are one or more decimal digits, with no sign.
- A parser that supports major 1 reads the marker. `MAJOR > 1` is E024 and no record is
  processed. A newer `MINOR` is W007 and parsing continues.
- An absent marker means IAC 1.0.
- A first line beginning `#!iac` that does not match the production is an ordinary
  comment with no diagnostic. A `#!iac` line in any other position is a comment and MUST
  be ignored; a linter SHOULD report W006 because it is almost certainly misplaced.

The marker is not a directive. It lives in the comment namespace so that parsers written
before 1.0 ignore it, and it is defined here because it shares the reserved `#!` prefix
with `#!cut` and any future structured marker.

## 3. Registered directives

IAC 1.0 defines exactly one directive.

| Directive | Value | Scope | Semantics |
|---|---|---|---|
| `#@language` | A BCP 47 language tag (RFC 5646), for example `zh-CN` or `en`. | Whole file. | Informational. It tells tools what language the text is in. It MUST NOT affect timing, text, colour, or Type. |

Rules:

- The value is the remainder of the line after exactly one SPACE, with trailing SPACE and
  TAB ignored. An empty value is malformed.
- A duplicate `#@language` is ignored after the first occurrence and MUST be reported as
  W006.
- A syntactically invalid language tag MUST NOT cause rejection. The value is ignored for
  informational purposes; the file remains valid.
- A parser MUST NOT use the tag to select a font, resolve a resource, or change parsing.

Example:

```
#!iac 1.0
#@language zh-CN
VO_1 : {"你好，世界。"|00:00:00:00-00:00:02:50|} : [#FFFFFF]
```

## 4. Unknown directives

- A parser MUST ignore a directive whose name it does not recognise and MUST report W006.
- A parser MUST NOT reject a file because of an unknown directive.
- A malformed directive (for example `#@` with no name, or `#@language` with no value) is
  treated as unknown: ignored, with W006.
- Unknown directives MUST NOT change the meaning of any record line.
- A linter SHOULD report W006 for every unknown or duplicate directive it finds.

This rule is the forward-compatibility mechanism for file-scoped metadata. A 1.0 parser
that ignored it would reject files written for a later minor version, which is exactly
what the version model forbids.

## 5. Namespace reservation

- `#@` is reserved for directives. Producers MUST NOT emit `#@` lines that are not
  intended as directives.
- `#!` is reserved for structured markers: the first-line `#!iac` version marker and the
  line-scoped `#!cut` retired record. Other `#!` lines are comments. `#!cut` MUST NOT be
  registered as a directive; it is not file-scoped metadata.
- `#` alone remains a plain comment. Comments MUST NOT be interpreted as configuration.
- No other line prefix is reserved in 1.0. Metadata that must be file-scoped belongs in a
  directive, not in a comment.

## 6. Registering a new directive

A new directive is added by an RFC in `rfcs/` and MUST satisfy all of the following:

1. it is file-scoped and does not change the meaning of a record line;
2. it is ignorable: a 1.0 parser that does not know it still parses every record
   identically and reports only W006;
3. its name matches `1*( ALPHA / DIGIT / "-" / "_" )` and does not collide with an
   existing name;
4. its value grammar, default when absent, duplicate behaviour, and interaction with
   existing directives are specified;
5. it introduces no external reference, path, URL, or executable content.

Adding a directive is a minor-version change. Removing or redefining one is a breaking
change and requires a major version with a deprecation cycle of at least one minor
release. Registry ownership and review are described in `GOVERNANCE.md`.

`#!cut` is not a directive and is outside this registry. It MUST NOT be registered here;
it is a line-scoped retired-record marker defined by `spec/iac-1.0.md` §5.4.
