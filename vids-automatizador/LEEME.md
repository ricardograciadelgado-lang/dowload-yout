# Automatizador de videos (ChatGPT + Google Vids)

Un solo programa para todo el trabajo de cada historia:

1. **ChatGPT**: pide los escenarios y las hojas de personaje (con la plantilla
   del villano gordo) y los guarda en `imagenes/` con nombres claros
   (`V5__Chayo.png`, `V5__tienda.png`). Si una hoja se rechaza, la pide
   **tal cual en un chat nuevo**, como dice la guía.
2. **Google Vids**: genera los 12 clips. Limpia el panel, sube los ingredientes
   (máximo 3), pega el prompt completo, pone 720p + Vertical + 10 s y pulsa
   **Generar**. Si el filtro rechaza, reintenta igual una vez y luego con
   cambios mínimos. Comprueba que el primer clip mida 720x1280.

Busca los botones por su **nombre**, no por posición, así que el zoom o mover
la ventana no le afecta.

**Se comunica con tu Claude de escritorio**, que lo supervisa sin gastar
tokens mirando la pantalla (ver `INSTRUCCIONES_CLAUDE.md`):
- `python control.py estado`: resumen de cómo va y pregunta pendiente.
- Cuando algo no sale solo, el programa **se pausa y le pregunta a Claude**.
  Claude contesta, por ejemplo `python control.py responder reintentar_con_prompt --prompt "..."`,
  y el programa sigue.
- Claude puede pausar, reanudar o parar el trabajo en cualquier momento.

> Qué **no** hace todavía: armar la línea de tiempo (+ → Insertar, 1 a 12),
> ponerle nombre al video ni descargar el MP4. Eso lo hace Claude de escritorio
> o se hace a mano.

---

## Instalación en Windows (una sola vez, ~15 min)

1. **Python**: descárgalo de <https://www.python.org/downloads/>.
   En el instalador marca **"Add python.exe to PATH"** y dale a *Install Now*.
2. **Este programa**: copia la carpeta `vids-automatizador` a tu PC
   (por ejemplo a `Documentos\vids-automatizador`).
3. Doble clic en **`instalar.bat`**.
4. **(Opcional) IA local**: instala Ollama desde <https://ollama.com>,
   abre una terminal y escribe:
   ```
   ollama pull qwen2.5vl:3b
   ```
   Pesa unos 3 GB y cabe en tu RTX 3050 de 4 GB. Sirve para que el programa
   "mire" la pantalla de Vids cuando algo sale raro. Sin ella también funciona.

## Probar sin gastar créditos

Doble clic en **`probar.bat`**. Abre páginas falsas que imitan ChatGPT y Vids
y hace una historia de prueba completa (3 imágenes + 3 clips, con una hoja
rechazada que se rehace en un chat nuevo).

## Uso normal

1. Doble clic en **`abrir_chrome.bat`** (tu Chrome normal puede seguir abierto).
   Se abre un Chrome aparte, con su propio perfil.
   - La **primera vez** inicia sesión en **ChatGPT** y en la cuenta **Pro** de
     Google Vids. Luego queda guardado.
2. En ese Chrome abre un video de la cuenta Pro → **Archivo → Video nuevo →
   Vertical → Video en blanco** (no uses `/videos/create`, abre la otra cuenta).
3. Pon tus historias en **`historias.json`** (mira el ejemplo que trae).
4. Doble clic en **`iniciar.bat`**.

Opciones (en una terminal abierta en la carpeta):

| Comando | Qué hace |
|---|---|
| `python automatizador.py` | Todo: imágenes y luego clips |
| `python automatizador.py --historia V5` | Solo esa historia |
| `python automatizador.py --solo imagenes` | Solo ChatGPT |
| `python automatizador.py --solo vids` | Solo Vids (con imágenes que ya tengas) |
| `python automatizador.py --resumen` | Solo muestra cómo va todo |

Si lo cierras a mitad, al volver a abrirlo **salta lo que ya está hecho**:
las imágenes que ya existen en `imagenes/` y los clips anotados en `progreso.json`.

Las imágenes que ya tengas (por ejemplo las de V3 y V4) solo hay que copiarlas
a `imagenes/` con su nombre (`V3__Chayo.png`) y no se vuelven a pedir.

## Qué deja al terminar

- `estado.txt`: resumen por historia y lista **NECESITA REVISION**.
- `imagenes/`: escenarios y hojas de personaje.
- `salida/V5/registro.txt`: qué pasó en cada imagen y en cada clip, y qué cambios mínimos se hicieron.
- `salida/V5/V5-E03_listo.png`: captura de cada intento en Vids.

## Formato de `historias.json`

Mira el ejemplo que viene en `historias.json`. Resumen:

- `imagenes`: lo que se pide a ChatGPT.
  - Escenario: `tipo: "escenario"`, `lugar` y `descripcion` (siempre la descripción literal del lugar).
  - Personaje: `tipo: "personaje"`, `nombre_personaje` y `descripcion`.
  - Si prefieres escribir el prompt entero tú, pon `"prompt": "..."` y se usa tal cual.
- `villano_nombre`: su hoja lleva sola la plantilla del villano gordo.
- `escenas`: `imagen`, `audio`, `dialogo`, `camara`, `sale_villano` e
  `ingredientes` (nombres de `imagenes`, máximo 3). Cuando `sale_villano` es
  `true`, se añade sola la línea en inglés del gordo usando `villano_rol`.

## Ajustes

Todo se cambia en **`config.py`**: resolución, pausas, plantillas, los textos
de rechazo, la lista de cambios mínimos y los nombres de los botones
(`SELECTORES` para Vids y `SELECTORES_CHATGPT` para ChatGPT). Si Google u
OpenAI cambian un botón, solo hay que actualizar su nombre ahí.

## Aviso

Google y OpenAI pueden limitar cuentas que automatizan sus páginas. El programa
ya hace pausas entre escenas y entre chats; no lo pongas más rápido ni lo uses
para cientos de imágenes o clips seguidos.
