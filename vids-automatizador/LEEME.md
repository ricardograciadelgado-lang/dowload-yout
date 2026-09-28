# Automatizador de Google Vids

Genera los 12 clips de cada historia en Google Vids sin hacerlo a mano:
limpia el panel, sube los ingredientes (máximo 3), pega el prompt completo,
pone 720p + Vertical + 10 s, pulsa **Generar**, espera el resultado y, si el
filtro lo rechaza, reintenta igual una vez y luego con cambios mínimos.

Busca los botones por su **nombre** (no por posición), así que el zoom o
mover la ventana no le afecta.

> Qué **no** hace todavía: armar la línea de tiempo (+ → Insertar, 1 a 12),
> ponerle nombre al video ni descargar el MP4. Eso sigue a mano por ahora.

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
   "mire" la pantalla cuando algo sale raro. Sin ella también funciona.

## Probar sin gastar créditos

Doble clic en **`probar.bat`**. Abre una página falsa que imita Vids y genera
la historia de ejemplo `V0`. Si ves "Terminado. Clips listos: 3/3", todo quedó bien instalado.

## Uso normal

1. Doble clic en **`abrir_chrome.bat`** (tu Chrome normal puede seguir abierto).
   Se abre un Chrome aparte, con su propio perfil.
   - La **primera vez** inicia sesión con la cuenta **Pro** de Vids. Luego queda guardada.
2. En ese Chrome abre un video de la cuenta Pro → **Archivo → Video nuevo →
   Vertical → Video en blanco** (no uses `/videos/create`, abre la otra cuenta).
3. Pon tus historias en **`historias.json`** (mira el ejemplo que trae).
4. Doble clic en **`iniciar.bat`**.
   - Solo una historia: abre una terminal en la carpeta y escribe
     `python generar_videos.py --historia V5`

Si lo cierras a mitad, al volver a abrirlo **salta las escenas que ya salieron**
(lo recuerda en `progreso.json`).

## Qué deja al terminar

- `salida/V5/registro.txt`: qué pasó en cada escena y qué cambios mínimos se hicieron.
- `salida/V5/V5-E03_listo.png`: captura de cada intento.
- `salida/pendientes.txt`: escenas que hay que revisar a mano.

Si el **primer clip** no mide 720x1280, el programa **se para**: revisa en el chip
"Omni • 720p • ▯ • 10s" que esté en Vertical (toca Horizontal y luego Vertical).

## Formato de `historias.json`

```json
{
  "historias": [
    {
      "id": "V5",
      "titulo": "EL TITULO DEL VIDEO",
      "villano_rol": "landlord in the white guayabera",
      "escenas": [
        {
          "numero": 1,
          "titulo": "Título de la escena",
          "imagen": "A candid vertical third-person photograph, ...",
          "audio": "Language: Spanish. Accent: Mexican, working-class urban. Tone: ... Ambient sounds: ...",
          "dialogo": "PERSONAJE (tono): \"Diálogo de 23 a 30 palabras.\"",
          "camara": "plano detalle de ...",
          "sale_villano": true,
          "ingredientes": ["C:/Users/TU_USUARIO/Downloads/Videos Vids tanda V/imagenes/V5__Chayo.png"]
        }
      ]
    }
  ]
}
```

Cuando `sale_villano` es `true`, se añade sola la línea en inglés del villano gordo.

## Ajustes

Todo se cambia en **`config.py`**: resolución, pausas entre escenas, los textos
del filtro, la lista de cambios mínimos y los nombres de los botones de Vids.
Si Google cambia algún botón, solo hay que actualizar `SELECTORES` ahí.

## Aviso

Google puede limitar cuentas que automatizan su página. El programa ya espera
entre 20 y 45 s entre escenas; no lo pongas más rápido ni lo uses para cientos de clips seguidos.
