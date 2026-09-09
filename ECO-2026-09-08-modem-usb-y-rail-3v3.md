# ECO 2026-09-08 — Módem SIM7600 por USB + raíl único 3.3V + correcciones del review

Fecha: 2026-09-08.

## ESTADO

**✅ APLICADO Y VERIFICADO (editado en los `.kicad_sch`, `kicad-cli sch erc` + netlist + render):**
| # | Cambio | Ficheros |
|---|--------|----------|
| Sec 9 | Divisor EN 1.21M/100k → 86.6k/10k (UVLO 12V — antes los buck no arrancaban), CBOOT C8/C19 0.47µF→100nF | psu_5v, psu_modem |
| Sec 1 | 3.3V único: U9 (NCP1117)+C37 fuera; FB1 ferrita buck U4→+3.3V; ESP32 del buck | ldo_3v3 |
| Sec 5 | Pull-ups SD R30/R31/R32 (10k) en SS/MOSI/MISO | sdcard |
| Sec 6 | TVS entrada D7 SMAJ16A (+24V→GND) | controlcarreta (raíz) |
| Sec 7 | U6 74LVC8T245 pines 5–10 (A3–A8) → GND | drivers |

Estado ERC: 0 errores. 16 avisos = 10 previos + 6 nuevos benignos (U6 A3–A8
`pin_to_pin`, mismo tipo que U7 ya tenía).

**❌ PENDIENTE — hacer en el editor de KiCad:**
- **Sec 2/3/4 — Rework del módem (USB mux TS3USB221 + recableado J14 al pinout
  SIM7600 + load-switch).** Es el cambio grande: 3 ICs nuevos en 4 hojas con
  redes jerárquicas. Requiere colocar y rutar; hacerlo a ciegas en el fichero
  crudo arriesga una red abierta invisible. Está todo especificado abajo.
- Menores: `pspice:C`→`Device:C` (usar **Change Symbol**, la geometría de pines
  difiere), renombrar red `+24V`→`+12V`, ESD SIM (Sec 8).

Decisiones tomadas por el usuario:
1. Interfaz USB del módem mediante **multiplexor USB** (un puerto a la vez), no hub.
2. **Eliminar por completo la UART al módem** — solo USB.
3. Usar los GPIO libres del ESP32 para control del módem.
4. **Raíl único de 3.3V** (elección de implementación libre).

Base: *SIM7600 Series_PCIE_Hardware Design_V1.01* (SIMCom).
Hechos clave del datasheet:
- Todos los pines digitales del módem son **1.8V**, abs. máx. **2.1V**. Nada de
  3.3V directo ni pull-ups a 3.3V sobre el módem.
- El USB del módem da 4 puertos virtuales (AT, Diagnóstico, NMEA/GNSS, Audio) →
  **la UART es redundante**.
- USB VBUS del módem va a VBAT **internamente** — no conectar VBUS en J14.
- PERST# (pin 22) ya tiene pull-up interno de 40Ω a 1.8V — **no añadir pull-up**.
- VCC del módem: 3.0–3.6V, típ 3.3V. Pico de corriente ~2A (ráfagas TX GSM),
  ~0.5–1.5A en datos LTE, ~17mA idle.
- **El USB nativo del ESP32-S3 es Full-Speed (12 Mbps)**, no High-Speed. El módem
  enumerará a FS. Suficiente para telemetría/MQTT/SMS/OTA lento; limita el
  throughput de datos LTE Cat-4. Como es FS, **el USBLC6-2SC6 (1.5 pF) sirve de
  protección ESD en todas las ramas USB** — no hacen falta arrays <1 pF.

---

## ⚠️ Decisiones abiertas (necesito respuesta para cerrar el ECO)

**D-1. ~~Química/tensión de la batería~~ → RESUELTO: batería 12V.**
Divisor EN corregido (Sección 9). TVS de entrada = SMAJ16A. Falta confirmar si
el punto LVD (11.6V on / 10.2V off) es el deseado.

**D-2. ¿Operación solo por USB en banco (sin +24V) para programar?**
Con el raíl único, si eliminamos el path VBUS→raíl el ESP32 **solo arranca con
+24V presente** (USB-C queda como datos/programación, no alimentación). Es lo
recomendado y más simple. Si necesitas programar sin conectar 24V, dímelo y
añado un path auxiliar.

---

## GPIO del ESP32-S3 — reasignación

| Pin | GPIO | Antes | Después |
|-----|------|-------|---------|
| 4  | IO4  | NC | **MDM_PWR_EN** → pin ON del load-switch del módem (activo alto) |
| 5  | IO5  | NC | **MDM_PERST** → PERST# del módem, **open-drain, sin pull-up externo** |
| 16 | IO46 | NC (strapping, PD interno) | **USB_MUX_SEL** → SEL del TS3USB221 (bajo=USB-C por defecto en arranque, alto=módem) |
| 10 | IO17 | TX_SIM (a módem) | **libre** → test point |
| 11 | IO18 | RX_SIM (a módem) | **libre** → test point |
| 15 | IO3  | MODEM_DTR | **libre** (es pin strapping) → test point |

Firmware: `IO4` como salida push-pull; `IO5` como `GPIO_MODE_OUTPUT_OD` (en reposo
Hi-Z → el módem lo lleva a 1.8V con su pull-up interno; bajar a 0 = reset);
`IO46` como salida, poner a nivel deseado **después** del arranque.

---

## Sección 1 — Raíl único de 3.3V — ✅ APLICADO 2026-09-08 (ERC 0 err, netlist OK)

**Objetivo:** un solo buck 24→3.3V (U4) alimenta ESP32 + módem + lógica + SD +
MAX3232. Se elimina la doble conversión 24→5→3.3 y los ~5 mA de Iq del NCP1117.

**Implementación real (más simple que el plan original — sin renombrar redes):**
- **U9 (NCP1117) y C37 eliminados** de `ldo_3v3.kicad_sch`.
- **FB1** añadido (Device:L, "FB 600R@100MHz 2A", `BLM21PG600SN1D`,
  `Inductor_SMD:L_0805_2012Metric`): `+3V3_MODEM` (salida buck U4) → **FB1** →
  `+3.3V`. La ferrita es la unión física entre las dos redes y filtra el rizado.
- **PWR_FLAG (#FLG06)** en `+3.3V` (alimentado a través de FB1 → ERC contento).
- **C38 (22µF) + C39 (10µF) + C40 (100nF)** quedan en `+3.3V` como bulk/desacoplo
  del lado ESP32.
- La hoja LDO_3V3 se mantiene (retitulada "FILTRO 3V3"); su símbolo jerárquico en
  el raíz no tiene sheet-pins, no hubo que tocar nada más.
- `+3V3_MODEM` sigue existiendo como nombre de red = salida cruda del buck U4
  (módem + su realimentación). `+3.3V` = todo lo demás, tras la ferrita.
- Netlist verificado: `U1.2` (pin 3V3 del ESP32), U10.4, U2.16, U5/6/7 pin 1-2,
  FB1.2 en `+3.3V`; FB1.1 + U4.9 + J14 VCC en `+3V3_MODEM`; `+5V` ya sin U9.

**Presupuesto U4:** LTE datos ~1.5A + ESP32 WiFi ~0.5A + resto ~0.2A ≈ 2.2A pico
< 3.5A del LM76003. OK.

**U3 (LM76003, `psu_5v.kicad_sch`) se mantiene**: 24→5V, ahora solo alimenta
Vcc(B) de U5/U6/U7. Sin cambios.

**SYNC/MODE (pin 17) de U3 y U4 → GND: DEJAR COMO ESTÁ.** El datasheet del
LM76003 dice explícitamente: *"Do not float. Tie to ground: DCM/PFM operation
under light loads, improved efficiency."* En el LM76003, **GND = modo eficiente**
(al revés que otros buck). El hallazgo previo del review sobre esto era erróneo.

---

## Sección 2 — Módem J14: recableado a USB (`modem.kicad_sch`)

### 2.1. Eliminar

- Red `CTS` (J14.23 ← R26 0Ω → GND) y **R26**. J14.23 = NC en el SIM7600.
- Conexión J14.11 (era `RX_SIM`) — pin real = UART_CTS, no se usa.
- Conexión J14.13 (era `TX_SIM`) — pin real = UART_RTS, no se usa.
- Conexión J14.31 (era `MODEM_DTR`) — pin real = NC.
- **R24** (pull-up de `W_DISABLE` a 3.3V — sobre-tensión sobre pin de 1.8V).
- **R25** (pull-up de `MDM_PERST` a 3.3V — sobre-tensión + redundante).
- Etiquetas jerárquicas `TX_SIM`, `RX_SIM`, `MODEM_DTR` de esta hoja **y** el
  sheet-pin correspondiente en el esquema raíz.

### 2.2. Pinout correcto del SIM7600-PCIE (referencia)

| Pin | Señal SIM7600 | Uso en esta placa |
|-----|---------------|-------------------|
| 2,24,39,41,52 | VCC 3.3V | `MDM_VCC` (tras load-switch) |
| 8/10/12/14 | USIM_VDD / DATA / CLK / RST | SIM → J16 (sin cambios) |
| 16 | USIM_DET | opcional: contacto CD de J16 (si J16 lo tiene). Si no, dejar NC |
| 20 | W_DISABLE# (1.8V, in) | **dejar ABIERTO** (RF siempre on con módem alimentado) |
| 22 | PERST# (1.8V, in, PU interno) | `MDM_PERST` → ESP32 IO5 (open-drain) |
| 30 | SCL (I2C, 1.8V) | NC |
| 32 | SDA (I2C, 1.8V) | NC |
| 36 | USB_DN | `MDM_USB_DM` → mux USB puerto 2 |
| 38 | USB_DP | `MDM_USB_DP` → mux USB puerto 2 |
| 42 | LED_WWAN# (1.8V, OD) | D4 + R27 → `+3.3V` (OK: pin ve ≤1.5V apagado < 2.1V máx) |
| 44 | UART_RI | NC |
| 1,3,5,7,17,19,23,25,28,31,33,45,47,48,49,51 | NC / no usados | dejar abiertos (poner NC flags) |

**UART real del módem:** RXD=17, TXD=19, RTS=13, CTS=11, DTR=46, RI=44 — **no se
cablean** (interfaz solo USB). Documentar en el esquema con un texto: "UART del
módem no usada — interfaz por USB".

### 2.3. Añadir en `modem.kicad_sch`

- J14.36 → etiqueta jerárquica `MDM_USB_DM`; J14.38 → `MDM_USB_DP`.
  Añadir sheet-pins en el raíz y llevar a `usb.kicad_sch`.
- J14.22 → etiqueta jerárquica `MDM_PERST` (nueva, hacia el raíz → hoja del ESP32).
- Red `MDM_VCC` desde el load-switch (Sección 3) a J14 pines 2/24/39/41/52.
  Bulk local: C29 (47µF, reubicar aquí) + **C_new 100µF** + 100nF cerca de J14.
- NC flags en todos los pines no usados de J14 para dejar el ERC limpio.

---

## Sección 3 — Load-switch de alimentación del módem (`modem.kicad_sch` o `psu_modem.kicad_sch`)

El SIM7600-PCIE **arranca solo al aplicar VCC** (no hay PWRKEY). Cortar VCC =
apagado y power-cycle limpio de un módem colgado.

| Ref | Parte sugerida | Función |
|-----|----------------|---------|
| U_LS | **TPS22965DSGR** (SON-6, 6A, 5.5V) | load-switch high-side, `+3.3V` → `MDM_VCC` |
| C_CT | ~10–22 nF | pin CT: rampa de subida ~1 ms para limitar inrush a los ~150µF de la rama módem |
| FB_MDM | ferrita 600Ω@100MHz ≥3A | en serie tras el switch, aísla ruido de conmutación del módem |

- `ON` de U_LS ← `MDM_PWR_EN` (ESP32 IO4). Pull-down 100k a GND en `ON`
  (módem apagado por defecto en arranque).
- Alternativa discreta si prefieres coherencia con Q1: P-FET (DMP3098L o
  similar, Vds ≥ 12V, ≥3A) + gate 100k a fuente + NPN pequeño para conmutar
  gate desde el GPIO + RC de ~1ms en gate para el slew.
- Entrada del switch: desde `+3.3V` (salida de U4, **antes** de FB1 del ESP32).

---

## Sección 4 — Multiplexor USB (`usb.kicad_sch`)

El ESP32-S3 tiene **un solo** puerto USB. El mux lo comparte entre USB-C y módem
(uno a la vez).

| Ref | Parte | Notas |
|-----|-------|-------|
| U_MUX | **TS3USB221ADGSR** (MSOP-10) | mux USB 2.0, VCC = `+3.3V`, C bypass 100nF |

Conexiones:
- **Common (D+/D−)** de U_MUX ↔ ESP32 USB (pines 14/13 = USB_D+/USB_D−).
  Estas son las redes `USB_DP` / `USB_DM` que hoy van del USBLC6 al ESP32 —
  reconéctalas al common del mux.
- **Puerto 1 (D1+/D1−)** → U8 (USBLC6-2SC6) → J19 USB-C (rama actual, sin cambios
  aguas abajo de U8).
- **Puerto 2 (D2+/D2−)** → **U8b (USBLC6-2SC6 nuevo)** → `MDM_USB_DP`/`MDM_USB_DM` → J14.
- `SEL` ← `USB_MUX_SEL` (ESP32 IO46). Con IO46 = PD interno, en arranque SEL=bajo
  → **puerto 1 (USB-C) seleccionado** (siempre programable al encender).
- `OE#` → GND (mux siempre habilitado).
- PCB: `MDM_USB_DP/DM` como par diferencial ~90Ω, corto, sin stubs.

**Nota de uso:** mientras `SEL`=módem no hay acceso a la placa por USB-C. El
firmware conmuta a demanda.

### 4.1. Path VBUS→raíl (D5)

Con el raíl único, D5 (VBUS→+5V) **ya no sirve** para alimentar el 3.3V (el buck
U4 no arranca con 4.7V en `+24V` por el divisor UVLO en EN).

- **Recomendado (decisión D-2 = no):** **eliminar D5**. La placa se alimenta solo
  de +24V; USB-C = datos/programación. Requiere +24V presente para programar.
- Si D-2 = sí (programar sin 24V): mantener un LDO pequeño de Iq bajo
  (p.ej. AP7361C-33 o MCP1700-3302) VBUS→3.3V, OR-eado a `+3.3V` con un Schottky
  (BAT54). Dímelo y lo detallo.

---

## Sección 5 — Tarjeta SD: pull-ups — ✅ APLICADO 2026-09-08 (ERC ok, netlist ok)

Añadidos en `sdcard.kicad_sch` (10k 0402, YAGEO RC0402FR-0710KL / 311-10.0KLRTR-ND):
- **R30** → `SS` (CS, U10.2) → +3.3V
- **R31** → `MOSI` (CMD, U10.3) → +3.3V
- **R32** → `MISO` (DAT0, U10.7) → +3.3V

Conectados vía hierarchical labels (mismo net que en U1/U10). Netlist verificado:
cada net = {Rxx.2, U1.pin, U10.pin}. DAT1/DAT2 (U10 pin 8/1) se dejan NC —
aceptable en modo SPI; opcional añadir 10k→+3.3V si hay problemas de modo.

---

## Sección 6 — Protección de entrada +24V — ✅ APLICADO 2026-09-08 (ERC ok, netlist ok)

Batería 12V → **D7 = SMAJ16A** (símbolo `Device:D_Zener`, footprint
`Diode_SMD:D_SMA`, MPN SMAJ16A / SMAJ16ALFCT-ND) añadido en la hoja raíz:
cátodo (D7.1) → `+24V` (rama protegida, tras F1+Q1), ánodo (D7.2) → GND.
Standoff 16V, recorta ~26V ≪ 42V abs.máx del LM76003. **No hace falta el
inductor serie** (a 12V el clamp ya está muy por debajo del límite).
Confirmar Q1 (SI4447ADY): P-channel (ya confirmado) y Vds ≥ 40V.

---

## Sección 7 — 74LVC8T245 U6: entradas al aire — ✅ APLICADO 2026-09-08

`drivers.kicad_sch`: eliminados los 6 no-connect de U6 pines 5–10 (A3–A8);
atados a **GND** con un bus vertical + símbolo GND (#PWR0180). Pines 14–19
(B3–B8, salidas) siguen con NC. Netlist: U6.5–10 en GND.
**Nota:** genera 6 avisos ERC `pin_to_pin` (Bidirectional↔Power) — mismo tipo
benigno que los 2 que ya tenía U7 A7/A8. Se pueden excluir en ajustes de ERC.

---

## Sección 8 — ESD en conectores expuestos

| Conector | Acción |
|----------|--------|
| J16 (SIM, accesible al usuario) | array ESD baja capacidad en SIM_IO/CLK/RST — **SP3010-04UTG** (Littelfuse, 0.5pF) o NUP4114. SIM_VCC: ferrita + 100nF (C36 ya está). |
| J4 (RS-232) | **sin acción** — el MAX3232**E** ya integra ±15kV HBM en las líneas RS-232. |
| J5–J12 (drivers) | **condicional**: si los cables salen del gabinete, array TVS (p.ej. SP724 / uClamp) por conector. Si van a placas internas en la misma caja, no. |
| J1 (+24V) | cubierto por Sección 6. |
| J19 (USB-C) | cubierto (USBLC6). |

---

## Sección 9 — Retoques de valores (cambios de propiedad, seguros)

### ✅ APLICADO 2026-09-08 (ERC 0 violaciones) — batería confirmada = **12V**

El "+24V" del esquema es en realidad **12V** (no hay boost; J1→F1→Q1→PVIN de
los buck directo). Con el divisor EN anterior (1.21M/100k, umbral ~15.5V) **los
buck U3/U4 nunca arrancarían a 12V → placa muerta**. Corregido para batería
plomo-ácido 12V con LVD:

| Ref | Antes | Ahora | MPN nuevo |
|-----|-------|-------|-----------|
| R15, R21 (EN sup.) | 1.21M | **86.6k** | RMCF0402FT86K6 / RMCF0402FT86K6TR-ND |
| R16, R22 (EN inf.) | 100k | **10k** | RC0402FR-0710KL / 311-10.0KLRTR-ND |
| C8, C19 (CBOOT) | 0.47µF | **100nF** | CL10B104KB8NNNC / 1276-1000-1-ND |

UVLO resultante (VEN_VOUT: subida 1.204V, hist. −150mV):
**encendido ≈ 11.6V, apagado ≈ 10.2V**. Ajusta R15/R21 si quieres otro punto de
corte (o quítalo: pon R15/R21 = R16/R22 = 10k → arranca a ~2.4V, sin LVD).
**Verificar disponibilidad de los 6 MPN antes de pedir.**
Impedancia del divisor baja de ~1.3M a ~97k → sin error por corriente de fuga
del pin EN ni captación de ruido.

### Pendiente (hacer en KiCad)

| Ref | Cambio | Motivo |
|-----|--------|--------|
| C33/C34/C35/C41 | símbolo `pspice:C` → `Device:C` (**Change Symbol**) | quita avisos ERC |
| F1 | símbolo `0679L5000-05` → neutro (`Device:Fuse`) | cosmético; valor/MPN ya OK a 12V |
| red `+24V` | renombrar a `+12V` o `+VBAT` | el nombre miente |
| D_TVS entrada | **SMAJ16A** (12V: standoff 16V, recorta 26V ≪ 42V) | ya no hace falta el inductor serie de la Sección 6 |

Revisar también el **divisor de VREAD** (R4 22k / R5 1k): 24V → ~1.04V al ADC del
ESP32. Funciona con el clamp D6 (zener 3.3V) pero desaprovecha rango. Si quieres
mejor resolución: R4=22k / R5=2.2k → ~2.2V a 24V (sigue con margen hasta ~30V
antes del clamp). Opcional.

---

## Checklist de verificación tras implementar

- [ ] `kicad-cli sch erc` → 0 errores, avisos revisados uno a uno
- [ ] Anotación completa, sin refs duplicadas
- [ ] Ningún pin de 3.3V del ESP32 llega directo a un pin del módem
- [ ] `MDM_PERST` sin pull-up externo; IO5 configurable como open-drain
- [ ] Mux USB: common↔ESP32, P1↔USB-C, P2↔módem; SEL↔IO46; OE#↔GND
- [x] `+3.3V` alimenta al ESP32 (vía FB1 desde el buck U4); U9 eliminado. `+3V3_MODEM` = salida cruda del buck (módem + realim.), unida a `+3.3V` por FB1
- [ ] Load-switch del módem: ON↔IO4, pull-down en ON, CT para ~1ms
- [ ] SD: 5 pull-ups a +3.3V
- [ ] TVS + L de entrada colocados; TVS acorde a la batería (D-1)
- [ ] U6 pines 5–10 a GND
- [ ] Presupuesto de corriente del buck U4 recalculado con la carga combinada
- [ ] Re-sincronizar netlist esquema→PCB y rehacer layout de las zonas afectadas
