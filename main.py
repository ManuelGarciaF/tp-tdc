#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import random

tam_buffer_receptor = 16 * 1000
nivel_deseado = tam_buffer_receptor * 0.95 # tita_i
mss = 536 # default ipv4
tiempo_total = 1 * 1000 # ms
tiempo_scan = 14 # ms, definido por el rtt

fin_estado_transitorio = (nivel_deseado * (tiempo_scan / mss))

def pasos():
    t = 0
    while True:
        t += tiempo_scan
        espacio_disponible = nivel_deseado - ocupacion_buffer
        salida_controlador = min(espacio_disponible, mss)
        perturbacion = perturbacion_por_perdida()
        datos_recibidos = max(salida_controlador + perturbacion, 0)
        perturbacion_efectiva = -perturbacion if salida_controlador > 0 else 0
        ocupacion_buffer += datos_recibidos # tita_o

        yield t, espacio_disponible, salida_controlador, perturbacion_efectiva, datos_recibidos, ocupacion_buffer


def main():
    salidas = [0]
    errores = [nivel_deseado]
    salidas_controlador = [0]
    recibidos = [0]
    perdidas = [0]
    tiempos = [0]

    ocupacion_buffer = 0
    for t, espacio_disponible, salida_controlador, perturbacion_efectiva, datos_recibidos, ocupacion_buffer in pasos():
        tiempos.append(t)
        errores.append(espacio_disponible)
        salidas_controlador.append(salida_controlador)
        recibidos.append(datos_recibidos)
        perdidas.append(-perturbacion if salida_controlador > 0 else 0)
        salidas.append(ocupacion_buffer)

    # Plot
    plt.rcParams.update({'font.size': 14})
    fig = plt.figure(figsize=(15, 10))

    gs = gridspec.GridSpec(3, 1, height_ratios=[2, 1, 1])  # 2:1:1 ratio = 50%, 25%, 25%
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])

    ax1.set_title('Simulación de control de flujo TCP')
    ax1.plot(tiempos, salidas, label='Ocupacion del Buffer')
    ax1.plot(tiempos, errores, label='Señal de Error')
    ax1.axhline(y=nivel_deseado, xmax=0.42, linestyle=':', label='Valor nominal')
    ax1.axhline(y=tam_buffer_receptor, color='r', linestyle='--', label='Límite de error (100% ocupación)')
    ax1.axvline(x=fin_estado_transitorio, color='g', linestyle=':', label='Fin de Estado Transitorio')
    ax1.set_ylabel('Bytes')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(tiempos, salidas_controlador, label='Salida del Controlador (Bytes enviados)')
    ax2.set_ylabel('Bytes')
    ax2.legend()
    ax2.grid(True)

    ax3.plot(tiempos, recibidos, label='Bytes Recibidos')
    ax3.plot(tiempos, perdidas, label='Perdida de datos en la Tx (Perturbación)')
    ax3.set_xlabel('Tiempo (milisegundos)')
    ax3.set_ylabel('Bytes')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    plt.savefig('out.png')

def perturbacion_por_perdida():
    # 80% de las veces no hay perdidas
    if random.randint(0,5) != 0:
        return 0

    # El 10% de las veces perdemos entre 1 y 64 bits
    return -random.randint(1, 64)


if __name__ == "__main__":
    main()
