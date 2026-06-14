# Provenance & reconstruction note

The original Part 1–10 deliverables and errata were generated as downloadable
files in a prior conversation ("Rebuilding Vox Cambridge Reverb solid state amp").
Those original files were not retained.

The documents in this folder were **reconstructed** from:
- Verbatim fragments recovered from that conversation's history (BOM tables,
  schematics, netlist notes, errata issues, SPICE netlist, JLCPCB settings, etc.),
- The project summary of design decisions and constraints.

**What this means for you, the builder:**
- Content recovered verbatim is reliable and matches what was originally produced.
- Where a section was only partially recovered, gaps were filled to keep the
  document coherent. These spots are flagged with `[RECONSTRUCTED]`.
- **Before committing to a board run or parts order, re-verify:** all part
  numbers and live stock status (Part 8), exact component values against the
  errata corrections, and any value you do not see corroborated in the SPICE
  netlist or KiCad netlist notes.
- The errata's three HIGH-severity items are folded into the relevant docs:
  (1) JFET is MMBF5457/J113, not through-hole 2N5457; (2) the 2200µF output
  coupling cap IS required for the LM1875 single-supply design; (3) MRB is
  hardwired 600Hz by default with no new panel holes.

Source conversation: https://claude.ai/chat/0fadd454-0a08-4d0d-b038-77c152ef5d69
