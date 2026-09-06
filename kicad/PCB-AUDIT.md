# PCB layout audit

Audit of `cambridge_reverb.kicad_pcb` (and the `power_section_demo`), done with
KiCad 8.0.9 (`kicad-cli pcb drc`, `pcbnew` geometry queries). First pass
2026-06-15 on the auto-grid starter board; **re-audited 2026-09-06** after the
footprint fixes, the floor-plan placement and the Freerouting pass. Status and
DRC numbers live in `PCB-NOTES.md`; this file is the category-by-category
layout review.

## Verdict (2026-09-06)
Electrically faithful (netlist matches the ERC-clean schematic) and now
**structurally clean before routing: 0 DRC errors, 0 warnings** on the placed
board (was 9 real errors + ~155 silk warnings on the grid-placed board). The two
real footprint defects from the first audit are fixed with datasheet-derived
project footprints, the bulk parts carry their real can/body sizes, and
placement follows the Part 5 floor plan. What remains is engineering judgement
on the *autorouted* copper (see `PCB-NOTES.md`), not layout hygiene.

## 1. Footprints
All 113 components carry a THT, hand-solderable footprint; pad numbers match the
symbol pins (verified — netlist resolves with 0 unconnected at the schematic).

| Class | Footprint | Verdict |
|-------|-----------|---------|
| R (¼ W) | `R_Axial_DIN0207…P5.08mm_Vertical` | ✅ compact vertical |
| R (1 W: `R_27V`) | `R_Axial_DIN0414_L11.9mm…P15.24mm` | ✅ **sized by value** (`gen_kicad.footprint_for`) |
| R (5 W: `R_bleed`) | `R_Axial_Power_L20.0mm_W6.4mm_P25.40mm` | ✅ sized by value |
| `R_spk_rtn` 0 Ω | `R_Axial_DIN0414…` (1 W-size link) | ✅ carries the full speaker current — fat pads, not a ¼ W jumper |
| C (film/disc) | `C_Disc_D7.5…P5.00mm` | ✅ generic |
| CP ≤ 22 µF / 47 µF | `CP_Radial_D5.0mm_P2.00mm` / `D6.3mm_P2.50mm` | ✅ sized by value; tantalums `C_reg_in`/`C_reg_out1` on 2.5 mm spacing |
| CP 1000 µF / 2200 µF / 4700 µF | `CP_Radial_D12.5_P5.00` / `D16.0_P7.50` / `D18.0_P7.50` | ✅ **real can sizes** (Panasonic FC per BOM) — the old board had every can as D8 |
| D / LED | `D_DO-41…` / `LED_D3.0mm` | ✅ |
| JFET | `TO-92_Inline` | ✅ for J113 / SOT-23-on-adapter |
| TL072 | `DIP-8_W7.62mm` | ✅ (socket in the real build) |
| LM317 | `TO-220-3_Vertical` | ✅ |
| **LM1875** | **`cambridge_reverb:TO-220-5_Vertical_P1.70mm_LM1875`** | ✅ **FIXED.** TI NDH0005D inline TO-220-5 (1.70 mm pitch, 0.89 × 0.38 mm leads). 1.1 mm drill (as stock) with **1.45 mm pads → 0.175 mm annular** (rule 0.15, JLCPCB 0.13); pad-local clearance 0.2 mm so the 0.25 mm pad gap passes next to the 0.3 mm HighCurrent clearance. Stock footprint gave 0.0875 mm → 5 DRC errors. |
| Fuse | `Fuseholder_Clip-5x20mm…` | ✅ |
| **Bridge** | **`cambridge_reverb:Bridge_KBP_P3.81mm`** | ✅ **FIXED.** Real KBP outline from Diodes DS39310 (KBP404G–KBP410G): 3.81 mm pitch, 1.2 mm drill / 2.0 mm pads, body 14.5 × 3.5 mm, pins **+ ~ ~ −**. Schematic bridge symbol renumbered to match. Was a `PinHeader_1x04` placeholder. |
| Pots ×5 / jacks / DIN / tank | **`WirePad_1x0N_P2.54mm_D1.2mm`** | ✅ Part 4 signal wire pads (2.0 mm / 1.2 mm drill) on the wiring edge; were 2.54 mm pin headers |
| Speaker / transformer | **`WirePad_1x0N_P5.08mm_D1.5mm`** | ✅ Part 4 power wire pads (3.0 mm / 1.5 mm drill) |
| Mounting | 4 × `MountingHole_3.2mm_M3` (NPTH, unique refs H1–H4) | ✅ new; 0.5 mm pour clearance |
| Test points ×26 | **`cambridge_reverb:TestPoint_THT_D2.0mm_Label`** | ✅ 2.0 mm pad / 1.0 mm drill; silk label = the footprint value (net alias) |

## 2. Placement — Part 5 floor plan, generated
`gen_pcb.py` now places into the five documented **zones, left → right**:

```
INPUT/PREAMP | TONE | REVERB/TREMOLO (+MRB) | POWER AMP | POWER SUPPLY
o o o  wiring edge: jacks · pots · tank/pots/DIN · speaker · transformer  o o o
```
- Zone widths are balanced automatically so every column packs to about the
  same height; inside a zone the parts keep their **sheet (signal-chain) order**,
  sorted tallest-first within a sheet so the rows ("shelves") pack tightly with a
  1.3 mm courtyard gap and 4 mm channels between zones.
- **Heat-sinking devices on the top edge**, tab outward, with the Part 5 **10 mm
  keep-out** below them: `IC_PA` (LM1875) above the power-amp zone, `U1` (LM317)
  above the PSU zone — both reachable by a chassis bracket.
- **All off-board wiring on the bottom edge** under its own zone (Part 5: board
  flips up for service); `T1` (transformer) pinned to the far right, so the
  nearest signal zone is a full PSU-zone width away (Part 5: "no signal traces
  within 15 mm of transformer pads").
- **Test-point strip** across the top of each zone: 26 labelled `TP_*` pads
  (footprint `TestPoint_THT_D2.0mm_Label`, value = net alias on silk), one GND
  per zone — the bring-up nodes of Parts 3/5. Table in `PCB-NOTES.md`.
- Reference/value text is hidden (silk clutter); showing refs is a GUI pass.
- Not encoded: "no traces under LFO timing components" — an autorouter cannot
  honour it; check the tremolo area by eye.

## 3. Board outline & chassis fit — figure corrected ⚠️
- Outline: **190 × 115 mm**, matching the original 25-5274-2 (errata #9).
- **The earlier density numbers were inflated.** The old `gen_pcb.py` summed
  `GetBoundingBox()` *including the hidden reference/value text boxes*, which
  roughly doubles a resistor's footprint. Text-less bounding boxes give:

| Board | Usable area | Parts area | Packing |
|-------|------------:|-----------:|--------:|
| 190 × 115 mm (original) | 16 150 mm² | ~5 290 mm² | **~33 %** (was reported 48–53 %) |
| 155 × 90 mm (Part 7 "safe-bet") | 9 450 mm² | ~5 290 mm² | **~56 %** (was reported 82–90 %) |

  So the 155 × 90 board is **no longer "not buildable"** — 56 % is dense but
  realistic for THT (this board packs the 190 × 115 to only ~62 % of its
  height). Errata #9 still stands: **measure the chassis first**, then set
  `BW, BH` in `gen_pcb.py` and regenerate (the placer rebalances the zones).

## 4. Net classes & design rules
- Three classes: **Default 0.5 mm / Power 1.5 mm / HighCurrent 2.5 mm**, with
  0.2 / 0.3 / 0.3 mm clearances; patterns target `+33V5`, `SPK_P`, `SPK_N`,
  `PA_OUT` (HighCurrent) and `VREG_IN`, `+17V`, `GND` (Power). Verified to match
  real nets, and **verified to survive the DSN export** (`route_board.py`), so
  the autorouter uses these widths.
- Rules (from Part 4) are conservative and JLCPCB-safe; the one exception (the
  LM1875 annular ring, §1) is resolved.

## 5. Copper, GND pour, layers
- 2-layer. **Bottom = GND pour** connecting all GND pads; refilled after routing.
- Mounting holes keep 0.5 mm of pour clearance; no isolated-copper items.
- Star-ground / stitching (Part 3/4) remain hand decisions on top of the pour.

## 6. Routing
- Done headlessly with **Freerouting** (`gen/route_board.py`), both in a two-layer
  mode and a **top-only** mode (bottom declared a plane so signals stay on F.Cu,
  the Part 4 intent). Results, unrouted counts and the DRC after import are in
  **`PCB-NOTES.md`**.
- An autorouter does not know audio: expect to tidy by hand the input/JFET-gate
  runs, the LFO area, the speaker/`+33V5` loop and the ground return before fab.

## Prioritized actions for a fab-ready board
1. **Measure the chassis** and lock the outline (errata #9) — regenerate.
2. Review the routed copper (§6) and hand-fix what an autorouter gets wrong.
3. Show reference designators on silk; DRC to zero again.
4. Gerbers per `docs/04-jlcpcb-fabrication.md` + `production/CHECKLIST.md`.
