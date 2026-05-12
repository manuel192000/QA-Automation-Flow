# Proyecto: QA Automation — Enterprise 2026

Este archivo es leído automáticamente por Claude Code cada vez que se inicia
en esta carpeta. Define el contexto, convenciones y comandos del proyecto.

---

## Contexto del proyecto

- **Rol:** QA manual automatizando su flujo de trabajo.
- **Producto bajo prueba:** oneshop (web frontend).
  - **Ambiente staging:** `https://oneshopqa.com.dev.nmg-platform.com/`
- **Gestor de incidencias:** monday.com, board "Enterprise 2026".
- **Estados de ticket QA:**
  `QA ready` → `QA in progress` → `QA passed` / `QA failed`
- **Decisión humana (NO automatizar):** el paso de `QA ready` → `QA in progress`
  lo hace el QA manualmente al tomar el caso. El orquestador automatizado
  solo procesa tickets ya en `QA in progress`.

---

## Stack técnico

- Python 3.11+
- Playwright + pytest-playwright
- pytest, pytest-html, python-dotenv, requests
- Monday GraphQL API v2

---

## Convenciones del proyecto

- **Tests:** en `tests/`, organizados por carpeta funcional (`smoke/`, `regression/`).
- **Page Objects:** en `pages/`, una clase por página.
- **Datos de prueba:** en `data/` (JSON/YAML).
- **Utilidades:** en `utils/` (cliente Monday, generador de reportes, etc.).
- **Reportes:** se generan en `reports/`.
- **Videos y traces:** en `videos/` y `traces/` (gitignored).

### Estilo de código
- Nombres de funciones y archivos en **inglés** (`test_login_with_valid_user`).
- Docstrings y comentarios en **español**.
- Cada test arranca con un docstring que incluye: ID Monday, descripción, precondiciones.
- Usar locators de Playwright (`page.get_by_role`, `page.get_by_test_id`).
  **Evitar XPath y selectores frágiles.**
- Nunca usar `time.sleep`. Usar `expect()` con auto-wait de Playwright.

### Estilo de tests
```python
def test_login_with_valid_credentials(page):
    """
    Monday: 1234567890
    Verifica que un usuario válido puede iniciar sesión.
    Precondiciones: usuario existe en BD de staging.
    """
    page.goto("/login")
    page.get_by_label("Email").fill("qa@oneshop.com")
    page.get_by_label("Password").fill("Test123!")
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
```

---

## Comandos comunes

| Comando | Qué hace |
|---|---|
| `pytest` | Corre todos los tests (headless) |
| `pytest --headed` | Corre con navegador visible |
| `pytest -m smoke` | Solo tests marcados como smoke |
| `pytest tests/smoke/test_homepage_smoke.py` | Test específico |
| `pytest --html=reports/last.html --self-contained-html` | Reporte HTML |
| `playwright codegen oneshopqa.com.dev.nmg-platform.com` | Generador de código (graba acciones manuales) |

---

## Slash commands disponibles

Definidos en `.claude/commands/`:

- `/qa-design` — Diseña casos de prueba a partir del texto de un ticket de Monday.
- `/qa-report` — Genera reporte QA (positivo o negativo) listo para pegar como update en Monday.

## Flujo del equipo

Manual: el QA toma el ticket, diseña casos, graba selectores con
`playwright codegen`, escribe el test, lo corre con `pytest`, y pega el
reporte generado en Monday. **No hay auto-trigger desde Monday** — esa
opción existe pero está archivada en `experimental/webhook/`.

---

## Variables de entorno (`.env`)

```
MONDAY_API_TOKEN=...
MONDAY_BOARD_ID=...
BASE_URL=https://oneshopqa.com.dev.nmg-platform.com/
TEST_USER_EMAIL=...
TEST_USER_PASSWORD=...
```

`.env` está gitignored. Para nuevos colaboradores, copiar `.env.example` y rellenar.

---

## Reglas para Claude Code en este proyecto

1. **Nunca commitear** `.env` o credenciales.
2. **Antes de escribir un test nuevo**, revisar si ya hay un Page Object reutilizable en `pages/`.
3. **Antes de inventar un locator**, sugerirle al usuario que añada `data-testid` al frontend si el elemento no es accesible.
4. **Todos los tests** deben ser ejecutables individualmente (sin depender de estado de tests previos).
5. **Idioma:** responder en español a Manuel; comentarios en español, código en inglés.
