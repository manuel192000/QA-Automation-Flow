# QUICKSTART — Daily workflow

Lo mínimo que necesitás para arrancar a trabajar cada día.
Si necesitás instalar todo desde cero (máquina nueva, primera vez), mirá
primero `SETUP.md`.

> El flujo actual del equipo es **manual**: vos corrés pytest cuando
> querés. El integrador automático Monday ↔ pytest (webhook) está
> archivado en `experimental/webhook/` por si en el futuro se decide
> reactivar.

---

## 1. Pre-flight (30 segundos)

```bash
cd "/Users/user/Documents/Claude/Projects/QA Automation Flow"
source .venv/bin/activate
```

Vas a ver `(.venv)` al inicio del prompt. Sanity check del staging:

```bash
curl -I https://oneshopqa.com.dev.nmg-platform.com
```

Debe responder `HTTP/2 200`. Si responde `403` o no responde, hablalo
con el admin del ambiente antes de seguir.

---

## 2. Trabajar en un ticket nuevo

1. **Leé el ticket** en Monday y copiá descripción + DOD.
2. **Diseñá los casos** abriendo Claude Code (`claude` en terminal) y
   pegando:
   ```
   /qa-design

   <descripción y DOD del ticket>
   ```
3. **Grabá los selectores** con codegen:
   ```bash
   playwright codegen --ignore-https-errors https://oneshopqa.com.dev.nmg-platform.com/
   ```
   Hacé las acciones manuales en el browser que se abre. El panel
   "Inspector" del costado te va escribiendo el código Python.
4. **Pedile a Claude Code** que arme el test:
   ```
   Crea un test en tests/regression/test_<feature>.py para el ticket
   <URL-MONDAY>. Selectores grabados con codegen:

   <pegá el código del Inspector>

   Seguí el patrón de tests/regression/test_predictive_search.py.
   ```
5. **Corré el test** local:
   ```bash
   pytest tests/regression/test_<feature>.py --headed
   ```
6. **Pegá el reporte en Monday.** El archivo está en
   `reports/qa_PASS_<timestamp>.md` o `qa_FAIL_<timestamp>.md`. Copialo
   y pegalo como update del ticket. Mové el status a `QA Passed` /
   `QA Failed`.

---

## 3. Re-correr la suite (cualquier momento)

```bash
pytest                              # toda la suite
pytest -m smoke                     # solo smoke
pytest tests/regression/            # solo regresión
pytest -k predictive --headed       # filtro por nombre, navegador visible
```

---

## 4. Verificaciones rápidas si algo no anda

| Síntoma | Verificación | Fix |
|---|---|---|
| Pytest dice `403 Forbidden` o `TargetClosedError` | `curl -I <BASE_URL>` | Tu IP no está autorizada por el staging. Hablalo con el admin del ambiente. |
| Videos no se reproducen en Monday | `which ffmpeg` | `brew install ffmpeg` para que los .webm se conviertan a .mp4. |
| Reporte se ve sin formato | que `markdown` esté instalado | `pip install markdown` |
| `command not found: pytest / playwright` | venv no activo | `source .venv/bin/activate` (debes ver `(.venv)` en prompt) |
| Video con nombre random tipo `page@abc.webm` | sesión interrumpida antes de `pytest_sessionfinish` | El renombrado descriptivo solo ocurre al final de un run completo. Re-corré el test entero. |

---

## 5. Datos técnicos para la demo / preguntas del lead

### ¿Qué hace el proyecto?

Toma el flujo manual de QA en `oneshop` (revisión de tickets, ejecución
de pruebas, reporte, cambio de estado) y lo encadena al cambio de estado
en Monday. El QA mantiene el control humano: tomar el ticket (avatar en
QA/Rel) y moverlo a `QA In Progress` son acciones manuales. A partir de
ahí, el resto corre solo: ejecución de pruebas en navegador real, captura
de evidencia (video + trace), generación del reporte y posteo como update
en el ticket con cambio de estado a `QA Passed` o `QA Failed`.

### Stack

| Capa | Herramienta | Por qué |
|---|---|---|
| Lenguaje | Python 3.12 | Sintaxis cercana a inglés; estándar en QA |
| Test framework | pytest + pytest-playwright | Estándar de la industria |
| Browser automation | Playwright (Chromium) | Auto-wait, video, trace, locators por accesibilidad |
| Reportes | Markdown → HTML | Markdown para lectura local, HTML para Monday |
| Integración Monday | GraphQL API v2 + webhooks | API oficial; webhook para trigger |
| Server local | Flask | Liviano, una sola dependencia |
| Tunnel | cloudflared | Gratuito, sin cuenta; URL pública para Monday |
| Editor / IA | Cursor + Claude Code (CLI) | Generación, edición e iteración de tests |

### Decisiones de diseño que vale defender

1. **Gate manual mantenido.** El QA decide qué tickets se ejecutan (con
   QA/Rel + status). Esto evita ejecuciones no deseadas y mantiene
   trazabilidad humana.
2. **Locators por rol de accesibilidad** (`get_by_role`, `get_by_test_id`).
   Más robustos a cambios visuales y a refactors de HTML que los XPath.
3. **Page Object Model**. Cada componente UI (modal de búsqueda, home,
   etc.) vive en `pages/`. Si un selector cambia, se arregla en un solo
   archivo y todos los tests siguen funcionando.
4. **Video + trace siempre**. Cualquier fallo es reproducible con la
   evidencia capturada. Modo `retain-on-failure` disponible para CI.
5. **Acoplamiento mínimo con Monday**. La metadata del ticket vive en el
   docstring del test (`Monday: <URL>`). No hay base de datos ni mapeos
   externos para mantener.
6. **Webhook + tunnel local**, no servidor en la nube. Costo cero,
   privacidad alta, deployable en cualquier laptop. Limitación: la URL
   cambia con cada reinicio del tunnel.

### Cobertura actual

- `tests/smoke/test_homepage_smoke.py` — humo del home.
- `tests/regression/test_predictive_search.py` — featured brands as pills
  en el modal de búsqueda (ticket NGSCH Follow-Up).

Para agregar nuevos tests basta con copiar el patrón del docstring y
declarar el `Monday: <URL>` correspondiente.

### Métricas / tiempos típicos

- Smoke (1–2 tests): ~10 segundos.
- Regression test individual: ~5–15 segundos según el flujo.
- Webhook → fin de pytest → posteo a Monday: ~30 segundos.

### Seguridad / secrets

- `.env` está en `.gitignore` — nunca se commitea.
- Variables sensibles: `MONDAY_API_TOKEN`, `TEST_USER_PASSWORD`.
- El webhook es un endpoint público mientras corre el tunnel. Opcional:
  `MONDAY_WEBHOOK_SECRET` para validar firma (no activado por defecto).
- El staging tiene cert mismatch; `ignore_https_errors` está activado
  intencionalmente solo para Playwright y `requests` en el health-check.

### Limitaciones conocidas / próximos pasos

- **URL del tunnel cambia** con cada reinicio. Mover a Cloudflare named
  tunnel (gratis, requiere dominio) elimina ese paso manual.
- **No hay test data automatizada**. Los datos semilla (usuarios, marcas
  featured) deben existir antes de correr los tests.
- **Un solo navegador (Chromium)**. Multi-browser estaría a 1 flag de
  pytest-playwright; pendiente decidir si vale.
- **Fase 6 (API testing)** está documentada en la hoja de ruta pero no
  implementada todavía.
