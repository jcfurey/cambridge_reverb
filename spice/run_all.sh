#!/usr/bin/env bash
# Run all ngspice block simulations in batch and print the key measured numbers.
# Requires: ngspice (apt install ngspice). Run from the spice/ directory.
set -u
cd "$(dirname "$0")"

fail=0
# Run a sim, print its key measured lines, and fail the script if ngspice itself
# errors (piping straight to grep would hide ngspice's non-zero exit status).
run() {
  echo "=== $1 ==="
  local out rc
  out="$(ngspice -b "$1" 2>&1)"; rc=$?
  printf '%s\n' "$out" | grep -E "= " | grep -viE "warning|note" || true
  if [ "$rc" -ne 0 ]; then echo "  !! ngspice FAILED on $1 (exit $rc)"; fail=1; fi
  echo
}

run dc_preamp_jfet.cir
run ac_reverb_driver.cir
run ac_mrb.cir
run tran_tremolo_lfo.cir
run ac_power_amp_lm1875.cir
run tran_reverb_mixer.cir
run ac_tonestack.cir
run tran_classa_output.cir

exit "$fail"
