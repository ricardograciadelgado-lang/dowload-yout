"""
Mando a distancia del automatizador (lo usa Claude, o tu a mano).

    python control.py estado                 -> resumen + pregunta pendiente
    python control.py pregunta               -> muestra la pregunta pendiente
    python control.py responder reintentar
    python control.py responder reintentar_con_prompt --prompt "prompt corregido"
    python control.py responder saltar
    python control.py responder parar
    python control.py pausar | reanudar | parar
"""

import argparse
import json
import sys
from pathlib import Path

import config

AQUI = Path(__file__).parent
ACCIONES = ["reintentar", "reintentar_con_prompt", "saltar", "parar"]


def carpeta():
    ruta = AQUI / config.CARPETA_COMUNICACION
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def leer(nombre):
    ruta = carpeta() / nombre
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def escribir(nombre, datos):
    ruta = carpeta() / nombre
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ruta)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("comando", choices=["estado", "pregunta", "responder", "pausar", "reanudar", "parar"])
    parser.add_argument("accion", nargs="?", choices=ACCIONES)
    parser.add_argument("--prompt", help="Prompt nuevo (con reintentar_con_prompt)")
    parser.add_argument("--prueba", action="store_true", help="Usa la carpeta del modo prueba")
    args = parser.parse_args()

    if args.prueba:
        config.CARPETA_COMUNICACION = "prueba/comunicacion"
        config.ARCHIVO_ESTADO = "prueba/estado_prueba.txt"

    if args.comando == "estado":
        estado = AQUI / config.ARCHIVO_ESTADO
        print(estado.read_text(encoding="utf-8") if estado.exists() else "Todavia no hay estado.")
        args.comando = "pregunta"

    if args.comando == "pregunta":
        pregunta = leer("pregunta.json")
        if pregunta:
            print("PREGUNTA PENDIENTE:\n" + json.dumps(pregunta, ensure_ascii=False, indent=2))
        else:
            print("No hay preguntas pendientes.")
        return

    if args.comando == "responder":
        pregunta = leer("pregunta.json")
        if not pregunta:
            sys.exit("No hay ninguna pregunta pendiente.")
        if not args.accion:
            sys.exit(f"Falta la accion: {', '.join(pregunta['opciones'])}")
        if args.accion not in pregunta["opciones"]:
            sys.exit(f"Para esta pregunta solo vale: {', '.join(pregunta['opciones'])}")
        if args.accion == "reintentar_con_prompt" and not args.prompt:
            sys.exit('Falta --prompt "..."')
        escribir("respuesta.json", {"id": pregunta["id"], "accion": args.accion, "prompt": args.prompt})
        print(f"Respuesta enviada: {args.accion}")
        return

    escribir("orden.json", {"orden": args.comando})
    print(f"Orden enviada: {args.comando}")


if __name__ == "__main__":
    main()
