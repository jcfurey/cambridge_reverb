# BOM cross-check (2026-06-14)

Cross-checked `bom.csv` against the recovered component values in
`../docs/02-bom-schematics.md` (Part 2), `../kicad/netlist-notes.txt`, and
`../spice/power_amp_lm1875.cir`. Summary of what was found and what changed.

## 1. Power-amp chain agrees across all four sources — confirmed
The LM1875 values are identical in Part 2, the SPICE netlist, the netlist notes,
and the BOM:

| Value | Part 2 | SPICE `.cir` | netlist-notes | bom.csv |
|-------|:------:|:------------:|:-------------:|:-------:|
| R_bias1/2 22K | ✓ | ✓ | ✓ | ✓ |
| R_fb 22K | ✓ | ✓ | ✓ | ✓ |
| R_gain 1K | ✓ | ✓ | ✓ | ✓ |
| C_in 1µF | ✓ | ✓ | ✓ | ✓ |
| C_gain 22µF | ✓ | ✓ | ✓ | ✓ |
| C_out 2200µF | ✓ | ✓ | ✓ | ✓ |
| R_zobel 10R / C_zobel 100nF | ✓ | ✓ | ✓ | ✓ |
| Gain = 23× (27 dB) | ✓ | ✓ | ✓ | ✓ |

No action needed on the power amp.

## 2. BOM was missing most preamp / reverb / tremolo / MRB / panel parts — fixed
The previous `bom.csv` was effectively a **power-supply + power-amp + partial-
effects** list. Components that appear in Part 2 and/or `netlist-notes.txt` but
were absent from the BOM have now been **added** (each tagged with its source in
the `notes` column):

- **Preamp (×2 JFET stages):** `R_g1/2` 1M, `R_d1/2` 10K, `R_s1/2` 2K2,
  `C_s1/2` 10µF, `C_in_pre` 47nF.
- **Reverb:** `R_drv1` 100K, `R_drv2` 10K, `R_drv3` 10R, `C_rev1` 1µF,
  `C_rev2` 10nF, `C_rev4` 100nF, `R_rec_bias` 1M, `R_rec1` 10K, `R_rec2` 2K2,
  `C_rec_byp` 10µF, `POT_REV`.
- **Tremolo:** `R_lfo1` 33K, `R_lfo_ser` 100K, `R_lfo_fb1` 10K, `R_lfo_fb2` 4K7,
  `R_led_diag` 2K2, `C_dc_blk` 10µF, `C_trem_out` 100nF, `POT_SPD` 500K,
  `POT_DPT` 100K.
- **Effects loop / panel:** `R_fx_pad` 10K, `POT_VOL`, `POT_TONE`, `J_IN` (×3),
  `FS_DIN`.
- **Mechanical / safety:** `R_bleed` 10K/5W (filter-cap discharge, from the
  Part 1 safety note), `HS_LM1875`, `INS_MICA`, `SOCKET_IC` (×2), `STANDOFF`.

## 3. SPICE `.cir` was simplified vs the documented model — now addressed
The original (LTspice) power-amp netlist omitted things the docs describe. Rather
than only flag them, an **ngspice-runnable** companion set now exists and was
**executed to verify** the design (`../spice/`, run `./run_all.sh`). The recovered
LTspice `power_amp_lm1875.cir` is left verbatim for provenance; the new
`ac_power_amp_lm1875.cir` adds the missing pieces:

- **`C_fb_hf` (1 nF across R_fb)** — added; the sim now shows the HF −3 dB at
  **6.83 kHz** (≈ the documented 7.2 kHz), confirming the bandwidth limit. The
  original `.cir` had no HF element.
- **10″ speaker model** (Re + Le + 105 Hz mechanical resonance) replaces the plain
  8 Ω resistor.
- **Guitar pickup/cable model** (3 H / 6 kΩ / 100 pF + 300 pF) — still a documented
  rebuild item for a full source-to-speaker chain (noted in `../spice/README.md`).

The sims also surfaced two real findings (both folded into errata):
- **Power-amp LF −3 dB is ~17 Hz, not 7.2 Hz** — the input coupling/bias network
  adds a second LF pole the docs didn't count. Beneficial for guitar.
- **Preamp bias is cold with Rs = 2.2 kΩ** (Vd ≈ 12 V vs the 8–9 V target);
  **Rs ≈ 1–1.2 kΩ** lands it. See errata Issue 15. (BOM note added on R_s1/R_s2.)

## 4. Still unverified — tone-stack values
The Vox "top-boost" tone-stack passive values were **not recovered**. A single
`TONE_STACK` placeholder row (value `TBD`) is in the BOM as a flag. Derive these
from the original 25-5274-2 tone network before ordering (Part 1 §2 preserves the
original tone-stack topology and voicing).

## 5. Value change applied from the consistency pass
`R_reg2` changed **3.0 kΩ → 3.09 kΩ (E96)** so the LM317 lands inside the stated
17.0–17.5 V window (16.88 V → 17.34 V). See errata Issue 10.
