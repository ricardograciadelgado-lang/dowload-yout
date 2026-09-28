"""
Acciones dentro de Google Vids (segun la guia del dueno).

Todo se busca por NOMBRE del boton/caja (ver SELECTORES en config.py),
nunca por posicion en la pantalla. Por eso el zoom o mover la ventana
no afecta.
"""

import time

import config
import ia_vision
import paginas
from paginas import ElementoNoEncontrado, contar_textos


class TamanoIncorrecto(Exception):
    pass


def buscar(page, clave, visible=True, espera=10):
    return paginas.buscar(page, config.SELECTORES, clave, visible, espera)


def existe(page, clave):
    return paginas.existe(page, config.SELECTORES, clave)


def contar(page, clave):
    return paginas.contar(page, config.SELECTORES, clave)


def contar_rechazos(page):
    return contar_textos(page, config.TEXTOS_RECHAZO)


# --- Preparacion -------------------------------------------------------------

def abrir_panel(page):
    """Deja abierto el panel 'Generacion de video con IA' en la pestana Crear."""
    if existe(page, "caja_prompt"):
        return
    try:
        buscar(page, "pestana_crear", espera=3).click()
    except ElementoNoEncontrado:
        buscar(page, "panel_ia").click()
        buscar(page, "pestana_crear").click()
    buscar(page, "caja_prompt")


def configurar_ajustes(page):
    """Chip 'Omni • 720p • ▯ • 10s' -> 720p, Horizontal y luego Vertical, 10 s.

    Tocar Horizontal y despues Vertical es a proposito: si solo se ve
    'Vertical' marcado sin tocarlo, los clips salen horizontales.
    """
    buscar(page, "chip_ajustes").click()
    time.sleep(1)
    for clave in ("opcion_resolucion", "opcion_horizontal", "opcion_vertical", "opcion_duracion"):
        try:
            buscar(page, clave, espera=3).click()
            time.sleep(0.7)
        except ElementoNoEncontrado:
            print(f"   (ajuste '{clave}' no aparecio, revisalo a mano)")
    page.keyboard.press("Escape")


def comprobar_tamano(page):
    """Tras el PRIMER clip: debe medir 720x1280. Si no, se para todo."""
    tamanos = page.evaluate(
        "[...document.querySelectorAll('video')]"
        ".filter(v => v.videoWidth).map(v => v.videoWidth + 'x' + v.videoHeight)"
    )
    if tamanos and config.TAMANO_ESPERADO not in tamanos:
        raise TamanoIncorrecto(
            f"El clip mide {tamanos[-1]} y deberia ser {config.TAMANO_ESPERADO}. "
            "Corrige Relacion de aspecto (toca Horizontal y luego Vertical) y vuelve a lanzar."
        )
    return tamanos


# --- Cada escena -------------------------------------------------------------

def limpiar(page):
    """Boton 'Borrar': limpia el prompt y los ingredientes anteriores."""
    try:
        boton = buscar(page, "boton_borrar", espera=1)
        if boton.is_enabled():
            boton.click()
            time.sleep(1)
    except ElementoNoEncontrado:
        pass


def subir_ingredientes(page, rutas):
    """Maximo 3 imagenes, directo al input oculto (sin abrir 'Ingredientes')."""
    for ruta in rutas[: config.MAX_INGREDIENTES]:
        buscar(page, "input_ingredientes", visible=False).set_input_files(ruta)
        time.sleep(config.ESPERA_ENTRE_IMAGENES)


def escribir_prompt(page, prompt):
    caja = buscar(page, "caja_prompt")
    caja.click()
    page.keyboard.press("Control+End")
    page.keyboard.insert_text(prompt)


def generar_escena(page, prompt, ingredientes):
    """Limpia, sube ingredientes, escribe el prompt y pulsa Generar.

    Devuelve cuantas tarjetas listas/rechazadas habia antes, para saber
    despues cual es la nueva.
    """
    abrir_panel(page)
    limpiar(page)
    antes = (contar(page, "senal_listo"), contar_rechazos(page))
    subir_ingredientes(page, ingredientes)
    escribir_prompt(page, prompt)
    buscar(page, "boton_generar").click()
    return antes


def esperar_resultado(page, antes, usar_ia):
    """Espera a que salga la tarjeta nueva. Devuelve 'listo', 'rechazado' o 'tiempo'."""
    listos_antes, rechazos_antes = antes
    inicio = time.time()
    ultima_ia = inicio
    while time.time() - inicio < config.ESPERA_MAXIMA_GENERACION:
        if contar(page, "senal_listo") > listos_antes:
            return "listo"
        if contar_rechazos(page) > rechazos_antes:
            return "rechazado"
        if usar_ia and time.time() - ultima_ia >= config.REVISAR_CON_IA_CADA:
            ultima_ia = time.time()
            estado = ia_vision.estado_de_pantalla(page.screenshot())
            print(f"   IA dice: {estado}")
            if estado == "rechazado":
                return estado
        time.sleep(3)
    return "tiempo"
