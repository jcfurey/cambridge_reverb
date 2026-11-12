# Ground-loop audit -- kicad/smd/cambridge_reverb_smd.kicad_pcb

## 1. Closed loops in the routed copper

88 routed nets checked (signal ground is a mesh by design and is not one of them). **None contains a closed loop.**

## 2. The big current loops, through the actual tracks

| loop | enclosed area | copper in the loop | its resistance | field at 10 cm |
|---|---:|---:|---:|---:|
| reservoir charging, half-cycle 1 | 5.2 cm2 | 161 mm | 80.2 mohm | 0.0222 uT at 0.213 A rms |
| reservoir charging, half-cycle 2 | 2.9 cm2 | 138 mm | 71.9 mohm | 0.0122 uT at 0.213 A rms |
| loudspeaker, positive half (reservoir -> IC -> speaker -> reservoir) | 4.4 cm2 | 292 mm | 168.2 mohm | 0.1051 uT at 1.2 A rms |
| loudspeaker, negative half (C_out -> IC -> speaker) | 6.1 cm2 | 243 mm | 157.9 mohm | 0.1454 uT at 1.2 A rms |
| LM1875 decoupling (C_byp1) | 0.3 cm2 | 57 mm | 29.0 mohm | -- |
| Zobel (R_zobel + C_zobel) | 1.3 cm2 | 70 mm | 41.4 mohm | -- |

For scale: the mains transformer's own stray field at 10 cm is of the order of 1 uT (toroid) to 10-50 uT (EI core).

### Power ground as a star at the reservoir

1 A of charging current from the centre tap (`T1.2`) to the reservoir's minus (`C_main.2`) drops 23.2 mV along its run. How far that moves the other power-ground pads against the reservoir's minus -- the copper they share with the charging pulses:

| pad | shared with the charging path |
|---|---:|
| `IC_PA.3` | 0 mohm |
| `R_spk_rtn.2` | 0 mohm |
| `C_byp1.2` | 0 mohm |
| `C_byp2.2` | 0 mohm |
| `C_zobel.2` | 0 mohm |
| `D2.2` | 0 mohm |
| `TP_PGND.1` | 0 mohm |

Limit 2 mohm (the reservoir pad itself is about 0.1). The LM1875's tab against the star link: 0 mohm -- the voltage per ampere of charging current that a tab shorted to the chassis would put round the ground system.

## 3. Copper under the mounting hardware

Nearest plane / pour copper to a mounting-hole centre: F.Cu 3.8 mm, In1.Cu 2.15 mm, B.Cu 3.8 mm. Outer layers need 3.5 mm (a 7 mm washer); the inner plane cannot be touched.

## 4. Wiring mistakes, simulated

One off-board connection added to the board as built; same charging pulses, same speaker current.

| | hum at the speaker, idle (standard / hot preamp) | speaker current fed back through the grounds |
|---|---:|---:|
| **as built** | 12.69 / 21.24 uV | none |
| LM1875 tab bare on the chassis (IC_PA.3 - J_IN1.2 (10 mohm)) | **89.01 / 2053.58 uV** | **-33.1 dB** (-6.1 dB hot) |
| metal speaker jack on the chassis (LS1.2 - J_IN1.2 (10 mohm)) | **68.83 / 1594.43 uV** | **-44.2 dB** (-17.2 dB hot) |
| transformer centre tap also to the chassis (T1.2 - J_IN1.2 (10 mohm)) | **10702.88 / 218597.81 uV** | **-35.2 dB** (-8.2 dB hot) |
| chassis bonded twice (jacks AND the chassis pad) (J_CHS.1 - J_IN1.2 (5 mohm)) | **12.6 / 19.21 uV** | **none** (none hot) |

- *LM1875 tab bare on the chassis:* the tab is pin 3 = power ground; with the chassis also on signal ground at the jacks it bridges the star.
- *metal speaker jack on the chassis:* the speaker's return terminal reaches signal ground a second way.
- *transformer centre tap also to the chassis:* the charging pulses get a second way home, through the chassis and the input ground.
- *chassis bonded twice (jacks AND the chassis pad):* no supply current is diverted -- but it is a loop for stray fields, see the table below.

## 5. Loops that close off the board

A stray field drives a current round any closed ground loop. Reference field: 1 uT at 50 Hz through 100 cm2 of loop = 3.14 uV (a toroid at 10-15 cm; an EI core is 10-50 times that). "Hot" = with the optional source-bypass capacitors fitted.

| loop, IF it is closed | pads, resistance on the board | whole loop | per mA: in the board copper | per mA: in the off-board conductor that carries signal | at the speaker for the reference field | keep it open by |
|---|---|---:|---:|---:|---:|---|
| two input-jack sleeves joined by a metal panel | J_IN1.2 - J_IN2.2, 1.72 mohm | 11.7 mohm | 190.135 uV (4762.539 hot) | 1050.0 uV (26240.0 hot), 5 mohm | **332.39 uV** (8309.52 hot) | non-insulated jacks: ONE sleeve wire to the board (the panel joins the sleeves); insulated jacks: all three |
| input jack 1 and the FX jack sleeves joined by the panel | J_IN1.2 - J_IN3.2, 1.95 mohm | 11.9 mohm | 226.704 uV (5571.702 hot) | 1050.0 uV (26240.0 hot), 5 mohm | **335.65 uV** (8363.37 hot) | as above |
| the two reverb-tank cable shields joined at the tank (4FB2A1C: both connectors grounded) | REV1.2 - REV1.4, 10056.66 mohm | 10136.7 mohm | 501.655 uV (507.543 hot) | 23000.0 uV (23000.0 hot), 40 mohm | **7.28 uV** (7.29 hot) | solder only the OUTPUT cable's shield at the board (pad 4) and leave the input shield open at this end; run the two cables together |
| chassis bonded at the input jacks and again at the chassis pad | J_IN1.2 - J_CHS.1, 2.52 mohm | 12.5 mohm | 251.572 uV (5681.832 hot) | 1050.0 uV (26240.0 hot), 5 mohm | **326.53 uV** (8008.39 hot) | ONE chassis bond: the jacks if they are not insulated, otherwise the chassis pad |
| footswitch cable shield / DIN shell on the chassis | FS1.4 - J_IN1.2, 2.37 mohm | 12.4 mohm | 242.535 uV (5678.381 hot) | -- | **61.59 uV** (1442.1 hot) | DIN pins 4-6 are the pedal's commons; do not tie them to the connector shell |
| volume-pot case soldered to its ground lug (case on the panel) | POT_VOL.1 - J_IN1.2, 2.5 mohm | 12.5 mohm | 213.063 uV (5702.853 hot) | -- | **53.57 uV** (1433.74 hot) | do not solder pot lugs to pot cases; the panel already holds the cases at chassis potential |
| reverb-pot case soldered to its ground lug | POT_REV.1 - J_IN1.2, 2.53 mohm | 12.5 mohm | 182.783 uV (5627.765 hot) | -- | **45.81 uV** (1410.59 hot) | as above |
