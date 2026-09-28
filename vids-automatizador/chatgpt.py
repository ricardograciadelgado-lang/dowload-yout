"""
Acciones dentro de ChatGPT: escenarios y hojas de personaje.

Reglas de la guia del dueno:
- Una conversacion por historia; si una hoja se rechaza, se pide TAL CUAL
  en un chat NUEVO (no se suaviza).
- La pestana tiene que estar visible o ChatGPT no pinta la respuesta:
  se trae al frente y se toma una captura pequena cada ~15 s.
- Si aparece "No se ha podido cargar esta conversacion", se espera unos minutos.
"""

import base64
import time
from pathlib import Path

import config
import paginas
from paginas import ElementoNoEncontrado, contar_textos

S = config.SELECTORES_CHATGPT

# Imagenes grandes de la conversacion (las generadas; no iconos ni avatares)
JS_IMAGENES = """
() => [...document.querySelectorAll('main img')]
  .filter(i => i.naturalWidth >= 512 && i.naturalHeight >= 512)
  .map(i => i.currentSrc || i.src)
  .filter((s, n, todas) => todas.indexOf(s) === n)
"""

JS_DESCARGAR = """
async (src) => {
  const r = await fetch(src, {credentials: 'include'});
  const b = new Uint8Array(await r.arrayBuffer());
  let s = '';
  for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode(...b.subarray(i, i + 0x8000));
  return btoa(s);
}
"""


def armar_prompt(imagen, villano_nombre=None):
    """Prompt de ChatGPT para un escenario o una hoja, segun la guia."""
    if imagen.get("prompt"):
        return imagen["prompt"]  # prompt literal del dueno
    if imagen["tipo"] == "escenario":
        return config.PLANTILLA_ESCENARIO.format(
            lugar=imagen["lugar"], descripcion=imagen["descripcion"]
        )
    descripcion = imagen["descripcion"]
    if imagen.get("villano") or imagen.get("nombre_personaje") == villano_nombre:
        descripcion = f"{descripcion}. {config.PLANTILLA_GORDO}"
    return config.PLANTILLA_PERSONAJE.format(
        nombre=imagen["nombre_personaje"], descripcion=descripcion
    )


def nuevo_chat(page):
    page.bring_to_front()
    try:
        paginas.buscar(page, S, "nuevo_chat", espera=5).click()
    except ElementoNoEncontrado:
        page.goto(config.URL_CHATGPT)
    paginas.buscar(page, S, "caja_prompt", espera=30)


def _enviar(page, prompt):
    caja = paginas.buscar(page, S, "caja_prompt", espera=30)
    caja.click()
    page.keyboard.insert_text(prompt)
    time.sleep(0.5)
    try:
        paginas.buscar(page, S, "boton_enviar", espera=5).click()
    except ElementoNoEncontrado:
        page.keyboard.press("Enter")


def generar_imagen(page, prompt, destino):
    """Pide la imagen en el chat abierto y la guarda en 'destino'.

    Devuelve 'listo', 'rechazado', 'bloqueado' o 'tiempo'.
    """
    page.bring_to_front()
    antes_img = page.evaluate(JS_IMAGENES)
    antes_rech = contar_textos(page, config.TEXTOS_RECHAZO_CHATGPT)
    _enviar(page, prompt)

    inicio = time.time()
    while time.time() - inicio < config.ESPERA_MAXIMA_IMAGEN:
        time.sleep(15 if not config.PRUEBA else 0.5)
        page.bring_to_front()
        page.screenshot(scale="css", clip={"x": 0, "y": 0, "width": 50, "height": 50})

        if contar_textos(page, config.TEXTOS_BLOQUEO_CHATGPT):
            return "bloqueado"
        if contar_textos(page, config.TEXTOS_RECHAZO_CHATGPT) > antes_rech:
            return "rechazado"
        nuevas = [s for s in page.evaluate(JS_IMAGENES) if s not in antes_img]
        if nuevas and not paginas.existe(page, S, "respondiendo"):
            datos = base64.b64decode(page.evaluate(JS_DESCARGAR, nuevas[-1]))
            Path(destino).parent.mkdir(parents=True, exist_ok=True)
            Path(destino).write_bytes(datos)
            return "listo"
    return "tiempo"
