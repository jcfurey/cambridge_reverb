# PCB — generated placement + headless autoroute

`cambridge_reverb.kicad_pcb` is built by two scripts (KiCad 8 `pcbnew` API):

1. **`gen/gen_pcb.py` — placement.** Every footprint from the schematic
   (`gen_kicad.py`'s component list) is placed into the **Part 5 floor plan**:
   columns left → right `INPUT/PREAMP (+TONE below it) | TREMOLO/MRB (+REVERB
   below it, next to its tank pads) | POWER AMP | POWER SUPPLY`, signal-chain
   order inside each zone (ICs and cans tallest-first, small parts in schematic
   order, short parts **stacked** beside tall ones so a can or DIP does not waste
   the row height under every resistor), column widths auto-balanced to equal
   height and repaired until no column overflows, a **labelled test-point strip**
   at the top of every zone (see *Test points*). `IC_PA` (LM1875) and `U1` (LM317)
   sit on the **top edge**, tab outward, with the Part 5 **10 mm keep-out**; all
   off-board wiring lands on **Part 4 wire pads along the bottom edge** (2.0 mm
   signal pads, 3.0 mm speaker/transformer pads), `T1` at the far right. 4 × M3
   mounting holes, 190 × 115 mm `Edge.Cuts`, bottom **GND pour**, **keepout rule
   areas** (2 mm edge frame + squares round the holes, tracks/vias only) so the
   router respects the fab's edge clearance, and two **locked escape stubs** off the
   LM1875's pins 4/5 (see below). Design rules in the `.kicad_pro` are **JLCPCB's
   2-layer limits** (Part 4) and `cambridge_reverb.kicad_dru` adds two crosstalk
   rules (below). **DRC before routing: 0 errors, 0 warnings** apart from the two
   dangling stubs.
2. **`gen/route_board.py` — routing.** Exports a Specctra DSN (the project's three
   net classes come through: 0.5 / 1.5 / 2.5 mm), injects Freerouting's
   `autoroute_settings` (bottom layer 6× trace cost so it is used only for short
   jumpers and the GND pour stays whole; via cost 80), runs **Freerouting 1.9.0**
   under `xvfb-run`, imports the SES and refills the pour.

Regenerate: `python3 kicad/gen/gen_pcb.py && python3 kicad/gen/route_board.py`
(needs Java + `kicad/gen/freerouting.jar` = freerouting-1.9.0.jar, git-ignored;
`apt install xvfb`). **Verify:** `kicad/gen/check.sh tht --no-regen` (or `smd`)
runs ERC + DRC and writes the reports to **`kicad/reports/`** — the committed
`*-erc.rpt` / `*-drc.json` files there are the evidence for every number in this
file. Without `--no-regen` the script regenerates first (which discards routing).

## Routing result — THT board (`kicad-cli 8.0.9 pcb drc`, this commit; `kicad/reports/tht-drc.json`)
| Item | Result |
|------|-------:|
| Connections (ratsnest, incl. 28 test points, the dual-gang speed pot, the errata #20 tone stack and the #21/#22 parts) | 222 |
| **Routed** | **215 / 222** (`unconnected_items`: 7) |
| DRC violations (`--severity-all`, JLCPCB limits + `.kicad_dru` crosstalk rules) | **1 error** — `starved_thermal` on the GND pad of `C_rec_byp`; 0 warnings; **0 rule hits** |
| Track segments | 1 421 — **F.Cu 5 645 mm**, B.Cu 902 mm (short jumpers) |
| Vias | 86 |
| Router settings | Freerouting 1.9.0, `-mp 150`, B.Cu trace cost ×7, via cost 60, class clearances HighCurrent 0.6 mm / TankDrive 1.2 mm (`route_board.py --bottom-cost 7 --via-cost 60`) |

The seven open connections: two pieces of **`+33V5`** at the power amp (`C_byp2` ↔ a
bottom jumper at ≈ (113, 62), and a 40 mm top run ending at ≈ (137, 68) — the 2.5 mm
Power trace could not thread the 0.6 mm rule past the PA parts; join at full width),
`JWT` (`R_j4` → the treble-pot pad on the wiring edge), `LFO_OUT` (two trace ends in the
tremolo zone), `R_DRVO` and `TKDRV` (the tank-drive path `C_rev1` / `R_drv3`, held apart
by the 1.2 mm TankDrive rule; 3–10 mm links) and `TREM_S` (`VTL1` LDR → `C_dc_blk`).
Eight GUI touches; listed so nobody trusts the copper blindly.

Honest note: the previous placement (before errata #21/#22) routed to 208/212, DRC clean,
without the crosstalk rules. This placement carries eight more parts and the two
clearance rules; fourteen settings were tried (6–16 open): ×8 / 60 → 6 open but 3 starved
thermals, **×7 / 60 → 7 open + 1 thermal (committed)**, ×6 / 80 → 13, ×7 / 80 → 12,
×8 / 80 → 10, ×9 / 60 → 10; with a 1.0 / 2.0 mm rule set every run left 14; with only
the HighCurrent rule 10–13; with TankDrive at 0.8 mm 8–16. **Evaluate candidates in
place** (next to the `.kicad_pro` / `.kicad_dru`): `kicad-cli pcb drc` on a copy in
another directory silently runs without the net classes and the rules and under-counts
(that cost an hour here). Freerouting is deterministic for identical input but
sensitive to small placement changes — always re-check `kicad/reports/` after
regenerating.

## Mixed SMD / THT variant — `smd/cambridge_reverb_smd.kicad_pcb` (155 × 90 mm)
Same schematic, second footprint profile (`--profile smd` on all three scripts),
sized for the **Part 7 155 × 90 "safe-bet" chassis**. What moves to SMD and what
deliberately does not:

| SMD (90 parts) | Stays THT (and why) |
|----------------|---------------------|
| 53 × R → **0805** (thin-film for the 1 M gate/input resistors); `R_reg2` → 1206 (85 mW) | LM1875, LM317, KBP bridge, 5 W / 1 W resistors, `R_zobel`, the 0 Ω speaker link — power |
| ≤ 100 nF → **1206** (C0G/NP0 in the signal path, 100 V X7R snubbers) | **all electrolytics** — a radial can standing up uses *less* board than an SMD can |
| 120 nF MRB, 1 µF coupling, `C_zobel` → **1210** (X7R 50/100 V; PPS film on a 2220 pad if you prefer) | TL072 × 2 in **DIP-8 sockets**, the tone TL074 in a **DIP-14 socket** (availability audit: swappable) |
| 1N4007 → **SMA** (S1M); 1N4148 → **SOD-123** (1N4148W) | `R_s1`, `R_s2`, `R_rec2` — bench-trimmed per JFET (errata #15), swap an axial not an 0805 |
| MMBF5457 → **SOT-23** fitted directly (1 D / 2 S / 3 G, errata #18) — no TO-92 adapter | LED, vactrol, toroid, fuse clip, wire pads, test points |

Placement rules for this profile: 6 mm margin (corner M3 holes stay), 0.4 mm part
gap (0.9 mm body-to-body once the courtyards are counted), 3 mm channels;
otherwise the same floor plan, test-point strips and escape stubs. The wiring edge
differs in one point: with the Bass/Treble pots and the MID CUT toggle (errata #20)
the 13 connector groups need ~146 mm and the 155 mm board has 137 mm between the
corner holes, so the **three input-jack pad groups run down the left edge**
(rotated, in the margin next to the preamp — the shortest input wiring); everything
else stays on the bottom edge, `T1` far right. Two more deliberate differences:
- **GND pour on both layers.** SMD ground pads have no through-hole to the bottom
  pour, so the top gets a pour too — connected *solid* to the SMD ground pads only
  (THT pads ground through the bottom pour, no top thermal spokes). The router is
  shown only the bottom plane (`route_board.py` drops the F.Cu plane from the DSN),
  so it drops a via from every SMD ground pad: real copper connectivity, and the
  top pour is extra ground copper on refill. (With both planes visible the router
  treated every SMD ground pad as "done" and 20 of them ended on pour islands.)
- **Net-class widths 2.0 / 1.0 mm** (HighCurrent / Power, 0.25 mm clearance) in
  `smd/cambridge_reverb_smd.kicad_pro`, vs 2.5 / 1.5 on the THT board. Part 4's
  widths were sized for the 190×115 board; at ~1.7 A peak and under 1 A RMS, 1 oz
  copper needs well under 1 mm, and 2.5 mm traces cannot pass between 0805/1206
  pads on a 155×90 board (errata #11 addendum). Parts area **~5 090 mm² → 54 % of the 155 × 90 usable area**
(the THT-profile parts would be 68 %). **Pre-route DRC: 0 errors, 0 warnings** beyond the two stub warnings.

**Routing result (this commit; `kicad/reports/smd-drc.json`)** — `route_board.py --in kicad/smd/cambridge_reverb_smd.kicad_pcb --bottom-cost 6 --via-cost 80` (class clearances HighCurrent 0.4 mm / TankDrive 0.8 mm, the board's `.kicad_dru` numbers):

| Item | Result |
|------|-------:|
| Connections (incl. 28 test points, the dual-gang speed pot, tone stack, #21/#22 parts; SMD ground pads count via the top pour) | 223 |
| **Routed** | **210 / 223** |
| DRC (`--severity-all`, JLC limits + rules) | **4 errors** — `starved_thermal` on the GND pads of `IC3` pin 11, `C_s2`, `R_spk_rtn`, `C_rec_byp`; 0 warnings; **0 rule hits** |
| Track segments | 1 154 — F.Cu 3 740 mm, B.Cu 1 124 mm |
| Vias | 120 (most are SMD-ground-pad drops to the bottom pour) |

The thirteen open items: four GND pour fragments (`C_s1`, `C_bref`, `IC1` pin 4 and a
top-pour island — stitching vias), `+33V5` ×2 and `+17V` ×1 (short rail links at the power
amp / tremolo bias, 3–6 mm), `AC1` / `AC2` (the snubber caps `C102` / `C103` to the
transformer pads, 10 mm), `LFO_OUT` (IC2 pin 1 to its trace, 27 mm along the top),
`Q2D` and `Q2G` (two 2 mm gaps in the preamp) and `TKDRV` (tank drive, 14 mm). All are
GUI touches; with the four thermals that is seventeen — the price of the crosstalk rules
on a 56 %-full board.

Sweep on this placement (150 passes; every candidate DRC'd *in place* with the rules):
plain routing (no class clearances) ×7 / 100 → **9 open but 47 rule violations** (32
HighCurrent, 15 TankDrive); 0.4 / 0.8 mm: ×7 / 100 → 13 open + 3 clearance + 3 mask
errors, **×6 / 80 → 13 open, 4 thermals, rules clean (committed)**; 0.35 / 0.6 mm →
12–14 open with 12–14 rule hits; HighCurrent-only 0.4 → 13 open, 8–11 TankDrive hits;
0.6 / 1.2 mm → 13–27 open. The placement before errata #21/#22 routed to 7 open without
rules; the SMD board sits at the router's limit at 155 × 90 (56 % parts by area), so
expect to finish a dozen links by hand after any regeneration — or drop the two rules
in `smd/cambridge_reverb_smd.kicad_dru` and take the 9-open plain routing knowingly.

**Assembly path:** JLCPCB places the SMD side (all are basic-class part sizes),
you hand-solder the ~76 THT parts. `production/smd/bom-jlcpcb.csv` (Comment /
Designator / Footprint / LCSC — LCSC left for the parts picker, nothing invented)
and `production/smd/cambridge_reverb_smd-top-pos.csv` (kicad-cli position file)
are the two inputs. Regenerate:
`python3 kicad/gen/gen_kicad.py --profile smd && python3 kicad/gen/gen_pcb.py --profile smd && python3 kicad/gen/gen_bom.py --profile smd --jlc && python3 kicad/gen/route_board.py --in kicad/smd/cambridge_reverb_smd.kicad_pcb`.

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
| `VB_3` | TP_VBIAS_3 | VBIAS_3 | Tone | ~8.5 V (mid-rail reference for IC3; every IC3 output sits here too) | spice (ac_tonestack) |
| `TMK` | TP_MK_OUT | MK_OUT | Tone | ~8.5 V DC + AC: the Bass/Treble network after the ×2 make-up, before the MID CUT — flat with the pots at noon; toggle SW_MID and 800 Hz drops ~10 dB at `TONE` but not here | spice (sweep_tonestack) |
| `TONE` | TP_TONE_OUT | TONE_OUT | Tone | 0 V DC (after C_tout); AC: volume-pot wiper, the internal FX-send tap (via R_fx_pad) | Part 1 §7, errata #20 |
| `VB_R` | TP_VBIAS_R | VBIAS_R | Reverb | ~8.5 V (mid-rail reference for IC1) | spice |
| `TK_IN` | TP_TANK_IN | TANK_IN | Reverb | AC: tank drive, ≈ 11× the driver input; no DC (after C_rev1) | spice |
| `TK_OUT` | TP_TANK_OUT | TANK_OUT | Reverb | AC: tank return, a few mV–tens of mV; silence → tank/cable | Part 9 |
| `QRD` | TP_QRD | QRD | Reverb | 8–9 V target (recovery JFET drain; trim R_rec2 like R_s1) | errata #15 |
| `BLEND` | TP_BLEND | BLEND | Reverb | ~8.5 V DC (summer output about VBIAS_R) + dry/wet mix AC, unity | spice (tran_reverb_mixer) |
| `GND` | TP_GND_REV | GND | Reverb | probe ground | — |
| `VB_T` | TP_VBIAS_T | VBIAS_T | Tremolo | ~8.5 V (mid-rail reference for IC2) | spice |
| `LFO` | TP_LFO | LFO_OUT | Tremolo | AC: the LFO — **10.6 Hz** with the speed pot at min, **0.60 Hz** at max, ~0.48 V amplitude (0.96 Vpp), sine-ish | spice (tran_tremolo_lfo, sweep_lfo_speed) |
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
`PRE` → `TMK` → `TONE` → `BLEND` → `TREM` → `MRB` → `PA_IN` → `SPK`.

## Crosstalk screen and the two routing rules it produced (Part 6c §4)
`kicad/gen/crosstalk_audit.py` estimates the mutual capacitance of every parallel run
between an aggressor net (PA_OUT / SPK / ZOB at 9.8 Vrms, the 24 Vrms AC1/AC2, VRAW,
+33V5 ripple, TANK_IN at 3 Vrms) and a sensitive node, and turns it into "coupled level
vs signal" and a loop gain. On the first routing of the errata #20 boards the worst pairs
were `TANK_IN` → `TANK_OUT` (11 mm side by side, **−37 dB**, THT) and `PA_OUT` →
`TANK_OUT` (0.25 mm apart, −37 dB, loop gain −44 dB, SMD); nothing near oscillation,
but not a layout anyone would sign. So:

| Rule (`.kicad_dru`, tracks/vias only) | Clearance | Also given to the router as | Why |
|---|---:|---|---|
| `HighCurrent` (PA_OUT, SPK, +33V5, VRAW, AC1, AC2) ↔ `Default` copper | **0.6 mm** | class HighCurrent clearance 600 µm in the DSN | 9.8 Vrms / 24 Vrms aggressors beside 20 mV–1 V nodes; 1.0 mm was tried first and left 14 (THT) / 27 (SMD) links unroutable |
| `TankDrive` (R_DRVO, TKDRV, TANK_IN) ↔ TANK_OUT / QRG / WET / DRVP | **1.2 mm** | class TankDrive clearance 1200 µm | reverb drive leaking into the reverb return |

Pad geometry is exempt (the LM1875's 1.7 mm pin row, 0805 feedback parts, snubber
caps), which is why the numbers are carried as *rules* rather than net-class clearances.
On the SMD board the rules are 0.4 / 0.8 mm (`smd/cambridge_reverb_smd.kicad_dru`) —
more left the router short of links (see the SMD sweep above).

After re-routing (`kicad/reports/crosstalk-{tht,smd}.md`): THT worst pair `TANK_IN` →
`TANK_OUT` **−50 dB** (was −37), then `PA_OUT` → `PA_BIAS` −66 dB (loop −59 dB); SMD
`TANK_IN` → `TANK_OUT` −42 dB (was −37; the two nets share adjacent pads on the tank
connector, so a few mm of side-by-side copper is unavoidable), `PA_OUT` → `TANK_OUT`
gone from the table, worst loop −68 dB. A hand pass should still move the tank return
away from the drive at the connector — the audit will show whether it helped.

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
- **Route the board in place.** `pcbnew.LoadBoard` picks the net classes up from
  the `.kicad_pro` next to the board; a copy routed from another directory came
  back with every track at the 0.2 mm default (199 `track_width` + 201 `clearance`
  errors). `route_board.py` now refuses a board without its project file.
- The router only knows the board *outline*: KiCad's 0.5 mm copper-to-edge rule
  and the mounting holes' local clearance do not reach it, and on the SMD board it
  ran a trace 45 mm along the left edge and under H3. `gen_pcb.py` therefore adds
  **keepout rule areas** (tracks + vias, pours allowed): a 2 mm frame inside the
  edge and a 7.2 mm square round each M3 hole — they export as `(keepout …)`.
- The SES import can leave a few zero-length track segments (`track_dangling`
  warnings); `route_board.py` prunes them.
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
| 190 × 115 mm (original 25-5274-2) | 16 150 mm² | ~6 450 mm² (THT parts) | **~40 %** |
| 155 × 90 mm (Part 7 "safe-bet") | 9 450 mm² | ~6 450 mm² (THT parts) / ~5 090 mm² (SMD profile) | **~68 %** / **~54 %** |

With the errata #19/#20 parts the THT board's columns use ~97 % of their height
at a 1.2 mm part gap (3.5 mm channels; the placer moves width between columns
until none overflows) — 190 × 115 is now the right size for the THT build, and
the 155 × 90 board only fits with the SMD profile. Errata #9 still applies —
**measure the chassis**, set `BW, BH` in `gen_pcb.py`, regenerate, re-route.

## Power-section routing demo — DRC clean
`power_section_demo.kicad_pcb` (also from `gen_pcb.py`) routes the +33V5 (2.5 mm)
and +17V (1.5 mm) rails by hand over a GND pour as a net-class width reference:
`kicad-cli pcb drc` → 0 violations, 2 ratsnest lines left on purpose (`VRAW`,
`VREG_IN` — the latter needs a via to cross the +17V trunk).
