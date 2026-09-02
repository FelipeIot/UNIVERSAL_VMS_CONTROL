#!/usr/bin/env python3
"""Collect the 3D models for every footprint on the board into an organised
   controlcarreta/3DSHAPES/ tree and write a manifest + relink helper."""
import os, re, shutil, glob, json, sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PROJ, "3DSHAPES")
KI_FP = "/usr/share/kicad/footprints"
KI_3D = "/usr/share/kicad/3dmodels"
ENV3D = {"KISYS3DMOD": KI_3D, "KICAD9_3DMODEL_DIR": KI_3D, "KICAD8_3DMODEL_DIR": KI_3D,
         "KICAD7_3DMODEL_DIR": KI_3D, "KICAD6_3DMODEL_DIR": KI_3D, "KIPRJMOD": PROJ}
# extra places project-custom footprints / models may live
EXTRA_FP = [os.path.join(PROJ, "libraries"),
            "/home/felipe/Documents/Documents/libraries",
            "/home/felipe/Documents/libraries",
            "/home/felipe/Documents/Documents/kicad/libraries"]

# footprints taken live from the schematic Footprint fields
def _footprints_from_sch():
    sch = open(os.path.join(PROJ, "controlcarreta.kicad_sch"), encoding="utf-8", errors="ignore").read()
    fps = set()
    for blk in re.split(r'\n\t\(symbol\n', sch)[1:]:
        if '(lib_id' not in blk:
            continue
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk)
        if not ref or ref.group(1).startswith('#'):
            continue
        m = re.search(r'\(property "Footprint" "([^"]+)"', blk)
        if m and ':' in m.group(1):
            fps.add(m.group(1))
    return sorted(fps)

FOOTPRINTS = _footprints_from_sch()

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
NO_MODEL_OK = {"MountingHole:MountingHole_4.3mm_M4"}

CATEGORY = {
    "RF_Module": "modules", "Connector_PCBEdge": "connectors",
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
    # 4) already collected here by a previous run.  The originals under libraries/
    #    are gitignored (modelos pesados), so for the project-custom parts the copy
    #    inside 3DSHAPES/ is the only surviving one -- never drop it.
    if not files and fp in EXPLICIT:
        kept = os.path.join(OUT, cat, os.path.basename(EXPLICIT[fp]))
        if os.path.isfile(kept):
            files.append(kept)
    # one model per footprint, source priority preserved, STEP preferred over WRL
    files = list(dict.fromkeys(files))
    if files:
        stem0 = os.path.splitext(files[0])[0]
        same = [f for f in files if os.path.splitext(f)[0] == stem0]
        step = [f for f in same if os.path.splitext(f)[1].lower() in (".step", ".stp")]
        files = [step[0] if step else files[0]]
    if not files:
        # stock KiCad footprint whose model just isn't installed on this machine ->
        # keep the ${KICAD9_3DMODEL_DIR} path; it resolves with a full kicad-packages3d.
        stock_model = None
        if modf and KI_FP in modf:
            mtxt = open(modf, encoding="utf-8", errors="ignore").read()
            mm = re.search(r'\(model\s+"([^"]+)"', mtxt)
            if mm:
                stock_model = mm.group(1)
        if fp in NO_MODEL_OK:
            entry["note"] = "no 3D model needed"
        elif stock_model:
            entry["note"] = "modelo referenciado por el footprint pero ausente en kicad-packages3d -> " + stock_model
        else:
            missing.append(fp)
            entry["note"] = "3D MODEL MISSING - source manually"
        manifest[fp] = entry
        continue
    dstdir = os.path.join(OUT, cat)
    os.makedirs(dstdir, exist_ok=True)
    for f in files:
        base = os.path.basename(f)
        dst = os.path.join(dstdir, base)
        if os.path.abspath(f) != os.path.abspath(dst) and (
                not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(f)):
            shutil.copy2(f, dst)
            copied += 1
        entry["models"].append(os.path.relpath(dst, PROJ))
    manifest[fp] = entry

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
print("copied %d model files into %s" % (copied, OUT))
print("MISSING 3D model for %d footprints:" % len(missing))
for m in missing:
    print("   -", m)
