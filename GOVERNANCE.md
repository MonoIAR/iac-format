# Governance

How IAC changes, who decides, and what an implementer can rely on. This document is
normative for the project's process, not for the format.

## Steward

The format is stewarded by the repository's maintainer, who owns the normative text in
`spec/`, the conformance corpus in `testdata/`, and the release record. Conformance is
self-declared and testable: run the corpus, publish the result. The steward does not
certify implementations, approve products, or review your files.

## Versioning

Versions are `MAJOR.MINOR`, plus a patch number for repository releases of the same
specification text.

| Change | Version | Rule |
|---|---|---|
| Typo, broken link, or a clarification that cannot change a conformance outcome | patch (`1.0.1`) | no RFC needed; the changelog records it |
| New `Type` value, new directive, new warning code, new informative page | minor (`1.1.0`) | RFC required |
| New record syntax, or any change that rejects a previously valid file or changes its meaning | major (`2.0.0`) | RFC required, plus the breaking-change gate below |

**Compatibility promise.** A parser implementing minor `x` must read any conforming
file from minor `y <= x` without loss of meaning. A parser meeting a file that declares
a newer minor does not fail on the version line: it reports W007 and continues. Only a
newer major is fatal (E015).

That promise constrains what a minor may add. A minor release may introduce only
constructs a 1.x parser can ignore or preserve: comments, directives, and registry
values. Anything that changes record syntax is a major change, so old parsers reject it
deliberately instead of misreading it.

## Deprecation

Nothing is removed in the release that deprecates it.

1. The RFC marks the construct deprecated and names its replacement.
2. The specification marks it deprecated in place, and the changelog records it.
3. It keeps parsing, with its existing diagnostic, for at least one minor release.
4. Removal happens only in the next major release.

The one-minor floor is a minimum, not a target. A deprecated construct keeps behaving
exactly as before until it is removed; deprecation is not a warning code of its own.

## RFC process

Every normative change starts as an RFC in `rfcs/`, using
[rfcs/0000-template.md](rfcs/0000-template.md). The process is the one
[RFC 0001](rfcs/0001-standardize-iac-1.0.md) followed.

1. **Proposal.** Open a pull request adding `rfcs/NNNN-short-title.md`. Numbering is
   sequential; claim the next free number.
2. **Discussion.** Comment on the pull request, not in chat, so the record survives.
   The author edits the RFC in place.
3. **Review.** Move the status to `Review` and ask for a decision.
4. **Comment period.** At least 10 calendar days for a minor change, 20 for a major or
   breaking one. The clock starts when the comment period is announced on the pull
   request.
5. **Decision.** Lazy consensus: the decision is made when the period closes and no
   maintainer has raised a substantive, unresolved objection. Silence is assent.
6. **Merge.** Set the status to `Accepted`. Implementation lands in separate pull
   requests that cite the RFC. An accepted RFC is not rewritten except for typographical
   fixes, which the changelog records as editorial.
7. **Supersession.** A later RFC may supersede an accepted one; the old document keeps
   its text and gains a `Superseded by NNNN` line in its header.

Statuses: `Draft`, `Review`, `Accepted`, `Rejected`, `Withdrawn`, `Superseded`.

An RFC that changes the grammar, field semantics, the error taxonomy, the registry, or
a conformance outcome must include a **Compatibility impact** section. Without it the
RFC is not ready for review.

## Breaking changes

A breaking change makes a previously valid file invalid, changes the meaning of a
valid file, or changes a conformance outcome that tools rely on. To approve one:

1. an RFC with a Compatibility impact section and a migration path;
2. a comment period of at least 20 days, announced as a breaking change;
3. approval by the steward and at least two maintainers who are not the author;
4. a deprecation cycle of at least one minor release, unless keeping the old construct
   is itself unsafe — and then the RFC says why;
5. conformance cases that pin both the old behaviour during deprecation and the new one;
6. a reference implementation that implements the change before the major release ships.

## Before 1.0 is announced

Nothing had been published when 1.0.0 was tagged, so one exception applies: duplicate
or superseded decision records may be consolidated into
[RFC 0001](rfcs/0001-standardize-iac-1.0.md) rather than kept as separate documents.
After the announcement, the supersession rule above applies unchanged.

## Licensing

By contributing you agree that your contribution is licensed as the file it touches:
specification text and docs under CC BY 4.0, code under Apache-2.0, example `.iac` files
under CC0-1.0. Commits carry a Developer Certificate of Origin sign-off; see
[CONTRIBUTING.md](CONTRIBUTING.md). There is no copyright assignment.
