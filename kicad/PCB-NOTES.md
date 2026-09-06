# PCB — generated placement + headless autoroute

`cambridge_reverb.kicad_pcb` is built by two scripts (KiCad 8 `pcbnew` API):

1. **`gen/gen_pcb.py` — placement.** Every footprint from the schematic
   (`gen_kicad.py`'s component list) is placed into the **Part 5 floor plan**:
   columns left → right `INPUT/PREAMP (+TONE below it) | TREMOLO/MRB (+REVERB
   below it, next to its tank pads) | POWER AMP | POWER SUPPLY`, signal-chain
   order inside each zone, column widths auto-balanced to equal height, a
   **labelled test-point strip** at the top of every zone (see *Test points*). `IC_PA` (LM1875) and `U1` (LM317) sit on the
   **top edge**, tab outward, with the Part 5 **10 mm keep-out**; all off-board
   wiring lands on **Part 4 wire pads along the bottom edge** (2.0 mm signal
   pads, 3.0 mm speaker/transformer pads), `T1` at the far right. 4 × M3 mounting
   holes, 190 × 115 mm `Edge.Cuts`, bottom **GND pour**, and two **locked escape
   stubs** off the LM1875's pins 4/5 (see below). **DRC before routing: 0 errors,
   0 warnings** apart from the two dangling stubs.
2. **`gen/route_board.py` — routing.** Exports a Specctra DSN (the project's three
   net classes come through: 0.5 / 1.5 / 2.5 mm), injects Freerouting's
   `autoroute_settings` (bottom layer 6× trace cost so it is used only for short
   jumpers and the GND pour stays whole; via cost 80), runs **Freerouting 1.9.0**
   under `xvfb-run`, imports the SES and refills the pour.

Regenerate: `python3 kicad/gen/gen_pcb.py && python3 kicad/gen/route_board.py`
(needs Java + `kicad/gen/freerouting.jar` = freerouting-1.9.0.jar, git-ignored;
`apt install xvfb`). Then `kicad-cli pcb drc --severity-all kicad/cambridge_reverb.kicad_pcb`.

## Routing result (`kicad-cli 8.0.9 pcb drc`, this commit)
| Item | Result |
|------|-------:|
| Connections (ratsnest, incl. the 26 test points) | 166 |
| **Routed** | **161 / 166** (`unconnected_items`: 5) |
| DRC violations (errors + warnings, `--severity-all`) | **0** |
| Track segments | 872 — **F.Cu 3 896 mm**, B.Cu 397 mm (short jumpers on 29 nets) |
| Vias | 54 |
| Router settings | Freerouting 1.9.0, `-mp 150`, B.Cu trace cost ×7, via cost 60 (`route_board.py --bottom-cost 7 --via-cost 60`) |

**The five open connections** (all short, all in the power-amp / effects
columns; finish in the GUI):

| Net | Between | Where |
|-----|---------|-------|
| `PA_BIAS` | `TP_PA_BIAS` pad ↔ the PA_BIAS trace near `R_bias1`/`R_bias2` | PA column, (108,31)→(125,62) |
| `PA_IN` | `C_in_pa` pin 1 ↔ the PA_IN trace from the IC2-B buffer | tremolo → PA column, (72,51)→(120,60) |
| `PA_INV` | `IC_PA` pin 2 ↔ the feedback node (`R_fb`/`C_fb_hf`/`R_gain`) | PA column, (117,15)→(106,69) |
| `R_INV` | `IC1` pin 2 ↔ `R_drv1`/`R_drv2` | reverb zone, (28,76)→(75,87) |
| `TREM_OUT` | `R_trem1` pin 2 ↔ `C_dc_blk`/`TP_TREM_OUT` | tremolo zone, (34,62)→(50,47) |

Sweep on this placement (150 passes unless noted): B.Cu ×6 → 4 open + 1
starved thermal; ×6 / via 60 → 3 open + 1 starved thermal; **×7 / via 60 → 5
open, DRC clean (committed)**; ×6 / via 70 / 250 passes → 3 open + 1 starved
thermal. The DRC-clean board was preferred over one with fewer ratsnest lines
plus a `starved_thermal` error (that is a hand fix too). Before the test points
were added the same flow reached 144/145 (one `PA_OUT` link open); the 21 extra
test-point connections cost a few more. Freerouting is run-to-run sensitive —
after any placement change re-check the count, do not assume it.

## Test points (bench bring-up, Part 5 order)
26 labelled test points (`TP_*` in the schematic/BOM; footprint
`TestPoint_THT_D2.0mm_Label`: 2.0 mm pad / 1.0 mm drill — fit a header pin or a
bare 0.6 mm wire loop so a scope hook grabs it). They sit in a **strip across the
top of each zone**, the silkscreen prints the alias, and every zone has a **GND**
pin for the probe clip. Expected values are from Part 3's troubleshooting table,
Part 2's set-up notes and the ngspice suite (`spice/README.md`).

| Silk | Ref | Net | Zone | Expect (DC unless noted) | Source |
|------|-----|-----|------|---------------------------|--------|
| `VRAW` | TP_VRAW | VRAW | PSU | ~33–35 V unloaded, bridge output *before* F1 (fuse check: VRAW ≠ +33V5 → F1 open) | Part 2 |
| `+33V5` | TP_33V5 | +33V5 | PSU | ~33.5 V | Part 3 |
| `VREG` | TP_VREG_IN | VREG_IN | PSU | ~31–33 V (LM317 input after the 100 Ω/1000 µF pre-filter) | Part 3 |
| `+17V` | TP_17V | +17V | PSU | 17.0–17.5 V (R_reg2 = 3.09 k; 16.9 V with 3.0 k) | Part 3, errata #10 |
| `GND` | TP_GND_PSU | GND | PSU | probe ground | — |
| `Q1D` | TP_Q1D | Q1D | Preamp | **8–9 V** target; ~12 V with the recovered Rs = 2.2 k → trim R_s1 (≈1–1.2 k) per device | errata #15, spice |
| `Q2D` | TP_Q2D | Q2D | Preamp | 8–9 V target (same trim, R_s2) | errata #15 |
| `PRE` | TP_PRE_OUT | PREAMP_OUT | Preamp | AC: amplified guitar signal (preamp gain ≈ 22 dB/stage in sim) | spice |
| `GND` | TP_GND_PRE | GND | Preamp | probe ground | — |
| `TONE` | TP_TONE_OUT | TONE_OUT | Tone | AC: volume-pot wiper; the internal FX-send tap (via R_fx_pad) | Part 1 §7 |
| `VB_R` | TP_VBIAS_R | VBIAS_R | Reverb | ~8.5 V (mid-rail reference for IC1) | spice |
| `TK_IN` | TP_TANK_IN | TANK_IN | Reverb | AC: tank drive, ≈ 11× the driver input; no DC (after C_rev1) | spice |
| `TK_OUT` | TP_TANK_OUT | TANK_OUT | Reverb | AC: tank return, a few mV–tens of mV; silence → tank/cable | Part 9 |
| `QRD` | TP_QRD | QRD | Reverb | 8–9 V target (recovery JFET drain; trim R_rec2 like R_s1) | errata #15 |
| `BLEND` | TP_BLEND | BLEND | Reverb | ~8.5 V DC (summer output about VBIAS_R) + dry/wet mix AC, unity | spice (tran_reverb_mixer) |
| `GND` | TP_GND_REV | GND | Reverb | probe ground | — |
| `VB_T` | TP_VBIAS_T | VBIAS_T | Tremolo | ~8.5 V (mid-rail reference for IC2) | spice |
| `LFO` | TP_LFO | LFO_OUT | Tremolo | AC: the LFO — ~16 Hz at the fast end (100 k/100 n), ~0.5 V amplitude in sim; speed pot sweeps it | spice (tran_tremolo_lfo) |
| `TREM` | TP_TREM_OUT | TREM_OUT | Tremolo | AC: post-LDR signal, amplitude pumping at the LFO rate when tremolo is on | Part 1 §5 |
| `PA_IN` | TP_PA_IN | PA_IN | Tremolo | ~8.5 V DC (IC2-B buffer about VBIAS_T) + the full effects-chain signal | roast R3 |
| `GND` | TP_GND_TREM | GND | Tremolo | probe ground | — |
| `MRB` | TP_MRB_OUT | MRB_OUT | MRB | AC: mid-boosted signal, peak ~580–600 Hz | spice (ac_mrb) |
| `PA_B` | TP_PA_BIAS | PA_BIAS | Power amp | ~16.75 V (V+/2 from the 22 k/22 k divider) | Part 2 |
| `PA_OUT` | TP_PA_OUT | PA_OUT | Power amp | **~16–17 V** (LM1875 pin 4, V+/2) — wrong → IC bad or oscillating | Part 3 |
| `SPK` | TP_SPK | SPK_P | Power amp | ~0 V DC after C_out (any DC here → C_out); AC = speaker signal | errata #7 |
| `GND` | TP_GND_PA | GND | Power amp | probe ground | — |

Bring-up order (Part 5): rails (`VRAW`/`+33V5`/`VREG`/`+17V`) with the series
light bulb → `PA_B`/`PA_OUT`/`SPK` DC with no signal → JFET drains (`Q1D`,
`Q2D`, `QRD`) and trim → `VB_R`/`VB_T` → signal generator into IN1, follow
`PRE` → `TONE` → `BLEND` → `TREM` → `MRB` → `PA_IN` → `SPK`.

## What the autorouter does NOT know — review by hand before fab
- **Audio layout.** It routes by cost, not by ear: the JFET gate inputs
  (`GUITAR_IN`, `Q1G`/`Q2G`), the reverb recovery input (`TANK_OUT`) and the LFO
  timing nodes may run next to `+33V5`/`PA_OUT`. Move or reroute them; keep the
  tremolo `LFO_*` nets short (Part 5 keep-out: no traces under the LFO timing parts).
- **Grounding.** The bottom pour is one net; the Part 3 **star ground** (power-amp
  return, speaker return, preamp ground) is a hand decision — at minimum keep the
  `C_main`/`R_spk_rtn`/`C_out` returns together and away from the input jacks.
- **HighCurrent loop.** The 2.5 mm `+33V5` / `PA_OUT` / `SPK_P` traces are correct
  in width but the router may loop them around the power-amp column; tighten them.
- **Bottom-layer jumpers** cut the pour locally. Check every GND pad still has ≥ 2
  thermal spokes (the DRC `starved_thermal` check) after any edit.
- **Silkscreen:** reference designators are hidden (regenerate with
  `hide_text=False` in `gen_pcb.py` and tidy in the GUI).

## Why the LM1875 has pre-routed stubs
The TO-220-5 pins are on a **1.70 mm pitch**. With the 0.3 mm HighCurrent/Power
clearance, no trace wider than ~1.35 mm can enter pins 3, 4 or 5 past their
neighbours, so the 2.5 mm `PA_OUT` / `+33V5` traces are physically unroutable to
the pin — every autorouter run left exactly those two connections open. A hand
layout necks the trace down at the pin; `gen_pcb.py` does the same with two
**locked 0.9 mm stubs** (pin 4 straight down 3.5 mm, pin 5 fanned 4 mm right).
Locked tracks export as `(type fix)`, so the router keeps them and attaches the
full-width trace at their ends. 0.9 mm × 3.5 mm of 1 oz copper at ~1.7 A peak is
a non-issue thermally. Pin 3 (GND/V−) needs nothing: it is a through-hole pad in
the bottom pour.

## Freerouting notes (what actually worked)
- **v1.9.0** honours `-mp` (max passes) and always writes the `.ses` — unrouted
  connections stay as ratsnest. Needs an X display even in CLI mode → `xvfb-run`.
- **v2.1.0** in CLI mode ignores `-mp`, `router.max_passes` *and*
  `router.job_timeout`, and only writes output when nothing is unrouted; with one
  hard connection it rips up forever (>400 passes observed). Its multi-threaded
  router also crashed on this board. Not usable for a bounded run.
- The Specctra export refuses duplicate references (the mounting holes are H1–H4
  for that reason). KiCad exports the GND zone as a `(plane)`, so GND pads need no
  traces — but bottom-layer traces slice the pour, which is why the bottom layer
  is made expensive rather than free: a free two-layer run put 2.3–2.5 m of copper
  on the bottom and left 10–11 GND pads on islands.

## Chassis-fit reality check ⚠️ (corrected 2026-09-06)
The earlier 48–53 % / 82–90 % densities counted hidden text in the bounding
boxes. Text-less footprint areas:

| Board | Usable area | Parts area | Packing |
|-------|------------:|-----------:|--------:|
| 190 × 115 mm (original 25-5274-2) | 16 150 mm² | ~5 290 mm² | **~33 %** |
| 155 × 90 mm (Part 7 "safe-bet") | 9 450 mm² | ~5 290 mm² | **~56 %** |

The 155 × 90 board is dense but plausible for THT; on 190 × 115 the placed columns
use ~85 % of the height at a 1.5 mm part gap. Errata #9 still applies — **measure
the chassis**, set `BW, BH` in `gen_pcb.py`, regenerate, re-route.

## Power-section routing demo — DRC clean
`power_section_demo.kicad_pcb` (also from `gen_pcb.py`) routes the +33V5 (2.5 mm)
and +17V (1.5 mm) rails by hand over a GND pour as a net-class width reference:
`kicad-cli pcb drc` → 0 violations, 2 ratsnest lines left on purpose (`VRAW`,
`VREG_IN` — the latter needs a via to cross the +17V trunk).
