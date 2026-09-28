"""
CONFIGURACION DEL AUTOMATIZADOR DE GOOGLE VIDS
------------------------------------------------
Aqui se cambia todo sin tocar el resto del programa.

La seccion SELECTORES le dice al programa como se llama cada boton o
caja dentro de Vids (sacado de la guia "Hacer videos en Google Vids").

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
