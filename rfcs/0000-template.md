# RFC NNNN — Title in sentence case

- **Status:** Draft
- **Version:** 1.0
- **Date:** YYYY-MM-DD
- **Supersedes:** none
- **Impact:** minor

> Status moves `Draft` → `Review` → `Accepted` | `Rejected` | `Withdrawn`. `Version` is the revision of this document, bumped on substantive edits. `Impact` is `patch` (editorial, no conformance change), `minor` (additive), or `breaking` — see [GOVERNANCE.md](../GOVERNANCE.md). Use a patch number, not an RFC, for an editorial fix.

## Abstract

One paragraph: what is undecided or broken today, what this RFC decides, and what an implementer must do differently afterwards. A reader should be able to stop here and know whether the rest concerns them.

## 1. Problem

State the defect, not the solution. Cite the current text and say what goes wrong because of it.

| # | Defect | Consequence |
|---|--------|-------------|
| 1 | The current specification says "split on ` : `" | Dialogue containing ` : ` cannot be represented |
| 2 | | |

> This table is the part reviewers test. "We think it would be nicer" is not a defect; "two implementations disagree by one centisecond on every cue" is. If there is no observable consequence, there is no RFC.

Also state what this RFC does **not** change. Scope creep is the usual reason an RFC stalls.

## 2. Decisions

One numbered decision per question, each with the same three parts: the decision itself, why it beats the alternatives, and its testable consequences. The normative consequences are what the spec and the conformance corpus will enforce.

### D1 — Short imperative title

**Decision.** What is true after this RFC. Use RFC 2119 keywords where the implementation must do something specific.

**Rationale.** Why this and not the obvious alternative. Name the alternative and say what it costs.

**Normative consequences.** Bullet list of testable statements: what MUST happen, what is forbidden, which error code applies, which registry entry is added, which example or conformance case pins it.

**Error codes.** New, changed, or removed codes from the taxonomy in [spec/iac-1.0.md](../spec/iac-1.0.md). "None" is a valid answer.

**Compatibility impact.** What happens to existing files, and what a parser written against the previous version does when it meets the new construct. "Degrades to W006" is an answer; "parsers will cope" is not.

### D2 — Next decision

Repeat the structure. Keep decisions independent: a reviewer should be able to accept D2 and reject D3 without the document collapsing.

## 3. Compatibility impact

The summary the release depends on:

- **Existing files:** unchanged, or which files change and how.
- **Older parsers:** the exact code an implementation at the previous version reports — E024 only for a major bump, W007 for a newer minor, W005/W006 for registry and directive additions.
- **Conformance cases:** which cases are added, and which existing expected outcomes change. An RFC that changes a normative outcome without adding a case is incomplete.
- **Deprecation:** if anything is being removed, the release that deprecates it and the release that removes it. Minimum one minor release in between.
- **Registry:** entries added to [registry/types.md](../registry/types.md) or [registry/directives.md](../registry/directives.md).

For a `patch` impact RFC, this section says why no conformance outcome can change.

## 4. Deferred

Ideas that came up, were judged out of scope, and would otherwise be re-proposed next month. One line each, with the reason. "Deferred because it needs a migration story" is enough; do not design it here.

## 5. Follow-up work

The concrete artefacts this RFC creates, as a numbered list, each with a path that will exist: spec sections, grammar productions, registry files, conformance cases, tooling changes, docs pages.

1. `spec/...` — what changes in the normative text.
2. `testdata/...` — cases that pin the decision.
3. `tools/...` — reference implementation changes.
4. `docs/...` — user-facing documentation that becomes wrong or necessary.
