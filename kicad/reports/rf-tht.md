### Ground and parasitics audit — `cambridge_reverb.kicad_pcb` (190.2 × 115.2 mm)

| Layer | Role | Track length (mm) |
|---|---|---:|
| `F.Cu` | signal | 2626 |
| `In1.Cu` | GND plane | — |
| `In2.Cu` | signal | 3751 |
| `B.Cu` | GND plane | — |

Tracks on a plane layer: **0**.

| Plane | Copper coverage | Pieces | Openings | Longer than 5 mm | Longest openings (length × width mm, at) |
|---|---:|---:|---:|---:|---|
| `In1.Cu` | 93.6 % | 1 | 466 | **3** | 10.05 × 2.95 `REV1`; 10 × 2.95 `FS1`; 8.55 × 3.45 `IC_PA`; 4.95 × 2.95 `POT_VOL`; 4.95 × 2.95 `POT_REV` |
| `B.Cu` | 89.5 % | 1 | 382 | **15** | 15.15 × 2.55 `FS1`; 10.1 × 2.55 `REV1`; 8.65 × 2.95 `IC_PA`; 8.6 × 3.1 `POT_VOL`; 7.65 × 2.55 `POT_TREB` |

| Check | Measured | Rule |
|---|---:|---|
| Copper to board edge, per layer | F.Cu 0.55, In1.Cu 0.55, In2.Cu 2.18, B.Cu 0.55 mm | ≥ 0.5 mm here (JLCPCB: ≥ 0.2 mm from a routed edge, ± 0.2 mm on the edge itself; ≥ 0.4 mm from a V-cut) |
| Top pour to the nearest foreign trace | 0.42 mm | ≥ 0.5 mm (2.4 × the 0.21 mm to the plane) |
| Top pour to the nearest HiZ trace | 0.91 mm | ≥ 1.0 mm |
| Top pour | 64.0 % of the board in 33 piece(s) | every piece tied to the planes (unconnected pieces are removed by the fill) |
| Perimeter ground fence | 106 vias, median pitch 5 mm, largest gap 25.2 mm (4 gaps over 10 mm) | 5 mm pitch; gaps only at the corner holes and the wiring pads |
| Ground vias, whole board | 360 (1.64 per cm²) | — |
| Furthest point from a ground via | 14.7 mm (near `R_mk2`), mean 3.7 mm | λ/10 in FR4: 14 mm at 1 GHz, 7.5 mm at 1.9 GHz |
| SMD ground pads with a via to the planes within 3.5 mm | 0 of 0 | all |

**Capacitance to ground of the sensitive nets** (trace over its plane + pads + vias; ± 30 %) and the corner it makes with the node impedance:

| Net | C (pF) | F.Cu (mm) | In2 (mm) | pads | vias | node impedance | corner |
|---|---:|---:|---:|---:|---:|---|---:|
| `TONE_OUT` | 29.5 | 22 | 141 | 6 | 3 | 62 k (volume wiper at half resistance) | **87 kHz** |
| `DRVP` | 13.0 | 22 | 53 | 3 | 1 | 62 k (volume wiper through C_drvin) | 198 kHz |
| `JWB` | 11.0 | 32 | 34 | 4 | 0 | 72 k (bass wiper, pot at noon) | 202 kHz |
| `GUITAR_IN` | 15.3 | 79 | 26 | 3 | 1 | 50 k (pickup, a few H: tens of kohm near resonance) | 209 kHz |
| `SUMJ` | 17.7 | 26 | 39 | 5 | 1 | 33 k (summer inputs in parallel -- a feedback node: see the stability note) | 273 kHz |
| `R_INV` | 57.1 | 12 | 188 | 3 | 1 | 9.1 k (tank-driver gain divider) | 306 kHz |
| `Q1G` | 8.9 | 0 | 45 | 4 | 0 | 51 k (pickup + R_rf1) | 350 kHz |
| `FS_MRB` | 41.3 | 156 | 47 | 6 | 1 | 10 k (MRB tank return, pedal open) | 386 kHz |
| `JWT` | 5.0 | 36 | 0 | 2 | 0 | 62 k (treble wiper) | 518 kHz |
| `JTB` | 8.3 | 0 | 46 | 2 | 0 | 36 k (C_j4 at 2 kHz) | 531 kHz |
| `WET` | 4.6 | 33 | 0 | 2 | 0 | 62 k (reverb-level wiper) | 557 kHz |
| `JTA` | 7.3 | 55 | 0 | 2 | 0 | 36 k (C_j3 at 2 kHz) | 603 kHz |
| `PA_BIAS` | 10.6 | 0 | 55 | 4 | 0 | 22 k (R_bias3) | 686 kHz |
| `WN1` | 10.7 | 19 | 39 | 3 | 2 | 15 k (LFO series arm (sub-audio)) | 992 kHz |
| `JB` | 14.5 | 0 | 80 | 3 | 0 | 10 k (R_j2) | 1099 kHz |
| `RF1` | 2.8 | 17 | 0 | 2 | 0 | 50 k (pickup + C_in_pre) | 1143 kHz |
| `LFO_P` | 9.2 | 5 | 43 | 4 | 0 | 15 k (LFO shunt arm (sub-audio)) | 1149 kHz |
| `FS_REV` | 11.5 | 54 | 21 | 3 | 1 | 10 k (recovery drain load) | 1388 kHz |
| `MRB_T` | 11.1 | 5 | 51 | 6 | 0 | 10 k (R_mrb_ser) | 1429 kHz |
| `LFO_N` | 32.4 | 0 | 107 | 5 | 0 | 3.2 k (LFO gain divider) | 1536 kHz |
| `JA` | 8.9 | 9 | 41 | 3 | 0 | 10 k (R_j1) | 1787 kHz |
| `OBUF_IN` | 8.5 | 62 | 0 | 3 | 0 | 10 k (R_mrb_ser) | 1879 kHz |
| `QRG` | 15.1 | 19 | 56 | 4 | 5 | 4 k (tank coil + R_rf2) | 2635 kHz |
| `Q2G` | 6.0 | 17 | 17 | 3 | 0 | 10 k (Q1 drain load) | 2661 kHz |
| `MKN` | 11.0 | 22 | 21 | 3 | 1 | 5 k (make-up gain divider) | 2883 kHz |
| `TANK_OUT` | 12.8 | 42 | 35 | 3 | 2 | 3 k (tank output coil) | 4149 kHz |
| `PA_INV` | 23.4 | 12 | 70 | 4 | 0 | 0.96 k (power-amp gain divider) | 7084 kHz |
| `RF2` | 3.0 | 19 | 0 | 2 | 0 | 3 k (tank coil + C_rev2) | 17803 kHz |
| `JOUT` | 6.4 | 19 | 16 | 3 | 1 | 1 k (R_j4 from the treble wiper) | 24955 kHz |
| `PA_IN` | 15.3 | 81 | 3 | 4 | 0 | 0.1 k (op-amp output) | 104126 kHz |

Lowest corner: `TONE_OUT` at 87 kHz. 1 net(s) below 100 kHz: `TONE_OUT`.
