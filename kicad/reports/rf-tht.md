### Ground and parasitics audit — `cambridge_reverb.kicad_pcb` (190.2 × 115.2 mm)

| Layer | Role | Track length (mm) |
|---|---|---:|
| `F.Cu` | signal | 2983 |
| `In1.Cu` | GND plane | — |
| `In2.Cu` | signal | 3667 |
| `B.Cu` | GND plane | — |

Tracks on a plane layer: **0**.

| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |
|---|---:|---:|---:|---:|---|
| `In1.Cu` | 93.5 % | 1 | 503 | **3** | 10.05 × 2.95 `REV1`; 10 × 2.95 `FS1`; 8.55 × 1.75 `IC_PA`; 4.95 × 2.95 `POT_VOL`; 4.95 × 2.95 `POT_REV` |
| `B.Cu` | 88.6 % | 1 | 407 | **13** | 15.15 × 2.55 `FS1`; 10.1 × 2.55 `REV1`; 9 × 3.55 `POT_TREB`; 8.65 × 2.95 `IC_PA`; 7.65 × 2.55 `POT_SPD_B` |

| Check | Measured | Rule |
|---|---:|---|
| Copper to board edge, per layer | F.Cu 0.55, In1.Cu 0.55, In2.Cu 2.18, B.Cu 0.55 mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |
| Top pour to the nearest foreign trace | 0.4 mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |
| Top pour to the nearest HiZ trace | 0.91 mm | ≥ 1.0 mm |
| Top pour | 61.7 % of the board in 43 piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |
| Perimeter ground fence | 106 vias, median pitch 5 mm, largest gap 25.2 mm (4 gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |
| Ground vias, whole board | 376 (1.72 per cm²) | — |
| Furthest point from a ground via | 14.1 mm (near `L1`), mean 3.4 mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |
| SMD ground pads with a via to the planes within 3.5 mm | 0 of 0 | all |

**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:

| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |
|---|---:|---:|---:|---:|---:|---|---:|
| `TONE_OUT` | 25.1 | 58 | 96 | 6 | 0 | 62 k (volume wiper at half resistance) | 102 kHz |
| `DRVP` | 17.8 | 45 | 44 | 3 | 10 | 62 k (volume wiper through C_drvin) | 144 kHz |
| `GUITAR_IN` | 18.3 | 0 | 103 | 3 | 0 | 50 k (pickup, a few H: tens of kohm near resonance) | 174 kHz |
| `JWB` | 11.6 | 21 | 46 | 4 | 0 | 72 k (bass wiper, pot at noon) | 190 kHz |
| `SUMJ` | 14.2 | 47 | 15 | 5 | 1 | 33 k (summer inputs in parallel -- a feedback node: see the stability note) | 339 kHz |
| `JWT` | 6.3 | 15 | 20 | 2 | 1 | 62 k (treble wiper) | 405 kHz |
| `FS_MRB` | 37.7 | 186 | 16 | 6 | 2 | 10 k (MRB tank return, pedal open) | 422 kHz |
| `JTB` | 9.9 | 0 | 55 | 2 | 0 | 36 k (C_j4 at 2 kHz) | 445 kHz |
| `JTA` | 9.1 | 70 | 0 | 2 | 0 | 36 k (C_j3 at 2 kHz) | 485 kHz |
| `PA_BIAS` | 13.1 | 49 | 32 | 5 | 0 | 22 k (R_bias3) | 554 kHz |
| `Q1G` | 5.6 | 18 | 12 | 4 | 0 | 51 k (pickup + R_rf1) | 556 kHz |
| `WET` | 4.1 | 28 | 0 | 2 | 0 | 62 k (reverb-level wiper) | 627 kHz |
| `WN1` | 15.0 | 17 | 66 | 3 | 2 | 15 k (LFO series arm (sub-audio)) | 708 kHz |
| `R_INV` | 24.6 | 58 | 45 | 3 | 3 | 9.1 k (tank-driver gain divider) | 712 kHz |
| `FS_REV` | 17.3 | 15 | 84 | 3 | 1 | 10 k (recovery drain load) | 919 kHz |
| `MRB_T` | 15.3 | 9 | 73 | 6 | 0 | 10 k (R_mrb_ser) | 1038 kHz |
| `RF1` | 2.8 | 17 | 0 | 2 | 0 | 50 k (pickup + C_in_pre) | 1144 kHz |
| `LFO_P` | 8.7 | 5 | 40 | 4 | 0 | 15 k (LFO shunt arm (sub-audio)) | 1217 kHz |
| `JA` | 9.5 | 0 | 51 | 3 | 0 | 10 k (R_j1) | 1669 kHz |
| `JB` | 8.8 | 17 | 34 | 3 | 0 | 10 k (R_j2) | 1810 kHz |
| `OBUF_IN` | 7.8 | 56 | 0 | 3 | 0 | 10 k (R_mrb_ser) | 2051 kHz |
| `Q2G` | 6.0 | 17 | 17 | 3 | 0 | 10 k (Q1 drain load) | 2663 kHz |
| `MKN` | 11.4 | 5 | 32 | 3 | 1 | 5 k (make-up gain divider) | 2788 kHz |
| `LFO_N` | 15.0 | 16 | 37 | 5 | 0 | 3.2 k (LFO gain divider) | 3320 kHz |
| `TANK_OUT` | 11.3 | 61 | 13 | 3 | 2 | 3 k (tank output coil) | 4715 kHz |
| `QRG` | 7.2 | 30 | 13 | 4 | 0 | 4 k (tank coil + R_rf2) | 5525 kHz |
| `PA_INV` | 21.1 | 0 | 70 | 3 | 0 | 0.96 k (power-amp gain divider) | 7862 kHz |
| `RF2` | 3.3 | 0 | 15 | 2 | 0 | 3 k (tank coil + C_rev2) | 16170 kHz |
| `JOUT` | 7.1 | 4 | 30 | 3 | 1 | 1 k (R_j4 from the treble wiper) | 22569 kHz |
| `PA_IN` | 40.5 | 67 | 90 | 4 | 6 | 0.1 k (op-amp output) | 39326 kHz |

Lowest corner: `TONE_OUT` at 102 kHz. Every net is above 100 kHz — under 0.2 dB at 20 kHz.
