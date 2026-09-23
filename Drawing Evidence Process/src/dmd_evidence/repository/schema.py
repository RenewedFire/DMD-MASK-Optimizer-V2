from __future__ import annotations

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dumps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    game_name TEXT,
    frame_count INTEGER NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dump_id INTEGER NOT NULL,
    source_frame_index INTEGER NOT NULL,
    frame_hash TEXT NOT NULL,
    frame_width INTEGER NOT NULL,
    frame_height INTEGER NOT NULL,
    frame_data TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dump_id, source_frame_index),
    FOREIGN KEY(dump_id) REFERENCES dumps(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_frame_id INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    display_order INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(evidence_frame_id) REFERENCES evidence_frames(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_evidence_frames_frame_hash
ON evidence_frames(frame_hash);

CREATE INDEX IF NOT EXISTS idx_regions_evidence_frame_id
ON regions(evidence_frame_id);
"""
