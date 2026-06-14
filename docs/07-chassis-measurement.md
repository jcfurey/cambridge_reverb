# Vox Cambridge Reverb — Part 7: Chassis Measurement & PCB Sizing

> Reconstructed document — see `PROVENANCE.md`. The "safe approach" summary is
> recovered substantially verbatim.

## The safe approach (recovered verbatim)
1. **Measure first, design second.** Don't assume any dimensions.
2. **Subtract 15 mm from each dimension** for guaranteed clearance.
3. **155 × 90 mm is the "safe bet"** if you can't measure yet — it will fit.
4. **Check vertical clearance** for the tallest component (main filter cap).
5. **Use nylon standoffs** for clean, insulated mounting.
6. **All wiring on one edge** so the board can flip up for service.
7. **Photograph everything** before, during, and after.

## Why no published dimension
No published dimensions exist for this chassis — every surviving amp differs
slightly from 1960s stamped-steel manufacturing. Measure your specific chassis
and fill in a measurement table before finalizing the Edge.Cuts outline.

## The main-filter-cap gotcha
The original ~5000µF cap was mounted vertically on the chassis pan, not the PCB.
If you want it on the PCB, measure clearance to the control panel above. If
tight, split into 2× 2200µF side by side or use a horizontal-mount cap.
