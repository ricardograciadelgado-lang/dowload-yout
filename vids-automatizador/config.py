"""
CONFIGURACION DEL AUTOMATIZADOR (ChatGPT + Google Vids)
--------------------------------------------------------
Aqui se cambia todo sin tocar el resto del programa.

Las secciones SELECTORES y SELECTORES_CHATGPT le dicen al programa como
se llama cada boton o caja (sacado de la guia "Hacer videos en Google Vids").

Cada selector puede escribirse de 3 formas:
    {"rol": "button", "nombre": "Generar"}  -> un boton con ese nombre
    {"texto": "Insertar"}                   -> cualquier cosa que muestre ese texto
    {"css": "[contenteditable]"}            -> nombre interno de la pagina (HTML)
Tambien puede ser una LISTA de opciones: se prueba una por una.
"""

# --- Pagina ---------------------------------------------------------------
# OJO: /videos/create abre con la cuenta que NO es Pro. Abre a mano un video
# de la cuenta Pro -> Archivo -> Video nuevo -> Vertical -> Video en blanco.
URL_VIDS = "https://docs.google.com/videos"

# Chrome se abre con abrir_chrome.bat y el programa se conecta a el.
PUERTO_CHROME = 9222

# --- Archivos -------------------------------------------------------------
ARCHIVO_HISTORIAS = "historias.json"
ARCHIVO_ESTADO = "estado.txt"          # resumen corto para que Claude supervise
CARPETA_COMUNICACION = "comunicacion"  # preguntas del programa y respuestas de Claude
ESPERA_RESPUESTA_CLAUDE = 1800         # segundos; si Claude no contesta, salta y sigue
PRUEBA = False                         # lo activa --prueba (no tocar)
ARCHIVO_PROGRESO = "progreso.json"     # recuerda que escenas ya se hicieron
CARPETA_SALIDA = "salida"              # capturas y registro por historia

# --- Generacion -----------------------------------------------------------
RESOLUCION = "720p"                    # 1080p solo si se pide
RELACION = "Vertical"
DURACION = "10s"
TAMANO_ESPERADO = "720x1280"           # se comprueba en el primer clip
MAX_INGREDIENTES = 3                   # limite de Vids: personajes + escenario
ESPERA_ENTRE_IMAGENES = 3.5            # segundos entre ingrediente e ingrediente
MAX_INTENTOS_POR_ESCENA = 3            # 1 normal, 1 igual, 1 con cambios minimos
ESPERA_MAXIMA_GENERACION = 600         # segundos que espera a que termine un clip
PAUSA_ENTRE_ESCENAS = (20, 45)         # segundos al azar, para no ir a ritmo de robot

# Linea que se anade en ingles cuando el villano sale en la escena
LINEA_GORDO = (
    "The {rol} is extremely obese: enormous wide body, huge round swollen face "
    "with a colossal double chin, belly bulging out under clothes far too small "
    "and stretched tight."
)

# --- IA local (Ollama) ----------------------------------------------------
USAR_IA = True
MODELO_IA = "qwen2.5vl:3b"
URL_OLLAMA = "http://localhost:11434"
REVISAR_CON_IA_CADA = 60               # segundos, mientras espera un clip

# --- Filtro de Vids ---------------------------------------------------------
TEXTOS_RECHAZO = [
    "infringe nuestras condiciones",
    "no se puede generar",
    "no se ha podido generar",
    "violates our",
    "can't generate",
    "couldn't generate",
]

# Cambios minimos para el ultimo intento (lo que ya ha bloqueado antes).
# Cada cambio queda anotado en salida/<historia>/registro.txt
CAMBIOS_MINIMOS = {
    "16-year-old": "teenage boy",
    "15-year-old": "teenage boy",
    "17-year-old": "teenage boy",
    "sweating and shouting": "tense and upset",
    "cabrones": "",
    "hueva": "flojera",
    "bájenle": "calma",
    "carnes": "comida",
    "mija": "hija",
    "anticipo": "adelanto",
}

# --- SELECTORES -------------------------------------------------------------
SELECTORES = {
    # Panel derecho "Generacion de video con IA" -> pestana Crear
    "panel_ia": [
        {"texto": "Generación de video con IA"},
    ],
    "pestana_crear": [
        {"rol": "tab", "nombre": "Crear"},
        {"rol": "button", "nombre": "Crear"},
    ],
    # Chip de ajustes "Omni • 720p • ▯ • 10s"
    "chip_ajustes": [
        {"rol": "button", "nombre": "Omni"},
        {"texto": "Omni •"},
    ],
    "opcion_resolucion": [{"texto": RESOLUCION}],
    "opcion_horizontal": [{"rol": "button", "nombre": "Horizontal"}, {"texto": "Horizontal"}],
    "opcion_vertical": [{"rol": "button", "nombre": "Vertical"}, {"texto": "Vertical"}],
    "opcion_duracion": [{"texto": DURACION}],
    # Input oculto de ingredientes (NO hacer clic en "Ingredientes")
    "input_ingredientes": [
        {"css": 'input[type=file][accept*="image/png"]'},
    ],
    # Editor del prompt
    "caja_prompt": [
        {"css": '[contenteditable][aria-label^="Describe tu video"]'},
        {"css": "[contenteditable]"},
    ],
    "boton_generar": [
        {"css": '[aria-label="Generar"]'},
        {"rol": "button", "nombre": "Generar"},
    ],
    "boton_borrar": [
        {"rol": "button", "nombre": "Borrar"},
    ],
    # Aparece en la tarjeta cuando el clip esta listo
    "senal_listo": [
        {"rol": "button", "nombre": "Insertar"},
    ],
}


# ===========================================================================
# CHATGPT (escenarios y hojas de personaje)
# ===========================================================================
URL_CHATGPT = "https://chatgpt.com"
CARPETA_IMAGENES = "imagenes"          # aqui se guardan V5__Chayo.png, V5__tienda.png...
ESPERA_MAXIMA_IMAGEN = 300             # segundos por imagen
# ChatGPT bloquea la carga unos minutos si se abren muchos chats seguidos
PAUSA_ENTRE_CHATS = (40, 80)
ESPERA_SI_BLOQUEA = 300                # "No se ha podido cargar esta conversacion"

PLANTILLA_ESCENARIO = (
    "creame la imagen del escenario {lugar} sin personajes, en formato vertical: "
    "{descripcion} Estética: Documental honesto, luz natural disponible."
)
PLANTILLA_PERSONAJE = (
    "ahora creame la hoja del personaje {nombre} — {descripcion} en fondo blanco "
    "en primer plano de el y en cuerpo completo a la izquierda sin texto"
)
PLANTILLA_GORDO = (
    "Complexión de obesidad mórbida irreal: cuerpo gigantesco, descomunalmente ancho "
    "y deforme por el peso excesivo, rostro exageradamente cachetón, gordote y papujado "
    "con una papada colosal que le oculta el cuello, y la piel llena de severas manchas "
    "grasientas. Su colosal panza sobresale y queda totalmente al descubierto por debajo "
    "de la ropa: cada prenda le queda diminuta, asfixiantemente apretada y encogida, con "
    "las costuras a punto de reventar."
)

TEXTOS_RECHAZO_CHATGPT = [
    "podría infringir nuestras normas",
    "infringir nuestras políticas",
    "no puedo ayudar con eso",
    "may violate our",
    "violate our content policies",
    "can't help with that",
]
TEXTOS_BLOQUEO_CHATGPT = [
    "no se ha podido cargar esta conversación",
    "unable to load conversation",
]

SELECTORES_CHATGPT = {
    "nuevo_chat": [
        {"css": 'a[data-testid="create-new-chat-button"]'},
        {"rol": "link", "nombre": "Nuevo chat"},
        {"rol": "button", "nombre": "Nuevo chat"},
    ],
    "caja_prompt": [
        {"css": "#prompt-textarea"},
        {"css": '[contenteditable][aria-label*="ChatGPT"]'},
    ],
    "boton_enviar": [
        {"css": '[data-testid="send-button"]'},
        {"rol": "button", "nombre": "Enviar"},
    ],
    # Mientras responde aparece el boton de detener
    "respondiendo": [
        {"css": '[data-testid="stop-button"]'},
    ],
    "respuesta": [
        {"css": '[data-message-author-role="assistant"]'},
    ],
}
