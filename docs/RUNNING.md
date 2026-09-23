# Running the Stage 0 Foundation

Stage 0 creates the project shell only. It does not parse DMD frame dumps or
perform analysis.

## Launch

Run from the project root:

```powershell
python -m src.app
```

Expected result:

- the application prints its configured project directories;
- `reports/logs/dmd_mask_optimizer.log` is created;
- no DMD analysis is performed.

## Test

Run from the project root:

```powershell
python -m unittest discover -s tests
```

## Parse Frame Dumps

Stage 1 exposes parser functions for code and tests:

```python
from src.parsing import parse_dump_file

frames = parse_dump_file("datasets/example_dump.txt")
```

Accepted frame headers are `0x` followed by 8 hexadecimal characters, matching
the real dump format.

A blank line normally terminates each frame. A complete final frame may also end
at EOF without a trailing blank line.

Each parsed frame preserves:

- frame number;
- original `0x########` hexadecimal header;
- exact 128x32 pixel matrix with values `0`, `1`, `2`, `3`;
- binary 128x32 matrix where any lit pixel is `1`.

The parser does not analyze, classify, colorize, or mask DMD content.

## View Frame Dumps

Run from the project root:

```powershell
python viewer/server.py
```

Open:

```text
http://127.0.0.1:8000
```

Use the controls to load a dataset, move to previous or next frames, jump to a
frame number, play or pause, and switch between exact `0-3` brightness and
binary on/off display.

Stage 3A adds component overlay modes:

- `Pixels`: tint only the actual pixels in each raw component.
- `Boxes`: draw raw component bounding boxes.
- `Pixels + Boxes`: show both.

These are raw binary components only. Pixels are connected when they touch by
edge or corner. The viewer does not merge nearby components, infer text, group
regions, or create masks.

Stage 3B adds pairwise relationship counts and relationship evidence to the
frame API. This evidence is numeric only: gaps, overlaps, distances, alignment
deltas, ratios, touching, and containment flags. It does not merge components or
create regions.

The viewer also includes a relationship review panel. It updates when the frame
changes and can filter relationships by maximum edge distance, result limit, and
component ID. Select a relationship row to highlight the two related components
on the DMD canvas.

Stage 3C adds candidate composite box overlays. Candidate boxes are review
proposals only. They are not final regions and are not optimal boxes. Use the
`Candidates` selector as a maximum relationship threshold: `Threshold 2` shows
threshold 1 and 2 candidates, and `Threshold 3` shows threshold 1, 2, and 3
candidates. The candidate review panel lists the currently visible proposals;
select a row to highlight that candidate box and the raw components that
produced it.

Stage 3D adds raw component review controls. The component panel lists raw
components by area and can filter out tiny components. Select a component row to
highlight its source island. The `Component IDs` selector can label only the
selected component or the currently visible component list.

Stage 4 adds spatial region discovery. Regions are conservative groupings built
from Stage 3 candidate-connection evidence, with singleton regions retained for
unconnected components. Use the `Regions` selector and the region review panel
to inspect grouped component membership, bounding boxes, lit area, occupancy,
and evidence-pair counts. Regions are spatial group proposals only; they are not
temporal tracks, semantic labels, masks, or final optimization results.

Stage 4B adds region split evidence for first-pass regions that may be
over-merged. Split detectors look for internal low-occupancy horizontal
corridors, vertical corridors, and negative-space horizontal bands inside lit
fields. Use `Regions -> Splits` or select a row in the Region Splits panel to
inspect the proposed split bands. Split evidence is geometry-only and does not
assign text, score, player, credit, name, or other semantic labels.

Stage 4C adds conservative refined region proposals. Refined regions keep a
first-pass region when no selected split evidence is useful, or replace that
region with the bands from the strongest horizontal/negative-space split
candidate. The current revision also suppresses broad horizontal slicing when it
looks like one coherent object has been cut into stacked bands, and may promote
nested vertical split evidence inside short lower row-like bands. Use
`Regions -> Refined` and the Refined Regions panel to inspect the current
refined proposals. These are still geometry-only region proposals, not temporal
tracks, semantic labels, or masks.
