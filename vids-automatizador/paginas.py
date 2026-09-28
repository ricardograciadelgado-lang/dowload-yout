"""
Herramientas comunes para buscar botones y cajas por su NOMBRE
(sirve igual para Vids y para ChatGPT). Nunca usa posiciones en pantalla.
"""

import time


class ElementoNoEncontrado(Exception):
    pass


def _locator(page, sel):
    if "css" in sel:
        return page.locator(sel["css"])
    if "texto" in sel:
        return page.get_by_text(sel["texto"], exact=False)
    if "nombre" in sel:
        return page.get_by_role(sel["rol"], name=sel["nombre"], exact=False)
    return page.get_by_role(sel["rol"])


def _opciones(selectores, clave):
    opciones = selectores[clave]
    return [opciones] if isinstance(opciones, dict) else opciones


def buscar(page, selectores, clave, visible=True, espera=10):
    """Prueba cada opcion del selector hasta encontrar una en la pagina."""
    limite = time.time() + espera
    while True:
        for sel in _opciones(selectores, clave):
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


def existe(page, selectores, clave):
    try:
        buscar(page, selectores, clave, espera=0)
        return True
    except ElementoNoEncontrado:
        return False


def contar(page, selectores, clave):
    """Cuantos elementos visibles hay de ese tipo (ej. botones Insertar)."""
    total = 0
    for sel in _opciones(selectores, clave):
        loc = _locator(page, sel)
        try:
            total = max(total, sum(1 for i in range(loc.count()) if loc.nth(i).is_visible()))
        except Exception:
            pass
    return total


def contar_textos(page, textos):
    total = 0
    for texto in textos:
        try:
            total += page.get_by_text(texto, exact=False).count()
        except Exception:
            pass
    return total
