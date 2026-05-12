"""
conftest.py — Fixtures globales para todos los tests.

pytest descubre este archivo automáticamente y aplica las fixtures
a cualquier test del proyecto.
"""

import os
import warnings
from pathlib import Path
import pytest
import requests
import urllib3
from dotenv import load_dotenv

# Silenciar warning de cert no verificado durante el health-check.
# El verify=False es intencional para ambientes de staging con certs raros.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cargar variables del .env al iniciar la sesión de pytest
load_dotenv()

# Carpetas para evidencia (video, trace, screenshots)
PROJECT_ROOT = Path(__file__).parent
VIDEOS_DIR = PROJECT_ROOT / "videos"
TRACES_DIR = PROJECT_ROOT / "traces"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Crear carpetas si no existen
for d in (VIDEOS_DIR, TRACES_DIR, REPORTS_DIR):
    d.mkdir(exist_ok=True)


# === Modo de grabación de video ===
# Controlado por la variable de entorno RECORD_VIDEO:
#   - "always"             (default) — graba video de TODOS los tests
#   - "retain-on-failure"  — graba siempre, pero borra al final los videos de los tests que pasaron
#   - "off"                — no graba video (más rápido y ligero, sin evidencia)
RECORD_VIDEO = os.getenv("RECORD_VIDEO", "always").lower()


# === Configuración global de Playwright ===

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Configuración por defecto del contexto del navegador.
    Aplica a todos los tests automáticamente.
    """
    args = {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "base_url": os.getenv("BASE_URL", "https://oneshopqa.com.dev.nmg-platform.com/"),
        # Ignora errores SSL — útil en ambientes de QA/staging con
        # certificados auto-firmados o cert mismatch.
        "ignore_https_errors": True,
    }
    if RECORD_VIDEO in ("always", "retain-on-failure"):
        args["record_video_dir"] = str(VIDEOS_DIR)
        args["record_video_size"] = {"width": 1440, "height": 900}
    return args


def pytest_configure(config):
    """
    Verificación previa: alcanzabilidad de BASE_URL.
    Si el sitio no responde, aborta la sesión con un mensaje claro en vez
    de dejar que cada test reviente con TargetClosedError críptico.

    También limpia evidencia anterior (videos/ y traces/) para que cada
    corrida sea autocontenida. Si querés conservar histórico, exportá
    KEEP_EVIDENCE=1 antes de correr pytest.
    """
    if not os.getenv("KEEP_EVIDENCE"):
        import shutil
        for d in (VIDEOS_DIR, TRACES_DIR):
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(exist_ok=True)

    base_url = os.getenv("BASE_URL", "https://oneshopqa.com.dev.nmg-platform.com/")
    try:
        resp = requests.get(
            base_url,
            timeout=10,
            verify=False,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            },
        )
        if resp.status_code == 403:
            pytest.exit(
                f"\n❌ {base_url} devolvió 403.\n"
                "   Tu IP no está autorizada por el staging. Contactá al admin del ambiente.\n",
                returncode=2,
            )
    except requests.exceptions.RequestException as e:
        pytest.exit(
            f"\n❌ No se pudo alcanzar {base_url}: {e}\n"
            "   Verificá tu conexión a internet.\n",
            returncode=2,
        )


# ===== Reporte QA automático al finalizar la sesión =====

# Acumulador de resultados de los tests durante la sesión
_session_results: list[dict] = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura el resultado de cada fase (setup/call/teardown) del test."""
    outcome = yield
    rep = outcome.get_result()
    # Guardar el resultado por fase para que otras fixtures puedan consultarlo
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when == "call":  # solo la fase de ejecución del test, no setup/teardown
        # Parsear browser del nodeid: "test_x.py::test_y[chromium]" -> "chromium"
        browser = None
        if "[" in item.nodeid and "]" in item.nodeid:
            browser = item.nodeid.rsplit("[", 1)[1].rstrip("]")

        _session_results.append({
            "nodeid": item.nodeid,
            "name": item.name,
            "outcome": rep.outcome,
            "duration_s": rep.duration,
            "error": str(rep.longrepr) if rep.failed else None,
            "docstring": (item.function.__doc__ or "").strip(),
            "browser": browser,
            "file": str(item.path.relative_to(PROJECT_ROOT)) if item.path else None,
        })


def _convert_videos_to_mp4():
    """
    Convert any .webm videos in videos/ to .mp4 so Monday can play them
    inline. Requires `ffmpeg` on PATH (brew install ffmpeg). If ffmpeg is
    not present, we leave the .webm files alone.
    """
    import shutil
    import subprocess
    if not VIDEOS_DIR.exists():
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ℹ️  ffmpeg no encontrado — los videos quedan en .webm. Instalalo con `brew install ffmpeg` para convertirlos a .mp4.")
        return
    for webm in VIDEOS_DIR.rglob("*.webm"):
        mp4 = webm.with_suffix(".mp4")
        if mp4.exists() and mp4.stat().st_mtime >= webm.stat().st_mtime:
            continue  # already converted
        try:
            subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", str(webm),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                 str(mp4)],
                check=True,
            )
            webm.unlink(missing_ok=True)  # drop the .webm so reports list only the mp4
        except Exception as e:
            print(f"⚠️  No pude convertir {webm.name} a mp4: {e}")


def _rename_videos_by_test_order():
    """
    Playwright nombra los videos con un hash random (`page@abc123.webm`),
    lo cual no nos dice nada al revisar evidencia. Acá renombramos cada
    archivo a `<nombre_del_test>_YYYY-MM-DD_HH-MM.webm`, asociando videos
    a tests por orden temporal (que es el orden en que pytest los corrió).
    """
    from datetime import datetime
    if not VIDEOS_DIR.exists() or not _session_results:
        return
    videos = sorted(VIDEOS_DIR.rglob("*.webm"), key=lambda p: p.stat().st_mtime)
    test_names = [r["name"] for r in _session_results]
    if not videos or not test_names:
        return
    for i, video in enumerate(videos):
        name = test_names[i] if i < len(test_names) else f"video_{i+1}"
        ts = datetime.fromtimestamp(video.stat().st_mtime).strftime("%Y-%m-%d_%H-%M")
        new_path = video.parent / f"{name}_{ts}.webm"
        if new_path.exists():
            continue
        try:
            video.rename(new_path)
        except Exception:
            pass


def pytest_sessionfinish(session, exitstatus):
    """
    Al terminar la sesión: renombra videos descriptivamente, los convierte
    a mp4 y genera el reporte Markdown en `reports/`.
    El posteo automático a Monday quedó archivado en `experimental/webhook/`
    — el flujo actual es manual: tomás el reporte y lo pegás como update.
    """
    if not _session_results:
        return
    from utils.report_builder import write_report

    _rename_videos_by_test_order()
    _convert_videos_to_mp4()

    base_url = os.getenv("BASE_URL")
    out = write_report(_session_results, base_url=base_url)
    print(f"\n📝 Reporte QA generado: {out}")


@pytest.fixture(autouse=True)
def _trace_each_test(context, request):
    """
    Inicia un trace de Playwright al comenzar el test y lo guarda
    al terminar. Los traces se pueden abrir con `playwright show-trace`.

    Si RECORD_VIDEO=retain-on-failure y el test pasó, borra su video
    al final (el trace se conserva siempre, ocupa muy poco).
    """
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    # Capturamos la ruta del video del primer page (típicamente solo hay uno
    # por test). page.video.path() devuelve la ruta donde Playwright
    # escribirá el .webm al cerrar el contexto.
    video_paths: list[Path] = []

    yield

    # Antes de cerrar el contexto, capturamos las rutas de los videos creados
    if RECORD_VIDEO in ("always", "retain-on-failure"):
        for page in context.pages:
            if page.video:
                try:
                    video_paths.append(Path(page.video.path()))
                except Exception:
                    pass

    trace_path = TRACES_DIR / f"{request.node.name}.zip"
    context.tracing.stop(path=str(trace_path))

    # Política de retención: en modo retain-on-failure, si el test pasó,
    # borramos sus videos. Si falló o no hubo fase "call", los conservamos.
    if RECORD_VIDEO == "retain-on-failure":
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.passed:
            for vp in video_paths:
                try:
                    if vp.exists():
                        vp.unlink()
                except Exception:
                    pass
