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
regions, optimal boxes, or mask candidates.
