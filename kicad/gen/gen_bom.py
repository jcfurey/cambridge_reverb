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
import jlc_parts

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
 "LINK":"Wire link (build option)",
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
 "JP_BR":"Bridge '-' pin to GND link: ONLY for a transformer WITHOUT centre tap",
 "R_qb":"Tremolo driver base series resistor (isolates the LFO from the footswitch short)",
 "R_fs_mrb":"DC return for the footswitched MRB tank",
 "C_s1":"Q1 source bypass (voicing option)","C_s2":"Q2 source bypass (voicing option)",
 "C_mixfb":"Reverb summer feedback capacitor: cancels the summing node's stray capacitance (errata #31)",
 "R_gnd":"STAR link: the one connection between signal ground (planes) and the speaker return / power ground",
 "R_spk_rtn":"Speaker return link to power ground (carries the full speaker current)",
 "J_CHS":"Chassis bond pads (signal ground): ONE wire to the chassis",
 "R_lp":"Power-amp input low-pass / RF stopper (with C_lp: 7.5 kHz)","C_lp":"Power-amp input low-pass (C0G)",
 "R_reg2b":"LM317 set resistor, lower half (R_reg2 + R_reg2b = 3.0k)",
 "C_mrb_600b":"MRB tank capacitor, 600 Hz position (3 x 22 nF in parallel)","C_mrb_600c":"MRB tank capacitor, 600 Hz position (3 x 22 nF in parallel)",
 "C_mrb_600":"MRB tank capacitor, 600 Hz position (3 x 22 nF in parallel)",
 "C_treble":"Bright cap across the volume pot (voicing part, hand-fitted)",
 "R_tg":"Reverb-tank input-shield return (ground-loop breaker: the tank joins both shields)",
 "R_jb":"Input DC return: keeps the jack side of C_in_pre at 0 V with nothing plugged in",
 "R_midb":"Bleeder across the mid-cut switch: keeps C_res charged to mid-rail while the switch is open (no click)",
 "R_mrb_b":"DC return for MRB_OUT (a node between two capacitors)",
 "R_tb":"Bleeder across the vactrol LDR: holds TREM_S at 0 V while the LED is dark (no thump when the tremolo starts)",
 "C_dc_blk":"Tremolo shunt DC block -- CERAMIC or film, not an electrolytic (leakage: errata #38)",
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
 "D1":   dict(dk="1N4007-E3/54GICT-ND", mou="625-1N4007-E3", notes="output clamp to V+; cathode (pad 1, the banded end) on +33V5"),
 "D2":   dict(dk="1N4007-E3/54GICT-ND", mou="625-1N4007-E3", notes="output clamp to GND; cathode (pad 1, the banded end) on PA_OUT"),
 "LED_rate":dict(dk="160-1127-ND", mou="", notes="3 mm red; antiparallel with LED_lim across R_lfo_fb1 = the LFO amplitude limiter (~1.6 V knee -> ~2 V LFO swing) AND the rate indicator; on-board, not panel"),
 "LED_lim": dict(dk="160-1127-ND", mou="", notes="3 mm red; the other half of the limiter (lights on the negative half-cycle)"),
 "Q_trem": dict(dk="2N3904FS-ND", mou="512-2N3904BU", notes="any small NPN; SMD board: MMBT3904 on the EBC-renumbered SOT-23 footprint (1=E 2=B 3=C like the TO-92)"),
 "C_drv":  dict(dk="", mou="", notes="100 uF/25 V electrolytic, + to the depth-pot wiper (8.5 V) side; with R_b1||R_b2 sets the 0.17 Hz LFO coupling corner"),
 "C_adj":  dict(dk="", mou="", notes="10 uF/25 V on the LM317 ADJ pin (TI: 65 -> 80 dB ripple rejection; output noise falls ~10x) -- spice/noise_frontend.cir"),
 "C_pre":  dict(dk="", mou="", notes="220 uF/25 V; with R_pre 100R a 7 Hz corner on the preamp/recovery JFET rail -- the resistor-loaded JFET stages have ~0 dB PSRR"),
 "C_bref": dict(dk="", mou="", notes="100 uF/25 V bypass on the LM1875 bias divider; without it the divider injected rail ripple x23 into the speaker (spice/ac_hum_psrr.cir)"),
 "VTL1": dict(dk="", mou="", notes="Xvive VTL5C1 (single-source) or DIY LED+LDR. AXIAL part laid flat: LED leads at the K end (pad 1 = LED CATHODE, the marked lead; pad 2 = anode), LDR leads at the other end (errata #25)"),
 "JP_BR": dict(dk="", mou="", notes="DO NOT FIT with a centre-tapped transformer (the original, or 2x24 V in series): CT goes to the T1 'CT' pad and the bridge works as a two-diode full wave. Fit a wire link ONLY for a single 24 V winding with no tap, and then leave the CT pad empty. Both together short the transformer (errata #26)"),
 "R_qb": dict(dk="", mou="", notes="1k; the footswitch's tremolo switch shorts the driver base (FS_TREM) to GND -- without R_qb that short would load the LFO through C_drv (errata #27)"),
 "R_fs_mrb": dict(dk="", mou="", notes="1M: keeps the MRB tank at 0 V DC while the footswitch is open (no pop); the tank's ground return is the footswitch (errata #27)"),
 "C_s1": dict(dk="", mou="", notes="VOICING OPTION, default NOT fitted. Without C_s1/C_s2 the preamp has 21 dB and stays clean to ~0.3 V pk; C_s1 only: 33 dB, breaks up above ~0.1 V pk; both: 45 dB, 8 % THD at 20 mV (spice/tran_preamp_headroom.cir, errata #28)"),
 "C_s2": dict(dk="", mou="", notes="see C_s1 (errata #28)"),
 "C_main":dict(dk="", mou="667-EEU-FC1H472", notes="low-ESR; or 2x2200uF if PCB-mounted (errata #16)"),
 "C_filt1":dict(dk="", mou="667-EEU-FC1H102", notes="low-ESR pre-filter bulk"),
 "C_filt2":dict(dk="", mou="667-EEU-FC1H102", notes="low-ESR pre-filter bulk"),
 "C101":dict(dk="", mou="", notes="bridge snubber: 100 nF, 100 V minimum (the diode it bridges sees twice the secondary peak), X7R or film"),
 "C102":dict(dk="", mou="", notes="bridge snubber, see C101"),
 "C103":dict(dk="", mou="", notes="bridge snubber, see C101"),
 "C104":dict(dk="", mou="", notes="bridge snubber, see C101"),
 "C_dc_blk":dict(dk="", mou="", notes="2.2 uF 50 V X7R (THT board: radial MLCC or box film, 5 mm pitch). NOT an electrolytic: its leakage charges the vactrol node while the tremolo is off and the next start thumps (errata #38)"),
 "R_tb":dict(dk="", mou="", notes="220k; with C_dc_blk's leakage in nanoamps TREM_S stays within millivolts of ground"),
 "R_jb":dict(dk="", mou="", notes="10M (4.7M-22M is fine): a DC return, not a load"),
 "R_gnd":dict(dk="", mou="", notes="0R (THT board: a wire link). Without it the planes float: check 0 ohm between TP GND and TP PGND before first power-up. The ONLY ground link -- do not add others (errata #32)"),
 "R_spk_rtn":dict(dk="", mou="", notes="0R: a bare wire link of 1 mm copper (or a 0R 1 W jumper); carries the speaker current from the LS1 '-' pad to power ground"),
 "J_CHS":dict(dk="", mou="", notes="no part. Bond the chassis to circuit ground in ONE place: either through the (non-insulated) input jacks -- then leave these pads empty -- or, with insulated jacks, by one wire from here to the chassis lug. The second pad takes a scope ground clip"),
 "R_lp":dict(dk="", mou="", notes="1k; with C_lp and R_bias3 the 7.5 kHz guitar roll-off, in FRONT of the LM1875 -- the feedback network must stay resistive (errata #35)"),
 "C_lp":dict(dk="", mou="", notes="22 nF C0G/film at the LM1875 + input (also the input capacitor the data sheet asks for against RF pickup)"),
 "R_reg2b":dict(dk="", mou="", notes="1.5k, see R_reg2"),
 "C_treble":dict(dk="", mou="", notes="470 pF C0G / silver mica, 5 mm pitch. The classic Vox bright cap -- 100 pF to 1 nF to taste, or leave it out. Hand-fitted on both boards (JLCPCB has no basic C0G of this value)"),
 "C_out":dict(dk="", mou="", notes="REQUIRED for single-supply (errata #7)"),
 "R_reg1":dict(dk="", mou="603-MFR-25FBF52-240R", notes=""),
 "R_reg2":dict(dk="", mou="", notes="1.5k; R_reg2 + R_reg2b = 3.0k -> 17.0 V typical incl. the adjust-pin current (16.4-17.7 V over the LM317's reference tolerance; errata #34)"),
 "R_27V":dict(dk="", mou="", notes="LM317-input RC pre-filter w/ C_filt1 (VREG_IN ~32V, roast R2)"),
 "C_reg_in":dict(dk="", mou="581-TAP106K050SCS", notes="tantalum"),
 "C_reg_out1":dict(dk="", mou="581-TAP106K025SCS", notes="tantalum"),
 "F1":   dict(dk="", mou="576-021801.6MXP", notes="5x20 mm TIME-LAG 1.6 A 250 V (Littelfuse 0218 01.6). Carries the reservoir's charging pulses: 1.1 A rms at full sine power, 1.5 A rms clipped -- a T1A sat above its rating (errata #33)"),
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
def smd_note(c):
    """SMD rows of bom-smd.csv: the exact JLCPCB part chosen in jlc_parts.py."""
    p = jlc_parts.part_for(c)
    if p is None:
        return None
    return f"JLCPCB {p['lcsc']} ({p['cls']}): {p['mfr']} {p['mpn']} -- {p['comment']}"
JLC_PKG = jlc_parts.PKG            # footprint column = the package JLCPCB lists for the part

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
        # JLCPCB assembly BOM for the SMD side (Comment, Designator, Footprint, LCSC Part #),
        # one line per LCSC part. The part numbers come from jlc_parts.py: every one was
        # looked up in JLCPCB's library (stock, class, package) -- none is a guess.
        smd = [(c, jlc_parts.part_for(c)) for c in comps if "(opt)" not in c["value"]]   # optional parts are DNP: not placed
        smd = [(c, p) for c, p in smd if p is not None]
        os.makedirs(os.path.join(ROOT, "production", "smd"), exist_ok=True)
        jout = os.path.join(ROOT, "production", "smd", "bom-jlcpcb.csv")
        by = defaultdict(list)
        for c, p in smd: by[p["lcsc"]].append((c, p))
        order = {"basic": 0, "preferred": 1, "extended": 2}
        with open(jout, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer", "MPN", "JLCPCB class"])
            for lcsc, cps in sorted(by.items(), key=lambda kv: (order[kv[1][0][1]["cls"]], kv[1][0][1]["kind"], kv[1][0][1]["comment"])):
                p = cps[0][1]
                w.writerow([p["comment"], ",".join(sorted(c["ref"] for c, _ in cps)), JLC_PKG[p["kind"]], lcsc, p["mfr"], p["mpn"], p["cls"]])
        ncls = defaultdict(int)
        for cps in by.values(): ncls[cps[0][1]["cls"]] += 1
        print(f"wrote {len(by)} JLCPCB assembly lines ({len(smd)} SMD parts; {ncls['basic']} basic, {ncls['preferred']} preferred, "
              f"{ncls['extended']} extended) -> production/smd/bom-jlcpcb.csv")
    miss = [c["ref"] for c in comps if c["ref"] not in CUR and c["libsym"] in ("OPAMP8","OPAMP14","LM1875","LM317","BRIDGE","NJFET","NPN")]
    if miss: print("  note: active parts without a curated P/N:", miss)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate the BOM from the schematic (per build profile)")
    ap.add_argument("--profile", choices=("tht", "smd"), default="tht")
    ap.add_argument("--jlc", action="store_true", help="also write production/smd/bom-jlcpcb.csv (SMD side)")
    a = ap.parse_args()
    main(a.profile, a.jlc)
