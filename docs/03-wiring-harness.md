# Vox Cambridge Reverb — Part 3: Wiring Harness & Troubleshooting

> Reconstructed document — see `PROVENANCE.md`. The troubleshooting tables, wire
> routing, and grounding rules are recovered substantially verbatim.

## Wire routing path — recovered verbatim
```
    CONTROL PANEL (above)
         |
    +----+----------------------------+
    |   wires run through gap          |
    |   between panel and chassis      |
    +----------------------------------+
    |          PCB (in chassis)        |
    |      WIRING PADS                 |
    +----------------------------------+
    |   wires to heatsink/xfmr         |
    |   run below chassis pan          |
    +----------------------------------+
         |
    HEATSINK + TRANSFORMER (below)

All signal wires (shielded) route along the LEFT side of the chassis.
All power wires (heavy gauge) route along the RIGHT side.
Physical separation minimizes magnetic coupling between supply currents
and sensitive audio signals.
```

## Footswitch (6-pin DIN)
The original 6-pin DIN footswitch connector and pedal are retained. Footswitch
pads on the PCB: FS_REV, FS_TREM, FS_MRB, FS_GND.

## Troubleshooting — no sound at all (recovered verbatim)

| Check | Expected | If wrong |
|-------|----------|----------|
| AC at T1 primary | 120 VAC | Check power cord, fuse, power switch |
| AC at T1 secondary | ~48 VAC (or ~24 VAC) | Transformer is dead — replace |
| DC at C_main (+) | 33–35 VDC | Check bridge rectifier, fuse F1 |
| DC at 17V rail | 17.0–17.5 V | Check LM317, R_reg1, R_reg2 |
| DC at LM317 input (VREG_IN) | ~31–33 V | Check R_27V (100Ω) + C_filt1 pre-filter |
| DC at LM1875 pin 5 | ~33.5 V | Check wiring to V+ rail |
| DC at LM1875 pin 4 | ~16–17 V (V+/2) | IC may be bad or oscillating |
| Signal at Q1 gate | Guitar signal present | Check input jack, C1, R1 |
| Signal at Q1 drain | Amplified signal | Check JFET biasing (Vd = 8–9V) |

## Troubleshooting — hum or buzz (recovered verbatim)

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 60 Hz hum (steady) | Ground loop or missing ground | Check star ground, all ground returns |
| 120 Hz buzz (harsh) | Rectifier noise or failed filter cap | Check snubbing caps C101–104, test C_main |
| Hum varies with volume | Preamp picking up noise | Shield input wiring, check preamp ground |
| Hum only with reverb on | Reverb pan cable unshielded | Use shielded cable for pan connections |
| Buzz with tremolo on | LFO coupling into audio path | Separate LFO wiring from signal wiring |

## Troubleshooting — oscillation (recovered verbatim)

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| High-frequency squeal | LM1875 oscillating | Check Zobel network, add 50pF cap across input |
| Low-frequency motorboating | Power supply feedback | Check all bypass caps, verify star ground |

## Star grounding
Single star-ground point located near C_main, connected to chassis. All ground
returns land at the star. The continuous bottom-layer ground plane ties to the
star via multiple vias near C_main (see Part 4).
