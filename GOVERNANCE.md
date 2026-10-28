# Governance

How IAC changes, who decides, and what an implementer can rely on. This document is normative for the project's process, not for the format.

## Steward

The format originates with MIAR STAFF and is stewarded by the IAC maintainers — the people with merge rights on this repository, listed authoritatively in the repository's commit history and release notes. Stewardship is held by that maintainer group rather than by a foundation; the copyright line in [LICENSE](LICENSE) records where the text came from, and decisions are made under this document. There is no trademark claim over the acronym, and the steward's authority is the published spec and the conformance suite, not a licence to control implementations.

The steward is responsible for:

- the normative text in `spec/` and the registry in `registry/`;
- the conformance corpus in `testdata/` and the meaning of its outcomes;
- releases, version numbers, and the CHANGELOG;
- running the RFC process below and applying lazy consensus;
- keeping the licence grants in place (spec text CC BY 4.0, reference code Apache-2.0, examples CC0-1.0).

The steward does not approve your product, certify your implementation, or review your files. Conformance is self-declared and testable: run the corpus, publish the result.

## Versioning

Versions are `MAJOR.MINOR`, plus a patch number for the repository's own releases. The spec version is what files declare:

| Change | Version | Rule |
|---|---|---|
| Typo, broken link, clarification that cannot change any conformance outcome | patch (`1.0.1`) | no RFC needed; the CHANGELOG records it |
| New `Type` value, new directive, new warning code, new informative appendix | minor (`1.1.0`) | RFC required |
| New record syntax, even optional; a change that alters the meaning of a valid file, rejects a previously valid file, or removes syntax | major (`2.0.0`) | RFC required, plus the breaking-change gate below |

**Compatibility promise.** A parser implementing minor `x` must read any conforming file from minor `y <= x` without loss of meaning. A parser meeting a file that declares a newer minor does not fail on the version line: it reports W007 and continues (spec §11). Only a newer major is fatal (E024).

That promise constrains what a minor release may add. Spec §11 limits a minor version to constructs that a 1.x parser can ignore or preserve: comments, directives, and registry values. Anything that changes record syntax is a major change — old parsers must reject it deliberately rather than misread it. In practice a 1.y construct therefore surfaces in a 1.x parser (`x < y`) as a warning: an unknown directive (W006), an unregistered `Type` (W005), or something ignorable in the comment namespace. A minor release that a 1.0 parser rejects with an error would break the promise, so it is not a minor release.

The deferred list in [RFC 0001 §4](rfcs/0001-standardize-iac-1.0.md#4-deferred-work) is a list of candidates, not a version commitment. An item that changes record syntax — `#RRGGBBAA` is the obvious case — cannot ship in a minor under this rule, so its RFC has to argue either for a major version or for an encoding that a 1.0 parser can ignore or preserve. Whatever the RFC concludes, the promise wins over the candidate's label.

**What a 1.x parser may not do:** infer a frame rate, treat centiseconds as frames, or reject a file because it declares a newer minor.

## Deprecation

Nothing is removed in the release that deprecates it.

1. The RFC marks the construct deprecated and names its replacement.
2. The spec text marks it deprecated in place, and the CHANGELOG records it under `Deprecated`.
3. It keeps parsing, with its existing diagnostic, for **at least one minor release**.
4. Removal happens only in the next major, and only if the deprecation has shipped for a full minor cycle.

The one-minor floor is the minimum, not a target: a construct in wide use can stay deprecated for several minors. Deprecation is not a warning code of its own; a deprecated construct keeps behaving exactly as before until it is removed.

## Maintainer roles

| Role | What they do | How to get it |
|---|---|---|
| Steward | Owns the spec, runs the RFC process, cuts releases, decides after lazy consensus | Appointed by the existing maintainers when the role falls vacant |
| Maintainer | Merge rights, reviews, release prep, registry updates | Nominated by a maintainer, no objection from the others in 7 days, evidence of sustained contributions |
| Reviewer | Reviews changes in a stated area (parser, converters, docs, corpus) | Asked by a maintainer; recorded in the repository |
| Contributor | Issues, PRs, conformance cases, RFC comments | Anyone; no application |

Maintainers who are inactive for 12 months move to emeritus status by their own agreement or by maintainer decision, and can be reinstated on request. A maintainer who violates the [Code of Conduct](CODE_OF_CONDUCT.md) is removed immediately by the remaining maintainers. Recusal is expected when a maintainer has a commercial interest in the outcome; vendor neutrality is a process requirement, not a slogan.

## RFC process

Every normative change starts as an RFC in `rfcs/`, using [rfcs/0000-template.md](rfcs/0000-template.md). The process is the one [RFC 0001](rfcs/0001-standardize-iac-1.0.md) itself followed.

1. **Proposal.** Open a pull request adding `rfcs/NNNN-short-title.md`. Numbering is sequential; claim the next free number when you open the PR. Status starts as `Draft`.
2. **Discussion.** Comment on the PR, not in chat, so the record survives. The author edits the RFC in place; there are no comment threads inside the document.
3. **Review.** When the author believes it is ready, they move the status to `Review` and ask for a decision.
4. **Comment period.** A minimum of **10 calendar days** for a minor change, **20** for a major or a breaking change. The clock starts when the comment period is announced on the PR, not when the RFC was opened.
5. **Decision.** See lazy consensus below.
6. **Merge.** An accepted RFC is merged with its status set to `Accepted`. The implementation work lands as separate PRs that cite the RFC; the RFC itself is never rewritten after acceptance except for typographical fixes, which are recorded in the CHANGELOG as editorial.
7. **Supersession.** A later RFC may supersede an accepted one; the old document keeps its text and gains `Superseded by NNNN` in its header.

Statuses: `Draft`, `Review`, `Accepted`, `Rejected`, `Withdrawn`, `Superseded`.

An RFC that changes the grammar, the field semantics, the error taxonomy, the registry, or conformance outcomes must include a **Compatibility impact** section: what changes for existing files, what a 1.x parser does with a file that uses the new thing, and which conformance cases are added or changed. An RFC without that section is not ready for `Review`.

Editorial errata do not need an RFC: typos, dead links, formatting, and clarifications that provably cannot change a conformance outcome ship as a patch with a CHANGELOG entry. If you are unsure which it is, it is an RFC.

### Lazy consensus

A decision is made when the comment period closes and no maintainer has raised a substantive, unresolved objection. Silence is assent — there is no quorum to assemble and no vote to schedule.

- An objection must state which requirement or existing behaviour it breaks, or which concrete harm it causes. "I don't like it" is a comment, not an objection.
- The author must answer every objection in the PR. An unanswered objection blocks acceptance.
- If an objection survives discussion and the maintainers cannot resolve it, the steward decides, states the reasoning in the PR, and records it in the RFC. A split maintainer group is not a reason to stall indefinitely: a documented decision that can be superseded is better than an open question.
- A rejected RFC is not deleted. It stays in `rfcs/` with `Rejected` and the reason, because the reason is the useful part.

## Breaking changes

A breaking change is any change that makes a previously valid file invalid, changes the meaning of a valid file, or changes a conformance outcome that existing tools rely on. Removing a deprecated construct is also breaking.

To approve one:

1. An RFC with a **Compatibility impact** section, including a migration path for existing files.
2. A full comment period of at least 20 days, announced explicitly as a breaking change.
3. Approval by the steward and at least **two maintainers who are not the author**, each recorded on the PR. One approval is not enough.
4. A deprecation cycle of at least one minor release, on the deprecation terms above, unless the construct is unsafe to keep parsing at all — and then the RFC must say why.
5. Conformance cases added that pin both the old behaviour (still accepted during deprecation) and the new one.
6. A reference implementation that implements the change, or a merged PR that does, before the major release ships.

A major release with a breaking change and no working reference implementation is not released.

## Changes to this document

This document changes by RFC like anything else, except for typographical fixes. The steward may correct roles and names without an RFC when a person changes role, recording it in the CHANGELOG.

## Licensing

By contributing you agree that your contribution is licensed as the file it touches: spec text and docs under CC BY 4.0, code under Apache-2.0, example `.iac` files under CC0-1.0. Commits carry a Developer Certificate of Origin sign-off; see [CONTRIBUTING.md](CONTRIBUTING.md). There is no copyright assignment.
