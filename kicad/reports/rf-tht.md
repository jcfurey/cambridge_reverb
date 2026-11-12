### Ground and parasitics audit — `cambridge_reverb.kicad_pcb` (190.2 × 115.2 mm)

| Layer | Role | Track length (mm) |
|---|---|---:|
| `F.Cu` | signal | 2829 |
| `In1.Cu` | GND plane | — |
| `In2.Cu` | signal | 3800 |
| `B.Cu` | GND plane | — |

Tracks on a plane layer: **0**.

| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |
|---|---:|---:|---:|---:|---|
| `In1.Cu` | 93.6 % | 1 | 496 | **3** | 10.05 × 2.95 `REV1`; 10 × 2.95 `FS1`; 8.55 × 1.75 `IC_PA`; 4.95 × 2.95 `POT_VOL`; 4.95 × 2.95 `POT_REV` |
| `B.Cu` | 89.3 % | 1 | 415 | **13** | 15.15 × 2.55 `FS1`; 10.1 × 2.55 `REV1`; 8.65 × 2.95 `IC_PA`; 7.65 × 2.55 `POT_TREB`; 7.65 × 2.55 `POT_SPD_B` |

| Check | Measured | Rule |
|---|---:|---|
| Copper to board edge, per layer | F.Cu 0.55, In1.Cu 0.55, In2.Cu 2.18, B.Cu 0.55 mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |
| Top pour to the nearest foreign trace | 0.41 mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |
| Top pour to the nearest HiZ trace | 0.91 mm | ≥ 1.0 mm |
| Top pour | 62.3 % of the board in 34 piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |
| Perimeter ground fence | 106 vias, median pitch 5 mm, largest gap 25.2 mm (4 gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |
| Ground vias, whole board | 370 (1.69 per cm²) | — |
| Furthest point from a ground via | 13.2 mm (near `L1`), mean 3.5 mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |
| SMD ground pads with a via to the planes within 3.5 mm | 0 of 0 | all |

**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:

| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |
|---|---:|---:|---:|---:|---:|---|---:|
| `TONE_OUT` | 27.4 | 67 | 101 | 6 | 1 | 62 k (volume wiper at half resistance) | **94 kHz** |
| `GUITAR_IN` | 21.0 | 0 | 119 | 3 | 0 | 50 k (pickup, a few H: tens of kohm near resonance) | 152 kHz |
| `JWB` | 11.6 | 21 | 46 | 4 | 0 | 72 k (bass wiper, pot at noon) | 190 kHz |
| `DRVP` | 11.9 | 90 | 0 | 3 | 0 | 62 k (volume wiper through C_drvin) | 216 kHz |
| `SUMJ` | 19.8 | 37 | 39 | 5 | 2 | 33 k (summer inputs in parallel -- a feedback node: see the stability note) | 244 kHz |
| `JWT` | 9.7 | 9 | 40 | 2 | 3 | 62 k (treble wiper) | 263 kHz |
| `FS_MRB` | 46.0 | 199 | 31 | 6 | 7 | 10 k (MRB tank return, pedal open) | 346 kHz |
| `Q1G` | 7.5 | 5 | 31 | 4 | 1 | 51 k (pickup + R_rf1) | 415 kHz |
| `JTA` | 9.6 | 0 | 53 | 2 | 0 | 36 k (C_j3 at 2 kHz) | 460 kHz |
| `PA_BIAS` | 15.0 | 28 | 59 | 5 | 0 | 22 k (R_bias3) | 482 kHz |
| `WET` | 5.0 | 0 | 25 | 2 | 0 | 62 k (reverb-level wiper) | 518 kHz |
| `JTB` | 8.5 | 11 | 36 | 2 | 1 | 36 k (C_j4 at 2 kHz) | 522 kHz |
| `WN1` | 13.1 | 6 | 63 | 3 | 2 | 15 k (LFO series arm (sub-audio)) | 812 kHz |
| `R_INV` | 18.3 | 28 | 43 | 3 | 1 | 9.1 k (tank-driver gain divider) | 953 kHz |
| `RF1` | 2.8 | 17 | 0 | 2 | 0 | 50 k (pickup + C_in_pre) | 1144 kHz |
| `LFO_P` | 8.9 | 23 | 24 | 4 | 2 | 15 k (LFO shunt arm (sub-audio)) | 1189 kHz |
| `LFO_N` | 36.0 | 7 | 116 | 5 | 0 | 3.2 k (LFO gain divider) | 1381 kHz |
| `MRB_T` | 11.4 | 71 | 5 | 6 | 0 | 10 k (R_mrb_ser) | 1399 kHz |
| `FS_REV` | 10.8 | 81 | 0 | 3 | 0 | 10 k (recovery drain load) | 1477 kHz |
| `JB` | 9.7 | 0 | 52 | 3 | 0 | 10 k (R_j2) | 1643 kHz |
| `JA` | 9.6 | 0 | 51 | 3 | 0 | 10 k (R_j1) | 1661 kHz |
| `OBUF_IN` | 8.5 | 62 | 0 | 3 | 0 | 10 k (R_mrb_ser) | 1879 kHz |
| `Q2G` | 6.0 | 17 | 17 | 3 | 0 | 10 k (Q1 drain load) | 2661 kHz |
| `MKN` | 11.5 | 7 | 31 | 3 | 1 | 5 k (make-up gain divider) | 2773 kHz |
| `TANK_OUT` | 14.3 | 52 | 35 | 3 | 3 | 3 k (tank output coil) | 3718 kHz |
| `QRG` | 9.1 | 29 | 25 | 4 | 0 | 4 k (tank coil + R_rf2) | 4379 kHz |
| `PA_INV` | 21.2 | 0 | 70 | 3 | 0 | 0.96 k (power-amp gain divider) | 7828 kHz |
| `RF2` | 3.3 | 0 | 15 | 2 | 0 | 3 k (tank coil + C_rev2) | 16093 kHz |
| `JOUT` | 5.7 | 22 | 12 | 3 | 0 | 1 k (R_j4 from the treble wiper) | 27690 kHz |
| `PA_IN` | 22.7 | 65 | 38 | 4 | 0 | 0.1 k (op-amp output) | 70043 kHz |

Lowest corner: `TONE_OUT` at 94 kHz. 1 net(s) below 100 kHz: `TONE_OUT`.
