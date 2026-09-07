#!/usr/bin/env bash
# Regenerate one build profile (schematic + placed PCB + BOM) and verify it:
#   ERC (kicad-cli sch erc) and DRC (kicad-cli pcb drc, --severity-all) reports go to
#   kicad/reports/<profile>-{erc,drc}.{rpt,json} -- the committed evidence for the
#   numbers quoted in kicad/PCB-NOTES.md.
#
#   kicad/gen/check.sh tht          # regenerate + verify the THT board (kicad/)
#   kicad/gen/check.sh smd          # regenerate + verify the SMD variant (kicad/smd/)
#   kicad/gen/check.sh tht --no-regen   # verify only (keeps a ROUTED board intact!)
#
# NOTE: regenerating rewrites the PLACED board -- it discards routing. After a
# re-route run with --no-regen, or route again (kicad/gen/route_board.py).
set -u
cd "$(dirname "$0")/../.."
P=${1:-tht}; REGEN=1; [ "${2:-}" = "--no-regen" ] && REGEN=0
case "$P" in
  tht) DIR=kicad;     SCH=cambridge_reverb.kicad_sch;     PCB=cambridge_reverb.kicad_pcb;     BOMF="";;
  smd) DIR=kicad/smd; SCH=cambridge_reverb_smd.kicad_sch; PCB=cambridge_reverb_smd.kicad_pcb; BOMF="--jlc";;
  *) echo "profile must be tht or smd"; exit 2;;
esac
R=kicad/reports; mkdir -p $R
if [ $REGEN = 1 ]; then
  python3 kicad/gen/gen_kicad.py --profile $P | tail -1 || { echo "gen_kicad FAILED"; exit 1; }
  python3 kicad/gen/gen_pcb.py --profile $P 2>&1 | grep -vE "^$|Debug:"
  python3 kicad/gen/gen_bom.py --profile $P $BOMF | head -3
  if [ "$P" = smd ]; then
    kicad-cli pcb export pos --side front --format csv --units mm --smd-only --exclude-dnp \
      -o production/smd/cambridge_reverb_smd-top-pos.csv $DIR/$PCB >/dev/null 2>&1 && echo "position file: $(($(wc -l < production/smd/cambridge_reverb_smd-top-pos.csv)-1)) SMD parts"
  fi
fi
kicad-cli sch erc --severity-all --exit-code-violations -o $R/$P-erc.rpt $DIR/$SCH >/dev/null 2>&1
echo "ERC[$P] exit=$? ($(grep -cE '^\[' $R/$P-erc.rpt) violation lines)"
for b in $DIR/$PCB kicad/power_section_demo.kicad_pcb; do
  [ -f $b ] || continue; [ "$P" = smd ] && [[ $b == *demo* ]] && continue
  n=$(basename $b .kicad_pcb); [ "$n" = power_section_demo ] && tag=demo || tag=$P
  kicad-cli pcb drc --severity-all --format json -o $R/$tag-drc.json $b >/dev/null 2>&1
  python3 - $R/$tag-drc.json $n <<'PY'
import json,sys,collections
d=json.load(open(sys.argv[1])); c=collections.Counter()
for v in d.get("violations",[]): c[(v["type"],v["severity"])]+=1
u=len(d.get("unconnected_items",[]))
err={k[0]:n for k,n in c.items() if k[1]=="error"}; warn={k[0]:n for k,n in c.items() if k[1]=="warning"}
print(f"DRC[{sys.argv[2]}] unconnected={u} errors={sum(err.values())} {err} warnings={sum(warn.values())} {warn}")
PY
done
