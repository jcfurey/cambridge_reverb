#!/usr/bin/env bash
# Rebuild one board from the generator to the order package, and verify it:
#
#   kicad/gen/build.sh smd      # schematic -> placed board -> BOM -> autoroute -> finish -> ground
#   kicad/gen/build.sh tht      #   stitching -> ERC/DRC reports -> crosstalk + ground / parasitics
#                               #   audits -> (smd) JLCPCB package -> verify.py (which also runs
#                               #   the ground-RETURN audit: kicad/reports/ground-<profile>.md)
#
# Needs kicad-cli 8, python3 with pcbnew + numpy + scipy, Java and kicad/gen/freerouting.jar
# (Freerouting 1.9.0, see route_board.py), xvfb-run when there is no display, ngspice.
# About ten minutes per routing attempt, nearly all of it the autorouter. Exit code = verify.py's.
#
# Freerouting's result differs from run to run, and now and then it boxes a small pad in
# with its own traces so that finish_routes.py cannot reach it any more (seen 2026-11-12:
# the bias divider's +33V5 pad behind a PA_OUT trace). The route is therefore ATTEMPTED
# with one via cost after another until the board is complete; VIA_COST="50" pins one.
set -euo pipefail
cd "$(dirname "$0")/../.."
P=${1:-smd}
case "$P" in
  smd) PCB=kicad/smd/cambridge_reverb_smd.kicad_pcb; VIAS=${VIA_COST:-"50 60 40 70"}; BOMF="--jlc";;
  tht) PCB=kicad/cambridge_reverb.kicad_pcb;         VIAS=${VIA_COST:-"60 50 40 70"}; BOMF="";;
  *) echo "profile must be smd or tht"; exit 2;;
esac
q() { grep -vE '^$|Debug:' || true; }
open_links() {   # open connections + DRC errors of the board as KiCad counts them
  local t; t=$(mktemp --suffix=.json)
  kicad-cli pcb drc --severity-all --format json -o "$t" "$PCB" >/dev/null 2>&1 || true
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d.get('unconnected_items', [])) + sum(1 for v in d.get('violations', []) if v['severity'] == 'error'))" "$t"
  rm -f "$t"
}
echo "== generate [$P]"
python3 kicad/gen/gen_kicad.py --profile "$P" | tail -1
python3 kicad/gen/gen_pcb.py --profile "$P" 2>&1 | q
python3 kicad/gen/gen_bom.py --profile "$P" $BOMF | q
PLACED=$(mktemp --suffix=.kicad_pcb); cp "$PCB" "$PLACED"
for VIA in $VIAS; do
  cp "$PLACED" "$PCB"
  echo "== autoroute (Freerouting, via cost $VIA)"
  python3 kicad/gen/route_board.py --in "$PCB" --via-cost "$VIA" --passes 150 2>&1 | q | tail -4
  echo "== finish the open links"
  python3 kicad/gen/finish_routes.py --in "$PCB" 2>&1 | q || true
  N=$(open_links)
  [ "$N" = 0 ] && break
  echo "   $N open connection(s) / error(s) left with via cost $VIA -- routing again with the next setting"
done
rm -f "$PLACED"
echo "== stitch the grounds"
python3 kicad/gen/stitch.py --in "$PCB" 2>&1 | q
echo "== reports"
bash kicad/gen/check.sh "$P" --no-regen | q
python3 kicad/gen/crosstalk_audit.py --board "$PCB" --md "kicad/reports/crosstalk-$P.md" 2>&1 | q | tail -2
python3 kicad/gen/rf_audit.py --board "$PCB" --md "kicad/reports/rf-$P.md" 2>&1 | q | grep -E "^Lowest|Tracks on" || true
if [ "$P" = smd ]; then
  echo "== JLCPCB package"
  python3 kicad/gen/fab_jlcpcb.py 2>&1 | q
fi
echo "== verify"
python3 kicad/gen/verify.py "$P" 2>&1 | q
