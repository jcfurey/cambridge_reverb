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

## 3. SPICE `.cir` is simplified vs the documented model — flagged, not fixed
The power-amp netlist omits things the docs describe; the sim is directionally
right but not the full guitar-optimized model:

- **`C_fb_hf` (1 nF across R_fb) is not in the `.cir`.** Part 2, the netlist
  notes, and the BOM all include it for the 7.2 kHz bandwidth limit, but the
  simulation has no HF rolloff element — so the `.cir` will show flat HF response
  instead of the intended −3 dB at ~7.2 kHz. Add `C_fb_hf PA_OUT NODE_FB 1n` to
  reproduce the documented bandwidth.
- **Speaker is a plain 8 Ω resistor.** Part 6B specifies a 10" speaker model
  (105 Hz mechanical resonance + voice-coil inductance); the `.cir` does not
  model it.
- **No guitar pickup / cable model** (3 H / 6 kΩ / 100 pF + 300 pF cable) at the
  input, which Part 6B lists as part of the guitar-optimized chain.

These are recorded in `../spice/README.md` as rebuild items; the recovered
`.cir` is left as-is (verbatim) so its provenance is clear.

## 4. Still unverified — tone-stack values
The Vox "top-boost" tone-stack passive values were **not recovered**. A single
`TONE_STACK` placeholder row (value `TBD`) is in the BOM as a flag. Derive these
from the original 25-5274-2 tone network before ordering (Part 1 §2 preserves the
original tone-stack topology and voicing).

## 5. Value change applied from the consistency pass
`R_reg2` changed **3.0 kΩ → 3.09 kΩ (E96)** so the LM317 lands inside the stated
17.0–17.5 V window (16.88 V → 17.34 V). See errata Issue 10.
