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

`[RECONSTRUCTED]` **Corrected (roast R2):** the earlier "18 W into 8 Ω" premise is
unreachable on the 33.5 V single rail — the real output ceiling is **~12 W**. At
~12 W the LM1875's worst-case dissipation is *lower* than the old 15–20 W figure,
so with a ≤2.5 °C/W sink + mica the junction stays comfortably within limits (the
sink is over-spec'd, which is safe). Thermal shutdown backstops sustained drive.
Still verify against the LM1875 datasheet SOA/thermal curves for your duty cycle.

`[MODELLED 2026-09-07]` **Part 6c §5** puts numbers on it (`spice/tran_thermal_lm1875.cir`,
2 K/W junction-case + 1.6 K/W greased mica): worst-case continuous sine is **9.4 W** of
dissipation (at 7 W out, not at full power). Junction temperature with a **2.5 K/W** sink:
82 / 97 / 112 °C at 25 / 40 / 55 °C ambient — the spec above holds with margin. **4 K/W**
is still fine to 55 °C (126 °C); **6 K/W** passes a sine test only in a cool room (145 °C
at 55 °C); **8–10 K/W** clip-on sinks reach thermal shutdown on sustained notes. A 40 g
sink saturates in ~5 minutes (τ ≈ 145 s), so a set of loud songs equals the steady-state
sine column. Bolting the tab directly to a grounded sink (single supply: tab = GND) saves
~6 K. The LM317 now carries ~25 mA (IC3 + the tremolo LED driver): 0.4–0.5 W, +25 K bare
— still no heatsink, but chassis-mount it in a hot cabinet.

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
