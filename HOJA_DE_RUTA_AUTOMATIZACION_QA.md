# Hoja de ruta — Automatización de tu flujo QA

**Proyecto:** Enterprise 2026 (monday.com) + oneshop
**Autor:** Manuel Villegas
**Fecha:** 2026-05-11

Este documento traduce tu flujo manual actual a un flujo automatizado usando **Cursor** y **Claude Code** como copilotos, y **Playwright (Python)** como motor de ejecución. Está organizado en **6 fases** que puedes ir activando una por una sin romper lo anterior.

---

## 1. Mapeo de tu flujo actual → qué automatizar

| # | Paso manual hoy | ¿Automatizable? | Herramienta destino |
|---|---|---|---|
| 1 | Abrir Monday → board Enterprise 2026 | No (login humano) | — |
| 2 | Filtrar tickets `QA ready` | Sí (visualización) | Monday API + script `qa list` |
| 3 | Auto-asignarte el ticket | **No automatizar** (tú decides) | — |
| 4 | Mover `QA ready` → `QA in progress` | **No automatizar** (decisión consciente) | — |
| 5 | Leer descripción + comentarios + updates | Sí (extracción) | Monday API + Claude resume |
| 6 | Diseñar casos de prueba a partir del ticket | Sí | Skill `qa-test-design` + Claude |
| 7 | Ejecutar pruebas en oneshop | Sí (la mayoría) | Playwright (Python) |
| 8 | Grabar video evidencia | Sí (nativo) | Playwright video + trace |
| 9 | Generar reporte QA positivo/negativo | Sí | Skill `qa-report` + plantilla |
| 10 | Pegar reporte como update en el ticket | Sí | Monday API |
| 11 | Mover ticket a `QA passed` / `QA failed` | Sí | Monday API |

**Resumen:** se automatiza todo excepto la decisión humana de tomar un ticket (pasos 3 y 4), que se mantiene como gate manual.

---

## 2. Stack recomendado

| Capa | Herramienta | Por qué |
|---|---|---|
| Editor IA | **Cursor** | Autocompletado contextual, edits inline, ideal para escribir tests |
| Agente IA | **Claude Code** (CLI) | Ejecuta tareas largas, lee/edita múltiples archivos, slash commands y skills |
| Lenguaje | **Python 3.11+** | Sintaxis amigable para QA, ecosistema maduro, fácil para nivel 2–3 |
| E2E framework | **Playwright** (`pytest-playwright`) | Graba video + trace + screenshots automáticos, multi-navegador, locators robustos |
| Test runner | **pytest** | Fixtures, marks, reportes HTML, paralelización |
| HTTP/API (Fase 6) | **httpx** o `playwright.request` | Para futuras pruebas de API |
| Integración Monday | **Monday GraphQL API v2** + `requests` | API oficial, gratuita en tu plan |
| Reportes | **pytest-html** + plantilla Markdown propia | Reporte legible que puedas pegar en Monday |
| Secrets | `.env` + `python-dotenv` | API tokens fuera del repo |

**¿Por qué Python y no JavaScript/TypeScript?**
Playwright funciona perfecto en ambos. Recomiendo Python porque:
1. La sintaxis se lee casi como inglés — más fácil para nivel 2–3.
2. pytest es el estándar de oro en QA y muchas empresas lo piden.
3. Si mañana quieres añadir testing de APIs, data validation o scripts auxiliares, Python es más versátil.

Si tu equipo usa JS/TS, podemos hacer el switch fácilmente — la estructura del proyecto es equivalente.

---

## 3. Fases de implementación

### Fase 0 — Setup del entorno (1–2 horas)

**Objetivo:** Tener Cursor + Claude Code + Python + Playwright instalados y el repo inicializado.

**Pasos:**

1. Instala **Cursor** desde https://cursor.com
2. Instala **Claude Code** (CLI):
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude login
   ```
3. Instala Python 3.11+ y crea el proyecto:
   ```bash
   cd "QA Automation Flow"
   python3 -m venv .venv
   source .venv/bin/activate   # en Mac/Linux
   # .venv\Scripts\activate    # en Windows
   pip install pytest pytest-playwright pytest-html python-dotenv requests
   playwright install chromium firefox webkit
   ```
4. Inicializa git:
   ```bash
   git init
   echo ".venv/\n.env\nreports/\nvideos/\ntraces/\n__pycache__/" > .gitignore
   ```
5. Abre la carpeta en Cursor y en Claude Code:
   ```bash
   cursor .
   claude   # arranca Claude Code en la misma carpeta
   ```

**Entregable Fase 0:** repo vacío, dependencias instaladas, Cursor + Claude Code funcionando.

---

### Fase 1 — Configurar Claude Code para tu flujo (2–3 horas) — **QUICK WIN**

**Objetivo:** Que Claude Code "entienda" tu contexto QA y tenga slash commands listos para diseñar casos de prueba y reportes.

**1.1 Crea el archivo `CLAUDE.md`** en la raíz del proyecto. Este archivo se carga automáticamente cada vez que abras Claude Code aquí. Es tu manual de instrucciones para el agente.

Contenido sugerido:
```markdown
# Proyecto: QA Automation — Enterprise 2026

## Contexto
- QA manual de oneshop, automatizando con Playwright + Python.
- Gestor de incidencias: monday.com, board "Enterprise 2026".
- Estados de ticket: QA ready → QA in progress → QA passed / QA failed.

## Convenciones
- Tests en `tests/`, organizados por módulo funcional.
- Page Objects en `pages/`.
- Datos de prueba en `data/`.
- Reportes generados en `reports/`.
- Lenguaje de tests: español en docstrings, inglés en nombres de funciones.

## Comandos comunes
- `pytest --headed` — corre tests con navegador visible
- `pytest -m smoke` — solo smoke tests
- `pytest --html=reports/last.html` — genera reporte HTML

## Estilo
- Cada test debe grabar video y trace.
- Cada test debe tener un docstring con: ID Monday, descripción, precondiciones.
```

**1.2 Crea slash commands personalizados** en `.claude/commands/`:

`.claude/commands/qa-design.md`:
```markdown
---
description: Diseña casos de prueba a partir de un ticket de Monday
---

Vas a actuar como QA senior. Lee el siguiente texto de un ticket de monday.com
(descripción + comentarios) y genera casos de prueba estructurados:

$ARGUMENTS

Devuelve una tabla Markdown con:
- ID (TC-001, TC-002…)
- Título
- Precondiciones
- Pasos
- Resultado esperado
- Prioridad (Alta/Media/Baja)
- Tipo (Funcional / UI / Regresión / Negativa / Borde)

Incluye al menos 1 caso negativo y 1 caso de borde por funcionalidad.
```

`.claude/commands/qa-report.md`:
```markdown
---
description: Genera reporte QA (positivo o negativo) listo para pegar en Monday
---

Genera un reporte QA en Markdown con esta estructura:

# Reporte QA — [Título del ticket]
**Ticket:** [ID Monday]
**Ambiente:** [staging/prod]
**Navegador:** [Chrome/Firefox/Safari]
**Fecha:** [YYYY-MM-DD]
**Estado general:** PASSED ✓ / FAILED ✗

## Overview
[Resumen 2-3 líneas del cambio probado]

## Casos ejecutados
| ID | Caso | Estado |
|---|---|---|
| TC-001 | … | PASSED |
| TC-002 | … | FAILED |

## Evidencia
- Video: [link]
- Screenshots: [links]

## Hallazgos
[Si FAILED: descripción del defecto, pasos para reproducir, severidad]

Input del ejecutor:
$ARGUMENTS
```

**1.3 Prueba el slash command** en Claude Code:
```
/qa-design
[pega aquí el texto de un ticket de Monday]
```

**Entregable Fase 1:** Claude Code te genera casos de prueba y reportes con un solo comando, copiando texto manualmente del ticket. **Ya estás ahorrando tiempo aquí**, aunque todavía no conectes Monday.

---

### Fase 2 — Estructura del proyecto Playwright (3–4 horas)

**Objetivo:** Tener el esqueleto del proyecto listo para empezar a escribir tests.

Estructura propuesta:
```
QA Automation Flow/
├── CLAUDE.md
├── .claude/
│   └── commands/
│       ├── qa-design.md
│       ├── qa-report.md
│       ├── qa-run.md
│       └── qa-publish.md
├── .env.example
├── conftest.py              # fixtures globales pytest
├── pytest.ini               # config pytest
├── pages/                   # Page Objects
│   ├── __init__.py
│   ├── base_page.py
│   └── home_page.py
├── tests/
│   ├── __init__.py
│   ├── smoke/
│   └── regression/
├── data/                    # datos de prueba (JSON/YAML)
├── utils/
│   ├── monday_client.py     # cliente Monday API
│   └── report_builder.py    # genera reporte Markdown
├── reports/                 # output HTML/MD
├── videos/                  # videos Playwright
└── traces/                  # traces Playwright
```

**Pídele a Claude Code que arme esta estructura:**
```
Crea la estructura inicial del proyecto Playwright siguiendo el árbol
descrito en HOJA_DE_RUTA_AUTOMATIZACION_QA.md sección "Fase 2".
Genera conftest.py con fixtures para grabar video y trace en cada test,
y un pytest.ini con la configuración estándar.
```

**Entregable Fase 2:** proyecto navegable, primer test "smoke" que abre oneshop y verifica que carga.

---

### Fase 3 — Reporte QA automatizado a partir de la ejecución (2–3 horas)

**Objetivo:** Que después de correr `pytest`, se genere automáticamente un reporte Markdown listo para pegar en Monday.

**3.1** Crea `utils/report_builder.py` que tome el output de pytest + los videos/screenshots y genere un `.md` con el formato de tu plantilla actual (overview, tabla de casos, evidencia, ambientes).

**3.2** Hook de pytest en `conftest.py` que invoque el builder al final de la sesión.

**3.3** Slash command `/qa-report` ya no necesita que pegues nada — toma el último reporte generado.

**Entregable Fase 3:** después de `pytest`, tienes en `reports/` un Markdown listo para copiar/pegar en el update del ticket.

---

### Fase 4 — Integración con Monday API (3–4 horas)

**Objetivo:** Leer tickets y postear updates sin abrir el navegador.

**4.1** Obtén tu **API token** de Monday: avatar → Developers → My Access Tokens.
Guárdalo en `.env`:
```
MONDAY_API_TOKEN=tu_token_aqui
MONDAY_BOARD_ID=12345678
```

**4.2** Crea `utils/monday_client.py` con funciones:
- `list_tickets(status="QA in progress", assignee=ME)` → devuelve tickets asignados a ti en ese estado
- `get_ticket(ticket_id)` → descripción + updates + comentarios
- `post_update(ticket_id, markdown_text)` → publica reporte como update
- `change_status(ticket_id, new_status)` → mueve a QA passed / QA failed

Monday usa **GraphQL** — Claude Code te genera estas funciones a partir de la documentación oficial (https://developer.monday.com/api-reference/docs).

**4.3** Slash command `/qa-fetch <ticket_id>`:
```markdown
Lee el ticket $ARGUMENTS de Monday, extrae descripción + comentarios,
y úsalo como entrada para /qa-design.
```

**Entregable Fase 4:** desde Claude Code, `/qa-fetch 1234567890` te trae el ticket y dispara el diseño de casos automáticamente.

---

### Fase 5 — Orquestador end-to-end (4–6 horas)

**Objetivo:** Un solo comando que ejecute el flujo completo desde un ticket en `QA in progress`.

Slash command `/qa-run <ticket_id>`:
1. Lee el ticket de Monday (Fase 4)
2. Diseña casos de prueba (Fase 1)
3. Ejecuta los tests Playwright correspondientes (Fase 2)
4. Genera reporte (Fase 3)
5. Postea el reporte como update en el ticket (Fase 4)
6. Mueve el ticket a `QA passed` o `QA failed` según el resultado (Fase 4)

**Importante:** este comando arranca desde `QA in progress` (que tú moviste manualmente). Nunca toca tickets en `QA ready`.

**Entregable Fase 5:** flujo completo automatizado. Tú tomas el ticket, mueves a `QA in progress`, corres `/qa-run`, revisas el resultado.

---

### Fase 6 — API testing (futuro)

Cuando llegues aquí, añadimos:
- `tests/api/` con pytest + `playwright.request` o `httpx`
- Schemas validados con `pydantic`
- Slash command `/qa-api <endpoint>` que genera tests a partir de un OpenAPI/Swagger

---

## 4. Cómo Cursor y Claude Code se complementan

| Tarea | Mejor en | Por qué |
|---|---|---|
| Escribir un test nuevo desde cero | **Claude Code** | Lee múltiples archivos, sigue convenciones del proyecto |
| Refactorizar un selector que cambió | **Cursor** | Edits inline en el archivo abierto |
| Generar Page Object a partir de HTML | **Claude Code** | Multi-archivo: PO + test + data |
| Autocompletar mientras escribes | **Cursor** | Tab-tab inline |
| Correr `/qa-run` end-to-end | **Claude Code** | Agente con permisos de ejecutar comandos |
| Revisar diff antes de commit | **Cursor** | Vista Git nativa |

Regla práctica: **Cursor para escribir, Claude Code para orquestar.**

---

## 5. Orden recomendado de ejecución

1. **Hoy / esta semana:** Fase 0 + Fase 1 (setup + slash commands). Ya con esto ahorras 30–40% del tiempo de diseño de casos y reportes.
2. **Semana 2:** Fase 2 (estructura Playwright + primer smoke test).
3. **Semana 3:** Fase 3 (reporte automático tras ejecución).
4. **Semana 4:** Fase 4 (integración Monday API).
5. **Semana 5:** Fase 5 (orquestador completo `/qa-run`).
6. **Mes 2+:** Fase 6 (APIs).

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Cambios de UI rompen tests | Usar `data-testid` cuando sea posible; pedir al frontend que los agregue |
| Token de Monday expuesto | Siempre `.env` + `.gitignore`; nunca commitear |
| Tests flakeantes | `expect().to_be_visible()` con auto-wait de Playwright; evitar `time.sleep` |
| Videos pesando mucho | Configurar `video="retain-on-failure"` en `conftest.py` |
| Pérdida de control humano | Mantener gate manual en `QA ready → QA in progress` (ya decidido) |

---

## 7. Siguiente paso concreto

Cuando estés listo, dime "**arranquemos Fase 0**" y juntos:
1. Verificamos que tengas Node, Python y Cursor instalados.
2. Inicializamos el repo en esta carpeta.
3. Creamos `CLAUDE.md` con tu contexto real.
4. Probamos el primer slash command con un ticket real de Monday (puedes pegarme el texto y validamos el output).
