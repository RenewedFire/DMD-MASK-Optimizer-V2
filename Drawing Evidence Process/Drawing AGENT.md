# AGENTS.md

## Project: DMD Region Evidence Collector

### Purpose

Build a standalone local application for creating human-labeled region evidence from VPinMAME DMD dumps.

This project is intentionally separate from the main mask/region-detection project. Its job is to create a durable, curated evidence repository that can later be used to train, evaluate, or refine the main region-detection logic.

The human operator should never need to inspect or edit JSON, database rows, coordinate data, or other machine-oriented representations.

The application must make evidence creation fast, visual, persistent, and deliberate.

---

## Core Product Goal

The operator must be able to:

1. Import a VPinMAME DMD dump.
2. Rapidly scrub through the dump using a timeline slider.
3. Stop only on frames that are useful as evidence.
4. Draw rectangular boxes over the regions a human would identify.
5. Move, resize, add, or delete those boxes visually.
6. Submit that frame as evidence.
7. Continue scrubbing without being forced into sequential frame review.
8. Close the application at any time.
9. Reopen it later and retain all evidence collected across all prior sessions.

The evidence repository must automatically amend itself over time.

---

# Primary UX Principles

## 1. Evidence selection is manual and intentional

Do not force the user to annotate every frame.

VPinMAME dumps may contain:

- repeated frames,
- near-duplicate frames,
- animation transitions,
- blank frames,
- uninteresting intermediary states,
- long stretches of visually redundant content.

The operator chooses which frames are useful evidence.

The main navigation method must therefore be a scrubber/timeline slider, not a sequential "next frame" workflow.

---

## 2. The human sees images and boxes, not data structures

The operator must not be exposed to:

- JSON,
- SQL,
- raw coordinates,
- hashes,
- serialized masks,
- internal IDs,
- database schemas.

All evidence creation must occur visually.

Internal storage formats are implementation details only.

---

## 3. Submission is explicit

Drawing a box does not automatically create permanent evidence.

The user must deliberately press a clear action such as:

**Submit Evidence**

When submitted, the application must immediately persist:

- the selected frame,
- all region rectangles,
- source dump identity,
- source frame index,
- relevant metadata,
- submission/update timestamps.

The operation should be committed immediately so evidence is not lost if the program closes shortly afterward.

---

## 4. Persistence is automatic across sessions

All submitted evidence must live in a persistent local repository.

The repository must be reused whenever the application starts.

Closing the application must not require an export step.

Opening the application later must expose the accumulated evidence from previous sessions.

Use SQLite unless there is a strong technical reason not to.

---

# Required User Interface

## Main Explorer / Annotation View

The main screen should contain:

- imported dump name,
- optional game identifier if available,
- current frame number,
- total frame count,
- DMD frame display,
- rectangular region overlays,
- timeline slider,
- evidence markers on the timeline,
- current number of drawn regions,
- Submit Evidence button,
- controls for deleting or clearing annotations,
- frame stepping controls,
- optional playback controls.

A rough conceptual layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ Dump: AFM.dump                    Evidence collected: 147    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                      DMD FRAME                               │
│                                                              │
│       ┌─────────────────────┐                                │
│       │      Region 1       │      ┌───────────────┐         │
│       │                     │      │   Region 2    │         │
│       └─────────────────────┘      └───────────────┘         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ◀  1 ───────────────────●──────────────────────── 18422  ▶   │
│                     Frame 8437                               │
│                                                              │
│ [ -10 ] [ -1 ] [ +1 ] [ +10 ] [ Play/Pause ]               │
│                                                              │
│ Regions: 2                  [ Clear ] [ Submit Evidence ]     │
└──────────────────────────────────────────────────────────────┘
```

Exact styling is flexible. Functional behavior is not.

---

# Timeline / Scrubbing Requirements

The timeline slider is central to the application.

It must:

- cover the entire imported dump,
- allow rapid manual scrubbing,
- update the displayed frame during navigation,
- allow precise frame selection,
- visually mark frames already stored as evidence,
- allow jumping to existing evidence entries.

Recommended navigation:

- Left / Right arrow: previous / next frame.
- Shift + Left / Right: jump approximately 10 frames.
- Optional configurable larger jump.
- Slider drag: fast exploration.
- Play/Pause: inspect animated sections.
- Playback speed should be appropriate for DMD content.

Do not automatically advance after evidence submission unless clearly useful and non-disruptive.

The operator should remain in control of frame selection.

---

# Region Annotation Requirements

The operator must be able to create rectangular region annotations directly over the displayed DMD frame.

Required interactions:

- click-drag to create a rectangle,
- select an existing rectangle,
- drag to move,
- resize using handles,
- delete selected rectangle,
- clear all rectangles for the current working frame,
- support multiple rectangles on one frame.

Coordinates must map to the source DMD frame, not merely the scaled display surface.

Zooming or UI scaling must not alter stored coordinates.

The internal representation may use:

```text
x
y
width
height
```

or:

```text
x1
y1
x2
y2
```

but this must remain invisible to the operator.

---

# Annotation Semantics

For the initial version, use an intentionally simple definition:

> A region is a rectangle manually drawn by the human around an area they perceive as a meaningful region in the DMD frame.

Do not require the operator to classify the region.

Do not initially require:

- text vs animation labels,
- score labels,
- sprite labels,
- masks,
- polygons,
- hierarchy,
- semantic tags.

The first dataset should answer only:

```text
Given this frame, which rectangular regions did the human identify?
```

Future schema evolution may add labels, but do not complicate the initial annotation workflow.

---

# Evidence Repository

Use a persistent local repository, preferably SQLite.

The database location must be stable across application runs.

Do not place the repository in a temporary directory.

A reasonable default might be:

```text
./data/region_evidence.sqlite
```

or a user-data location appropriate to the platform.

If the application is portable, prefer a predictable repository path within the project/application data directory.

---

# Suggested Data Model

The exact schema may evolve, but preserve the conceptual separation below.

## Dump

Suggested fields:

- id
- content_hash
- filename
- optional game_name
- frame_count
- imported_at
- last_opened_at

`content_hash` should identify the actual dump contents, not just the filename.

Renaming a dump must not create a new logical dump if its contents are unchanged.

---

## Evidence Frame

Suggested fields:

- id
- dump_id
- source_frame_index
- frame_hash
- frame_width
- frame_height
- frame_data
- created_at
- updated_at

The original selected frame data must be stored in the evidence repository.

Do not rely solely on the original source dump remaining available.

The evidence repository should remain usable if the original dump is later deleted, moved, or renamed.

---

## Region

Suggested fields:

- id
- evidence_frame_id
- x
- y
- width
- height
- display_order
- created_at
- updated_at

Use source-frame coordinates.

---

# Frame Storage

Every submitted evidence frame must include enough original frame information to reconstruct the exact image used for annotation.

Prefer storing the native DMD pixel/intensity representation rather than only a rendered PNG if practical.

A rendered preview may additionally be stored or generated for convenience.

The learning system must eventually have access to the exact source frame representation.

---

# Hashing and Identity

Use hashing to identify content reliably.

## Dump hashing

Hash the dump contents.

Purpose:

- recognize a previously imported dump,
- survive filename changes,
- avoid accidental duplicate logical imports.

## Frame hashing

Hash the canonical raw frame representation.

Purpose:

- identify exact repeated frames,
- detect evidence duplication,
- support duplicate awareness.

Do not use hashing to silently reject human submissions.

If the human deliberately submits an identical frame in another context, preserve that action unless project rules later establish deduplication semantics.

---

# Duplicate Awareness

The application should help the operator avoid unnecessary duplicate work without taking control away from them.

When the current frame is already represented in the evidence repository, show a visual notice such as:

```text
This exact frame already exists in evidence.
```

Useful optional actions:

- jump to existing evidence,
- inspect existing boxes,
- copy existing annotation,
- continue and submit anyway.

Never block the user solely because an exact frame already exists.

---

# Evidence Markers

Frames already submitted from the current dump should appear as markers on the timeline.

Requirements:

- markers must be visually distinguishable from the slider itself,
- clicking a marker should jump to that evidence frame,
- existing annotations should load when revisiting evidence,
- edits should update the existing evidence record rather than creating accidental duplicate records for the same dump/frame pair.

If the user explicitly wants a separate duplicate sample later, that can be added as a separate feature.

For the initial implementation, treat one dump/frame pair as one editable evidence entry.

---

# Editing Existing Evidence

Existing evidence must be editable visually.

Workflow:

1. User navigates to a previously submitted frame.
2. Existing boxes load automatically.
3. User can move, resize, add, or remove boxes.
4. User presses an explicit update/save action.
5. Repository is updated atomically.

Do not require direct database editing.

---

# Evidence Browser

Provide a simple visual way to inspect accumulated evidence.

Minimum useful capabilities:

- total evidence frame count,
- total region count,
- evidence grouped or filterable by dump,
- thumbnails or frame previews,
- region-count display,
- ability to reopen an evidence frame for editing.

A later version may add filtering/search.

The initial browser does not need advanced analytics.

---

# Session Behavior

The repository is continuous across sessions.

Example:

```text
Session 1:
AFM dump
+84 evidence frames

Session 2:
MM dump
+112 evidence frames

Session 3:
AFM second recording
+37 evidence frames

Session 4:
TZ dump
+96 evidence frames

Result:
One accumulated repository containing all submitted evidence.
```

There is no concept of resetting evidence merely because the application restarts.

---

# Separation From the Main Project

This project must remain independently runnable.

Do not couple its runtime directly to the existing production region detector.

The intended relationship is:

```text
DMD Region Evidence Collector
        ↓
Persistent Evidence Repository
        ↓
Future Training / Evaluation Pipeline
        ↓
Production Region Detector
```

The collector creates ground truth.

The production detector consumes knowledge derived from that ground truth later.

---

# Architecture

Keep the code separated into clear responsibilities.

Suggested structure:

```text
dmd-region-evidence/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── src/
│   └── dmd_evidence/
│       ├── app.py
│       ├── config.py
│       │
│       ├── dmd/
│       │   ├── importer.py
│       │   ├── decoder.py
│       │   ├── frame.py
│       │   └── hashing.py
│       │
│       ├── repository/
│       │   ├── database.py
│       │   ├── schema.py
│       │   ├── dumps.py
│       │   ├── evidence.py
│       │   └── migrations.py
│       │
│       ├── ui/
│       │   ├── main_window.py
│       │   ├── frame_view.py
│       │   ├── timeline.py
│       │   ├── annotation_layer.py
│       │   └── evidence_browser.py
│       │
│       └── services/
│           ├── import_service.py
│           └── evidence_service.py
│
├── data/
│   └── .gitkeep
│
└── tests/
    ├── test_hashing.py
    ├── test_repository.py
    ├── test_coordinates.py
    └── test_importer.py
```

This is a recommendation, not an absolute requirement.

Favor maintainability over matching this exact tree.

---

# UI Technology

Choose a desktop UI technology suitable for:

- responsive slider scrubbing,
- custom image display,
- pointer-based rectangle drawing,
- resize handles,
- keyboard shortcuts,
- SQLite integration,
- local file importing.

If using Python, PySide6 / Qt is a strong default.

Avoid choosing a technology that makes precise rectangle editing or fast frame rendering unnecessarily difficult.

The tool should run locally.

A network service should not be required for normal evidence collection.

---

# VPinMAME Dump Import

Build the importer as an isolated component.

The rest of the application should consume a normalized frame interface rather than depending directly on dump parsing details.

Conceptual interface:

```python
dump = open_dump(path)

dump.frame_count
dump.width
dump.height

frame = dump.get_frame(index)
```

A frame should expose the canonical pixel/intensity data needed for:

- display,
- hashing,
- storage,
- future ML consumption.

Do not spread VPinMAME parsing logic throughout the UI.

---

# Performance Requirements

Scrubbing should feel interactive.

Do not fully decode and retain every rendered frame in memory unless the dump format and typical sizes make that clearly safe.

Prefer:

- indexed access,
- bounded caching,
- prefetching around the current slider position if useful,
- lightweight frame representations.

Moving the slider should not perform database writes.

Only evidence-related actions need persistence.

---

# Reliability Requirements

Evidence is valuable and should be difficult to lose.

Implement:

- immediate database transactions on submit/update,
- schema migrations,
- graceful handling of interrupted imports,
- database initialization on first run,
- integrity checks where reasonable.

Never silently discard evidence because of malformed source metadata or renamed files.

---

# Repository Backups

The SQLite database should be easy for the user to back up manually.

Keep primary evidence in a small number of predictable files.

Do not scatter permanent evidence across temporary caches.

A future backup/export feature is desirable, but it is not required for the first usable build.

---

# Machine Learning Scope

Do not begin by building the learning model.

The first milestone is a high-quality evidence collection system.

The project should make future ML straightforward, but the annotation interface must not depend on ML being available.

Future stages may include:

- training a region proposal model,
- active learning,
- model-generated boxes for human correction,
- uncertainty-driven sample suggestions,
- evaluation against held-out evidence,
- integration with the main project.

Those are downstream tasks.

Do not allow them to delay the evidence collector.

---

# Future Model Review Mode

Design the annotation representation so a later mode can display model-proposed rectangles.

Future workflow:

```text
Model proposes regions
        ↓
Human reviews visually
        ↓
Human moves / resizes / deletes / adds boxes
        ↓
Submit corrected evidence
        ↓
Repository grows
```

Human-created and model-assisted evidence should ultimately use the same stored region format.

Do not implement this until the manual evidence workflow is stable.

---

# Initial Development Stages

## Stage 1 — Repository foundation

Implement:

- SQLite database creation,
- schema/migrations,
- dump records,
- evidence frame records,
- region records,
- CRUD operations,
- hashing utilities,
- automated tests.

No polished UI is required yet.

---

## Stage 2 — Dump importer and frame viewer

Implement:

- local file selection,
- VPinMAME dump parsing,
- frame indexing,
- frame rendering,
- current frame display,
- frame count display,
- previous/next stepping.

Keep parser logic isolated.

---

## Stage 3 — Timeline navigation

Implement:

- full dump slider,
- responsive scrubbing,
- exact frame navigation,
- +/- 1 stepping,
- +/- 10 stepping,
- optional playback.

This is a core feature, not optional polish.

---

## Stage 4 — Rectangle annotation

Implement:

- create region,
- select region,
- move region,
- resize region,
- delete region,
- clear current annotations,
- correct mapping between scaled UI and source-frame coordinates.

Test coordinate conversion carefully.

---

## Stage 5 — Evidence submission

Implement:

- Submit Evidence action,
- frame persistence,
- region persistence,
- immediate commit,
- evidence count update,
- timeline evidence markers.

At this point the application should already be useful for real evidence collection.

---

## Stage 6 — Reopen and edit

Implement:

- automatic repository reopening,
- recognize previously imported dumps by hash,
- load evidence markers,
- load existing boxes,
- update existing evidence.

Verify data survives application restart.

---

## Stage 7 — Evidence browser

Implement:

- visual evidence listing,
- grouping/filtering by dump,
- thumbnails/previews,
- evidence frame region counts,
- reopen evidence for editing.

Keep this practical rather than elaborate.

---

## Stage 8 — Duplicate awareness

Implement:

- frame hashing,
- exact-frame lookup,
- unobtrusive duplicate notice,
- jump to existing evidence,
- optional annotation reuse.

Do not block deliberate human action.

---

# Minimum Acceptance Criteria

The first production-usable version is complete when all of the following work:

1. User can launch the application locally.
2. User can import a supported VPinMAME DMD dump.
3. Application displays the dump correctly.
4. User can scrub the entire dump with a slider.
5. User can step forward/backward precisely.
6. User can draw multiple rectangular regions on a selected frame.
7. User can move and resize those regions.
8. User can delete regions.
9. User can press Submit Evidence.
10. Submitted evidence is immediately written to persistent storage.
11. The original selected frame is retained in the repository.
12. Existing evidence is visibly marked on the timeline.
13. Closing and reopening the program preserves all prior evidence.
14. Reloading a known dump restores its evidence markers.
15. Navigating to existing evidence restores its boxes.
16. Existing evidence can be edited and saved.
17. Evidence from multiple dumps accumulates in the same repository.
18. The operator never needs to inspect or edit JSON or SQL.
19. Renaming an imported dump does not defeat content identity.
20. The application can identify exact duplicate frames by hash.

---

# Testing Priorities

Automated tests should strongly cover:

## Coordinate conversion

Verify that annotations remain correct at different display scales.

For example:

```text
native DMD: 128 × 32
display:    1024 × 256
```

A box drawn on the scaled display must resolve exactly to native-frame coordinates.

---

## Persistence

Test:

- create evidence,
- close database connection,
- reopen repository,
- retrieve exact frame and boxes.

---

## Hash stability

The same dump/frame contents must always produce the same canonical hash.

Filename and path must not affect content identity.

---

## Evidence updates

Editing an existing dump/frame annotation must update that evidence rather than silently creating unintended duplicates.

---

## Import safety

Malformed or unsupported input should produce a clear user-facing error without damaging existing evidence.

---

# Engineering Rules for Codex

While implementing this project:

1. Prefer clear, maintainable code over clever abstractions.
2. Keep UI, dump parsing, persistence, and future ML concerns separated.
3. Add tests alongside meaningful non-UI logic.
4. Do not expose internal database structures to the human workflow.
5. Do not implement features that force sequential annotation.
6. Do not require the user to export/save manually after each session.
7. Do not make ML a prerequisite for evidence collection.
8. Do not silently destroy or overwrite evidence.
9. Preserve original frame data for every submitted sample.
10. Treat the accumulated repository as valuable ground-truth data.
11. Use migrations for database schema changes.
12. Keep evidence creation usable even when duplicate detection or other optional helpers fail.
13. Avoid speculative complexity until the core collector is reliable.
14. Document any assumptions made about the VPinMAME dump format.
15. If the dump format is uncertain, isolate assumptions in the importer rather than baking them into the rest of the application.

---

# Definition of Done for the Collector

The application is successful when a human can spend a session rapidly browsing DMD dumps and collecting representative region examples with very little friction.

A successful session should feel like:

```text
Open dump
    ↓
Scrub
    ↓
Interesting frame
    ↓
Draw boxes
    ↓
Submit
    ↓
Scrub
    ↓
Interesting frame
    ↓
Draw boxes
    ↓
Submit
    ↓
Close application
```

Later:

```text
Reopen application
    ↓
All previous evidence is still present
    ↓
Open another dump
    ↓
Continue adding evidence
```

The repository—not the individual session—is the durable output of this project.

---

# Long-Term Intent

Once enough evidence exists, this repository will serve as the ground truth for determining how well automated region detection matches human judgment.

Future evaluation should be based on the accumulated human-labeled evidence rather than isolated hand-picked regression fixes.

The desired progression is:

```text
Human evidence creation
        ↓
Curated ground-truth repository
        ↓
Training / active learning
        ↓
Automated region prediction
        ↓
Evaluation against human evidence
        ↓
Improved production detector
```

Protect the quality, persistence, and usability of the evidence repository above all else.
