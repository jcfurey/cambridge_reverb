#!/usr/bin/env python3
"""Generate bom/bom.csv (and bom/bom-grouped.csv) FROM THE SCHEMATIC.

The schematic (via gen_kicad's COMPONENTS) is the single source of truth for what
is on the board, so the BOM can no longer drift from it. Per-reference electrical
rows are merged with curated part numbers / notes and an explicit list of
off-board & mechanical items that are not in the netlist (sockets, heatsink, mica,
standoffs, fuse holders, mains fuse).  Run from repo root:

    python3 kicad/gen/gen_bom.py
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(__file__))
import gen_kicad as g

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# generic description per primitive class
CLASS_DESC = {
 "R":"Resistor","C":"Capacitor (film/ceramic)","CP":"Capacitor (electrolytic)",
 "L":"Inductor","D":"Diode","LED":"LED","FUSE":"Fuse","POT":"Potentiometer (panel, reused)",
 "NJFET":"N-ch JFET","BRIDGE":"Bridge rectifier","LM317":"Adj. regulator",
 "LM1875":"Power amplifier","OPAMP8":"Dual op-amp","JACK":"1/4in jack (panel, reused)",
 "SPEAKER":"Speaker (reused)","XFMR":"Power transformer (reused/AnTek)",
 "VTL5C1":"LED/LDR optocoupler","Reverb_Tank_4FB2A1C":"Reverb pan (off-board)",
 "Footswitch_DIN6":"6-pin DIN footswitch (panel)","PWR_FLAG":"",
}
# per-ref description override (function), where it adds clarity
DESC = {
 "IC1":"Dual op-amp: reverb tank driver + wet/dry summer","IC2":"Dual op-amp: tremolo LFO + output buffer",
 "IC_PA":"Power amplifier","U1":"+17V rail regulator","BR1":"Bridge rectifier",
 "Q1":"Preamp JFET","Q2":"Preamp JFET","Q_rec":"Reverb-recovery JFET",
 "REV1":"Reverb pan (high-Z input)","FS1":"Footswitch DIN connector","LS1":"10in speaker",
 "VTL1":"Tremolo optocoupler","L1":"MRB tank inductor","T1":"Power transformer",
 "POT_VOL":"Volume","POT_TONE":"Tone","POT_REV":"Reverb level","POT_SPD":"Tremolo speed","POT_DPT":"Tremolo depth",
}
# curated part numbers + key notes, keyed by reference
CUR = {
 "IC1":  dict(dk="296-1775-5-ND", mou="595-TL072CP", notes="DIP-8; use a machined-pin SOCKET_IC"),
 "IC2":  dict(dk="296-1775-5-ND", mou="595-TL072CP", notes="DIP-8; use a machined-pin SOCKET_IC"),
 "IC_PA":dict(dk="LM1875T/NOPB-ND", mou="926-LM1875T/NOPB", notes="Single-source (TI) - buy a spare. Heatsink <=2.5 C/W + mica; NOT socketed"),
 "U1":   dict(dk="LM317T/NOPB-ND", mou="926-LM317T/NOPB", notes=""),
 "BR1":  dict(dk="KBP410G-ND", mou="821-KBP410G", notes="Or 4x 1N4007"),
 "Q1":   dict(dk="MMBF5457CT-ND", mou="863-MMBF5457", notes="AVAILABILITY WATCH (JFETs going EOL) - buy spares; alts J113/LSK170. SOT-23->TO-92 adapter or J113"),
 "Q2":   dict(dk="MMBF5457CT-ND", mou="863-MMBF5457", notes="see Q1"),
 "Q_rec":dict(dk="MMBF5457CT-ND", mou="863-MMBF5457", notes="see Q1"),
 "D1":   dict(dk="1N4007-E3/54GICT-ND", mou="625-1N4007-E3", notes="output clamp"),
 "D2":   dict(dk="1N4007-E3/54GICT-ND", mou="625-1N4007-E3", notes="output clamp"),
 "D_lfo1":dict(dk="1N4148FS-ND", mou="512-1N4148", notes="LFO amplitude clamp"),
 "D_lfo2":dict(dk="1N4148FS-ND", mou="512-1N4148", notes="LFO amplitude clamp"),
 "LED_rate":dict(dk="160-1127-ND", mou="", notes="on-board diagnostic, not panel"),
 "VTL1": dict(dk="", mou="", notes="Xvive VTL5C1 (single-source) or DIY LED+LDR"),
 "C_main":dict(dk="", mou="667-EEU-FC1H472", notes="low-ESR; or 2x2200uF if PCB-mounted (errata #16)"),
 "C_filt1":dict(dk="", mou="667-EEU-FC1H102", notes="low-ESR pre-filter bulk"),
 "C_filt2":dict(dk="", mou="667-EEU-FC1H102", notes="low-ESR pre-filter bulk"),
 "C101":dict(dk="", mou="594-K104Z15Y5VF5TL2", notes="bridge snubber"),
 "C102":dict(dk="", mou="594-K104Z15Y5VF5TL2", notes="bridge snubber"),
 "C103":dict(dk="", mou="594-K104Z15Y5VF5TL2", notes="bridge snubber"),
 "C104":dict(dk="", mou="594-K104Z15Y5VF5TL2", notes="bridge snubber"),
 "C_out":dict(dk="", mou="", notes="REQUIRED for single-supply (errata #7)"),
 "R_reg1":dict(dk="", mou="603-MFR-25FBF52-240R", notes=""),
 "R_reg2":dict(dk="", mou="", notes="3.09k E96 -> 17.34V (errata #10)"),
 "R_27V":dict(dk="", mou="", notes="LM317-input RC pre-filter w/ C_filt1 (VREG_IN ~32V, roast R2)"),
 "C_reg_in":dict(dk="", mou="581-TAP106K050SCS", notes="tantalum"),
 "C_reg_out1":dict(dk="", mou="581-TAP106K025SCS", notes="tantalum"),
 "F1":   dict(dk="", mou="576-0273001.H", notes="secondary fuse; prefer AC-secondary placement (roast R5)"),
 "R_s1": dict(dk="", mou="", notes="2K2 biases Vd~12V; ~1-1.2k -> 8-9V target (errata #15), trim per device"),
 "R_s2": dict(dk="", mou="", notes="see R_s1 (errata #15)"),
 "L1":   dict(dk="", mou="", notes="reuse original ~1H, or 2x 0.5H Fasel"),
 "REV1": dict(dk="", mou="", notes="Accutronics/Belton 4FB2A1C ~1475ohm - NOT 4AB3C1B (8ohm)"),
 "T1":   dict(dk="", mou="", notes="reuse original (test ~48VAC) or AnTek AS-0524 50VA"),
}
REUSE = {"POT_VOL","POT_TONE","POT_REV","POT_SPD","POT_DPT","J_IN1","J_IN2","J_IN3","FS1","LS1","T1","REV1","L1"}

# off-board / mechanical items that are NOT in the netlist
# (ref, description, value, package, dk, mou, qty, notes)
MECH = [
 ("F_MAINS","MAINS PRIMARY fuse (SAFETY)","T800mA 250V slow-blow","5x20mm","","",1,"IEC inlet primary fuse (120V; ~T400mA@230V). REQUIRED, was missing (roast R1). Off-board"),
 ("F_MAINS_holder","Fused IEC inlet / panel fuse holder","","panel","","",1,"carries the mains fuse"),
 ("F1_holder","Secondary fuse holder","5x20mm","PCB/panel","","534-3557",1,""),
 ("SOCKET_IC","8-pin DIP machined-pin socket","turned-pin","DIP-8","ED3008-5-ND","575-193308",2,"REQUIRED for IC1/IC2 (machined, not stamped)"),
 ("SOCKET_U1","TO-220 socket (optional)","3-pin","TO-220","","",0,"optional LM317 field-swap; LM1875 stays soldered"),
 ("HS_LM1875","Heatsink for LM1875","<=2.5 C/W","bracket","","",1,"reuse original bracket; mica + shoulder washer"),
 ("INS_MICA","TO-220 mica insulator + bushing","","","","",1,"for LM1875"),
 ("STANDOFF","Nylon standoffs + screws","","","","",4,"PCB mounting"),
]

def describe(c):
    if c["ref"] in DESC: d = DESC[c["ref"]]
    else: d = CLASS_DESC.get(c["libsym"], c["libsym"])
    if c["ref"] in REUSE and "reuse" not in d.lower(): d += " (reused/off-board)"
    return d

def main():
    g.build()
    comps = [c for c in g.COMPONENTS if c["libsym"] != "PWR_FLAG"]   # drop virtual flags
    rows = []
    for c in sorted(comps, key=lambda c: (c["sheet"], c["ref"])):
        cur = CUR.get(c["ref"], {})
        rows.append([c["ref"], describe(c), c["value"], c["fp"].split(":")[-1] if c["fp"] else "",
                     cur.get("dk",""), cur.get("mou",""), 1, cur.get("notes","")])
    hdr = ["ref","description","value","footprint","digikey_pn","mouser_pn","qty","notes"]
    out = os.path.join(ROOT, "bom", "bom.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        f.write("# GENERATED from the schematic by kicad/gen/gen_bom.py -- do not hand-edit.\n")
        f.write("# Electrical rows are 1:1 with the KiCad netlist; mechanical/off-board items follow.\n")
        w.writerow(hdr)
        for r in rows: w.writerow(r)
        w.writerow(["# --- off-board / mechanical (not in netlist) ---","","","","","","",""])
        for m in MECH: w.writerow(list(m))
    # grouped order-summary by (value, footprint)
    from collections import defaultdict
    grp = defaultdict(list)
    for c in comps: grp[(c["value"], c["fp"].split(":")[-1] if c["fp"] else "")].append(c["ref"])
    gout = os.path.join(ROOT, "bom", "bom-grouped.csv")
    with open(gout, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["qty","value","footprint","refs"])
        for (val, fp), refs in sorted(grp.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            w.writerow([len(refs), val, fp, " ".join(sorted(refs))])
    print(f"wrote {len(rows)} electrical + {len(MECH)} mechanical rows -> bom/bom.csv")
    print(f"wrote {len(grp)} grouped lines -> bom/bom-grouped.csv")
    miss = [c["ref"] for c in comps if c["ref"] not in CUR and c["libsym"] in ("OPAMP8","LM1875","LM317","BRIDGE","NJFET")]
    if miss: print("  note: active parts without a curated P/N:", miss)

if __name__ == "__main__":
    main()
