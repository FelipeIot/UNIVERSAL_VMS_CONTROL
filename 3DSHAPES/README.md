# 3DSHAPES/ — modelos 3D del proyecto

Todos los modelos 3D de los componentes de la placa, **locales al proyecto** y
organizados por categoría. Así el proyecto es portátil (se puede mover/archivar
y las vistas 3D siguen funcionando) y no depende de rutas absolutas del PC.

```
3DSHAPES/
├── modules/        ESP32-S3-WROOM-1
├── ics/            MAX3232, NCP1117, USBLC6, LM2596, 74LVC8T245, SI4447
├── connectors/     USB-C, DE9, nano-SIM, u.FL, SMA, bornera, header, MOLEX, microSD
├── passives/       R, C, L, diodos, LED, pulsadores
├── power/          fusible
└── manifest.json   footprint → categoría → archivo de modelo
```

29 modelos STEP (12 MB), uno por footprint. Los taladros de montaje no llevan
modelo — es correcto.

## Cómo se usa

Los footprints referencian el modelo como
`${KIPRJMOD}/3DSHAPES/<categoría>/<archivo>` — `${KIPRJMOD}` es una variable
interna de KiCad que apunta a la carpeta del proyecto, así que funciona en
cualquier PC sin configurar nada.

### Flujo tras cambiar el esquemático
1. En Pcbnew: **Tools → Update PCB from Schematic** (trae los footprints nuevos
   con sus rutas de modelo por defecto).
2. Recolecta los modelos de los footprints nuevos:
   ```
   python3 scripts/collect_3d.py
   ```
3. Ejecuta el reenlazador:
   ```
   python3 scripts/relink_3d.py
   ```
   Reescribe las líneas `(model ...)` del `.kicad_pcb` para que apunten a esta
   carpeta y elimina bloques `(model ...)` duplicados que hayan quedado de
   ediciones anteriores. Idempotente; deja un `.bak`.
4. Recarga la placa en Pcbnew y abre el visor 3D (Alt+3).

### Comprobación
```
kicad-cli pcb export step --force -o /tmp/board.step controlcarreta.kicad_pcb
```
No debe imprimir ningún `Could not add 3D model for ...`.

### Regenerar la carpeta
`collect_3d.py` lee los footprints del esquemático y copia los modelos desde
`kicad-packages3d` (`/usr/share/kicad/3dmodels`) y desde `libraries/`. Los STEP
de `libraries/` están en `.gitignore` (pesados), así que en un clon nuevo ya no
existen: para esos componentes el script **conserva la copia que ya hay en esta
carpeta** — es la única original que sobrevive, no la borres.

Cuando un footprint trae `.step` y `.wrl`, se guarda sólo el `.step`.

## Notas / pendientes

| Footprint | Estado |
|---|---|
| `Connector_PCBEdge:BUS_PCI_Express_Mini_Full` (J14) | **Sin modelo 3D.** El footprint apunta a `Connector_PCBEdge.3dshapes/BUS_PCI_Express_Mini_Full.step`, pero esa librería **no existe en `kicad-packages3D`** (verificado contra el repo oficial de KiCad, no es que falte en este PC). Hay que sacar el STEP del fabricante del zócalo (JAE MM60-52B1-E1-R650) o modelarlo. |
| `Connector_Coaxial:SMA_Amphenol_132134-16_Vertical` (J1255) | Se usa el modelo del **-11** (casi idéntico); el `-16` no viene en `kicad-packages3d`. |
| `TerminalBlock_Altech_AK300-2` (J1/J2) | Modelo = `DG302-5.0-02P` (bornera equivalente de 5 mm, de `libraries/Tblock/`). |
| `nanoSIM_Hinged_CUI_NSIM-2-C` (J15) | El `microSIM_JAE` inicial no tenía modelo 3D en KiCad 9; cambiado a este portaSIM que sí lo trae. |
| Taladro M4 (H1–H4) | Sin modelo — es correcto, son agujeros. |
| U1 (ESP32-DEVKITC-32D), U7 (SIM800L) en el `.kicad_pcb` | Restos del layout **anterior** a la migración a ESP32-S3; sus rutas 3D absolutas siguen rotas a propósito. Desaparecen al hacer *Update PCB from Schematic*. |

Modelos propios del proyecto (no de KiCad): `MOLEX10POS.stp`, `SO8.STEP`
(SI4447), `0679L5000-05.step` (fusible), `micro SD Card Slot.step`,
`DG302-5.0-02P-12-00AH.STEP`.
