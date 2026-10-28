# Media Type and File Extension

- **Status:** Informative registration package
- **Applies to:** IAC 1.0

## 1. Current status

| Item | Value |
|---|---|
| Interim media type | `text/x-iac` (unregistered, no IANA action) |
| Proposed registered media type | `text/vnd.iac` |
| Primary file extension | `.iac` |
| Legacy extension | `.txt` (accepted, MUST NOT be produced by new tooling) |
| Character encoding | UTF-8 only, no BOM on output |

`text/x-iac` is a stopgap. It is not registered, it MUST NOT be submitted to IANA, and
it SHOULD be replaced by `text/vnd.iac` once the prerequisites in §5 are met. Tools MAY
accept either name during the transition; a tool that writes IAC SHOULD label it
`text/x-iac` until the registration is approved.

## 2. Rationale for `text/vnd.iac`

- **`text/*`** because IAC is line-oriented, human-readable, and defined over a
  character encoding. It is not a binary container, not a multipart type, and needs no
  structured-syntax suffix.
- **`vnd.`** because the format is defined by its steward organisation, not by the IETF.
  The vendor tree is the correct place for a format with a single change controller.
- **No `+` suffix.** IAC is not XML, JSON, or any other structured syntax; it has its own
  grammar and a `+suffix` would mislead parsers.
- **No required parameters.** The encoding is fixed by the specification. A `charset`
  parameter is allowed for transport compatibility but only the value `UTF-8` is valid.

## 3. IANA registration template

The following is the intended submission to the IANA media type registry, completed as
far as the format can determine it. Fields that depend on the steward's contact details
are supplied by the steward at submission time; see §5.

```
Type name: text

Subtype name: vnd.iac

Required parameters: none

Optional parameters: charset
   Only the value "UTF-8" is valid. If the parameter is absent, UTF-8 is
   assumed. Other values are invalid and MUST NOT be used to interpret an
   IAC file; see spec/iac-1.0.md §2.1 and §12.

Encoding considerations: 8bit
   IAC files are UTF-8 text. The format is line-oriented. LF is canonical;
   parsers accept LF, CRLF, and CR. A leading BOM is tolerated on input and
   MUST NOT be emitted on output.

Security considerations:
   See spec/appendix/security-considerations.md. IAC has no executable
   surface, no external references, no paths, and no URLs. Parsers must
   enforce the resource limits in spec/iac-1.0.md §9.

Interoperability considerations:
   Major version 1 files are forward compatible within 1.x. A parser that
   supports 1.0 reads any 1.y file with y <= 0 and warns on a newer minor.
   A newer major is rejected with E024. Unknown directives are ignored and
   unknown Type values are preserved, so extension does not break readers.
   The legacy .txt extension is accepted but not produced.

Published specification:
   IAC 1.0 — Subtitle Format Specification, spec/iac-1.0.md, version 1.0,
   dated 2026-10-29. A permanent public URL for this document and for
   spec/iac.abnf is a prerequisite for submission (§5).

Applications that use this media type:
   Game dialogue and subtitle authoring; song lyric tracks; timed text in
   application builds; localisation pipelines; subtitle editors and linters.

Fragment identifier considerations: none

Additional information:
   Magic number(s): an optional first line beginning with "#!iac " (five
      bytes plus a space) followed by MAJOR.MINOR. This is a text marker,
      not a reliable binary signature; content sniffing should not rely on
      it.
   File extension(s): .iac
   Macintosh file type code(s): none
   Deprecated alias names: text/x-iac is an unregistered interim label, not
      an alias to register.

Person & email address to contact for further information:
   The registration contact published by the IAC steward organisation
   (see GOVERNANCE.md).

Intended usage: COMMON

Restrictions on usage: none

Author:
   The IAC steward organisation (see GOVERNANCE.md).

Change controller:
   The IAC steward organisation (see GOVERNANCE.md).
```

## 4. File extension

- The primary extension is `.iac`. New tooling MUST write `.iac`.
- `.txt` is legacy. A parser MUST accept valid IAC in a `.txt` file, but a Producer MUST
  NOT create one and a tool MUST NOT use any other extension for new output.
- The extension is not part of the format. A file's validity is determined by its
  bytes, not by its name; a `.iac` file with a BOM is a warning, and a `.txt` file with
  valid content is still valid IAC.

## 5. Prerequisites before registering

Registration is a claim that a stable, publicly specified format exists and has a
responsible owner. The following MUST be true before `text/vnd.iac` is submitted.

1. **Steward organisation.** A named organisation is responsible for the format and is
   recorded in `GOVERNANCE.md`. It supplies the change controller, the registration
   contact, and the permanent URL for the specification. A format without a steward has
   no one to answer an interoperability or security report.
2. **Stable specification.** IAC 1.0 is published, versioned, and under change control
   through `rfcs/`. There are no open errata that change the wire format or the
   diagnostic codes. The spec and `spec/iac.abnf` are available at a permanent public
   URL, not only in a repository checkout.
3. **Reference implementation.** `tools/iac_lint.py` implements the Parser role and
   passes every case in `testdata/conformance.json`, including exact code sets. The
   conformance suite is published with the specification so a second implementation can
   demonstrate agreement.
4. **Completed template.** The template in §3 is filled with real contact details,
   published specification URLs, and the steward's legal name. Placeholders are not
   acceptable in a submission.
5. **Expert review.** The submission goes through the IANA media type review process of
   RFC 6838, including the designated expert for the `text` tree. Registration is not
   automatic and may require changes to the subtype name or parameters.

Until all five hold, `text/x-iac` remains the interim label and no IANA action is taken.

## 6. What registration does not change

Registration does not change the file format, the version number, the grammar, the
diagnostic codes, or the extension. It changes only the label a transport uses. A file
that is valid under `text/x-iac` is byte-identical under `text/vnd.iac`.

## 7. References

- RFC 6838 — Media Type Specifications and Registration Procedures.
- RFC 6657 — Update to MIME regarding "charset" Parameter Handling in Textual Media
  Types.
- `spec/iac-1.0.md` §12 — media type and extension rules.
- `spec/appendix/security-considerations.md` — security review material.
- `testdata/conformance.json` — the conformance suite referenced in §5.
