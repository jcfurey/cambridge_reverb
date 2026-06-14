# Vox Cambridge Reverb — Errata & Sanity Check

> Reconstructed document — see `PROVENANCE.md`. The original errata listed 17
> cross-document inconsistencies. Issues 1–8 below are recovered substantially
> verbatim. Issues 9–17 were not recovered in full; their topics are noted from
> the project summary and flagged `[NOT FULLY RECOVERED]` so you know to
> re-derive them if needed. The three HIGH-severity items are folded into the
> relevant reconstructed docs.

## Issue 1 — Part 1 referenced external FX-loop / headphone jacks
The user keeps the original panel with no new holes. FX loop must be internal-only
(IN3 repurposing); headphone output removed; MRB internal-only.
**Severity:** MEDIUM. *(Folded into Part 1 §7.)*

## Issue 2 — Part 1 key-improvements list mentioned external features
Change to: internal FX-loop provision (IN3), on-board tremolo rate LED
(diagnostic, not panel), remove headphone output.
**Severity:** LOW.

## Issue 3 — Bridge rectifier naming (KBU4M vs KBP410G)
Both are 4A/1000V; different packages (KBP410 inline 4-pin, KBU4M SIP 4-pin).
PCB footprint should accommodate both. Part 8 prefers KBP410G for availability.
**Severity:** LOW.

## Issue 4 — Part 2 listed 2N5457 TO-92 (discontinued) — HIGH
Through-hole 2N5457 is discontinued; the Mouser P/N would show no stock. Primary
options are MMBF5457 on adapter or J113; keep 2N5457 only "if you find genuine."
**Severity:** HIGH. *(Folded into Parts 1, 2, 8.)*

## Issue 5 — Part 1 listed TIP41C/TIP42C discrete output as an option
The rest of the suite assumes the LM1875 as the sole power amp. Clarify the
discrete stage is reference-only, not developed (no BOM/SPICE/wiring).
**Severity:** MEDIUM. *(Folded into Part 1 §3.)*

## Issue 6 — Part 1 mentioned LM13700 OTA tremolo modulator
No BOM/SPICE/wiring exists for it; LED/LDR (VTL5C1) is used throughout. Note as
an undocumented advanced alternative.
**Severity:** LOW.

## Issue 7 — Part 2 said 2200µF output cap was "only for discrete output" — HIGH
The LM1875 in single-supply mode ALSO requires the 2200µF output coupling cap.
Remove the qualifier.
**Severity:** HIGH. *(Folded into Part 2 BOM + Part 1 §3.)*

## Issue 8 — Part 1 §6 described MRB with a panel rotary switch
Implies a new panel control. Default is hardwired 600 Hz; any selector is
internal-only (inside chassis or repurposing the line-reverse switch).
**Severity:** MEDIUM. *(Folded into Part 1 §6.)*

## Issues 9–17 — `[NOT FULLY RECOVERED]`
The original document resolved 17 issues total. Issues 9–17 were not recovered
verbatim. Based on the project record, remaining checks likely covered: cross-doc
agreement on the reverb pan part number (4FB2A1C vs the incompatible 4AB3C1B),
the regulated-rail value (17V) consistency, board-dimension consistency between
Parts 4/5/7 (190×115 vs 155×90), and consistent JFET bias values across Part 2
and the SPICE files. **Re-run a consistency pass** against the reconstructed docs
before fabrication.
