# Agent Loop Instructions: Evidence-Aligned Region Detection

## Purpose

Use the human evidence repository to improve region detection without repeatedly making production code changes. The agent should loop on comparison, failure analysis, and simulated candidate strategies first. Detector code changes are allowed only after the agent presents findings and the user approves the proposed implementation.

## Primary Rule

Do not edit production detector code during the evidence-learning loop.

Production code includes:

- `src/spatial/**`
- `src/evidence/**`
- `viewer/**`
- `tests/**`
- project source-of-truth documentation, unless the requested task is documentation-only

During the loop, the agent may read these files and may create temporary analysis artifacts under `reports/`. It must not patch detector, evaluator, viewer, or test behavior until the user approves a specific implementation proposal.

## Required Inputs

Use the current human evidence export and current detector reports:

- `Drawing Evidence Process/Exports_Test.json`
- `reports/evidence_region_evaluation_summary.json`
- `reports/evidence_failure_patterns.json`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

If any report is stale or missing, regenerate comparison data only as needed for analysis. Avoid full project test runs until implementation is approved.

## Evidence Semantics

The loop must preserve these assumptions:

- Human evidence boxes are spatial/logical comparison regions, not pixel-perfect masks.
- Human evidence may overlap or nest.
- A broad container region and smaller internal content regions can both be correct.
- Irregular objects may be represented by rectangular boxes that include background or unrelated pixels.
- Score and text regions can be valid even when internal digits or displayed words vary later.
- Evidence is intended to teach region boundaries and grouping behavior, not semantic labels.

## Loop Workflow

Repeat these steps without editing production code:

1. Establish the current baseline.
   - Record matched, missed, extra, mean alignment, mean match score, and worst frames.
   - Separate geometry-only results from learned-prior results.

2. Bucket failures.
   - Group misses by actionable pattern, such as:
     - missing child region inside broad container;
     - under-grouped pieces inside a human region;
     - partial-overlap geometry mismatch;
     - irregular object or container ROI mismatch;
     - over-grouped detector region contains human region;
     - missing isolated human region;
     - internal-gap text or row grouping mismatch;
     - missing broad container or logical region.

3. Identify candidate strategies.
   - Propose changes as hypotheses, not patches.
   - Each hypothesis should name the behavior it would change, the failure bucket it targets, and the likely risk.
   - Favor strategies that can improve many evidence frames, not one screenshot.

4. Simulate or score candidates outside production code.
   - Use read-only adapters, scratch scripts, or report-generation helpers.
   - Cache expensive detector outputs where practical.
   - Compare candidate settings or derived boxes against the same evidence export.
   - Do not modify `src/spatial`, `src/evidence`, viewer code, or tests during this phase.

5. Rank candidate strategies.
   - Prefer candidates that improve aggregate alignment, reduce missed regions, and do not create excessive extra regions.
   - Track the exact failure buckets improved or worsened.
   - Reject candidates that only move errors from one bucket to another without net improvement.
   - Reject candidates that depend on directly replaying the exact evidence frame as detector output.

6. Check regression risk.
   - Confirm that locked Stage 3, Stage 4A, and Stage 4B behavior would remain conceptually intact.
   - Treat Stage 4C as validating unless the source of truth says it has been relocked.
   - Note any likely test additions or updates, but do not make them yet.

7. Stop and report before implementation.
   - When one or more candidates look meaningfully better, present the findings to the user.
   - Ask for approval before making any code changes.

## Confidence Standard

The agent may say it is comfortable proposing implementation only when it can show:

- a current baseline;
- at least one candidate strategy compared against that baseline;
- the expected metric movement;
- which failure buckets improve;
- which frames or buckets regress;
- why the improvement is not merely overfitting one evidence example;
- which files/functions would likely change;
- which tests and reports would be run after implementation.

Confidence does not require perfect evidence alignment. It does require a clear aggregate improvement story and an honest risk statement.

## Findings Report Format

Before implementing, present:

```text
Evidence Alignment Findings

Baseline:
- geometry-only: ...
- learned-prior: ...

Dominant failures:
- ...

Candidate strategies compared:
- Candidate A: target, expected impact, risk
- Candidate B: target, expected impact, risk

Recommended implementation:
- ...

Why this is worth coding:
- ...

Likely files/functions to change:
- ...

Validation after approval:
- ...

Approval request:
May I implement the recommended change?
```

## Implementation After Approval

Only after explicit user approval:

- patch the smallest necessary production files;
- update or add focused tests;
- regenerate evidence reports;
- run the appropriate automated tests;
- summarize actual metric movement versus the predicted movement;
- document meaningful source-of-truth changes.

## Anti-Patterns

Avoid:

- patching detector logic first and checking later;
- tuning to a single pasted screenshot;
- treating human boxes as exact pixel masks;
- treating overlapping evidence boxes as contradictions;
- reporting only one score without missed/extra tradeoffs;
- increasing extra regions heavily while claiming success from a small match increase;
- silently changing locked earlier-stage behavior;
- asking the user to manually validate every failed frame.
