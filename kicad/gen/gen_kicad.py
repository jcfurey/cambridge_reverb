#!/usr/bin/env python3
"""Generate the Vox Cambridge Reverb KiCad 7 hierarchical schematic.

Self-contained: defines primitive symbols (cr_primitives.kicad_sym) with known
pin geometry, then emits a root sheet + 8 sub-sheets wired with labels.
Connectivity uses a short wire stub from each pin endpoint to a label
(global_label for cross-sheet/rail nets, local label otherwise) -- robust and
ERC-clean without fragile wire routing. Validated with `kicad-cli sch erc`.

Symbol-lib coords are y-up; schematic is y-down, so pin endpoints map as
(Px+ex, Py-ey).  Run from repo root:  python3 kicad/gen/gen_kicad.py
"""
import uuid, os, math

ROOT = os.path.join(os.path.dirname(__file__), "..")
def U(): return str(uuid.uuid4())
def SNAP(v): return round(round(v / 1.27) * 1.27, 4)   # snap to 50-mil grid

# ----------------------------------------------------------------------------
# Primitive symbol database.
# pins: (number, name, ex, ey, ox, oy)  in SYMBOL (y-up) coords.
#   (ex,ey) = connection endpoint; (ox,oy) = outward unit vector.
# body: list of rectangles (x1,y1,x2,y2) drawn for looks (y-up).
# ----------------------------------------------------------------------------
def ang(ox, oy):
    # pin graphic is drawn from endpoint toward body = opposite of outward
    if (ox, oy) == (-1, 0): return 0
    if (ox, oy) == (1, 0):  return 180
    if (ox, oy) == (0, 1):  return 270
    if (ox, oy) == (0, -1): return 90
    raise ValueError((ox, oy))

SYMS = {
 "R":  dict(ref="R", desc="Resistor", hide_nums=True,
            pins=[("1","~",-5.08,0,-1,0),("2","~",5.08,0,1,0)],
            body=[(-2.54,-1.27,2.54,1.27)]),
 "C":  dict(ref="C", desc="Unpolarized capacitor", hide_nums=True,
            pins=[("1","~",-5.08,0,-1,0),("2","~",5.08,0,1,0)],
            body=[(-0.5,-2.54,-0.5,2.54),(0.5,-2.54,0.5,2.54)]),
 "CP": dict(ref="C", desc="Polarized capacitor (pin1 +)", hide_nums=True,
            pins=[("1","+",-5.08,0,-1,0),("2","~",5.08,0,1,0)],
            body=[(-0.5,-2.54,-0.5,2.54),(0.6,-2.54,2.4,2.54)]),
 "L":  dict(ref="L", desc="Inductor", hide_nums=True,
            pins=[("1","~",-5.08,0,-1,0),("2","~",5.08,0,1,0)],
            body=[(-2.54,-1.0,2.54,1.0)]),
 "D":  dict(ref="D", desc="Diode (1=A 2=K)", hide_nums=True,
            pins=[("1","A",-5.08,0,-1,0),("2","K",5.08,0,1,0)],
            body=[(-1.27,-1.27,1.27,1.27)]),
 "LED":dict(ref="D", desc="LED (1=A 2=K)", hide_nums=True,
            pins=[("1","A",-5.08,0,-1,0),("2","K",5.08,0,1,0)],
            body=[(-1.27,-1.27,1.27,1.27)]),
 "FUSE":dict(ref="F", desc="Fuse", hide_nums=True,
            pins=[("1","~",-5.08,0,-1,0),("2","~",5.08,0,1,0)],
            body=[(-2.54,-1.0,2.54,1.0)]),
 "POT":dict(ref="RV", desc="Potentiometer (1,3 ends; 2 wiper)", hide_nums=False,
            pins=[("1","1",-5.08,0,-1,0),("3","3",5.08,0,1,0),("2","W",0,5.08,0,1)],
            body=[(-2.54,-1.27,2.54,1.27)]),
 "NJFET":dict(ref="Q", desc="N-channel JFET (D G S)", hide_nums=False,
            pins=[("2","G",-7.62,0,-1,0),("1","D",2.54,7.62,0,1),("3","S",2.54,-7.62,0,-1)],
            body=[(-2.54,-3.81,2.54,3.81)]),
 "BRIDGE":dict(ref="BR", desc="Bridge rectifier", hide_nums=False,
            pins=[("1","~",-7.62,0,-1,0),("3","~",7.62,0,1,0),
                  ("2","+",0,7.62,0,1),("4","-",0,-7.62,0,-1)],
            body=[(-5.08,-5.08,5.08,5.08)]),
 "LM317":dict(ref="U", desc="LM317 adj regulator (3=IN 2=OUT 1=ADJ)", hide_nums=False,
            pins=[("3","IN",-10.16,0,-1,0),("2","OUT",10.16,0,1,0),("1","ADJ",0,-10.16,0,-1)],
            body=[(-7.62,-5.08,7.62,5.08)]),
 "LM1875":dict(ref="U", desc="LM1875 power amp (1=+ 2=- 4=OUT 5=V+ 3=V-)", hide_nums=False,
            pins=[("1","IN+",-12.7,2.54,-1,0),("2","IN-",-12.7,-2.54,-1,0),
                  ("4","OUT",12.7,0,1,0),("5","V+",0,10.16,0,1),("3","V-",0,-10.16,0,-1)],
            body=[(-7.62,-7.62,7.62,7.62)]),
 "OPAMP8":dict(ref="U", desc="Dual op-amp (TL072 DIP-8 pinout)", hide_nums=False,
            pins=[("3","IN1+",-12.7,5.08,-1,0),("2","IN1-",-12.7,2.54,-1,0),
                  ("5","IN2+",-12.7,-2.54,-1,0),("6","IN2-",-12.7,-5.08,-1,0),
                  ("1","OUT1",12.7,5.08,1,0),("7","OUT2",12.7,-5.08,1,0),
                  ("8","V+",0,10.16,0,1),("4","V-",0,-10.16,0,-1)],
            body=[(-7.62,-7.62,7.62,7.62)]),
 "PWR_FLAG":dict(ref="#FLG", desc="Power flag", hide_nums=True, power=True,
            pins=[("1","pwr",0,0,0,1)], body=[], pin_type="power_out"),
 "JACK":dict(ref="J", desc="1/4in input jack (1=Tip 2=Sleeve)", hide_nums=False,
            pins=[("1","T",5.08,2.54,1,0),("2","S",5.08,-2.54,1,0)],
            body=[(-2.54,-3.81,2.54,3.81)]),
 "SPEAKER":dict(ref="LS", desc="10in speaker (1=+ 2=-)", hide_nums=False,
            pins=[("1","+",-5.08,2.54,-1,0),("2","-",-5.08,-2.54,-1,0)],
            body=[(-2.54,-3.81,2.54,3.81)]),
 "XFMR":dict(ref="T", desc="Power transformer secondary (off-board)", hide_nums=False,
            pins=[("1","A",5.08,5.08,1,0),("2","CT",5.08,0,1,0),("3","B",5.08,-5.08,1,0)],
            body=[(-2.54,-7.62,2.54,7.62)]),
}

def sym_body(name, libname=None):
    s = SYMS[name]
    title = libname or name      # top symbol id (may be "lib:Name" when embedding)
    child = name                 # child unit symbols always use the BARE name
    ref = s["ref"]; hide = s.get("hide_nums", False)
    pin_type = s.get("pin_type", "passive")
    out = []
    extra = ' (pin_numbers hide)' if hide else ''
    out.append(f'  (symbol "{title}"{extra} (pin_names (offset 0.254)) (in_bom yes) (on_board yes)')
    refy = 6.35 if s["body"] else 2.54
    out.append(f'    (property "Reference" "{ref}" (at 0 {refy} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'    (property "Value" "{title}" (at 0 -{refy} 0) (effects (font (size 1.27 1.27))))')
    out.append(f'    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    out.append(f'    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    out.append(f'    (property "ki_description" "{s["desc"]}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    if s.get("power"):
        out.append(f'    (property "ki_keywords" "power-flag" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    # graphics unit _0_1
    out.append(f'    (symbol "{child}_0_1"')
    for (x1,y1,x2,y2) in s["body"]:
        if x1==x2 or y1==y2:
            out.append(f'      (polyline (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0.254) (type default)) (fill (type none)))')
        else:
            out.append(f'      (rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.254) (type default)) (fill (type none)))')
    out.append('    )')
    # pins unit _1_1
    out.append(f'    (symbol "{child}_1_1"')
    for (num,nm,ex,ey,ox,oy) in s["pins"]:
        a = ang(ox,oy)
        length = 2.54
        pt = pin_type
        if s.get("power"):
            out.append(f'      (pin power_out line (at {ex} {ey} {a}) (length {length})')
        else:
            out.append(f'      (pin {pt} line (at {ex} {ey} {a}) (length {length})')
        out.append(f'        (name "{nm}" (effects (font (size 1.016 1.016))))')
        out.append(f'        (number "{num}" (effects (font (size 1.016 1.016)))))')
    out.append('    )')
    out.append('  )')
    return "\n".join(out)

def write_primitives_lib():
    parts = ['(kicad_symbol_lib (version 20220914) (generator cambridge_reverb_gen)']
    for name in SYMS:
        parts.append(sym_body(name))
    parts.append(')')
    p = os.path.join(ROOT, "symbols", "cr_primitives.kicad_sym")
    open(p, "w").write("\n".join(parts) + "\n")
    return p

# ----------------------------------------------------------------------------
# Schematic emitter
# ----------------------------------------------------------------------------
class Sheet:
    # page (A3) and the target center for content. True page center horizontally;
    # nudged up only slightly so the tallest sheet still clears the title block.
    PAGE_W, PAGE_H = 420.0, 297.0
    CX, CY = 210.0, 141.0

    def __init__(self, title, fname):
        self.title = title; self.fname = fname
        self.ops = []            # deferred draw ops; coordinates centered at render time
        self.used = set()        # lib symbol names used
        self.uuid = U()          # this file's own root uuid
        self.inst = U()          # uuid of the (sheet) instance in the root

    def comp(self, libsym, ref, value, x, y, nets, mirror=None):
        """Place a component and attach labels to pins per nets={pinnum:netname}."""
        x = SNAP(x); y = SNAP(y)     # keep pins/wires on KiCad's 1.27mm connection grid
        self.used.add(libsym)
        fp = FOOTPRINTS.get(libsym, "")
        COMPONENTS.append(dict(ref=ref, libsym=libsym, value=value, fp=fp,
                               sheet=self.title, x=x, y=y, nets=dict(nets),
                               pins=PINS[libsym]))
        self.ops.append(('sym', libsym, ref, value, fp, x, y, U()))
        for (num, nm, ex, ey, ox, oy) in PINS[libsym]:
            if num not in nets:
                continue
            net = nets[num]
            px = x + ex; py = y - ey         # symbol y-up -> schematic y-down
            sox, soy = ox, -oy
            lx = px + 2.54 * sox; ly = py + 2.54 * soy
            rot = 0
            if sox < 0: rot = 180
            elif soy > 0: rot = 270
            elif soy < 0: rot = 90
            self.ops.append(('wire', px, py, lx, ly))
            self.ops.append(('label', net, lx, ly, rot, net in GLOBAL_NETS))

    def note(self, text, x, y):
        self.ops.append(('text', text, x, y))

    def _sym_sexpr(self, libsym, ref, value, fp, x, y, cu):
        lib_id = "cr_primitives:%s" % libsym if libsym in PRIM else "cambridge_reverb:%s" % libsym
        s = [f'  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)',
             '    (in_bom yes) (on_board yes) (dnp no)',
             f'    (uuid {cu})',
             f'    (property "Reference" "{ref}" (at {x+2.54} {y-7.62} 0) (effects (font (size 1.27 1.27)) (justify left)))',
             f'    (property "Value" "{value}" (at {x+2.54} {y-5.08} 0) (effects (font (size 1.27 1.27)) (justify left)))',
             f'    (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))']
        for (num, nm, ex, ey, ox, oy) in PINS[libsym]:
            s.append(f'    (pin "{num}" (uuid {U()}))')
        s.append(f'    (instances (project "cambridge_reverb" (path "{INSTPATH(self)}" (reference "{ref}") (unit 1))))')
        s.append('  )')
        return "\n".join(s)

    def _bbox(self):
        """Bounding box of the circuit (symbols + wires + labels); notes excluded
        so a long caption doesn't skew the centering."""
        xs, ys = [], []
        for op in self.ops:
            if op[0] == 'sym':
                xs.append(op[5]); ys.append(op[6])
            elif op[0] == 'wire':
                xs += [op[1], op[3]]; ys += [op[2], op[4]]
            elif op[0] == 'label':
                xs.append(op[2]); ys.append(op[3])
        return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)

    def render(self):
        minx, miny, maxx, maxy = self._bbox()
        # translate content so its center lands on (CX, CY); snap so pins stay on grid
        dx = SNAP(self.CX - (minx + maxx) / 2.0)
        dy = SNAP(self.CY - (miny + maxy) / 2.0)
        items = []
        for op in self.ops:
            if op[0] == 'sym':
                _, libsym, ref, value, fp, x, y, cu = op
                items.append(self._sym_sexpr(libsym, ref, value, fp, x + dx, y + dy, cu))
            elif op[0] == 'wire':
                _, x1, y1, x2, y2 = op
                items.append(f'  (wire (pts (xy {x1+dx} {y1+dy}) (xy {x2+dx} {y2+dy})) '
                             f'(stroke (width 0) (type default)) (uuid {U()}))')
            elif op[0] == 'label':
                _, net, x, y, rot, g = op
                x += dx; y += dy
                if g:
                    items.append(f'  (global_label "{net}" (shape input) (at {x} {y} {rot}) '
                                 f'(fields_autoplaced) (effects (font (size 1.27 1.27)) (justify left)) (uuid {U()}))')
                else:
                    items.append(f'  (label "{net}" (at {x} {y} {rot}) '
                                 f'(effects (font (size 1.27 1.27)) (justify left)) (uuid {U()}))')
            elif op[0] == 'text':
                _, text, x, y = op
                items.append(f'  (text "{text}" (at {x+dx} {y+dy} 0) '
                             f'(effects (font (size 1.5 1.5)) (justify left)) (uuid {U()}))')
        libdefs = []
        for name in sorted(self.used):
            libdefs.append(sym_body(name, libname="cr_primitives:%s" % name)
                           if name in PRIM else CUSTOM_BODIES[name])
        out = ['(kicad_sch (version 20230121) (generator cambridge_reverb_gen)',
               f'  (uuid {self.uuid})',
               '  (paper "A3")',
               f'  (title_block (title "Vox Cambridge Reverb -- {self.title}") (company "Reconstructed"))',
               '  (lib_symbols', "\n".join(libdefs), '  )',
               "\n".join(items),
               '  (sheet_instances (path "/" (page "1")))', ')']
        p = os.path.join(ROOT, self.fname)
        open(p, "w").write("\n".join(out) + "\n")
        return p

PRIM = set(SYMS.keys())
PINS = {name: SYMS[name]["pins"] for name in SYMS}
ROOTUUID = U()
CUSTOM_BODIES = {}
COMPONENTS = []   # structured records for the PCB generator

# Footprint assignment (THT, hand-solderable). Pad numbers match symbol pins.
FOOTPRINTS = {
 "R":   "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical",
 "C":   "Capacitor_THT:C_Disc_D7.5mm_W2.5mm_P5.00mm",
 "CP":  "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
 "L":   "cambridge_reverb:Inductor_MRB_1H_Toroid",
 "D":   "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
 "LED": "LED_THT:LED_D3.0mm",
 "FUSE":"Fuse:Fuseholder_Clip-5x20mm_Eaton_1A5601-01_Inline_P20.80x6.76mm_D1.70mm_Horizontal",
 # Panel pots are reused/off-board (wired to the panel), so on the PCB they are a
 # 3-pad wiring connector, not an on-board panel-pot footprint.
 "POT": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
 "NJFET":"Package_TO_SOT_THT:TO-92_Inline",
 "BRIDGE":"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
 "LM317":"Package_TO_SOT_THT:TO-220-3_Vertical",
 "LM1875":"Package_TO_SOT_THT:TO-220-5_Vertical",
 "OPAMP8":"Package_DIP:DIP-8_W7.62mm",
 "JACK":"Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
 "SPEAKER":"Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
 "XFMR":"Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
 "PWR_FLAG":"",   # virtual, no board footprint
 "VTL5C1":"cambridge_reverb:VTL5C1",
 "Reverb_Tank_4FB2A1C":"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
 "Footswitch_DIN6":"Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
}

# Hierarchical instance path for a symbol living in sheet `sh`.
# Toggle PATHMODE to experiment: "inst" -> /<sheetinst>, "root" -> /<root>/<sheetinst>
import os as _os
PATHMODE = _os.environ.get("PATHMODE", "inst")
def INSTPATH(sh):
    if PATHMODE == "flat": return "/%s" % sh.uuid     # sheet is its own root
    if PATHMODE == "root": return "/%s/%s" % (ROOTUUID, sh.inst)
    return "/%s" % sh.inst

# ----------------------------------------------------------------------------
# Load custom-part symbols (VTL5C1, reverb tank, DIN-6) from the curated lib:
# grab each symbol block (for embedding) and its pin endpoints (for wiring).
# ----------------------------------------------------------------------------
def load_custom():
    import re
    src = open(os.path.join(ROOT, "symbols", "cambridge_reverb.kicad_sym")).read()
    for name in ["VTL5C1", "Reverb_Tank_4FB2A1C", "Footswitch_DIN6"]:
        i = src.find(f'(symbol "{name}"')
        depth=0; j=i
        while j < len(src):
            if src[j]=='(': depth+=1
            elif src[j]==')':
                depth-=1
                if depth==0: break
            j+=1
        block = src[i:j+1]
        # rename top symbol to lib:Name for schematic embedding
        body = block.replace(f'(symbol "{name}"', f'(symbol "cambridge_reverb:{name}"', 1)
        CUSTOM_BODIES[name] = "  " + body
        # parse top-level pins (number + at x y angle)
        pins=[]
        for m in re.finditer(r'\(pin\s+\w+\s+line\s+\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\).*?\(number\s+"(\w+)"', block, re.S):
            x=float(m.group(1)); y=float(m.group(2)); a=int(m.group(3)); num=m.group(4)
            ox,oy = {0:(-1,0),180:(1,0),270:(0,1),90:(0,-1)}[a]
            pins.append((num,num,x,y,ox,oy))
        PINS[name]=pins
        SYMS.setdefault(name, dict(pins=pins))

GLOBAL_NETS = {
 "+33V5","VREG_IN","+17V","GND","SPK_P","SPK_N",
 "GUITAR_IN","PREAMP_OUT","TONE_OUT","BLEND","TREM_OUT","PA_IN",
 "MRB_OUT","FX_RET","VBIAS_R","VBIAS_T","FS_REV","FS_TREM","FS_MRB",
}
# FS_REV/FS_TREM/FS_MRB are footswitch control lines: they leave the DIN
# connector (switching sheet) and land on their effect sheet via a control
# pulldown. Exact switching topology follows the original pedal; represented
# here as defined control nets so they aren't single-ended.

def build():
    load_custom()
    sheets=[]

    # ---- Sheet 1: Power Supply ----
    s=Sheet("Power Supply","power_supply.kicad_sch"); sheets.append(s)
    s.note("POWER SUPPLY  -- bridge -> 33.5V main, 27V dropper, LM317 17V rail",50,20)
    s.comp("XFMR","T1","reuse / AnTek AS-0524",40,60,{"1":"AC1","2":"GND","3":"AC2"})
    s.comp("BRIDGE","BR1","KBP410G",80,60,{"1":"AC1","3":"AC2","2":"VRAW","4":"GND"})
    s.comp("FUSE","F1","1A SB",120,40,{"1":"VRAW","2":"+33V5"})
    s.comp("CP","C_main","4700uF/50V",120,70,{"1":"+33V5","2":"GND"})
    s.comp("R","R_bleed","10k/5W",150,70,{"1":"+33V5","2":"GND"})
    s.note("VREG_IN: LM317-input RC pre-filter (100R + C_filt1) -- ripple + power-amp decoupling; ~32V under load (not a 27V rail)",40,18)
    s.comp("R","R_27V","100R/1W",120,100,{"1":"+33V5","2":"VREG_IN"})
    s.comp("CP","C_filt1","1000uF/50V",150,100,{"1":"VREG_IN","2":"GND"})
    s.comp("LM317","U1","LM317T",90,140,{"3":"VREG_IN","2":"+17V","1":"ADJ17"})
    s.comp("R","R_reg1","240R",130,130,{"1":"+17V","2":"ADJ17"})
    s.comp("R","R_reg2","3.09k",130,160,{"1":"ADJ17","2":"GND"})
    s.comp("CP","C_reg_in","10uF/50V",60,160,{"1":"VREG_IN","2":"GND"})
    s.comp("CP","C_reg_out1","10uF/25V",160,140,{"1":"+17V","2":"GND"})
    s.comp("C","C_reg_out2","100nF",185,140,{"1":"+17V","2":"GND"})
    # Mid-rail references for single-supply op-amps. SPLIT into VBIAS_R (reverb)
    # and VBIAS_T (tremolo) so LFO current on the tremolo ref cannot modulate the
    # reverb stage (roast R6). Each: 100k/100k + 47uF bypass.
    s.note("VBIAS_R / VBIAS_T = separate mid-rail (~8.5V) refs for reverb / tremolo ICs (split, roast R6)",40,180)
    s.comp("R","R_vbr1","100k",110,195,{"1":"+17V","2":"VBIAS_R"})
    s.comp("R","R_vbr2","100k",110,220,{"1":"VBIAS_R","2":"GND"})
    s.comp("CP","C_vbr","47uF/25V",150,207,{"1":"VBIAS_R","2":"GND"})
    s.comp("R","R_vbt1","100k",185,195,{"1":"+17V","2":"VBIAS_T"})
    s.comp("R","R_vbt2","100k",185,220,{"1":"VBIAS_T","2":"GND"})
    s.comp("CP","C_vbt","47uF/25V",225,207,{"1":"VBIAS_T","2":"GND"})
    s.comp("PWR_FLAG","#FLG1","",40,30,{"1":"+33V5"})
    s.comp("PWR_FLAG","#FLG2","",70,30,{"1":"VREG_IN"})
    s.comp("PWR_FLAG","#FLG3","",100,30,{"1":"+17V"})
    s.comp("PWR_FLAG","#FLG4","",130,30,{"1":"GND"})

    # ---- Sheet 2: Preamp ----
    s=Sheet("Preamp","preamp.kicad_sch"); sheets.append(s)
    s.note("PREAMP  -- 2x JFET common-source (MMBF5457). Rs placed 2K2 (recovered); ~1-1.2k for the 8-9V drain target (errata #15)",50,20)
    s.comp("C","C_in_pre","47nF",40,60,{"1":"GUITAR_IN","2":"Q1G"})
    s.comp("R","R_g1","1M",40,90,{"1":"Q1G","2":"GND"})
    s.comp("NJFET","Q1","MMBF5457",90,70,{"2":"Q1G","1":"Q1D","3":"Q1S"})
    s.comp("R","R_d1","10k",90,40,{"1":"+17V","2":"Q1D"})
    s.comp("R","R_s1","2K2",90,110,{"1":"Q1S","2":"GND"})
    s.comp("CP","C_s1","10uF/25V",130,110,{"1":"Q1S","2":"GND"})
    s.comp("C","C_cpl12","100nF",130,70,{"1":"Q1D","2":"Q2G"})
    s.comp("R","R_g2","1M",130,95,{"1":"Q2G","2":"GND"})
    s.comp("NJFET","Q2","MMBF5457",175,70,{"2":"Q2G","1":"Q2D","3":"Q2S"})
    s.comp("R","R_d2","10k",175,40,{"1":"+17V","2":"Q2D"})
    s.comp("C","C_pres","100pF",175,110,{"1":"Q2D","2":"GND"})
    s.comp("R","R_s2","2K2",215,95,{"1":"Q2S","2":"GND"})
    s.comp("CP","C_s2","10uF/25V",215,120,{"1":"Q2S","2":"GND"})
    s.comp("C","C_treble","470pF",215,55,{"1":"Q2D","2":"PREAMP_OUT"})

    # ---- Sheet 3: Tone Stack ----
    s=Sheet("Tone Stack","tone_stack.kicad_sch"); sheets.append(s)
    s.note("TONE STACK -- Vox top-boost network. VALUES TBD (cross-check #4): replicate 25-5274-2.",40,20)
    s.comp("POT","POT_VOL","reuse",70,70,{"1":"PREAMP_OUT","2":"VOL_W","3":"GND"})
    s.comp("POT","POT_TONE","reuse",140,70,{"1":"VOL_W","2":"TONE_OUT","3":"GND"})
    s.comp("R","R_fx_pad","10k",110,120,{"1":"VOL_W","2":"FX_RET"})
    s.comp("C","C_tone_tbd","TBD",170,110,{"1":"TONE_OUT","2":"GND"})

    # ---- Sheet 4: Reverb (netlist-notes sheet 4) ----
    s=Sheet("Reverb","reverb.kicad_sch"); sheets.append(s)
    s.note("REVERB -- IC1-A: TL072 tank driver (11x) + JFET recovery. IC1-B: active wet/dry summer (roast R3). All on VBIAS_R.",40,20)
    # IC1-A = tank driver (pins 1,2,3) ; IC1-B = wet/dry summing mixer (pins 5,6,7)
    s.comp("OPAMP8","IC1","TL072CP",110,80,{"3":"DRVP","2":"R_INV","1":"R_DRVO",
            "8":"+17V","4":"GND","5":"VBIAS_R","6":"SUMJ","7":"BLEND"})
    s.comp("C","C_drvin","100nF",40,165,{"1":"TONE_OUT","2":"DRVP"})   # AC couple in
    s.comp("R","R_drvbias","220k",75,165,{"1":"DRVP","2":"VBIAS_R"})   # mid-rail bias
    s.comp("R","R_drv1","100k",150,55,{"1":"R_INV","2":"R_DRVO"})
    s.comp("R","R_drv2","10k",150,110,{"1":"R_INV","2":"VBIAS_R"})     # AC gnd via VBIAS_R
    s.comp("CP","C_rev1","1uF",160,80,{"1":"R_DRVO","2":"TKDRV"})
    s.comp("R","R_drv3","10R",195,80,{"1":"TKDRV","2":"TANK_IN"})
    s.comp("Reverb_Tank_4FB2A1C","REV1","4FB2A1C",235,90,
            {"1":"TANK_IN","2":"GND","3":"TANK_OUT","4":"GND"})
    s.comp("C","C_rev2","10nF",60,120,{"1":"TANK_OUT","2":"QRG"})
    s.comp("NJFET","Q_rec","MMBF5457",110,140,{"2":"QRG","1":"QRD","3":"QRS"})
    s.comp("R","R_rec_bias","1M",60,150,{"1":"QRG","2":"GND"})
    s.comp("R","R_rec1","10k",110,115,{"1":"+17V","2":"QRD"})
    s.comp("R","R_rec2","2K2",110,170,{"1":"QRS","2":"GND"})
    s.comp("CP","C_rec_byp","10uF",150,170,{"1":"QRS","2":"GND"})
    s.comp("C","C_rev4","100nF",150,140,{"1":"QRD","2":"REVWCW"})
    s.comp("POT","POT_REV","reuse",200,150,{"1":"REVWCW","2":"WET","3":"GND"})  # reverb-level (wet send)
    # IC1-B active inverting summer (roast R3): dry always on, wet via POT_REV.
    # Out = -(dry + wet) about VBIAS_R, low-Z. Unity each (all 100k).
    s.comp("R","R_mixfb","100k",90,55,{"1":"SUMJ","2":"BLEND"})        # summer feedback
    s.comp("C","C_drymix","1uF",20,40,{"1":"TONE_OUT","2":"DRMX"})     # dry in (AC)
    s.comp("R","R_drymix","100k",55,40,{"1":"DRMX","2":"SUMJ"})        # dry -> summer
    s.comp("C","C_wetmix","1uF",230,150,{"1":"WET","2":"WMX"})         # wet in (post POT_REV)
    s.comp("R","R_wetmix","100k",265,150,{"1":"WMX","2":"SUMJ"})       # wet -> summer
    s.comp("R","R_fs_rev","100k",30,170,{"1":"FS_REV","2":"GND"})   # footswitch control tap

    # ---- Sheet 5: Tremolo (netlist-notes sheet 5) ----
    s=Sheet("Tremolo","tremolo.kicad_sch"); sheets.append(s)
    s.note("TREMOLO -- IC2-A: Wien LFO (~16Hz) -> VTL5C1. IC2-B: post-MRB output buffer -> PA_IN. All on VBIAS_T.",40,20)
    # IC2-A = LFO (pins 1,2,3) ; IC2-B = output buffer (pins 5,6,7), follower to PA_IN
    s.comp("OPAMP8","IC2","TL072CP",110,90,{"3":"LFO_P","2":"LFO_N","1":"LFO_OUT",
            "8":"+17V","4":"GND","5":"OBUF_IN","6":"PA_IN","7":"PA_IN"})
    s.comp("C","C_obuf_in","1uF",30,40,{"1":"MRB_OUT","2":"OBUF_IN"})  # post-MRB into buffer
    s.comp("R","R_obuf_b","100k",30,70,{"1":"OBUF_IN","2":"VBIAS_T"})  # bias buffer mid-rail
    s.comp("R","R_lfo_ser","100k",150,60,{"1":"LFO_OUT","2":"WN1"})
    s.comp("C","C_lfo1","100nF",185,60,{"1":"WN1","2":"LFO_P"})
    s.comp("R","R_lfo1","33k",150,120,{"1":"LFO_P","2":"VBIAS_T"})  # LFO biased to mid-rail
    s.comp("C","C_lfo2","100nF",185,120,{"1":"LFO_P","2":"VBIAS_T"})
    s.comp("R","R_lfo_fb1","10k",70,70,{"1":"LFO_OUT","2":"LFO_N"})
    s.comp("R","R_lfo_fb2","4K7",70,110,{"1":"LFO_N","2":"VBIAS_T"}) # AC gnd via VBIAS_T
    s.comp("D","D_lfo1","1N4148",40,70,{"1":"LFO_OUT","2":"LFO_N"})
    s.comp("D","D_lfo2","1N4148",40,100,{"1":"LFO_N","2":"LFO_OUT"})
    s.comp("R","R_led","1k",150,150,{"1":"LFO_OUT","2":"VLED"})
    s.comp("VTL5C1","VTL1","VTL5C1",200,150,{"1":"VLED","2":"GND","3":"TREM_S","4":"GND"})
    s.comp("R","R_led_diag","2K2",150,180,{"1":"LFO_OUT","2":"DLED"})
    s.comp("LED","LED_rate","3mm red",195,180,{"1":"DLED","2":"GND"})
    s.comp("R","R_trem1","10k",60,150,{"1":"BLEND","2":"TREM_OUT"})  # series; VTL1 LDR shunts to GND
    s.comp("CP","C_dc_blk","10uF",60,180,{"1":"TREM_OUT","2":"TREM_S"})
    # (removed dead C_trem_out/R_trem_pass MRB_FEED branch -- TREM_OUT feeds MRB directly)
    s.comp("R","R_fs_trem","100k",30,180,{"1":"FS_TREM","2":"GND"})   # footswitch control tap

    # ---- Sheet 6: MRB (netlist-notes sheet 6) ----
    s=Sheet("MRB","mrb.kicad_sch"); sheets.append(s)
    s.note("MRB -- parallel LC tank, default 600 Hz (1H || 68n). 450/750 internal-only.",40,20)
    s.comp("C","C_mrb_in","100nF",50,70,{"1":"TREM_OUT","2":"MRB_N"})
    s.comp("R","R_mrb_ser","10k",90,70,{"1":"MRB_N","2":"MRB_T"})
    s.comp("L","L1","1H toroid",130,100,{"1":"MRB_T","2":"GND"})
    s.comp("C","C_mrb_600","68nF",170,100,{"1":"MRB_T","2":"GND"})
    s.comp("C","C_mrb_450","120nF (opt)",170,130,{"1":"MRB_T","2":"GND"})
    s.comp("C","C_mrb_750","47nF (opt)",170,160,{"1":"MRB_T","2":"GND"})
    s.comp("C","C_mrb_out","100nF",90,130,{"1":"MRB_T","2":"MRB_OUT"})
    s.comp("R","R_fs_mrb","100k",50,160,{"1":"FS_MRB","2":"GND"})   # footswitch control tap

    # ---- Sheet 7: Power Amp (netlist-notes sheet 7, verbatim) ----
    s=Sheet("Power Amp","power_amp.kicad_sch"); sheets.append(s)
    s.note("POWER AMP -- LM1875, gain 23x. Sim: HF -3dB 6.8kHz (C_fb_hf), LF ~17Hz.",40,20)
    s.comp("C","C_in_pa","1uF film",40,70,{"1":"PA_IN","2":"PA_BIAS"})
    s.comp("R","R_bias1","22k",40,45,{"1":"+33V5","2":"PA_BIAS"})
    s.comp("R","R_bias2","22k",40,95,{"1":"PA_BIAS","2":"GND"})
    s.comp("LM1875","IC_PA","LM1875T",110,80,{"1":"PA_BIAS","2":"PA_INV","4":"PA_OUT","5":"+33V5","3":"GND"})
    s.comp("R","R_fb","22k",150,50,{"1":"PA_INV","2":"PA_OUT"})
    s.comp("C","C_fb_hf","1nF",150,30,{"1":"PA_INV","2":"PA_OUT"})
    s.comp("R","R_gain","1k",70,120,{"1":"PA_INV","2":"PA_GAIN"})
    s.comp("CP","C_gain","22uF/25V",110,120,{"1":"PA_GAIN","2":"GND"})
    s.comp("R","R_zobel","10R",160,110,{"1":"PA_OUT","2":"ZOB"})
    s.comp("C","C_zobel","100nF",190,110,{"1":"ZOB","2":"GND"})
    s.comp("CP","C_out","2200uF/35V",160,80,{"1":"PA_OUT","2":"SPK_P"})
    s.comp("D","D1","1N4007",150,150,{"1":"PA_OUT","2":"+33V5"})
    s.comp("D","D2","1N4007",190,150,{"1":"GND","2":"PA_OUT"})
    s.comp("C","C_byp1","100nF",40,150,{"1":"+33V5","2":"GND"})
    s.comp("CP","C_byp2","10uF/50V",75,150,{"1":"+33V5","2":"GND"})

    # ---- Sheet 8: Switching / I-O ----
    s=Sheet("Switching / I-O","switching.kicad_sch"); sheets.append(s)
    s.note("SWITCHING / I-O -- input jacks (IN3=internal FX loop), footswitch DIN, speaker.",40,20)
    s.comp("JACK","J_IN1","Input 1",60,60,{"1":"GUITAR_IN","2":"GND"})
    s.comp("JACK","J_IN2","Input 2",60,90,{"1":"GUITAR_IN","2":"GND"})
    s.comp("JACK","J_IN3","IN3 / FX return",60,120,{"1":"FX_RET","2":"GND"})
    s.comp("Footswitch_DIN6","FS1","DIN-6",150,90,
            {"1":"FS_REV","2":"FS_TREM","3":"FS_MRB","4":"GND","5":"GND","6":"GND"})
    s.comp("SPEAKER","LS1","10in Bulldog",210,150,{"1":"SPK_P","2":"SPK_N"})
    s.comp("R","R_spk_rtn","0R",170,150,{"1":"SPK_N","2":"GND"})
    # (R_painput removed -- IC2-B buffer now drives PA_IN from MRB_OUT, roast R3)

    return sheets

def write_root(sheets):
    out=[]
    out.append('(kicad_sch (version 20230121) (generator cambridge_reverb_gen)')
    out.append(f'  (uuid {ROOTUUID})')
    out.append('  (paper "A3")')
    out.append('  (title_block (title "Vox Cambridge Reverb -- Root") (company "Reconstructed"))')
    out.append('  (lib_symbols)')
    out.append('  (text "Signal flow: GUITAR_IN -> Preamp -> Tone -> [Reverb blend] -> Tremolo -> MRB -> Power Amp -> Speaker.\\nInter-sheet nets use global labels. Routing among effects is a documented assumption where the recovered notes are silent (see kicad/SCHEMATIC-BUILD.md)." (at 30 25 0) (effects (font (size 2 2)) (justify left)) (uuid %s))' % U())
    x=40; y=60; col=0
    for sh in sheets:
        out.append(f'  (sheet (at {x} {y}) (size 50 30) (fields_autoplaced)')
        out.append('    (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))')
        out.append(f'    (uuid {sh.inst})')
        out.append(f'    (property "Sheetname" "{sh.title}" (at {x} {y-1} 0) (effects (font (size 1.5 1.5)) (justify left bottom)))')
        out.append(f'    (property "Sheetfile" "{sh.fname}" (at {x} {y+31} 0) (effects (font (size 1.2 1.2)) (justify left top)))')
        out.append(f'    (instances (project "cambridge_reverb" (path "/{ROOTUUID}" (page "{col+2}"))))')
        out.append('  )')
        col+=1; x+=70
        if x>250: x=40; y+=50
    # page numbers
    out.append('  (sheet_instances')
    out.append('    (path "/" (page "1"))')
    out.append('  )')
    out.append(')')
    open(os.path.join(ROOT,"cambridge_reverb.kicad_sch"),"w").write("\n".join(out)+"\n")

if __name__ == "__main__":
    write_primitives_lib()
    sheets = build()
    for sh in sheets:
        sh.render()
    write_root(sheets)
    print("generated root + %d sheets" % len(sheets))
