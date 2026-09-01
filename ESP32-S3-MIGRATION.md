# Migración ESP32-DevKitC-32D → ESP32-S3-WROOM-1

Fecha: 2026-09-01

**Abre `controlcarreta.kicad_sch`** (archivo nuevo). El esquemático modificado se
guardó con la extensión correcta de KiCad 9 — `controlcarreta.sch` daba el error
*"is not a KiCad schematic file"* porque KiCad 9 no abre contenido v9 con extensión
`.sch`. Al abrir el proyecto `controlcarreta.kicad_pro` ya toma el `.kicad_sch`
automáticamente.

- `controlcarreta.kicad_sch` → esquemático con el ESP32-S3 (USAR ESTE)
- `controlcarreta.sch` → original sin tocar (legacy, se puede borrar)
- `controlcarreta.sch.esp32-devkitc.bak` → copia de seguridad idéntica

## Qué cambió

- **U1** ya no es la placa `ESP32-DEVKITC-32D` enchufada en headers. Ahora es el
  **módulo SMD `ESP32-S3-WROOM-1-N8`** (8 MB flash, sin PSRAM) soldado directo a la PCB.
  Símbolo: `RF_Module:ESP32-S3-WROOM-1` · Footprint: `RF_Module:ESP32-S3-WROOM-1`.
- Se añadió toda la circuitería de soporte que antes daba la DevKitC:
  regulador 3V3, desacoplo, reset/boot y USB.
- **Todas las 28 señales originales conservan su nombre de red.** Sólo cambió el
  GPIO físico al que van (ver tabla). El firmware hay que reasignarlo.

## Componentes nuevos

| Ref | Valor | Función | Footprint |
|-----|-------|---------|-----------|
| U8  | NCP1117-3.3 | LDO 3V3 desde +5V (≈800 mA) | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` |
| U9  | USBLC6-2SC6 | Protección ESD en D+/D-/VBUS | `Package_TO_SOT_SMD:SOT-23-6` |
| J13 | USB-C 2.0 (16P) | Programación / consola (USB-Serial-JTAG nativo del S3) | `Connector_USB:USB_C_Receptacle_GCT_USB4085` |
| D7  | SS14 | Schottky VBUS→+5V (permite alimentar por USB, bloquea retorno) | `Diode_SMD:D_SMA` |
| SW1 | — | Pulsador RESET (EN → GND) | `Button_Switch_THT:SW_PUSH_6mm` |
| SW2 | — | Pulsador BOOT (IO0 → GND) | `Button_Switch_THT:SW_PUSH_6mm` |
| R13 | 10k | Pull-up EN | 1206 |
| R14 | 10k | Pull-up IO0 | 1206 |
| R15 / R16 | 5.1k | Resistencias CC1 / CC2 del USB-C (perfil device) | 1206 |
| C10 | 10µF | Entrada LDO | 0805 |
| C11 | 22µF | Salida LDO / bulk | 0805 |
| C12 | 10µF | Bulk módulo | 0805 |
| C13 | 100nF | Desacoplo HF módulo | 0805 |
| C14 | 1µF | Retardo RC en EN | 0805 |
| C15 | 100nF | Antirrebote IO0 | 0805 |

Símbolos locales nuevos en `controlcarreta.kicad_sym` (añadida a `sym-lib-table`):
`NCP1117-3.3_SOT223`, `USBLC6-2SC6`.

## Arquitectura de alimentación (cambio importante)

Antes: +24V → U2 (buck LM2596) → **+5V** → la DevKitC generaba **+3V3** para toda la placa.

Ahora: +24V → U2 → **+5V** → **U8 (LDO)** → **+3V3**.
El +3V3 alimenta: módulo U1, SD card U3, lado A de U4/U5/U6, R100, J2.
El USB-C puede alimentar +5V a través de D7 durante trabajo de banco.

> Verifica térmicamente U8: (5 − 3.3) × I. Con WiFi transmitiendo (~pico 500 mA)
> son ~0.85 W; en SOT-223 con plano de cobre está en el límite. Si te preocupa,
> cambia U8 por un buck 3V3 o reparte el cobre bajo el tab.

## Tabla de reasignación de GPIO

`pin#` = número de pad del módulo ESP32-S3-WROOM-1.

| Red | ESP32 antiguo (DevKitC) | ESP32-S3 nuevo | pin# módulo | Notas |
|-----|------------------------|----------------|-------------|-------|
| FOTO   | GPIO36 (SENSOR_VP, solo-in) | **GPIO1**  | 39 | ADC1_CH0 |
| VREAD  | GPIO4  | **GPIO2**  | 38 | ADC1_CH1 |
| TX_GPS | GPIO16 | **GPIO4**  | 4  | |
| RX_GPS | GPIO17 | **GPIO5**  | 5  | |
| LE1    | GPIO0  | **GPIO6**  | 6  | (antes en pin de boot) |
| LE2    | GPIO15 | **GPIO7**  | 7  | |
| LE3    | GPIO7  | **GPIO8**  | 12 | |
| LE4    | GPIO11 | **GPIO9**  | 17 | |
| SS     | GPIO5  | **GPIO10** | 18 | FSPICS0 |
| MOSI   | GPIO23 | **GPIO11** | 19 | FSPID |
| SCK    | GPIO18 | **GPIO12** | 20 | FSPICLK |
| MISO   | GPIO19 | **GPIO13** | 21 | FSPIQ |
| LE5    | GPIO27 | **GPIO14** | 22 | |
| LE6    | GPIO25 | **GPIO15** | 8  | |
| LE7    | GPIO32 | **GPIO16** | 9  | |
| TX_SIM | GPIO9  | **GPIO17** | 10 | U1TXD |
| RX_SIM | GPIO10 | **GPIO18** | 11 | U1RXD |
| ~~LE8~~ (panel 8) | GPIO34 (solo-in) | **eliminado** | — | panel J11 desactivado |
| D1     | GPIO2  | **GPIO35** | 28 | |
| D2     | GPIO8  | **GPIO36** | 29 | |
| D3     | GPIO6  | **GPIO37** | 30 | |
| D4 (dato) | GPIO13 | **GPIO38** | 31 | |
| D5 (dato) | GPIO26 | **GPIO39** | 32 | |
| D6     | GPIO33 | **GPIO40** | 33 | |
| D7     | GPIO35 (solo-in) | **GPIO41** | 34 | |
| ~~D8~~ (panel 8) | GPIO39 (solo-in) | **eliminado** | — | panel J11 desactivado |
| CL     | GPIO14 | **GPIO47** | 24 | |
| BRILLO | GPIO12 | **GPIO48** | 25 | PWM ok |
| STATUS1 (LED D4 vía R8) | GPIO22 | **GPIO42** | 35 | (pin que ocupaba D8) |
| STATUS2 (LED D5 vía R9) | GPIO21 | **GPIO21** | 23 | (pin que ocupaba LE8) |

### Reservados / libres

| pin# | GPIO | Uso |
|------|------|-----|
| 3  | EN     | reset (R13 + C14 + SW1) |
| 27 | GPIO0  | boot (R14 + C15 + SW2) |
| 13 | GPIO19 (USB_D-) | USB-C J13 |
| 14 | GPIO20 (USB_D+) | USB-C J13 |
| 36 | GPIO44 / U0RXD | `RX_EXT` — RS-232 a equipo externo (MAX3232 U11). Usar como UART1/2 en firmware. |
| 37 | GPIO43 / U0TXD | `TX_EXT` — RS-232 a equipo externo (MAX3232 U11). Usar como UART1/2 en firmware. |
| 15 | GPIO3  | libre (strapping – dejar sin usar) |
| 16 | GPIO46 | libre (strapping – dejar sin usar) |
| 26 | GPIO45 | libre (strapping – dejar sin usar) |
| 2 / 1,40,41 | 3V3 / GND | alimentación |

## Puntos que TIENES que revisar

1. **Se eliminó el panel de LED nº 8** (nets `D8` y `LE8`) para liberar 2 GPIO.
   Ahora las 28 señales caben en los GPIO "limpios" y **GPIO43/44 (UART0) quedan
   libres**. STATUS1→GPIO42, STATUS2→GPIO21 (los pines que ocupaban D8/LE8).
   - El conector **J11 queda sin uso** (sus entradas en U6 A7/A8 se ataron a GND;
     ERC marca 2 avisos `pin_to_pin` benignos por eso). Puedes despoblar J11, o si
     querías quitar 2 paneles enteros (J10 **y** J11) dímelo y quito también D7/LE7.
   - Paneles 1–7 (J4–J10) funcionan igual.

2. **Los pines "solo-entrada" del ESP32 clásico ya no existen en el S3.** En el
   diseño viejo LE8, D7 y D8 estaban en pines solo-entrada (GPIO34/35/39) — es
   decir el ESP los *leía*. Si en tu lógica esos deberían ser salidas, el diseño
   viejo estaba mal y ahora puedes corregirlo en firmware; si eran de verdad
   entradas, todo igual.

3. **ADC:** FOTO y VREAD quedaron en GPIO1/GPIO2 (ADC1). Bien: ADC2 no se puede
   usar con WiFi activo. Mantenlos en ADC1 (GPIO1–GPIO10).

4. **PCB:** el footprint de U1 cambió por completo (de header modular a SMD
   castellado) y hay 16 componentes nuevos. Hay que re-hacer buena parte del
   layout. Importa el netlist nuevo a Pcbnew ("Update PCB from Schematic").

5. **Edición conservando formato:** el `.sch` se editó por cirugía de texto
   (no round-trip completo), así que el 99 % del archivo es idéntico byte a byte
   al que escribió KiCad. ERC = 0 errores; los warnings `endpoint_off_grid` son
   los mismos que ya traía el original. Si KiCad pide actualizar la librería
   `controlcarreta` (símbolos U8/U9), es porque hay que registrarla — ya está
   añadida en `sym-lib-table`.

6. **`+3V8`** (rail del SIM800L) no se tocó — sigue saliendo de +5V vía D3.

## Links de DigiKey en el campo Datasheet (2026-09-01)

Se rellenó el campo *Datasheet* de los 67 componentes con su página de producto
en DigiKey (H1–H4 = agujeros de montaje, sin parte). Para los pasivos genéricos
que no tenían MPN se eligió una parte estándar equivalente — **revísalas antes de
comprar**, sobre todo tensión/dieléctrico:

| Componentes | Parte elegida | Nota |
|---|---|---|
| R3,R4,R6,R13,R14,R100 (10k) | Stackpole RMCF1206FT10K0 | 1206 1% (familia de R1/R2) |
| R5,R7 (1.5k) | RMCF1206FT1K50 | |
| R8,R9 (330) | RMCF1206FT330R | |
| R10 (100k) | RMCF1206FT100K | |
| R11 (22k) | RMCF1206FT22K0 | |
| R12 (1k) | RMCF1206FT1K00 | |
| R15,R16 (5.1k) | RMCF1206FT5K10 | CC del USB-C |
| C4–C9 (4.7µF) | Samsung CL21A475KAQNNNE | 0805 25V X5R |
| C10,C12 (10µF) | Samsung CL21A106KOQNNNE | 0805 **16V** X5R — para C10 (entrada LDO desde +5V) mejor subir a 25V |
| C11 (22µF) | Samsung CL21A226MOCLRNC | 0805 16V X5R |
| C13,C15 (100nF) | Samsung CL21B104KBCNNNC | 0805 50V X7R |
| C14 (1µF) | Samsung CL21B105KBFNNNE | 0805 50V X7R |
| D2,D3 (1N4007) | Vishay 1N4007-E3/54 | |
| D4,D5 (LED) | Vishay TLHR5400 | rojo 5mm THT |
| D7 (SS14) | onsemi SS14 | Schottky 40V 1A SMA |
| L1 | Bourns SDR1806-330ML | 33µH (coincide con el footprint) |
| Q1 | Vishay SI4447ADY-T1-GE3 | |
| U2 | TI LM2596S-ADJ/NOPB | |
| U3 (sdcard) | Hirose DM3AT-SF-PEJM5 | socket microSD push-pull |
| U7 (sim800l) | link a simcom.com (DigiKey no lo lista) | |
| U8 | onsemi NCP1117ST33T3G | |
| U9 | USBLC6-2SC6 (Slkormicro en DigiKey; ST está sin stock) | |
| J1,J2 | On Shore OSTTC020162 | bornera 5mm 2 pos (footprint Altech AK300) |
| J3 | Würth 61300411121 | tira de pines 1x4 2.54mm |
| J13 | GCT USB4085-GF-A | USB-C (coincide con el footprint) |
| SW1,SW2 | Omron B3F-1000 | táctil 6mm THT |
| U1 | Espressif ESP32-S3-WROOM-1-N8 | |

## Módem celular: SIM800L → zócalo Mini PCIe (2026-09-01)

**Hoja pasada a A3** (había que ubicar 24 componentes nuevos). Abre
`controlcarreta.kicad_sch`.

### Qué se quitó
`U7` (SIM800L) + `R6`/`R7` (divisor de nivel UART que ya no hace falta — el
módem mini-PCIe es 3.3V, igual que el ESP32-S3) + `J12214` (u.FL de la
SIM800L). El rail `+3V8` se deja intacto (sigue alimentando el conector GPS `J3`).

### Qué se añadió
| Ref | Qué es | Función |
|---|---|---|
| **J14** | Zócalo Mini PCIe 52 pines (símbolo propio `controlcarreta:MINI_PCIE_52`) | Aquí se enchufa el módem — **Quectel EG25-G** o **SIMCom SIM7600G-H** versión Mini PCIe. Extraíble. |
| U10 | LM2596S-ADJ | Buck **dedicado** +24V → **+3V3_MODEM** (rail separado del +3.3V de lógica) |
| L2 | 33µH (Bourns SDR1806) | Bobina del buck |
| D8 | SS34 | Diodo de rueda libre del buck |
| R24/R25 | 1k / 1.69k | Divisor de realimentación del buck → 3.3V |
| C24 | 1.5nF | Feed-forward del buck |
| C25 | 100µF | Bulk de entrada (+24V) |
| C26 | **470µF baja ESR** | Bulk junto al zócalo — el módem pide picos de hasta **2.7A** en TX |
| C27 | 100nF | Desacoplo HF junto al zócalo |
| R20/R21 | 10k / 10k | Pull-ups de `W_DISABLE#` y `PERST#` (quedan **sin conectar al ESP** — ver nota) |
| D9/R26 | LED + 1k | Indicador de red (`LED_WWAN#`, activo en bajo) |
| **J15** | Portador nano-SIM (`Connector:SIM_Card`) | SIM física, cableada a las señales UIM del zócalo |
| C22 | 100nF | Desacoplo de `SIM_VCC` |
| **J16** | u.FL (Hirose U.FL-R-SMT-1) | Sustituye a J12214; aquí va el pigtail MAIN del módem. **J1255 (SMA) se mantiene** como antena de panel |
| H5 | Taladro M2 | Retención mecánica de la tarjeta Mini PCIe |

### Interfaz elegida: UART (no USB)
`TX_SIM`/`RX_SIM` (los mismos nombres de red de antes) van ahora directo —
**sin divisor de nivel** — a `UART_TX`/`UART_RX` del zócalo (pines 13/11).
El USB del zócalo (pines 36/38) queda **sin conectar**: el USB-C del ESP32-S3
(J13) sigue siendo sólo para programar/depurar el ESP, no el módem.

### Puntos que revisar
1. **`W_DISABLE#` y `PERST#` NO están conectados al ESP** — sólo llevan
   pull-up (RF activo, módem fuera de reset por defecto). Los dejé así a
   propósito: esos dos pines de GPIO libres (43/44) son la UART0, que
   parpadea en cada arranque del ESP — conectarlos ahí resetearía/apagaría el
   módem en cada boot. Si quieres control por firmware, usa dos GPIO
   dedicados (tendrías que liberar 2 más) o acepta el riesgo del glitch de
   arranque.
2. **Detección de SIM deshabilitada**: `USIM_PRESENCE` (pin 44) se ató a GND.
   En firmware manda `AT+QSIMDET=0,0` (o el equivalente del módem que uses) o
   cambia esa red si tu portaSIM sí tiene switch de detección.
3. **Presupuesto térmico de U10**: (24−3.3)×I en LM2596 (TO-263). Con el
   módem en pico de 2A son ~41W — **demasiado para el TO-263 sin más ayuda**.
   En régimen normal (~0.3–0.5A promedio) son 8–10W, ya exige buen cobre/disipador.
   Si vas a operar cerca del pico sostenido, considera bajar la entrada del
   buck (usar el rail de +5V en vez de +24V) o un regulador con mejor
   eficiencia a esa relación de conversión.
4. **Footprint del zócalo** (`Connector_PCBEdge:mini_PCIe_Molex_679100000`) y
   del u.FL/nanoSIM son de referencia — confírmalos contra el conector físico
   que vayas a comprar antes de fabricar.
5. El **GPS externo (J3) sigue igual** — no se tocó. El EG25-G/SIM7600 traen
   GNSS propio si más adelante quieres consolidarlo.

## Puerto serie RS-232 para EQUIPO EXTERNO (MAX3232 + DE9) — 2026-09-01

**Este puerto NO es para programar** — es un enlace de datos dedicado a un
equipo externo. La programación y la consola del ESP32-S3 van por el **USB-C
(J13)** (USB-Serial-JTAG nativo del S3 — no necesita UART).

| Ref | Qué es | Footprint |
|---|---|---|
| **U11** | MAX3232 (transceptor RS-232 3.3V, símbolo propio `controlcarreta:MAX3232`) | `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm` |
| **J17** | Conector **DE9 macho** (DB9), cableado como **DTE** | `Connector_Dsub:DSUB-9_Pins_Horizontal_P2.77x2.84mm_EdgePinOffset9.40mm` |
| C28,C29 | 100nF | Bomba de carga del MAX3232 (C1, C2) |
| C30,C31 | 100nF | Depósito V+ / V− |
| C32 | 100nF | Desacoplo VCC |

### Conexionado (nets `TX_EXT` / `RX_EXT`)
- ESP32-S3 pin 37 (GPIO43) → `TX_EXT` → MAX3232 T1IN
- ESP32-S3 pin 36 (GPIO44) → `RX_EXT` ← MAX3232 R1OUT
- MAX3232 T1OUT → **DE9 pin 3 (TXD)** ; MAX3232 R1IN ← **DE9 pin 2 (RXD)** ; DE9 pin 5 → GND
- MAX3232 alimentado de **+3.3V** (rail de lógica, U8). Consumo despreciable.
- Canal 2 del MAX3232 sin usar (T2IN a GND; resto NC). Sin RTS/CTS.

### ⚠️ GPIO43/44 son físicamente los pines de la UART0 del ROM
No quedaban otros GPIO libres (los demás son strapping o USB). Implicaciones:

1. **En firmware, asigna este puerto a `UART1` o `UART2`** (matriz GPIO), **no
   a `UART0`**. Enruta el log/consola de ESP-IDF al **USB-Serial-JTAG**
   (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG`). Así GPIO43/44 quedan 100 % para el
   equipo externo.
2. **Al encender**, el bootloader ROM escribe ~6 líneas de log a 115200 bps por
   GPIO43 (~50 ms) → le llegan al equipo externo como bytes basura. Si el
   protocolo del equipo externo no tolera eso, **quema el eFuse
   `UART_PRINT_CONTROL = 3`** (deshabilita el log ROM) — o usa GPIO46 (pin de
   strapping libre) con `UART_PRINT_CONTROL = 1/2` para controlarlo con un
   pull-up/down.
3. La programación por USB-C **no toca** GPIO43/44 en el S3, así que no hay
   conflicto con el equipo externo durante el flasheo.
4. GPIO0 (botón BOOT) en alto al arrancar ⇒ el equipo externo **no puede**
   meter al ESP en modo descarga por accidente.

### Cable
J17 está como **DTE** (igual que un COM de PC). Para conectar a otro DTE
(PC) usa cable **null-modem**; a un DCE (módem), cable recto. Si el equipo
externo espera lo contrario, cambia J17 a `DE9_Socket` (hembra) y cruza
TX/RX en el esquemático.

### Recomendado para un enlace de campo (opcional, no incluido)
- Array TVS en las líneas RS-232 del DE9 (IEC 61000-4-2 nivel contacto).
- Resistencias serie ~100 Ω entre MAX3232 y DE9 (limitación de falta).

## Modelos 3D locales al proyecto — 2026-09-01

Se creó `3d_models/` con **todos los modelos 3D de la placa** (28 archivos STEP,
12 MB) organizados por categoría: `modules/ ics/ connectors/ passives/ power/`.
Ver `3d_models/README.md`.

- Modelos de KiCad (`kicad-packages3d`) + modelos propios de `libraries/` +
  `~/Documents/Documents/libraries/`, todos copiados a la carpeta del proyecto
  → proyecto portátil, sin rutas absolutas.
- `scripts/collect_3d.py` — regenera la carpeta.
- `scripts/relink_3d.py` — **tras "Update PCB from Schematic"**, reescribe todas
  las rutas `(model ...)` del `.kicad_pcb` a `${KIPRJMOD}/3d_models/...`
  (probado: 48 rutas). Idempotente, deja `.bak`.
- **Falta el modelo del zócalo Mini PCIe (J14)** — hay que crear ese footprint y
  su 3D a mano (KiCad no lo trae). Detalles en `3d_models/README.md`.
- J15 pasó a footprint `Connector_Card:nanoSIM_Hinged_CUI_NSIM-2-C` (el
  `microSIM_JAE` no tiene modelo 3D en KiCad 9).

## Links DigiKey — componentes de módem + RS-232 (2026-09-01)

Se completó el campo *Datasheet* de los 18 componentes que faltaban. Ahora
**los 87 componentes reales tienen link de DigiKey** (H1–H5 = taladros, sin parte).

| Ref | Parte elegida | Nota |
|---|---|---|
| J14 | Quectel **EG25GGB-MINIPCIE** | versión Mini PCIe del EG25-G |
| J17 | Amphenol **L717SDE09PA4CH4F** | DE9 macho acodado, solder cup |
| U11 | TI **MAX3232IDR** | SOIC-16 |
| R20,R21 (10k) / R24,R26 (1k) | Stackpole RMCF1206FT10K0 / FT1K00 | 1206 |
| R25 (1.69k) | Stackpole RMCF1206FT1K69 | 1206 1% |
| C22,C27–C32 (100nF) | Samsung CL21B104KBCNNNC | 0805 X7R 50V |
| C24 (1.5nF) | KEMET C0805C152K5REC7210 | 0805 X7R 50V |
| C25 (100µF, entrada buck +24V) | KEMET EDH107M035A9MAA | **electrolítico 35V** — footprint corregido a `CP_Elec_8x10.5` |
| C26 (470µF, bulk módem, baja ESR) | Panasonic EEH-ZK1E471P | **polímero 25V** — footprint corregido a `CP_Elec_10x10.5` |

> C25/C26 usan símbolo `Device:C` (sin barra de polaridad). Cámbialos a
> `Device:CP` en KiCad para que se vea la polaridad (el footprint ya es
> polarizado y pin1 = +).

## J14: zócalo Mini PCIe real (2026-09-01)

El footprint/símbolo del zócalo Mini PCIe que había puesto era inventado
(`Connector_PCBEdge:mini_PCIe_Molex_679100000` + símbolo propio `MINI_PCIE_52`).
Sustituido por los **estándar de KiCad**:

- Símbolo: `Connector:Bus_PCI_Express_Mini` (pinout Mini PCIe estándar, 52 pines + MP).
- Footprint: `Connector_PCBEdge:BUS_PCI_Express_Mini_Full` (zócalo Mini PCIe 52 pines,
  tamaño completo, con el taladro del standoff).
- `H5` → footprint `Connector_PCBEdge:JAE_MM60-EZH039-Bx_BUS_PCI_Express_Holder`
  (la retención/latch JAE MM60).
- Símbolos propios `MINI_PCIE_52` eliminados de `controlcarreta.kicad_sym`.

El cableado se mantiene por **número de pin** (que es lo que conecta): el
símbolo estándar usa los nombres del estándar PCIe (REFCLK±, PERn0/p0, etc.),
pero el módem celular (EG25-G / SIM7600) reutiliza esos pines para UART, SIM y
control — las redes van bien:

| pin | nombre en el símbolo | uso real (módem) | red |
|---|---|---|---|
| 11 | REFCLK− | UART_RX (entra al módem) | `RX_SIM` |
| 13 | REFCLK+ | UART_TX (sale del módem) | `TX_SIM` |
| 23 | PERn0 | UART_CTS | `CTS` → **R27 (0 Ω) → GND** |
| 31 | PETn0 | DTR | GND |
| 20 | W_DISABLE# | airplane mode | `W_DISABLE` (pull-up R20) |
| 22 | PERST# | reset | `MDM_PERST` (pull-up R21) |
| 8/10/12/14 | UIM_PWR/DATA/CLK/RST | SIM | `SIM_VCC/IO/CLK/RST` → J15 |
| 42 | LED_WWAN# | LED de red | `WWAN_LED` → D9 |
| 2/24/39/41/52 | +3V3AUX | alimentación | `+3V3_MODEM` |

> **R27 (0 Ω)** nuevo: el pin 23 en el símbolo estándar es tipo *output*, así
> que atarlo directo a GND daba error de ERC. Va a GND por una resistencia de
> 0 Ω (EG25-G: "conectar CTS a GND si no se usa control de flujo").

ERC: **0 errores**.
