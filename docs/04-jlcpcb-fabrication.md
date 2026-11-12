# Vox Cambridge Reverb — Part 4: JLCPCB Fabrication Guide

> Reconstructed document — see `PROVENANCE.md`. Order specs, design rules, net
> classes, Gerber/drill export steps, silkscreen layout, and the pre-order
> checklist are recovered substantially verbatim.
>
> **Ordering the SMD / THT board (2026-11):** the order package is generated —
> `production/smd/` holds the Gerber + drill zip, the assembly BOM with LCSC part numbers
> and the pick-and-place file, and `production/smd/README.md` lists the order settings.
> This Part is the background: design limits, net classes, the reasoning. Build it with
> `kicad/gen/build.sh smd`; the manual Gerber steps further down are only needed for the
> THT board.
>
> Note: the board outline below shows 190×115 mm (matching the original
> 25-5274-2 footprint). Part 7 recommends 155×90 mm as a conservative default
> pending chassis measurement. Use whichever your measured chassis supports;
> set the Edge.Cuts outline accordingly.

## JLCPCB order specifications — recovered verbatim

| Parameter | Setting | Notes |
|-----------|---------|-------|
| Layers | **4** *(2026-09-08, errata #24; was 2)* | F.Cu signal + GND pour / In1 GND plane / In2 signal / **B.Cu GND plane** *(errata #31; B.Cu used to carry tracks)* — stackup **JLC04161H-7628** (0.035 mm outer copper, 0.2104 mm 7628 prepreg, 1.065 mm core, 0.0152 mm inner copper): each signal layer is 0.21 mm from its own plane |
| Dimensions | 190 × 115 mm (THT board) · **170 × 105 mm (SMD / THT board, the assembled one)** | 190 × 115 matches the original 25-5274-2 board |
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
board area. Their price table as last updated 2026-10-22 (read 2026-11-12): setup $8.18 +
stencil $1.53 + $0.0016 per joint, plus **$3.07 per order for every "extended"
(non-basic-library) part type**; basic parts carry no loading fee, and JLCPCB's assembly
pages say the same of "preferred" extended parts on Economic PCBA (the table itself does
not list them — `jlc_cost.py` prints the worst case too). `kicad/gen/jlc_cost.py` reads
the generated assembly BOM and shows which knob moves the number:

| | Before | Errata #23 (assumed classes) | 2026-11-11, classes looked up (errata #30) | **2026-11-12, re-selected (errata #36)** |
|---|---:|---:|---:|---:|
| SMD parts placed / assembly lines | 90 / 31 | 95 / 29 | 95 / 31 | **99 / 26** |
| Extended part types | 7 | 3 | 14 + 2 "preferred" | **3** + 3 "preferred" |
| Joints per board | 183 | 194 | 194 | 202 |
| Assembly fees for 5 boards | ~$32 | ~$20 | ~$54 | **~$21** |
| … with the parts | | | | **~$45** ($4.83 of parts per board) |

*After errata #38–#41 (the same day): six more 0805 parts on the board — four bleeders, the
tank loop breaker, and the tremolo's coupling capacitor now a placed 2.2 µF ceramic
instead of a hand-soldered electrolytic — **105 parts in 28 lines, 3 extended + 4
"preferred", 214 joints: $20.63 of assembly fees for five boards, $45.20 with the parts
($4.91 per board).** No new extended line.*

The second column rested on an assumption — that common 1206 capacitor values are
basic-library parts whatever the dielectric. The third looked every part up, but only in
the footprint the board already had: in 1206, C0G above 100 pF and 100 V X7R are all
extended. **The fourth looked the other way round — what does the basic library hold,
and can the circuit use it?** C0G 33 pF (preferred), 100 pF and 2.2 nF, and a 100 V X7R
100 nF, are basic parts in **0805**; the remaining values were moved onto those and onto
the two C0G lines that have no basic equivalent in any size (22 nF and 100 nF), see
errata #36 for the list. The board still keeps C0G on every high-impedance and
frequency-setting node (DC-biased X7R on a 1 MΩ node in a combo cabinet is a
microphone) and 100 V parts on the 33.5 V rail and across the bridge. What is left as
extended: 22 nF C0G, 100 nF C0G, and the JFET.

What changed in the earlier passes: every SMD capacitor was made **1206** (the 1210 line — 1 µF X7R 50 V and the
Zobel 100 nF — was an extended part for no electrical gain; 1206 1 µF/50 V X7R is a
basic part), the two optional MRB caps (`C_mrb_450`, `C_mrb_750`, marked "(opt)") are
**DNP** — on the board, excluded from the assembly BOM and the position file — and the
mid-cut gyrator uses **2.2 nF / 180 k** (E24, same 1.86 H) instead of 1.8 nF / 220 k.
Three **fiducials** (1 mm copper, 2 mm mask; `FID1–3`, an asymmetric set, ≥ 4 mm from the
edge) sit in the margins for the placement camera. `kicad/gen/fab_jlcpcb.py` writes the
pick-and-place file in JLCPCB's columns with the usual +180° on the SOT-23 parts; the
orientation of D1 / D2 and the four SOT-23s in JLCPCB's placement preview must still be
checked by eye before paying.

## KiCad design rules for JLCPCB — recovered, re-read 2026-11-11 (errata #31)

The "JLCPCB" column is their capability table as published on 2026-11-11
(jlcpcb.com/capabilities/pcb-capabilities; multilayer, 1 oz outer copper). The "Project"
column is what both `.kicad_pro` files and the `.kicad_dru` rules enforce in DRC —
`kicad/gen/verify.py` fails if a project value drops below JLCPCB's.

| Rule | Project (DRC) | JLCPCB | Notes |
|------|-------|------------|-------|
| Track width / spacing | 0.25 / 0.20 mm (smallest used: 0.30 / 0.20) | 0.09 / 0.09 mm multilayer | audio does not need tighter |
| Via drill / diameter | 0.3 / 0.6 mm minimum; every via on the boards is 0.4 / 0.8 or larger | 0.15 / 0.25 mm; **0.2–0.25 mm holes with a via under 0.45 mm cost extra** | no surcharge |
| Through-hole drill | 0.3 mm (smallest used 0.75 mm) | 0.15 mm; hole tolerance +0.13 / −0.08 mm, position ±0.075 mm | |
| Annular ring (PTH + via) | **0.20 mm** *(was 0.18)* | multilayer 1 oz: 0.20 recommended, 0.15 absolute | the LM1875 pads sit exactly on 0.20 (errata #23) |
| Hole-to-hole | 0.5 mm | pad holes 0.45 mm, via holes 0.2 mm | |
| **Hole-to-copper** | **0.35 mm** *(was 0.30)* | PTH to track 0.35 recommended / 0.28 minimum; **inner-layer PTH hole to copper 0.3 mm**; inner-layer via hole to copper 0.2 mm | this is the number that sizes every opening in the two ground planes |
| Pad-to-track / SMD pad-to-pad | 0.20 mm (class clearance) | 0.10 / 0.15 mm | |
| **Copper to board edge** | **0.5 mm, all four layers** | **0.2 mm from a routed edge or a routed slot; the edge itself is ±0.2 mm** (±0.1 mm "high precision"); 0.4 mm from a V-cut | 0.2 + 0.2 of tolerance + 0.1: copper never reaches the edge, and the board stays legal if JLCPCB adds V-cut rails for assembly. Traces stay 2 mm in (keepout frame) |
| Cut-outs / slots | none on this board | non-plated slot ≥ 1.0 mm wide, plated ≥ 0.35 mm (multilayer); no square inside corners | only the outline and four 3.2 mm NPTH holes |
| Unplated holes | 3.2 mm, copper 0.5 mm away + a keepout square | NPTH ≥ 0.5 mm; NPTH to track 0.2 mm | |
| Solder-mask dam | 0.10 mm | 0.10 mm (green) | mask expansion can be 1 : 1 since their 2025 LDI upgrade |
| Silkscreen | 0.15 mm stroke, 1.0 mm high; **text 0.15 mm off every pad** (`silk_to_pad` rule) | 0.15 mm / 1.0 mm; pad to silkscreen 0.15 mm | |
| Fiducials (assembly) | 1 mm copper, 4.0 mm from the edge | "1 mm fiducials centered at 3.85 mm from the panel edges" | |
| Copper weight | 1 oz outer, 0.5 oz inner | inner 0.5 oz by default (1 or 2 oz optional) | nothing but the short high-current runs is on the inner signal layer; see PCB-NOTES |

**Ground-system rules** (ours, not JLCPCB's — what makes the copper behave at radio
frequency; measured on the finished board by `kicad/gen/rf_audit.py`, enforced by
`verify.py`, reasons in errata #31 and PCB-NOTES):

| Rule | Value |
|---|---|
| Stack | `F.Cu` signal + ground pour · `In1` solid ground · `In2` signal · `B.Cu` solid ground — nothing routed on a plane |
| Plane clearance | 0.2 mm to copper, 0.35 mm to a hole; unused inner-layer pad copper removed, so a plane's opening round a foreign pin is hole + 0.7 mm and the web between 2.54 mm pins survives |
| Top pour to traces | 0.5 mm; **1.0 mm from high-impedance (HiZ) nets**; no sliver under 0.4 mm |
| Edge fence | ground vias every 5 mm, 2.5 mm in from the edge |
| Stitching | ground vias on a 7.5 mm grid wherever a via fits on every layer, 1 mm clear of every pad |
| SMD ground pads | each has its own via to the planes, beside the pad, never in it or under the part |

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

> **4-layer (generated, errata #31):** In1 and B.Cu are both solid GND planes — rules 4
> and 6 hold by construction, nothing is routed on either — In2 is the inner signal
> layer, buried between them, and F.Cu carries the component-side traces with a GND
> pour around them. `gen_pcb.py` places a ground via fence along the perimeter every
> 5 mm (rule 3 asked 15) and gives every SMD ground pad its own via; `stitch.py` adds
> ground vias on a 7.5 mm grid after routing and then fills the gaps the grid left (no
> free spot further than 6 mm from a ground via). Every part has keepout areas between
> its pins on the component side so traces cannot run through footprints.
>
> **Star ground (generated, errata #32):** the planes are SIGNAL ground only. The heavy
> returns — transformer centre tap, reservoir, LM1875 pin 3 with its decoupling and
> Zobel — are a separate net `PGND`, routed as 1.5 mm traces; the speaker's return pad is
> `SPK_N`. Two 0 Ω links join them: `R_spk_rtn` (`SPK_N` → `PGND`) and `R_gnd`
> (`SPK_N` → planes), the star. "Connect to the star ground via multiple vias near
> C_main" (step 2 above) is superseded: one link, no others.
> `kicad/gen/ground_audit.py` checks the result on the routed copper.
>
> **Ground loops (generated, errata #40, #43):** no ground copper within 3.8 mm of a
> mounting-hole centre on either outer layer (a screw head or a 7 mm washer on solder
> mask over ground copper is an unplanned chassis bond). Inside `PGND` the charging
> pulses have a run of their own from the centre tap to the reservoir's minus pad, so
> power ground is a star at that pad whatever the autorouter does with the rest.
> No copper neck under 0.2 mm anywhere (`min_connection` in the `.kicad_pro`).
> `kicad/gen/loop_audit.py` checks all of it.

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
- [x] All test points and wiring pads labeled on silkscreen (generated, errata #30)
- [ ] Power trace widths 1.5 mm+ (rails), 2.5 mm+ (speaker/power amp)
- [ ] Polarity markers on electrolytics; pin-1 dots on ICs
- [ ] LM1875/LM317 oriented toward the board edge nearest the heatsink
- [ ] Gerber preview on JLCPCB matches your design (every layer)
