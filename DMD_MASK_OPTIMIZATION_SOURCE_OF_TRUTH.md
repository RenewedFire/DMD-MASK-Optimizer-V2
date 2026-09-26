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
| 4A | First-Pass Region Proposals | LOCKED | 2026-09-20 | Transitive candidate-evidence region proposals implemented and validated as a useful first pass with known over-merge limitations. |
| 4B | Region Split Evidence | LOCKED | 2026-09-21 | Horizontal, vertical, and negative-space split evidence implemented, exposed in viewer/API, and passed human validation as review evidence. |
| 4C | Region Merge / Refinement Rules | VALIDATING |  | Reopened with evidence: suppress coherent-object slicing and promote vertical evidence inside lower row-like bands; awaiting human validation before relock. |
| 4D | Region Review Tools | NOT STARTED |  | Planned substage. Improve review of region membership, split evidence, and refinement decisions. |
| 5 | Temporal Region Tracking | NOT STARTED |  |  |
| 6 | Temporal Behavior Analysis | NOT STARTED |  |  |
| 7 | Structural Continuity / Anchors | NOT STARTED |  |  |
| 8 | Sequence Segmentation | NOT STARTED |  |  |
| 9 | Human Ground Truth / Calibration | IN PROGRESS |  | Split out into standalone `Drawing Evidence Process` evidence collector so human-verified regions can guide future detector evaluation and refinement. |
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

Group low-level components into useful coherent regions, in validated substages.

A region should correspond to an area that behaves as a meaningful spatial unit.

Stage 4 is intentionally split because useful region discovery requires both:

- grouping evidence that can propose coherent areas;
- split/refinement evidence that prevents over-merged regions.

Possible evidence:

- proximity;
- repeated positioning;
- overlapping locations;
- common movement;
- similar dimensions;
- repeated occupancy;
- internal blank corridors;
- vertical band separation;
- horizontal line/baseline alignment;
- row-like or column-like grouping.

Store:

```text
region ID
bounding geometry
component membership
location
size
occupancy
persistence evidence
split / refinement evidence when available
```

### Key human validation question

> Does everything grouped into this region reasonably belong together spatially?

### Stage 4A — First-Pass Region Proposals

Goal:

Create reviewable first-pass spatial region proposals from Stage 3 evidence.

Scope:

- group components through Stage 3 candidate-connection evidence;
- retain singleton regions for unconnected components;
- expose region IDs, component membership, bounding boxes, area, occupancy, and evidence pairs;
- provide viewer selection for region proposals.

Known limitation:

- Transitive candidate-evidence grouping may over-merge stacked or nearby content into one broad region.

Lock condition:

- First-pass region proposals are generated, inspectable, explainable, and useful as input to later split/refinement substages.

### Stage 4B — Region Split Evidence

Goal:

Detect when a first-pass region should be split into separate spatial subregions.

Scope:

- identify vertical bands and row-like separations;
- identify internal blank corridors;
- identify horizontal baseline/line evidence;
- identify vertical corridor evidence inside bands where practical;
- identify negative-space bands where meaningful information is represented by dark cutouts inside lit regions;
- propose split candidates without assigning text/score/player/credit semantics;
- preserve component membership traceability.

Validation example:

- `mixed_01.txt`, frame index `403` shown as viewer frame `404`, header `0x0009b72e`: the bottom `BILL PAXTON` line is visually separable but Stage 4A includes it in one broad first-pass region with nearby upper content. Stage 4B should produce evidence that this lower horizontal band can be reviewed separately.
- `sample_dump.txt`, frame index `0`, header `0x000a58fc`: the bottom status row has meaningful left/middle/right geometry groups that require vertical corridor evidence for review.
- `mixed_01.txt`, frame index `500` shown as viewer frame `501`, header `0x0009e320`: meaningful information is represented as negative space inside a lit field, so Stage 4B should produce negative-space band evidence even when lit-component splits do not apply.

Lock condition:

- split evidence makes over-merged first-pass regions reviewable as plausible separate spatial units without creating excessive fragments.

### Stage 4C — Region Merge / Refinement Rules

Goal:

Refine split candidates into better region proposals.

Scope:

- prevent over-fragmentation after Stage 4B splits;
- preserve coherent visual units such as words, phrases, art chunks, or aligned clusters as geometry only;
- decide when split pieces should remain related within one region proposal;
- keep evidence inspectable.

Lock condition:

- refined region proposals are neither whole-screen blobs nor excessive fragments.

### Stage 4D — Region Review Tools

Goal:

Improve visual review of Stage 4 region proposals and evidence.

Scope:

- inspect region membership;
- inspect split evidence;
- inspect refinement evidence;
- compare first-pass and refined region boxes;
- maintain frame navigation, playback, exact display, binary display, and locked Stage 3 review behavior.

Lock condition:

- the operator can inspect region grouping and split/refinement reasoning quickly and understand what the detector is doing.

---

## Drawing Evidence Process — Standalone Human Evidence Collector

### Current decision

Main detector development is paused while a separate evidence-collection subprocess is built in `Drawing Evidence Process`.

Reason:

- recent Stage 4C work has been driven by individual visual examples;
- that loop is useful but inefficient when region interpretation depends on human judgment;
- future detector changes should be evaluated against accumulated human-verified examples rather than isolated screenshots.

### Goal

Create a standalone local tool for drawing human-verified rectangular regions on selected DMD frames.

The collector is separate from the production detector. Its purpose is to create durable ground truth:

```text
exact dump/frame data
human drawn region rectangles
stable dump and frame identity
persistent evidence history
```

### Required initial behavior

- import or open supported VPinMAME DMD dumps;
- scrub the dump non-sequentially with a timeline;
- allow the operator to choose only useful evidence frames;
- draw, move, resize, delete, and clear rectangular region boxes visually;
- submit evidence explicitly;
- persist submitted evidence immediately in SQLite;
- reopen later with all prior evidence intact;
- mark existing evidence on the timeline;
- load existing boxes when returning to an evidence frame;
- keep coordinates in native DMD frame space;
- avoid exposing JSON, SQL, hashes, or raw coordinate editing to the operator.

### Relationship to the main project

The evidence collector creates human ground truth. The main DMD mask optimizer may later consume the evidence repository through an evaluation or training layer.

Intended future loop:

```text
Human draws verified regions
        ↓
Evidence repository stores frame + boxes
        ↓
Detector runs on same frames
        ↓
Comparison reports detector-vs-human differences
        ↓
Rules, thresholds, or models are adjusted
        ↓
Detector is re-evaluated against the evidence repository
```

The collector must not depend on the current Stage 4 detector implementation at runtime. Reuse of stable parsing concepts is allowed, but detector logic must remain outside the annotation workflow.

### Initial implementation boundary

Build the collector in its own folder and start with:

- SQLite schema and migrations;
- dump and frame hashing;
- evidence frame and region persistence;
- isolated dump importer interface;
- tests for hashing, persistence, evidence updates, and coordinate conversion.

UI stages can then build on this foundation.

### Success evidence for this subprocess

A successful first usable version lets the operator:

```text
open dump
scrub to useful frame
draw boxes
submit evidence
move to another useful frame
draw boxes
submit evidence
close the app
reopen the app
see previous evidence still present
edit existing boxes
continue collecting evidence
```

### Constraints

- Do not require ML for evidence collection.
- Do not force sequential frame annotation.
- Do not silently discard or overwrite evidence.
- Do not use the evidence collector to directly mutate Stage 4 detector rules.
- Treat the SQLite repository as valuable ground-truth data.

### Stage 1 foundation record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Standalone Python package scaffold in `Drawing Evidence Process`.
- SQLite schema foundation for dumps, evidence frames, regions, and schema migrations.
- Dump identity by content hash.
- Evidence frame identity by dump/frame pair.
- Frame hash utility based on canonical native DMD pixel data.
- Region persistence in native frame coordinates.
- Evidence update behavior that replaces region boxes for an existing dump/frame entry instead of creating accidental duplicate evidence frames.
- Original frame data storage with every submitted evidence frame.
- Isolated DMD dump importer using the locked `0x########` header shape and 128x32 rows of `0`, `1`, `2`, and `3`.
- Coordinate conversion helpers between scaled display rectangles and native DMD coordinates.
- Automated tests for hashing, importer behavior, coordinate conversion, persistence, dump identity, and evidence updates.

**Files added:**

- `Drawing Evidence Process/pyproject.toml`
- `Drawing Evidence Process/README.md`
- `Drawing Evidence Process/sitecustomize.py`
- `Drawing Evidence Process/src/dmd_evidence/`
- `Drawing Evidence Process/tests/`
- `Drawing Evidence Process/data/.gitkeep`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 10 tests.
- From main project root: `python -m unittest discover -s tests`
- Result: passed, 61 tests.
- Human validation: confirmed by user on 2026-09-23 as part of "Process is validated."

**Successful human/developer validation looks like:**

- The evidence collector tests pass from inside `Drawing Evidence Process`.
- Creating evidence for a dump/frame persists a frame record and its regions.
- Reopening the SQLite database preserves submitted evidence.
- Submitting the same dump/frame again updates the existing evidence frame instead of creating an accidental duplicate.
- Renaming a dump with the same content hash resolves to the same logical dump record.
- Coordinate conversion preserves intended native 128x32 positions when the display is scaled.

**Failure examples:**

- Evidence disappears after closing and reopening the database.
- The same dump/frame silently creates duplicate evidence entries during normal edits.
- Filename changes create duplicate logical dumps despite identical content.
- Stored region coordinates depend on display scaling instead of native DMD coordinates.
- The importer accepts unsupported headers or malformed pixel rows without a clear error.

**Lock note:**

The repository foundation is locked as the durable storage base for later evidence-collection UI stages.

### Stage 2 initial viewer record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Tkinter-based local viewer entry point.
- File-open control for supported text dump files.
- DMD frame rendering at a fixed display scale.
- Current dump name, frame count, source frame index, viewer frame number, and header display.
- Previous/next frame stepping.
- Left/right keyboard stepping.
- UI rendering helpers separated from importer and repository logic.
- Automated tests for rendering color mapping and scaled pixel rectangles.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/app.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/rendering.py`
- `Drawing Evidence Process/tests/test_rendering.py`
- `Drawing Evidence Process/README.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 12 tests.
- App import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as part of "Process is validated."

**Successful human validation looks like:**

- Running `python run.py` from `Drawing Evidence Process` opens a local desktop window.
- `Open Dump` loads a supported VPinMAME text dump.
- The frame display visually matches the DMD dump.
- The frame count, current frame number, zero-based frame index, and header update correctly.
- `Prev`, `Next`, left arrow, and right arrow move one frame at a time.

**Failure examples:**

- Opening a valid dump displays an import error.
- Pixel brightness values render with visibly incorrect colors.
- Frame stepping changes the label but not the displayed image.
- The viewer skips frames or reports incorrect frame totals.
- UI code contains parsing or detector logic instead of calling the isolated importer.

**Next subprocess stage:**

Stage 3 should add full-dump timeline navigation, responsive scrubbing, exact frame navigation, +/- 1 and +/- 10 stepping, and optional playback. This remains navigation only; rectangle annotation begins in Stage 4 of the subprocess.

### Stage 3 timeline navigation record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Full-dump timeline slider.
- Slider scrubbing updates the displayed frame.
- Exact frame entry and `Jump` button.
- `-1`, `+1`, `-10`, and `+10` stepping controls.
- Left/right arrow keys for single-frame stepping.
- Shift+left/right arrow keys for 10-frame stepping.
- Play/Pause control for forward playback.
- Timeline/navigation helper functions separated from the Tkinter window for automated testing.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/navigation.py`
- `Drawing Evidence Process/tests/test_navigation.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 15 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "stage validated."

**Successful human validation looks like:**

- Running `python run.py` opens the evidence collector.
- Loading a dump enables the timeline and navigation controls.
- Dragging the timeline rapidly changes the displayed frame.
- The current frame label, zero-based index, header, jump entry, and DMD image stay synchronized.
- `-1`, `+1`, `-10`, `+10`, left/right arrows, and Shift+left/right arrows move to the expected frames without going below the first frame or beyond the final frame.
- Entering a one-based frame number and pressing `Jump` moves to that frame.
- `Play` advances frames automatically and becomes `Pause` while playing.
- Playback stops cleanly at the final frame.

**Failure examples:**

- Slider movement updates the label but not the image.
- The jump box uses zero-based numbering instead of human-visible one-based numbering.
- Navigation controls can move outside the valid frame range.
- Playback continues after the final frame or leaves the button stuck as `Pause`.
- Timeline code writes evidence or changes annotations. Stage 3 is navigation only.

**Next subprocess stage:**

Stage 4 should add rectangle annotation: create, select, move, resize, delete, clear, and scale-correct native-coordinate storage.

### Stage 4 rectangle annotation record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Click-drag creation of rectangular annotations on the DMD canvas.
- Reverse-drag normalization, so boxes can be drawn in any direction.
- Box selection by clicking inside an existing rectangle.
- Selected-box move by dragging the box body.
- Selected-box resize by dragging corner handles.
- `Delete Box` button and Delete-key removal of the selected rectangle.
- `Clear Boxes` button for the current frame's draft annotations.
- Per-frame in-memory draft annotations, so navigating away and back during the session preserves unsaved boxes for that frame.
- Annotation overlay redraw after frame render, navigation, selection, movement, resizing, deletion, and clearing.
- Native 128x32 coordinate conversion for all annotation geometry.
- Annotation helper functions separated from Tkinter for automated testing.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/annotations.py`
- `Drawing Evidence Process/tests/test_annotations.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 20 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "Validation is successful."

**Successful human validation looks like:**

- Running `python run.py` opens the evidence collector.
- Loading a dump still supports all locked Stage 3 navigation behavior.
- Click-dragging on the DMD frame creates a yellow rectangle over the intended visual region.
- Clicking a rectangle selects it and shows a green outline with corner handles.
- Dragging the selected rectangle body moves it without changing its size.
- Dragging a selected corner handle resizes the rectangle.
- Drawing from lower-right to upper-left still creates a valid rectangle.
- `Delete Box` removes only the selected rectangle.
- `Clear Boxes` removes all draft rectangles for the current frame.
- Navigating away from a frame and back restores that frame's draft boxes during the same session.
- No evidence is written to SQLite yet. Stage 4 is annotation editing only.

**Failure examples:**

- Boxes appear offset from the pointer or drift after navigation.
- Resizing changes the wrong corner.
- Moving a box changes its size.
- Delete removes the wrong rectangle.
- Clear removes boxes from other frames.
- Navigation stops working after drawing boxes.
- Stage 4 writes evidence to the repository before explicit evidence submission exists.

**Next subprocess stage:**

Stage 5 should add explicit evidence submission from the UI: submit/update the current frame and its rectangles into SQLite, commit immediately, update evidence counts, and prepare timeline evidence markers.

### Stage 5 evidence submission record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Persistent `EvidenceService` wrapper around the SQLite repository for UI use.
- Repository initialization when the evidence collector starts.
- Dump registration by content hash when a dump is opened.
- `Submit Evidence` button in the viewer.
- Submit/update behavior for the current frame and its current rectangles.
- Immediate SQLite commit through the repository transaction.
- Evidence frame count display in the dump status line.
- Repository-wide status display with total dumps, evidence frames, and boxes in SQLite.
- Green evidence markers below the timeline for frames submitted from the current dump.
- Clickable evidence markers that jump to the nearest saved frame.
- Visible `Saved Frames` list for the currently loaded dump.
- Clear current-dump scope label for saved-frame list.
- Saved-frame list rows show one-based frame number, zero-based index, and saved box count.
- Selecting a saved-frame row jumps to that evidence frame.
- Repository-wide `All Repository Evidence` list showing saved frames across all dumps.
- Selecting repository evidence from the current dump jumps the normal viewer to that frame.
- Selecting repository evidence from another dump opens the stored SQLite frame in repository preview mode.
- Repository preview mode displays saved boxes and allows edit/resubmit back to the same evidence record.
- Saved evidence-frame indices reload when opening a known dump.
- Saved boxes load automatically when navigating to a submitted frame.
- Submitted boxes remain editable as draft annotations after reload.
- Resizable application window with canvas scaling that preserves 128x32 native coordinate mapping.
- DMD frame rendering uses one scaled image item instead of thousands of canvas pixel rectangles, improving annotation responsiveness.
- `F11` fullscreen toggle and `Esc` fullscreen exit.
- UI close handler closes the repository connection.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/services/__init__.py`
- `Drawing Evidence Process/src/dmd_evidence/services/evidence_service.py`
- `Drawing Evidence Process/src/dmd_evidence/repository/__init__.py`
- `Drawing Evidence Process/src/dmd_evidence/repository/database.py`
- `Drawing Evidence Process/src/dmd_evidence/repository/models.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/rendering.py`
- `Drawing Evidence Process/tests/test_evidence_service.py`
- `Drawing Evidence Process/tests/test_navigation.py`
- `Drawing Evidence Process/tests/test_repository.py`
- `Drawing Evidence Process/tests/test_rendering.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 28 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "Validation of both requested repository-wide functions is complete."

**Successful human validation looks like:**

- Running `python run.py` opens the evidence collector.
- Loading a dump still supports locked navigation and annotation behavior.
- Drawing one or more boxes and pressing `Submit Evidence` immediately updates the evidence-frame count.
- Repository totals remain visible when switching dumps, so evidence from other dumps is not mistaken for deleted data.
- A green marker appears under the timeline at the submitted frame.
- The submitted frame appears in the `Saved Frames For Current Dump` list.
- Clicking a green marker jumps to the nearest saved frame.
- Selecting a `Saved Frames` row jumps to that saved frame.
- Maximizing or resizing the window enlarges the DMD canvas.
- Drawing, moving, and resizing boxes still aligns with DMD pixels after maximizing.
- Creating, moving, and resizing boxes remains responsive at larger window sizes.
- `F11` toggles fullscreen and `Esc` exits fullscreen.
- Selecting a row in `All Repository Evidence` shows that saved frame.
- If the row belongs to the current dump, the normal viewer jumps to that frame.
- If the row belongs to another dump, repository preview mode displays the stored SQLite frame and boxes without needing to load the original dump file.
- Editing boxes in repository preview mode and pressing `Submit Evidence` updates that same evidence record.
- Navigating away and back to the submitted frame reloads the saved boxes.
- Editing boxes on the same frame and pressing `Submit Evidence` updates the existing evidence instead of creating a duplicate frame entry.
- Closing and reopening the app, then loading the same dump, restores the submitted frame markers and saved boxes.
- The SQLite database is created at `Drawing Evidence Process/data/region_evidence.sqlite`.

**Failure examples:**

- Pressing `Submit Evidence` appears successful but nothing survives app restart.
- Loading a different dump makes the current-dump list empty without any repository-wide indication that earlier evidence still exists.
- Submitted boxes reload offset, scaled incorrectly, or attached to the wrong frame.
- Re-submitting a frame creates duplicate evidence-frame entries for the same dump/frame pair.
- Evidence markers do not appear after submission.
- The `Saved Frames For Current Dump` list does not match the SQLite evidence for the current dump.
- Selecting a saved frame jumps to the wrong frame.
- Maximizing the window visually scales the frame but causes boxes to save offset or incorrectly sized.
- Annotation drawing becomes sluggish enough to cause accidental box placement.
- `All Repository Evidence` omits saved frames that exist in SQLite.
- Selecting repository evidence from another dump requires the original dump file to be loaded.
- Editing repository preview evidence creates a duplicate instead of updating the selected evidence record.
- Opening a renamed dump with identical content loses existing evidence identity.
- Submission breaks annotation editing or Stage 3 navigation.

**Next subprocess stage:**

Stage 6 should harden reopen/edit behavior: verify existing dumps are recognized by hash, evidence markers load reliably on startup/open, existing boxes can be edited and saved after restart, and user-facing status/errors make persistence state clear.

---

### Stage 6 reopen/edit hardening record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Known-dump detection before upsert, based on dump content hash.
- Service-level flag indicating whether the last opened dump was already known.
- UI status line that reports ready state, known/new dump load state, saved frame count, successful saves, successful repository-preview updates, and submit failures.
- Reopen tests proving a renamed dump with the same content hash restores saved frame indices and saved boxes.
- Repository-preview update tests proving edits persist after closing and reopening the repository.
- Canvas resize repaint now works for repository-preview frames as well as loaded dump frames.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/repository/database.py`
- `Drawing Evidence Process/src/dmd_evidence/services/evidence_service.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/tests/test_evidence_service.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 30 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "Successful validation."

**Successful human validation looks like:**

- Open a dump that already has submitted evidence and the status line reports it as a known dump.
- The current-dump saved-frame list and timeline markers appear immediately after opening the known dump.
- Saved boxes reload when navigating to a saved frame after app restart.
- Editing a saved frame after restart and pressing `Submit Evidence` updates the same evidence record.
- Selecting repository evidence from another dump still opens repository preview mode.
- Editing repository-preview boxes and pressing `Submit Evidence` remains persisted after restart.
- Status text changes after save/update actions so the operator knows persistence succeeded.

**Failure examples:**

- A dump with the same content hash is treated as unrelated after rename.
- Evidence markers or saved boxes do not reload after restarting the app.
- Editing and resubmitting existing evidence after restart creates duplicate records.
- Repository-preview edits appear to save but are gone after restart.
- Status text implies a save succeeded when the repository write failed.

**Next subprocess stage:**

Stage 7 should improve the evidence browser: stronger grouping/filtering by dump, easier repository-level review, and optional previews/thumbnails if useful.

---

### Stage 7 evidence browser improvements record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Repository dump listing query for browser filter options.
- Service method to list all known dumps.
- `All Repository Evidence` dump filter dropdown.
- Text search box for repository evidence rows.
- Refresh button for repository browser data.
- Optional evidence descriptor field saved with each submitted evidence frame.
- Descriptor display in repository browser rows.
- Descriptor editing when resubmitting current-dump or repository-preview evidence.
- Browser filtering by dump, descriptor, filename, one-based frame number, zero-based index, and box count.
- Testable browser filtering helper outside Tkinter.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/repository/database.py`
- `Drawing Evidence Process/src/dmd_evidence/repository/models.py`
- `Drawing Evidence Process/src/dmd_evidence/repository/schema.py`
- `Drawing Evidence Process/src/dmd_evidence/services/evidence_service.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/browser.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/tests/test_browser.py`
- `Drawing Evidence Process/tests/test_evidence_service.py`
- `Drawing Evidence Process/tests/test_repository.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Result: passed, 35 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "Validation Passed."

**Successful human validation looks like:**

- `All Repository Evidence` still lists evidence across all dumps by default.
- Selecting a dump from the filter dropdown limits the list to that dump.
- Entering a descriptor before `Submit Evidence` saves it with that evidence frame.
- Reopening or selecting saved evidence restores the descriptor for editing.
- Typing a search term filters visible evidence rows.
- Searching by descriptor, filename, `frame N`, `index N`, or box count text finds expected rows.
- Selecting a filtered row still opens that evidence correctly.
- Pressing `Refresh` updates the browser list after evidence is added or edited.

**Failure examples:**

- Dump filter hides evidence from the selected dump.
- Text filter searches stale data or ignores visible row text.
- Descriptor is not saved, not restored, or not searchable.
- Selecting a filtered row opens the wrong evidence.
- Refresh clears the selected dump filter unexpectedly.
- Browser filtering breaks repository preview or current-dump jumping.

**Next subprocess stage:**

Stage 8 should add duplicate awareness using frame hashes: detect exact repeated frames, warn unobtrusively, and allow navigation/reuse without blocking deliberate submissions.

---

### Stage 8 duplicate awareness record - 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Service-level exact-frame lookup using canonical frame hashes.
- Current-frame duplicate notice in the evidence collector UI.
- `Open First Match` control for jumping to matching evidence in the current dump or previewing matching evidence from another dump.
- Duplicate detection remains non-blocking; users can still submit deliberate evidence for the current frame.
- README documentation for exact-frame match behavior.
- Unit coverage confirming matches are based on native pixel content, not source index or header.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/services/evidence_service.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/tests/test_evidence_service.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Launcher import smoke check: `python -c "import run; print('launcher import ok')"`
- Result: passed, 36 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "Validation Complete."

**Successful human validation looks like:**

- On a frame with no exact repository match, the duplicate row says `Exact frame matches: none` and the match button is disabled.
- On a frame already saved in the repository, the duplicate row shows at least one exact match.
- If the first match belongs to the current dump, `Open First Match` jumps to that saved frame and restores its descriptor and boxes.
- If the first match belongs to another dump, `Open First Match` opens repository preview mode and shows the saved frame, descriptor, and boxes.
- The duplicate notice updates as the frame changes, after submitting evidence, and after refreshing the repository browser.
- Submitting evidence remains possible even when exact matches are present.

**Failure examples:**

- The duplicate row reports matches for visually different frames.
- The duplicate row misses a byte-identical frame saved under another filename, header, or source index.
- `Open First Match` opens the wrong evidence record.
- Duplicate awareness prevents intentional submission.
- Duplicate information becomes stale after saving or refreshing.

**Next subprocess stage:**

Stage 9 should add export/reporting for collected evidence if needed after Stage 8 is validated.

---

### Stage 9 export/reporting record - 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Service-level JSON export for the full evidence repository.
- Deterministic export payload containing repository counts, dump metadata, evidence frame hashes, descriptors, stored frame pixels, and all region boxes.
- `Export Report` button in the repository browser controls.
- User-facing export success/failure status messages.
- README documentation for exported report contents.
- Unit coverage proving the exported JSON contains machine-readable evidence.

**Files added or changed:**

- `Drawing Evidence Process/src/dmd_evidence/services/evidence_service.py`
- `Drawing Evidence Process/src/dmd_evidence/ui/main_window.py`
- `Drawing Evidence Process/tests/test_evidence_service.py`
- `Drawing Evidence Process/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- From `Drawing Evidence Process`: `python -m unittest discover -s tests`
- Launcher import smoke check: `python -c "import run; print('launcher import ok')"`
- Result: passed, 37 tests.
- Launcher import smoke check passed.
- Human validation: confirmed by user on 2026-09-23 as "Stage 9 is complete."

**Successful human validation looks like:**

- `Export Report` opens a save dialog from the evidence collector.
- Saving to a `.json` path creates a readable JSON file.
- The status line reports the exported dump, evidence-frame, and box counts.
- The JSON includes every saved dump currently shown by repository totals.
- Each exported evidence frame includes descriptor text, frame hash, source frame index, stored frame data, and region boxes.
- Nested or overlapping human regions are valid evidence. A larger container/border region may intentionally contain smaller text/content regions.
- Human-drawn boxes are spatial/logical comparison regions, not pixel-perfect masks. A box may contain variable score digits, animation states, background pixels, unused pixels, or noise that should not be treated as literal evidence membership.
- Exporting does not change the current frame, selected evidence, annotations, or repository contents.

**Failure examples:**

- The export button creates an empty or invalid JSON file.
- Export counts do not match the repository status line.
- Region boxes, descriptors, or frame hashes are missing from exported evidence.
- Exporting changes existing evidence or current UI selection.
- Export failure silently appears successful.

**Subprocess completion note:**

No further Drawing Evidence Process stages are needed for the current scope. The subprocess now supports human evidence collection, editing, duplicate awareness, and export. Next work should return to the main process as evidence-based region detector evaluation.

Human evidence is not required to be a flat, non-overlapping partition of the frame. A frame may correctly contain a large region for a bordered/container panel and smaller regions inside it for internal content. Future evaluation must be containment-aware and must not treat nested boxes as contradictory merely because they overlap.

Human evidence boxes define intended spatial/logical comparison areas, not exact pixel masks. The evaluator must not require exact pixel membership or exact pixel values inside a box. This matters for score regions where digits can change, irregular animated objects where a bounding box contains background, and any region whose internal pixels vary while the human-meaningful region boundary remains stable.

---

### Evidence-guided region detector evaluation record - 2026-09-25

**Status:** IMPLEMENTED / VALIDATING

**Purpose:**

Use exported human region evidence to evaluate and improve region detection logic by aggregate scoring, not by manually validating one failure at a time.

**What was implemented:**

- Added `src/evidence` evaluation package.
- Added export loader for `dmd-region-evidence-export` JSON.
- Added detector pipeline adapter that runs current refined region detection against each evidence frame.
- Added containment-aware box matching.
- Added aggregate evaluation report with:
  - frame count;
  - human region count;
  - detected region count;
  - matched/missed/extra region counts;
  - mean alignment score;
  - mean match score;
  - worst-frame summaries.
- Added option sweep helper for evidence-guided detector tuning.
- Added missed-region failure pattern analysis.
- Added automated tests for evidence export evaluation and option ranking.
- Wrote current report to `reports/evidence_region_evaluation_summary.json`.
- Wrote current failure pattern report to `reports/evidence_failure_patterns.json`.

**Evidence semantics used by the evaluator:**

- Human boxes are spatial/logical comparison regions, not pixel-perfect masks.
- Human boxes may overlap or nest.
- Matching is one-to-one for aggregate scoring, but uses both IoU and containment coverage so near-contained boxes can match without requiring exact pixel membership.
- The evaluator reports failures in aggregate; it does not require the operator to manually review every mismatch.

**First measured baseline against `Drawing Evidence Process/Exports_Test.json`:**

- Evidence frames: 72.
- Human regions: 302.
- Previous detector defaults:
  - mean alignment score: 0.355.
  - matched regions: 91.
  - missed regions: 211.
  - extra regions: 160.
- Evidence-guided safe default change:
  - `min_negative_space_ratio` changed from `0.25` to `0.20`.
  - Candidate grouping default remained at threshold `3` because threshold `2` improved the evidence score slightly but broke locked Stage 4 behavior.
- Evidence-guided contextual merge change:
  - `Insert Coin.txt`, frame index `10`, is now interpreted as two human-logical regions: the left animation/art object and the right `INSERT COINS` contextual text block.
  - The earlier three-refined-region expectation for this frame is superseded by human evidence semantics: stacked rows can belong to one contextual region even when a low-occupancy horizontal corridor exists between them.
  - A conservative post-refinement merge combines two wide, strongly x-overlapping stacked row bands when they remain compact enough to avoid broad unrelated merges.
- Evidence-guided over-grouping change:
  - broad kept first-pass regions can now retain the parent region while also exposing supplemental vertical child regions when Stage 4B already found strong vertical split evidence.
  - This preserves valid nested/container evidence while giving the evaluator and later detector stages child proposals inside broad regions.
- Current measured result:
  - mean alignment score: 0.433.
  - matched regions: 111.
  - missed regions: 191.
  - extra regions: 148.

**Failure pattern analysis against current evidence:**

- `missing child region inside broad container`: 128 missed regions.
- `under-grouped pieces inside human region`: 22 missed regions.
- `partial-overlap geometry mismatch`: 20 missed regions.
- `irregular object or container ROI mismatch`: 8 missed regions.
- `over-grouped detector region contains human region`: 6 missed regions.
- `missing isolated human region`: 4 missed regions.
- `internal-gap text/row grouping mismatch`: 2 missed regions.
- `missing broad container/logical region`: 1 missed region.

**Interpretation of failure patterns:**

The original over-grouping bucket is now clarified into two separate cases. True close-scale over-grouping is down to 6 missed regions. The dominant remaining issue is `missing child region inside broad container`, where the detector has a broad parent/container region but lacks human-comparable child proposals inside it. Supplemental vertical child regions reduced the original over-grouping bucket and improved aggregate alignment from 0.410 to 0.433, but the next detector logic work should target child-region proposal generation inside broad containers, with particular attention to negative-space/text-band cases where the current split choice creates broad dark bands instead of human-comparable content regions.

**Files added or changed:**

- `src/evidence/__init__.py`
- `src/evidence/evaluation.py`
- `src/spatial/regions.py`
- `tests/test_evidence_evaluation.py`
- `reports/evidence_region_evaluation_summary.json`
- `reports/evidence_failure_patterns.json`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 64 tests.

**Interpretation:**

The evidence set is sufficient to guide detector optimization. Parameter tuning alone produced a measurable safe improvement, but many zero-match frames remain. The remaining failures indicate that the current Stage 4 geometry logic lacks a stronger concept of human logical grouping across internal gaps, containers, and irregular animation regions.

**Next recommended work:**

Continue evidence-guided optimization by addressing the highest-impact over-grouping bucket first. Add logic that can propose useful child regions inside broad detector regions while preserving valid nested/container evidence. Accept changes only when aggregate evidence scores improve without breaking locked regression tests.

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

## Stage 4A Completion Record — 2026-09-20

**Status:** LOCKED

**What was implemented:**

- Added first-pass spatial region proposal discovery from locked Stage 3 candidate evidence.
- Connected candidate pairs are grouped transitively into spatial regions.
- Unconnected raw components are retained as singleton regions.
- Added region IDs.
- Added region component membership.
- Added region bounding boxes.
- Added region lit-pixel area.
- Added region occupancy ratio.
- Added region candidate IDs and evidence pairs.
- Added region payloads to the viewer frame API.
- Added region counts to the viewer status area.
- Added a viewer `Regions` selector with `Off`, `Boxes`, and `Selected` modes.
- Added a region review panel that filters by result limit and minimum component count.
- Added region-row selection that highlights the selected region box on the DMD canvas.

**Files created:**

- `src/spatial/regions.py`
- `tests/test_spatial_regions.py`

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
- Result: passed, 48 tests.
- `node --check viewer/viewer.js`
- Result: passed.

**Real-data results, frame 0:**

- `High_Score.txt`: 25 components, 300 relationships, 24 candidate boxes, 4 regions.
- `Insert Coin.txt`: 1 component, 0 relationships, 0 candidate boxes, 1 region.
- `mixed_01.txt`: 25 components, 300 relationships, 24 candidate boxes, 4 regions.
- `sample_dump.txt`: 31 components, 465 relationships, 47 candidate boxes, 1 region.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- Use `Regions -> Boxes` to inspect visible region boxes.
- Use `Regions -> Selected` with the region review panel to inspect one selected region at a time.
- Use `Min components` to focus on grouped regions and hide singleton components during review.
- The key Stage 4A validation question is: are first-pass region proposals generated, inspectable, explainable, and useful as input to split/refinement work?
- User confirmed Stage 4A is complete after identifying that first-pass regions exist and that the `BILL PAXTON` example is a Stage 4B split/refinement need rather than a Stage 4A generation failure.

**Successful human validation looks like:**

- Region boxes are generated from candidate evidence and are inspectable as first-pass proposals.
- Selecting a region row highlights the same area described by its component IDs and bounding box.
- Singleton regions preserve isolated components without pretending they belong to a larger group.
- Region evidence remains explainable through component membership and evidence-pair counts.

**Failure examples:**

- No regions are generated even though components exist.
- Region rows do not match highlighted bounding boxes.
- Selecting a region row highlights the wrong bounding box.
- The viewer implies semantic meanings such as score, player, credit, or initials.

**Known limitations:**

- Regions are first-pass spatial group proposals only.
- Regions are built from within-frame candidate evidence only.
- Transitive candidate-evidence grouping may over-merge stacked or nearby content into one broad region.
- Example known limitation: `mixed_01.txt`, frame index `403` / viewer frame `404`, header `0x0009b72e`, where the bottom `BILL PAXTON` line is visually separable but Stage 4A includes it in a broad region with upper content.
- No temporal tracking exists yet.
- No semantic labels, sequence detection, mask classification, or masking exists.

**Locked components changed:**

- No Stage 0, Stage 1, Stage 2, Stage 3A, Stage 3B, Stage 3C, or Stage 3D behavior was intentionally changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `tests/test_spatial_components.py`
- `tests/test_spatial_relationships.py`
- `tests/test_spatial_candidates.py`
- `tests/test_spatial_regions.py`

**Notes for future stages:**

- Stage 4B should add split evidence for over-merged first-pass regions before Stage 5 temporal tracking begins.

## Stage 4B Validation Record — 2026-09-21

**Status:** LOCKED

**What was implemented:**

- Added geometry-only region split evidence for first-pass Stage 4A regions.
- Added horizontal internal corridor detection based on low row occupancy inside a region.
- Added vertical internal corridor detection based on low column occupancy inside regions or detected bands.
- Added negative-space horizontal band detection for dark cutouts inside lit regions.
- Added row-like split bands above and below detected corridor rows.
- Added split band IDs.
- Added split band component membership.
- Added split band bounding boxes.
- Added split band lit-pixel area and Y ranges.
- Added crossing component IDs for components that contribute pixels to more than one proposed band.
- Added region split evidence payloads to the viewer frame API.
- Added region split counts to the viewer status area.
- Added a `Regions -> Splits` overlay mode.
- Added a Region Splits review panel with selectable split rows.
- Added split-band overlay boxes for selected and visible split candidates.

**Files modified:**

- `src/spatial/regions.py`
- `src/spatial/__init__.py`
- `viewer/server.py`
- `viewer/index.html`
- `viewer/style.css`
- `viewer/viewer.js`
- `tests/test_spatial_regions.py`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `docs/RUNNING.md`
- `viewer/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 54 tests.
- `node --check viewer/viewer.js`
- Result: passed.

**Real-data validation target:**

- `mixed_01.txt`, frame index `403` / viewer frame `404`, header `0x0009b72e`.
- Stage 4B reports 1 split candidate for region `0`.
- The split candidate identifies corridor row `23`.
- The lower proposed band spans `y=24..31`, matching the visually separate lower horizontal band previously discussed.
- Component `10` is reported as a crossing component because it contributes pixels to more than one proposed band.
- `sample_dump.txt`, frame index `0`, header `0x000a58fc`.
- Stage 4B reports vertical split candidates that expose left/middle/right geometry evidence inside bands.
- `mixed_01.txt`, frame index `500` / viewer frame `501`, header `0x0009e320`.
- Stage 4B reports 1 negative-space split candidate with two horizontal dark bands spanning `y=4..13` and `y=20..29`.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- Use `Regions -> Splits` to show split-band boxes.
- Use the Region Splits panel to select one split candidate at a time.
- For the known `BILL PAXTON` example, validate whether the lower split band is reviewable as a separate geometry-only band.
- User confirmed the `mixed_01.txt`, frame index `500` / viewer frame `501`, header `0x0009e320`, negative-space evidence block is solved.
- User confirmed Stage 4B can be locked as split-evidence generation, with noisy split candidates accepted as evidence for Stage 4C to refine.

**Successful human validation looks like:**

- Split evidence appears when a first-pass region contains a clear internal low-occupancy horizontal corridor.
- Vertical split evidence appears when a band contains meaningful low-occupancy column corridors.
- Negative-space split evidence appears when meaningful structure is represented by dark cutouts inside a lit field.
- The selected split bands visually correspond to plausible separated spatial bands.
- Crossing components are reported instead of silently forcing ambiguous membership.
- Split evidence remains review evidence only and does not assign semantic labels.

**Failure examples:**

- No split evidence appears for the known `mixed_01.txt` frame `403` / viewer frame `404` case.
- Split bands are drawn in the wrong location.
- The detector splits a dense coherent region with no meaningful internal corridor.
- The viewer implies semantic meanings such as text, score, player, credit, actor name, or initials.

**Known limitations:**

- Stage 4B detects split evidence only; Stage 4C owns final refined region decisions.
- Vertical split evidence is still review evidence and may include extra candidate bands that Stage 4C must refine.
- Negative-space evidence identifies dark bands inside lit regions, but does not classify them semantically.
- The Region Splits count is a count of split evidence candidates, not a count of final regions.
- Split bands can share crossing components when a raw component spans more than one band.
- No temporal tracking, sequence detection, semantic labels, mask classification, or masking exists.

**Locked components changed:**

- No Stage 0, Stage 1, Stage 2, Stage 3A, Stage 3B, Stage 3C, Stage 3D, or Stage 4A behavior was intentionally changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `tests/test_spatial_components.py`
- `tests/test_spatial_relationships.py`
- `tests/test_spatial_candidates.py`
- `tests/test_spatial_regions.py`

**Notes for future stages:**

- Stage 4C should decide how to refine or merge split bands into improved region proposals.

## Stage 4C Validation Record — 2026-09-23

**Status:** LOCKED

**What was implemented:**

- Added conservative refined spatial region proposals.
- Added refined region IDs.
- Added source first-pass region IDs.
- Added optional source split IDs and source band IDs.
- Added refinement reasons.
- Added refined region component IDs where available.
- Added refined region bounding boxes and area.
- Added a refinement rule that keeps first-pass regions when no selected split evidence is useful.
- Added a refinement rule that replaces a first-pass region with the strongest horizontal or negative-space split bands.
- Added refined region payloads to the viewer frame API.
- Added refined region counts to the viewer status area.
- Added a `Regions -> Refined` overlay mode.
- Added a Refined Regions review panel with selectable refined-region rows.

**Files modified:**

- `src/spatial/regions.py`
- `src/spatial/__init__.py`
- `viewer/server.py`
- `viewer/index.html`
- `viewer/style.css`
- `viewer/viewer.js`
- `tests/test_spatial_regions.py`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `docs/RUNNING.md`
- `viewer/README.md`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 58 tests.
- `node --check viewer/viewer.js`
- Result: passed.

**Real-data validation targets:**

- `Insert Coin.txt`, frame index `10` / viewer frame `11`, header `0x48cfc511`: original Stage 4C validation refined 2 first-pass regions into 3 refined regions by keeping the left animation/art region and splitting the right text block into two geometry-only bands. This expectation is now superseded by evidence-guided validation: the right `INSERT COINS` text block should be treated as one contextual region despite the internal row gap.
- `mixed_01.txt`, frame index `500` / viewer frame `501`, header `0x0009e320`: Stage 4C refines 1 first-pass region into 2 negative-space refined regions.

**Visual validation:**

- Available through `python viewer/server.py` and `http://127.0.0.1:8000`.
- Use `Regions -> Refined` to inspect refined region boxes.
- Use the Refined Regions panel to select one refined proposal at a time.
- Compare with `Regions -> Boxes` and `Regions -> Splits` when a refined result needs explanation.
- User originally confirmed refined regions looked correct on both target examples: `Insert Coin.txt`, frame index `10`, and `mixed_01.txt`, frame index `500`. Later evidence-guided review superseded the Insert Coin interpretation so the right text block is one contextual region.

**Successful human validation looks like:**

- Refined regions improve obvious Stage 4A over-merged regions.
- Refined regions do not blindly accept every noisy Stage 4B split candidate.
- Refined rows clearly identify whether they came from a kept first-pass region or a source split/band.
- Refined regions remain geometry-only and do not assign semantic labels.

**Failure examples:**

- Refined regions simply duplicate every noisy split candidate.
- Refined regions ignore a strong horizontal or negative-space split that was already validated in Stage 4B.
- Refined boxes are drawn in the wrong location.
- The viewer implies semantic meanings such as text, score, player, credit, actor name, or initials.

**Known limitations:**

- Stage 4C currently chooses horizontal or negative-space split bands conservatively.
- Stage 4C does not yet use vertical split evidence as final refined regions by default.
- Stage 4C does not use temporal behavior, sequence context, semantic labels, mask classification, or masking.

**Locked components changed:**

- No Stage 0, Stage 1, Stage 2, Stage 3A, Stage 3B, Stage 3C, Stage 3D, Stage 4A, or Stage 4B behavior was intentionally changed.

**Regression tests that must continue to pass:**

- `tests/test_foundation.py`
- `tests/test_frame_parser.py`
- `tests/test_viewer_server.py`
- `tests/test_viewer_assets.py`
- `tests/test_spatial_components.py`
- `tests/test_spatial_relationships.py`
- `tests/test_spatial_candidates.py`
- `tests/test_spatial_regions.py`

**Notes for future stages:**

- Stage 4D should improve comparison/review of first-pass regions, split evidence, and refined regions.

## Stage 4C Revision Record — 2026-09-23

**Status:** VALIDATING

**Why Stage 4C was reopened:**

- Human review found that `mixed_01.txt`, frame index `850` / viewer frame `851`, header `0x000a7b2a`, was over-splitting a coherent left-side object into stacked horizontal refined regions.
- Human review found that `mixed_01.txt`, frame index `900` / viewer frame `901`, header `0x000a923c`, needed a broad upper score-like region plus more useful lower-row vertical split promotion.
- These are Stage 4C refinement-selection defects, not Stage 4B split-evidence defects.

**Revision behavior:**

- Stage 4C still treats Stage 4B splits as evidence only.
- Stage 4C suppresses horizontal slicing when several broad, strongly overlapping bands look like one coherent object being cut into slices.
- Stage 4C prefers stronger coverage when choosing a primary split, so a fuller row split can beat a smaller negative-space split.
- Stage 4C may promote nested vertical split evidence inside short lower row-like bands.
- Stage 4C remains geometry-only. It must not label content as score, player, ball, credits, wind speed, names, or text.

**Files modified for the revision:**

- `src/spatial/regions.py`
- `tests/test_spatial_regions.py`
- `DMD_MASK_OPTIMIZATION_SOURCE_OF_TRUTH.md`

**Automated tests:**

- `python -m unittest discover -s tests`
- Result: passed, 60 tests.
- `node --check viewer/viewer.js`
- Result: passed.

**Revision validation targets:**

- `mixed_01.txt`, frame index `850` / viewer frame `851`, header `0x000a7b2a`: the left object should remain one large kept first-pass refined region, not multiple horizontal slices.
- `mixed_01.txt`, frame index `900` / viewer frame `901`, header `0x000a923c`: the upper score-like area should remain a broad refined region, while lower row-like content should promote useful vertical refined regions.
- `Insert Coin.txt`, frame index `10` / viewer frame `11`, header `0x48cfc511`: should keep the left animation/art region and merge the right stacked `INSERT COINS` rows into one contextual text-block region.
- `mixed_01.txt`, frame index `500` / viewer frame `501`, header `0x0009e320`: should still identify two negative-space refined regions.

**Successful human validation looks like:**

- The revision fixes the known over-split object case without breaking earlier 4C examples.
- The revision produces more useful lower-row refined boxes on the score/status frame without claiming semantic meaning.
- Refined regions are still proposals and may remain imperfect on transition frames or semantically complex layouts.

**Known limitations after revision:**

- Stage 4C still does not use temporal context, animation continuity, sequence identity, OCR, semantic labels, mask classification, or final mask scoring.
- Transition frames may remain difficult because they can contain overlapping outgoing and incoming visual events.
- Geometry-only refined regions may not always match human semantic grouping.

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

## 2026-09-20 — Stage 4 Split Into Region Proposal And Refinement Substages

**Reason for change:**

Stage 4A first-pass region proposals correctly generated inspectable spatial regions from Stage 3 candidate evidence, but human validation found that transitive grouping can over-merge stacked or nearby content. In `mixed_01.txt`, frame index `403` / viewer frame `404`, header `0x0009b72e`, the bottom `BILL PAXTON` line is visually separable but Stage 4A includes it in one broad region with nearby upper content.

**Stages affected:**

- Stage 4
- Stage 5 boundary clarified

**Old assumption:**

Stage 4 could be validated as a single implementation of spatial region discovery.

**New approved rule:**

Stage 4 is split into:

- Stage 4A — First-Pass Region Proposals
- Stage 4B — Region Split Evidence
- Stage 4C — Region Merge / Refinement Rules
- Stage 4D — Region Review Tools

Stage 4A is locked as the first-pass proposal generator. Stage 4B is the next approved implementation target and should address over-merged regions using geometry-only split evidence such as vertical bands, internal blank corridors, and horizontal baseline/line separation.

**Regression impact:**

Stage 4A regression tests must continue to pass. Stage 4B must add focused tests without weakening locked Stage 3 or Stage 4A behavior.

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

**Current stage:** Evidence-guided region detector evaluation

The standalone `Drawing Evidence Process` is complete for the current scope. Main detector work has resumed through aggregate evidence-guided evaluation rather than one-off screenshot validation.

The Drawing Evidence Process must remain separate from the main region detector. Its completed foundation includes:

- SQLite repository creation and migrations;
- dump records keyed by content hash;
- evidence frame records keyed by dump/frame;
- region records in native DMD coordinates;
- original frame data retained with each submitted evidence frame;
- CRUD/update behavior that preserves existing evidence;
- tests for hashing, persistence, evidence update, and coordinate conversion.

Its completed initial viewer includes:

- local dump file opening;
- current frame rendering;
- frame count, frame index, and header display;
- previous/next stepping.

Its locked timeline navigation includes:

- full-dump slider scrubbing;
- exact one-based frame navigation;
- +/- 1 and +/- 10 stepping;
- arrow-key and Shift+arrow stepping;
- forward playback.

Its locked rectangle annotation includes:

- click-drag box creation;
- select, move, resize, delete, and clear controls;
- per-frame in-memory draft boxes;
- scale-correct native-coordinate geometry.

Its locked evidence submission and repository evidence browser includes:

- `Submit Evidence` for the current frame and rectangles;
- immediate SQLite persistence;
- evidence-frame count updates;
- repository-wide total counts for dumps, evidence frames, and boxes;
- green timeline markers for saved frames;
- clickable marker navigation to saved frames;
- visible `Saved Frames For Current Dump` list;
- visible `All Repository Evidence` list across all dumps;
- saved-frame row navigation;
- repository evidence selection that jumps current-dump evidence or previews stored SQLite frames from other dumps;
- repository preview editing with resubmit/update of the selected evidence record;
- saved box reload when revisiting a submitted frame;
- resizable/fullscreen drawing surface with native-coordinate preservation;
- persistence across app restart for the same dump content hash.

Its locked reopen/edit hardening includes:

- known-dump detection by content hash;
- status text for known/new dump loads, saves, preview updates, and failures;
- restart tests for saved-frame indices and saved boxes;
- restart tests for repository-preview edit persistence;
- repository-preview repaint support after resize.

Its locked evidence browser improvements include:

- dump filter dropdown for `All Repository Evidence`;
- descriptor field saved with evidence frames and shown in repository rows;
- text search across visible repository evidence row details, including descriptors;
- browser refresh control;
- repository dump-list query and service method;
- testable browser filtering helper.

Stage 8 duplicate awareness is locked. It adds exact frame-hash matching, a current-frame duplicate notice, and an `Open First Match` control that jumps to current-dump evidence or previews matching evidence from another dump without blocking intentional submissions.

Stage 9 export/reporting is locked. It adds a JSON repository export with counts, dump metadata, evidence frame hashes, descriptors, stored frame pixels, and human-drawn region boxes.

The Drawing Evidence Process is complete for the current scope. Do not add more subprocess stages unless a new evidence-collection need is identified. The next logical main-project step is evidence-based region detector evaluation: run detector output against exported human evidence and report alignment failures.

Human evidence boxes may overlap or nest. A bordered/container region and its internal content regions can all be valid regions in the same frame. The future evaluator must support containment-aware matching rather than assuming every human region is mutually exclusive.

Human evidence boxes are not pixel-perfect masks. They define spatial/logical comparison areas whose contents may change. Score digits, animation frames, background pixels inside irregular-object boxes, and unused interior pixels must not be treated as evidence errors solely because they differ from the exported frame's pixels.

Evidence-guided detector evaluation is implemented and validating:

- `src/evidence` loads exported human evidence and runs the current refined-region detector against each evidence frame;
- matching is containment-aware and does not assume human boxes are pixel masks;
- aggregate reports include matched, missed, and extra region counts plus worst-frame summaries;
- current report is written to `reports/evidence_region_evaluation_summary.json`;
- first measured safe detector improvement changed `min_negative_space_ratio` from `0.25` to `0.20`;
- evidence alignment improved from `0.355` to `0.410` while `python -m unittest discover -s tests` passes 64 tests.

Stage 4C revision validation is still pending and must not be relocked until the user explicitly validates it.

Stage 4C revision validation must confirm:

- `mixed_01.txt`, frame index `850` / viewer frame `851`, header `0x000a7b2a`, keeps the left object as one large refined region instead of slicing it into horizontal bands;
- `mixed_01.txt`, frame index `850` / viewer frame `851`, header `0x000a7b2a`, keeps the right-side stacked content horizontally separated;
- `mixed_01.txt`, frame index `900` / viewer frame `901`, header `0x000a923c`, keeps the upper score-like area broad and promotes useful lower-row vertical refined boxes;
- `Insert Coin.txt`, frame index `10` / viewer frame `11`, header `0x48cfc511`, refines to 2 geometry-only contextual regions: left animation/art and right `INSERT COINS` text block;
- `mixed_01.txt`, frame index `500` / viewer frame `501`, header `0x0009e320`, still refines to 2 negative-space geometry-only regions;
- refined regions remain geometry-only and do not assign semantic labels.

Do not implement Stage 4D review tooling, temporal tracking, sequence detection, semantic labels, mask classification, or masking unless explicitly approved after Stage 4C is relocked.

Do not connect the Drawing Evidence Process directly to Stage 4 detector mutation. The evidence repository may later support evaluation, regression generation, rule tuning, or model training, but those are downstream integration tasks.

At Stage 4C relock:

1. update the Stage 4C revision record from `VALIDATING` to `LOCKED`;
2. preserve locked Stage 4A and Stage 4B behavior unless a documented defect requires a targeted revision;
3. document the exact human validation evidence used to relock Stage 4C;
4. include operator-facing validation instructions in the completion response.

Do not begin Stage 4D automatically.
