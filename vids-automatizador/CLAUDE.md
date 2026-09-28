# Proyecto: automatizador de videos (ChatGPT + Google Vids)

Eres el supervisor de este programa. Antes de hacer nada, lee
`INSTRUCCIONES_CLAUDE.md` (cómo lanzarlo, vigilarlo y responderle) y, si el
dueño la adjunta, la guía "Hacer videos en Google Vids".

Resumen rápido:
- Lanzar (en segundo plano): `python automatizador.py` (o `--historia V5`).
- Vigilar cada 5-10 min: `python control.py estado`. No mires el navegador salvo que haga falta.
- Si hay PREGUNTA PENDIENTE: `python control.py responder <accion> [--prompt "..."]`.
- Pausar / reanudar / parar: `python control.py pausar|reanudar|parar`.
- Probar sin gastar créditos: `python automatizador.py --prueba`.
