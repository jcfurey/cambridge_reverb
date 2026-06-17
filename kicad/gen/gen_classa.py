#!/usr/bin/env python3
"""Generate the Class-A power-amp VARIANT as a standalone schematic.

A drop-in alternative to the main `power_amp` sheet: the same LM1875 stage plus an
LM317 constant-current sink (I = 1.25/R_set = 0.5 A) from the output to ground, so
the LM1875 runs single-ended Class A up to ~1 W into 8 ohm (AB beyond). Kept
SEPARATE from the main design (variant alongside AB) -- see docs/classA-power-amp.md.

Run from repo root:  python3 kicad/gen/gen_classa.py
"""
import os, sys
os.environ["PATHMODE"] = "flat"          # standalone root schematic
sys.path.insert(0, os.path.dirname(__file__))
import gen_kicad as g

g.write_primitives_lib()
s = g.Sheet("Power Amp -- Class-A variant", "power_amp_classa.kicad_sch")
s.note("CLASS-A VARIANT: LM1875 + LM317 constant-current sink (~0.5A) from output to GND => single-ended Class A up to ~1W, AB beyond. ~16W standing heat -> <=1.5 C/W sinks. See docs/classA-power-amp.md.", 40, 12)

# --- LM1875 power stage (identical to the main power_amp sheet) ---
s.comp("C","C_in_pa","1uF",40,70,{"1":"PA_IN","2":"PA_BIAS"})
s.comp("R","R_bias1","22k",40,45,{"1":"+33V5","2":"PA_BIAS"})
s.comp("R","R_bias2","22k",40,95,{"1":"PA_BIAS","2":"GND"})
s.comp("LM1875","IC_PA","LM1875T",110,80,{"1":"PA_BIAS","2":"PA_INV","4":"PA_OUT","5":"+33V5","3":"GND"})
s.comp("R","R_fb","22k",150,50,{"1":"PA_INV","2":"PA_OUT"})
s.comp("C","C_fb_hf","1nF",150,30,{"1":"PA_INV","2":"PA_OUT"})
s.comp("R","R_gain","1k",70,120,{"1":"PA_INV","2":"PA_GAIN"})
s.comp("CP","C_gain","22uF/25V",110,120,{"1":"PA_GAIN","2":"GND"})
s.comp("R","R_zobel","10R",165,110,{"1":"PA_OUT","2":"ZOB"})
s.comp("C","C_zobel","100nF",195,110,{"1":"ZOB","2":"GND"})
s.comp("CP","C_out","2200uF/35V",160,80,{"1":"PA_OUT","2":"SPK_P"})
s.comp("D","D1","1N4007",150,150,{"1":"PA_OUT","2":"+33V5"})
s.comp("D","D2","1N4007",195,150,{"1":"GND","2":"PA_OUT"})
s.comp("C","C_byp1","100nF",40,150,{"1":"+33V5","2":"GND"})
s.comp("CP","C_byp2","10uF/50V",75,150,{"1":"+33V5","2":"GND"})

# --- Class-A bias: LM317 constant-current SINK, PA_OUT -> GND, I=1.25/R_set ---
s.comp("LM317","U_ccs","LM317T CCS",110,185,{"3":"PA_OUT","2":"CCS_O","1":"GND"})
s.comp("R","R_set","2.5R 2W",155,185,{"1":"CCS_O","2":"GND"})  # 1.25/2.5 = 0.5A

# --- I/O so no net is single-ended (clean standalone ERC) ---
s.comp("JACK","J_PAIN","from preamp",30,40,{"1":"PA_IN","2":"GND"})
s.comp("SPEAKER","LS1","10in 8ohm",215,80,{"1":"SPK_P","2":"SPK_N"})
s.comp("R","R_spk_rtn","0R",185,95,{"1":"SPK_N","2":"GND"})
s.comp("PWR_FLAG","#FLG1","",30,150,{"1":"+33V5"})
s.comp("PWR_FLAG","#FLG2","",60,40,{"1":"GND"})

path = s.render()

# minimal project so kicad-cli can ERC it standalone
pro = os.path.join(g.ROOT, "power_amp_classa.kicad_pro")
open(pro, "w").write('{"meta":{"filename":"power_amp_classa.kicad_pro","version":1},'
                     '"schematic":{},"sheets":[],"libraries":{"pinned_symbol_libs":[],"pinned_footprint_libs":[]}}\n')
print("wrote", path)
