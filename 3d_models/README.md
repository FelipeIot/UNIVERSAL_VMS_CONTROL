# 3d_models/ — modelos 3D del proyecto

Todos los modelos 3D de los componentes de la placa, **locales al proyecto** y
organizados por categoría. Así el proyecto es portátil (se puede mover/archivar
y las vistas 3D siguen funcionando) y no depende de rutas absolutas del PC.

```
3d_models/
├── modules/        ESP32-S3-WROOM-1, zócalo Mini PCIe
├── ics/            MAX3232, NCP1117, USBLC6, LM2596, 74LVC8T245, SI4447
├── connectors/     USB-C, DE9, nano-SIM, u.FL, SMA, bornera, header, MOLEX, microSD
├── passives/       R, C, L, diodos, LED, pulsadores
├── power/          fusible
├── mechanical/     (taladros de montaje — no necesitan modelo)
└── manifest.json   footprint → categoría → archivo(s) de modelo
```

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
   Reescribe todas las líneas `(model ...)` del `.kicad_pcb` para que apunten a
   esta carpeta. Idempotente; deja un `.bak`.
3. Recarga la placa en Pcbnew y abre el visor 3D (Alt+3).

### Regenerar la carpeta
```
python3 scripts/collect_3d.py
```
Vuelve a copiar los modelos desde las librerías de KiCad (`/usr/share/kicad/3dmodels`)
y desde `libraries/` del proyecto. Requiere el paquete `kicad-packages3d`.

## Notas / pendientes

| Footprint | Estado |
|---|---|
| `Connector_PCBEdge:mini_PCIe_Molex_679100000` (J14) | **FALTA modelo.** Este footprint hay que crearlo/descargarlo — KiCad no trae ni el footprint ni el 3D del zócalo Mini PCIe. Fuentes: Molex 67910-xxxx, Amphenol MDT4xx, GCT MPCIE, o SnapEDA/Ultra Librarian. Colócalo en `3d_models/modules/` y añade la línea `(model ...)` al footprint. |
| `SMA_Amphenol_132134-16_Vertical` (J1255) | Se usó el modelo del **-11** (casi idéntico) porque el `-16` no viene en `kicad-packages3d` 9.0. Cámbialo si consigues el exacto. |
| `TerminalBlock_Altech_AK300-2` (J1/J2) | Modelo = `DG302-5.0-02P` (bornera equivalente 5 mm de `libraries/Tblock/`). |
| Taladros M2/M4 | Sin modelo — es correcto, son sólo agujeros. |

Modelos propios del proyecto (no de KiCad): `MOLEX10POS.stp`, `SO8.STEP`
(SI4447), `0679L5000-05.step` (fusible), `micro SD Card Slot.step`,
`DG302-5.0-02P-12-00AH.STEP` — copiados de `libraries/` y de
`~/Documents/Documents/libraries/`.
