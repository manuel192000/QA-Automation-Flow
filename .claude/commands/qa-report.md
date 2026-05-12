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
