# PCB layout audit

Full audit of `cambridge_reverb.kicad_pcb` (and the `power_section_demo`), done
with KiCad 8.0.9 (`kicad-cli pcb drc`, `pcbnew` geometry queries). The board is a
**generated, auto-placed, GND-poured starter** — placed, not signal-routed.

## Verdict
Electrically faithful (netlist matches the ERC-clean schematic) and structurally
sound (outline, GND pour, net classes). The open items are a **handful of real
placement errors (9)**, a large pile of **cosmetic silkscreen warnings (≈155)**,
and the **131 unrouted nets** — all of which trace back to one root cause: the
board is **densely packed for all-through-hole** (see §3). None are wiring errors.

## DRC summary (`kicad-cli pcb drc`)

| Bucket | Count | Severity | Nature |
|--------|------:|----------|--------|
| `unconnected_items` | 131 | error | **Unrouted** signal nets (GND is poured). Expected — routing is the next step. |
| `annular_width` | 5 | error | All on `IC_PA` (LM1875, TO-220-5). Stock footprint, see §1. |
| `courtyards_overlap` | 2 | error | Two neighbours too close at grid density. |
| `hole_near_hole` / `copper_edge_clearance` | 1 + 1 | error | Placement artifacts at the grid edges. |
| `silk_overlap` + `silk_over_copper` | 144 + 8 | warning | Footprint outline silk colliding at density (refs/values already hidden). |
| `text_height` / `text_thickness` / `silk_edge_clearance` | 3 | warning | Stray footprint fab/silk text. |

So: **9 real (non-routing) errors**, ~155 cosmetic warnings, 131 unrouted.
The `power_section_demo` board is **0 violations**.

## 1. Footprints
All 102 components carry a THT, hand-solderable footprint; pad numbers match the
symbol pins (verified — netlist resolves with 0 unconnected at the schematic).

| Class | Footprint | Verdict |
|-------|-----------|---------|
| R | `R_Axial_DIN0207…P5.08mm_Vertical` | ✅ compact vertical, good for density |
| C / CP | `C_Disc_D7.5…` / `CP_Radial_D8.0_P3.5` | ✅ generic; bump CP size for the real 4700 µF `C_main` |
| D / LED | `D_DO-41…` / `LED_D3.0mm` | ✅ |
| JFET | `TO-92_Inline` | ✅ for J113 / SOT-23-on-adapter |
| TL072 | `DIP-8_W7.62mm` | ✅ (add a socket in the real build) |
| LM317 | `TO-220-3_Vertical` | ✅ annular 0.40 mm |
| **LM1875** | `TO-220-5_Vertical` | ⚠️ **pads 1.275 mm on a 1.1 mm drill → 0.0875 mm annular**, below the 0.15 mm rule (and JLCPCB's 0.13 mm). See fix below. |
| Fuse | `Fuseholder_Clip-5x20mm…` | ✅ large; give it room |
| Bridge | `PinHeader_1x04` | ⚠️ **placeholder** — KBP410G has no stock footprint here; make a real 4-pin inline before fab |
| **Pots ×5** | `PinHeader_1x03` | ✅ **fixed this pass** — the pots are reused/**off-board** (panel-mounted), so they are 3-pad wiring connectors now, not 16 mm panel-pot footprints (was a real mis-modeling and a big silk-overlap source) |
| Jacks / speaker / DIN / tank / xfmr | pin headers | ✅ off-board wiring connectors (intentional) |

**LM1875 annular fix (recommended):** the TO-220-5 lead is ~0.9×0.5 mm, so the
1.1 mm drill is generous. Options, best first: (a) a project TO-220-5 footprint
with **1.4 mm pads** (annular 0.2 mm at 1.0 mm drill; pad-pad gap 0.3 mm at the
1.7 mm pitch still meets clearance); (b) accept 0.0875 mm — TO-220 through-holes
are mechanically robust, but it is below JLCPCB's 0.13 mm, so confirm with the fab;
(c) relax the project rule to 0.13 mm (only helps with wider pads). Not auto-fixed
here because it means shipping a custom power-device footprint.

## 2. Placement
- **Auto-grid**, centered horizontally this pass; off-board connectors on the
  bottom **wiring edge**, the 25 mm toroid in a reserved right strip.
- **Floor-plan adherence (Part 5):** the grid fills in schematic/sheet order, so
  parts are *loosely* grouped by block (PSU, preamp, …) but not laid into the
  documented L→R bands (Input/Preamp → Tone → Reverb/Trem → Power Amp → PSU).
  Proper zoning is manual work.
- **Silk/courtyard overlaps are a density symptom, not a wiring problem.** At the
  ~13 mm grid pitch the larger parts (DIP-8, TO-220, electrolytics, fuseholder)
  sit close enough that their silk outlines touch. Spreading them out doesn't fit
  (see §3). References and values are already hidden to cut the noise.

## 3. Board outline & chassis fit ⚠️ (the headline)
- Outline: **190 × 115 mm**, matching the original 25-5274-2 (errata #9).
- **Packing density** (Σ footprint bounding boxes ÷ usable area, printed by
  `gen_pcb.py`): **~48 %** on 190 × 115 (was 51 % before the pot fix) — feasible
  but **dense** for single-sided THT routing — and **~82 %** on the Part 7
  155 × 90 "safe-bet", which is **not buildable** as drawn.
- This density is the root cause of the silk/courtyard/edge items. **Before
  committing to a board size: measure the real chassis** (it may exceed the
  155 × 90 worst case), **and/or move the small passives to SMD** to roughly halve
  the parts area and open up routing room.

## 4. Net classes & design rules
- Three classes: **Default 0.5 mm / Power 1.5 mm / HighCurrent 2.5 mm**.
- Patterns now correctly target `+33V5`, `SPK_P`, `SPK_N`, `PA_OUT` (HighCurrent)
  and `VREG_IN`, `+17V`, `GND` (Power) — the `SPKR±`→`SPK_P/SPK_N` bug was fixed in
  the review round. Verified the patterns match real nets.
- Rules (from Part 4) are conservative and JLCPCB-safe **except** the 0.15 mm min
  annular vs the LM1875 footprint (§1). Vias are pre-sized per class (0.4/0.8/1.0
  mm drill).

## 5. Copper, GND pour, layers
- 2-layer. **Bottom = continuous GND pour** (connects all 55 GND pads — that net
  is effectively routed). Top is free for signal routing.
- No isolated-copper or zone-fill DRC issues. Star-ground / stitching (Part 3/4)
  are placement-time decisions for the manual pass.

## 6. Routing status
- **Signal nets: unrouted** (131 ratsnest connections) — KiCad has no headless
  autorouter, so this is GUI hand-work.
- **Demonstrated** in `power_section_demo.kicad_pcb`: `+33V5` (2.5 mm) and `+17V`
  (1.5 mm) rails routed over a GND pour, **DRC 0 violations**.

## Prioritized actions for a fab-ready board
1. **Resolve the size/density first** (measure chassis or go SMD) — everything
   else depends on it.
2. Place into the Part 5 floor-plan zones; that clears the silk/courtyard items.
3. Fix the **LM1875 annular** (wider-pad TO-220-5) and make a **real KBP410G**
   bridge footprint.
4. Route (top signal, bottom GND), HighCurrent for the speaker/PA path.
5. DRC to zero → Gerbers per `docs/04-jlcpcb-fabrication.md` + `production/CHECKLIST.md`.
