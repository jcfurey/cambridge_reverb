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
The original 6-pin DIN footswitch connector and pedal are retained. Pads on the PCB
(group `FS1`, silk `REV TRM MRB G G G`): three lines and three grounds. **Each pedal
button must short its line to a ground pad** (errata #27):

| Line | Button closed | Button open / no pedal |
|------|---------------|------------------------|
| `REV` | reverb off | reverb on (level pot) |
| `TRM` | tremolo off | tremolo on (depth pot) |
| `MRB` | **MRB on** | MRB out of circuit (flat) |

`REV` carries the reverb signal at ~10 kΩ: use the pedal's screened cable. To have the
MRB without a pedal, link pads 3 and 4.

## Panel pots
Every pot group is labelled `CCW · W · CW` on the board: lug 1 (the counter-clockwise
end, left lug seen from the shaft with the lugs down) to `CCW`, the wiper to `W`, lug 3
to `CW`. Clockwise is then "more" on every control (errata #29). The speed pot is one
dual-gang part: gang A to `POT_SPD_A`, gang B to `POT_SPD_B`.

## Power transformer (errata #26)
Pads `AC · CT · AC` and the link `JP_BR` beside them:
- **centre-tapped secondary** (the original; or 2 × 24 V in series): ends to `AC`, tap to
  `CT`, **`JP_BR` open**;
- **single 24 V winding** (or 2 × 24 V in parallel): ends to `AC`, `CT` empty, **wire
  link in `JP_BR`**.
Never both: the centre tap and the bridge's "−" pin on ground together short each
half-winding through a bridge diode.

## Troubleshooting — no sound at all (recovered verbatim)

| Check | Expected | If wrong |
|-------|----------|----------|
| AC at T1 primary | 120 VAC | Check power cord, fuse, power switch |
| AC at T1 secondary | ~48 VAC (or ~24 VAC) | Transformer is dead — replace |
| DC at C_main (+) | 33–35 VDC | Check bridge rectifier, fuse F1 |
| DC at 17V rail | 16.4–17.7 V (17.0 typ.) | Check LM317, R_reg1, R_reg2 |
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
| Hum only with reverb on | Reverb pan cable unshielded — or BOTH shields grounded with a both-grounded tank (a loop) | Use shielded cable for pan connections; ground-loop rule 6 below |
| Hum that changes when you touch a jack, pot or the footswitch cable | A second ground path through the chassis | Ground-loop rules 1–7 below |
| Thump when the tremolo starts / click from the mid-cut switch | A node floating on a capacitor | `R_tb`, `R_midb` fitted? (errata #38, #39) |
| Buzz with tremolo on | LFO coupling into audio path | Separate LFO wiring from signal wiring |

## Troubleshooting — oscillation (recovered verbatim)

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| High-frequency squeal | LM1875 oscillating | Check Zobel network, add 50pF cap across input |
| Low-frequency motorboating | Power supply feedback | Check all bypass caps, verify star ground |

## Star grounding
*As built since errata #32 (2026-11-12).* The board has three ground nets:

| Net | What is on it | Copper |
|---|---|---|
| `PGND` power ground | transformer centre tap, reservoir `C_main` −, LM1875 pin 3 with its decoupling, Zobel and clamp diode, bridge snubbers | 1.5 mm traces |
| `SPK_N` speaker return | the `LS1` "−" pad | 1.5 mm trace |
| `GND` signal ground | everything else: both planes and the top pour | planes |

`R_spk_rtn` (0 Ω, a wire link) takes the speaker return to power ground; **`R_gnd`
(0 Ω) is the star**: the one link from the speaker's "−" terminal to the planes. The
reservoir's charging pulses (0.7 A peaks at idle, 3 A at full power) and the speaker
current therefore never flow in the copper the preamp is referenced to. On the earlier
single-net board they did, and `kicad/gen/ground_audit.py` puts the result at 4–7 mV of
buzz at the speaker at idle; now it is under 0.1 mV (`kicad/reports/ground-*.md`).

- Do not add ground links. One is the design.
- **Chassis:** bond it to circuit ground in ONE place. With the original
  (non-insulated) input jacks that place is the jacks: leave the `J_CHS` pads empty.
  With insulated jacks run one wire from `J_CHS` (SMD board; the PSU-corner `GND`
  test point on the THT board) to the chassis lug. The mains safety earth goes to
  the chassis, never to the board.
- Before first power-up: 0 Ω between test points `GND` and `PGND`.

## Ground loops — eight wiring rules (errata #40, #41)

The board has one ground link by design. Every rule below keeps a second one from
appearing through the hardware or the wiring; `kicad/gen/loop_audit.py` simulates what
each mistake costs (`kicad/reports/loops-*.md`).

1. **One chassis bond.** Metal (non-insulated) input jacks ARE that bond — then leave
   `J_CHS` empty. With insulated jacks: one wire from `J_CHS` (SMD board; the
   power-supply `GND` test point on the THT board) to the chassis lug.
2. **Insulate both TO-220 tabs.** The LM1875's tab is its pin 3 = power ground; bare on
   a chassis that is also signal ground it bridges the star (simulated: hum ×100 with
   the hot preamp, and the speaker current fed back into the input within 6 dB of
   oscillation). Mica + shoulder bushing; the LM317's tab is +17 V. Meter check before
   power: tab to chassis open circuit.
3. **Transformer centre tap to the board's `CT` pad only**, never to a chassis lug
   (simulated: 16 mV of buzz, 300 mV with the hot preamp). An electrostatic screen, if
   the transformer has one, goes to the chassis.
4. **Speaker: both wires to the `LS1` pads.** If you add a speaker jack it must be an
   insulated one — its sleeve is the star point, not chassis.
5. **Input jacks on a metal panel: ONE sleeve wire to the board** (the panel joins the
   three sleeves; three wires would be three loops in series with the input). Insulated
   jacks: all three sleeve wires. Keep tip and sleeve wires twisted together.
6. **Reverb tank** (the 4FB2A1C grounds BOTH its connectors to the tank chassis, so two
   soldered shields close a loop — the largest in the amplifier). *SMD board:* solder
   both; the input shield's pad returns through `R_tg` (10 Ω), which opens the loop.
   *THT board:* solder only the OUTPUT cable's shield (pad 4, `G`) and leave the input
   cable's shield unconnected at the board end. Either way run the two cables together
   and away from the transformer.
7. **Pots and footswitch:** do not solder pot lugs to pot cases (the panel already
   grounds the cases), and do not tie DIN pins 4–6 to the connector shell.
8. **Mounting hardware** may be metal or nylon: the board has no copper within 3.8 mm
   of a hole centre on either face.

**THT board only — two resistors on the parts themselves** (that board has no room for
them; the SMD board carries them as `R_jb` and `R_midb`, errata #39):
- 10 MΩ across the tip and sleeve lugs of input jack 1 (DC return for the jack side of
  `C_in_pre`: no thump when a guitar is plugged in);
- 1 MΩ across the two lugs of the mid-cut toggle switch (keeps `C_res` charged while the
  switch is open: no click when it closes).
