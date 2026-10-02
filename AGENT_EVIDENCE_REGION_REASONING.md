# Agent Instructions: Evidence-Only Region Reasoning Analysis

## Purpose

Analyze the human evidence repository to derive general mathematical and spatial rules for region identification. The goal is to learn how humans interpret DMD regions across ROMs without memorizing ROM-specific coordinates.

## Hard Constraints

This is analysis only.

Do not:

- edit `src/spatial/**`;
- edit `src/evidence/**`;
- edit viewer code;
- edit tests;
- implement detector logic;
- tune Stage 4 code;
- use ROM-specific coordinates as final learned behavior.

The agent may:

- read `Drawing Evidence Process/Exports_Test.json`;
- read current reports;
- compute evidence summaries;
- classify evidence frames by complexity;
- draft spatial reasoning rules;
- report findings and gaps.

## Core Question

Can human region evidence teach general spatial reasoning rules that identify simple regions across ROMs, without relying on ROM-specific layout memory?

Evidence should teach why a region is a region, not merely where one known ROM tends to place boxes.

## Simple Evidence Frame Definition

A simple frame is a human evidence frame that has:

- no nested parent/child regions;
- no overlapping human boxes;
- no obvious noisy transition content;
- few regions, ideally 1 to 5;
- mostly rectangular, band-like, row-like, or object-like regions;
- minimal irregular sprite debris;
- regions explainable by spacing, alignment, occupancy, row/column grouping, contrast, or container boundaries.

Initially exclude:

- transition frames;
- nested container frames;
- large border-plus-child frames;
- irregular moving object frames;
- frames with many tiny sprite fragments;
- frames where human intent depends heavily on sequence context.

## Initial Simple Frame Candidates

Begin with these candidate frames:

- `Large 1 Player.txt`, frame `1028`, `Ball 1 Locked`
- `mixed_01.txt`, frame `86`, `CheckSum`
- `Large 1 Player.txt`, frame `5638`, `Chase Jackpot`
- `Large 1 Player.txt`, frame `4223`, `Cow Jackpot`
- `Large 1 Player.txt`, frame `1401`, `Super Pops (No Background)`
- `Large 1 Player.txt`, frame `1400`, `Super Pops (Background)`
- `mixed_01.txt`, frame `559`, `5 Million`
- `mixed_01.txt`, frame `560`, `5 Million (Inverse)`
- `mixed_01.txt`, frame `163`, `Push Start`
- `Large 1 Player.txt`, frame `1963`, `Special`
- `Large 1 Player.txt`, frame `1784`, `Train Explosion`
- `High_Score.txt`, frame `0`, `High Score #1 Regular`
- `High_score_interations.txt`, frame `2`, `High Score #3 Regular`

These frames are candidates, not guaranteed perfect examples. Confirm their simplicity through analysis before deriving rules from them.

## Analysis Loop

Repeat without coding:

1. Select a simple evidence frame.
2. List the human regions in spatial terms:
   - row band;
   - text group;
   - score field;
   - isolated object;
   - container;
   - negative-space content;
   - status line;
   - separated-but-contextual phrase.
3. For each human region, describe measurable spatial evidence:
   - bounding dimensions;
   - lit occupancy;
   - internal gaps;
   - alignment with neighboring components;
   - shared baseline;
   - shared height;
   - horizontal or vertical separation;
   - containment or surrounding border;
   - whether gaps are letter gaps, word gaps, or region gaps.
4. Propose a general rule that would identify that region.
5. Test the rule analytically against the rest of the simple frame set.
6. Track failures:
   - over-splits one human region;
   - merges separate regions;
   - misses a sparse region;
   - creates a noisy extra region;
   - depends on ROM-specific coordinates.
7. Revise the rule.
8. Continue until the rule set explains the selected simple frames without ROM-specific positions.

## Expected Rule Categories

Derive rules in these categories where supported:

- Text Row Rule
- Phrase Gap Rule
- Separate Row Rule
- Score Field Rule
- Object Rule
- Container Rule
- Negative-Space Rule
- Noise Rejection Rule

## Required Output

Produce a written report only:

```text
Evidence-Only Region Reasoning Report

Simple frames analyzed:
- ...

Rules that explain them:
- Rule name
- Spatial evidence
- Frames explained
- Known failure risk

Frames not yet explained:
- ...

Conclusion:
- Is the evidence sufficient to teach general region reasoning?
- What detector/scoring model should be designed next?
```

Do not proceed to implementation until the simple-frame rule set is accepted.
