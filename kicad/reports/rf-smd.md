### Ground and parasitics audit — `cambridge_reverb_smd.kicad_pcb` (170.2 × 105.2 mm)

| Layer | Role | Track length (mm) |
|---|---|---:|
| `F.Cu` | signal | 2788 |
| `In1.Cu` | GND plane | — |
| `In2.Cu` | signal | 2856 |
| `B.Cu` | GND plane | — |

Tracks on a plane layer: **0**.

| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |
|---|---:|---:|---:|---:|---|
| `In1.Cu` | 94.6 % | 1 | 281 | **3** | 10.05 × 2.95 `FS1`; 10 × 2.95 `REV1`; 8.55 × 3.45 `IC_PA`; 4.95 × 3 `J_IN3`; 4.95 × 3 `J_IN2` |
| `B.Cu` | 92.2 % | 1 | 236 | **11** | 15.1 × 2.45 `FS1`; 10 × 2.45 `REV1`; 8.65 × 2.95 `IC_PA`; 8.6 × 3.15 `POT_DPT`; 7.55 × 2.45 `POT_TREB` |

| Check | Measured | Rule |
|---|---:|---|
| Copper to board edge, per layer | F.Cu 0.55, In1.Cu 0.55, In2.Cu 1.39, B.Cu 0.55 mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |
| Top pour to the nearest foreign trace | 0.41 mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |
| Top pour to the nearest HiZ trace | 0.91 mm | ≥ 1.0 mm |
| Top pour | 60.7 % of the board in 45 piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |
| Perimeter ground fence | 95 vias, median pitch 5 mm, largest gap 21.8 mm (5 gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |
| Ground vias, whole board | 326 (1.82 per cm²) | — |
| Furthest point from a ground via | 14.3 mm (near `TP_TREM_OUT`), mean 3.3 mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |
| SMD ground pads with a via to the planes within 3.5 mm | 21 of 21 | all |

**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:

| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |
|---|---:|---:|---:|---:|---:|---|---:|
| `TONE_OUT` | 21.2 | 106 | 32 | 6 | 2 | 62 k (volume wiper at half resistance) | 121 kHz |
| `JWB` | 15.6 | 15 | 71 | 4 | 1 | 72 k (bass wiper, pot at noon) | 141 kHz |
| `DRVP` | 9.8 | 51 | 13 | 3 | 1 | 62 k (volume wiper through C_drvin) | 263 kHz |
| `WET` | 6.8 | 50 | 0 | 2 | 0 | 62 k (reverb-level wiper) | 379 kHz |
| `JWT` | 5.6 | 41 | 0 | 2 | 0 | 62 k (treble wiper) | 461 kHz |
| `JTA` | 9.2 | 19 | 32 | 2 | 2 | 36 k (C_j3 at 2 kHz) | 478 kHz |
| `FS_MRB` | 32.1 | 61 | 67 | 6 | 2 | 10 k (MRB tank return, pedal open) | 495 kHz |
| `JTB` | 8.1 | 2 | 40 | 2 | 1 | 36 k (C_j4 at 2 kHz) | 543 kHz |
| `GUITAR_IN` | 5.8 | 27 | 9 | 3 | 0 | 50 k (pickup, a few H: tens of kohm near resonance) | 548 kHz |
| `PA_BIAS` | 11.7 | 62 | 17 | 4 | 0 | 22 k (R_bias3) | 619 kHz |
| `LFO_P` | 16.5 | 70 | 36 | 4 | 1 | 15 k (LFO shunt arm (sub-audio)) | 642 kHz |
| `SUMJ` | 6.5 | 29 | 0 | 5 | 0 | 33 k (summer inputs in parallel -- a feedback node: see the stability note) | 746 kHz |
| `R_INV` | 23.3 | 42 | 46 | 3 | 6 | 9.1 k (tank-driver gain divider) | 751 kHz |
| `WN1` | 11.8 | 4 | 58 | 3 | 1 | 15 k (LFO series arm (sub-audio)) | 896 kHz |
| `Q1G` | 3.2 | 16 | 0 | 4 | 0 | 51 k (pickup + R_rf1) | 986 kHz |
| `JB` | 15.8 | 7 | 80 | 3 | 1 | 10 k (R_j2) | 1007 kHz |
| `OBUF_IN` | 14.2 | 88 | 13 | 3 | 1 | 10 k (R_mrb_ser) | 1120 kHz |
| `JA` | 13.9 | 5 | 70 | 3 | 1 | 10 k (R_j1) | 1145 kHz |
| `MRB_T` | 13.4 | 23 | 46 | 6 | 1 | 10 k (R_mrb_ser) | 1184 kHz |
| `FS_REV` | 7.4 | 52 | 0 | 3 | 0 | 10 k (recovery drain load) | 2148 kHz |
| `LFO_N` | 18.0 | 22 | 42 | 5 | 2 | 3.2 k (LFO gain divider) | 2756 kHz |
| `RF1` | 1.1 | 3 | 0 | 2 | 0 | 50 k (pickup + C_in_pre) | 2819 kHz |
| `MKN` | 10.1 | 8 | 23 | 3 | 3 | 5 k (make-up gain divider) | 3156 kHz |
| `TANK_OUT` | 12.5 | 38 | 36 | 3 | 2 | 3 k (tank output coil) | 4253 kHz |
| `Q2G` | 2.8 | 15 | 0 | 3 | 0 | 10 k (Q1 drain load) | 5775 kHz |
| `QRG` | 3.9 | 22 | 0 | 4 | 0 | 4 k (tank coil + R_rf2) | 10268 kHz |
| `PA_INV` | 13.5 | 74 | 0 | 4 | 0 | 0.96 k (power-amp gain divider) | 12284 kHz |
| `JOUT` | 10.0 | 23 | 35 | 3 | 1 | 1 k (R_j4 from the treble wiper) | 15984 kHz |
| `RF2` | 1.4 | 5 | 0 | 2 | 0 | 3 k (tank coil + C_rev2) | 37083 kHz |
| `PA_IN` | 25.8 | 3 | 82 | 4 | 1 | 0.1 k (op-amp output) | 61807 kHz |

Lowest corner: `TONE_OUT` at 121 kHz. Every net is above 100 kHz — under 0.2 dB at 20 kHz.
