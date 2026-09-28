"""
IA local que "mira" la pantalla.

Usa Ollama (gratis, corre en tu PC) con un modelo que entiende imagenes.
Solo se le hacen preguntas simples, porque los modelos pequenos
(3B-4B) se equivocan si se les pide manejar la pagina sola.
"""

import base64

import requests

import config

ESTADOS = ("listo", "rechazado", "cargando")

PREGUNTA_ESTADO = (
    "Esta es una captura de Google Vids mientras genera un clip de video. "
    "Responde con UNA sola palabra:\n"
    "- listo: si el video ya se genero y se ve el resultado\n"
    "- rechazado: si aparece un mensaje de error, de politica o de que no se pudo generar\n"
    "- cargando: si todavia esta generando o esperando\n"
    "Respuesta:"
)


def ia_disponible():
    """True si Ollama esta encendido y tiene el modelo descargado."""
    if not config.USAR_IA:
        return False
    try:
        r = requests.get(f"{config.URL_OLLAMA}/api/tags", timeout=3)
        modelos = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return False
    base = config.MODELO_IA.split(":")[0]
    return any(m == config.MODELO_IA or m.startswith(base) for m in modelos)


def preguntar(captura_png, pregunta):
    """Manda una captura y una pregunta a la IA. Devuelve su respuesta en texto."""
    imagen = base64.b64encode(captura_png).decode()
    r = requests.post(
        f"{config.URL_OLLAMA}/api/chat",
        json={
            "model": config.MODELO_IA,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [{"role": "user", "content": pregunta, "images": [imagen]}],
        },
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def estado_de_pantalla(captura_png):
    """Devuelve 'listo', 'rechazado', 'cargando' o 'desconocido'."""
    try:
        respuesta = preguntar(captura_png, PREGUNTA_ESTADO).lower()
    except Exception as e:
        print(f"   (IA no respondio: {e})")
        return "desconocido"
    for estado in ESTADOS:
        if estado in respuesta:
            return estado
    return "desconocido"
