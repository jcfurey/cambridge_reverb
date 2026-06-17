# Class-A power amp — "what it wanted to be" (exploration)

Running the power amp in **Class A** for an AC15-style voice. This note has the
real numbers (simulated) and the honest trade. **Status: explored, not yet built
into the main design** — it's a real architectural change with thermal
consequences (see the question at the end).

## Why it's worth it (the tone)
`spice/tran_classa_output.cir` (transistor-level, single +33.5 V rail, ~0.7 W into
8 Ω) compares the output stage at AB vs Class-A bias:

| Mode | Idle current | THD @ ~0.7 W | What you hear |
|------|-------------:|-------------:|---------------|
| Class **AB** (small idle) | ~0.11 A | **1.05 %** | crossover notch — the SS "stiffness" |
| Class **A** (idle ≥ peak load I) | ~0.49 A | **0.0025 %** | no crossover — smooth, even-harmonic compression |

That ~400× drop in distortion (the crossover region simply vanishes) is exactly
the smooth, compressed, "chimey" character people chase in an AC15. For a guitar
amp the magic is at **low-to-mid volume**, which is precisely where Class A lives.

## The catch (the heat) — Class A is a furnace
Class A draws its full idle current **continuously, signal or not**. On a single
33.5 V rail an idle of ~0.5 A is:

- **~16 W of continuous heat** at idle…
- …for a **Class-A output ceiling of only ~1 W** into 8 Ω (`P = I_A²·R/2`).
  Above ~1 W it slides into Class AB — so you get **pure Class A up to ~1 W,
  then AB up to the ~12 W ceiling** (roast R2). That sliding behaviour is actually
  *ideal* for guitar: Class-A sparkle where you play, full power on tap for loud.

**True 15 W of Class A is not happening in this chassis** — it would be 60 W+ of
continuous heat and need a much bigger rail, transformer, and heatsink. The
buildable, authentic move is **"Class A for the first watt, AB beyond."**

## Recommended implementation: Class-A-biased LM1875 (keep the chipamp)
Add a **constant-current sink** (~0.5 A) from the LM1875 output to ground. The
LM1875's upper (sourcing) transistor then conducts continuously (it always feeds
the CCS), so the stage runs **single-ended Class A up to ±I_A load current**, then
reverts to push-pull AB. Minimal change; keeps the existing supply, gain network,
and output cap.

- **CCS as an LM317 current source** (recognizable, robust): `I_A = 1.25 / R_set`,
  so `R_set ≈ 2.5 Ω (2 W)` for 0.5 A. The LM317 sinks 0.5 A at ~15 V ≈ **7.5 W**;
  the LM1875 idle adds ~**8.4 W** → heat **splits across two devices** (each on its
  own sink → far easier than 16 W in one package). A transistor/MOSFET CCS works
  too.
- **Heatsink:** the existing ≤2.5 °C/W bracket is *marginal* at this dissipation
  (Tj ≈ 130 °C worst-case in a warm room). Recommend **≤1.5 °C/W** per device, or
  accept it runs hot and lower `I_A` (less Class A, less heat). The original
  germanium amp ran warm too — this is in that spirit but warmer.
- **Supply/transformer:** the ~50 VA / ~1 A transformer can feed ~0.5 A of standing
  current plus program; more Class A (higher `I_A`) needs a beefier transformer.

## Knobs / variants
- **`I_A` sets the Class-A window vs heat:** 0.3 A ≈ 0.4 W Class A / ~10 W heat;
  0.5 A ≈ 1 W / ~16 W; 0.75 A ≈ 2.3 W / ~25 W (needs real cooling).
- **Discrete purist option:** a JLH-1969-style discrete Class-A amp is the classic
  "proper" route, but it's ~1.5 A standing (40 W+ heat) for ~10 W and needs a
  bigger supply — a different build, noted for completeness.
- **Switchable:** a panel/internal switch could disable the CCS (back to AB/cool)
  vs enable Class A — but "no new holes," so it'd be an internal jumper.

## Verification
`spice/tran_classa_output.cir` (in `run_all.sh`): AB THD ~1.05 % with ~0.11 A
idle; Class A THD ~0.0025 % with ~0.49 A idle. Heat budget computed above from the
0.49 A standing current.
