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

The initial Stage 2 viewer can open a dump, display frames, show frame count and
header, and step previous/next. Timeline scrubbing and annotation tools are not
implemented yet.

## Launch Viewer

```powershell
python run.py
```

## Run Tests

```powershell
python -m unittest discover -s tests
```
