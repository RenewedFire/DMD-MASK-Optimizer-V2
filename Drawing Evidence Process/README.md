# DMD Region Evidence Collector

Standalone local tool for collecting human-drawn rectangular region evidence from
VPinMAME DMD dumps.

This project is separate from the main detector. Its output is a persistent
SQLite evidence repository that can later be used to evaluate, tune, or train
region detection logic.

## Current Stage

Repository foundation:

- SQLite schema and migrations
- dump records keyed by content hash
- evidence frames keyed by dump/frame
- region records in native DMD coordinates
- original frame data stored with each evidence frame
- importer and hashing utilities
- coordinate conversion helpers

The initial viewer can open a dump, display frames, show frame count and header,
scrub with a timeline, jump to an exact frame, step by 1 or 10 frames, play
forward, draw/edit rectangular annotations, and submit/update evidence into the
persistent SQLite repository at `data/region_evidence.sqlite`.

Submitted evidence frames are marked under the timeline and listed in the
`Saved Frames For Current Dump` list. Clicking a marker or selecting a
saved-frame row jumps back to that saved frame. Returning to a submitted frame
reloads its saved boxes for editing.

The repository status line shows total dumps, evidence frames, and boxes in the
SQLite repository. The saved-frame list is scoped to the currently loaded dump,
so it can be empty for a new dump even when the repository totals show evidence
from earlier dumps.

The `All Repository Evidence` list shows saved frames across all dumps. Selecting
an entry from the current dump jumps the normal viewer to that frame. Selecting
an entry from another dump opens the stored SQLite frame in repository preview
mode, displays its saved boxes, and allows the boxes to be edited and submitted
back to the same evidence record.

The status line reports whether an opened dump was recognized from the
repository, how many saved frames were found for it, and whether evidence saves
or repository-preview updates succeed.

Each evidence frame can include a human descriptor entered before pressing
`Submit Evidence`. The descriptor is saved with the evidence frame, shown in the
repository browser, editable on later submissions, and included in text search.

The repository evidence browser can be filtered by dump and by text. Text search
matches visible row details such as descriptor, filename, frame number,
zero-based index, and box count.

The viewer also checks the current displayed frame against existing repository
evidence by exact frame hash. When the same native pixel frame already exists in
SQLite, the `Exact frame matches` row shows the match count and the first saved
location. `Open First Match` jumps to that evidence if it is in the current dump,
or opens it in repository preview mode if it belongs to another dump. This is
only a notice; submitting evidence is still allowed.

`Export Report` writes the full SQLite evidence repository to a JSON file. The
export includes dump metadata, evidence frame hashes, descriptors, stored frame
pixels, and all human-drawn region boxes. This report is intended for review and
future regression/calibration work outside the drawing UI.

The window is resizable, and the DMD canvas scales up while preserving native
128x32 coordinate mapping. Press `F11` to toggle fullscreen and `Esc` to leave
fullscreen.

The DMD frame is rendered as a single scaled image so annotation editing remains
responsive at larger window sizes.

## Launch Viewer

```powershell
python run.py
```

## Run Tests

```powershell
python -m unittest discover -s tests
```
