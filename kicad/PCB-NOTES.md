# PCB — generated placement + headless autoroute

`cambridge_reverb.kicad_pcb` is built by two scripts (KiCad 8 `pcbnew` API):

1. **`gen/gen_pcb.py` — placement.** Every footprint from the schematic
   (`gen_kicad.py`'s component list) is placed into the **Part 5 floor plan**:
   columns left → right `INPUT/PREAMP (+TONE below it) | REVERB/TREMOLO/MRB |
   POWER AMP | POWER SUPPLY`, signal-chain order inside each zone, column widths
   auto-balanced to equal height. `IC_PA` (LM1875) and `U1` (LM317) sit on the
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
| Connections (ratsnest) | 145 |
| **Routed** | **144 / 145** (`unconnected_items`: 1) |
| DRC violations (errors + warnings, `--severity-all`) | **0** |
| Track segments | 753 — **F.Cu 3 683 mm**, B.Cu 351 mm (short jumpers on 26 nets) |
| Vias | 26 |
| Router settings | Freerouting 1.9.0, `-mp 150`, B.Cu trace cost ×6, via cost 80 (`route_board.py` defaults) |

**The one open connection is `PA_OUT`** in the power-amp column: the router left
a 2.5 mm F.Cu run ending on `D1` pin 1 (≈ 113, 47 mm) and a B.Cu fragment at
≈ (115, 55 mm) on the `C_out`/`R_zobel` side, with `R_bias1` sitting between
them. Every straight or dog-leg link I tried shorts through `R_bias1` pin 2, so
it is a 1-minute GUI job (nudge `R_bias1` or route around it) — not fudged here.

A parameter sweep on this placement (150 passes each) shows how much the bottom
cost matters: B.Cu cost ×3 → 7 unrouted, ×4 → 3 (+1 starved thermal), **×6 → 1**,
×4 with via cost 40 → 7. Freerouting is also run-to-run sensitive: the same
settings on earlier placements gave 5–10 open connections, so re-routing after a
placement change means re-checking the count, not assuming it.

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
