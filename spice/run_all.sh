#!/usr/bin/env bash
# Run every ngspice netlist -- the fixed-point block checks and the parameter
# SWEEPS -- and save each one's result table to results/<name>.txt (committed as
# the evidence for the numbers in README.md). Prints the key lines as it goes and
# fails if ngspice itself errors. Requires ngspice (apt install ngspice).
set -u
cd "$(dirname "$0")"
mkdir -p results
fail=0
# lines of ngspice chatter that carry no result
NOISE='^\s*$|Note:|Warning:|Doing analysis|Reference value|No\. of Data|^\*\*|Circuit:|ngspice-|Using SPARSE|Initial Transient|^Total|^Program|CPU time|elapsed|Reset re-loads|^Node |^----|^[a-z0-9#._]+\s+-?[0-9.e+-]+$|Using transient|^binary raw|^[a-z0-9_]+\s+=\s.*(from|at)=|^Harmonic|^ [0-9]\s|^-------- '
run() {   # run <netlist> [grep-pattern for the printed summary]
  local f=$1 pat=${2:-"= "} out rc
  echo "=== $f ==="
  out="$(ngspice -b "$f" 2>&1)"; rc=$?
  printf '%s\n' "$out" | grep -vE "$NOISE" > "results/${f%.cir}.txt"
  grep -E "$pat" "results/${f%.cir}.txt" | grep -viE "warning|note|error" | head -40
  if [ "$rc" -ne 0 ]; then echo "  !! ngspice FAILED on $f (exit $rc)"; fail=1; fi
  echo
}
# --- fixed-point block checks ---
run dc_preamp_jfet.cir
run ac_reverb_driver.cir
run ac_mrb.cir
run tran_tremolo_lfo.cir
run ac_power_amp_lm1875.cir
run tran_reverb_mixer.cir
run ac_tonestack.cir
run tran_classa_output.cir "= |THD"
# --- parameter sweeps (tables) ---
run sweep_preamp_bias.cir        "^[0-9R]"
run sweep_tonestack.cir          "^[0-9p]"
run sweep_lfo_speed.cir          "^[0-9p]"
run sweep_lfo_speed_recovered.cir "^[0-9p]"
run sweep_classa_bias.cir        "^(ROW|vb)|THD"
run sweep_pa_headroom.cir        "^[0-9V]"
echo "results written to spice/results/ (exit $fail)"
exit "$fail"
