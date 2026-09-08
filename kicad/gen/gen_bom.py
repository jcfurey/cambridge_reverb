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
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import gen_kicad as g

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# generic description per primitive class
CLASS_DESC = {
 "R":"Resistor","C":"Capacitor (film/ceramic)","CP":"Capacitor (electrolytic)",
 "L":"Inductor","D":"Diode","LED":"LED","FUSE":"Fuse","POT":"Potentiometer (panel, reused)",
 "NJFET":"N-ch JFET","NPN":"NPN transistor","BRIDGE":"Bridge rectifier","LM317":"Adj. regulator",
 "LM1875":"Power amplifier","OPAMP8":"Dual op-amp","OPAMP14":"Quad op-amp","SW_SPST":"SPST toggle switch (panel)","JACK":"1/4in jack (panel, reused)",
 "SPEAKER":"Speaker (reused)","XFMR":"Power transformer (reused/AnTek)",
 "VTL5C1":"LED/LDR optocoupler","Reverb_Tank_4FB2A1C":"Reverb pan (off-board)",
 "Footswitch_DIN6":"6-pin DIN footswitch (panel)","PWR_FLAG":"","TP":"Test point (header pin or wire loop)",
}
# per-ref description override (function), where it adds clarity
DESC = {
 "IC1":"Dual op-amp: reverb tank driver + wet/dry summer","IC2":"Dual op-amp: tremolo LFO + output buffer",
 "IC3":"Quad op-amp: tone input buffer + x2 make-up after the passive James bass/treble network + mid-cut gyrator + output buffer",
 "POT_BASS":"Bass","POT_TREB":"Treble","SW_MID":"Mid-cut toggle (panel, line-reverse switch hole)",
 "IC_PA":"Power amplifier","U1":"+17V rail regulator","BR1":"Bridge rectifier",
 "Q1":"Preamp JFET","Q2":"Preamp JFET","Q_rec":"Reverb-recovery JFET",
 "REV1":"Reverb pan (high-Z input)","FS1":"Footswitch DIN connector","LS1":"10in speaker",
 "VTL1":"Tremolo optocoupler","L1":"MRB tank inductor","T1":"Power transformer",
 "Q_trem":"Tremolo LED driver (emitter follower, AC-coupled from the depth pot)",
 "LED_rate":"LFO limiter LED = rate indicator (on-board)","LED_lim":"LFO limiter LED (other half-cycle)",
 "C_drv":"LED-driver coupling (LFO -> base)","R_b1":"LED-driver base bias","R_b2":"LED-driver base bias",
 "R_e":"LED-driver emitter resistor (sets peak LED current ~6 mA)","R_c":"Vactrol LED series resistor",
 "C_adj":"LM317 ADJ bypass: +15 dB ripple rejection, ~10x less rail noise","R_pre":"Preamp rail decoupling (with C_pre)",
 "C_pre":"Preamp rail decoupling (with R_pre)","R_bias3":"LM1875 + input bias feed (from the bypassed divider)",
 "C_bref":"LM1875 bias-divider bypass (kills the rail-ripple path into the + input)",
 "R_rf1":"RF stopper, guitar input (with C_rf1: 1.6 MHz)","C_rf1":"RF stopper, guitar input (C0G)",
 "R_rf2":"RF stopper, reverb tank return (with C_rf2)","C_rf2":"RF stopper, tank return (C0G)",
 "POT_VOL":"Volume","POT_TONE":"Tone","POT_REV":"Reverb level","POT_SPD_A":"Tremolo speed -- dual-gang pot, gang A (series Wien arm)","POT_SPD_B":"Tremolo speed -- dual-gang pot, gang B (shunt Wien arm); ONE part with POT_SPD_A","POT_DPT":"Tremolo depth",
}
# curated part numbers + key notes, keyed by reference
CUR = {
 "IC1":  dict(dk="296-1775-5-ND", mou="595-TL072CP", notes="DIP-8; use a machined-pin SOCKET_IC"),
 "IC2":  dict(dk="296-1775-5-ND", mou="595-TL072CP", notes="DIP-8; use a machined-pin SOCKET_IC"),
 "IC3":  dict(dk="", mou="595-TL074CN", notes="DIP-14; machined-pin SOCKET_IC14. Tone stack (errata #20)"),
 "SW_MID": dict(dk="", mou="", notes="SPST (or SPDT wired as SPST) mini toggle, panel-mount in the ORIGINAL line-reverse switch hole (no new hole); switches an audio shunt sitting at mid-rail DC -> no pop"),
 "POT_BASS": dict(dk="", mou="", notes="reused panel pot; James network scaled for 250k lin -- if the original measures differently, scale R_j1/R_j2/R_j3 and C_j1/C_j2 to keep the same corner frequencies"),
 "POT_TREB": dict(dk="", mou="", notes="reused panel pot; James network scaled for 250k lin -- scale C_j3/C_j4 inversely to keep the treble corner"),
 "IC_PA":dict(dk="LM1875T/NOPB-ND", mou="926-LM1875T/NOPB", notes="Single-source (TI) - buy a spare. Heatsink <=2.5 C/W + mica; NOT socketed"),
 "U1":   dict(dk="LM317T/NOPB-ND", mou="926-LM317T/NOPB", notes=""),
 "BR1":  dict(dk="KBP410G-ND", mou="821-KBP410G", notes="Or 4x 1N4007"),
 "Q1":   dict(dk="MMBF5457CT-ND", mou="863-MMBF5457", notes="AVAILABILITY WATCH (JFETs going EOL) - buy spares; alts J113/LSK170. THT board: SOT-23 on a TO-92 adapter or J113 -- pads 1/2/3 = D/S/G (errata #18); SMD variant fits it directly"),
 "Q2":   dict(dk="MMBF5457CT-ND", mou="863-MMBF5457", notes="see Q1"),
 "Q_rec":dict(dk="MMBF5457CT-ND", mou="863-MMBF5457", notes="see Q1"),
 "D1":   dict(dk="1N4007-E3/54GICT-ND", mou="625-1N4007-E3", notes="output clamp"),
 "D2":   dict(dk="1N4007-E3/54GICT-ND", mou="625-1N4007-E3", notes="output clamp"),
 "LED_rate":dict(dk="160-1127-ND", mou="", notes="3 mm red; antiparallel with LED_lim across R_lfo_fb1 = the LFO amplitude limiter (~1.6 V knee -> ~2 V LFO swing) AND the rate indicator; on-board, not panel"),
 "LED_lim": dict(dk="160-1127-ND", mou="", notes="3 mm red; the other half of the limiter (lights on the negative half-cycle)"),
 "Q_trem": dict(dk="2N3904FS-ND", mou="512-2N3904BU", notes="any small NPN; SMD board: MMBT3904 on the EBC-renumbered SOT-23 footprint (1=E 2=B 3=C like the TO-92)"),
 "C_drv":  dict(dk="", mou="", notes="100 uF/25 V electrolytic, + to the depth-pot wiper (8.5 V) side; with R_b1||R_b2 sets the 0.17 Hz LFO coupling corner"),
 "C_adj":  dict(dk="", mou="", notes="10 uF/25 V on the LM317 ADJ pin (TI: 65 -> 80 dB ripple rejection; output noise falls ~10x) -- spice/noise_frontend.cir"),
 "C_pre":  dict(dk="", mou="", notes="220 uF/25 V; with R_pre 100R a 7 Hz corner on the preamp/recovery JFET rail -- the resistor-loaded JFET stages have ~0 dB PSRR"),
 "C_bref": dict(dk="", mou="", notes="100 uF/25 V bypass on the LM1875 bias divider; without it the divider injected rail ripple x23 into the speaker (spice/ac_hum_psrr.cir)"),
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
 "POT_SPD_A": dict(dk="", mou="", notes="DUAL-GANG 250k linear, 1 part = gangs A+B (same panel hole as the original speed pot); errata #19"),
 "POT_SPD_B": dict(dk="", mou="", notes="second gang of POT_SPD_A -- do not order twice"),
}
REUSE = {"POT_VOL","POT_BASS","POT_TREB","POT_REV","POT_DPT","J_IN1","J_IN2","J_IN3","FS1","LS1","T1","REV1","L1"}
# POT_SPD_A/B: the tremolo speed pot is NEW -- a dual-gang 250k lin in the original
# speed-pot hole (errata #19); the original single pot is not reused.

# off-board / mechanical items that are NOT in the netlist
# (ref, description, value, package, dk, mou, qty, notes)
MECH = [
 ("F_MAINS","MAINS PRIMARY fuse (SAFETY)","T800mA 250V slow-blow","5x20mm","","",1,"IEC inlet primary fuse (120V; ~T400mA@230V). REQUIRED, was missing (roast R1). Off-board"),
 ("F_MAINS_holder","Fused IEC inlet / panel fuse holder","","panel","","",1,"carries the mains fuse"),
 ("F1_holder","Secondary fuse holder","5x20mm","PCB/panel","","534-3557",1,""),
 ("SOCKET_IC","8-pin DIP machined-pin socket","turned-pin","DIP-8","ED3008-5-ND","575-193308",2,"REQUIRED for IC1/IC2 (machined, not stamped)"),
 ("SOCKET_IC14","14-pin DIP machined-pin socket","turned-pin","DIP-14","","",1,"REQUIRED for IC3 (tone stack TL074)"),
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

# "smd" profile: the curated THT part numbers do not apply to the remapped parts;
# they get a spec note instead (generic JLCPCB-basic-class parts) -- no invented P/Ns.
SMD_NOTES = {
 "R_0805_2012Metric": "0805 1% (thin-film for the 1M gate / input resistors; thick-film elsewhere); JLCPCB basic",
 "R_1206_3216Metric": "1206 1% 0.25 W (dissipates ~85 mW)",
 "C_1206_3216Metric": "1206 50 V; C0G/NP0 in the signal path (X7R ok for supply bypass); snubbers 100 V X7R",
 "D_SMA":             "S1M (1 kV 1 A SMA) replaces 1N4007",
 "D_SOD-123":         "1N4148W replaces 1N4148",
 "SOT-23":            "MMBF5457 fitted directly (no TO-92 adapter); pin 1 D, 2 S, 3 G per onsemi",
}
def smd_note(c):
    fpn = c["fp"].split(":")[-1] if c["fp"] else ""
    return SMD_NOTES.get(fpn)

def main(profile="tht", jlc=False):
    g.set_profile(profile)
    g.build()
    suffix = "" if profile == "tht" else "-" + profile
    comps = [c for c in g.COMPONENTS if c["libsym"] != "PWR_FLAG"]   # drop virtual flags
    rows = []
    for c in sorted(comps, key=lambda c: (c["sheet"], c["ref"])):
        cur = CUR.get(c["ref"], {})
        if c["libsym"] == "TP":
            cur = dict(notes="bench test point: fit a header pin or a bare 0.6 mm wire loop; silk shows the net")
        if profile == "smd" and smd_note(c):
            cur = dict(dk="", mou="", notes=smd_note(c) + (("; was: " + cur["notes"]) if cur.get("notes") else ""))
        rows.append([c["ref"], describe(c), c["value"], c["fp"].split(":")[-1] if c["fp"] else "",
                     cur.get("dk",""), cur.get("mou",""), 1, cur.get("notes","")])
    hdr = ["ref","description","value","footprint","digikey_pn","mouser_pn","qty","notes"]
    out = os.path.join(ROOT, "bom", f"bom{suffix}.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        f.write("# GENERATED from the schematic by kicad/gen/gen_bom.py -- do not hand-edit.\n")
        f.write("# Electrical rows are 1:1 with the KiCad netlist; mechanical/off-board items follow.\n")
        w.writerow(hdr)
        for r in rows: w.writerow(r)
        w.writerow(["# --- off-board / mechanical (not in netlist) ---","","","","","","",""])
        for m in MECH: w.writerow(list(m))
    # grouped order-summary by (value, footprint)
    grp = defaultdict(list)
    for c in comps:
        val = "test point (label = net)" if c["libsym"] == "TP" else c["value"]   # 26 one-offs -> one order line
        grp[(val, c["fp"].split(":")[-1] if c["fp"] else "")].append(c["ref"])
    gout = os.path.join(ROOT, "bom", f"bom{suffix}-grouped.csv")
    with open(gout, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["qty","value","footprint","refs"])
        for (val, fp), refs in sorted(grp.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            w.writerow([len(refs), val, fp, " ".join(sorted(refs))])
    print(f"wrote {len(rows)} electrical + {len(MECH)} mechanical rows -> bom/bom{suffix}.csv")
    print(f"wrote {len(grp)} grouped lines -> bom/bom{suffix}-grouped.csv")
    if jlc:
        # JLCPCB assembly BOM for the SMD side only (Comment, Designator, Footprint, LCSC).
        # LCSC numbers are left for the JLC parts picker -- none are invented here.
        smd = [c for c in comps if c["fp"] and ("_SMD:" in c["fp"] or "SOT_SMD" in c["fp"] or "SOT-23" in c["fp"])
               and "(opt)" not in c["value"]]          # optional MRB caps are DNP: not placed by JLC
        os.makedirs(os.path.join(ROOT, "production", "smd"), exist_ok=True)
        jout = os.path.join(ROOT, "production", "smd", "bom-jlcpcb.csv")
        by = defaultdict(list)
        for c in smd: by[(c["value"], c["fp"].split(":")[-1])].append(c["ref"])
        with open(jout, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
            for (val, fpn), refs in sorted(by.items(), key=lambda kv: (kv[0][1], kv[0][0])):
                w.writerow([val, ",".join(sorted(refs)), fpn, ""])
        print(f"wrote {len(by)} JLCPCB assembly lines ({len(smd)} SMD parts) -> production/smd/bom-jlcpcb.csv")
    miss = [c["ref"] for c in comps if c["ref"] not in CUR and c["libsym"] in ("OPAMP8","OPAMP14","LM1875","LM317","BRIDGE","NJFET","NPN")]
    if miss: print("  note: active parts without a curated P/N:", miss)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate the BOM from the schematic (per build profile)")
    ap.add_argument("--profile", choices=("tht", "smd"), default="tht")
    ap.add_argument("--jlc", action="store_true", help="also write production/smd/bom-jlcpcb.csv (SMD side)")
    a = ap.parse_args()
    main(a.profile, a.jlc)
