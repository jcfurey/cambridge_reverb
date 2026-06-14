# Vox Cambridge Reverb — Part 5: Thermal, Placement & Assembly

> Reconstructed document — see `PROVENANCE.md`. Thermal conclusions, the floor
> plan, and the build timeline are recovered substantially verbatim; some
> numeric derivations are `[RECONSTRUCTED]`.

## Thermal — bottom line (recovered verbatim)

**LM1875 needs a heatsink rated ≤ 2.5 °C/W.** The original V1031 heatsink
bracket should work — it was designed for germanium transistors dissipating
comparable heat. Mount the LM1875 with a mica insulator, shoulder bushing, and
thermal grease.

**LM317 needs no heatsink** — it dissipates ~0.25 W powering the preamp. Bolt it
to the chassis if convenient, but thermally it's a non-issue.

`[RECONSTRUCTED]` Worst-case LM1875 dissipation at 18 W into 8 Ω is on the order
of ~15–20 W; with a junction-to-case path plus a ≤2.5 °C/W sink and mica
insulator, junction temperature stays within the device limit at normal playing
levels. Verify against the LM1875 datasheet SOA/thermal curves for your duty cycle.

## Component placement floor plan (recovered verbatim)
```
+-------------------------------------------------------------+
|  190 mm                                                     |
|  +---------+----------+----------+----------+----------+     |
|  | INPUT / |  TONE    | REVERB / |  POWER   |  POWER   |  ^  |
|  | PREAMP  |  STACK   | TREMOLO  |  AMP     | SUPPLY   | 115 |
|  | Q1,Q2   | passives | TL072s   | (LM1875) | BR1,U1   | mm  |
|  |         |          | VTL1     |          | C_main   |  v  |
|  +---------+----------+----------+----------+----------+     |
|  o o o o o o o o o WIRING EDGE (all pads) o o o o o ...      |
+-------------------------------------------------------------+
```
Signal flows left → right. All off-board wiring exits one edge so the board can
flip up for service.

## Keep-out zones (recovered verbatim)
- 10 mm clearance around LM1875 and LM317 mounting area
- No signal traces within 15 mm of transformer wiring pads
- No traces under LFO timing components (noise sensitive)

## Suggested build timeline (recovered verbatim)

| Week | Task |
|------|------|
| 1 | Photograph and document original amp. Test transformer. Remove original PCB. |
| 2 | Create KiCad schematic (Part 2 reference). Run ERC. |
| 3 | PCB layout in KiCad (Parts 4 & 5). Run DRC. |
| 4 | Order PCBs from JLCPCB. Order components from Mouser. |
| 5 | (Wait for delivery — 7–14 days.) |
| 6 | Populate power supply first. Test DC rails. |
| 7 | Populate preamp and tone stack. Test with signal generator. |
| 8 | Populate reverb, tremolo, MRB. Test each effect. |
| 9 | Populate power amp. Test at low volume with series light bulb. |
| 10 | Install PCB in chassis. Wire control and rear panels. |
| 11 | Final testing, biasing, burn-in at full volume. |
| 12 | Button it up, play it, enjoy it. |
