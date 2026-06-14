# Vox Cambridge Reverb — Part 8: Verified In-Stock BOM

> Reconstructed document — see `PROVENANCE.md`. The availability table, the
> Digikey semiconductor rows, the JFET selection guidance, and the parts-to-reuse
> table are recovered substantially verbatim.
>
> **Stock status was accurate as of the original April 2026 search and WILL drift.
> Re-verify live stock and pricing at Digikey/Mouser before ordering.**

## Availability issues found (recovered verbatim)

| Part | Issue | Solution |
|------|-------|----------|
| 2N5457 (TO-92) | **Discontinued** in through-hole by onsemi | Use MMBF5457 (SOT-23 SMD) on adapter, or J113 through-hole |
| VTL5C1 vactrol | **Original Perkin-Elmer discontinued** (RoHS cadmium ban) | Use Xvive VTL5C1 clone, or DIY LED+LDR |
| TDA2030/TDA2050 | **Discontinued** by ST | Not in our design — we use LM1875 (still active at TI) |
| KBU4M bridge | Available but double-check | KBP410G is a common alternative, same specs |

## Verified semiconductors (recovered verbatim)

| Ref | Description | Digikey P/N | Alt | ~Price | Notes |
|-----|-------------|-------------|-----|--------|-------|
| Q1, Q2, Q_rec | N-ch JFET | MMBF5457CT-ND (SOT-23) | Mouser 863-MMBF5457 | ~$0.60 | Use SOT-23→TO-92 adapter |
| Q1, Q2, Q_rec (ALT) | N-ch JFET TH | J113-ND (TO-92) | Mouser 512-J113 | ~$0.75 | Higher Idss — adjust bias |
| IC_PA | Power amplifier | LM1875T/NOPB-ND | Mouser 926-LM1875T/NOPB | ~$4.50 | Active at TI |
| IC1, IC2 | Dual JFET op-amp | 296-1775-5-ND (TL072CP) | Mouser 595-TL072CP | ~$0.65 | DIP-8 |
| U1 | Voltage regulator | LM317T/NOPB-ND | Mouser 926-LM317T/NOPB | ~$1.50 | TO-220 |
| BR1 | Bridge rectifier | KBP410G-ND | Mouser 821-KBP410G | ~$0.55 | Or 4× 1N4007 |
| D1, D2 | Output clamp diodes | 1N4007-E3/54GICT-ND | Mouser 625-1N4007-E3 | ~$0.12 | |
| D_lfo1, D_lfo2 | Signal diodes | 1N4148FS-ND | Mouser 512-1N4148 | ~$0.05 | |
| LED_rate | 3mm red LED | 160-1127-ND | — | ~$0.15 | |

### JFET selection: MMBF5457 vs J113 (recovered verbatim)
**MMBF5457 on SOT-23 adapter (recommended for accuracy):** exact SMD equivalent
of the 2N5457 — same die, same specs. Adapter boards are pennies from JLCPCB.
Bias values in all documents target 2N5457 specs (Vp ≈ -1.8V, Idss ≈ 3mA) and
work directly. The through-hole 2N5457 has been discontinued and counterfeits
are common — avoid random eBay/Amazon listings.

## Parts to reuse from the original amp (recovered verbatim)

| Part | Condition check | Reuse if… |
|------|----------------|-----------|
| Power transformer T1 | Secondary ~48 VAC | Windings intact (no open/short) |
| Potentiometers (×6) | Rotate slowly, listen for scratch | Smooth, no crackle with signal |
| Input jacks (×3) | Tip contact spring tension | Grip the plug firmly |
| Footswitch + DIN cable | Press each button, check continuity | All 3 buttons work, cable intact |
| Speaker (10" Gold Bulldog) | Push cone gently | Moves freely, no rub/tear/burn |
| Reverb pan | Tap springs for "boing" | Springs + transducers OK |
| MRB inductor | DCR ~50–100Ω | Not open circuit |
| Chassis pan + hardware | Visual | No cracks, severe rust |
| Power switch | Click, continuity | Reliable, no intermittent |

**Estimated Digikey order:** ~$45–60 (excluding pots/optocoupler/specialty parts).
**Total project cost, all sources:** ~$80–120.
