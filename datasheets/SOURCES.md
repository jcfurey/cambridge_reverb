# Datasheet sources — committed PDFs and what each one backs

The PDFs in this folder are the manufacturer documents the footprints, pinouts and
design numbers were taken from. They are **committed on purpose** (the previous
policy of not committing them was reversed 2026-09-07): a footprint or a pin
number is only as good as the drawing it came from, and errata #18 (JFET pins)
showed why the exact revision matters. Re-download from the source URL when
re-verifying before an order; the SHA-256 prefix identifies the revision used here.

| File | Part | Source | Revision | Used for | SHA-256 (16) |
|---|---|---|---|---|---|
| `LM1875_TI_SNAS524A.pdf` | LM1875T power amp | ti.com/lit/ds/symlink/lm1875.pdf | SNAS524A, May 2004 | TO-220-5 NDH0005D package drawing (1.70 mm pitch, 0.89×0.38 mm leads) → footprint `TO-220-5_Vertical_P1.70mm_LM1875`; pinout 1 IN+ 2 IN− 3 V− 4 OUT 5 V+ | `049a5385f4720ade` |
| `LM317_TI.pdf` | LM317T regulator | ti.com/lit/ds/symlink/lm317.pdf | SLVS044Z, rev. April 2025 | Vout = 1.25 (1 + R2/R1) (errata #10); TO-220 pinout ADJ/OUT/IN | `323ec64a58515090` |
| `TL072_TI.pdf` | TL072 dual op-amp | ti.com/lit/ds/symlink/tl072.pdf | SLOS080W, rev. July 2025 | DIP-8 pinout; supply range for the single-supply +17 V design; slew/GBW behind `opamp*.sub` | `40b14981bad45917` |
| `MMBF5457_onsemi_2023-01_Rev1.pdf` | MMBF5457 JFET (SOT-23) | onsemi.com/pdf/datasheet/mmbf5457-d.pdf | Rev. 1, January 2023 | **SOT-23 pinout 1 D / 2 S / 3 G** — the symbol renumbering of errata #18; SMD-variant footprint | `94751083a9322c4c` |
| `2N5457_onsemi_2010-02_Rev6.pdf` | 2N5457 JFET (TO-92, discontinued) | onsemi.com/pdf/datasheet/2n5457-d.pdf | Rev. 6, February 2010 | **TO-92 lead order 1 Drain / 2 Source / 3 Gate** (errata #18); Idss/Vp spread behind the errata #15 bias trim | `d547280c34509502` |
| `J111-J113_onsemi_2006-03_Rev2.pdf` | J111/J112/J113 JFET (TO-92 alternative) | onsemi.com/pdf/datasheet/j111-d.pdf | Rev. 2, March 2006 | The THT-alternative JFET (BOM): same D-S-G lead order; check Vgs(off) vs the 2N5457 when substituting | `8ceafd60592e75de` |
| `KBP404G-KBP410G_Diodes_DS39310.pdf` | KBP410G bridge rectifier | diodes.com/datasheet/download/KBP404G-KBP410G.pdf | DS39310 Rev. 3-2, February 2026 | **KBP outline** (3.81 mm pitch, 0.86×0.55 mm leads, 14.5×3.5 mm body) and the **+ ~ ~ −** pin order → `Bridge_KBP_P3.81mm`, bridge symbol renumbered | `c13e1a92de6bc9d3` |
| `KBP005G-KBP10G_Diodes_DS21203.pdf` | KBP005G–KBP10G (same KBP package, 1.5 A) | diodes.com/assets/Datasheets/ds21203.pdf | DS21203 Rev. 13-2, August 2025 | Cross-check that the KBP outline is identical across the family | `a714169960729a36` |
| `1N4001-1N4007_Vishay.pdf` | 1N4007 (D1, D2 output clamps) | vishay.com/docs/88503/1n4001.pdf | 29-Apr-2020 | DO-41 dimensions (THT board) | `56a77c6615c90c11` |
| `1N4148_Vishay.pdf` | 1N4148 (D_lfo1/2 LFO clamp) | vishay.com/docs/81857/1n4148.pdf | Rev. 1.6, 07-Nov-2024 | DO-35 dimensions (THT board) | `aefe85400a427ed8` |
| `1N4148W_BAV16W_Diodes_DS30086.pdf` | 1N4148W (SOD-123, SMD variant) | diodes.com/assets/Datasheets/ds30086.pdf | DS30086 Rev. 31-2, September 2024 | SOD-123 replacement for 1N4148 on the SMD board | `39c16a6888bdab22` |
| `VTL5C1_VTL5C2_PerkinElmer_Vactec.pdf` | VTL5C1 vactrol (Xvive remake) | logosfoundation.org/instrum_gwr/playerpiano/Optor_VTL5C1_87223.pdf (hosted copy of the PerkinElmer/Vactec catalog page) | catalog p. 43 (undated) | Package dimensions behind the `VTL5C1` footprint; on/off resistance, response time for the tremolo depth. Xvive publishes no PDF — their part is a drop-in remake | `e6cdace0ba7d05bb` |
| `AS-0524_AnTek.pdf` | AnTek AS-0524 toroid (optional T1) | antekinc.com/content/AS-0524.pdf | AnTek test sheet (undated) | Secondary voltage / VA and the open- and short-circuit test data (Part 9) | `76013dad454a445f` |

## Not committed (no PDF obtainable, or not a single document)

| Part | Why | Where the numbers came from |
|---|---|---|
| **S1M** (SMA rectifier, SMD variant) | Diodes' S1A–S1M sheet was not reachable from this session (404). Any S1M / SMA 1 kV 1 A part is a drop-in; the footprint is KiCad's stock `D_SMA`. | KiCad library footprint; generic JEDEC DO-214AC |
| **KBU4M** (alternative bridge, errata #3) | onsemi's KBU4A–KBU4M sheet was not reachable. KBU is a 5.08 mm-pitch package and needs a footprint swap. | not used on either board |
| **Accutronics / Belton 4FB2A1C** reverb pan | No manufacturer PDF; the distributor spec table is the reference. Input 1475 Ω (200 Ω DC), output 2250 Ω (200 Ω DC), decay 1.75–3.0 s, 2×2 springs, 42.5 × 11 × 3.3 cm, in/out grounded. | amplifiedparts.com/tech-articles/accutronics-products-and-specifications |
| TL072 SPICE model | not a datasheet; the ngspice macromodels are in `spice/models/` | — |

## Reverb-pan code reminder
The Accutronics/Belton 4-digit-plus code encodes the tank: confirm the part is
**4FB2A1C** (high-impedance input ~1475 Ω) and **not** 4AB3C1B (8 Ω input,
incompatible with the direct TL072 driver — see Part 9 / errata Issue 14).

## Verification reminder
Stock and part status drift (see Part 8). Re-check live availability at
Digikey/Mouser and confirm the JFET and bridge selections before ordering — and
if a datasheet revision changes, re-check the package drawing against the
footprint in `kicad/footprints/cambridge_reverb.pretty/`.
