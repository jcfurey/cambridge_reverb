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
| Layers | **4** *(2026-09-08, errata #24; was 2)* | F.Cu signal / In1 GND plane / In2 signal / B.Cu signal + GND pour — stackup **JLC04161H-7628** (0.035 mm outer copper, 0.2104 mm 7628 prepreg, 1.065 mm core, 0.0152 mm inner copper) |
| Dimensions | 190 × 115 mm | Matches original 25-5274-2 board footprint |
| PCB Qty | 5 | Minimum order |
| PCB Thickness | 1.6 mm | Matches original board thickness |
| Copper Weight | 2 oz *(1 oz is enough — see the 2026-09-07 rules note below)* | Handles power-amp traces better |
| Surface Finish | HASL (with lead) | Best for hand-soldering through-hole; cheapest |
| Solder Mask | Green | Fastest processing |
| Silkscreen | White | Standard |
| Via Covering | Tented | Protects vias from solder bridges |
| Confirm Production File | Yes | Always review the Gerber preview |
| Remove Order Number | Specify location | "JLCJLCJLC" text on silkscreen, or pay $1 to remove |

Estimated cost: ~$2–7 for 5 boards + ~$5–15 shipping. Under $25 total.

> **2026-09-07/08:** 190 × 115 mm is above the "100 × 100 mm" tier (2-layer $2, **4-layer
> ~$7** per five), so the bare board is area-priced (a live quote is the only reliable
> number — expect roughly $30–60 per five for the 4-layer 170 × 100 / 190 × 115 boards); choose **1 oz** outer
> copper and **lead-free HASL** unless you have a reason not to — both are the no-surcharge
> defaults. Order the **JLC04161H-7628** stackup (the default 4-layer 1.6 mm), no impedance
> control needed; the In1 GND plane is generated as a full-board zone and Gerbers must
> include `In1.Cu` / `In2.Cu`.

## SMT assembly of the mixed SMD/THT board (`kicad/smd/`) — cost model, added 2026-09-07

JLCPCB's economic assembly is priced per **solder joint** and per **part type**, not per
board area: setup $8 + stencil $1.50 + $0.0016 per joint, plus **$3 per order for every
"extended" (non-basic-library) part type**. `kicad/gen/jlc_cost.py` reads the generated
assembly BOM and shows which knob moves the number:

| | Before | After (errata #23) |
|---|---:|---:|
| SMD parts placed / assembly lines | 90 / 31 | 95 / 29 |
| Extended part types (× $3) | 7 ($21) | 3 ($9: MMBF5457 SOT-23, 3.09 k E96, 68 nF) |
| Joints per board | 183 | 194 |
| Assembly for 5 boards (estimate) | ~$32 | **~$20** |

What changed: every SMD capacitor is **1206** (the 1210 line — 1 µF X7R 50 V and the
Zobel 100 nF — was an extended part for no electrical gain; 1206 1 µF/50 V X7R is a
basic part), the two optional MRB caps (`C_mrb_450`, `C_mrb_750`, marked "(opt)") are
**DNP** — on the board, excluded from the assembly BOM and the position file — and the
mid-cut gyrator uses **2.2 nF / 180 k** (E24, same 1.86 H) instead of 1.8 nF / 220 k.
Three **fiducials** (1 mm copper, 2 mm mask; `FID1–3`, an asymmetric set) sit in the
margins for the placement camera. Rotation of SOT-23 and SMA parts in JLC's preview must
still be checked by eye (KiCad's 0° and JLC's 0° differ for some packages).

## KiCad design rules for JLCPCB — recovered, re-checked 2026-09-07

The "JLCPCB min" column is from jlcpcb.com/capabilities (2-layer, 1 oz, checked
2026-09-07); the "Value" column is what both `.kicad_pro` files now enforce in DRC, so
`kicad/gen/check.sh` catches a fab violation before the Gerbers do. Where our own margin
was already stricter than JLC it stays.

| Rule | Value (DRC) | JLCPCB min | Notes |
|------|-------|------------|-------|
| Min track width | 0.25 mm (10 mil) | 0.10 mm (1 oz) / 0.16 mm (2 oz) | Comfort; audio doesn't need tighter |
| Min clearance | 0.20 mm (8 mil) | 0.10 mm | Safe, avoids extra fees |
| Min via drill / diameter | 0.3 / 0.6 mm | 0.3 / 0.45 mm (0.15 mm holes or < 0.45 mm vias cost extra) | No surcharge; classes use 0.4/0.8, 0.8/1.4, 1.0/1.6 |
| Min through-hole drill | 0.3 mm | 0.15 mm | Smallest used: 0.75 mm (TO-92) |
| **Min annular ring (PTH + via)** | **0.18 mm** | **0.18 mm absolute, 0.25 mm recommended** | Errata #23: stock TO-92 (0.15) and the LM1875 footprint (0.175) failed this — fixed (0.35 / 0.20) |
| **Hole-to-hole (different nets)** | **0.5 mm** | 0.45 mm (PTH), 0.2 mm (vias) | was 0.25 |
| **Hole-to-copper** | **0.3 mm** | 0.254 mm | was 0.25 |
| Pad-to-pad (SMD, different nets) | 0.20 mm (class clearance) | 0.15 mm | |
| Board edge clearance | 0.5 mm | 0.2 mm | plus a 2 mm routing keepout frame (`gen_pcb.py`) |
| **Solder-mask dam** | **0.10 mm** | 0.10 mm (green) | |
| Min silkscreen width / text height | 0.15 mm / 1.0 mm | 0.15 mm / 1.0 mm | |
| Copper weight | **1 oz** | — | 2 oz was in the recovered order spec; 1 oz is enough (Part 6c: 2.5 mm / 2.0 mm traces at 1.7 A peak) and cheaper |

### Net classes — recovered verbatim

| Net class | Track width | Clearance | Via drill | Use for |
|-----------|------------|-----------|-----------|---------|
| Default | 0.30 mm | 0.20 mm | 0.3 mm | All signal traces |
| Power | 1.50 mm | 0.30 mm | 0.5 mm | +33.5V, VREG_IN, +17V, GND power rails |

- **Power class:** +33V5, VREG_IN, +17V, GND (HighCurrent class: SPK_P, SPK_N, PA_OUT)
- **Default class:** everything else

## Wiring pads — recovered verbatim

| Pad | Size | Drill | Silkscreen label |
|-----|------|-------|------------------|
| Signal pads (inputs, pots) | 2.0 mm | 1.2 mm | IN1, VOL_H, VOL_W, … |
| Power pads (transformer, speaker) | 3.0 mm | 1.5 mm | T1_A, T1_CT, T1_B, SPK+, SPK- |
| Ground pad | 3.0 mm | 1.5 mm | GND (star ground) |
| Footswitch pads | 2.0 mm | 1.2 mm | FS_REV, FS_TREM, FS_MRB, FS_GND |

## Ground plane design — recovered verbatim (2-layer), superseded by the 4-layer stack (errata #24)
1. Pour covers the entire bottom layer except pad clearances.
2. Connect to the star ground via multiple vias near C_main.
3. Ground-stitching vias every 15 mm along the perimeter.
4. Do NOT split the ground plane — keep it continuous.
5. Route all signal traces on the TOP layer only.
6. Bottom layer is ground plane only.
7. Use thermal-relief pads (4 spokes) for through-hole ground connections.

> **4-layer (generated):** In1 is the solid, unbroken GND plane (rule 4 now holds by
> construction — nothing is routed on it), In2 is an inner signal layer, B.Cu keeps a GND pour
> around the bottom traces, and `gen_pcb.py` places the perimeter stitching vias of rule 3
> (every 15 mm, locked). Signals route on F.Cu, In2 and B.Cu; every part has keepout
> areas between its pins on the outer layers so traces cannot run through footprints.

In KiCad: Edit → Fill Zones → B.Cu → Net GND; clearance 0.3 mm, min width
0.25 mm, thermal relief gap 0.5 mm, spoke width 0.5 mm.

## Gerber export from KiCad (8/9) — recovered verbatim
1. Run DRC (Inspect → Design Rules Check). Fix all errors.
2. Refill zones (Edit → Fill All Zones, shortcut B).
3. File → Fabrication Outputs → Gerbers (.gbr).
4. Output folder: `JLCPCB`.
5. Layers: F.Cu, In1.Cu, In2.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts (4-layer since errata #24).
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
