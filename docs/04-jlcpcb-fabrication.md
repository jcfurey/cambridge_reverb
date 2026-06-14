# Vox Cambridge Reverb — Part 4: JLCPCB Fabrication Guide

> Reconstructed document — see `PROVENANCE.md`. Order specs, design rules, net
> classes, Gerber/drill export steps, silkscreen layout, and the pre-order
> checklist are recovered substantially verbatim.
>
> Note: the board outline below shows 190×115 mm (matching the original
> 25-5274-2 footprint). Part 7 recommends 155×90 mm as a conservative default
> pending chassis measurement. Use whichever your measured chassis supports;
> set the Edge.Cuts outline accordingly.

## JLCPCB order specifications — recovered verbatim

| Parameter | Setting | Notes |
|-----------|---------|-------|
| Layers | 2 | Top copper + bottom copper (ground plane) |
| Dimensions | 190 × 115 mm | Matches original 25-5274-2 board footprint |
| PCB Qty | 5 | Minimum order |
| PCB Thickness | 1.6 mm | Matches original board thickness |
| Copper Weight | 2 oz | Handles power-amp traces better |
| Surface Finish | HASL (with lead) | Best for hand-soldering through-hole; cheapest |
| Solder Mask | Green | Fastest processing |
| Silkscreen | White | Standard |
| Via Covering | Tented | Protects vias from solder bridges |
| Confirm Production File | Yes | Always review the Gerber preview |
| Remove Order Number | Specify location | "JLCJLCJLC" text on silkscreen, or pay $1 to remove |

Estimated cost: ~$2–7 for 5 boards + ~$5–15 shipping. Under $25 total.

## KiCad design rules for JLCPCB — recovered verbatim

| Rule | Value | JLCPCB min | Notes |
|------|-------|------------|-------|
| Min track width | 0.25 mm (10 mil) | 0.127 mm | Comfort; audio doesn't need tighter |
| Min clearance | 0.20 mm (8 mil) | 0.127 mm | Safe, avoids extra fees |
| Min via drill | 0.3 mm | 0.3 mm | No surcharge |
| Min via diameter | 0.6 mm | 0.45 mm | Solid annular ring |
| Min through-hole drill | 0.8 mm | 0.3 mm | Most leads 1.0 mm |
| Min annular ring | 0.15 mm | 0.13 mm | Comfortable margin |
| Board edge clearance | 0.5 mm | 0.3 mm | |
| Min silkscreen width | 0.15 mm | 0.15 mm | |
| Min silkscreen text height | 1.0 mm | 0.8 mm | |

### Net classes — recovered verbatim

| Net class | Track width | Clearance | Via drill | Use for |
|-----------|------------|-----------|-----------|---------|
| Default | 0.30 mm | 0.20 mm | 0.3 mm | All signal traces |
| Power | 1.50 mm | 0.30 mm | 0.5 mm | +33.5V, +27V, +17V, GND power rails |

- **Power class:** +33V5, +27V, +17V, GND, SPKR+, SPKR-
- **Default class:** everything else

## Wiring pads — recovered verbatim

| Pad | Size | Drill | Silkscreen label |
|-----|------|-------|------------------|
| Signal pads (inputs, pots) | 2.0 mm | 1.2 mm | IN1, VOL_H, VOL_W, … |
| Power pads (transformer, speaker) | 3.0 mm | 1.5 mm | T1_A, T1_CT, T1_B, SPK+, SPK- |
| Ground pad | 3.0 mm | 1.5 mm | GND (star ground) |
| Footswitch pads | 2.0 mm | 1.2 mm | FS_REV, FS_TREM, FS_MRB, FS_GND |

## Ground plane design — recovered verbatim
1. Pour covers the entire bottom layer except pad clearances.
2. Connect to the star ground via multiple vias near C_main.
3. Ground-stitching vias every 15 mm along the perimeter.
4. Do NOT split the ground plane — keep it continuous.
5. Route all signal traces on the TOP layer only.
6. Bottom layer is ground plane only.
7. Use thermal-relief pads (4 spokes) for through-hole ground connections.

In KiCad: Edit → Fill Zones → B.Cu → Net GND; clearance 0.3 mm, min width
0.25 mm, thermal relief gap 0.5 mm, spoke width 0.5 mm.

## Gerber export from KiCad (8/9) — recovered verbatim
1. Run DRC (Inspect → Design Rules Check). Fix all errors.
2. Refill zones (Edit → Fill All Zones, shortcut B).
3. File → Fabrication Outputs → Gerbers (.gbr).
4. Output folder: `JLCPCB`.
5. Layers: F.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts.
6. General options: plot reference designators; check zone fills before plotting.
7. Gerber options: Protel filename extensions; subtract soldermask from silkscreen; coordinate format 4.6 mm.
8. Plot.
9. Generate Drill Files: Excellon; alternate drill mode for oval holes; map = Gerber; origin absolute; mm; decimal zeros. Generate drill + map.
10. Zip the output folder (.gbr + .drl).

Alternative: install the "Fabrication Toolkit" plugin (repo
`https://raw.githubusercontent.com/Bouni/bouni-kicad-repository/main/repository.json`)
to generate JLCPCB-ready zipped Gerbers in one click.

## Pre-order checklist — recovered verbatim
- [ ] DRC passes with zero errors
- [ ] All zones filled
- [ ] Board outline is a closed shape on Edge.Cuts
- [ ] All mounting holes present and correctly sized
- [ ] No copper within 0.5 mm of board edge
- [ ] Correct pad sizes and drills on all footprints
- [ ] Ground plane covers entire bottom layer, no isolated islands
- [ ] All test points and wiring pads labeled on silkscreen
- [ ] Power trace widths 1.5 mm+ (rails), 2.5 mm+ (speaker/power amp)
- [ ] Polarity markers on electrolytics; pin-1 dots on ICs
- [ ] LM1875/LM317 oriented toward the board edge nearest the heatsink
- [ ] Gerber preview on JLCPCB matches your design (every layer)
