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
board during this work), and now and then it boxes a small pad in with its own traces
so that even `finish_routes.py` cannot reach it (2026-11-12: the bias divider's `+33V5`
pad behind a `PA_OUT` trace — one from-scratch run in three). `build.sh` therefore
routes again with the next via cost until KiCad's DRC counts no open connection, and
`verify.py` / `fab_jlcpcb.py` refuse anything less: the outcome is complete and clean
every time, the copper is not the same copper every time.

## Status — both boards fully routed, 0 DRC errors, 0 warnings (2026-11-12, errata #32–#36)

`kicad/gen/build.sh <smd|tht>` runs the whole chain; `kicad/gen/verify.py <profile>` is
the gate (`kicad/reports/verify-*.txt`: **75 / 75** checks on the SMD board, **66 / 66**
on the THT board). Numbers from `kicad-cli 8.0.9 pcb drc --severity-all`, reports in
`kicad/reports/`.

| | SMD / THT board (`smd/`, the JLCPCB one) | THT board |
|---|---:|---:|
| Outline | **170 × 105 mm** | 190 × 115 mm |
| Parts / nets / connections | 186 / 88 / 251 | 181 / 87 / 245 |
| Stack | F.Cu signal + pour / In1 GND / In2 signal / B.Cu GND | same |
| Ground nets | `GND` (planes) · `PGND` · `SPK_N`, joined by `R_spk_rtn` and `R_gnd` | same |
| Routed by Freerouting 1.9.0 (150 passes, 2 signal layers) | 241 | 236 |
| Closed by `finish_routes.py` | 10 | 9 |
| **Open connections** | **0** | **0** |
| DRC (JLCPCB limits, `.kicad_dru` rules, keepouts) | **0 errors, 0 warnings** | **0 errors, 0 warnings** |
| Track segments | 1 332 — F.Cu 2 765 mm, In2 2 543 mm, **B.Cu 0** | 1 458 — F.Cu 2 829 mm, In2 3 800 mm, **B.Cu 0** |
| Vias (all through) | 92 signal + 337 ground | 73 signal + 370 ground |
| Ground planes: openings over 5 mm (In1 / B.Cu) | 3 / 12, longest 10 / 15 mm | 3 / 13, longest 10 / 15 mm |
| Furthest point from a ground via | 13.3 mm (mean 3.2) | 13.2 mm (mean 3.5) |
| Ground-return hum at the speaker, idle (`reports/ground-*.md`) | **13 µV** (was 4.4 mV) | **31 µV** (was 7.4 mV) |
| LM1875 decoupling / Zobel from its pins | 20 / 15 mm (was 66 / 62) | 25 / 25 mm (was 71 / 62) |
| Lowest stray-capacitance corner | `TONE_OUT` 25 pF → 101 kHz | `TONE_OUT` 27 pF → 94 kHz |
| Footprint keepout areas | 149 | 154 |
| Worst crosstalk pair (`reports/crosstalk-*.md`) | `R_DRVO` → `SUMJ` −84 dB | `TKDRV` → `FS_MRB` −78 dB |
| Router settings | via cost 50 | via cost 60 |

### How the last links get closed — `gen/finish_routes.py`
Freerouting takes each net class as one width and one clearance, so on every run the
same two kinds of connection stay open:

- **signal-level branches of a power net** — `PA_OUT` to the feedback resistor `R_fb`,
  `+33V5` to the bias divider, the speaker return to the star link `R_gnd`. A 1.5 mm trace with its 0.4 / 0.6 mm rule does
  not fit between 0805 pads, although those branches carry microamps;
- **the tank drive** (`R_DRVO`, `TKDRV`, `TANK_IN`): its 0.6 / 0.8 mm spacing is only
  required from the tank *return* nets (the `.kicad_dru` rule), but the router has to
  keep it from everything.

`finish_routes.py` reads the open links from KiCad's own DRC and routes them with an A*
search on a 0.1 mm grid over the signal layers (F.Cu and In2), using the rules as written: per-pair
clearances exactly as the `.kicad_dru` states them, the footprint / edge / hole keepouts,
hole-to-hole spacing, no via on an SMD pad, none within 1 mm of a ground pin (the plane's
thermal spokes). A link attaches to the nearest point of the copper it has to reach.
Widths: the class width first; a rail link that cannot get through is tried at 0.8 mm
(narrower than an 0805 pad, so its end stays out of the keepout between the pads);
a link that only feeds a resistor, a small capacitor or a test point — and does not end
on one of the parts that carry the amps — may neck down to 0.5 mm. The script prints
every link with its length, width and the reason for a reduced width, and KiCad's DRC is
the judge afterwards. It routes the shortest links first — a local link needs the space
next to its pads, a long one can go round — and if any link finds no path it starts
again from the autorouted board with the failed links first. A signal net that cannot
get through at its class width is tried at 0.3 mm. On the committed SMD board it placed
11 links in one attempt: four on `PA_OUT` / `+33V5` at 0.8 mm (feedback network and bias
divider — 1 oz copper carries about 2 A at that width), one at the full 1.5 mm, the
three tank-drive nets and three other signal links at 0.5 mm. A link ends exactly on a pad's centre, or on the grid cell
that lies on a track's centre line; a last pass deletes any stub shorter than its own
width that KiCad reports as a dangling end, keeping the deletion only if nothing came
apart.

### Mixed SMD / THT variant — what is SMD and what is not
Same circuit, second footprint profile (`--profile smd` on every script). Since errata
#36 three values are built differently: `R_reg2` (2 × 1.5 k here, one 3 k on the THT
board), the 600 Hz MRB capacitor (3 × 22 nF here, one 68 nF film there), and this board
also has the `J_CHS` chassis pads and a `PGND` test point.

| SMD (101 footprints, 99 placed by JLCPCB) | Stays THT (and why) |
|----------------|---------------------|
| 56 × R → **0805** 1 % (one of them the 0 Ω star link `R_gnd`; `R_reg2` is 2 × 1.5 k, 42 mW each) | LM1875, LM317, KBP bridge, 5 W / 1 W resistors, `R_zobel`, the 0 Ω speaker link — power |
| ceramic C → **0805** where JLCPCB keeps the part as a basic one (C0G 33 pF / 100 pF / 2.2 nF, 100 V X7R 100 nF: 15 parts), else **1206** (22 nF and 100 nF C0G, 1 µF X7R: 24 footprints) — `gen/jlc_parts.py`, errata #36 | **all electrolytics** — a radial can standing up uses *less* board than an SMD can |
| 1N4007 → **SMA** (M7) | TL072 × 2 in **DIP-8 sockets**, the tone TL074 in a **DIP-14 socket** (swappable) |
| MMBF5457 → **SOT-23** fitted directly (1 D / 2 S / 3 G, errata #18); 2N3904 → MMBT3904 on the E-B-C-renumbered SOT-23 | `R_s1`, `R_s2`, `R_rec2` — bench-trimmed per JFET (errata #15), swap an axial not an 0805 |
| `C_mrb_450`, `C_mrb_750`: footprints only (DNP) | LEDs, vactrol, toroid, fuse clip, wire pads, test points; the bright cap `C_treble` (a voicing part — and JLCPCB has no basic C0G of its value) |

Placement: 6 mm margin, 1.2 mm part gap, the input-jack pads down the **left edge**
(shortest input wiring, their labels beside them), everything else on the bottom edge
with `JP_BR` and `T1` at the far right. SMD ground pads sit solid in the top pour and
each has its own via to the two planes. Net-class widths on this board: HighCurrent
1.5 mm, Power 0.5 mm, HiZ 0.3 mm, Default 0.5 mm.

**Assembly path:** JLCPCB places the 99 SMD parts; you solder 37 through-hole parts and
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

**Grounding — `R_gnd`, `R_spk_rtn`, `J_CHS` (errata #32).** Both 0 Ω links are
required: `R_spk_rtn` (a bare 1 mm wire link or a 0 Ω 1 W jumper, hand-soldered on both
boards) carries the speaker return to power ground, `R_gnd` (0805 0 Ω placed by JLCPCB;
a wire link on the THT board) is the one link from there to the planes. Do not add
ground links anywhere else. `J_CHS` (SMD board) is for a chassis wire when the input
jacks are insulated from the panel; with ordinary jacks leave it empty.

**Bright cap — `C_treble` (errata #36).** Hand-fitted on both boards: 470 pF C0G or
silver mica is the stock Vox value; 100 pF–1 nF to taste, or none.

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
28 labelled test points (29 on the SMD board: `PGND`) (`TP_*` in the schematic/BOM; footprint
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
| `+17V` | TP_17V | +17V | PSU | 17.0 V typical, 16.4–17.7 V (R_reg2 = 3.0 k) | Part 3, errata #34 |
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
| `PGND` | TP_PGND | PGND | Power amp (SMD board; on the THT board use the T1 `CT` pad) | **0 Ω to `GND` with the power off** (through `R_spk_rtn` + `R_gnd`); under power a few mV of pulses against `GND` — that is the drop the star keeps out of the planes | errata #32 |

Bring-up order (Part 5): rails (`VRAW`/`+33V5`/`VREG`/`+17V`) with the series
light bulb → `PA_B`/`PA_OUT`/`SPK` DC with no signal → JFET drains (`Q1D`,
`Q2D`, `QRD`) and trim → `VB_R`/`VB_T` → signal generator into IN1, follow
`PRE` → `TMK` → `TONE` → `BLEND` → `TREM` → `MRB` → `PA_IN` → `SPK`.

## Four layers, keepouts and rules by impedance (errata #24, 2026-09-08; ground system errata #31, 2026-11-11)

**Stack** (both boards, JLCPCB JLC04161H-7628, 1.6 mm — dimensions from JLCPCB's
impedance page: 35 µm copper / 0.2104 mm 7628 prepreg, εr 4.4 / 15 µm / 1.065 mm core /
15 µm / 0.2104 mm prepreg / 35 µm):

| Layer | Role | Its reference |
|---|---|---|
| `F.Cu` | components, signal traces, ground pour between them | `In1`, 0.21 mm below |
| `In1.Cu` | **solid ground plane** | — |
| `In2.Cu` | signal traces — the long runs, buried between the two planes | `B.Cu`, 0.21 mm below (`In1` is 1.07 mm above) |
| `B.Cu` | **solid ground plane**, solder side of the through-hole parts | — |

Nothing is routed on a plane, and no two signal layers face each other without a plane
between. Until errata #31 B.Cu carried traces and In2's only close neighbour was the
pour those traces left.

**The ground system** (generated by `gen_pcb.py` and `stitch.py`, measured by
`rf_audit.py` → `reports/rf-*.md`, enforced by `verify.py`):

- *Plane openings follow the holes.* Plane clearance is 0.2 mm to copper and 0.35 mm to
  a hole, and unused pad copper is removed from the inner layers (a pad or via keeps a
  ring only on a layer where something connects to it). The opening round a foreign pin
  is then hole + 0.7 mm instead of pad + 1.0 mm, and a 1.0 mm web of plane survives
  between the pins of a DIP. What is left over 5 mm: on In1 the footswitch and tank pad
  rows (their ground pads' thermal reliefs join the neighbours' openings — the pad and
  its spokes still bridge them) and the LM1875's 1.7 mm pin row; on B.Cu, where the pads
  are needed for soldering, the rows of 2.0 mm wiring pads along the board edge.
- *Top pour:* 0.5 mm from every trace — more than twice the 0.21 mm to the plane, so the
  plane sets a trace's capacitance and the pour adds about a tenth — and 1.0 mm from the
  HiZ class. No sliver under 0.4 mm. Pieces with no via to the planes are removed by the
  fill, so there is no floating copper.
- *Edge:* all copper 0.5 mm back from the outline; traces 2 mm back; a ground via fence
  every 5 mm, 2.5 mm in.
- *Stitching:* a via beside every SMD ground pad (placed and locked before routing),
  then ground vias on a 7.5 mm grid wherever one fits on every layer and stays 1 mm
  clear of every pad — most of those pads are soldered by hand.
- *Through-hole ground pins* connect to In1 with thermal reliefs and to nothing else;
  the bottom plane makes no pad connections, so the solder side of a ground pin is an
  ordinary pad.
- *Fills use the project's rules.* Every script fills through `route_board.refill()`,
  which initialises pcbnew's rule engine first; without that a scripted fill honours
  only each zone's own clearance (errata #31). `gen_pcb.py` does it in a fresh
  interpreter (`refill_file()`): filled inside the placement process, the filler
  intermittently logged coordinate-overflow assertions and crashed (2026-11-12).

**Stray capacitance.** `rf_audit.py` sums, for each sensitive net, the trace over its
plane (microstrip on F.Cu, offset stripline on In2), its pads and its vias, and gives
the corner frequency against that node's impedance. On the SMD board the largest is the
volume-pot wiper `TONE_OUT`, 21 pF against 62 kΩ: 121 kHz. Everything else is higher.
The one place a few pF matter is a feedback node — the reverb summer's `SUMJ` — and it
has `C_mixfb` (errata #31).

**No routes through footprints.** For every real part (not test points, fiducials or
holes) the generator writes rule areas named `kp_<ref>` — tracks disallowed on the
component side, vias too under SMD parts — over the space *between* the part's pads: the strips between the pins of
a row and the body between two rows, across the full courtyard. Any pad is still
reachable from outside its footprint; nothing runs between the legs of a resistor, under
a DIP, or through the toroid. Power-only parts (every pad on a rail / GND / speaker net)
are exempt — a rail trace under the bridge or a filter can is not the noise path this is
for, and the 1.5 mm rail traces need the room. 153 areas on the THT board, 145 on the SMD
board; Freerouting gets them as Specctra keepouts, KiCad DRC checks them (`keepout` test).

**Net classes and rules.** Widths / class clearances from the `.kicad_pro`; the
`.kicad_dru` rules bind tracks and vias only (fixed pad geometry such as the LM1875's
1.7 mm pin row is exempt) and `route_board.py` hands the router the same numbers as
per-class clearances so the result is rule-clean. 153 / 145 keepout areas (THT / SMD).

| Class | Nets | Width THT / SMD | Class clearance | Rules (THT / SMD) |
|---|---|---:|---:|---|
| `HiZ` | JFET gates and the RF nodes ahead of them (GUITAR_IN, RF1, Q1G, Q2G, RF2, QRG, TANK_OUT), tone ladder + wipers (JA/JB/JWB/JTA/JTB/JWT/JOUT, TONE_OUT), DRVP, OBUF_IN, LFO timing (WN1, LFO_P), MRB_T, PA_BIAS, WET/REVWCW | 0.3 / 0.3 | 0.3 / 0.25 | HighCurrent ≥ **0.6 / 0.4 mm** |
| `Default` (low-Z signal) | op-amp outputs, drains, everything else | 0.5 / 0.5 | 0.2 / 0.2 | HighCurrent ≥ **0.6 / 0.4 mm** |
| `Power` | +17V, +17V_PRE, VREG_IN, GND | 1.0 / 0.5 | 0.3 / 0.25 | separation from HiZ = the class clearance + the 0.21 mm plane geometry |
| `HighCurrent` | PA_OUT, ZOB, SPK_P/N, +33V5, VRAW, AC1, AC2, BR_NEG, **PGND** | 1.5 / 1.5 | 0.3 / 0.25 | see HiZ / Default rows (1 oz copper carries ~2.5 A at 1.5 mm; the amp peaks at 1.7 A) |
| `TankDrive` | R_DRVO, TKDRV, TANK_IN | 0.5 / 0.5 | 0.2 / 0.2 | ≥ **0.8 / 0.6 mm** from TANK_OUT / RF2 / QRG / WET / DRVP |

Origin: `kicad/gen/crosstalk_audit.py` (Part 6c §4) on the two-layer routing found the
reverb drive 0.3 mm from the reverb return (−37 dB) and PA_OUT 0.25 mm from the recovery
gate; the 2-layer rules (0.6 / 1.2 mm) got the worst pair to −50 dB at the price of open
links. A first 4-layer set (HighCurrent 1.0 mm, HiZ 0.5 mm, 2.5 mm rails) left ~70 links
open: a 0.5 mm HiZ clearance cannot enter a DIP pin between its 2.54 mm neighbours, and a
2.5 mm rail with 1.0 mm on each side does not fit the 1.6 mm gaps between parts once
nothing may run under them — so the numbers above are the ones the geometry allows, and
power-only parts (bridge, filter cans, clamp diodes, transformer / speaker pads) are
exempt from the keepouts. On the current copper (`kicad/reports/crosstalk-{tht,smd}.md`,
h = 0.21 mm, and since errata #31 with the tank driver's own output `R_DRVO` / `TKDRV`
counted as aggressors, not just `TANK_IN`): SMD worst pair `R_DRVO` → `SUMJ`
**−84 dB**; THT worst pair `TKDRV` → `FS_MRB` **−78 dB** (re-routed 2026-11-12; the 2026-11-11 copper had −61 / −75 dB).
The two-layer boards started at −37 dB. The earlier four-layer figures (−66 / −74 dB)
left out the driver output, and assumed a plane between In2 and B.Cu that was not
there.

## Return currents: the star ground (errata #32, 2026-11-12)

`rf_audit.py` asks whether the ground is one ground at radio frequency. `ground_audit.py`
asks the opposite question, at 100 Hz: **what flows in it, and what does that cost?** It
rasterises the routed ground copper of every layer (0.25 mm cells), joins the layers
through every via, and solves the resistor network for each current loop; the voltage it
finds between the two ground references of a stage is multiplied by that stage's gain to
the speaker. The pulse spectrum comes from a small time-domain rectifier model (0.7 A
peaks at idle, 3 A at full power).

| | 2026-11-11 copper (one ground net) | now |
|---|---:|---:|
| Buzz at the speaker at idle, SMD / THT | 4.4 / 7.4 mV | **13 / 31 µV** |
| … with `C_s1` / `C_s2` fitted | 6.9 / 23.9 mV | 22 / 82 µV |
| Speaker current fed back through the ground, loop gain | -49 / -42 dB | none: it does not enter the planes |

Picture: `docs/ground-return-before-after.png`.

How: the planes are **signal ground only**. `PGND` — transformer centre tap, `JP_BR`,
reservoir negative, the bridge snubbers to ground, LM1875 pin 3 with `C_byp1`, `C_byp2`,
`C_zobel` and `D2` — is a routed net of 1.5 mm traces; `SPK_N` is the speaker's return
pad. `R_spk_rtn` links `SPK_N` to `PGND`, and **`R_gnd` links `SPK_N` to the planes**:
the planes are referenced to the loudspeaker's own "−" terminal, and since the link
carries no load current no drop on the power ground is in series with the signal. The
star is a property of the netlist — three nets and two links — so it survives any
re-route. What still returns through the planes is the regulator's supply current and
the half-milliamp of ripple current of its pre-filter (`C_filt1` / `C_filt2`): that is
the residual in the table.

The same pass moved the parts that belong AT an IC next to it (`gen_pcb.CLOSE`,
`NEAR_BY_PROFILE`): LM1875 decoupling and Zobel, on the SMD board also its feedback and
input-filter parts, the LM317's set resistor and capacitors, the reverb op-amp's
feedback network, and the JFET rail filter `R_pre` / `C_pre` (to the preamp).
Limits: a DC sheet model with simulated gains — good for comparing layouts and for an
order of magnitude; transformer stray field and chassis loops are outside it.

## What the autorouter does NOT know — review by hand before fab
- **Audio layout.** It routes by cost, not by ear: the JFET gate inputs
  (`GUITAR_IN`, `Q1G`/`Q2G`), the reverb recovery input (`TANK_OUT`) and the LFO
  timing nodes may run next to `+33V5`/`PA_OUT`. Move or reroute them; keep the
  tremolo `LFO_*` nets short (Part 5 keep-out: no traces under the LFO timing parts).
- **Grounding.** Ground is two solid planes and a stitched pour, not a star: the
  power-amp, speaker and rectifier return currents flow in the planes, and whatever
  voltage they drop there is shared by everything referenced to the same stretch. The
  two planes together are about 0.35 mΩ per square, so the rectifier's charging pulses
  (several amps peak) put a few tenths of a millivolt between the `CT` pad and
  `C_main`'s negative pin, and some fraction of that between other points nearby. The
  layout keeps the PSU and the power amp at the far end from the input, but nothing has
  been measured. If there is a 100 / 120 Hz buzz on the bench, the first experiment is
  Part 3's: solder the transformer centre tap and the speaker return (`LS1 −`) straight
  to `C_main`'s negative pin with their own wires, so those currents never enter the
  plane.
- **HighCurrent loop.** The 2.5 mm `+33V5` / `PA_OUT` / `SPK_P` traces are correct
  in width but the router may loop them around the power-amp column; tighten them.
- **If you edit the copper by hand:** keep the bottom layer free of traces, refill the
  zones in the editor (not in a script, unless through `route_board.refill()`), and run
  `kicad/gen/verify.py` — its RF group re-measures the planes.
- **Inner copper.** The wide rail and output traces partly run on In2 (0.5 oz at
  JLCPCB by default): 1.5 mm there is good for about 1 A RMS at a 10 K rise, which
  covers this amplifier (0.55 A average at full power). Order 1 oz inner copper if you
  want the margin.
- **It is a ground system, not an impedance-controlled board.** No trace here is a
  transmission line below a gigahertz and none is laid out as one.

## Why the LM1875 has pre-routed stubs
The TO-220-5 pins are on a **1.70 mm pitch**. With the 0.3 mm HighCurrent/Power
clearance, no trace wider than ~1.35 mm can enter pins 3, 4 or 5 past their
neighbours, so the 2.5 mm `PA_OUT` / `+33V5` traces are physically unroutable to
the pin — every autorouter run left exactly those two connections open. A hand
layout necks the trace down at the pin; `gen_pcb.py` does the same with three
**locked 0.9 mm stubs** (pin 4 straight down 6 mm, pin 5 fanned 5 mm right and down,
and — since pin 3 is on the routed power ground, errata #32 — pin 3 straight down 6 mm
on the inner signal layer).
Locked tracks export as `(type fix)`, so the router keeps them and attaches the
full-width trace at their ends. 0.9 mm × 3.5 mm of 1 oz copper at ~1.7 A peak is
a non-issue thermally.

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
