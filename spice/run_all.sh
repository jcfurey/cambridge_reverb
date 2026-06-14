#!/usr/bin/env bash
# Run all ngspice block simulations in batch and print the key measured numbers.
# Requires: ngspice (apt install ngspice). Run from the spice/ directory.
set -u
cd "$(dirname "$0")"

run() { echo "=== $1 ==="; ngspice -b "$1" 2>&1 | grep -E "= " | grep -viE "warning|note"; echo; }

run dc_preamp_jfet.cir
run ac_reverb_driver.cir
run ac_mrb.cir
run tran_tremolo_lfo.cir
run ac_power_amp_lm1875.cir
