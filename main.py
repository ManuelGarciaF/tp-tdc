#!/usr/bin/env python3

import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.animation as animation
import random


#
# Parametros
#

tiempo_total = 2000  # ms
tiempo_paso_simulacion = 200 # ms, tiempo para graficar cada ciclo

# Configurables mediante casillas de texto
params = {
    "tam buffer rx": 16000,          # Bytes, determina el error superior
    "nivel deseado (%)": 0.95,       # Valor nominal
    "mss": 536,                      # Tamaño máximo por ciclo
    "tiempo scan": 14,               # Tiempo de scan
    "consumo aplicacion": 128,       # Numero de bytes consumidos por ciclo
    "probabilidad perturbacion": 20, # Dada como porcentaje, un número entre 0 y 100
    "limite bytes perturbados": 64,  # El número de bytes perdidos va entre 0 y este número
}


def nivel_deseado():
    return params["nivel deseado (%)"] * params["tam buffer rx"]


def fin_estado_transitorio():
    cambio_total = params["mss"] - params["consumo aplicacion"]
    return nivel_deseado() * (params["tiempo scan"] / cambio_total)


#
# Lógica de la simulación
#
def gen_pasos():
    t = 0
    ocupacion_buffer = 0
    while True:
        t += params["tiempo scan"]
        espacio_disponible = nivel_deseado() - ocupacion_buffer
        salida_controlador = min(espacio_disponible, params["mss"])
        perturbacion = perturbacion_por_perdida()
        datos_recibidos = max(salida_controlador + perturbacion, 0)
        perdida = -perturbacion if salida_controlador > 0 else 0

        ocupacion_buffer += datos_recibidos
        ocupacion_buffer = max(ocupacion_buffer - params["consumo aplicacion"], 0)

        yield t, espacio_disponible, salida_controlador, perdida, datos_recibidos, ocupacion_buffer


def perturbacion_por_perdida():
    if random.randint(0, 99) <= params["probabilidad perturbacion"]:
        return -random.randint(1, int(params["limite bytes perturbados"]))
    return 0


#
# No mirar, codigo horrible para GUI y plots
#
def main():
    salidas = [0]
    mediciones = [0]
    errores = [0]
    salidas_controlador = [0]
    recibidos = [0]
    perdidas = [0]
    tiempos = [0]

    # Plot to fill with data
    plot = setup_plots()

    # Setup window
    root = tkinter.Tk()
    root.wm_title("Simulacion Control de flujo TCP")
    canvas = FigureCanvasTkAgg(plot["fig"], master=root)

    # Update plot function
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
        mediciones.append(ocupacion_buffer)
        errores.append(espacio_disponible)
        salidas_controlador.append(salida_controlador)
        perdidas.append(perdida)
        recibidos.append(datos_recibidos)
        salidas.append(ocupacion_buffer)

        plot["lines"]["salida"].set_data(tiempos, salidas)
        plot["lines"]["medicion"].set_data(tiempos, mediciones)
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

        canvas.draw_idle()
        return plot["lines"].values()

    gen = gen_pasos()
    ani = animation.FuncAnimation(
        plot["fig"], update, gen, interval=tiempo_paso_simulacion, cache_frame_data=False
    )
    plt.tight_layout()

    def reset():
        nonlocal ani
        nonlocal gen
        ani.event_source.stop()
        del ani

        for data_list in (
            salidas,
            mediciones,
            errores,
            salidas_controlador,
            recibidos,
            perdidas,
            tiempos,
        ):
            data_list.clear()

        for line in plot["lines"].values():
            line.set_data([], [])

        gen = gen_pasos()
        ani = animation.FuncAnimation(
            plot["fig"], update, gen, interval=tiempo_paso_simulacion, cache_frame_data=False
        )
        canvas.draw_idle()

    # GUI
    canvas.draw()

    # mpl_toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
    # mpl_toolbar.update()

    config_bar = tkinter.Frame(master=root)
    config_bar.pack(side=tkinter.TOP, fill=tkinter.X)

    button_reset = tkinter.Button(master=config_bar, text="Reiniciar", command=reset)
    button_reset.pack(side=tkinter.LEFT, padx=2, pady=2)

    entries = {}
    for i, (key, val) in enumerate(params.items()):
        label = tkinter.Label(config_bar, text=key)
        label.pack(side=tkinter.LEFT, padx=2, pady=2)

        var = tkinter.StringVar(master=config_bar, value=str(val))
        entry = tkinter.Entry(config_bar, textvariable=var, width=10)
        entry.pack(side=tkinter.LEFT, padx=2, pady=2)
        entries[key] = {"var": var, "entry": entry}

    def apply_params():
        for key, entry in entries.items():
            val = entry["var"].get()
            if val:
                params[key] = float(entry["var"].get())
                canvas.draw()

        # Actualizar reglas
        plot["hlines"]["lh_valor_nominal"].set_ydata([nivel_deseado(), nivel_deseado()])
        plot["hlines"]["lh_limite_error"].set_ydata([params["tam buffer rx"], params["tam buffer rx"]])
        plot["vlines"]["lv_fin_transitorio"].set_xdata([fin_estado_transitorio(), fin_estado_transitorio()])
        canvas.draw_idle()

    apply_btn = tkinter.Button(config_bar, text="Aplicar", command=apply_params)
    apply_btn.pack(side=tkinter.LEFT, padx=2, pady=2)

    # mpl_toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

    root.update()
    tkinter.mainloop()


def setup_plots():
    plt.rcParams.update({"font.size": 12})
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(6, 1)
    ax_salida = fig.add_subplot(gs[0])
    ax_medicion = fig.add_subplot(gs[1])
    ax_error = fig.add_subplot(gs[2])
    ax_controlador = fig.add_subplot(gs[3])
    ax_perturbacion = fig.add_subplot(gs[4])
    ax_recibidos = fig.add_subplot(gs[5])

    (l_salida,) = ax_salida.plot([], [], label="Ocupacion del Buffer")
    lh_valor_nominal = ax_salida.axhline(y=nivel_deseado(), linestyle=":", label="Valor nominal")
    lv_fin_transitorio = ax_salida.axvline(
        x=fin_estado_transitorio(),
        color="g",
        linestyle=":",
        label="Fin de Estado Transitorio",
    )
    lh_limite_error = ax_salida.axhline(
        y=params["tam buffer rx"],
        color="r",
        linestyle="--",
        label="Límite de error (100% ocupación)",
    )

    (l_medicion,) = ax_medicion.plot([], [], label="Medición de capacidad")

    (l_error,) = ax_error.plot([], [], label="Señal de error (espacio a llenar)")

    (l_controlador,) = ax_controlador.plot(
        [], [], label="Salida del Controlador (Bytes enviados)"
    )

    (l_perturbacion,) = ax_perturbacion.plot(
        [], [], label="Perdida de datos en la Tx (Perturbación)"
    )

    (l_recibidos,) = ax_recibidos.plot([], [], label="Bytes Recibidos")

    # Titles and labels
    ax_salida.set_title("Simulación de control de flujo TCP")
    for ax in (ax_salida, ax_medicion, ax_error, ax_controlador, ax_perturbacion, ax_recibidos):
        ax.set_ylabel("Bytes")
        ax.grid(True)
        ax.legend(loc="lower right")
        ax.set_xbound(lower=0)
        # ax.set_xlim(0, 2000) #Si queremos que todos los graficos esten limitados inicialmente entre 0 y 2000 bytes

    ax_recibidos.set_xlabel("Tiempo (milisegundos)")

    # Todos los objetos
    return {
        "fig": fig,
        "axes": {
            "salida": ax_salida,
            "medicion": ax_medicion,
            "error": ax_error,
            "controlador": ax_controlador,
            "perturbacion": ax_perturbacion,
            "recibidos": ax_recibidos,
        },
        "lines": {
            "salida": l_salida,
            "medicion": l_medicion,
            "error": l_error,
            "controlador": l_controlador,
            "perturbacion": l_perturbacion,
            "recibidos": l_recibidos,
        },
        "hlines": {
            "lh_valor_nominal": lh_valor_nominal,
            "lh_limite_error": lh_limite_error,
        },
        "vlines": {
            "lv_fin_transitorio": lv_fin_transitorio,
        },
    }


if __name__ == "__main__":
    main()
