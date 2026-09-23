# Viewer

Run the Stage 2 forensic DMD viewer from the project root:

```powershell
python viewer/server.py
```

Open:

```text
http://127.0.0.1:8000
```

The viewer loads files from `datasets/` through the locked Stage 1 parser and
shows exact `0-3` brightness or binary on/off frames. It does not perform
sequence detection, mask classification, or masking.

Stage 3A adds raw connected lit-pixel component overlays. Pixels are connected
when they touch by edge or corner. Overlay modes can show component pixels,
component boxes, or both. These overlays do not merge components, score
relationships, propose candidate composite boxes, or create final spatial
regions.

Stage 3B adds relationship review controls below the DMD canvas. The panel sorts
relationships by edge distance and filters by max distance, result limit, and
component ID. Select a relationship row to highlight the two related components
on the DMD canvas. It presents numeric evidence only and does not group
components.

Stage 3C adds candidate composite box overlays. These are pair-based review
proposals derived from nearby relationship evidence. They are not final spatial
regions, optimal boxes, or mask candidates. The `Candidates` selector is
cumulative: `Threshold 2` includes threshold 1 and 2 proposals, while
`Threshold 3` includes threshold 1, 2, and 3 proposals. The candidate review
panel filters by result limit and component ID. Select a candidate row to
highlight that proposal and its source components on the canvas.

Stage 3D adds raw component review controls. Use the component panel to inspect
raw component IDs, area, bounding boxes, and centroids. Select a component row
to highlight it on the canvas. Use `Component IDs` to label either the selected
component or the visible filtered component list.

Stage 4 adds spatial region review. Regions group components through Stage 3
candidate evidence and keep unconnected components as singleton regions. Use the
region panel to inspect component membership, bounds, area, occupancy, and
evidence-pair counts. These are spatial group proposals only, not semantic
labels, masks, or temporal tracks.

Stage 4B adds region split evidence. Split candidates identify internal
low-occupancy horizontal corridors, vertical corridors, and negative-space
horizontal bands inside first-pass regions. Use the Region Splits panel to
select one split candidate and display its band boxes. Split evidence remains
geometry-only.

Stage 4C adds refined region proposals. The current conservative rule keeps
unsplit first-pass regions and uses the strongest horizontal or negative-space
split bands when they improve a first-pass region. The current revision also
suppresses broad stacked slicing when the bands look like one coherent object,
and may promote nested vertical split evidence inside short lower row-like
bands. Use `Regions -> Refined` and the Refined Regions panel to inspect these
proposals.
