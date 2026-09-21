# DMD Mask Optimization Project — Source of Truth

> **Purpose:** This file is the authoritative running state of the project.  
> Codex must read this file before beginning any development work.  
> When stages are completed, amended, split, added, or rejected, update this file so future work does not depend on chat history.

---

## 1. Project Goal

Build a program that analyzes raw pinball DMD frame data and determines where masks are useful for future DMD colorization.

The program itself does **not** colorize the DMD.

Its job is to learn how a ROM uses the display and determine:

- what logical DMD sequences exist;
- where those sequences occur;
- which sequences or frames are related;
- which information is structurally stable;
- which information varies between occurrences;
- which frames/sequences need no mask at all;
- where masks would allow reusable matching despite variable information;
- which exclusion regions should form those masks;
- whether masks cause unwanted matches;
- and which final mask set offers the best useful coverage with the least unnecessary masking.

A mask is a **spatial exclusion filter**.

It does not assign colors.

It tells a later matching/colorization system:

> Ignore this spatial area when determining whether this display matches a known colorization target.

---

## 2. DMD Input Definition

Initial target DMD:

- Width: **128 pixels**
- Height: **32 pixels**
- Pixel states: **0, 1, 2, 3**

Interpretation:

- `0` = off / black
- `1` = low intensity
- `2` = medium intensity
- `3` = high intensity

Expected frame-dump format:

- each frame begins with a `0x` prefix followed by 8 hexadecimal digits;
- DMD pixel data follows;
- a blank line terminates the frame;
- a complete final frame may also terminate at EOF without a trailing blank line.

Preserve two representations internally:

### Exact brightness representation

Values remain exactly:

`0, 1, 2, 3`

### Binary structural representation

- `0` = OFF
- `1` = ON, meaning source value `1–3`

The original 0–3 brightness data must never be discarded.

---

## 3. Central Mask Principle

A changing DMD region does **not** automatically require a mask.

There are two fundamentally different types of change.

### 3.1 Intended visual change

Example:

- Animation Frame 1
- Animation Frame 2
- Animation Frame 3
- Animation Frame 4

If every animation frame will ultimately be colorized individually, then the changing animation itself is not information that should be ignored.

Those frames may require **no mask**.

### 3.2 Variable data inside reusable structure

Example:

```text
PLAYER 1
125,000
```

later:

```text
PLAYER 1
247,500
```

If both displays should reuse the same underlying colorization despite score changes, then the score region may need to be excluded during matching.

That is a strong mask candidate.

### Locked distinction

> **Dynamic content and mask-required content are not the same thing.**

The program must determine whether masking is necessary **before** generating or optimizing a mask.

---

## 4. Possible Final Outcomes

Every analyzed frame, sequence, or family should eventually be classifiable as one of the following.

### NO MASK — STATIC / EXACT

No relevant variable information exists.

The display can be matched/colorized directly.

### NO MASK — INDIVIDUALLY COLORIZED ANIMATION

The sequence changes through time, but each animation frame/state is intended to be treated as its own visual target.

The changing animation is meaningful artwork, not unwanted variability.

### MASK REQUIRED — VARIABLE FIELD

Part of the display should remain reusable while another part changes between occurrences.

Typical examples may eventually include scores, initials, player numbers, ball numbers, credits, countdown values, or other variable fields.

These semantic labels must not be hard-coded as assumptions.

### MASK POSSIBLY USEFUL

Evidence suggests reusable structure exists, but variability or collision risk is not yet sufficiently understood.

### UNSAFE / UNCERTAIN

The system cannot yet determine a safe strategy.

Do not force a mask decision.

---

## 5. Development Philosophy

Develop one validated component at a time.

Every stage must follow:

```text
IMPLEMENT
   ↓
AUTOMATED TEST
   ↓
REAL-DATA TEST
   ↓
VISUAL VALIDATION
   ↓
DOCUMENT
   ↓
LOCK
   ↓
NEXT STAGE
```

Once a stage passes, its expected behavior and public interfaces are considered locked.

Do not casually rewrite working components later.

If a locked stage must change:

1. identify the demonstrated failure;
2. show evidence;
3. propose the smallest possible change;
4. rerun that stage's tests;
5. rerun dependent regression tests;
6. document the impact in this file.

Do not build future-stage functionality early unless required by the current stage.

---

## 6. High-Level Architecture

```text
Raw DMD Dump
      ↓
Frame Parser
      ↓
Normalized Frame Store
      ↓
Forensic Viewer
      ↓
Spatial Feature Discovery
      ↓
Spatial Region Discovery
      ↓
Temporal Region Tracking
      ↓
Behavioral Analysis
      ↓
Sequence Segmentation
      ↓
Sequence Identity + Occurrences
      ↓
Related Sequence / Family Discovery
      ↓
Cross-Occurrence Variability
      ↓
MASK NECESSITY CLASSIFICATION
      │
      ├── No mask required
      │
      ├── Individually colorized frames
      │
      ├── Mask beneficial
      │
      └── Uncertain
      ↓
Mask Candidate Generation
      ↓
Mask Matching + Collision Analysis
      ↓
Mask Optimization
      ↓
Full-ROM Validation
      ↓
Final Recommendations
```

---

# 7. Running Project State

## Status legend

- `NOT STARTED`
- `IN PROGRESS`
- `VALIDATING`
- `LOCKED`
- `NEEDS REVISION`
- `SUPERSEDED`

| Stage | Name | Status | Locked Date | Notes |
|---|---|---:|---|---|
| 0 | Project Foundation | LOCKED | 2026-09-19 | Application shell, project structure, configuration, logging, safe output directories, tests, and run instructions are in place. |
| 1 | Frame Parser | LOCKED | 2026-09-19 | Raw dumps with `0x########` headers parse into deterministic frame objects with exact 0-3 and binary matrices; 17 automated tests and real sample dump pass. |
| 2 | Forensic DMD Viewer | LOCKED | 2026-09-19 | Web viewer loads real dataset, renders 128x32 exact and binary frames, supports navigation/playback, and passed human visual confirmation. |
| 3A | Lit Pixel Components | LOCKED | 2026-09-19 | Raw 8-connected lit components implemented, exposed in viewer pixel/box overlays, and passed human visual confirmation. |
| 3B | Component Relationship Evidence | LOCKED | 2026-09-20 | Pairwise relationship evidence implemented, exposed through viewer API/review panel, and passed human validation. |
| 3C | Candidate Composite Boxes | LOCKED | 2026-09-20 | Pair-based candidate boxes implemented with cumulative threshold review, selectable candidate rows, and passed human validation. |
| 3D | Viewer Review Tools | LOCKED | 2026-09-20 | Raw component review panel, readable ID labels, crisp overlay boxes, and thicker review outlines passed human validation. |
| 4 | Spatial Region Discovery | NOT STARTED |  |  |
| 5 | Temporal Region Tracking | NOT STARTED |  |  |
| 6 | Temporal Behavior Analysis | NOT STARTED |  |  |
| 7 | Structural Continuity / Anchors | NOT STARTED |  |  |
| 8 | Sequence Segmentation | NOT STARTED |  |  |
| 9 | Human Ground Truth / Calibration | NOT STARTED |  |  |
| 10 | Sequence Identity and Occurrences | NOT STARTED |  |  |
| 11 | Sequence Representation | NOT STARTED |  |  |
| 12 | Related Sequence / Family Discovery | NOT STARTED |  |  |
| 13 | Cross-Occurrence Variability | NOT STARTED |  |  |
| 14 | Mask Necessity Classification | NOT STARTED |  |  |
| 15 | Mask-Necessity Visual Validation | NOT STARTED |  |  |
| 16 | Mask Candidate Generation | NOT STARTED |  |  |
| 17 | Mask Matching Engine | NOT STARTED |  |  |
| 18 | Collision Analysis | NOT STARTED |  |  |
| 19 | Individual Mask Optimization | NOT STARTED |  |  |
| 20 | Mask Set Optimization | NOT STARTED |  |  |
| 21 | Full-ROM Validation | NOT STARTED |  |  |
| 22 | Multi-ROM Generalization | NOT STARTED |  |  |
| 23 | Final Export | NOT STARTED |  |  |

---

# 8. Stage Definitions

## Stage 0 — Project Foundation

### Goal

Create a clean project structure and testing environment.

Suggested structure:

```text
project/
│
├── src/
│   ├── parsing/
│   ├── frames/
│   ├── spatial/
│   ├── temporal/
│   ├── sequences/
│   ├── families/
│   ├── masks/
│   └── optimization/
│
├── viewer/
├── tests/
├── datasets/
├── reports/
└── docs/
```

Implement:

- configuration;
- logging;
- test runner;
- safe output directories;
- basic documentation.

No DMD analysis yet.

### Lock condition

Application launches and test infrastructure works reliably.

---

## Stage 1 — Frame Parser

### Goal

Convert the raw dump into reliable frame objects.

Each frame stores:

```text
frame number
original header
128 × 32 exact pixel matrix
128 × 32 binary on/off matrix
```

Valid exact values:

`0, 1, 2, 3`

### Tests

Test:

- dimensions;
- frame count;
- headers;
- blank-line termination;
- valid pixel states;
- malformed frames;
- truncated files;
- invalid symbols.

Create artificial files where expected results are known exactly.

### Lock condition

The same source always produces the same normalized frames.

---

## Stage 2 — Forensic DMD Viewer

### Goal

Create the primary human-validation interface.

Support:

- dataset loading;
- actual 128×32 DMD display;
- previous/next frame;
- jump to frame;
- playback;
- pause;
- exact 0–3 brightness display;
- binary on/off display.

Future analytical overlays will be added here.

### Lock condition

Rendered frames are proven to correspond correctly to source data.

---

## Stage 3 — Low-Level Spatial Features

### Goal

Identify geometric structures inside individual frames in small validated substages.

This stage is intentionally split because component detection, connection evidence, and useful bounding boxes are complex and should not be solved in one pass.

### Stage 3A — Lit Pixel Components

Goal:

Detect raw connected components from binary frames only.

Connectivity rule:

- Lit pixels are connected when they touch by edge or corner.
- This is 8-connectivity.
- Diagonal contact is sufficient for the same raw component.

Scope:

- contiguous lit-pixel components;
- component ID;
- component area;
- occupied pixels;
- raw bounding box;
- width and height;
- centroid.

Explicitly out of scope:

- merging nearby components;
- component relationship scoring;
- candidate composite boxes;
- optimal bounding boxes;
- text/score/player/credit/initial semantics;
- spatial region grouping;
- temporal tracking;
- sequence detection;
- mask classification or masking.

Viewer requirement:

- overlay raw component bounding boxes;
- show component IDs or inspectable component details where practical;
- preserve the Stage 2 exact/binary display and navigation behavior.

Lock condition:

- every raw component overlay matches the visible lit-pixel island it came from.

### Stage 3B — Component Relationship Evidence

Goal:

Calculate relationships between raw components without grouping them yet.

Possible evidence:

- distance between components;
- horizontal or vertical adjacency;
- overlap along X/Y axes;
- size similarity;
- alignment evidence;
- containment or touching edges where applicable.

Lock condition:

- relationship evidence is inspectable and numerically sane.

### Stage 3C — Candidate Composite Boxes

Goal:

Propose possible grouped bounding boxes for review without deciding final spatial regions.

Scope:

- candidate boxes around nearby or aligned components;
- alternate candidates at different connection distances;
- retained evidence explaining why components were connected;
- separate overlays for raw components and candidate composite boxes.

Important rule:

- Do not call these boxes final or optimal. Stage 3C produces candidates only. Final coherent spatial region decisions belong to Stage 4.

Lock condition:

- candidate boxes are useful for review and do not hide the raw component evidence.

### Stage 3D — Viewer Review Tools

Goal:

Improve visual review so Stage 3 outputs can be inspected without guessing.

Scope:

- toggle raw component boxes;
- toggle component IDs;
- toggle candidate composite boxes when Stage 3C exists;
- click or hover component details where practical;
- maintain frame navigation, playback, exact display, and binary display.

Lock condition:

- the operator can inspect examples quickly and understand what the detector is doing.

Do not assign semantics such as score, player, credits, or initials.

The program knows geometry only.

### Stage 3 Overall Boundary

Stage 3 should produce raw geometry and reviewable evidence only.

Spatial region grouping belongs to Stage 4.

Temporal behavior belongs to later stages.

Mask necessity and mask generation are far out of scope.

---

## Stage 4 — Spatial Region Discovery

### Goal

Group low-level components into useful coherent regions.

A region should correspond to an area that behaves as a meaningful spatial unit.

Possible evidence:

- proximity;
- repeated positioning;
- overlapping locations;
- common movement;
- similar dimensions;
- repeated occupancy.

Store:

```text
region ID
bounding geometry
component membership
location
size
occupancy
persistence evidence
```

### Key human validation question

> Does everything grouped into this region reasonably belong together spatially?

### Lock condition

The program produces useful regions rather than whole-screen blobs or excessive pixel fragments.

---

## Stage 5 — Temporal Region Tracking

### Goal

Track spatial regions from frame to frame.

A tracked region may:

- remain unchanged;
- change contents;
- move;
- grow;
- shrink;
- disappear;
- reappear;
- split;
- merge.

Determine whether a region in one frame is related to one in later frames.

### Viewer requirement

Show region IDs through time.

### Lock condition

Region continuity through neighboring frames is reliable.

---

## Stage 6 — Temporal Behavior Analysis

### Goal

Describe how regions behave.

Possible descriptive behaviors:

- persistent stable;
- persistent changing;
- periodic;
- flashing;
- moving;
- progressive animation;
- appearing/disappearing;
- transient;
- uncertain.

### Locked rule

`dynamic` does **not** mean `mask required`.

### Lock condition

The system meaningfully describes temporal region behavior.

---

## Stage 7 — Structural Continuity / Anchors

### Goal

Identify features that provide continuity across frames.

An anchor is:

> A spatial or behavioral feature that helps establish that frames belong to the same logical context.

Anchors can be static or dynamic.

Animations may have no static anchor at all; temporal progression can provide behavioral continuity.

### Lock condition

Candidate continuity evidence corresponds to visually sensible DMD behavior.

---

## Stage 8 — Sequence Segmentation

### Goal

Determine where logical DMD sequences begin and end.

Use:

- spatial structure;
- tracked regions;
- continuity anchors;
- temporal progression;
- appearance/disappearance;
- transition behavior;
- stabilization;
- blank-frame context.

Do not use whole-frame pixel difference as the semantic definition of a sequence.

A blank frame does not automatically create a boundary.

A large visual change does not automatically create a boundary.

A small change does not automatically mean continuity.

### Core principle

> A new logical sequence begins when a new spatial/temporal display context becomes established.

### Viewer requirement

For each proposed boundary show surrounding actual frames.

Human choices:

- `SAME SEQUENCE`
- `NEW SEQUENCE`

### Lock condition

Real boundary examples are trustworthy under visual inspection.

---

## Stage 9 — Human Ground Truth / Calibration

### Goal

Allow corrections without manual code changes.

Store:

- same sequence;
- new sequence;
- optional note.

These become ground-truth regression examples.

The program should expose which evidence contributed to its decision.

Do not solve disagreement by blindly adjusting one global threshold.

### Lock condition

Known human-verified boundaries are reproducible regression tests.

---

## Stage 10 — Sequence Identity and Occurrences

### Goal

Separate:

> What logical sequence is this?

from:

> Where did it occur?

Example:

```text
Sequence 14

Occurrence 1: frames 100–120
Occurrence 2: frames 850–870
Occurrence 3: frames 4100–4120
```

Repeated appearances should preserve separate occurrence locations while potentially sharing sequence identity.

### Lock condition

Repeated logical content can be recognized without losing stream position.

---

## Stage 11 — Sequence Representation

### Goal

Build a reusable structural summary for every sequence.

Possible data:

```text
sequence ID
occurrences
duration
spatial regions
region behaviors
stable structures
changing structures
temporal behavior
representative frames
```

Do not create masks yet.

### Lock condition

Sequence summaries faithfully describe actual sequence playback.

---

## Stage 12 — Related Sequence / Family Discovery

### Goal

Identify sequences that share a common underlying structure.

Use:

- region arrangement;
- spatial structure;
- anchor positions;
- stable areas;
- variable areas;
- temporal role.

### Viewer requirement

Show proposed family members side by side.

### Lock condition

Human review confirms family relationships are useful and not based only on superficial similarity.

---

## Stage 13 — Cross-Occurrence Variability

### Goal

Determine what genuinely changes between occurrences of the same sequence or family.

Classify regions such as:

- identical;
- brightness variation only;
- structurally stable;
- variable content;
- variable position;
- occasionally absent;
- highly variable.

Compare using both:

- exact `0–3` brightness;
- binary on/off structure.

### Critical distinction

Differentiate:

#### Intra-sequence animation

Changes because the artwork itself progresses.

from:

#### Cross-occurrence variability

Changes because player/game information differs when the same reusable display occurs again.

This distinction is fundamental to mask necessity.

### Lock condition

Variation maps visibly correspond to genuine repeated-display variability.

---

## Stage 14 — Mask Necessity Classification

### Goal

Determine whether a mask is needed **before generating one**.

This is mandatory.

### Category A — NO MASK: EXACT/STABLE

No meaningful variable information exists.

Recommendation:

`NO MASK`

### Category B — NO MASK: FRAME-SPECIFIC ANIMATION

The sequence is dynamic, but changing pixels are intentional artwork.

Each animation state/frame is intended to be colorized independently.

Recommendation:

`NO MASK — COLORIZE FRAMES/STATES INDIVIDUALLY`

Do not mask the meaningful animation.

### Category C — MASK BENEFICIAL: VARIABLE DATA

The same reusable display contains fields whose values vary between occurrences.

Recommendation:

`GENERATE MASK CANDIDATE`

### Category D — MIXED

A sequence contains both:

- intended animation variation;
- independently variable player/game data.

Only the independently variable information should be considered for masking.

Do not mask meaningful animation simply because it changes.

### Category E — UNCERTAIN

Evidence is insufficient.

Do not automatically create a mask.

Flag for review.

---

## Stage 15 — Mask-Necessity Visual Validation

### Goal

Verify Stage 14 classifications before mask generation.

Viewer should automatically show examples of:

- stable no-mask sequences;
- individually colorized animations;
- clearly mask-worthy variable fields;
- mixed sequences;
- uncertain cases.

For each case show:

- actual frames;
- multiple occurrences where available;
- detected variable regions;
- proposed classification;
- reason.

Human choices:

- `NO MASK — CORRECT`
- `MASK NEEDED`
- `ANIMATION — COLORIZE INDIVIDUALLY`
- `UNCERTAIN`

### Lock condition

Mask/no-mask classification is trustworthy.

---

## Stage 16 — Mask Candidate Generation

### Goal

Generate candidate exclusion regions only for sequences/families classified as benefiting from masks.

Masks should target:

> Variable information that should be ignored so stable reusable display structure can match.

Do not mask:

- meaningful animation artwork;
- stable distinguishing structure;
- differences that define separate colorization frames.

Possible mask geometry:

- connected variable regions;
- coherent bounding areas;
- simplified composite shapes.

Store:

```text
mask ID
target sequence/family
shape
excluded pixels
reason for exclusion
source variability evidence
```

### Viewer requirement

Overlay the proposed mask over actual frames.

### Lock condition

Candidate masks visually cover only variability that should actually be ignored.

---

## Stage 17 — Mask Matching Engine

### Goal

Build a deterministic comparison engine.

Given:

```text
Frame A
Frame B
Mask
```

compare only non-excluded pixels.

Support explicit modes:

- exact 0–3 comparison;
- binary structural comparison.

### Tests

Artificial cases must cover:

- exact match;
- difference entirely inside mask;
- difference outside mask;
- empty mask;
- full exclusion;
- brightness-only differences;
- edge pixels.

### Lock condition

Mask matching is mathematically trusted before optimization begins.

---

## Stage 18 — Collision Analysis

### Goal

Determine whether a mask causes unrelated displays to match.

Measure:

### Positive coverage

How many intended frames/occurrences match?

### Negative collisions

How many unrelated frames/sequences incorrectly match?

A mask with perfect intended coverage but many unrelated matches is unsafe.

### Viewer requirement

Automatically present the most dangerous collision examples.

### Lock condition

False-match testing is reliable.

---

## Stage 19 — Individual Mask Optimization

### Goal

Select the strongest version of each needed mask.

Balance:

- intended coverage;
- collision avoidance;
- retained identifying information;
- excluded area;
- spatial complexity;
- reuse;
- robustness.

Prefer excluding **only what is necessary**.

Do not reduce the decision to one metric.

### Lock condition

Selected masks outperform alternatives under documented criteria.

---

## Stage 20 — Mask Set Optimization

### Goal

Optimize the complete collection of masks.

Determine whether masks can be:

- reused;
- merged;
- eliminated;
- generalized;
- specialized where collision avoidance requires it.

Preserve explicit no-mask decisions.

Example final inventory:

```text
Sequence Family A → Mask 1
Sequence Family B → No mask
Animation C → No mask; individual frame colorization
Sequence Family D → Mask 2
Static Frame E → No mask
```

### Lock condition

Every remaining mask provides a demonstrated benefit that cannot be achieved safely without it.

---

## Stage 21 — Full-ROM Validation

### Goal

Run the complete system against a representative ROM capture.

Report at minimum:

```text
frames analyzed
sequences
occurrences
families

no-mask stable sequences
no-mask animation sequences
mask-required sequences/families
mixed cases
uncertain cases

candidate masks
optimized masks
mask coverage
collisions
```

Automatically select unusual or uncertain cases for visual review.

Do not use number of masks as the success criterion.

A ROM legitimately requiring fewer masks is a successful result.

### Lock condition

Recommendations make sense across representative ROM behavior.

---

## Stage 22 — Multi-ROM Generalization

### Goal

Determine whether the system learned general DMD behavior rather than assumptions specific to one game.

Test substantially different ROMs.

Avoid game-specific hard-coded rules.

Investigate whether technical parameters can be derived from each dataset where appropriate.

### Lock condition

The architecture operates effectively across different DMD styles.

---

## Stage 23 — Final Export

### Goal

Export machine-readable and human-readable results.

Possible output:

```text
sequence identities
sequence occurrences
families
spatial regions
temporal behaviors
variability maps

mask-necessity classification

no-mask sequences
individual-animation sequences
mask-required families
uncertain cases

candidate masks
selected masks
coverage metrics
collision evidence
```

The export should allow future colorization tooling to know:

- which mask should be used, if any;
- whether the display needs a mask at all;
- why that decision was made.

---

# 9. Important Terminology

## Static

Little or no visual change.

## Dynamic

Visual content changes through time.

Dynamic does **not** mean mask-required.

## Variable

Content differs between occurrences of what should otherwise be reusable structural content.

This is more relevant to mask necessity than simple temporal change.

## Animation

Intentional visual progression through frames.

Animation changes should generally be preserved when individual frames/states are going to be colorized separately.

## Mask-required variability

Variation that interferes with reusable matching but is not part of the identifying visual structure that should determine colorization.

This is what masks should target.

---

# 10. Example Decisions

## Example 1 — Completely static screen

```text
EXTRA BALL
```

Always identical.

Result:

`NO MASK`

---

## Example 2 — Animation

```text
Frame 1: character at left
Frame 2: character moving
Frame 3: character at right
```

Each frame will be separately colorized.

Result:

`NO MASK — INDIVIDUAL FRAME COLORIZATION`

Do not mask the moving character.

---

## Example 3 — Score screen

Occurrence A:

```text
PLAYER 1
125,000
```

Occurrence B:

```text
PLAYER 1
487,250
```

If both should use the same underlying colorization treatment:

Result:

`MASK CANDIDATE FOR VARIABLE SCORE REGION`

---

## Example 4 — Animation plus score

```text
[ANIMATED CHARACTER]

SCORE 125,000
```

The character moves every frame.

The score changes independently between occurrences.

Result:

- preserve animation;
- mask variable score only.

This is a mixed case.

---

# 11. Cross-Stage Rules for Codex

## 11.1 Read this file first

Before beginning any task, Codex must inspect this source-of-truth file and identify:

- current stage;
- locked stages;
- current approved scope;
- known amendments;
- known limitations.

Do not rely on old chat instructions if they conflict with this file.

## 11.2 Do not silently change locked components

Any change to an accepted stage requires explicit evidence and regression testing.

## 11.3 Do not use aggregate counts as proof

Counts such as:

```text
500 frames
100 sequences
12 masks
```

do not establish correctness by themselves.

Use actual visual evidence.

## 11.4 Automatically find review cases

The program should identify:

- representative examples;
- unusual cases;
- uncertain classifications;
- boundary disagreements;
- mask collisions.

Do not force the user to manually search the ROM.

## 11.5 Preserve raw evidence

Always retain:

- exact 0–3 frames;
- source frame positions;
- occurrence locations;
- raw sequence membership.

Derived models must remain traceable to source frames.

## 11.6 Separate evidence from decisions

Prefer:

```text
Evidence:
- region persists
- values differ across occurrences
- surrounding structure is identical

Decision:
- candidate variable field
```

rather than an unexplained score.

## 11.7 Hard-coded parameters

Technical image-processing thresholds may exist.

Document:

- what the threshold controls;
- why it is required;
- how it was selected;
- what changes when adjusted.

Do not allow one arbitrary global sensitivity to become the semantic definition of sequences or masks.

---

# 12. Beginner-Friendly Operation

Assume the operator is not a programmer.

Any visual-validation stage should provide explicit instructions such as:

```text
1. Run:
   python viewer/server.py

2. Open:
   http://127.0.0.1:8000

3. Load:
   datasets/example.txt

4. Select:
   Review Cases

5. Inspect the automatically selected examples.

6. Report simple observations:
   Case 1 = correct
   Case 2 = should not have a mask
   Case 3 = animation should remain unmasked
```

Do not require routine JSON inspection.

Do not require the user to manually locate interesting frames unless unavoidable.

Whenever Codex completes a new function, viewer feature, stage, or substage, the user-facing output must include:

- exactly how the operator should validate it;
- which viewer controls, datasets, frames, or API endpoints to use;
- what a successful validation looks like in plain language;
- what a failure would look like;
- whether the validation is visual, numeric, automated-only, or not applicable.

Do not assume the operator can infer the validation method from the implementation details.

---

# 13. Credit-Efficiency Rules

Before coding each stage, Codex should:

1. read this file;
2. inspect existing locked interfaces;
3. identify exactly which files need modification;
4. reuse validated functionality;
5. implement only the current approved stage;
6. run current-stage tests;
7. run relevant locked-stage regression tests;
8. update this file with results;
9. produce the stage report;
10. include human-validation instructions and success/failure examples;
11. stop.

Avoid:

- speculative future features;
- unnecessary refactors;
- duplicate systems;
- rewriting accepted components;
- tuning until aggregate results merely "look good."

---

# 14. Standard Stage Report

At the end of every stage, Codex must provide and append/update a report containing:

```text
STAGE:
PURPOSE:

FILES CREATED:
FILES MODIFIED:

WHAT WAS IMPLEMENTED:

AUTOMATED TESTS:
- passed:
- failed:

REAL-DATA TEST:

VISUAL VALIDATION AVAILABLE:
yes/no

HOW TO VALIDATE:

SUCCESSFUL VALIDATION LOOKS LIKE:

VALIDATION FAILURE LOOKS LIKE:

KNOWN LIMITATIONS:

LOCKED COMPONENTS CHANGED:
yes/no

PASS CRITERIA MET:
yes/no

RECOMMENDATION:
LOCK / REFINE

STOP.
```

Codex must not automatically begin the next stage.

---

# 15. Stage Completion Records

Add one subsection here for every completed or materially revised stage.

Use this template:

```markdown
## Stage X Completion Record — YYYY-MM-DD

**Status:** LOCKED / NEEDS REVISION / SUPERSEDED

**What was implemented:**

**Files created:**

**Files modified:**

**Automated tests:**

**Real-data results:**

**Visual validation:**

**How to validate:**

**Successful validation looks like:**

**Validation failure looks like:**

**Known limitations:**

**Locked decisions created by this stage:**

**Regression tests that must continue to pass:**

**Notes for future stages:**
```

No stage should be marked `LOCKED` without an explicit completion record.

## Stage 0 Completion Record — 2026-09-19

**Status:** LOCKED

**What was implemented:**

- Created the Stage 0 project structure.
- Added a Python application entry point that initializes configuration, required directories, and logging.
- Added centralized configuration for the initial 128x32 DMD contract and valid pixel states `0,1,2,3`.
- Added safe output path helpers to prevent generated output from escaping approved project directories.
- Added automated foundation tests using Python's standard `unittest` runner.
- Added beginner-friendly run instructions.

**Files created:**

- `pyproject.toml`
- `src/__init__.py`
- `src/app.py`
- `src/config.py`
- `src/logging_setup.py`
- `src/safe_paths.py`
- `src/parsing/__init__.py`
- `src/frames/__init__.py`
- `src/spatial/__init__.py`
- `src/temporal/__init__.py`
- `src/sequences/__init__.py`
- `src/families/__init__.py`
- `src/masks/__init__.py`
- `src/optimization/__init__.py`
- `viewer/README.md`
- `docs/RUNNING.md`
- `tests/__init__.py`
- `tests/test_foundation.py`

**Files modified:**

- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 5 tests.

**Real-data results:**

- Not applicable for Stage 0. No DMD parsing or analysis has been implemented.

**Visual validation:**

- Not applicable for Stage 0. Viewer implementation begins in Stage 2.

**Known limitations:**

- No frame parser exists yet.
- No DMD viewer exists yet.
- No spatial, temporal, sequence, family, mask, or optimization analysis exists yet.
- The project is not currently a git repository.

**Locked decisions created by this stage:**

- Use Python standard library tooling for the initial foundation.
- Run tests with `python -m unittest discover -s tests`.
- Launch the foundation smoke test with `python -m src.app`.
- Keep generated logs under `reports/logs/`.
- Preserve the initial DMD contract in centralized configuration: 128x32 pixels and valid states `0,1,2,3`.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`

**Notes for future stages:**

- Stage 1 should build on `src/config.py` for dimensions and valid pixel states.
- Stage 1 should not discard exact `0,1,2,3` brightness data.
- Stage 1 should add parser-specific tests without weakening the Stage 0 foundation tests.

## Stage 1 Completion Record — 2026-09-19

**Status:** LOCKED

**What was implemented:**

- Added immutable `DmdFrame` objects with frame number, original header, exact pixel matrix, and binary pixel matrix.
- Added raw dump parsing from text and file paths.
- Enforced real dump style frame headers: `0x` followed by 8 hexadecimal digits.
- Enforced blank-line frame termination.
- Enforced exactly 128x32 pixels per frame.
- Preserved exact `0,1,2,3` brightness values.
- Derived binary structure where `0` remains off and `1,2,3` become on.
- Added deterministic parser behavior for repeated parsing of the same source.
- Added parser documentation to `docs/RUNNING.md`.

**Files created:**

- `src/frames/frame.py`
- `src/parsing/frame_parser.py`
- `tests/test_frame_parser.py`

**Files modified:**

- `src/frames/__init__.py`
- `src/parsing/__init__.py`
- `docs/RUNNING.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 15 tests.

**Real-data results:**

- No real frame dump is currently present in `datasets/`, so real-data parser validation could not be performed yet.
- Artificial frame dumps with known expected results were used for Stage 1 lock tests.

**Visual validation:**

- Not applicable for Stage 1. Viewer implementation begins in Stage 2.

**Known limitations:**

- Parser assumes each frame has one `0x########` hexadecimal header followed by exactly 4096 pixel symbols before a blank terminator.
- Parser ignores whitespace inside pixel rows but does not attempt to recover from malformed input.
- No normalized frame store beyond returned in-memory `DmdFrame` objects exists yet.
- No DMD viewer exists yet.
- No spatial, temporal, sequence, family, mask, or optimization analysis exists yet.

**Locked decisions created by this stage:**

- Public parser entry points are `parse_dump_text(text)` and `parse_dump_file(path)`.
- Parser failures raise `FrameParseError`.
- `DmdFrame.exact_pixels` and `DmdFrame.binary_pixels` are immutable tuple-of-tuples matrices.
- Frame numbers are zero-based in source order.
- Header text is preserved exactly after trimming surrounding whitespace.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`

**Notes for future stages:**

- Stage 2 should use the locked `DmdFrame` exact and binary matrices for viewer display.
- Stage 2 should visually prove rendered frames correspond to parser output.
- Future storage or indexing should preserve source frame order and exact header values.

## Stage 1 Revision Record — 2026-09-19

**Status:** LOCKED

**Reason for revision:**

- Real-data validation against `datasets/sample_dump.txt` demonstrated that actual frame headers use `0x` followed by 8 hexadecimal digits, for example `0x000a58fc`.
- The earlier Stage 1 parser did not yet reflect the real dataset header contract.

**Evidence:**

- Initial real-data parse failed with `FrameParseError`: `Frame 0 has invalid header at line 1: '0x000a58fc'`.
- Inspection showed subsequent headers follow the same `0x########` format.

**What was changed:**

- The parser now accepts `0x` followed by 8 hexadecimal characters.
- Header text is still preserved exactly after trimming surrounding whitespace.
- Regression tests were added for the real dump header style and for rejecting bare hexadecimal headers.
- Run documentation was updated with the accepted header format.

**Files modified:**

- `src/parsing/frame_parser.py`
- `tests/test_frame_parser.py`
- `docs/RUNNING.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 16 tests.

**Real-data results:**

- `datasets/sample_dump.txt` parsed successfully.
- Frames parsed: 184.
- First header: `0x000a58fc`.
- Last header: `0x0019b6e2`.
- Dimensions: 128x32.
- Pixel counts: `0:318843`, `1:203136`, `2:248`, `3:231437`.

**Regression impact:**

- Bare hexadecimal headers are no longer accepted.
- The `0x########` header regression tests must continue to pass.

**Requires reopening a locked stage:** yes, Stage 1 was revised with real-data evidence and relocked.

## Stage 1 Revision Record — 2026-09-19 EOF Final Frame Terminator

**Status:** LOCKED

**Reason for revision:**

- Real-data validation against `datasets/Insert Coin.txt` demonstrated that the final frame can be complete but not followed by a trailing blank line.
- The parser previously required a blank-line terminator even at EOF.

**Evidence:**

- Initial parse failed with `FrameParseError`: `Frame 37 with header '0x48cfd06b' is missing blank-line terminator`.
- Inspection showed the final frame has 32 complete 128-pixel rows and then EOF.

**What was changed:**

- A complete final frame may terminate at EOF without a trailing blank line.
- Incomplete final frames still fail through the existing pixel-count validation.
- Regression tests now cover both complete EOF termination and truncated EOF failure.

**Files modified:**

- `src/parsing/frame_parser.py`
- `tests/test_frame_parser.py`
- `docs/RUNNING.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 28 tests.

**Real-data results:**

- `High_Score.txt`: 239 frames, first `0x0009547d`, last `0x29825dbb`.
- `Insert Coin.txt`: 38 frames, first `0x48cfc1f4`, last `0x48cfd06b`.
- `mixed_01.txt`: 926 frames, first `0x00088b41`, last `0x000aa6fd`.
- `sample_dump.txt`: 184 frames, first `0x000a58fc`, last `0x0019b6e2`.

**Regression impact:**

- Locked parser behavior now accepts EOF as the final-frame terminator only after complete pixel validation.
- Malformed/truncated frame tests must continue to pass.

**Requires reopening a locked stage:** yes, Stage 1 was revised with real-data evidence and relocked.

## Stage 2 Completion Record — 2026-09-19

**Status:** LOCKED

**What was implemented:**

- Added a standard-library local web server for the forensic DMD viewer.
- Added dataset listing and frame APIs backed by the locked Stage 1 parser.
- Added browser UI for dataset loading, previous/next frame navigation, jump-to-frame, playback/pause, exact `0-3` display, and binary on/off display.
- Added a 128x32 canvas renderer with pixelated scaling for inspection.
- Added tests for dataset summaries, frame payloads, exact/binary matrices, JSON serialization, and dataset path safety.
- Added beginner-friendly run instructions.

**Files created:**

- `viewer/server.py`
- `viewer/index.html`
- `viewer/style.css`
- `viewer/viewer.js`
- `tests/test_viewer_server.py`

**Files modified:**

- `viewer/README.md`
- `docs/RUNNING.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 21 tests.

**Real-data results:**

- `datasets/sample_dump.txt` is listed by the viewer API.
- Viewer API loads frame 0 from `sample_dump.txt`.
- Dataset summary reports 184 frames, 128x32 dimensions, first header `0x000a58fc`, and last header `0x0019b6e2`.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- User confirmed that the rendered viewer output is visually valid.
- Exact and binary display modes are accepted for Stage 2.

**Known limitations:**

- No analytical overlays exist yet.
- No spatial, temporal, sequence, family, mask, or optimization analysis exists yet.
- The viewer reparses the selected dataset for each frame API request; this is acceptable for Stage 2 validation and can be optimized later if needed.
- Stage 2 does not yet include overlays or analysis features; those begin in later stages.

**Locked components changed:**

- No Stage 0 or Stage 1 public interfaces were changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`

**Notes for future stages:**

- Stage 3 overlays should build on this viewer rather than replacing its dataset loading or basic navigation behavior.

## Stage 3A Completion Record — 2026-09-19

**Status:** LOCKED

**What was implemented:**

- Added raw connected lit-pixel component detection from binary frame matrices.
- Used 8-connectivity; edge-touching and corner-touching lit pixels are part of the same raw component.
- Added component IDs in scan order.
- Added component area.
- Added occupied pixel coordinates.
- Added raw bounding boxes with min/max coordinates, width, and height.
- Added centroids.
- Added component payloads to the viewer frame API.
- Added Stage 2 viewer component overlay modes for raw component pixels, raw component boxes, or both.

**Files created:**

- `src/spatial/components.py`
- `tests/test_spatial_components.py`

**Files modified:**

- `src/spatial/__init__.py`
- `viewer/server.py`
- `viewer/index.html`
- `viewer/style.css`
- `viewer/viewer.js`
- `tests/test_viewer_server.py`
- `viewer/README.md`
- `docs/RUNNING.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 27 tests.

**Real-data results:**

- `datasets/sample_dump.txt`, frame 0, parsed through the viewer API.
- Header: `0x000a58fc`.
- Raw components detected: 112.
- First component bounding box: `min_x=0`, `min_y=1`, `max_x=22`, `max_y=25`, `width=23`, `height=25`.
- First component area: 341.
- Largest component area in frame 0: 451.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- Use the `Components` selector to inspect raw component pixels, raw component boxes, or both.
- User confirmed that Stage 3A is working correctly.
- Raw component pixel overlays are accepted as the primary validation view.

**Known limitations:**

- Components are raw 8-connected binary islands.
- Diagonal-only contacts are intentionally connected.
- No component merging exists.
- No nearby-component relationships exist.
- No candidate composite boxes exist.
- No optimal bounding boxes exist.
- No spatial region grouping, temporal tracking, sequence detection, mask classification, or masking exists.
- Component payloads include occupied pixels for traceability, which is useful for validation but may be optimized later if needed.

**Locked components changed:**

- No Stage 0, Stage 1, or Stage 2 public interfaces were changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_spatial_components.py`

**Notes for future stages:**

- Stage 3B should consume Stage 3A components as raw evidence and add relationship evidence without grouping components.

## Stage 3B Completion Record — 2026-09-20

**Status:** LOCKED

**What was implemented:**

- Added pairwise relationship evidence between Stage 3A raw components.
- Added horizontal gap and vertical gap.
- Added edge distance and centroid distance.
- Added X/Y overlap pixel counts.
- Added X/Y overlap ratios.
- Added area, width, and height similarity ratios.
- Added top, bottom, left, and right alignment deltas.
- Added touching, containment, horizontal-adjacent, and vertical-adjacent evidence flags.
- Added relationship evidence payloads to the viewer frame API.
- Added relationship count to the viewer status area.
- Added a viewer relationship review panel that updates per frame and filters by max edge distance, result limit, and component ID.
- Added relationship-row selection that highlights the two related components on the DMD canvas.

**Files created:**

- `src/spatial/relationships.py`
- `tests/test_spatial_relationships.py`

**Files modified:**

- `src/spatial/__init__.py`
- `viewer/server.py`
- `viewer/index.html`
- `viewer/viewer.js`
- `tests/test_viewer_server.py`
- `docs/RUNNING.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 34 tests.

**Real-data results:**

- `High_Score.txt`, frame 0: 25 components, 300 relationships.
- `Insert Coin.txt`, frame 0: 1 component, 0 relationships.
- `mixed_01.txt`, frame 0: 25 components, 300 relationships.
- `sample_dump.txt`, frame 0: 31 components, 465 relationships.

**Visual validation:**

- Not a visual overlay stage.
- Relationship counts are visible in the viewer status area.
- A compact relationship review panel is available below the DMD canvas.
- Selecting a relationship row highlights the two related components for human validation.
- Full relationship evidence is available through the viewer frame API.
- User confirmed that relationship evidence describes highlighted component relationships correctly.

**Known limitations:**

- Relationships are evidence only.
- No components are merged.
- No relationship evidence creates a grouping decision.
- No candidate composite boxes exist.
- No optimal bounding boxes exist.
- No spatial region grouping, temporal tracking, sequence detection, mask classification, or masking exists.
- Pairwise relationship counts grow with component count.

**Locked components changed:**

- No Stage 0, Stage 1, Stage 2, or Stage 3A public interfaces were changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_spatial_components.py`
- `tests/test_spatial_relationships.py`

**Notes for future stages:**

- Stage 3C may consume Stage 3B relationship evidence to propose candidate composite boxes.
- Stage 3C must still avoid final region decisions; those belong to Stage 4.

## Stage 3C Validation Record — 2026-09-20

**Status:** LOCKED

**What was implemented:**

- Added pair-based candidate composite box generation from Stage 3B relationship evidence.
- Added thresholded candidate generation using review thresholds `1`, `2`, and `3`.
- Added candidate IDs.
- Added candidate component IDs.
- Added candidate union bounding boxes.
- Added evidence pairs explaining which relationship produced each candidate.
- Added candidate payloads to the viewer frame API.
- Added candidate count to the viewer status area.
- Added viewer candidate overlays filtered by maximum threshold or all candidates.
- Added cumulative candidate threshold review: `Threshold 2` includes threshold 1 and 2 proposals, and `Threshold 3` includes threshold 1, 2, and 3 proposals.
- Added a candidate review panel that updates per frame and filters by result limit and component ID.
- Added candidate-row selection that highlights the selected candidate box and the raw source components that produced it.

**Files created:**

- `src/spatial/candidates.py`
- `tests/test_spatial_candidates.py`

**Files modified:**

- `src/spatial/__init__.py`
- `viewer/server.py`
- `viewer/index.html`
- `viewer/style.css`
- `viewer/viewer.js`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `docs/RUNNING.md`
- `viewer/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 41 tests.

**Real-data results:**

- `datasets/sample_dump.txt`, frame 0: 31 components, 465 relationships, 47 candidate boxes.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- Use the `Candidates` selector as a maximum threshold selector. `Threshold 1` shows only the tightest proposals, `Threshold 2` includes threshold 1 and 2 proposals, and `Threshold 3` includes threshold 1, 2, and 3 proposals.
- Use the candidate review panel below the canvas to limit the visible candidates or filter to one component ID.
- Select a candidate row to highlight that proposal. The viewer should draw one prominent candidate box and the raw components that created it.
- Candidate boxes are review proposals only; they are not final regions, optimal boxes, or masks.
- User confirmed Stage 3C is doing its job after validating that selected candidate rows are traceable to highlighted source components.

**Successful human validation looks like:**

- Candidate rows can be matched to visible highlighted source components on the canvas.
- Increasing the threshold adds looser proposals without removing tighter lower-threshold proposals.
- The selected candidate box encloses only the two raw components identified by that row's evidence pair.
- Candidate overlays remain secondary to raw component evidence and do not require guessing which components produced a box.

**Failure examples:**

- A selected candidate row highlights unrelated raw components.
- Threshold 2 or 3 hides candidates that were visible at a lower threshold.
- The overlay becomes a dense lattice where individual candidate proposals cannot be reviewed.
- Candidate boxes are interpreted as final spatial regions, optimal boxes, or mask regions.

**Known limitations:**

- Candidate boxes are pair-based only.
- Candidate boxes may be wide when the source components are wide.
- No transitive grouping is performed in Stage 3C.
- No final spatial region decisions exist.
- No optimal bounding boxes exist.
- No temporal tracking, sequence detection, mask classification, or masking exists.

**Locked components changed:**

- No Stage 0, Stage 1, Stage 2, Stage 3A, or Stage 3B public interfaces were changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_spatial_components.py`
- `tests/test_spatial_relationships.py`
- `tests/test_spatial_candidates.py`

**Notes for future stages:**

- Stage 3D may improve candidate review controls and selection details.
- Stage 4 may consume candidates as evidence, but final coherent spatial region decisions belong to Stage 4.

## Stage 3D Validation Record — 2026-09-20

**Status:** LOCKED

**What was implemented:**

- Added a raw component review panel below the DMD canvas.
- Added component review filtering by result limit and minimum component area.
- Added component rows showing component ID, area, bounding box, and centroid.
- Added component-row selection that highlights the selected raw component on the DMD canvas.
- Added a `Component IDs` selector with `Off`, `Selected`, and `Visible` modes.
- Moved component ID labels from the pixel-scaled canvas to a crisp HTML overlay layer.
- Moved component boxes, selected component boxes, selected relationship boxes, and candidate threshold boxes to the crisp HTML overlay layer.
- Increased box overlay thickness for readability.
- Preserved Stage 2 navigation/playback and exact/binary display behavior.
- Preserved locked Stage 3A component detection, Stage 3B relationship evidence, and Stage 3C candidate generation behavior.

**Files modified:**

- `viewer/index.html`
- `viewer/style.css`
- `viewer/viewer.js`
- `tests/test_viewer_assets.py`
- `docs/RUNNING.md`
- `viewer/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 43 tests.
- `node --check viewer/viewer.js`
- Result: passed.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- Use the component review panel to select raw components by ID.
- Use `Min area` to hide tiny raw components when the list is too noisy.
- Use `Component IDs -> Selected` to label only the selected component.
- Use `Component IDs -> Visible` to label the currently filtered component list.
- Use `Components -> Boxes` and `Candidates -> Threshold 1/2/3` to inspect crisp, readable overlay boxes.
- User confirmed Stage 3D is validated.

**Successful human validation looks like:**

- Selecting a component row highlights the matching raw lit-pixel island on the canvas.
- The listed area, box size, and centroid are consistent with the highlighted component.
- Component ID labels help identify components without obscuring the underlying DMD frame.
- Switching frames clears stale selections and updates component, relationship, and candidate review panels.

**Failure examples:**

- A selected component row highlights the wrong island.
- Component ID labels obscure so much of the frame that raw evidence cannot be inspected.
- Component review controls break frame navigation, playback, exact display, binary display, relationship review, or candidate review.
- The viewer implies semantic meanings such as score, player, credit, or initials.

**Known limitations:**

- Component IDs are visual review aids only.
- Component review does not merge components or create regions.
- Relationship and candidate panels remain evidence/proposal review tools only.
- No final spatial region decisions, temporal tracking, sequence detection, mask classification, or masking exists.

**Locked components changed:**

- No Stage 0, Stage 1, Stage 2, Stage 3A, Stage 3B, or Stage 3C analysis behavior was changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `tests/test_spatial_components.py`
- `tests/test_spatial_relationships.py`
- `tests/test_spatial_candidates.py`

**Notes for future stages:**

- Stage 4 may use the review tooling for validation, but coherent spatial region decisions belong to Stage 4.

---

# 16. Project Amendment Log

Whenever this plan changes, add an entry here.

Use:

```markdown
## YYYY-MM-DD — Amendment Title

**Reason for change:**

**Stages affected:**

**Old assumption:**

**New approved rule:**

**Regression impact:**

**Requires reopening a locked stage:** yes/no
```

Amendments should modify the relevant stage text above as well as documenting the change here.

### Initial amendments

#### DMD State Correction

**Approved rule:** The DMD uses four pixel states: `0,1,2,3`, not five states.

#### No-Mask Classification Added

**Approved rule:** Not every dynamic frame or sequence requires a mask.

Animations intended for individual frame/state colorization may require no mask even though nearly every pixel changes.

Mask generation must be preceded by explicit mask-necessity classification.

## 2026-09-19 — Stage 3 Split Into Validated Substages

**Reason for change:**

Low-level spatial feature discovery is complex enough that raw component detection, relationship evidence, candidate boxes, and review tooling should be validated separately. In particular, determining useful bounding boxes and connecting nearby areas should not be treated as a single first-pass implementation.

**Stages affected:**

- Stage 3
- Stage 4 boundary clarified

**Old assumption:**

Stage 3 would implement connected components, bounding boxes, centroids, occupied pixels, and nearby-component relationships as one stage.

**New approved rule:**

Stage 3 is split into:

- Stage 3A — Lit Pixel Components
- Stage 3B — Component Relationship Evidence
- Stage 3C — Candidate Composite Boxes
- Stage 3D — Viewer Review Tools

Stage 3A is the next approved implementation target. Stage 3C may propose candidate composite boxes, but final or optimal spatial region decisions belong to Stage 4.

**Regression impact:**

Stage 0, Stage 1, and Stage 2 regression tests must continue to pass. Stage 3A must add focused tests without weakening locked parser or viewer behavior.

**Requires reopening a locked stage:** no

## 2026-09-20 — Human Validation Instructions Required

**Reason for change:**

The operator repeatedly needed to ask how to validate newly implemented stages and viewer features. Validation expectations must be explicit at completion time.

**Stages affected:**

- All future stages and substages.
- Any newly completed function or viewer feature that requires user review.

**Old assumption:**

Stage reports listed tests and visual-validation availability, but did not always explain how a human should validate the output or what success/failure looked like.

**New approved rule:**

Every completed function, viewer feature, stage, or substage must include operator-facing validation instructions, successful-validation examples, and failure examples. These instructions must be included in the final Codex response and in the source-of-truth completion or validation record when applicable.

**Regression impact:**

No code regression impact. Future documentation and stage reports must include the new validation fields.

**Requires reopening a locked stage:** no

---

# 17. Open Questions / Unresolved Decisions

Use this section for decisions that are not yet ready to become locked rules.

Do not silently resolve them in code.

Current open questions:

- Exact final mask representation/export format.
- Exact family similarity methodology.
- Exact learning/adaptation method for spatial and temporal behavior.
- Whether some sequences require hybrid exact-brightness and binary-structure matching.
- How confidence/uncertainty should be represented in the final export.

Add or remove items as the project progresses.

---

# 18. Final Definition of Success

The project succeeds when it can transform raw DMD data into:

```text
Raw Frames
   ↓
Spatial Understanding
   ↓
Temporal Understanding
   ↓
Logical Sequences
   ↓
Occurrences
   ↓
Related Families
   ↓
True Cross-Occurrence Variability
   ↓
Does this need a mask?
   │
   ├── NO → preserve/colorize directly
   │
   └── YES
          ↓
     Mask Candidates
          ↓
     Collision Testing
          ↓
     Optimization
          ↓
     Validated Mask
```

The system should **not** attempt to maximize the number of masks produced.

A correct conclusion of:

> No mask is necessary for this frame or sequence.

is just as valuable as discovering an optimized mask.

### Central design principle

> **Preserve meaningful visual content. Mask only the variability that must be ignored to enable useful, reliable reuse during future colorization.**

---

# 19. Current Approved Task

**Current stage:** Awaiting approval for Stage 4 — Spatial Region Discovery

Stage 3D is locked. Codex must not begin Stage 4 until the user explicitly approves that next stage.

Stage 3D locked validation confirmed:

- the component review panel updates as frames change;
- selecting a component row highlights the matching raw component;
- component ID labels help identify selected or visible components without hiding raw evidence;
- component boxes and candidate threshold boxes are visually readable;
- relationship and candidate review panels still work as validated in Stage 3B and Stage 3C;
- candidates and relationships remain evidence/proposals only, not final regions.

Do not implement final spatial region decisions, optimal bounding boxes, temporal tracking, sequence detection, mask classification, or masking yet.

At Stage 4 approval:

1. confirm Stage 4 scope before implementation;
2. preserve locked Stage 3A, 3B, 3C, and 3D behavior unless a documented defect requires a targeted revision;
3. implement spatial region discovery only;
4. include operator-facing validation instructions when Stage 4 work is complete.

Do not begin Stage 4 automatically.
