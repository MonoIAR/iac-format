# RFC NNNN — Title in sentence case

- **Status:** Draft
- **Date:** YYYY-MM-DD
- **Impact:** patch | minor | breaking

> Status moves `Draft` → `Review` → `Accepted` | `Rejected` | `Withdrawn`.
> `Impact` follows the versioning table in [GOVERNANCE.md](../GOVERNANCE.md); a
> patch-level editorial fix needs no RFC.

## Abstract

One paragraph: what is undecided or broken today, what this RFC decides, and what an
implementer must do differently afterwards. A reader should be able to stop here and
know whether the rest concerns them.

## 1. Problem

State the defect, not the solution. Cite the current text and say what goes wrong
because of it.

| # | Defect | Consequence |
|---|---|---|
| 1 | The current specification says ... | ... |

> This table is the part reviewers test. "We think it would be nicer" is not a
> defect; "two implementations disagree by one centisecond on every cue" is. If
> there is no observable consequence, there is no RFC.

Also state what this RFC does **not** change. Scope creep is the usual reason an RFC
stalls.

## 2. Decisions

One numbered decision per question. Keep decisions independent: a reviewer should be
able to accept D2 and reject D3 without the document collapsing.

### D1 — Short imperative title

**Decision.** What is true after this RFC. Use RFC 2119 keywords where the
implementation must do something specific.

**Why.** Why this and not the obvious alternative. Name the alternative and say what
it costs.

**Consequences.** Testable statements: what MUST happen, what is forbidden, which
error code applies, which registry entry is added, which conformance case pins it.

## 3. Compatibility impact

- **Existing files:** unchanged, or which files change and how.
- **Older parsers:** the exact code an implementation at the previous version reports
  — E015 only for a major bump, W007 for a newer minor, W005/W006 for registry and
  directive additions.
- **Conformance cases:** which cases are added or changed. A normative change without
  a case is incomplete.
- **Registry:** entries added to [`spec/registry.md`](../spec/registry.md).
