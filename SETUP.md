# Setup desde cero — QA Automation Flow

Guía paso a paso para clonar y dejar funcionando este repositorio en una máquina nueva.
Pensada para QAs de cualquier nivel: si seguís los pasos en orden, en ~30 min tenés todo corriendo.

---

## 1. Pre-requisitos por sistema operativo

### macOS

```bash
# Homebrew (gestor de paquetes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Herramientas base
brew install node python@3.12 git
```

### Windows

1. Instala [Node.js LTS](https://nodejs.org/en/download).
2. Instala [Python 3.12](https://www.python.org/downloads/) — marca **"Add Python to PATH"** en el instalador.
3. Instala [Git for Windows](https://git-scm.com/download/win).

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm git
```

---

## 2. Editor y agente IA

### Cursor

Descárgalo de https://cursor.com e instala como cualquier app.

### Claude Code (CLI)

```bash
npm install -g @anthropic-ai/claude-code --foreground-scripts
claude --version
claude login
```

> Si la instalación falla con `Cannot find module 'install.cjs'`, reinstala con
> `--foreground-scripts` (como arriba) o usa el instalador nativo:
> `curl -fsSL https://claude.ai/install.sh | bash`.

Necesitarás una cuenta de Anthropic con plan que incluya Claude Code (Pro o Max).

---

## 3. Clonar el proyecto

```bash
git clone <URL-del-repositorio> "QA Automation Flow"
cd "QA Automation Flow"
```

---

## 4. Entorno Python (venv)

### macOS / Linux

```bash
# En macOS, "python3" del sistema suele ser 3.9 (de Apple). Usar SIEMPRE python3.12.
python3.12 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Tu prompt debe verse así (fíjate en el `(.venv)`):

```
(.venv) user@MacBook-Pro-de-User QA Automation Flow %
```

> **Regla de oro:** cada vez que abras una terminal nueva en este proyecto, activa el venv antes
> de correr cualquier `pip`, `pytest`, `playwright` o `python`.

---

## 5. Instalar dependencias y navegadores

```bash
pip install -r requirements.txt
playwright install chromium firefox webkit
```

`playwright install` baja ~500MB. Si solo querés Chromium para empezar:

```bash
playwright install chromium
```

---

## 6. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y rellena:

| Variable | Cómo obtenerla |
|---|---|
| `BASE_URL` | URL del ambiente. Por defecto el staging del proyecto. |
| `MONDAY_API_TOKEN` | En Monday → avatar (esquina superior derecha) → **Developers** → **My Access Tokens** → generar. |
| `MONDAY_BOARD_ID` | Abre el board "Enterprise 2026" y mira la URL: `https://....monday.com/boards/<ID>`. |
| `TEST_USER_EMAIL` / `TEST_USER_PASSWORD` | Credenciales del usuario de QA en staging. |

`.env` está en `.gitignore`. **Nunca lo subas al repo.**

---

## 7. Verificar acceso al staging

Antes de correr tests, confirma que el staging responde desde tu red:

```bash
curl -I https://oneshopqa.com.dev.nmg-platform.com
```

Debe responder `HTTP/2 200`. Si responde `403` o no responde, hablalo con el
admin del ambiente — puede haber restricciones de red corporativa.

---

## 8. Correr el primer test

```bash
pytest tests/smoke/ --headed
```

Resultado esperado:

```
tests/smoke/test_homepage_smoke.py::test_homepage_loads[chromium] PASSED
tests/smoke/test_homepage_smoke.py::test_homepage_has_no_console_errors[chromium] PASSED
================================================== 2 passed in X.Xs ==================================================
```

Después de cada corrida:
- **Videos** de cada test → carpeta `videos/`
- **Traces** Playwright → carpeta `traces/`. Inspecciona uno con:
  ```bash
  playwright show-trace traces/test_homepage_loads.zip
  ```

---

## 9. Slash commands en Claude Code

Verifica que existan dos archivos:

```
.claude/commands/qa-design.md
.claude/commands/qa-report.md
```

Si **no** existen, dentro del proyecto corre `claude` y pégale:

```
crea .claude/commands/qa-design.md y .claude/commands/qa-report.md
con el contenido de Fase 1 del roadmap (si tenés copia local de
`HOJA_DE_RUTA_AUTOMATIZACION_QA.md`) o siguiendo `CLAUDE.md` y los archivos en
`.claude/commands/`.
```

Después usalos así (dentro de Claude Code):

```
/qa-design

[pega aquí el texto descripción + comentarios de un ticket de Monday]
```

```
/qa-report

[pega aquí los datos del run: ticket, casos ejecutados, ambiente, navegador, evidencia]
```

---

## 10. Comandos del día a día

| Comando | Qué hace |
|---|---|
| `source .venv/bin/activate` | Activa el venv (cada terminal nueva). |
| `pytest` | Todos los tests, headless. |
| `pytest --headed` | Con navegador visible. |
| `pytest -m smoke` | Solo tests marcados como smoke. |
| `pytest tests/smoke/test_homepage_smoke.py` | Un archivo específico. |
| `pytest -k login` | Filtra por nombre de test. |
| `pytest --html=reports/last.html --self-contained-html` | Genera reporte HTML. |
| `playwright codegen <url>` | Grabador: hace clics y te genera el código Python. |
| `playwright show-trace traces/<archivo>.zip` | Abre un trace paso a paso. |
| `claude` | Arranca Claude Code en la carpeta. |

### Variables de entorno útiles al correr `pytest`

| Variable | Valores | Efecto |
|---|---|---|
| `RECORD_VIDEO` | `always` (default) / `retain-on-failure` / `off` | Modo de grabación de video. `always` graba todo (mejor para evidencia local). `retain-on-failure` graba todo pero borra los videos de los tests que pasaron (mejor para CI/disco). `off` no graba (más rápido). |
| `KEEP_EVIDENCE` | `1` para activar | Conserva `videos/` y `traces/` de la corrida anterior. Por defecto se limpia al inicio. |

Ejemplos:

```bash
# Local (default): graba siempre, limpia al inicio
pytest --headed

# CI / pre-release: solo conserva evidencia de fallos
RECORD_VIDEO=retain-on-failure pytest

# Debug rápido sin video (más veloz)
RECORD_VIDEO=off pytest -m smoke
```

---

## 11. Troubleshooting (errores reales que vivimos)

### `error: externally-managed-environment` al hacer `pip install`
**Causa:** el venv no está activado o se creó con el Python del sistema.
**Fix:**
```bash
rm -rf .venv
python3.12 -m venv .venv     # usa python3.12, NO python3
source .venv/bin/activate
which python                  # debe apuntar dentro de .venv
pip install -r requirements.txt
```

### `command not found: python3.12`
**macOS:** `brew install python@3.12` y verifica con `which python3.12`.
**Linux:** `sudo apt install python3.12 python3.12-venv`.
**Windows:** reinstala desde python.org marcando "Add to PATH".

### `command not found: pytest` o `playwright`
**Causa:** olvidaste activar el venv. Ejecuta `source .venv/bin/activate` y revisa que veas `(.venv)` en el prompt.

### `Error: claude native binary not installed`
Reinstala el CLI:
```bash
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code --foreground-scripts
```
O usa el instalador nativo: `curl -fsSL https://claude.ai/install.sh | bash`.

### `net::ERR_CERT_COMMON_NAME_INVALID` al navegar
El staging tiene cert mismatch. Ya está cubierto: `conftest.py` pasa `ignore_https_errors=True` al contexto Playwright.

### El health-check aborta con "❌ devolvió 403"
Tu IP no está autorizada por el staging. Verifica con `curl -I <BASE_URL>` que devuelva 200; si da 403, contactá al admin del ambiente.

### `TargetClosedError` durante un test
Cerraste manualmente la ventana del navegador antes de que el test termine. Déjala correr.

### Las ventanas de Chromium ni se abren
El health-check abortó antes. Mira la salida — te dice exactamente por qué (típicamente, el staging no respondió 200).

### `Cannot find module 'install.cjs'` al instalar Claude Code CLI
Node 26+ con npm a veces no corre el postinstall del paquete. Reinstala con `--foreground-scripts`:
```bash
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code --foreground-scripts
```
Si sigue fallando, usá el instalador nativo: `curl -fsSL https://claude.ai/install.sh | bash`.

### `to_have_url(lambda...)` → "value must be a string or regular expression"
Playwright Python no acepta lambdas en `to_have_url`. Cambialo a `re.compile(r"...")`.

### Monday devuelve `Cannot query field "url" on type "Webhook"`
El tipo `Webhook` de Monday no expone la URL vía API. Pedile solo `id` y `event`.

### Monday devuelve `Internal Server Error` al crear webhook
Generalmente es porque el server local no respondió al handshake. Verificá:
1. `python -m utils.qa_runner` esté corriendo → `curl http://localhost:8765/health` debe devolver `{"status":"ok"}`.
2. `cloudflared` esté corriendo → `curl <tu-tunnel>/health` también debe devolver `{"status":"ok"}`.
3. Si ves `502 Bad Gateway`, el tunnel está vivo pero el server flask no.

### Monday `"This status label doesn't exist, possible statuses are: ..."`
Los labels son **case-sensitive**. Los del board OS Enterprise Sprints 2026 son
`QA Passed` y `QA Failed` (P y F mayúsculas). Confirmá tu `.env`:
```bash
grep MONDAY_QA .env
```
Si no aparecen las dos líneas o están en minúsculas, agregalas / corregilas:
```bash
echo "MONDAY_QA_PASSED_LABEL=QA Passed" >> .env
echo "MONDAY_QA_FAILED_LABEL=QA Failed" >> .env
```

### `403 Forbidden` desde Python pero `curl` pasa con 200
El WAF del staging bloquea User-Agents de bot. `requests` por defecto envía
`python-requests/2.x` (bloqueado), curl envía `curl/8.x` (permitido).
Ya cubierto en `conftest.py` — el health-check pasa un User-Agent de Chrome real.

### El test `predictive_search` falla por `to_be_visible` en `brands_section()`
El label "BRANDS" no es un heading HTML — es texto plano. El locator usa
`get_by_text(re.compile(r"^brands$", re.IGNORECASE))` para encontrarlo.

### Solo se ve 1 fila en el reporte para un test con 3 asserts
Agregale al docstring un bloque `Checks:` listando cada validación. El report
builder lo expande en N filas (una por check):
```python
"""
Monday: ...
Title: ...
Feature Area: ...
Validation Type: ...
Checks:
  - AMANA brand appears in results
  - AMANA brand is inside Brands section
  - AMANA brand is rendered as pill
"""
```

---

## 12. Estructura del proyecto

```
QA Automation Flow/
├── CLAUDE.md                          # Contexto que Claude Code lee automáticamente
├── SETUP.md                           # Este archivo
├── README.md                          # Guía corta
├── .claude/commands/                  # Slash commands personalizados
│   ├── qa-design.md
│   └── qa-report.md
├── .env.example                       # Plantilla de variables
├── requirements.txt                   # Dependencias Python
├── pytest.ini                         # Config pytest
├── conftest.py                        # Fixtures globales + health-check
├── pages/                             # Page Objects
│   ├── base_page.py
│   └── home_page.py
├── tests/                             # Tests pytest
│   └── smoke/
│       └── test_homepage_smoke.py
├── utils/                             # Helpers (Monday client, report builder, ...)
├── data/                              # Datos de prueba
├── reports/                           # Reportes generados (gitignored)
├── videos/                            # Videos de Playwright (gitignored)
└── traces/                            # Traces de Playwright (gitignored)
```

---

## 13. Integración opcional con Monday API

> **Estado:** opcional. El flujo del día a día es manual (vos pegás el reporte
> y movés el estado a `QA Passed`/`QA Failed`). Si querés automatizar el
> posteo, el cliente está disponible y documentado abajo.

### Integración con Monday — Fase 4 (manual + cliente disponible)

El proyecto puede leer tickets, postear el reporte como update y cambiar el estado
automáticamente al terminar `pytest`. Para usarlo:

### 13.1 Token y board

En `.env`:

```
MONDAY_API_TOKEN=<tu_token>          # Avatar → Developers → My Access Tokens
MONDAY_BOARD_ID=18395174855          # OS Enterprise Sprints 2026
MONDAY_STATUS_COLUMN_ID=status
MONDAY_QA_PASSED_LABEL=QA Passed
MONDAY_QA_FAILED_LABEL=QA Failed
MONDAY_POST_ENABLED=1                # 0 = solo reporte local; 1 = además postea
```

### 13.2 Validar conexión

```bash
# Confirmar token y ver tu user_id
python -c "from utils import monday_client; print(monday_client.get_me())"

# Leer un ticket
python -c "from utils import monday_client; print(monday_client.get_item('11916681731')['name'])"
```

### 13.3 Convención obligatoria en tests

Cada test que deba postear a Monday tiene que declarar el ticket en su docstring:

```python
def test_xxx(page):
    """
    Monday: https://retailerwebservices.monday.com/boards/.../pulses/<id>
    Title: <título corto del reporte>
    Feature Area: <área del producto>
    Validation Type: <tipo: UI Regression, Functional, etc.>
    Checks:
      - <validación 1>
      - <validación 2>
    """
    ...
```

El report builder y el publisher leen esto para:
- Saber a qué ticket postear (campo `Monday:`).
- Pintar el título y la metadata del reporte.
- Expandir la tabla "Test Cases Summary" con un check por fila.

### 13.4 Cómo funciona hoy

Al final de cada `pytest`, `conftest.py`:
1. Renombra los videos a `<nombre_test>_<timestamp>.webm` (descriptivos).
2. Convierte los `.webm` a `.mp4` con `ffmpeg` (si está instalado).
3. Llama a `report_builder.write_report()` → genera `reports/qa_PASS_*.md`
   o `qa_FAIL_*.md`.

A partir de ahí, vos copiás el reporte y lo pegás como update en Monday.

> **Auto-posteo a Monday (archivado):** el flujo que hacía esto en automático
> al cambiar columnas en Monday vive en `experimental/webhook/` con su propio
> README. No está en el flujo principal del equipo; si en el futuro se decide
> reactivar, hay instrucciones para hacerlo.

---

## 14. Webhook auto-trigger — archivado en `experimental/webhook/`

> **Estado:** desactivado. La integración existe en `experimental/webhook/`
> y se documentó completa pero el equipo eligió mantener la ejecución manual
> de pytest para no perder control humano. Esta sección queda como referencia
> histórica por si en el futuro se decide reactivar.

El proyecto incluye un servidor que escucha webhooks de Monday y dispara tests
automáticamente cuando un ticket te es asignado en `QA In Progress`.

### 14.1 Cómo funciona

```
Monday (cualquier cambio en el board)
   ↓ webhook
QA Runner (utils/qa_runner.py)
   ↓ valida: yo en QA/Rel  +  status "QA In Progress"
   ↓ busca tests con `Monday: <ticket_id>` en docstring
   ↓ ejecuta pytest <esos archivos>
conftest → reporte → Monday update + cambio de estado
```

El **gate manual** se mantiene: vos mismo movés el status de `QA Ready` →
`QA In Progress` cuando tomás el ticket. Sin ese cambio, el runner descarta el evento.

### 14.2 Configuración en `.env`

```
MONDAY_QA_REL_COLUMN_ID=multiple_person_mkxkt529   # columna QA/Rel del board
MONDAY_MY_USER_ID=58862089                         # tu id (autodetectable)
MONDAY_QA_TRIGGER_LABEL=QA In Progress             # label que dispara
QA_RUNNER_PORT=8765
```

### 14.3 Las 3 terminales

Para el flujo webhook se necesitan **3 terminales abiertas en simultáneo**,
todas con `(.venv)` activo. Si cerrás una, el flujo se cae.

**Terminal 1 — server flask:**
```bash
cd "/Users/user/Documents/Claude/Projects/QA Automation Flow"
source .venv/bin/activate
python -m utils.qa_runner
```

**Terminal 2 — cloudflared tunnel (URL pública para Monday):**
```bash
cloudflared tunnel --url http://localhost:8765
```
Anotá la URL que imprime (tipo `https://random-words.trycloudflare.com`).

**Terminal 3 — registrar webhook (solo una vez por sesión):**
```bash
cd "/Users/user/Documents/Claude/Projects/QA Automation Flow"
source .venv/bin/activate
WEBHOOK_URL=https://random-words.trycloudflare.com/webhook \
    python -m utils.register_webhook
```
Cuando termine podés cerrar **solo la 3 (no la 1 ni la 2)**.

### 14.4 Limitación del tunnel gratuito

`trycloudflare.com` da URLs **efímeras** — cuando reiniciás cloudflared,
la URL cambia y tenés que re-correr `register_webhook` con la URL nueva.

Para algo permanente: registrar un tunnel con cuenta de Cloudflare y dominio
propio, o usar [ngrok](https://ngrok.com) con plan de pago.

### 14.5 Probar el flujo end-to-end

1. Asegurate de que las 3 terminales hayan corrido sin errores.
2. Andá al ticket de predictive search en Monday.
3. Confirmá: tu avatar en `QA/Rel` + status en `QA In Progress`.
4. Cambiá cualquier cosa chiquita (otra columna, descripción).
5. Mirá la terminal 1: deberías ver
   ```
   🔔 Webhook received for item <id>
   ▶️  Tests for ticket <id>: [...]
   🚀 Running: ...
   📝 Reporte QA generado: reports/qa_PASS_...md
   📤 Monday: update posteado en ticket(s) <id>
   ```
6. En Monday: reporte como update + estado movido a `QA Passed`.

---

## 15. Próximos hitos del proyecto

Resumen (el roadmap por fases puede estar solo en copia local, fuera del repo):

- **Fase 6:** API testing (pytest + `httpx` o `playwright.request`).
- **Cobertura:** seguir agregando tests al directorio `tests/regression/` siguiendo
  el patrón de `test_predictive_search.py`. Cada nuevo test que tenga `Monday: <id>`
  en su docstring queda automáticamente conectado al flujo del webhook.
- **Producción del webhook:** mover de `trycloudflare.com` a un tunnel con
  dominio fijo (Cloudflare named tunnel o ngrok pago) para que la URL no cambie.
