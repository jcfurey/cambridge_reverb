### Ground and parasitics audit — `cambridge_reverb_smd.kicad_pcb` (170.2 × 105.2 mm)

| Layer | Role | Track length (mm) |
|---|---|---:|
| `F.Cu` | signal | 2765 |
| `In1.Cu` | GND plane | — |
| `In2.Cu` | signal | 2543 |
| `B.Cu` | GND plane | — |

Tracks on a plane layer: **0**.

| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |
|---|---:|---:|---:|---:|---|
| `In1.Cu` | 94.6 % | 1 | 290 | **3** | 10.05 × 2.95 `FS1`; 10 × 2.95 `REV1`; 8.55 × 1.75 `IC_PA`; 4.95 × 3 `J_IN3`; 4.95 × 3 `J_IN2` |
| `B.Cu` | 92.1 % | 1 | 235 | **12** | 15.1 × 2.45 `FS1`; 10 × 2.45 `REV1`; 8.65 × 2.95 `IC_PA`; 7.55 × 2.45 `POT_TREB`; 7.55 × 2.45 `POT_SPD_A` |

| Check | Measured | Rule |
|---|---:|---|
| Copper to board edge, per layer | F.Cu 0.55, In1.Cu 0.55, In2.Cu 1.45, B.Cu 0.55 mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |
| Top pour to the nearest foreign trace | 0.42 mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |
| Top pour to the nearest HiZ trace | 0.91 mm | ≥ 1.0 mm |
| Top pour | 62.0 % of the board in 51 piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |
| Perimeter ground fence | 95 vias, median pitch 5 mm, largest gap 21.8 mm (5 gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |
| Ground vias, whole board | 337 (1.88 per cm²) | — |
| Furthest point from a ground via | 13.3 mm (near `L1`), mean 3.2 mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |
| SMD ground pads with a via to the planes within 3.5 mm | 18 of 18 | all |

**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:

| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |
|---|---:|---:|---:|---:|---:|---|---:|
| `TONE_OUT` | 25.4 | 41 | 106 | 6 | 1 | 62 k (volume wiper at half resistance) | 101 kHz |
| `JWB` | 9.9 | 48 | 10 | 4 | 2 | 72 k (bass wiper, pot at noon) | 224 kHz |
| `JWT` | 7.1 | 3 | 34 | 2 | 1 | 62 k (treble wiper) | 364 kHz |
| `FS_MRB` | 43.2 | 92 | 88 | 8 | 0 | 10 k (MRB tank return, pedal open) | 369 kHz |
| `DRVP` | 6.5 | 19 | 16 | 3 | 1 | 62 k (volume wiper through C_drvin) | 393 kHz |
| `GUITAR_IN` | 6.9 | 22 | 16 | 3 | 1 | 50 k (pickup, a few H: tens of kohm near resonance) | 462 kHz |
| `WET` | 5.5 | 39 | 0 | 2 | 0 | 62 k (reverb-level wiper) | 468 kHz |
| `JTB` | 7.8 | 3 | 38 | 2 | 1 | 36 k (C_j4 at 2 kHz) | 568 kHz |
| `JTA` | 7.3 | 3 | 35 | 2 | 1 | 36 k (C_j3 at 2 kHz) | 606 kHz |
| `Q1G` | 3.4 | 19 | 0 | 4 | 0 | 51 k (pickup + R_rf1) | 915 kHz |
| `SUMJ` | 5.2 | 22 | 0 | 5 | 0 | 33 k (summer inputs in parallel -- a feedback node: see the stability note) | 925 kHz |
| `WN1` | 10.9 | 4 | 53 | 3 | 1 | 15 k (LFO series arm (sub-audio)) | 969 kHz |
| `PA_BIAS` | 7.3 | 46 | 0 | 5 | 0 | 22 k (R_bias3) | 986 kHz |
| `MRB_T` | 14.5 | 92 | 0 | 8 | 0 | 10 k (R_mrb_ser) | 1100 kHz |
| `LFO_N` | 31.8 | 6 | 100 | 5 | 1 | 3.2 k (LFO gain divider) | 1562 kHz |
| `OBUF_IN` | 9.8 | 29 | 26 | 3 | 2 | 10 k (R_mrb_ser) | 1625 kHz |
| `R_INV` | 10.7 | 6 | 28 | 3 | 2 | 9.1 k (tank-driver gain divider) | 1640 kHz |
| `LFO_P` | 6.5 | 41 | 0 | 4 | 0 | 15 k (LFO shunt arm (sub-audio)) | 1641 kHz |
| `RF1` | 1.9 | 9 | 0 | 2 | 0 | 50 k (pickup + C_in_pre) | 1689 kHz |
| `JA` | 8.0 | 58 | 0 | 3 | 0 | 10 k (R_j1) | 1977 kHz |
| `FS_REV` | 8.0 | 57 | 0 | 3 | 0 | 10 k (recovery drain load) | 1997 kHz |
| `JB` | 7.3 | 52 | 0 | 3 | 0 | 10 k (R_j2) | 2174 kHz |
| `TANK_OUT` | 10.6 | 24 | 34 | 3 | 2 | 3 k (tank output coil) | 5020 kHz |
| `Q2G` | 2.3 | 11 | 0 | 3 | 0 | 10 k (Q1 drain load) | 6915 kHz |
| `MKN` | 4.4 | 21 | 0 | 3 | 0 | 5 k (make-up gain divider) | 7158 kHz |
| `QRG` | 3.8 | 22 | 0 | 4 | 0 | 4 k (tank coil + R_rf2) | 10356 kHz |
| `JOUT` | 12.4 | 7 | 58 | 3 | 2 | 1 k (R_j4 from the treble wiper) | 12877 kHz |
| `PA_INV` | 7.8 | 7 | 19 | 3 | 1 | 0.96 k (power-amp gain divider) | 21297 kHz |
| `RF2` | 2.2 | 12 | 0 | 2 | 0 | 3 k (tank coil + C_rev2) | 24401 kHz |
| `PA_IN` | 26.3 | 2 | 84 | 4 | 1 | 0.1 k (op-amp output) | 60561 kHz |

Lowest corner: `TONE_OUT` at 101 kHz. Every net is above 100 kHz — under 0.2 dB at 20 kHz.
