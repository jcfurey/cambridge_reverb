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
| Connections (ratsnest, incl. 28 test points, the dual-gang speed pot, the errata #20–#24 parts) | 226 |
| **Routed** | **218 / 226** (`unconnected_items`: 8) |
| DRC violations (`--severity-all`, JLCPCB limits, `.kicad_dru` rules, 155 footprint keepouts, edge / hole keepouts) | **0 errors, 0 rule hits**; 1 `track_dangling` warning (an escape stub end) |
| Track segments | 947 — F.Cu 1 706 mm, **In2.Cu 2 257 mm**, B.Cu 1 378 mm |
| Vias | 48 (+ 34 locked perimeter GND stitching vias) |
| Router settings | Freerouting 1.9.0, `-mp 150`, 3-layer DSN (In1 plane stripped), B.Cu cost ×1.2, via cost 50, class clearances HighCurrent 0.6 / HiZ 0.3 / TankDrive 0.8 mm (`route_board.py --bottom-cost 1.2 --via-cost 50 --passes 150`) |

The outer layers carry only escapes; the long runs are on In2 under the GND plane. The
eight open connections: `+33V5` ×2 (`C_byp2` ↔ an In2 run; the pin-5 stub end ↔ the
rail), `PA_BREF`, `PA_IN` (IC2 pin 7's In2 run ↔ `TP_PA_IN`), `QC` and `TREM_S` (the
vactrol to `Q_trem` / `C_dc_blk`, 40 mm across the tremolo zone), `VBIAS_T` (`R_vbt2`)
and `VOLTOP` (`POT_VOL` on the wiring edge). Eight GUI touches — on In2, where there is
room — listed so nobody trusts the copper blindly.

Honest note on the sweep: the 4-layer flow needed four fixes before it routed at all —
Freerouting ignores `active off` (7 m of copper on the planes), a `power`-typed plane
layer made it treat every through-hole pad as connected (adjacent same-net pins left
open), the first keepouts blocked the tiny link between a unity buffer's two pins, and
keepouts on *both* outer layers plus a 1.0 mm HighCurrent / 0.5 mm HiZ clearance left
33–73 links open. With the plane stripped from the DSN, keepouts on the component side
only, same-net pin gaps exempt and 0.6 / 0.3 / 0.8 mm class clearances: via cost 40 → 10
open, 50 → **8 (committed)**, 60 → 11, 70 → 12; the same placement without any footprint
keepouts → 21, so the keepouts now cost nothing. Evaluate candidates *in place* (next
to the `.kicad_pro` / `.kicad_dru`).

## Mixed SMD / THT variant — `smd/cambridge_reverb_smd.kicad_pcb` (170 × 100 mm)
Same schematic, second footprint profile (`--profile smd` on all three scripts). It was
sized for the **Part 7 155 × 90 "safe-bet" chassis** until errata #24: on four layers
with the footprint keepouts every SMD ground / rail pad needs a via beside it, and at
the 0.5 mm part gap that 155 × 90 forced there was room for none (30 of 52 open links
were exactly those). **170 × 100 mm, 1.0 mm gap** routes; it is still 20 mm shorter and
15 mm narrower than the 190 × 115 original, so any chassis that took the original takes
it. Set `BW, BH, GAP` back in `gen_pcb.py` if the measured chassis really is smaller,
and expect to finish the ground vias by hand. What moves to SMD and what deliberately
does not:

| SMD (90 parts) | Stays THT (and why) |
|----------------|---------------------|
| 53 × R → **0805** (thin-film for the 1 M gate/input resistors); `R_reg2` → 1206 (85 mW) | LM1875, LM317, KBP bridge, 5 W / 1 W resistors, `R_zobel`, the 0 Ω speaker link — power |
| ≤ 100 nF → **1206** (C0G/NP0 in the signal path, 100 V X7R snubbers) | **all electrolytics** — a radial can standing up uses *less* board than an SMD can |
| 120 nF MRB, 1 µF coupling, `C_zobel` → **1210** (X7R 50/100 V; PPS film on a 2220 pad if you prefer) | TL072 × 2 in **DIP-8 sockets**, the tone TL074 in a **DIP-14 socket** (availability audit: swappable) |
| 1N4007 → **SMA** (S1M); 1N4148 → **SOD-123** (1N4148W) | `R_s1`, `R_s2`, `R_rec2` — bench-trimmed per JFET (errata #15), swap an axial not an 0805 |
| MMBF5457 → **SOT-23** fitted directly (1 D / 2 S / 3 G, errata #18) — no TO-92 adapter | LED, vactrol, toroid, fuse clip, wire pads, test points |

Placement rules for this profile: 6 mm margin (corner M3 holes stay), 1.0 mm part
gap (1.5 mm body-to-body once the courtyards are counted; 0.4 → 0.5 → 1.0 as the
footprint keepouts made the gaps the routing channels and the ground vias needed room),
3 mm channels;
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
  pads on a 155×90 board (errata #11 addendum). Parts area **~5 300 mm² → 41 % of the 170 × 100 usable area** (54 % of the old 155 × 90)
(the THT-profile parts would be 68 %). **Pre-route DRC: 0 errors, 0 warnings** beyond the two stub warnings.

**Routing result (this commit; `kicad/reports/smd-drc.json`)** — `route_board.py --in kicad/smd/cambridge_reverb_smd.kicad_pcb --bottom-cost 1.2 --via-cost 40 --passes 150 --drop-planes top` (3-layer DSN, F.Cu pour hidden so every SMD ground pad gets a via; class clearances HighCurrent 0.4 / HiZ 0.25 / TankDrive 0.6 mm):

| Item | Result |
|------|-------:|
| Connections (incl. 28 test points, the dual-gang speed pot, tone stack, #21–#24 parts; SMD ground pads sit solid in the F.Cu pour) | 226 |
| **Routed** | **216 / 226** |
| DRC (`--severity-all`, JLC limits, rules, 147 footprint keepouts) | **1 error** — `starved_thermal` on `IC3` pin 11 on the In1 plane; 0 rule hits; 1 `track_dangling` warning (stub end) |
| Track segments | 1 041 — F.Cu 2 243 mm, **In2.Cu 1 699 mm**, B.Cu 792 mm |
| Vias | 124 (+ 27 locked perimeter GND stitching vias) |

The ten open items: the **power-amp cluster** — `PA_OUT` ×4 (`C_fb_hf` / `R_fb` / `D2`
and the pin-4 stub end to the In2 run; the 1.5 mm HighCurrent trace with its 0.4 mm
rule does not thread the 0805 feedback parts), `+33V5` (`R_bias1`), `+17V_PRE`
(`C_pre`, 25 mm), the **tank-drive cluster** — `TANK_IN` (a 39 mm In2 run to `R_drv3`),
`TKDRV`, `R_DRVO`, and `VBIAS_R` (`R_drv2`). Ten GUI touches; the PA cluster is one
short hand-routed 1.5 mm trace along D2 / C_fb_hf / R_fb.

Sweep on this placement (150 passes, in-place DRC): via cost 40 → **10 open + 1 thermal
(committed)**, 50 → 14, 70 (bottom ×1.0) → 12. Before the 1.2 mm gap and the smaller
rail vias (1.0 mm gap, 1.2 / 1.4 mm Power / HighCurrent vias) the same board gave
28–30 open, 30 of them rail / ground pads with no room for a via; at 155 × 90 / 0.5 mm
it gave 52. The SMD board is now 41 % parts by area and routes like the THT board.

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
