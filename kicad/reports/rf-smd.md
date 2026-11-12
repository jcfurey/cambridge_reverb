### Ground and parasitics audit — `cambridge_reverb_smd.kicad_pcb` (170.2 × 105.2 mm)

| Layer | Role | Track length (mm) |
|---|---|---:|
| `F.Cu` | signal | 2819 |
| `In1.Cu` | GND plane | — |
| `In2.Cu` | signal | 2712 |
| `B.Cu` | GND plane | — |

Tracks on a plane layer: **0**.

| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |
|---|---:|---:|---:|---:|---|
| `In1.Cu` | 94.5 % | 1 | 307 | **2** | 10.05 × 2.95 `FS1`; 8.55 × 1.75 `IC_PA`; 4.95 × 3 `J_IN3`; 4.95 × 3 `J_IN2`; 4.95 × 3 `J_IN1` |
| `B.Cu` | 91.3 % | 1 | 254 | **11** | 15.1 × 2.45 `FS1`; 10 × 2.45 `REV1`; 8.65 × 2.95 `IC_PA`; 8 × 3.35 `POT_SPD_B`; 7.55 × 2.45 `POT_TREB` |

| Check | Measured | Rule |
|---|---:|---|
| Copper to board edge, per layer | F.Cu 0.55, In1.Cu 0.55, In2.Cu 1.45, B.Cu 0.55 mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |
| Top pour to the nearest foreign trace | 0.42 mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |
| Top pour to the nearest HiZ trace | 0.93 mm | ≥ 1.0 mm |
| Top pour | 60.8 % of the board in 58 piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |
| Perimeter ground fence | 96 vias, median pitch 5 mm, largest gap 22 mm (4 gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |
| Ground vias, whole board | 340 (1.9 per cm²) | — |
| Furthest point from a ground via | 15.2 mm (near `L1`), mean 3.1 mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |
| SMD ground pads with a via to the planes within 3.5 mm | 22 of 22 | all |

**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:

| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |
|---|---:|---:|---:|---:|---:|---|---:|
| `TONE_OUT` | 24.9 | 76 | 76 | 6 | 2 | 62 k (volume wiper at half resistance) | 103 kHz |
| `JWB` | 12.6 | 35 | 36 | 4 | 2 | 72 k (bass wiper, pot at noon) | 176 kHz |
| `JWT` | 7.2 | 2 | 35 | 2 | 1 | 62 k (treble wiper) | 359 kHz |
| `DRVP` | 6.6 | 12 | 21 | 3 | 1 | 62 k (volume wiper through C_drvin) | 391 kHz |
| `GUITAR_IN` | 8.0 | 42 | 9 | 4 | 0 | 50 k (pickup, a few H: tens of kohm near resonance) | 397 kHz |
| `FS_MRB` | 36.1 | 111 | 45 | 8 | 5 | 10 k (MRB tank return, pedal open) | 440 kHz |
| `JTA` | 10.0 | 1 | 52 | 2 | 1 | 36 k (C_j3 at 2 kHz) | 442 kHz |
| `WET` | 4.5 | 31 | 0 | 2 | 0 | 62 k (reverb-level wiper) | 565 kHz |
| `JTB` | 7.0 | 4 | 32 | 2 | 1 | 36 k (C_j4 at 2 kHz) | 635 kHz |
| `PA_BIAS` | 10.8 | 23 | 37 | 5 | 0 | 22 k (R_bias3) | 672 kHz |
| `SUMJ` | 5.8 | 26 | 0 | 5 | 0 | 33 k (summer inputs in parallel -- a feedback node: see the stability note) | 829 kHz |
| `Q1G` | 3.3 | 18 | 0 | 4 | 0 | 51 k (pickup + R_rf1) | 937 kHz |
| `WN1` | 10.7 | 10 | 47 | 3 | 1 | 15 k (LFO series arm (sub-audio)) | 994 kHz |
| `JB` | 13.6 | 42 | 40 | 3 | 2 | 10 k (R_j2) | 1168 kHz |
| `MRB_T` | 12.1 | 72 | 0 | 8 | 0 | 10 k (R_mrb_ser) | 1316 kHz |
| `LFO_P` | 7.7 | 19 | 20 | 4 | 1 | 15 k (LFO shunt arm (sub-audio)) | 1382 kHz |
| `RF1` | 1.9 | 9 | 0 | 2 | 0 | 50 k (pickup + C_in_pre) | 1689 kHz |
| `JA` | 9.2 | 11 | 37 | 3 | 1 | 10 k (R_j1) | 1737 kHz |
| `R_INV` | 9.2 | 6 | 24 | 3 | 1 | 9.1 k (tank-driver gain divider) | 1900 kHz |
| `LFO_N` | 23.4 | 7 | 71 | 5 | 1 | 3.2 k (LFO gain divider) | 2126 kHz |
| `FS_REV` | 6.8 | 47 | 0 | 3 | 0 | 10 k (recovery drain load) | 2332 kHz |
| `OBUF_IN` | 6.8 | 47 | 0 | 3 | 0 | 10 k (R_mrb_ser) | 2334 kHz |
| `MKN` | 7.4 | 9 | 14 | 3 | 2 | 5 k (make-up gain divider) | 4323 kHz |
| `TANK_OUT` | 11.0 | 25 | 36 | 3 | 2 | 3 k (tank output coil) | 4838 kHz |
| `Q2G` | 2.3 | 11 | 0 | 3 | 0 | 10 k (Q1 drain load) | 6945 kHz |
| `QRG` | 3.9 | 23 | 0 | 4 | 0 | 4 k (tank coil + R_rf2) | 10267 kHz |
| `JOUT` | 12.8 | 5 | 62 | 3 | 2 | 1 k (R_j4 from the treble wiper) | 12443 kHz |
| `PA_INV` | 9.4 | 5 | 24 | 3 | 2 | 0.96 k (power-amp gain divider) | 17604 kHz |
| `RF2` | 2.2 | 12 | 0 | 2 | 0 | 3 k (tank coil + C_rev2) | 23793 kHz |
| `PA_IN` | 19.5 | 53 | 33 | 4 | 0 | 0.1 k (op-amp output) | 81787 kHz |

Lowest corner: `TONE_OUT` at 103 kHz. Every net is above 100 kHz — under 0.2 dB at 20 kHz.
