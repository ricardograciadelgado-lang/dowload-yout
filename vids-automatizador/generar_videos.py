"""
AUTOMATIZADOR DE GOOGLE VIDS
Genera los 12 clips de cada historia, uno por uno.

Uso normal (primero abre Chrome con abrir_chrome.bat):
    python generar_videos.py

Solo una historia:
    python generar_videos.py --historia V5

Modo prueba (pagina falsa, no gasta creditos ni usa tu cuenta):
    python generar_videos.py --prueba
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

import config
import ia_vision
import vids

AQUI = Path(__file__).parent


def cargar_json(ruta, defecto):
    ruta = AQUI / ruta
    if not ruta.exists():
        return defecto
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_json(ruta, datos):
    (AQUI / ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def anotar(historia_id, linea):
    carpeta = AQUI / config.CARPETA_SALIDA / historia_id
    carpeta.mkdir(parents=True, exist_ok=True)
    hora = datetime.now().strftime("%H:%M:%S")
    with open(carpeta / "registro.txt", "a", encoding="utf-8") as f:
        f.write(f"[{hora}] {linea}\n")


def construir_prompt(historia, escena):
    """Escena completa: imagen + linea del gordo + audio + dialogo + cambio de camara."""
    partes = [escena["imagen"]]
    if escena.get("sale_villano") and historia.get("villano_rol"):
        partes[0] += " " + config.LINEA_GORDO.format(rol=historia["villano_rol"])
    partes.append(escena["audio"])
    if escena.get("dialogo"):
        partes.append(escena["dialogo"])
    if escena.get("camara"):
        partes.append(f"(Cambio de cámara: {escena['camara']})")
    return "\n".join(partes)


def aplicar_cambios_minimos(prompt):
    """Devuelve (prompt nuevo, lista de cambios hechos)."""
    cambios = []
    for viejo, nuevo in config.CAMBIOS_MINIMOS.items():
        if viejo.lower() in prompt.lower():
            inicio = prompt.lower().index(viejo.lower())
            prompt = prompt[:inicio] + nuevo + prompt[inicio + len(viejo):]
            cambios.append(f"'{viejo}' -> '{nuevo}'")
    return prompt, cambios


def conectar(p, prueba, ver=False):
    """Devuelve la pestana de Vids donde se trabajara."""
    if prueba:
        navegador = p.chromium.launch(headless=not ver)
        page = navegador.new_page()
        page.goto((AQUI / "prueba" / "vids_falso.html").as_uri())
        return page
    try:
        navegador = p.chromium.connect_over_cdp(f"http://localhost:{config.PUERTO_CHROME}")
    except Exception:
        sys.exit(
            "No pude conectarme a Chrome.\n"
            "Abre primero abrir_chrome.bat, inicia sesion en Google y vuelve a intentar."
        )
    contexto = navegador.contexts[0]
    for page in contexto.pages:
        if "docs.google.com/videos" in page.url:
            page.bring_to_front()
            return page
    page = contexto.new_page()
    page.goto(config.URL_VIDS)
    input(
        "Abre en esa pestana el video de la cuenta Pro donde van los clips\n"
        "(Archivo -> Video nuevo -> Vertical -> Video en blanco) y pulsa Enter aqui..."
    )
    return page


def ruta_ingrediente(nombre):
    ruta = Path(nombre)
    return str(ruta if ruta.is_absolute() else AQUI / ruta)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historia", help="Solo esta historia (ej: V5)")
    parser.add_argument("--prueba", action="store_true", help="Usa la pagina falsa de prueba")
    parser.add_argument("--ver", action="store_true", help="En modo prueba, muestra el navegador")
    args = parser.parse_args()

    if args.prueba:
        config.PAUSA_ENTRE_ESCENAS = (0, 0)
        config.ESPERA_MAXIMA_GENERACION = 20
        config.ESPERA_ENTRE_IMAGENES = 0.2
        config.ARCHIVO_PROGRESO = "progreso_prueba.json"
        (AQUI / config.ARCHIVO_PROGRESO).unlink(missing_ok=True)

    datos = cargar_json(config.ARCHIVO_HISTORIAS, None)
    if not datos:
        sys.exit(f"No encontre {config.ARCHIVO_HISTORIAS}.")
    historias = datos["historias"]
    if args.historia:
        historias = [h for h in historias if h["id"] == args.historia]

    progreso = cargar_json(config.ARCHIVO_PROGRESO, {})
    usar_ia = ia_vision.ia_disponible()
    print(f"IA local ({config.MODELO_IA}): {'activa' if usar_ia else 'no disponible, sigo sin ella'}")

    pendientes = []
    with sync_playwright() as p:
        page = conectar(p, args.prueba, args.ver)
        vids.abrir_panel(page)
        vids.configurar_ajustes(page)
        tamano_comprobado = False

        for historia in historias:
            hid = historia["id"]
            print(f"\n=== {hid}: {historia.get('titulo', '')} ===")
            for escena in historia["escenas"]:
                clave = f"{hid}-E{escena['numero']:02d}"
                if progreso.get(clave) == "listo":
                    print(f"{clave}: ya estaba hecha, la salto")
                    continue

                prompt = construir_prompt(historia, escena)
                ingredientes = [ruta_ingrediente(i) for i in escena.get("ingredientes", [])]
                estado = "error"
                for intento in range(1, config.MAX_INTENTOS_POR_ESCENA + 1):
                    if intento == config.MAX_INTENTOS_POR_ESCENA and estado == "rechazado":
                        prompt, cambios = aplicar_cambios_minimos(prompt)
                        if not cambios:
                            break  # no hay cambio minimo conocido: queda pendiente
                        print(f"   cambios minimos: {', '.join(cambios)}")
                        anotar(hid, f"{clave} cambios minimos: {', '.join(cambios)}")
                    print(f"{clave}: generando (intento {intento})...")
                    try:
                        antes = vids.generar_escena(page, prompt, ingredientes)
                        estado = vids.esperar_resultado(page, antes, usar_ia)
                    except vids.ElementoNoEncontrado as e:
                        estado = "error"
                        print(f"   {e}")
                    captura = AQUI / config.CARPETA_SALIDA / hid / f"{clave}_{estado}.png"
                    captura.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(captura))
                    anotar(hid, f"{clave} intento {intento}: {estado}")
                    print(f"   -> {estado}")
                    if estado == "listo":
                        break

                if estado == "listo" and not tamano_comprobado:
                    try:
                        print(f"   tamano del clip: {vids.comprobar_tamano(page)}")
                        tamano_comprobado = True
                    except vids.TamanoIncorrecto as e:
                        progreso[clave] = "tamano_incorrecto"
                        guardar_json(config.ARCHIVO_PROGRESO, progreso)
                        sys.exit(f"\nPARO: {e}")

                progreso[clave] = estado
                guardar_json(config.ARCHIVO_PROGRESO, progreso)
                if estado != "listo":
                    pendientes.append(f"{clave} ({estado}): {escena.get('titulo', '')}")

                time.sleep(random.uniform(*config.PAUSA_ENTRE_ESCENAS))

    hechas = sum(1 for v in progreso.values() if v == "listo")
    print(f"\nTerminado. Clips listos: {hechas}/{len(progreso)}")
    print("Siguiente paso a mano: armar la linea de tiempo (boton '+', luego 'Insertar', de la 1 a la 12).")
    if pendientes:
        (AQUI / config.CARPETA_SALIDA / "pendientes.txt").write_text(
            "Escenas que hay que revisar a mano:\n" + "\n".join(pendientes), encoding="utf-8"
        )
        print(f"{len(pendientes)} escenas pendientes -> {config.CARPETA_SALIDA}/pendientes.txt")


if __name__ == "__main__":
    main()
