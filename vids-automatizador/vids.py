"""
Acciones dentro de Google Vids (segun la guia del dueno).

Todo se busca por NOMBRE del boton/caja (ver SELECTORES en config.py),
nunca por posicion en la pantalla. Por eso el zoom o mover la ventana
no afecta.
"""

import time

import config
import ia_vision


class ElementoNoEncontrado(Exception):
    pass


class TamanoIncorrecto(Exception):
    pass


def _locator(page, sel):
    if "css" in sel:
        return page.locator(sel["css"])
    if "texto" in sel:
        return page.get_by_text(sel["texto"], exact=False)
    if "nombre" in sel:
        return page.get_by_role(sel["rol"], name=sel["nombre"], exact=False)
    return page.get_by_role(sel["rol"])


def _opciones(clave):
    opciones = config.SELECTORES[clave]
    return [opciones] if isinstance(opciones, dict) else opciones


def buscar(page, clave, visible=True, espera=10):
    """Prueba cada opcion del selector hasta encontrar una en la pagina."""
    limite = time.time() + espera
    while True:
        for sel in _opciones(clave):
            loc = _locator(page, sel)
            try:
                for i in range(loc.count()):
                    elemento = loc.nth(i)
                    if not visible or elemento.is_visible():
                        return elemento
            except Exception:
                pass
        if time.time() > limite:
            raise ElementoNoEncontrado(f"No encontre '{clave}' en la pagina")
        time.sleep(0.5)


def existe(page, clave):
    try:
        buscar(page, clave, espera=0)
        return True
    except ElementoNoEncontrado:
        return False


def contar(page, clave):
    """Cuantos elementos visibles hay de ese tipo (ej. botones Insertar)."""
    total = 0
    for sel in _opciones(clave):
        loc = _locator(page, sel)
        try:
            total = max(total, sum(1 for i in range(loc.count()) if loc.nth(i).is_visible()))
        except Exception:
            pass
    return total


def contar_rechazos(page):
    total = 0
    for texto in config.TEXTOS_RECHAZO:
        try:
            total += page.get_by_text(texto, exact=False).count()
        except Exception:
            pass
    return total


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
