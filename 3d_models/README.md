# 3d_models/ — modelos 3D del proyecto

Todos los modelos 3D de los componentes de la placa, **locales al proyecto** y
organizados por categoría. Así el proyecto es portátil (se puede mover/archivar
y las vistas 3D siguen funcionando) y no depende de rutas absolutas del PC.

```
3d_models/
├── modules/        ESP32-S3-WROOM-1
├── ics/            MAX3232, NCP1117, USBLC6, LM2596, 74LVC8T245, SI4447
├── connectors/     USB-C, DE9, nano-SIM, u.FL, SMA, bornera, header, MOLEX, microSD, Mini PCIe
├── passives/       R, C, L, diodos, LED, pulsadores
├── power/          fusible
└── manifest.json   footprint → categoría → archivo(s) de modelo
```

(Los taladros de montaje no llevan modelo — es correcto.)

## Cómo se usa

Los footprints referencian el modelo como
`${KIPRJMOD}/3d_models/<categoría>/<archivo>` — `${KIPRJMOD}` es una variable
interna de KiCad que apunta a la carpeta del proyecto, así que funciona en
cualquier PC sin configurar nada.

### Flujo tras cambiar el esquemático
1. En Pcbnew: **Tools → Update PCB from Schematic** (trae los footprints nuevos
   con sus rutas de modelo por defecto).
2. Ejecuta el reenlazador:
   ```
   python3 scripts/relink_3d.py
   ```
   Reescribe las líneas `(model ...)` del `.kicad_pcb` para que apunten a esta
   carpeta. Idempotente; deja un `.bak`.
3. Recarga la placa en Pcbnew y abre el visor 3D (Alt+3).

### Regenerar la carpeta
```
python3 scripts/collect_3d.py
```
Lee los footprints del esquemático, copia los modelos desde `kicad-packages3d`
(`/usr/share/kicad/3dmodels`) y desde `libraries/` del proyecto.

## Notas / pendientes

| Footprint | Estado |
|---|---|
| `Connector_PCBEdge:BUS_PCI_Express_Mini_Full` (J14) | Footprint **estándar de KiCad** (zócalo Mini PCIe 52 pines). Su modelo 3D (`Connector_PCBEdge.3dshapes/BUS_PCI_Express_Mini_Full.step`) viene en el `kicad-packages3d` completo — esta máquina lo tiene incompleto, así que se deja la ruta `${KICAD9_3DMODEL_DIR}/...` (resuelve sola en una instalación completa, o descárgalo del repo oficial `kicad-packages3D`). |
| `Connector_PCBEdge:JAE_MM60-EZH039-Bx_BUS_PCI_Express_Holder` (H5) | Retención/latch del Mini PCIe. Igual: footprint estándar, modelo en `kicad-packages3d`. |
| `SMA_Amphenol_132134-16_Vertical` (J1255) | Se usó el modelo del **-11** (casi idéntico) porque el `-16` no viene en el `kicad-packages3d` de esta máquina. |
| `TerminalBlock_Altech_AK300-2` (J1/J2) | Modelo = `DG302-5.0-02P` (bornera equivalente 5 mm de `libraries/Tblock/`). |
| `nanoSIM_Hinged_CUI_NSIM-2-C` (J15) | El `microSIM_JAE` que puse primero no tenía modelo 3D en KiCad 9; cambiado a este portaSIM que sí lo trae. |
| Taladro M4 (H1–H4) | Sin modelo — es correcto, son agujeros. |

Modelos propios del proyecto (no de KiCad): `MOLEX10POS.stp`, `SO8.STEP`
(SI4447), `0679L5000-05.step` (fusible), `micro SD Card Slot.step`,
`DG302-5.0-02P-12-00AH.STEP` — copiados de `libraries/` y de
`~/Documents/Documents/libraries/`.
