#!/usr/bin/env bash
# Rebuild one board from the generator to the order package, and verify it:
#
#   kicad/gen/build.sh smd      # schematic -> placed board -> BOM -> autoroute -> finish -> ground
#   kicad/gen/build.sh tht      #   stitching -> ERC/DRC reports -> crosstalk + ground / parasitics
#                               #   audits -> (smd) JLCPCB package -> verify.py
#
# Needs kicad-cli 8, python3 with pcbnew + numpy + scipy, Java and kicad/gen/freerouting.jar
# (Freerouting 1.9.0, see route_board.py), xvfb-run when there is no display, ngspice.
# About ten minutes per board, nearly all of it the autorouter. Exit code = verify.py's.
set -eu
cd "$(dirname "$0")/../.."
P=${1:-smd}
case "$P" in
  smd) PCB=kicad/smd/cambridge_reverb_smd.kicad_pcb; VIA=${VIA_COST:-60}; BOMF="--jlc";;
  tht) PCB=kicad/cambridge_reverb.kicad_pcb;         VIA=${VIA_COST:-50}; BOMF="";;
  *) echo "profile must be smd or tht"; exit 2;;
esac
q() { grep -vE '^$|Debug:' || true; }
echo "== generate [$P]"
python3 kicad/gen/gen_kicad.py --profile "$P" | tail -1
python3 kicad/gen/gen_pcb.py --profile "$P" 2>&1 | q
python3 kicad/gen/gen_bom.py --profile "$P" $BOMF | q
echo "== autoroute (Freerouting, via cost $VIA)"
python3 kicad/gen/route_board.py --in "$PCB" --via-cost "$VIA" --passes 150 2>&1 | q | tail -4
echo "== finish the open links"
python3 kicad/gen/finish_routes.py --in "$PCB" 2>&1 | q || true
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
