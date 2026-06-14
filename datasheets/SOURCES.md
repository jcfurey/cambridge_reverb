# Datasheet sources

PDFs are **not committed** to the repo (licensing + binary bloat). Download the
current revision for each part from the manufacturer before finalizing values.
Drop the PDFs in this folder locally; they are covered by `.gitignore` patterns
only if you choose to ignore them — otherwise keep them out of version control.

| Part | Used for | Manufacturer | Where to get the datasheet |
|------|----------|--------------|----------------------------|
| LM1875T/NOPB | Power amplifier | Texas Instruments | ti.com → "LM1875" (product page → Technical documents) |
| LM317T/NOPB | 17 V rail regulator | Texas Instruments | ti.com → "LM317" |
| TL072CP | Reverb driver + tremolo LFO | Texas Instruments | ti.com → "TL072" |
| MMBF5457 | Preamp / reverb JFET (SMD) | onsemi | onsemi.com → "MMBF5457" |
| J113 | Preamp / reverb JFET (TH alt) | onsemi / Fairchild | onsemi.com → "J113" |
| 1N4007 | Output clamp / rectifier | onsemi / Vishay | onsemi.com → "1N4007" |
| 1N4148 | LFO amplitude clamp | onsemi / Vishay | onsemi.com → "1N4148" |
| KBP410G | Bridge rectifier | Comchip / multiple | distributor product page (Digikey KBP410G-ND) |
| Xvive VTL5C1 | Tremolo optocoupler | Xvive (PerkinElmer clone) | xvive.com / Amplified Parts product page |
| Accutronics 4FB2A1C | Reverb pan (high-Z input) | Belton / Accutronics | belton.co.kr / amplifiedparts reverb tank guide |
| AnTek AS-0524 | Optional T1 replacement | AnTek | antekinc.com → "AS-0524" |

## Reverb-pan code reminder
The Accutronics/Belton 4-digit-plus code encodes the tank: confirm the part is
**4FB2A1C** (high-impedance input ~1475 Ω) and **not** 4AB3C1B (8 Ω input,
incompatible with the direct TL072 driver — see Part 9 / errata Issue 14). The
decoder is in the Accutronics "reverb tank" application note.

## Verification reminder
Stock and part status were current as of the original April 2026 search and
**will drift** (see Part 8). Re-check live availability at Digikey/Mouser and
confirm the JFET and bridge selections before ordering.
