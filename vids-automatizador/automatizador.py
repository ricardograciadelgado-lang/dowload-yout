"""
AUTOMATIZADOR: ChatGPT (imagenes) + Google Vids (clips)
Un solo programa para todo el trabajo de cada historia:
  1) ChatGPT: escenarios y hojas de personaje -> carpeta imagenes/
  2) Vids: los 12 clips con esas imagenes como ingredientes

Uso normal (primero abre Chrome con abrir_chrome.bat):
    python automatizador.py
    python automatizador.py --historia V5        (solo una historia)
    python automatizador.py --solo imagenes      (solo ChatGPT)
    python automatizador.py --solo vids          (solo Vids)
    python automatizador.py --resumen            (solo muestra como va)

Modo prueba (paginas falsas, no gasta creditos ni usa tus cuentas):
    python automatizador.py --prueba
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

import chatgpt
import config
import ia_vision
import vids

AQUI = Path(__file__).parent


# --- Archivos ---------------------------------------------------------------

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


def ruta_imagen(nombre):
    """'V5__Chayo' -> imagenes/V5__Chayo.png ; una ruta completa se deja igual."""
    ruta = Path(nombre)
    if ruta.suffix == "":
        ruta = Path(config.CARPETA_IMAGENES) / f"{nombre}.png"
    return ruta if ruta.is_absolute() else AQUI / ruta


# --- Resumen para supervisar (Claude de escritorio lee esto) -----------------

def escribir_estado(historias, progreso, fase, pendientes):
    lineas = [f"Actualizado: {datetime.now():%Y-%m-%d %H:%M:%S}", f"Trabajando en: {fase}", ""]
    for h in historias:
        imgs = h.get("imagenes", [])
        img_ok = sum(1 for i in imgs if ruta_imagen(i["nombre"]).exists())
        clips = [f"{h['id']}-E{e['numero']:02d}" for e in h["escenas"]]
        clips_ok = sum(1 for c in clips if progreso.get(c) == "listo")
        lineas.append(f"{h['id']} {h.get('titulo', '')}: imagenes {img_ok}/{len(imgs)}, clips {clips_ok}/{len(clips)}")
    lineas.append("")
    if pendientes:
        lineas.append("NECESITA REVISION:")
        lineas += [f"- {p}" for p in pendientes]
    else:
        lineas.append("Sin problemas por ahora.")
    texto = "\n".join(lineas) + "\n"
    (AQUI / config.ARCHIVO_ESTADO).write_text(texto, encoding="utf-8")
    return texto


# --- Navegador ----------------------------------------------------------------

def _pestana(contexto, contiene, url, mensaje):
    for page in contexto.pages:
        if contiene in page.url:
            return page
    page = contexto.new_page()
    page.goto(url)
    if mensaje:
        input(mensaje)
    return page


def conectar(p, prueba, ver, necesita_chatgpt, necesita_vids):
    """Devuelve (pestana_chatgpt, pestana_vids)."""
    if prueba:
        contexto = p.chromium.launch(headless=not ver).new_context()
        gpt = contexto.new_page()
        gpt.goto((AQUI / "prueba" / "chatgpt_falso.html").as_uri())
        vid = contexto.new_page()
        vid.goto((AQUI / "prueba" / "vids_falso.html").as_uri())
        return gpt, vid
    try:
        navegador = p.chromium.connect_over_cdp(f"http://localhost:{config.PUERTO_CHROME}")
    except Exception:
        sys.exit(
            "No pude conectarme a Chrome.\n"
            "Abre primero abrir_chrome.bat, inicia sesion y vuelve a intentar."
        )
    contexto = navegador.contexts[0]
    gpt = vid = None
    if necesita_chatgpt:
        gpt = _pestana(contexto, "chatgpt.com", config.URL_CHATGPT, None)
    if necesita_vids:
        vid = _pestana(
            contexto, "docs.google.com/videos", config.URL_VIDS,
            "Abre en esa pestana el video de la cuenta Pro donde van los clips\n"
            "(Archivo -> Video nuevo -> Vertical -> Video en blanco) y pulsa Enter aqui...",
        )
    return gpt, vid


# --- Fase 1: ChatGPT ---------------------------------------------------------

def fase_imagenes(page, historia, pendientes, actualizar):
    hid = historia["id"]
    faltan = [i for i in historia.get("imagenes", []) if not ruta_imagen(i["nombre"]).exists()]
    if not faltan:
        return
    print(f"\n=== {hid}: imagenes en ChatGPT ({len(faltan)} por hacer) ===")
    chatgpt.nuevo_chat(page)  # una conversacion por historia
    for imagen in faltan:
        nombre = imagen["nombre"]
        prompt = chatgpt.armar_prompt(imagen, historia.get("villano_nombre"))
        destino = ruta_imagen(nombre)
        estado = "error"
        for intento in range(1, config.MAX_INTENTOS_POR_ESCENA + 1):
            print(f"{nombre}: pidiendo a ChatGPT (intento {intento})...")
            try:
                estado = chatgpt.generar_imagen(page, prompt, destino)
            except chatgpt.ElementoNoEncontrado as e:
                estado = "error"
                print(f"   {e}")
            print(f"   -> {estado}")
            anotar(hid, f"{nombre} intento {intento}: {estado}")
            if estado == "listo":
                break
            if estado == "bloqueado":
                print(f"   ChatGPT bloqueo la carga; espero {config.ESPERA_SI_BLOQUEA} s")
                time.sleep(0 if config.PRUEBA else config.ESPERA_SI_BLOQUEA)
                page.reload()
            # Rechazada: la misma peticion TAL CUAL en un chat NUEVO
            time.sleep(random.uniform(*config.PAUSA_ENTRE_CHATS))
            chatgpt.nuevo_chat(page)
        if estado != "listo":
            pendientes.append(f"{nombre} ({estado}): hacer la hoja a mano en un chat nuevo")
        actualizar(f"{hid} imagenes")
        time.sleep(random.uniform(*config.PAUSA_ENTRE_ESCENAS) / 4)


# --- Fase 2: Vids ------------------------------------------------------------

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


def fase_vids(page, historia, progreso, usar_ia, estado_global, pendientes, actualizar):
    hid = historia["id"]
    print(f"\n=== {hid}: clips en Vids ===")
    page.bring_to_front()
    if not estado_global["ajustado"]:
        vids.abrir_panel(page)
        vids.configurar_ajustes(page)
        estado_global["ajustado"] = True

    for escena in historia["escenas"]:
        clave = f"{hid}-E{escena['numero']:02d}"
        if progreso.get(clave) == "listo":
            print(f"{clave}: ya estaba hecha, la salto")
            continue

        ingredientes = [ruta_imagen(i) for i in escena.get("ingredientes", [])]
        faltan = [i.name for i in ingredientes if not i.exists()]
        if faltan:
            print(f"{clave}: faltan imagenes {faltan}, la salto")
            pendientes.append(f"{clave}: faltan ingredientes {', '.join(faltan)}")
            continue

        prompt = construir_prompt(historia, escena)
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
                antes = vids.generar_escena(page, prompt, [str(i) for i in ingredientes])
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

        if estado == "listo" and not estado_global["tamano_ok"]:
            try:
                print(f"   tamano del clip: {vids.comprobar_tamano(page)}")
                estado_global["tamano_ok"] = True
            except vids.TamanoIncorrecto as e:
                progreso[clave] = "tamano_incorrecto"
                guardar_json(config.ARCHIVO_PROGRESO, progreso)
                pendientes.append(f"PARADO: {e}")
                actualizar("parado por tamano incorrecto")
                sys.exit(f"\nPARO: {e}")

        progreso[clave] = estado
        guardar_json(config.ARCHIVO_PROGRESO, progreso)
        if estado != "listo":
            pendientes.append(f"{clave} ({estado}): {escena.get('titulo', '')}")
        actualizar(f"{hid} clips")
        time.sleep(random.uniform(*config.PAUSA_ENTRE_ESCENAS))


# --- Principal ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historia", help="Solo esta historia (ej: V5)")
    parser.add_argument("--solo", choices=["imagenes", "vids"], help="Solo una de las dos fases")
    parser.add_argument("--resumen", action="store_true", help="Solo muestra como va todo")
    parser.add_argument("--prueba", action="store_true", help="Usa las paginas falsas de prueba")
    parser.add_argument("--ver", action="store_true", help="En modo prueba, muestra el navegador")
    args = parser.parse_args()

    if args.prueba:
        config.PRUEBA = True
        config.PAUSA_ENTRE_ESCENAS = (0, 0)
        config.PAUSA_ENTRE_CHATS = (0, 0)
        config.ESPERA_MAXIMA_GENERACION = 20
        config.ESPERA_MAXIMA_IMAGEN = 20
        config.ESPERA_ENTRE_IMAGENES = 0.2
        config.ARCHIVO_HISTORIAS = "prueba/historias_prueba.json"
        config.ARCHIVO_PROGRESO = "prueba/progreso_prueba.json"
        config.ARCHIVO_ESTADO = "prueba/estado_prueba.txt"
        config.CARPETA_IMAGENES = "prueba/imagenes"
        config.CARPETA_SALIDA = "prueba/salida"
        (AQUI / config.ARCHIVO_PROGRESO).unlink(missing_ok=True)
        for f in (AQUI / config.CARPETA_IMAGENES).glob("*.png"):
            f.unlink()

    datos = cargar_json(config.ARCHIVO_HISTORIAS, None)
    if not datos:
        sys.exit(f"No encontre {config.ARCHIVO_HISTORIAS}.")
    historias = datos["historias"]
    if args.historia:
        historias = [h for h in historias if h["id"] == args.historia]

    progreso = cargar_json(config.ARCHIVO_PROGRESO, {})
    pendientes = []

    def actualizar(fase):
        escribir_estado(historias, progreso, fase, pendientes)

    if args.resumen:
        print(escribir_estado(historias, progreso, "nada (solo resumen)", []))
        return

    hacer_imagenes = args.solo in (None, "imagenes")
    hacer_vids = args.solo in (None, "vids")
    usar_ia = hacer_vids and ia_vision.ia_disponible()
    if hacer_vids:
        print(f"IA local ({config.MODELO_IA}): {'activa' if usar_ia else 'no disponible, sigo sin ella'}")
    actualizar("empezando")

    with sync_playwright() as p:
        pagina_gpt, pagina_vids = conectar(p, args.prueba, args.ver, hacer_imagenes, hacer_vids)
        estado_global = {"ajustado": False, "tamano_ok": False}
        for historia in historias:
            if hacer_imagenes:
                fase_imagenes(pagina_gpt, historia, pendientes, actualizar)
            if hacer_vids:
                fase_vids(pagina_vids, historia, progreso, usar_ia, estado_global, pendientes, actualizar)

    actualizar("terminado")
    print("\n" + (AQUI / config.ARCHIVO_ESTADO).read_text(encoding="utf-8"))
    if hacer_vids:
        print("Siguiente paso a mano: armar la linea de tiempo (boton '+', luego 'Insertar', de la 1 a la 12).")


if __name__ == "__main__":
    main()
