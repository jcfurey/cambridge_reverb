# Vox Cambridge Reverb — Part 9: Transformers & Magnetic Components

> Reconstructed document — see `PROVENANCE.md`. Summarized from the project
> design record; verify specifics before purchasing magnetics.

## Power transformer T1
Test the original first (see Part 8 reuse table): secondary should read ~48 VAC.
If healthy, reuse it — it saves the biggest headache. If dead, the **AnTek
AS-0524** toroidal is a candidate replacement (verify secondary voltage/current
against the 33.5 V main rail requirement before buying).

## Eliminated audio transformers
- **Driver transformer T2** — eliminated; the LM1875 needs no phase-splitter.
- **Reverb transformer T3** — eliminated; the TL072 drives the high-impedance
  pan directly.

## Reverb pan impedance matching
Use the **Accutronics 4FB2A1C** (~1475 Ω input impedance). The 8 Ω-input
**4AB3C1B is incompatible** with the direct TL072 driver — do not substitute it.

## MRB inductor
Reuse the original ~1H inductor if its DCR reads ~50–100 Ω and it's not open.
Substitution option: Fasel wah inductors (e.g. 2× ~0.5H in series to approximate 1H).
Default MRB tuning is 600 Hz (68 nF with 1 H).
