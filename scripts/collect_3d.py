#!/usr/bin/env python3
"""Collect the 3D models for every footprint on the board into an organised
   controlcarreta/3d_models/ tree and write a manifest + relink helper."""
import os, re, shutil, glob, json, sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PROJ, "3d_models")
KI_FP = "/usr/share/kicad/footprints"
KI_3D = "/usr/share/kicad/3dmodels"
ENV3D = {"KISYS3DMOD": KI_3D, "KICAD9_3DMODEL_DIR": KI_3D, "KICAD8_3DMODEL_DIR": KI_3D,
         "KICAD7_3DMODEL_DIR": KI_3D, "KICAD6_3DMODEL_DIR": KI_3D, "KIPRJMOD": PROJ}
# extra places project-custom footprints / models may live
EXTRA_FP = [os.path.join(PROJ, "libraries"),
            "/home/felipe/Documents/Documents/libraries",
            "/home/felipe/Documents/libraries",
            "/home/felipe/Documents/Documents/kicad/libraries"]

FOOTPRINTS = [
    "Button_Switch_THT:SW_PUSH_6mm", "Capacitor_SMD:CP_Elec_8x10.5",
    "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder",
    "Connector_Card:nanoSIM_Hinged_CUI_NSIM-2-C",
    "Connector_Coaxial:SMA_Amphenol_132134-16_Vertical",
    "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
    "Connector_Dsub:DSUB-9_Pins_Horizontal_P2.77x2.84mm_EdgePinOffset9.40mm",
    "Connector_PCBEdge:mini_PCIe_Molex_679100000",
    "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "Connector_USB:USB_C_Receptacle_GCT_USB4085",
    "Diode_SMD:D_2114_3652Metric", "Diode_SMD:D_SMA", "Diode_SMD:D_SOD-123",
    "Diode_SMD:D_SOD-123F", "Inductor_SMD:L_Bourns_SDR1806",
    "LED_SMD:LED_0805_2012Metric", "LED_THT:LED_D5.0mm", "MOLEX10POS:MOLEX10POS",
    "MountingHole:MountingHole_2.2mm_M2", "MountingHole:MountingHole_4.3mm_M4",
    "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm",
    "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "Package_TO_SOT_SMD:SOT-23-6",
    "Package_TO_SOT_SMD:TO-263-5_TabPin3", "RF_Module:ESP32-S3-WROOM-1",
    "Resistor_SMD:R_1206_3216Metric", "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder",
    "SI4447ADY-T1-GE3:SOIC127P600X175-8N",
    "TerminalBlock:TerminalBlock_Altech_AK300-2_P5.00mm",
    "fuse:FUSC6125X279N", "sdcard:sdcardgoia",
]

# explicit model source for parts whose bundled/relative model is missing or broken
DOC = "/home/felipe/Documents/Documents"
EXPLICIT = {
    "MOLEX10POS:MOLEX10POS": DOC + "/libraries/MOLEX10POS/MOLEX10POS.stp",
    "fuse:FUSC6125X279N": PROJ + "/libraries/fuse/0679L5000-05.step",
    "sdcard:sdcardgoia": PROJ + "/libraries/sdcard/micro SD Card Slot.step",
    "SI4447ADY-T1-GE3:SOIC127P600X175-8N": PROJ + "/libraries/Si4447ADY/SO8.STEP",
    "TerminalBlock:TerminalBlock_Altech_AK300-2_P5.00mm":
        PROJ + "/libraries/Tblock/DG302-5.0mm/STEP/DG302-5.0-xxP (pitch 5.0mm)/DG302-5.0-02P-12-00AH.STEP",
    # SMA 132134-16 model is absent in KiCad 9 packages3d -> use the near-identical -11
    "Connector_Coaxial:SMA_Amphenol_132134-16_Vertical":
        KI_3D + "/Connector_Coaxial.3dshapes/SMA_Amphenol_132134-11_Vertical.step",
}
NO_MODEL_OK = {"MountingHole:MountingHole_2.2mm_M2", "MountingHole:MountingHole_4.3mm_M4"}

CATEGORY = {
    "RF_Module": "modules", "Connector_PCBEdge": "modules",
    "Package_SO": "ics", "Package_TO_SOT_SMD": "ics", "SI4447ADY-T1-GE3": "ics",
    "Connector_USB": "connectors", "Connector_Dsub": "connectors",
    "Connector_Coaxial": "connectors", "Connector_Card": "connectors",
    "Connector_PinHeader_2.54mm": "connectors", "MOLEX10POS": "connectors",
    "TerminalBlock": "connectors", "sdcard": "connectors",
    "Resistor_SMD": "passives", "Capacitor_SMD": "passives", "Inductor_SMD": "passives",
    "Diode_SMD": "passives", "LED_SMD": "passives", "LED_THT": "passives",
    "Button_Switch_THT": "passives",
    "fuse": "power", "MountingHole": "mechanical",
}

def find_kicad_mod(libnick, name):
    cands = [os.path.join(KI_FP, libnick + ".pretty", name + ".kicad_mod")]
    for base in EXTRA_FP:
        cands += [os.path.join(base, libnick + ".pretty", name + ".kicad_mod"),
                  os.path.join(base, libnick, name + ".kicad_mod")]
        cands += glob.glob(os.path.join(base, "**", libnick + ".pretty", name + ".kicad_mod"), recursive=True)
        cands += glob.glob(os.path.join(base, libnick, "**", name + ".kicad_mod"), recursive=True)
    for c in cands:
        if os.path.isfile(c):
            return c
    return None

def resolve_model(path, modfile):
    p = path
    for k, v in ENV3D.items():
        p = p.replace("${%s}" % k, v).replace("$(%s)" % k, v)
    if not os.path.isabs(p):
        p = os.path.normpath(os.path.join(os.path.dirname(modfile), p))
    return p

def variants(p):
    """given a resolved model path (maybe .wrl / .step / none), yield existing files"""
    stem, _ = os.path.splitext(p)
    seen = []
    for ext in (".step", ".stp", ".STEP", ".STP", ".wrl", ".WRL", ".x3d"):
        f = stem + ext
        if os.path.isfile(f) and f not in seen:
            seen.append(f)
    return seen

# footprint -> model path, harvested from the current PCB
PCB_MAP = {}
pcb = open(os.path.join(PROJ, "controlcarreta.kicad_pcb"), encoding="utf-8", errors="ignore").read()
for m in re.finditer(r'\(footprint "([^"]+)"', pcb):
    nxt = pcb.find('(footprint "', m.start() + 12)
    blk = pcb[m.start(): nxt if nxt > 0 else len(pcb)]
    mm = re.findall(r'\(model "([^"]+)"', blk)
    if mm:
        PCB_MAP.setdefault(m.group(1), mm[0])

os.makedirs(OUT, exist_ok=True)
manifest = {}
missing = []
copied = 0
for fp in FOOTPRINTS:
    nick, name = fp.split(":", 1)
    cat = CATEGORY.get(nick, "misc")
    modf = find_kicad_mod(nick, name)
    entry = {"footprint": fp, "category": cat, "kicad_mod": modf, "models": []}
    files = []
    # 0) explicit override
    if fp in EXPLICIT and os.path.isfile(EXPLICIT[fp]):
        files.append(EXPLICIT[fp])
    # 1) model line(s) in the footprint file
    if not files and modf:
        txt = open(modf, encoding="utf-8", errors="ignore").read()
        for mp in re.findall(r'\(model\s+"([^"]+)"', txt):
            for vf in variants(resolve_model(mp.strip(), modf)):
                files.append(vf)
    # 2) model path recorded in the PCB for this footprint
    if fp in PCB_MAP:
        for vf in variants(resolve_model(PCB_MAP[fp], os.path.join(PROJ, "x"))):
            files.append(vf)
        # also the exact file (covers .stp / odd names)
        rp = resolve_model(PCB_MAP[fp], os.path.join(PROJ, "x"))
        if os.path.isfile(rp):
            files.append(rp)
    # 3) bundled 3dshapes by library/name
    if not files:
        for guess in glob.glob(os.path.join(KI_3D, nick + ".3dshapes", name + ".*")):
            files.append(guess)
    files = sorted(set(files))
    if not files:
        if fp not in NO_MODEL_OK:
            missing.append(fp)
        entry["note"] = "no 3D model needed" if fp in NO_MODEL_OK else "3D MODEL MISSING - source manually"
        manifest[fp] = entry
        continue
    dstdir = os.path.join(OUT, cat)
    os.makedirs(dstdir, exist_ok=True)
    for f in files:
        base = os.path.basename(f)
        dst = os.path.join(dstdir, base)
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(f):
            shutil.copy2(f, dst)
            copied += 1
        entry["models"].append(os.path.relpath(dst, PROJ))
    manifest[fp] = entry

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
print("copied %d model files into %s" % (copied, OUT))
print("MISSING 3D model for %d footprints:" % len(missing))
for m in missing:
    print("   -", m)
