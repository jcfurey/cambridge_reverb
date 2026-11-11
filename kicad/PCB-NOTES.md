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
2. **`gen/route_board.py` — routing.** Exports a Specctra DSN (the project's net
   classes come through), strips the In1 plane layer, injects Freerouting's
   `autoroute_settings` and the per-class routing clearances, runs **Freerouting 1.9.0**
   under `xvfb-run`, imports the SES and refills the pours.
3. **`gen/finish_routes.py` — the last links.** A grid maze router that closes the
   connections Freerouting leaves open, with the project's rules as written (below).

Rebuild: **`kicad/gen/build.sh tht`** (or `smd`) — generate, route, finish, reports,
order package, verify; about ten minutes. Needs Java + `kicad/gen/freerouting.jar`
(freerouting-1.9.0.jar, git-ignored), `xvfb`, `python3-numpy`, `python3-scipy`, ngspice.
**Verify an existing build:** `kicad/gen/verify.py tht` (or `smd`); `kicad/gen/check.sh
<profile> --no-regen` rewrites the ERC / DRC reports in **`kicad/reports/`**, the
committed evidence for the numbers in this file. Freerouting's result is not
bit-reproducible from run to run (the open-link count moved between 7 and 15 on the SMD
board during this work); `finish_routes.py` and the DRC gate are what make the outcome
the same — complete and clean — every time.

## Status — both boards fully routed, 0 DRC errors, 0 warnings (2026-11-11)

`kicad/gen/build.sh <smd|tht>` runs the whole chain; `kicad/gen/verify.py <profile>` is
the gate (`kicad/reports/verify-*.txt`: **49 / 49** checks on the SMD board, **40 / 40**
on the THT board). Numbers from `kicad-cli 8.0.9 pcb drc --severity-all`, reports in
`kicad/reports/`.

| | SMD / THT board (`smd/`, the JLCPCB one) | THT board |
|---|---:|---:|
| Outline | **170 × 105 mm** | 190 × 115 mm |
| Parts / nets / connections | 178 / 85 / 232 | 178 / 85 / 232 |
| Routed by Freerouting 1.9.0 (150 passes) | 217 | 224 |
| Closed by `finish_routes.py` | 15 | 8 |
| **Open connections** | **0** | **0** |
| DRC (JLCPCB limits, `.kicad_dru` rules, keepouts) | **0 errors, 0 warnings** | **0 errors, 0 warnings** |
| Track segments | 1 095 — F.Cu 2 370 mm, In2 1 583 mm, B.Cu 1 139 mm | 1 155 — F.Cu 1 974 mm, In2 2 474 mm, B.Cu 1 228 mm |
| Vias (+ locked perimeter stitching vias) | 87 (+ 27) | 24 (+ 34) |
| Footprint keepout areas | 144 | 152 |
| Worst crosstalk pair (`reports/crosstalk-*.md`) | `PA_OUT` → `PA_BIAS` −90 dB, loop −82 dB | `TANK_IN` → `SUMJ` −64 dB; worst loop −77 dB |
| Router settings | via cost 60, B.Cu ×1.2 | via cost 50, B.Cu ×1.2 |

### How the last links get closed — `gen/finish_routes.py`
Freerouting takes each net class as one width and one clearance, so on every run the
same two kinds of connection stay open:

- **signal-level branches of a power net** — `PA_OUT` to the feedback parts `R_fb` /
  `C_fb_hf`, `+33V5` to the bias divider. A 1.5 mm trace with its 0.4 / 0.6 mm rule does
  not fit between 0805 pads, although those branches carry microamps;
- **the tank drive** (`R_DRVO`, `TKDRV`, `TANK_IN`): its 0.6 / 0.8 mm spacing is only
  required from the tank *return* nets (the `.kicad_dru` rule), but the router has to
  keep it from everything.

`finish_routes.py` reads the open links from KiCad's own DRC and routes them with an A*
search on a 0.1 mm grid over F.Cu / In2 / B.Cu, using the rules as written: per-pair
clearances exactly as the `.kicad_dru` states them, the footprint / edge / hole keepouts,
hole-to-hole spacing, no via on an SMD pad, none within 1 mm of a ground pin (the plane's
thermal spokes). A link attaches to the nearest point of the copper it has to reach.
Widths: the class width first; a rail link that cannot get through is tried at 1.0 mm;
a link that only feeds a resistor, a small capacitor or a test point — and does not end
on one of the parts that carry the amps — may neck down to 0.5 mm. The script prints
every link with its length, width and the reason for a reduced width, and KiCad's DRC is
the judge afterwards. On the committed SMD board it placed 15 links: six at 0.5 mm
signal width, five on `PA_OUT` / `+33V5` at 1.0 mm (feedback network, bias divider and
the D1 clamp), one at the full 1.5 mm, and the three tank-drive nets.

### Mixed SMD / THT variant — what is SMD and what is not
Same schematic, second footprint profile (`--profile smd` on every script).

| SMD (96 footprints, 94 placed by JLCPCB) | Stays THT (and why) |
|----------------|---------------------|
| 57 × R → **0805** 1 %; `R_reg2` → 1206 (85 mW) | LM1875, LM317, KBP bridge, 5 W / 1 W resistors, `R_zobel`, the 0 Ω speaker link — power |
| every film / ceramic C → **1206**: C0G in the signal path, 100 V X7R on the rails and the bridge, 1 µF X7R (`gen/jlc_parts.py`) | **all electrolytics** — a radial can standing up uses *less* board than an SMD can |
| 1N4007 → **SMA** (M7) | TL072 × 2 in **DIP-8 sockets**, the tone TL074 in a **DIP-14 socket** (swappable) |
| MMBF5457 → **SOT-23** fitted directly (1 D / 2 S / 3 G, errata #18); 2N3904 → MMBT3904 on the E-B-C-renumbered SOT-23 | `R_s1`, `R_s2`, `R_rec2` — bench-trimmed per JFET (errata #15), swap an axial not an 0805 |
| `C_mrb_450`, `C_mrb_750`: footprints only (DNP) | LEDs, vactrol, toroid, fuse clip, wire pads, test points |

Placement: 6 mm margin, 1.2 mm part gap, the input-jack pads down the **left edge**
(shortest input wiring, their labels beside them), everything else on the bottom edge
with `JP_BR` and `T1` at the far right. GND pour on both outer layers (SMD ground pads
sit solid in the top pour and get a via to the In1 plane). Net-class widths on this
board: HighCurrent 1.5 mm, Power 0.5 mm, HiZ 0.3 mm, Default 0.5 mm.

**Assembly path:** JLCPCB places the 94 SMD parts; you solder 36 through-hole parts and
the wiring. The order package — Gerber zip, BOM with LCSC numbers, pick-and-place file,
assembly drawing — is in `production/smd/` (`gen/fab_jlcpcb.py`).

## Silkscreen (2026-11-11)
Every part has its reference on the front silk at JLCPCB's legend minimum (1.0 mm high,
0.15 mm stroke, glyphs 0.65 mm wide). The placer reserves a **label strip above every
small part** — the label shares the gap to the row above, so on the THT board it costs
no area and on the SMD board 0.75 mm per row — which keeps every label off the pads and
out from under its neighbours, and leaves the strip as extra routing room on copper.
DIP sockets, the fuse clip, the 5 W / 1 W resistors and the toroid carry the reference
inside their outline; the two heat-sinked TO-220s below (the tab side is the board
edge). Test points print their net alias instead.

Wiring pads say what each pad is for:

| Group | Pads |
|---|---|
| `J_IN1` / `J_IN2` / `J_IN3` | `T` tip, `S` sleeve |
| all seven pot groups | `CCW` · `W` · `CW` — **lug 1 = CCW end, 2 = wiper, 3 = CW end; clockwise = more** on every control (errata #29). `POT_SPD_A` / `POT_SPD_B` are the two gangs of one dual pot |
| `SW_MID` | `A` · `B` |
| `REV1` (tank) | `IN` · `G` · `OUT` · `G` |
| `FS1` (footswitch) | `REV` · `TRM` · `MRB` · `G` · `G` · `G` — each button shorts its line to a `G` |
| `LS1` | `+` · `−` |
| `T1` | `AC` · `CT` · `AC` |
| `JP_BR` | `NO CT` `ONLY` — the bridge-negative link, see below |

The board's name and revision are on the top edge; `JLCJLCJLCJLC` on the bottom silk is
where JLCPCB may print the order number.

## Build options (2026-11-11)

**Transformer / rectifier — `JP_BR` (errata #26).**
- Centre-tapped secondary (the original transformer, ~48 V CT; or a 2 × 24 V toroid in
  series): ends to the two `AC` pads, tap to `CT`, **`JP_BR` open**. The bridge works as
  a two-diode full-wave rectifier.
- Single 24 V winding, no tap (or two 24 V windings in parallel): ends to the two `AC`
  pads, `CT` pad empty, **fit a wire link in `JP_BR`**.
- Both at once shorts each half-winding through a bridge diode. Bring the supply up on a
  series lamp either way.

**Voicing — `C_s1`, `C_s2` (errata #28).** Source-bypass electrolytics, default not fitted.

| Fitted | Preamp gain | THD at 0.1 V pk in | at 0.2 V pk | Character |
|---|---:|---:|---:|---|
| neither (default) | 21 dB | 0.5 % | 1.1 % | clean; full power from ~55 mV pk |
| `C_s1` only | 33 dB | 1.0 % | 14 % | breaks up with humbuckers / hard picking |
| both | 45 dB | 35 % | 43 % | overdriven at any guitar level (8 % at 20 mV) |

(`spice/tran_preamp_headroom.cir`.) The JFET drain trim of errata #15 is the same in all
three.

**Footswitch (errata #27).** No pedal: reverb and tremolo follow their pots, MRB is
out. Pedal buttons short `REV` (reverb off), `TRM` (tremolo off), `MRB` (MRB **on**) to
`G`. MRB without a pedal: link `FS1` pads 3–4.

## Test points (bench bring-up, Part 5 order)
28 labelled test points (`TP_*` in the schematic/BOM; footprint
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

## Four layers, keepouts and rules by impedance (errata #24, 2026-09-08)

**Stack** (both boards, JLCPCB JLC04161H-7628, 1.6 mm): `F.Cu` signal — `In1.Cu` **solid
GND plane** — `In2.Cu` inner signal layer — `B.Cu` signal with a GND pour. `gen_pcb.py`
writes the plane as a full-board zone, keeps the B.Cu pour (shield and return around the
bottom traces; it makes no pad connections — the plane does, with thermal reliefs — so
crowded bottom traces cannot starve a spoke), and drops **perimeter GND stitching vias** every 15 mm (locked; they tie
the pour to the plane and make the board edge a ground ring). Every F.Cu and In2 trace
sits 0.21 mm from the GND plane — 7× closer than the 1.5 mm of the two-layer boards, so
trace-to-trace coupling drops ~10× and the plane is a real RF return; B.Cu traces sit on
the 1.07 mm core with the GND pour around them. Through-hole ground pads connect to the
plane through their holes (thermal reliefs); SMD ground pads get a via from the router
(the top GND pour of the two-layer SMD board is gone). `In2` started as a **+17 V plane**
(`IN2_PLANE = "+17V"` in `gen_pcb.py` brings it back): with the footprint keepouts
confining the outer layers to the gaps between parts, two routing layers left 33–43
links open on the THT board, so In2 carries signals (long runs, under the plane) and
+17 V is routed as 1.0 mm Power traces. The plane layer is **removed from the DSN**
the router sees (`route_board.py strip_layers`): Freerouting 1.9 ignores `active off`
(it routed 7 m of copper on the planes), and typed as a `power` layer it treated every
through-hole pad touching the plane as already connected and left adjacent same-net pins
open. So the router works a 3-layer board (F.Cu / In2 / B.Cu) whose ground target is the
B.Cu pour; KiCad joins the In1 plane on import.

**No routes through footprints.** For every real part (not test points, fiducials or
holes) the generator writes rule areas named `kp_<ref>` — tracks and vias disallowed on
F.Cu and B.Cu — over the space *between* the part's pads: the strips between the pins of
a row and the body between two rows, across the full courtyard. Any pad is still
reachable from outside its footprint; nothing runs between the legs of a resistor, under
a DIP, or through the toroid. Power-only parts (every pad on a rail / GND / speaker net)
are exempt — a rail trace under the bridge or a filter can is not the noise path this is
for, and the 1.5 mm rail traces need the room. 147 areas on the THT board, 139 on the SMD
board; Freerouting gets them as Specctra keepouts, KiCad DRC checks them (`keepout` test).

**Net classes and rules.** Widths / class clearances from the `.kicad_pro`; the
`.kicad_dru` rules bind tracks and vias only (fixed pad geometry such as the LM1875's
1.7 mm pin row is exempt) and `route_board.py` hands the router the same numbers as
per-class clearances so the result is rule-clean. 147 / 139 keepout areas (THT / SMD).

| Class | Nets | Width THT / SMD | Class clearance | Rules (THT / SMD) |
|---|---|---:|---:|---|
| `HiZ` | JFET gates and the RF nodes ahead of them (GUITAR_IN, RF1, Q1G, Q2G, RF2, QRG, TANK_OUT), tone ladder + wipers (JA/JB/JWB/JTA/JTB/JWT/JOUT, TONE_OUT), DRVP, OBUF_IN, LFO timing (WN1, LFO_P), MRB_T, PA_BIAS, WET/REVWCW | 0.3 / 0.3 | 0.3 / 0.25 | HighCurrent ≥ **0.6 / 0.4 mm** |
| `Default` (low-Z signal) | op-amp outputs, drains, everything else | 0.5 / 0.5 | 0.2 / 0.2 | HighCurrent ≥ **0.6 / 0.4 mm** |
| `Power` | +17V, +17V_PRE, VREG_IN, GND | 1.0 / 0.8 | 0.3 / 0.25 | (In2 carries +17V as a plane; separation from HiZ = the class clearance + the 0.21 mm plane geometry) |
| `HighCurrent` | PA_OUT, ZOB, SPK_P/N, +33V5, VRAW, AC1, AC2 | 1.5 / 1.5 | 0.3 / 0.25 | see HiZ / Default rows (1 oz copper carries ~2.5 A at 1.5 mm; the amp peaks at 1.7 A) |
| `TankDrive` | R_DRVO, TKDRV, TANK_IN | 0.5 / 0.5 | 0.2 / 0.2 | ≥ **0.8 / 0.6 mm** from TANK_OUT / RF2 / QRG / WET / DRVP |

Origin: `kicad/gen/crosstalk_audit.py` (Part 6c §4) on the two-layer routing found the
reverb drive 0.3 mm from the reverb return (−37 dB) and PA_OUT 0.25 mm from the recovery
gate; the 2-layer rules (0.6 / 1.2 mm) got the worst pair to −50 dB at the price of open
links. A first 4-layer set (HighCurrent 1.0 mm, HiZ 0.5 mm, 2.5 mm rails) left ~70 links
open: a 0.5 mm HiZ clearance cannot enter a DIP pin between its 2.54 mm neighbours, and a
2.5 mm rail with 1.0 mm on each side does not fit the 1.6 mm gaps between parts once
nothing may run under them — so the numbers above are the ones the geometry allows, and
power-only parts (bridge, filter cans, clamp diodes, transformer / speaker pads) are
exempt from the keepouts. After re-routing on four layers (`kicad/reports/crosstalk-{tht,smd}.md`, h = 0.21 mm):
THT worst pair `TANK_IN` → `TANK_OUT` **−66 dB** (2-layer: −37, then −50 with rules),
`PA_OUT` → `PA_BIAS` −84 dB (loop −77 dB); SMD `TANK_IN` → `TANK_OUT` **−74 dB**
(was −42), worst loop `PA_OUT` → `PA_IN` −82 dB. Every entry is below −65 dB on both
boards: the planes did what the spacing rules alone could not.

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
- **Inner copper.** The wide rail and output traces partly run on In2 (0.5 oz at
  JLCPCB by default): 1.5 mm there is good for about 1 A RMS at a 10 K rise, which
  covers this amplifier (0.55 A average at full power). Order 1 oz inner copper if you
  want the margin.

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

With the errata #19–#24 parts the THT board's columns use ~96 % of their height
at a 1.6 mm part gap (3.5 mm channels; the placer stacks short parts beside tall
ones and moves width between columns until none overflows; the gap went 1.2 → 1.6
when the footprint keepouts made the gaps the routing channels) — 190 × 115 is now the right size for the THT build, and
the 155 × 90 board only fits with the SMD profile. Errata #9 still applies —
**measure the chassis**, set `BW, BH` in `gen_pcb.py`, regenerate, re-route.

## Power-section routing demo — DRC clean
`power_section_demo.kicad_pcb` (also from `gen_pcb.py`) routes the +33V5 (2.5 mm)
and +17V (1.5 mm) rails by hand over a GND pour as a net-class width reference:
`kicad-cli pcb drc` → 0 violations, 2 ratsnest lines left on purpose (`VRAW`,
`VREG_IN` — the latter needs a via to cross the +17V trunk).
