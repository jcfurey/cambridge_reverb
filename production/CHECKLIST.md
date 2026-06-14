# Production / fab package checklist

What goes in a JLCPCB order package, and the gate checks before you click "order."
Order settings and the full pre-order DRC checklist live in
`../docs/04-jlcpcb-fabrication.md`; this is the packaging/handoff view.

## Fab package contents (per board revision)

```
production/
  vox_cambridge_revA/
    gerbers_revA.zip        # F.Cu B.Cu F.SilkS B.SilkS F.Mask B.Mask Edge.Cuts + .drl
    bom_revA.csv            # snapshot of ../bom/bom.csv at tape-out
    cpl_revA.csv            # pick-and-place (only if using JLCPCB assembly)
    assembly_revA.pdf       # placement / orientation drawing
    NOTES.md                # what changed vs previous rev, known issues
```

Gerbers/zip are regenerated artifacts — `.gitignore` leaves `production/` and
`kicad/gerbers/` untracked by default. Commit a tagged zip only when you want a
frozen, orderable revision in history (uncomment the lines in `.gitignore`).

## JLCPCB order recap (from Part 4)

- 2 layers, **1.6 mm**, **2 oz copper**, HASL(lead), green mask, white silk, tented vias
- Board outline = your measured size (190×115 or 155×90 — errata #9)
- Qty 5 (minimum); ~$2–7 + shipping, under ~$25 total
- "Confirm production file" = Yes; review the Gerber preview every layer

## Pre-order gate (must all pass)

- [ ] DRC clean (zero errors) with the three net classes from
      `../kicad/cambridge_reverb.kicad_pro` (Default / Power / HighCurrent)
- [ ] All zones filled; bottom-layer ground pour continuous, no islands
- [ ] Edge.Cuts is a single closed outline at the measured size
- [ ] Power path: +33V5 / SPK_P / SPK_N / PA_OUT on **HighCurrent (2.5 mm)** class
      (errata #11); +27V / +17V / GND on Power (1.5 mm)
- [ ] LM1875 + LM317 oriented toward the heatsink-side board edge
- [ ] Polarity markers on electrolytics; pin-1 dots on ICs
- [ ] Wiring-edge pads all silkscreen-labeled; one edge only
- [ ] Gerber preview on JLCPCB matches the design on every layer
