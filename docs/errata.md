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
(1.50 mm)** and assigns +33V5/+27V/+17V/GND/SPKR± all to Power. But the Part 4
pre-order checklist *and* `netlist-notes.txt` both call for **2.5 mm** on the
speaker / power-amp current path. The single 1.5 mm Power class can't satisfy
that. **Resolution:** add a third **HighCurrent (2.50 mm)** class for
`+33V5`, `SPKR+`, `SPKR-`, and the LM1875 output; keep **Power (1.50 mm)** for
`+27V`, `+17V`, `GND`. This three-class split is encoded in
`kicad/cambridge_reverb.kicad_pro`.
**Severity:** MEDIUM.

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
**Caveat:** only the *power-amp* SPICE netlist was recovered, so there is **no
preamp/recovery SPICE** to cross-check the bias point against. **Resolution:**
values are internally consistent; flag the missing preamp simulation for rebuild
(see `spice/README.md`). **Severity:** LOW.

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
