#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.animation as animation
import random

tam_buffer_receptor = 16 * 1000
nivel_deseado = tam_buffer_receptor * 0.95  # tita_i
mss = 536  # default ipv4
tiempo_total = 1 * 1000  # ms
tiempo_scan = 14  # ms, definido por el rtt

fin_estado_transitorio = nivel_deseado * (tiempo_scan / mss)


def gen_pasos():
    t = 0
    ocupacion_buffer = 0
    while True:
        t += tiempo_scan
        espacio_disponible = nivel_deseado - ocupacion_buffer
        salida_controlador = min(espacio_disponible, mss)
        perturbacion = perturbacion_por_perdida()
        datos_recibidos = max(salida_controlador + perturbacion, 0)
        perdida = -perturbacion if salida_controlador > 0 else 0
        ocupacion_buffer += datos_recibidos  # salida

        yield t, espacio_disponible, salida_controlador, perdida, datos_recibidos, ocupacion_buffer


def perturbacion_por_perdida():
    # 80% de las veces no hay perdidas
    if random.randint(0, 5) != 0:
        return 0

    # El 10% de las veces perdemos entre 1 y 64 bits
    return -random.randint(1, 64)


salidas = []
errores = []
salidas_controlador = []
recibidos = []
perdidas = []
tiempos = []


def main():

    # Plot
    plot = setup_plots()

    def update(data):
        (
            t,
            espacio_disponible,
            salida_controlador,
            perdida,
            datos_recibidos,
            ocupacion_buffer,
        ) = data
        tiempos.append(t)

        errores.append(espacio_disponible)
        salidas_controlador.append(salida_controlador)
        perdidas.append(perdida)
        recibidos.append(datos_recibidos)
        salidas.append(ocupacion_buffer)

        plot["lines"]["salida"].set_data(tiempos, salidas)
        plot["lines"]["error"].set_data(tiempos, errores)
        plot["lines"]["controlador"].set_data(tiempos, salidas_controlador)
        plot["lines"]["perturbacion"].set_data(tiempos, perdidas)
        plot["lines"]["recibidos"].set_data(tiempos, recibidos)

        # Scroll window
        if t > tiempo_total:
            for ax in plot["axes"].values():
                ax.relim()
                ax.set_xlim(t - tiempo_total, t)
                ax.autoscale_view(scalex=False)
        else:
            for ax in plot["axes"].values():
                ax.relim()
                ax.set_xlim(0, tiempo_total)
                ax.autoscale_view(scalex=False)

        return plot["lines"].values()

    ani = animation.FuncAnimation(
        plot["fig"], update, gen_pasos, interval=200, save_count=200
    )
    plt.tight_layout()
    plt.show()


def setup_plots():
    plt.rcParams.update({"font.size": 14})
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(5, 1)
    ax_salida = fig.add_subplot(gs[0])
    ax_error = fig.add_subplot(gs[1])
    ax_controlador = fig.add_subplot(gs[2])
    ax_perturbacion = fig.add_subplot(gs[3])
    ax_recibidos = fig.add_subplot(gs[4])

    (l_salida,) = ax_salida.plot([], [], label="Ocupacion del Buffer")
    ax_salida.axhline(y=nivel_deseado, linestyle=":", label="Valor nominal")
    ax_salida.axvline(
        x=fin_estado_transitorio,
        color="g",
        linestyle=":",
        label="Fin de Estado Transitorio",
    )

    (l_error,) = ax_error.plot([], [], label="Señal de error")
    ax_error.axhline(
        y=tam_buffer_receptor,
        color="r",
        linestyle="--",
        label="Límite de error (100% ocupación)",
    )

    (l_controlador,) = ax_controlador.plot(
        [], [], label="Salida del Controlador (Bytes enviados)"
    )

    (l_perturbacion,) = ax_perturbacion.plot(
        [], [], label="Perdida de datos en la Tx (Perturbación)"
    )

    (l_recibidos,) = ax_recibidos.plot([], [], label="Bytes Recibidos")

    # Titles and labels
    ax_salida.set_title("Simulación de control de flujo TCP")
    for ax in (ax_salida, ax_error, ax_controlador, ax_perturbacion, ax_recibidos):
        ax.set_ylabel("Bytes")
        ax.grid(True)
        ax.legend(loc="best")
        ax.set_xbound(lower=0)
        ax.set_xlim(0, 2000)

    ax_recibidos.set_xlabel("Tiempo (milisegundos)")

    return {
        "fig": fig,
        "axes": {
            "salida": ax_salida,
            "error": ax_error,
            "controlador": ax_controlador,
            "perturbacion": ax_perturbacion,
            "recibidos": ax_recibidos,
        },
        "lines": {
            "salida": l_salida,
            "error": l_error,
            "controlador": l_controlador,
            "perturbacion": l_perturbacion,
            "recibidos": l_recibidos,
        },
    }


if __name__ == "__main__":
    main()
