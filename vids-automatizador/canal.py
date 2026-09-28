"""
Canal de comunicacion entre el programa y Claude (supervisor).

- Cuando algo falla y el programa no puede resolverlo solo, escribe
  comunicacion/pregunta.json y SE PAUSA hasta que Claude conteste con
  control.py (o hasta que pase ESPERA_RESPUESTA_CLAUDE: entonces salta y sigue).
- Entre paso y paso revisa comunicacion/orden.json por si Claude mando
  pausar, reanudar o parar.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import config

AQUI = Path(__file__).parent


class ParadaPedida(Exception):
    pass


def carpeta():
    ruta = AQUI / config.CARPETA_COMUNICACION
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _leer(nombre):
    ruta = carpeta() / nombre
    if not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None  # se esta escribiendo; se lee en la siguiente vuelta


def _escribir(nombre, datos):
    ruta = carpeta() / nombre
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ruta)


def _borrar(nombre):
    (carpeta() / nombre).unlink(missing_ok=True)


def revisar_ordenes():
    """Llamar entre pasos. Bloquea si Claude pidio pausa; lanza ParadaPedida si pidio parar."""
    avisado = False
    while True:
        orden = (_leer("orden.json") or {}).get("orden")
        if orden == "parar":
            _borrar("orden.json")
            raise ParadaPedida("Claude pidio parar")
        if orden != "pausar":
            return
        if not avisado:
            print("   (en pausa por orden de Claude; esperando 'reanudar')")
            avisado = True
        time.sleep(2)


def preguntar(tipo, clave, detalle, prompt=None, captura=None, opciones=None):
    """Deja la pregunta para Claude y espera su respuesta.

    Devuelve un dict como {"accion": "reintentar", "prompt": "..."}.
    Acciones: reintentar, reintentar_con_prompt, saltar, parar.
    """
    opciones = opciones or ["reintentar", "reintentar_con_prompt", "saltar", "parar"]
    pregunta = {
        "id": f"{clave}-{int(time.time())}",
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,
        "clave": clave,
        "detalle": detalle,
        "prompt_actual": prompt,
        "captura": str(captura) if captura else None,
        "opciones": opciones,
        "como_responder": "python control.py responder <accion> [--prompt \"...\"]",
    }
    _borrar("respuesta.json")
    _escribir("pregunta.json", pregunta)
    print(f"   ESPERANDO A CLAUDE: {tipo} en {clave} (ver {config.CARPETA_COMUNICACION}/pregunta.json)")

    limite = time.time() + config.ESPERA_RESPUESTA_CLAUDE
    while time.time() < limite:
        respuesta = _leer("respuesta.json")
        if respuesta and respuesta.get("id") in (pregunta["id"], None):
            _borrar("respuesta.json")
            _borrar("pregunta.json")
            print(f"   Claude responde: {respuesta.get('accion')}")
            if respuesta.get("accion") == "parar":
                raise ParadaPedida("Claude pidio parar")
            return respuesta
        time.sleep(2)

    _borrar("pregunta.json")
    print("   Claude no respondio a tiempo; la salto y sigo")
    return {"accion": "saltar", "motivo": "sin respuesta"}
