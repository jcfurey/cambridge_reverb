# Vox Cambridge Reverb V1031/V1032 — Part 1: Modernized Rebuild Guide

> Reconstructed document — see `PROVENANCE.md`. Design philosophy and the
> power-amp section are recovered substantially verbatim; some surrounding prose
> is `[RECONSTRUCTED]` to keep the guide coherent.

## Original amp summary

| Parameter | Original spec |
|-----------|--------------|
| Model | V1031 (1966), V1032 (1967, adds E-Tuner) |
| Power | 18 W RMS into 8 Ω |
| Topology | Single-channel, 3 inputs, OTL output |
| Output devices | Matched germanium PNP pair (NTE-121MP equivalent) |
| Driver | 2N2219 silicon NPN in TO-3, through driver transformer (T2) |
| Preamp | Discrete bipolar transistors on PCB 25-5274-2 |
| Power supply | 33.5 VDC main, taps at 27 V and 17 V; full-wave rectifier, center-tapped transformer |
| Effects | Reverb (2-spring pan), Tremolo, MRB (~600 Hz mid boost) |
| Speaker | 10" Oxford "Gold Bulldog" alnico |
| Footswitch | 3-button: Reverb, Tremolo, MRB |

## Modernization philosophy

The goal is to preserve the original signal-path topology and tonal character
while replacing every component with modern, reliable, higher-performance parts.
All improvements are internal only — the original front and rear panels are
preserved exactly, with no new holes drilled.

Key improvements over the original:
- LM317-regulated 17 V preamp rail (the single biggest noise reduction over the original)
- Continuous bottom-layer ground plane (the original board had none)
- Elimination of the germanium output stage and both audio transformers (driver T2, reverb T3)
- Internal effects-loop provision (via IN3 jack repurposing)
- On-board tremolo rate LED (diagnostic, not panel-mounted)

## Section 1: Power supply — modernized

KBP410G bridge rectifier feeding the 33.5 V main rail; 27 V tap via a dropper
resistor; 17 V preamp rail regulated by an LM317T. Rectifier snubbing caps
across the diodes. The LM317 on the 17 V rail is the most impactful single
change for noise. (Full values in Part 2.)

## Section 2: Preamp — modernized

JFET common-source stages replace the original discrete bipolar preamp. JFETs
clip softly (tube-like), present very high input impedance for guitar pickups,
and self-bias easily. The Vox "top boost" voicing comes from the tone-stack
values, which are preserved.

**JFET device:** the through-hole 2N5457 is **discontinued** (see Part 8). Use
the **MMBF5457** (SOT-23, exact same die) on a SOT-23→TO-92 adapter, or the
through-hole **J113** with adjusted bias. The bias values throughout these
documents target 2N5457 specs (Vp ≈ -1.8 V, Idss ≈ 3 mA) and work directly with
the MMBF5457.

## Section 3: Power amplifier — modernized

### Original circuit
Driver transistor Q7 (2N2219 silicon NPN) → driver transformer T2 (phase
splitter) → 2× germanium PNP output transistors in push-pull OTL configuration.

### Modernized design
**Eliminate the driver transformer entirely.** The selected design uses a
monolithic power amplifier IC.

**LM1875 implementation (the design used throughout this document set):**
```
Pin 1 (Non-inv input) ← from preamp/reverb blend through 1µF coupling cap
  Input biased to V+/2 through resistor divider (2× 22kΩ)
Pin 2 (Inv input) ← feedback network
  R_feedback = 22kΩ (from output to pin 2)
  R_ground = 1kΩ (from pin 2 to ground through 22µF cap)
  Gain = 1 + 22k/1k = ~23x (adjustable)
Pin 3: V- (ground in single-supply)
Pin 4: Output → 2200µF/35V coupling cap → speaker
Pin 5: V+ (connect to +33.5V main rail)

Zobel: 10Ω + 100nF across output to ground
Bypass: 100nF + 10µF on each supply pin to ground
```
The IC includes thermal shutdown, short-circuit protection, and SOA limiting.
Mount it on the existing heatsink bracket under the chassis where the germanium
transistors were.

> **Note on alternatives:** A discrete TIP41C/TIP42C complementary output stage
> was mentioned during design as a reference alternative for "vintage" breakup,
> but it is **not** carried through the rest of the document set (no BOM, SPICE,
> or wiring). All Parts 2–10 are built around the LM1875. Treat the discrete
> output as a separate development effort not covered here. (Errata Issue 5.)

## Section 4: Reverb — modernized

A TL072 op-amp drives the reverb pan directly; the original reverb transformer
T3 is eliminated. A JFET recovery amp provides the high input impedance for the
return. The pan must be the high-impedance **Accutronics 4FB2A1C (~1475 Ω input)**
— the 8 Ω-input 4AB3C1B is incompatible with the direct TL072 driver. (Detail
in Part 2 / Part 9.)

## Section 5: Tremolo — modernized

A Wien-bridge LFO (TL072 half) drives an LED/LDR optocoupler (**Xvive VTL5C1**
or DIY LED+LDR; original Perkin-Elmer vactrols are discontinued under RoHS
cadmium restrictions). The LFO output also drives an on-board diagnostic rate
LED. Speed and depth pots use the original panel positions.

## Section 6: MRB (Mid Resonance Boost)

A parallel LC tank using the original-style inductor. Default is **hardwired at
600 Hz** (original spec); the line-reverse switch position is available for
internal repurposing if a multi-frequency selector is desired later — but no new
panel holes. (Errata Issue 8.)

## Section 7: Added features (internal only)

- **Effects loop:** internal-only provision via IN3 jack repurposing; switching
  jacks normal the dry path when nothing is inserted.
- **Tremolo rate LED:** on-board diagnostic, not panel-mounted.
- Headphone output described in early drafts was **removed** (would require a
  new panel hole). (Errata Issues 1–2.)

## Safety

- **Always discharge filter capacitors** before working on the circuit (10 kΩ/5 W resistor across each cap).
- **Never work on the amp with power applied** unless experienced with live-chassis work and using one hand only.
- **Install a proper 3-wire grounded power cord** if the original was 2-prong; bond the safety ground to the chassis.
- A ground-lift, if used for hum, must keep the chassis grounded through a 100 nF/400 V safety capacitor.

## Appendix: schematic resources
- Original V1031 schematic: schematicheaven.net (free PDF)
- GeoFEX repair-board documentation: geofex.com
- Vox Showroom: voxshowroom.com (under-the-hood photos)
- Reverb.com schematic package: high-resolution factory scans
