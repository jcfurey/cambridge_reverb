# Vox Cambridge Reverb — Errata & Sanity Check

> Reconstructed document — see `PROVENANCE.md`. The original errata listed 17
> cross-document inconsistencies. Issues 1–8 below are recovered substantially
> verbatim. Issues 9–17 were **not** recovered verbatim; they were re-derived by
> a fresh consistency pass on 2026-06-14 (the resolutions are newly authored, the
> reconciled values are recovered). The three HIGH-severity items (Issues 4, 7,
> and the JFET/MRB items) are folded into the relevant reconstructed docs.

## Issue 1 — Part 1 referenced external FX-loop / headphone jacks
The user keeps the original panel with no new holes. FX loop must be internal-only
(IN3 repurposing); headphone output removed; MRB internal-only.
**Severity:** MEDIUM. *(Folded into Part 1 §7.)*

## Issue 2 — Part 1 key-improvements list mentioned external features
Change to: internal FX-loop provision (IN3), on-board tremolo rate LED
(diagnostic, not panel), remove headphone output.
**Severity:** LOW.

## Issue 3 — Bridge rectifier naming (KBU4M vs KBP410G)
Both are 4A/1000V; different packages (KBP410 inline 4-pin, KBU4M SIP 4-pin).
PCB footprint should accommodate both. Part 8 prefers KBP410G for availability.
**Severity:** LOW.

**Update (2026-09-06):** the board now carries a real, datasheet-derived
**KBP footprint** (`cambridge_reverb:Bridge_KBP_P3.81mm`, from Diodes DS39310
KBP404G–KBP410G: 3.81 mm pitch, 0.86 × 0.55 mm leads → 1.2 mm drill, 14.5 × 3.5 mm
body, pins **+ ~ ~ −** as marked). The schematic bridge symbol was renumbered to
that physical order (pin 1 = +, 2 = ~, 3 = ~, 4 = −) so pad and pin numbers agree.
One footprint **cannot** accommodate both parts: KBU is 5.08 mm pitch, and
overlapping the two hole patterns would put holes 1.27 mm apart (violates the
0.25 mm hole-to-hole rule). To build with a KBU4M instead, swap the `BRIDGE`
footprint in `kicad/gen/gen_kicad.py` for a 5.08 mm-pitch one and regenerate.

## Issue 4 — Part 2 listed 2N5457 TO-92 (discontinued) — HIGH
Through-hole 2N5457 is discontinued; the Mouser P/N would show no stock. Primary
options are MMBF5457 on adapter or J113; keep 2N5457 only "if you find genuine."
**Severity:** HIGH. *(Folded into Parts 1, 2, 8.)*

## Issue 5 — Part 1 listed TIP41C/TIP42C discrete output as an option
The rest of the suite assumes the LM1875 as the sole power amp. Clarify the
discrete stage is reference-only, not developed (no BOM/SPICE/wiring).
**Severity:** MEDIUM. *(Folded into Part 1 §3.)*

## Issue 6 — Part 1 mentioned LM13700 OTA tremolo modulator
No BOM/SPICE/wiring exists for it; LED/LDR (VTL5C1) is used throughout. Note as
an undocumented advanced alternative.
**Severity:** LOW.

## Issue 7 — Part 2 said 2200µF output cap was "only for discrete output" — HIGH
The LM1875 in single-supply mode ALSO requires the 2200µF output coupling cap.
Remove the qualifier.
**Severity:** HIGH. *(Folded into Part 2 BOM + Part 1 §3.)*

## Issue 8 — Part 1 §6 described MRB with a panel rotary switch
Implies a new panel control. Default is hardwired 600 Hz; any selector is
internal-only (inside chassis or repurposing the line-reverse switch).
**Severity:** MEDIUM. *(Folded into Part 1 §6.)*

## Issues 9–17 — consistency pass (2026-06-14)

The original Issues 9–17 were not recovered verbatim. Rather than leave them as
a stub, the topics flagged in the project record were re-derived by a fresh
cross-document consistency pass over the *reconstructed* docs, the BOM, the
SPICE netlist, and `kicad/netlist-notes.txt`. These resolutions are **newly
authored** (not recovered originals); the underlying values they reconcile are
recovered. Re-verify before fabrication.

## Issue 9 — Board dimensions: 190×115 vs 155×90 mm
Part 4 (and the Part 5 floor plan) use **190 × 115 mm** to match the original
25-5274-2 footprint; Part 7 recommends **155 × 90 mm** as a measure-first "safe
bet." These are not contradictory — the outline is a measurement-gated decision
point, not a fixed value. **Resolution:** measure the chassis (Part 7 procedure),
then set `Edge.Cuts` to the largest size your measured chassis supports; default
to 155×90 only if you cannot measure. Both numbers are intentionally retained.
**Severity:** MEDIUM (decision point — must be closed before the PCB outline is final).

## Issue 10 — 17 V rail: LM317 set resistors yield 16.9 V, below the stated 17.0–17.5 V band — re-verify
Part 2 specifies `R_reg1 = 240 Ω`, `R_reg2 = 3.0 kΩ`. With the LM317
(`Vout = 1.25 × (1 + R_reg2/R_reg1)`, I_adj negligible) this gives
**1.25 × (1 + 3000/240) = 16.88 V** — about 0.13 V *below* the 17.0–17.5 V
window quoted in Part 2 §setup and the Part 3 troubleshooting table.
**Resolution:** either (a) accept ~16.9 V and widen the stated window to
**16.8–17.5 V**, or (b) to actually land in 17.0–17.5 V, use `R_reg2 ≈ 3.09 kΩ`
(E96 → 17.34 V) or 3.01–3.07 kΩ. Recommended: **R_reg2 = 3.09 kΩ (E96)**.
**Severity:** MEDIUM.

## Issue 11 — Net-class table is missing a high-current (speaker/PA) class
Part 4's net-class table defines only **Default (0.30 mm)** and **Power
(1.50 mm)** and assigns +33V5/VREG_IN/+17V/GND/SPK_P/SPK_N all to Power. But the Part 4
pre-order checklist *and* `netlist-notes.txt` both call for **2.5 mm** on the
speaker / power-amp current path. The single 1.5 mm Power class can't satisfy
that. **Resolution:** add a third **HighCurrent (2.50 mm)** class for
`+33V5`, `SPKR+`, `SPKR-`, and the LM1875 output; keep **Power (1.50 mm)** for
`VREG_IN`, `+17V`, `GND`. This three-class split is encoded in
`kicad/cambridge_reverb.kicad_pro`.
**Severity:** MEDIUM.

**Update (2026-09-06):** `VRAW` (bridge output → fuse → `C_main`) and the
transformer secondary nets `AC1`/`AC2` carry the same current as `+33V5` (more,
as RMS: rectifier charging pulses) but had fallen into the 0.5 mm Default class.
They are now in **HighCurrent** too (`.kicad_pro` pattern list).

**Addendum (SMD variant, 2026-09-06):** `kicad/smd/cambridge_reverb_smd.kicad_pro`
uses **HighCurrent 2.0 mm / Power 1.0 mm** (0.25 mm clearance) instead of 2.5 / 1.5.
The wider classes were sized for the 190×115 THT board; on the 155×90 mixed-SMD
board they cannot pass between 0805/1206 pads and starved the router. Electrically
2.0 / 1.0 mm on 1 oz copper carry several amps — ample for ~1.7 A peak / <1 A RMS.

## Issue 12 — Via-drill specs disagree between Part 4 and netlist-notes
Part 4 design rules give min via drill **0.3 mm** and a Power-class via drill of
**0.5 mm**; `netlist-notes.txt` instead says **signal vias 0.5 mm**, **power
vias 1.0 mm**, **ground-stitch 0.8 mm**. **Resolution** (reconciled, encoded in
the `.kicad_pro`): Default via **0.4 mm drill / 0.8 mm dia**; Power via
**0.8 mm drill / 1.4 mm dia**; HighCurrent via **1.0 mm drill / 1.6 mm dia**;
ground-stitch vias **0.8 mm**. All are ≥ JLCPCB minimums and surcharge-free.
**Severity:** LOW.

## Issue 13 — Signal trace width: 0.30 mm (net class) vs 0.50 mm (netlist-notes)
Part 4's Default net class is 0.30 mm; `netlist-notes.txt` suggests 0.50 mm for
signal. Both pass DRC and exceed JLCPCB's 0.127 mm minimum. **Resolution:** adopt
**0.50 mm** as the working signal default for hand-assembly robustness (more
copper, easier rework); the net-class minimum stays 0.30 mm so tight spots are
still legal. Encoded in the `.kicad_pro` Default class.
**Severity:** LOW.

## Issue 14 — Reverb-pan part number consistency — confirmed, no action
Cross-checked Part 1 §4, Part 9, and `bom/bom.csv`: all specify the
high-impedance **Accutronics 4FB2A1C (~1475 Ω)** and all explicitly flag the
8 Ω-input **4AB3C1B as incompatible** with the direct TL072 driver. Consistent
across every document. **No change required.**
**Severity:** NONE (verified consistent).

## Issue 15 — JFET bias values across Part 2 and netlist-notes — consistent; preamp SPICE absent
Part 2's preamp self-bias (`R_g = 1 MΩ`, `R_d ≈ 10 kΩ`, `R_s ≈ 2.2 kΩ`,
`C_s = 10 µF`) matches the reverb-recovery JFET in `netlist-notes.txt`
(`R_rec_bias = 1 MΩ`, `R_rec1 = 10 kΩ`, `R_rec2 = 2.2 kΩ`, `C_rec_byp = 10 µF`).
**Caveat:** only the *power-amp* SPICE netlist was recovered, so there was no
preamp/recovery SPICE to cross-check the bias point against.

**Update (ngspice, 2026-06-14):** a preamp sim now exists
(`spice/dc_preamp_jfet.cir`). With a nominal 2N5457 (Idss ≈ 3 mA, Vp ≈ −1.8 V),
the recovered `R_s ≈ 2.2 kΩ` / `R_d = 10 kΩ` bias the **drain at ~12 V**
(Id ≈ 0.49 mA) — *colder* than the 8–9 V target in Part 2/Part 3. Simulated fix:
**R_s ≈ 1.0 kΩ → Vd ≈ 8.5 V**, **R_s ≈ 1.2 kΩ → Vd ≈ 9.5 V**. The 2N5457 has a
wide Idss/Vp spread, so treat R_s ≈ 1–1.2 kΩ as the nominal and **trim per device
on the bench**. The BOM keeps the recovered 2.2 kΩ with this note.
**Severity:** LOW (bias trim) — but verify before relying on the stated 8–9 V.

## Issue 16 — Main filter cap: 4700 µF (Part 2) vs 2× 2200 µF split (Part 7)
Part 2's BOM gives **C_main = 4700 µF/50 V**; Part 7 notes the original ~5000 µF
cap was chassis-mounted and suggests **2× 2200 µF side-by-side** *only if* you
PCB-mount it and vertical clearance to the control panel is tight. Not a conflict
— 4700 µF is canonical; the 2× 2200 µF is a mechanical fallback. **Resolution:**
BOM keeps 4700 µF; clearance check in Part 7 decides whether the split is needed.
**Severity:** LOW.

## Issue 17 — "Bypass on each supply pin" wording vs single-supply reality
Part 1 §3 says "100 nF + 10 µF on **each** supply pin." In the single-supply
LM1875 design, V− (pin 3) **is** ground, so the bypass pair lands on **V+ (pin 5)
only**, exactly as Part 2 and the netlist show (`C_byp1`, `C_byp2` on pin 5 → GND).
**Resolution:** read "each supply pin" as "the V+ supply pin"; no extra parts.
**Severity:** LOW (wording).

## Issue 18 — JFET symbol pin numbers did not match the TO-92 / SOT-23 parts (2026-09-06) — HIGH
The generated schematic's JFET symbol numbered its pins **1 = Drain, 2 = Gate,
3 = Source**, and the board used the stock `TO-92_Inline` footprint with pads 1-2-3
in a row. The onsemi datasheets for **both** specified parts number the leads
**1 = Drain, 2 = Source, 3 = Gate** — 2N5457/J113 (TO-92, straight-lead) and
MMBF5457 (SOT-23) alike — so a real part fitted to the old board would have had
its gate on the source pad and vice-versa (Q1, Q2, Q_rec). ERC/DRC cannot see
this; it was caught while adding the SOT-23 footprint for the mixed-SMD variant.
**Resolution:** symbol renumbered to 1 = D, 2 = S, 3 = G; all three JFET net maps
updated; both boards regenerated. If you populate the THT board with a SOT-23 on a
TO-92 adapter, wire the adapter D-S-G to pads 1-2-3.
**Severity:** HIGH (silent wiring fault) — fixed in the generator; verify against
the datasheet of whatever JFET you actually buy (J113: also D-S-G).

## Issue 19 — The tremolo LFO as recovered cannot run at tremolo rates (2026-09-07) — HIGH
The recovered Wien-bridge LFO put the speed pot in **one** arm only: series arm
`R_lfo_ser` 10 k + `POT_SPD` 0–500 k with `C_lfo1` 100 nF, shunt arm a fixed
`R_lfo1` 33 k with `C_lfo2` 100 nF, amplifier gain 1 + 10 k/4.7 k = 3.13. For an
asymmetric Wien network the loop only starts when gain > 2 + R1/R2, i.e. while the
series arm stays under ~37 k — the bottom **5 %** of the pot — and there it runs at
**45–80 Hz** (f₀ = 1/(2π√(R1R2)C)). Everywhere else it does not oscillate at all.
Part 2's "~1 Hz to ~10 Hz" was never reachable with those values. Swept and shown
in `spice/sweep_lfo_speed_recovered.cir` (results in `spice/results/`).
**Resolution:** symmetric network with a **dual-gang 250 k lin speed pot**, one gang
in each arm, `R_lfo_ser` = `R_lfo_sh` = 15 k floors, `C_lfo1` = `C_lfo2` = **1 µF**.
The attenuation is then exactly 1/3 at every setting, the existing gain-3.13 /
diode-limited amplifier starts everywhere, and f = 1/(2π(15 k + pot)·1 µF) =
**10.6 Hz (fast) … 0.60 Hz (slow)** at constant 0.96 Vpp
(`spice/sweep_lfo_speed.cir`). The dual-gang pot goes in the original speed-pot
hole (no new holes); the original single pot is no longer reused. Alternative if
you insist on the single pot: a one-op-amp Schmitt relaxation LFO — square/
exponential waveform, harder tremolo; not adopted. `POT_SPD_A`/`POT_SPD_B` in the
schematic and BOM are the two gangs of **one** part.
**Severity:** HIGH (the effect did not work as drawn) — fixed in the generator;
both boards regenerated and re-routed.

## Issue 20 — Tone: the single "cut" pot did not match the panel, and the recovered coupling had no bass (2026-09-07) — HIGH
Two problems in the tone sheet, one recovered and one designed. **(a)** The
recovered preamp coupled Q2's drain to the tone/volume network through
`C_treble` **470 pF alone** — into the ~250 k volume pot that is a **1.3 kHz
high-pass**: no bass or low-mids at all reached the reverb, tremolo or power amp.
`C_treble` is the Vox "chime" cap; it belongs *across the top of the volume pot*
as a bright cap, not in series as the only coupling. **(b)** The Cambridge Reverb's
panel has **Bass and Treble** pots, but the designed substitute (cross-check §4)
was a Volume + single treble "cut" pot: the Bass hole had nothing to drive.
**Resolution (built design, `kicad/gen/gen_kicad.py` tone sheet):**
- `C_cpl_out` **1 µF** couples Q2D → `PREAMP_OUT` (flat to ~16 Hz into the 1 M
  bias resistor); `C_treble` 470 pF moves across the top half of the volume pot
  (bright cap: treble lift at low volume, transparent at full).
- A **passive James (Thomas-Vox style) Bass/Treble network** driven by a TL074
  buffer (`IC3`-A) and followed by a ×2 make-up stage (`IC3`-B) — the topology the
  originals used, deliberately **not** an active Baxandall: asymmetric, more cut
  than boost, a slight bright tilt at noon, both pots **250 k lin** in the original
  holes. `R_j1`/`R_j2` 10 k, `C_j1`/`C_j2` 22 nF, `R_j3` 68 k (bass ladder);
  `C_j3`/`C_j4` 2.2 nF, `R_j4` 1 k (treble ladder). Swept in
  `spice/sweep_tonestack.cir`: bass −7.5 … +4.9 dB @ 100 Hz, treble −16.5 … +5.6 dB
  @ 10 kHz, noon flat within 0.3 dB (`spice/results/`).
- A **switchable MID CUT** for honky pickups: `R_mid` 10 k then a series-resonant
  shunt to mid-rail — `C_res` 22 nF + a gyrator (`IC3`-C, `R_gL` 4.7 k, `C_gg`
  1.8 nF, `R_gg` 220 k → L = 1.86 H). **−9.6 dB at ~800 Hz, Q ≈ 0.6** (broad:
  −3 dB from ~400 Hz to ~1.7 kHz), flat within 0.05 dB when off. `SW_MID` is an
  SPST mini toggle in the **original line-reverse switch hole** (that position
  was reserved for "internal repurposing" in Issue 8 — no new holes). The switch
  sits on a node at mid-rail DC on both sides, so it does not pop.
- `IC3`-D buffers the result into the volume pot; `TONE_OUT` still feeds the
  summer, the tank driver and the FX send as before. `IC3` gets its own mid-rail
  (`VBIAS_3`, split-bias policy) and a DIP-14 socket; test points `TMK`
  (make-up output) and `VB_3` join the strip.
**Severity:** HIGH ((a) alone made the amp sound like a treble-only transistor
radio) — fixed in the generator; both boards regenerated and re-routed. The
"designed substitute" wording in cross-check §4 is superseded.

## Issue 21 — Hum and hiss: the LM1875 bias divider had no bypass, and the LM317's noise reached the JFETs (2026-09-07) — HIGH
Found by the first noise / hum models (`spice/ac_hum_psrr.cir`, `spice/noise_frontend.cir`,
Part 6c). **(a) Hum.** The power-amp input was biased by `R_bias1`/`R_bias2` (22 k/22 k
from +33V5) with the LM1875's + input sitting *on* the divider node and no bypass
capacitor: half the rail ripple went straight into the amplifier, ×23, to the speaker —
**+4 dB ripple-to-speaker, 0.4 Vrms of 100 Hz at idle (−28 dB below full power)**. Fix:
the textbook single-supply network — divider node bypassed by `C_bref` **100 µF**, then
`R_bias3` **22 k** into the + input (input impedance unchanged, LF corner 7 Hz with
`C_in_pa`): **−58 dB**, 0.3 mV. **(b) Hiss.** The LM317 puts out ~510 µV rms of noise
(TI: 0.003 % of V_out, 10 Hz–10 kHz) and the JFET common-source stages have ~0 dB PSRR,
so the regulator — not the JFETs — set the preamp noise floor, **23 dB above** the JFETs'
own: input-referred 37 µV rms, SNR 34 dB at 12 W. Fix: `C_adj` **10 µF** on the LM317 ADJ
pin (TI: ripple rejection 65 → 80 dB, noise ÷ ~10) and an RC-decoupled rail for the
three JFET stages, `R_pre` **100 Ω** + `C_pre` **220 µF** (`+17V_PRE`, 7 Hz corner) —
EIN 2.7 µV, SNR 57 dB, hum path B −95 dB. Four cheap parts. **Severity:** HIGH (the amp
would have hummed audibly at idle and hissed like a much worse design).

## Issue 22 — Tremolo had no depth: the vactrol LED ran at 7 mA DC (2026-09-07) — HIGH
`spice/tran_tremolo_depth.cir` (a behavioural VTL5C1 added to the errata #19 LFO) shows
the tremolo as drawn: the LFO output sits at the 8.5 V mid-rail with a ±0.5 V swing
(1N4148 limiter), and the vactrol LED was returned to **ground** through 1 k — so it
carried **6.4–7.4 mA DC**, the LDR sat at ~1 kΩ, and the "tremolo" was a permanent
**−19.5 dB pad with 1.7 dB of wobble**. The rate LED (2.2 k to ground) glowed steadily
for the same reason. Fix: the limiter diodes become two antiparallel **red LEDs** across
`R_lfo_fb1` (knee ~1.6 V → **2 V** LFO swing; `LED_rate` is one of them and now really
blinks; `LED_lim` is the other; `D_lfo1`/`D_lfo2`/`R_led_diag`/`R_led` are gone) and the
vactrol LED gets a driver: `Q_trem` (2N3904; MMBT3904 on the SMD board, on a SOT-23
footprint renumbered to the TO-92's E-B-C order) as an emitter follower, AC-coupled from
the depth pot by `C_drv` **100 µF** into a **180 k/10 k** base bias (~0.9 V, just below
conduction), `R_e` **470 Ω**, vactrol LED from +17 V via `R_c` **100 Ω** in the collector.
Result: LED 0…4.7 mA at the LFO rate, LDR 1.9 k…50 MΩ, **15 dB depth**, 0.8 dB insertion
loss. The LM317 sees ≤ 6 mA more at the LFO peak (Part 6c §5). **Severity:** HIGH (the
effect did not work); the depth pot and the footswitch tap are unchanged.

## Issue 23 — Fab rules: two footprints under JLCPCB's annular-ring minimum; assembly cost knobs (2026-09-07) — MEDIUM
Checking both boards against JLCPCB's published 2-layer limits (Part 4, updated): the stock
`TO-92_Inline` (1.05 mm pads on 0.75 mm holes) has a **0.15 mm** ring and the project's
LM1875 footprint (1.45 mm pads on 1.1 mm holes) **0.175 mm** — both under JLC's 0.18 mm
absolute minimum (0.25 recommended). Fixes: JFETs and the new `Q_trem` on
`TO-92_Inline_Wide` (2.54 mm pitch — which also matches the SOT-23→TO-92 adapters —
1.5 mm pads, 0.35 mm ring); LM1875 pads 1.5 × 2.6 mm (0.20 mm ring; the 1.7 mm pitch
cannot give 0.25 without a 1.0 mm drill that the 0.97 mm lead diagonal would not
survive — JLC's absolute minimum is met, the recommendation is not, and it is stated on
the footprint). Both `.kicad_pro` files now carry the JLC limits as DRC constraints
(hole-to-hole 0.5, hole-to-copper 0.3, annular 0.18, mask dam 0.1, silk 0.15 / 1.0 mm),
so the check is automatic. Cost: on the assembled SMD board the price is driven by
part **types** (an "extended" library part costs $3 per type per order) rather than
board area, so the 1210 capacitor line (an extended part) is folded into 1206, the two
optional MRB caps are marked **DNP** (not placed, not in the assembly BOM), and the
gyrator moves to E24 values (2.2 nF / 180 k, same 1.86 H): 31 → 29 lines, 7 → 3
extended types (`kicad/gen/jlc_cost.py`; the MMBF5457, the 3.09 k E96 set resistor and
the 68 nF MRB cap). Three fiducials were added for the
pick-and-place camera. **Severity:** MEDIUM (a fab would have flagged the rings or
produced breakouts; the rest is money).

## Issue 24 — Layout: traces threaded between component leads; no RF reference plane (2026-09-08) — MEDIUM (design change)
The two-layer boards routed the way two-layer boards do: signal traces between the legs of
resistors, under DIPs, beside the toroid, and the bottom "ground plane" was a pour
sliced by every jumper — the first crosstalk audit (Part 6c §4) put the reverb drive
0.3 mm from the reverb return and the power-amp output 0.25 mm from the recovery gate.
Resolution (`kicad/gen/gen_pcb.py`, `route_board.py`, both boards):
- **Four copper layers** (JLCPCB JLC04161H-7628, 1.6 mm): F.Cu signal — **In1 solid GND
  plane** — In2 inner signal layer — B.Cu signal with a GND pour. Every F.Cu / In2 trace
  now sits 0.21 mm from the GND plane instead of 1.5 mm: trace-to-trace coupling falls
  ~10× and the plane is a real RF/EMI reference and return. Perimeter **GND stitching
  vias** every 15 mm tie the B.Cu pour to the In1 plane (Part 4's rule, now generated).
  In2 was a +17 V plane in the first cut; with the keepouts below, two routing layers left
  33–43 links open on the THT board, so In2 routes signals (under the plane) and +17 V is
  a 1.0 mm Power trace — `IN2_PLANE = "+17V"` in `gen_pcb.py` restores the plane.
- **No routes through footprints.** For every real part the generator writes rule areas
  (no tracks / vias, F.Cu + B.Cu) over the space *between* its pads — the strips between
  the pins of a row and the body between two rows, across the full courtyard. A trace can
  reach any pad from outside; it can no longer pass between the legs of a resistor, under
  an IC, or through the MRB toroid. The router sees them as Specctra keepouts; KiCad DRC
  checks them.
- **Rules by impedance.** New `HiZ` net class (0.3 mm, 0.3 / 0.25 mm clearance) for the
  high-impedance nodes — JFET gates and the RF nodes ahead of them, the tank return, the
  tone ladder and wipers, the LFO timing nodes, the MRB tank, the LM1875 + input; `Power`
  (1.0 / 0.8 mm) for the rails, `HighCurrent` (1.5 mm — 1 oz copper carries ~2.5 A at that
  width, the amp peaks at 1.7 A; Part 4's 2.5 mm was sized for a two-layer board with no
  plane) for PA_OUT / ZOB / SPK / +33V5 / VRAW / AC; `Default` = low-impedance signal
  (op-amp outputs, drains). `.kicad_dru`: HighCurrent ≥ 0.6 mm from any signal trace,
  tank drive ≥ 0.8 mm from the return (SMD board: 0.4 / 0.6), tracks and vias only; the
  router is given the same numbers per class. On the 0.21 mm plane spacing, 0.6 mm
  couples like ~2 mm did on the two-layer boards; a wider first attempt (1.0 mm / 0.5 mm
  HiZ) left ~70 links open because a 0.5 mm clearance cannot enter a DIP pin between its
  neighbours.
- **RF stoppers** at the two antennas: `R_rf1` 1 k + `C_rf1` 100 pF at Q1's gate (guitar
  cable) and `R_rf2` 1 k + `C_rf2` 100 pF at the recovery JFET's gate (tank cable) —
  1.6 MHz corners, nothing at audio, 4 nV/√Hz against the pickup's own 10.
**Board size:** the SMD variant grows from Part 7's 155 × 90 to **170 × 100 mm** (1.0 mm
part gap): at 0.5 mm no ground / rail via fitted beside an SMD pad and 30 of 52 links
stayed open; 170 × 100 still fits any chassis the 190 × 115 original did (Issue 9).
**Cost:** a 4-layer 170 × 100 / 190 × 115 board is area-priced above JLC's $7 100 × 100 mm
tier (Part 4). **Severity:** MEDIUM — the two-layer boards worked on paper; this is the
layout a low-noise guitar amp should have.
