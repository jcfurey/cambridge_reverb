# Ground-loop audit -- kicad/cambridge_reverb.kicad_pcb

## 1. Closed loops in the routed copper

86 routed nets checked (signal ground is a mesh by design and is not one of them). **None contains a closed loop.**

## 2. The big current loops, through the actual tracks

| loop | enclosed area | copper in the loop | its resistance | field at 10 cm |
|---|---:|---:|---:|---:|
| reservoir charging, half-cycle 1 | 11.4 cm2 | 158 mm | 88.1 mohm | 0.0487 uT at 0.213 A rms |
| reservoir charging, half-cycle 2 | 10.1 cm2 | 156 mm | 80.3 mohm | 0.0428 uT at 0.213 A rms |
| loudspeaker, positive half (reservoir -> IC -> speaker -> reservoir) | 10.7 cm2 | 253 mm | 130.7 mohm | 0.257 uT at 1.2 A rms |
| loudspeaker, negative half (C_out -> IC -> speaker) | 7.5 cm2 | 263 mm | 138.2 mohm | 0.1809 uT at 1.2 A rms |
| LM1875 decoupling (C_byp1) | 12.4 cm2 | 171 mm | 94.6 mohm | -- |
| Zobel (R_zobel + C_zobel) | 0.8 cm2 | 59 mm | 34.1 mohm | -- |

For scale: the mains transformer's own stray field at 10 cm is of the order of 1 uT (toroid) to 10-50 uT (EI core).

### Power ground as a star at the reservoir

1 A of charging current from the centre tap (`T1.2`) to the reservoir's minus (`C_main.2`) drops 37.1 mV along its run. How far that moves the other power-ground pads against the reservoir's minus -- the copper they share with the charging pulses:

| pad | shared with the charging path |
|---|---:|
| `IC_PA.3` | 0 mohm |
| `R_spk_rtn.2` | 0 mohm |
| `C_byp1.2` | 0 mohm |
| `C_byp2.2` | 0 mohm |
| `C_zobel.2` | 0 mohm |
| `D2.2` | 0 mohm |

Limit 2 mohm (the reservoir pad itself is about 0.1). The LM1875's tab against the star link: 0 mohm -- the voltage per ampere of charging current that a tab shorted to the chassis would put round the ground system.

## 3. Copper under the mounting hardware

Nearest plane / pour copper to a mounting-hole centre: F.Cu 3.8 mm, In1.Cu 2.15 mm, B.Cu 3.8 mm. Outer layers need 3.5 mm (a 7 mm washer); the inner plane cannot be touched.

## 4. Wiring mistakes, simulated

One off-board connection added to the board as built; same charging pulses, same speaker current.

| | hum at the speaker, idle (standard / hot preamp) | speaker current fed back through the grounds |
|---|---:|---:|
| **as built** | 25.51 / 71.93 uV | none |
| LM1875 tab bare on the chassis (IC_PA.3 - J_IN1.2 (10 mohm)) | **60.75 / 1858.81 uV** | **-42.7 dB** (-6.8 dB hot) |
| metal speaker jack on the chassis (LS1.2 - J_IN1.2 (10 mohm)) | **54.34 / 1374.38 uV** | **-49.6 dB** (-13.7 dB hot) |
| transformer centre tap also to the chassis (T1.2 - J_IN1.2 (10 mohm)) | **8067.23 / 407883.13 uV** | **-48.0 dB** (-12.1 dB hot) |
| chassis bonded twice (jacks AND the chassis pad) (TP_GND_PSU.1 - J_IN1.2 (5 mohm)) | **22.69 / 26.25 uV** | **none** (none hot) |

- *LM1875 tab bare on the chassis:* the tab is pin 3 = power ground; with the chassis also on signal ground at the jacks it bridges the star.
- *metal speaker jack on the chassis:* the speaker's return terminal reaches signal ground a second way.
- *transformer centre tap also to the chassis:* the charging pulses get a second way home, through the chassis and the input ground.
- *chassis bonded twice (jacks AND the chassis pad):* no supply current is diverted -- but it is a loop for stray fields, see the table below.

## 5. Loops that close off the board

A stray field drives a current round any closed ground loop. Reference field: 1 uT at 50 Hz through 100 cm2 of loop = 3.14 uV (a toroid at 10-15 cm; an EI core is 10-50 times that). "Hot" = with the optional source-bypass capacitors fitted.

| loop, IF it is closed | pads, resistance on the board | whole loop | per mA: in the board copper | per mA: in the off-board conductor that carries signal | at the speaker for the reference field | keep it open by |
|---|---|---:|---:|---:|---:|---|
| two input-jack sleeves joined by a metal panel | J_IN1.2 - J_IN2.2, 1.59 mohm | 11.6 mohm | 171.891 uV (4320.444 hot) | 1050.0 uV (26240.0 hot), 5 mohm | **331.07 uV** (8280.31 hot) | non-insulated jacks: ONE sleeve wire to the board (the panel joins the sleeves); insulated jacks: all three |
| input jack 1 and the FX jack sleeves joined by the panel | J_IN1.2 - J_IN3.2, 1.77 mohm | 11.8 mohm | 186.77 uV (4723.006 hot) | 1050.0 uV (26240.0 hot), 5 mohm | **330.22 uV** (8267.14 hot) | as above |
| the two reverb-tank cable shields joined at the tank (4FB2A1C: both connectors grounded) | REV1.2 - REV1.4, 1.51 mohm | 81.5 mohm | 422.93 uV (406.694 hot) | 23000.0 uV (23000.0 hot), 40 mohm | **902.8 uV** (902.18 hot) | solder only the OUTPUT cable's shield at the board (pad 4) and leave the input shield open at this end; run the two cables together |
| chassis bonded at the input jacks and again at the chassis pad | J_IN1.2 - TP_GND_PSU.1, 2.28 mohm | 12.3 mohm | 164.378 uV (5724.723 hot) | 1050.0 uV (26240.0 hot), 5 mohm | **310.62 uV** (8176.02 hot) | ONE chassis bond: the jacks if they are not insulated, otherwise the chassis pad |
| footswitch cable shield / DIN shell on the chassis | FS1.4 - J_IN1.2, 2.31 mohm | 12.3 mohm | 120.012 uV (5588.598 hot) | -- | **30.62 uV** (1425.72 hot) | DIN pins 4-6 are the pedal's commons; do not tie them to the connector shell |
| volume-pot case soldered to its ground lug (case on the panel) | POT_VOL.1 - J_IN1.2, 2.22 mohm | 12.2 mohm | 169.831 uV (5301.054 hot) | -- | **43.67 uV** (1362.99 hot) | do not solder pot lugs to pot cases; the panel already holds the cases at chassis potential |
| reverb-pot case soldered to its ground lug | POT_REV.1 - J_IN1.2, 2.45 mohm | 12.5 mohm | 51.655 uV (5488.508 hot) | -- | **13.03 uV** (1384.57 hot) | as above |
