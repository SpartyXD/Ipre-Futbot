"""
Cliente de teclado: PC -> TCP al Pico.

El Pico crea su propia red WiFi y hace de servidor (ver pico/main.py). Antes
de correr esto, conecta el WiFi del PC a esa red (SSID por defecto:
"FutBot_1", clave "futbot123").

Protocolo: "vL,vR,sol,rod\n" (vL/vR duty -100..100, sol y rod 0/1). Se envia
a HZ fijo sin importar si hay cambios, para alimentar el watchdog del Pico.

Requisitos: pip install keyboard
En Linux hace falta correr como root; en macOS, dar permiso de Accesibilidad.
"""

import socket
import time

import keyboard

ROBOT_IP = "192.168.4.1"   # IP por defecto del Access Point de MicroPython
ROBOT_PORT = 8080
HZ = 20
DUTY = 60                  # duty al mover adelante/atras
TURN_DUTY = DUTY // 2      # duty extra por rueda al girar


def compute_command():
    vl = 0
    vr = 0

    # Chequeos independientes (no elif encadenado) para permitir combinaciones,
    # por ejemplo W+D hace una curva en vez de solo avanzar o solo girar.
    if keyboard.is_pressed("w"):
        vl += DUTY
        vr += DUTY
    if keyboard.is_pressed("s"):
        vl -= DUTY
        vr -= DUTY
    if keyboard.is_pressed("a"):
        vl -= TURN_DUTY
        vr += TURN_DUTY
    if keyboard.is_pressed("d"):
        vl += TURN_DUTY
        vr -= TURN_DUTY

    vl = max(-100, min(100, vl))
    vr = max(-100, min(100, vr))

    sol = 1 if keyboard.is_pressed("space") else 0
    rod = 1 if keyboard.is_pressed("shift") else 0

    return vl, vr, sol, rod


def connect():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ROBOT_IP, ROBOT_PORT))
            sock.settimeout(None)
            print("Conectado al robot en {}:{}".format(ROBOT_IP, ROBOT_PORT))
            return sock
        except OSError as e:
            print("No se pudo conectar ({}), reintentando...".format(e))
            time.sleep(1)


def main():
    sock = connect()
    print("W/S adelante-atras, A/D giro, SPACE patea, SHIFT rodillo. ESC para salir.")
    period = 1.0 / HZ
    try:
        while not keyboard.is_pressed("esc"):
            vl, vr, sol, rod = compute_command()
            line = "{},{},{},{}\n".format(vl, vr, sol, rod)
            try:
                sock.send(line.encode())
            except OSError:
                print("Se perdio la conexion, reintentando...")
                sock.close()
                sock = connect()
            time.sleep(period)

        sock.send(b"0,0,0,0\n")
    finally:
        sock.close()
    print("Saliendo.")


if __name__ == "__main__":
    main()
