# Adoption playbook

An ordered plan for taking IAC 1.0 from a frozen spec to something a studio can depend on. It is written for whoever holds the work, not for a marketing page: every step has a deliverable, an owner, and a gate that says whether it worked.

Roles below are hats, not headcount — one person can wear several. **Steward** owns the spec and the RFC process. **Tooling** owns the reference implementation and converters. **Docs** owns the guides. **Loc** is a localisation lead who can speak for vendor workflows. **Community** owns outreach and naming.

## (a) Freeze the spec and ship the reference implementation

Everything else depends on this, so it goes first and nothing else starts until it is true.

- Tag 1.0.0. Freeze the spec text, the ABNF grammar, and the registry at that tag.
- Ship `tools/iac_lint.py` as a single file with no third-party dependencies, so a studio can vendor it into an existing build without a package manager review. No npm or PyPI release in this phase — those are planned, and a package that does not exist yet must not appear in install instructions.
- Run the conformance corpus in CI on every change, for the Parser and Producer roles. A red suite blocks the tag.
- Publish the compatibility promise where an adopter will find it: README, spec §11, and this document. It is the reason a studio can write files today.
- Cut release notes that list the 1.0 decisions, not a feature list — the CHANGELOG is the record.

**Gate:** a new machine can clone the repo and validate the examples with no install step, and CI shows the corpus passing.

## (b) Editor support

The first hour of any new format is whether the editor fights you. Do this before converters; it is cheap and it decides whether anyone writes a test file.

- A TextMate grammar (`.tmLanguage.json`) published as a VS Code extension, plus a plain TextMate bundle for everything else. Highlight: version marker, directives, comments, `#!cut` retired lines and their payloads, `AudioName`, quoted text, `|` delimiters, time tokens, colour, `Type`.
- Snippets for a record, a cue, a retired record, and a file header. Four snippets is enough.
- File association: `files.associations` guidance for VS Code, `*.iac` in the shared-mime-info step below, and a note in the quickstart.
- Deliberately not in scope for 1.0: a language server, semantic completion for track names, diagnostics-on-type. A grammar that highlights correctly is worth more than a half-finished server.

**Gate:** someone who has never seen the format installs the extension and gets correct highlighting on all three examples in under five minutes.

## (c) Converters in both directions

Migration is the adoption story: nobody starts a project in a new format, they move an existing one into it.

- Keep `from-srt` minimal and boring.
- Add SRT export, VTT import and export, and ASS import. Export is not an afterthought: a pipeline that can only move in one direction is a trap, and the third step of any trial is "get it back out for the player".
- Every converter reports what it dropped, per file, in a form a human reads. Silent loss is the failure mode that ends trials.
- Test each converter against the lossiness table in [conversion.md](guides/conversion.md) with fixtures that have touching boundaries, a retired `#!cut` line, mixed encodings, and ASS with alpha.

**Gate:** an existing SRT-based build can round-trip a real subtitle file through IAC and produce output that passes its own QA, with a written list of what changed.

## (d) Localisation-tool integration

CAT tools ingest custom formats through regex profiles. That works only if the profile's assumptions hold, so be precise about which ones.

A single regex cannot implement the quote-aware record split — the split is the whole problem, which is why the reference parser exists. The workable integration is two-stage:

1. **Flatten** with a real parser: one line per cue, three tab-separated columns — record name, cue index, text. Skip `#!cut` lines unless the vendor explicitly wants to translate them; they are comments, and a translator working on a retired line is usually wasted effort. This is a derived intermediate, not IAC, and it is disposable.
2. **Import** the flat file with a trivial filter: `^(?<record>[^\t]+)\t(?<index>\d+)\t(?<text>.*)$`. Any tool that accepts regex custom formats can match that.
3. **Reassemble** on export by `record` + `index`, with the export refusing to write if a cue is missing or duplicated.

For tools that must read canonical `.iac` directly, this profile matches a record line because the tail is constrained:

```text
^(?<name>[^"].+?) : \{(?<cues>.*)\} : (?<color>\[#[0-9A-Fa-f]{6}\])(?: : (?<type>\w+))?$
```

It works because `AudioName` may not contain ` : ` and the cue set is greedy to the last brace. It is a parser for well-formed files only: it does not validate, does not split cues, and will accept nonsense in the cue set. It also matches nothing on a `#!cut` line, which starts with `#` and is a comment first — say that in the profile's description rather than letting a vendor discover it.

Also prepare an XLIFF export for vendors whose workflow is translation-exchange rather than subtitle-file. That is a converter, not a new format, and it is the path most likely to be accepted without negotiation.

**Gate:** one vendor or one internal translation team imports and exports a real project without hand-editing files.

## (e) Media-type registration

`text/x-iac` is interim and unregistered (spec §12). Unregistered types work, but proxies, editors, and asset pipelines guess, and guessing is what the format is trying to avoid.

- Submit the registration template in [spec/appendix/media-type.md](../spec/appendix/media-type.md) for IANA media type review. The intended registered name is `text/vnd.iac`; `text/x-iac` is the interim placeholder (spec §12). Expect the review to take months, and expect questions about why it is not `text/plain`.
- Add a shared-mime-info entry: glob `*.iac`, magic `#!iac `, subclass of `text/plain`, plus an icon so file managers stop showing a blank page.
- Register the extension with GitHub Linguist, VS Code, and your asset pipeline's importer list. Each one is a five-minute change that removes a support ticket.
- Keep `.txt` as read-only legacy: parse it, never produce it (RFC 0001 §D16).

**Gate:** a double-clicked `.iac` file opens in a text editor on a clean desktop, and a browser or CDN serves it as text rather than a download.

## (f) Naming

"IAC" is Infrastructure as Code in every search engine, conference talk, and job posting. The format cannot win that query, and pretending otherwise wastes a year.

- Every user-facing title carries "subtitle": `IAC subtitle format`, `IAC subtitle parser`. Never bare "IAC" in a title, package name, or README heading.
- Package names, when they exist, are `iac-subtitle` / `iac_subtitle` — not `iac`, which is taken and ambiguous.
- Repository description, docs titles, and issue templates use the full phrase. The acronym alone stays inside the repository, where context is already established.
- Do not buy into tag wars or police casual use of "IAC" in chat. The goal is that a search for "subtitle format with inline timing" reaches the spec, not that the acronym becomes unambiguous.
- When citing the format externally, link the spec rather than restating the grammar — one canonical URL per claim.

**Gate:** searching "IAC subtitle format" returns the repository in the first page of results, and "IAC format" returns Infrastructure as Code — which is expected and acceptable.

## (g) 90-day plan

Week numbers are relative to the 1.0.0 tag. Gates are cumulative: a week that misses its gate delays the next, it does not run in parallel.

| Week | Work | Owner | Gate |
|---|---|---|---|
| 1 | Tag 1.0.0, freeze spec, run corpus in CI, release notes | Steward | Clone-to-validate works with no install |
| 2 | Docs pass: README, quickstart, and error reference verified against the shipped build by someone outside the project | Docs | A reader who knows SRT can validate a file unaided |
| 3 | TextMate grammar and VS Code extension; snippets; file associations | Tooling | Five-minute install, correct highlighting on all examples |
| 4 | SRT export; converter loss reports; fixtures for boundaries and encodings | Tooling | Round-trip of a real SRT file passes its own QA |
| 5 | VTT and ASS import; colour conversion tests including alpha | Tooling | Lossiness table verified against fixtures |
| 6 | Flat-export/CAT profile; XLIFF export spike; vendor conversation starts | Loc | One vendor imports a sample project |
| 7 | shared-mime-info entry; Linguist registration; media-type submission | Community | `.iac` opens as text on a clean desktop |
| 8 | Naming pass across repo, docs, and package metadata; search check | Community | "IAC subtitle format" finds the spec |
| 9 | Trial with one real production: master in IAC, exports to its delivery targets | Steward + Loc | A shipped build used an `.iac` master |
| 10 | Fix what the trial found; 1.0.x patch if needed | Steward | Trial issues closed or scheduled |
| 11 | Publish conformance results and a "who implements what" list | Tooling | List has at least one entry that is not ours |
| 12 | Retrospective; decide 1.1 scope from real usage, not from the deferred list | Steward | 1.1 RFC drafted or explicitly deferred |

Two rules for the plan itself: do not start 1.1 work before week 12, and do not ship a feature that the conformance corpus cannot express.

## (h) Success metrics

Measure adoption, not enthusiasm. Four numbers, each with a way to count it that does not depend on self-reporting.

| Metric | How to count | 90-day target |
|---|---|---|
| Files in the wild | Public repositories containing `.iac` files outside this project (code search, weekly) | 3 |
| Third-party implementations | Independent parsers or producers that pass the conformance corpus, listed in the repo | 1 |
| Conformance runs | CI runs of the corpus reported by adopters (link or badge in their repo) | 2 |
| Non-steward contributions | Merged PRs from outside the originating organisation | 3 |

Targets are provisional and deliberately low. A format with one external parser and three real files is ahead of a format with a thousand stars; the reverse is the usual vanity metric. If week 12 arrives with zero external implementations, the honest response is to ask why — most likely the converters or the editor story, both of which are fixable — rather than to lower the bar or announce a foundation.

Do not report download counts of anything that is not published. Do not claim vendor support that a vendor has not stated. Adoption documents age badly when they are optimistic; this one should still be true in a year.
