# Contexto del proyecto — IRB1010 Robot de Fútbol

> Documento de traspaso. Resume el estado del repo, los hallazgos del análisis
> y las prioridades. Guardarlo como `CLAUDE.md` en la raíz del repositorio.

---

## Qué es esto

Robot de fútbol educativo para el curso IRB1010, Pontificia Universidad Católica de Chile.
Plataforma para enseñar visión por computadora y control. Desarrollado por un equipo
anterior, ahora en fase de recuperación.

**Objetivo actual:** hacer funcionar UN robot con control por teclado vía WiFi.
Visión y control autónomo vienen después. ROS2 es trabajo futuro pedido por el
profesor guía — no implementar todavía, pero no cerrar puertas.

**Persona a cargo:** fuerte en electrónica, Arduino y ESP32. Sin experiencia previa
en MicroPython ni ROS2.

---

## Hardware (confirmado)

| Elemento | Detalle |
|---|---|
| MCU | Raspberry Pi Pico 2 W (RP2350) según el informe; los READMEs dicen Pico W — **verificar el silkscreen físico**, el `.uf2` no es intercambiable |
| Drivers | 2× TB6612FNG. Driver 1 = Motor 1. Driver 2 = Motor 2 + rodillo |
| Motores | 2× DC N20, reductora 1:100, encoders magnéticos. Tracción diferencial, rueda loca atrás |
| Rodillo | Motor DC + correa GT2 (dribbler, aplica backspin) |
| Pateador | Solenoide lineal vía TIP102 + diodo flyback |
| Buck | Mini-360 |
| Batería | **LiPo 4S, 14.8 V nominal — CONFIRMADO por el usuario, tiene el pack en mano** |

### ⚠️ Riesgo eléctrico activo

4S cargada = **16.8 V**. El VM máximo absoluto del TB6612FNG es **15 V**
(rango recomendado 2.5–13.5 V). **VM debe alimentarse desde el Mini-360, nunca
directo del pack.** El informe especifica "5 V regulado para el TB6612FNG y motores".
Verificar con multímetro en el pin VM antes de energizar. Idem VSYS del Pico (1.8–5.5 V).

Pendiente: confirmar que el Mini-360 aguanta la corriente de dos N20 + rodillo en
bloqueo simultáneo (esos módulos suelen ser 1–1.5 A continuos).

### Pinout (de `software/player/extras/close_loop.py`)

```
Driver 1 (Motor 1 / izq)        Driver 2 (Motor 2 / der + rodillo)
  STBY   GP3                      STBY   GP11
  AIN1   GP2                      AIN1   GP6
  AIN2   GP1                      AIN2   GP5
  PWMA   GP0                      PWMA   GP4
  ENC_A  GP7                      ENC_A  GP9
  ENC_B  GP8                      ENC_B  GP10
                                  BIN1   GP12  (rodillo)
                                  BIN2   GP13  (rodillo)
                                  PWMB   GP14  (rodillo)
Solenoide  GP15
LEDs: verde GP20, amarillo GP19, azul GP18, onboard "LED"
```

El código es la única documentación del pinout. **Falta contrastarlo con
`hardware/PCB/Schematic_PCB.pdf`.** GP0/GP4/GP14 caen en slices PWM distintas
(0, 2, 7), así que las tres llamadas a `freq()` no se pisan.

---

## Arquitectura

```
PC (base/)                                Pico (player/)
  Keyboard_process ─┐
                    ▼
             robots_shared  ◄── Field_process (webcam, ArUco + blob)
             (mp Manager)
                    ▼
             Server_process  ──── WiFi TCP :8080 ────►  cliente socket
             (TCP)                "vR, vL, sol, rod"    + PID + PWM
```

Los tres procesos del PC son procesos OS separados que comparten estado vía
`multiprocessing.SyncManager`. **Los proxies del manager reenvían llamadas a
métodos, no acceso a atributos** — por eso `clases.py` expone todo con getters.
Si se agrega un atributo, hay que agregar su getter.

---

## Estado real del código

- **`software/base/`** (PC): completo y casi funcional. Visión, teclado, servidor TCP.
- **`software/player/main.py`** (robot): **todo comentado.** El código activo es un
  blink de LED de 6 líneas. El firmware real (WiFi, socket, PID, motores) está debajo
  como bloque de comentarios.
- **`State_process.py`**: máquina de estados autónoma, desconectada en `main.py`.
  No tocar por ahora.

---

## Bugs encontrados en el código original

1. **CRÍTICO — scope de `clientes` en `Server_process.py`.** Hay un `clientes = []`
   a nivel de módulo, pero `server_process()` declara su propio `clientes = []` local
   que lo tapa. Las conexiones se agregan a la lista local; `enviar_a_todos()` itera
   la global, que queda vacía siempre. El servidor imprime "cliente conectado" y
   "enviando" pero no envía a nadie. Parece problema de red y no lo es.

2. **`enviar_vel()` sin sleep.** Busy-loop a máxima velocidad martillando el proxy
   del manager por IPC. Agregar `time.sleep(0.02)`.

3. **`enviar_a_todos()` muta `clientes` mientras itera.** `remove()` dentro del `for`
   salta elementos silenciosamente. Iterar sobre una copia.

4. **Sin framing en el protocolo.** TCP es un stream de bytes; dos updates rápidos
   llegan pegados (`"50, 50, 0, 00, 0, 0, 0"`). El `split(",")` del Pico devuelve 7
   campos, `ValueError`, y como el `try` solo captura `KeyboardInterrupt`, la excepción
   mata la tarea con la última velocidad enganchada. Terminar mensajes en `\n` y
   bufferear por líneas.

5. **Sin failsafe en el robot.** El servidor envía solo al cambiar; si se cae el WiFi
   el Pico mantiene el último comando indefinidamente. Watchdog obligatorio antes de
   que el robot toque el suelo.

6. **`time.sleep_ms()` en `State_process.py`** — API de MicroPython en archivo CPython.
   Revienta al llegar al estado `SHOOTING`.

7. **`keyboard` requiere root en Linux**, permiso de Accesibilidad en macOS.

8. **`detectar_color()` devuelve `data[0]`**, el primer contorno, no el más grande.
   Cambiar a `max(data, key=area)`.

9. **`__pycache__` commiteados** de dos versiones de Python distintas. Borrar y
   agregar a `.gitignore`.

### Conflicto de datos sin resolver

`main.py` asume **345** pulsos/rev; `extras/close_loop.py` asume **685**. Hay que
medirlo empíricamente. El lazo cerrado no significa nada hasta resolverlo.

---

## Código nuevo entregado (barebones de prueba)

Reemplaza `base/main.py` para el bring-up. Sin OpenCV, sin multiprocessing, sin cámara
(el usuario no tiene una todavía).

```
pico/   hw.py             pines + API simple; único archivo que toca `machine`
        test.py           menú interactivo de pruebas de componentes
        main.py           cliente WiFi + lazo abierto + watchdog
        stop.py           parada de emergencia
pc/     server_simple.py  teclado → TCP, un archivo, solo `pip install keyboard`
```

Diferencias deliberadas respecto del original:

- Mensajes terminados en `\n` y bufereados; líneas incompletas o malformadas se
  descartan en vez de crashear.
- Watchdog de 500 ms en el Pico; el servidor transmite a 20 Hz incondicionalmente
  para alimentarlo.
- Solenoide por flanco de subida, tope de 80 ms y cooldown de 500 ms dentro de
  `hw.kick()`.
- Chequeos de teclas independientes (no cadena `elif`), así W+D hace curva.
- `broadcast()` itera sobre una copia de la lista de clientes.

`hw.LEFT_SIGN` / `hw.RIGHT_SIGN` centralizan la polaridad: si una rueda gira al revés
se corrige ahí, no recableando.

---

## Límites del Pico que condicionan el diseño

**RP2350 (Pico 2 W):** dual Cortex-M33 @150 MHz con FPU, 520 KB SRAM, 12 slices PWM,
3 bloques PIO.
**RP2040 (Pico W):** dual Cortex-M0+ @133 MHz, **sin FPU**, 264 KB SRAM, 8 slices PWM,
2 bloques PIO.

- MicroPython corre ~50–100× más lento que C equivalente. Un loop de polling llega a
  ~10–20k iteraciones/s.
- A 685 pulsos/rev y 200 RPM cada encoder genera ~2280 flancos/s. Dos encoders = 4560.
  **El polling en Python del código original pierde cuentas.** La solución correcta es
  PIO (decodificación de cuadratura en hardware). Para control por teclado no importa:
  usar lazo abierto.
- El GC produce pausas de milisegundos impredecibles. No asignar memoria dentro de
  loops de control (nada de f-strings, `.split()`, listas nuevas).
- No hay visión posible en el Pico. El split PC-visión / Pico-actuación es obligatorio,
  y es justo la frontera donde entrarán los nodos ROS2.

---

## Prioridades

1. Verificar el pinout contra el esquemático del PCB.
2. Confirmar con multímetro que VM del TB6612FNG viene del regulador, no del pack 4S.
3. Correr `test.py` componente por componente, ruedas en el aire.
4. Ajustar `LEFT_SIGN` / `RIGHT_SIGN` según resultados.
5. Medir pulsos/rev reales y documentarlo.
6. WiFi → red → manejo por teclado, todavía en el soporte.
7. Aplicar los fixes 1, 2, 3 a `Server_process.py` si se retoma el pipeline original.

---

## Camino a ROS2 (futuro, no ahora)

Mapeo natural: `Field_process` → nodo de visión publicando estado de cancha;
`Keyboard_process` / `State_process` → nodo controlador publicando `Twist` en
`/robot_0/cmd_vel`; `Server_process` → nodo puente que traduce a protocolo serial/TCP.

El Pico puede quedarse con el protocolo actual detrás del puente (más simple, firmware
sin cambios) o correr micro-ROS — pero micro-ROS exige el SDK de C, no MicroPython, lo
que choca con el objetivo pedagógico. El puente es casi seguro la decisión correcta.

**Implicancia para hoy:** mantener el protocolo de cable limpio y documentado. Esa
interfaz es la costura por donde se va a insertar ROS2.
