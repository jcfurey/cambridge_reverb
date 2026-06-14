# Building the KiCad schematic

## What's in the repo now vs. what you build in the GUI

**In the repo (hand-authored, ready to use):**
- `cambridge_reverb.kicad_pro` — design rules + the three net classes from the
  consistency pass (Default 0.5 mm / Power 1.5 mm / HighCurrent 2.5 mm, errata
  #11–13), with net-name patterns pre-assigning `+33V5`/`SPKR±`/`PA_OUT` to
  HighCurrent.
- `symbols/cambridge_reverb.kicad_sym` — custom symbols: `VTL5C1`,
  `Reverb_Tank_4FB2A1C`, `Footswitch_DIN6`.
- `footprints/cambridge_reverb.pretty/` — `VTL5C1`, `Inductor_MRB_1H_Toroid`
  (25 mm), `Wiring_Edge_Array_35` (3 mm pads / 1.5 mm drill, labeled).
- `sym-lib-table` / `fp-lib-table` — register the two project libraries.

**Built in the KiCad GUI (not committed as wired sheets):** the eight hierarchical
`.kicad_sch` sheets. The recovered design gives exact component values and
net-by-net connections (below + `netlist-notes.txt`), but a fully *wired*
multi-sheet schematic's geometry can't be machine-validated in this environment,
and a single malformed token makes KiCad refuse to open the file. Rather than
ship a fragile auto-generated schematic, this guide lets you assemble a clean one
in ~an afternoon. Use **net labels** for connectivity (the connections are given
as nets, so you don't need pretty wire routing to get a correct netlist).

## One-time setup
1. Open `cambridge_reverb.kicad_pro` in KiCad. The two project libs auto-load via
   the `*-lib-table` files (`${KIPRJMOD}` paths).
2. Schematic Setup → verify the three net classes are present.
3. Create a root sheet with eight hierarchical sub-sheets, one per block, in
   signal-flow order.

## Stock-symbol map
Standard KiCad library symbols for the generic parts:

| Part | KiCad symbol |
|------|--------------|
| Resistor | `Device:R` |
| Film/ceramic cap | `Device:C` |
| Electrolytic/tantalum cap | `Device:C_Polarized` |
| Inductor (MRB) | `Device:L` → footprint `cambridge_reverb:Inductor_MRB_1H_Toroid` |
| JFET (MMBF5457/J113) | `Device:Q_NJFET_DGS` (or `Transistor_FET:MMBF5457`) |
| TL072 | `Amplifier_Operational:TL072` |
| LM1875 | `Amplifier_Audio:LM1875T` if present, else generic 5-pin TO-220 power-amp symbol |
| LM317 | `Regulator_Linear:LM317_TO-220` |
| Bridge rectifier | `Device:D_Bridge_+-AA` |
| 1N4007 / 1N4148 | `Diode:1N4007` / `Diode:1N4148` |
| LED | `Device:LED` |
| Pot | `Device:R_Potentiometer` |
| VTL5C1 / reverb tank / DIN-6 | `cambridge_reverb:VTL5C1` / `:Reverb_Tank_4FB2A1C` / `:Footswitch_DIN6` |

Inter-sheet nets: `+33V5`, `+27V`, `+17V`, `GND`, `SPKR+`, `SPKR-`, plus block
hand-offs `PREAMP_OUT`, `TONE_OUT`, `DRY_SIGNAL`, `WET`, `BLEND`, `PA_INPUT`,
`PA_OUT`. Keep these names exactly so the net-class patterns in the `.kicad_pro`
match.

## Per-sheet contents (values from Part 2 + netlist-notes; verify against errata)

**Sheet 1 — Power Supply:** BR1 (KBP410G), C101–104 (10nF snubbers), C_main
4700µF, C_filt1/2 1000µF, U1 LM317 with R_reg1 240R + **R_reg2 3.09k** (errata
#10), C_reg_in/out, R_27V 47R/2W dropper, F1 1A. Outputs `+33V5`, `+27V`, `+17V`,
`GND`. R_bleed 10k/5W across C_main.

**Sheet 2 — Preamp:** Q1, Q2 (MMBF5457). Per stage: R_g 1M, R_d 10k, R_s 2k2,
C_s 10µF; C_in_pre 47nF. C_pres 100pF at Q2 drain, C_treble 470pF.

**Sheet 3 — Tone Stack:** Vox top-boost network (POT_VOL, POT_TONE). **Values
TBD** — replicate the original 25-5274-2 tone network (cross-check #4).

**Sheet 4 — Reverb:** IC1 (TL072) driver: R_drv1 100k / R_drv2 10k (gain 11×),
R_drv3 10R, C_rev1 1µF to `Reverb_Tank_4FB2A1C` IN. Recovery: Q_rec, R_rec_bias
1M, R_rec1 10k, R_rec2 2k2, C_rec_byp 10µF; C_rev2 10nF return, C_rev4 100nF,
POT_REV mix → `WET` → blend.

**Sheet 5 — Tremolo:** IC2 (TL072) Wien-bridge LFO: R_lfo1 33k, R_lfo_ser 100k,
C_lfo1/2 100nF, R_lfo_fb1 10k / R_lfo_fb2 4k7, D_lfo1/2 1N4148. VTL1 via R_led 1k;
LED_rate via R_led_diag 2k2. Signal: R_trem1 10k + VTL1 LDR shunt. POT_SPD 500k,
POT_DPT 100k, C_dc_blk 10µF, C_trem_out 100nF.

**Sheet 6 — MRB:** C_mrb_in 100nF → L1 1H ∥ C_mrb_600 68nF (default, ~610 Hz) →
C_mrb_out 100nF. Optional internal-only positions C_mrb_450 120nF / C_mrb_750
47nF (no new panel hole — errata #8).

**Sheet 7 — Power Amp (LM1875):** see `netlist-notes.txt` sheet 7 for the exact
connection list. R_bias1/2 22k, R_fb 22k ∥ C_fb_hf 1nF, R_gain 1k + C_gain 22µF,
C_in_pa 1µF, C_out_pa 2200µF (required, errata #7), R_zobel 10R + C_zobel 100nF,
C_byp1 100nF + C_byp2 10µF on pin 5 only (errata #17), D1/D2 1N4007. Gain 23×.

**Sheet 8 — Switching / Wiring:** `Footswitch_DIN6` (FS_REV/TREM/MRB/GND), input
jacks (IN3 = internal FX loop, R_fx_pad 10k), and the `Wiring_Edge_Array_35`
off-board pad bank.

## Before layout / fab
- Run **ERC**; resolve unconnected/conflicting nets.
- Assign the HighCurrent class to the speaker/PA path if any net escaped the
  name patterns.
- Follow `docs/04-jlcpcb-fabrication.md` for DRC, ground pour, and Gerber export;
  `production/CHECKLIST.md` for the fab package.
