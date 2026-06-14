# Vox Cambridge Reverb (V1031/V1032) — Electronics Rebuild

Complete electronics rebuild of a Vox Cambridge Reverb solid-state guitar amplifier:
original electronics gutted and replaced with modern components, while preserving
all original functionality, the original front/rear panel layout (no new holes),
and the original chassis. Guitar-frequency and 10" alnico speaker optimized throughout.

## Core design decisions

| Block | Replacement |
|-------|-------------|
| Power amp | LM1875T (replaces germanium push-pull; eliminates driver transformer T2) |
| Preamp JFETs | MMBF5457 (SOT-23 on adapter) or J113 (2N5457 discontinued) |
| Reverb driver / tremolo LFO | TL072CP (eliminates reverb transformer T3; drives high-Z pan directly) |
| Reverb pan | Accutronics 4FB2A1C (~1475 Ω input) — 8 Ω 4AB3C1B is **incompatible** |
| Tremolo modulation | Xvive VTL5C1 or DIY LED/LDR optocoupler |
| Power regulation | LM317T (17 V regulated preamp rail), KBP410G bridge rectifier |

## Key constraints
- No new holes in original panels; all improvements internal only
- Tremolo rate LED is PCB-mounted (diagnostic, not panel-mounted)
- MRB hardwired to 600 Hz (original spec)
- Line reverse switch position repurposed internally
- Original 6-pin DIN footswitch connector and pedal retained
- PCB sized at 155×90 mm (conservative default pending chassis measurement)

## Guitar-optimization specifics
- 100 pF presence rolloff cap at Q2 drain
- 1 nF feedback cap across LM1875 R_fb (7.2 kHz bandwidth limit)
- 470 pF treble cap for Vox chime character
- Guitar pickup model (3 H / 6 kΩ / 100 pF) with 300 pF cable capacitance
- 10" speaker model with 105 Hz mechanical resonance and voice coil inductance

## Repository layout

```
docs/         Design guide, BOM notes, wiring, fab guide, thermal, errata (Parts 1–10)
kicad/        KiCad project, schematics, PCB, symbols/, footprints/, gerbers/
spice/        LTspice simulations + models/
bom/          Bill of materials (CSV/markdown), Mouser/Digikey part numbers
datasheets/   Component datasheets (PDFs)
photos/       Chassis, panel, build progress photos
production/   JLCPCB fab packages, assembly drawings
```

## Tools
- **EDA:** KiCad
- **Simulation:** LTspice
- **PCB fab:** JLCPCB
- **Sourcing:** Mouser, Digikey

## Project status
Completed across 10 structured parts plus an errata document resolving 17
cross-document inconsistencies. See `docs/` and `CHANGELOG.md`.
