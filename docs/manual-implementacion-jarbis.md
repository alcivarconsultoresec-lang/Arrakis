# Manual Maestro de Implementación de Ω JARBIS

> Guía paso a paso, pensada para personas **sin formación técnica**.
> 
> Objetivo: que puedas pasar de “no sé por dónde empezar” a “lo tengo funcionando, mantenido y escalando”.

---

## 0) Cómo usar este manual (muy importante)

Este documento está diseñado como una ruta de viaje.

- Si estás en **cero absoluto**, empieza en la **Fase 1** y sigue en orden.
- Si ya tienes algo andando, salta a la fase que necesites.
- Cada fase incluye:
  - Qué vas a lograr.
  - Qué necesitas antes de empezar.
  - Instrucciones numeradas.
  - “Checklist de éxito” para validar que vas bien.

### Regla de oro

No avances de fase si no puedes marcar todos los puntos del checklist.

---

## 1) Qué es Ω JARBIS en palabras simples

Ω JARBIS es un sistema que ayuda a una operación (restaurante, hotel, retail, etc.) a:

1. Recibir eventos (por ejemplo: “compré 10 kg de tomate”).
2. Entenderlos automáticamente.
3. Actualizar un “gemelo digital” del negocio.
4. Detectar riesgos.
5. Recomendar (o ejecutar) acciones según políticas.

Piensa en Ω JARBIS como una mezcla entre:

- un asistente operativo,
- un centro de control,
- y un sistema de decisiones gobernadas.

---

## 2) Qué incluye el proyecto actualmente

En este repositorio ya tienes una base funcional con:

- API en FastAPI.
- Motor Mimético (núcleo auditado).
- Motor de Decisiones.
- Motor de Políticas.
- Bus de eventos en memoria.
- Panel web de configuración y torre de control.
- Pruebas básicas.

---

## 3) Ruta completa de implementación (mapa general)

### Fase 1 — Preparación del entorno
Tener tu computadora lista.

### Fase 2 — Arranque local del sistema
Levantar API y panel web.

### Fase 3 — Primera operación real guiada
Enviar eventos y validar respuestas.

### Fase 4 — Configuración de políticas
Definir qué se informa, qué se sugiere y qué se automatiza.

### Fase 5 — Operación diaria
Usar Ω JARBIS como rutina de trabajo.

### Fase 6 — Mantenimiento
Prevenir fallos, hacer respaldos y validar calidad.

### Fase 7 — Escalado
Pasar de piloto a operación multi-tenant más robusta.

---



## 3.1 Ruta express (si quieres verlo funcionando en 5 minutos)

1. Copia variables de entorno:

```bash
cp .env.example .env
```

2. Levanta el sistema con Docker:

```bash
docker compose up --build
```

3. Abre:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/config`

Si esta ruta express funciona, luego continúa desde Fase 3 para operación guiada.


## 4) Fase 1: Preparación del entorno (desde cero)

## Objetivo
Tener todo instalado sin tocar código complejo.

## Necesitas

- Una computadora con internet.
- Terminal (Mac/Linux) o PowerShell (Windows).
- Permisos para instalar software.

## Paso a paso

1. Instala **Python 3.10+**.
2. Descarga o clona este repositorio.
3. Entra a la carpeta del proyecto.
4. Crea un entorno virtual.
5. Instala dependencias.

### Comandos sugeridos (Mac/Linux)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Comandos sugeridos (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Checklist de éxito

- [ ] Puedes activar el entorno virtual.
- [ ] `pip install -r requirements.txt` termina sin error.

---

## 5) Fase 2: Arranque local del sistema

## Objetivo
Ver Ω JARBIS funcionando en tu máquina.

## Paso a paso

1. Activa entorno virtual.
2. Levanta servidor.

```bash
uvicorn app.main:app --reload
```

3. Abre en navegador:
   - API docs: `http://127.0.0.1:8000/docs`
   - Panel: `http://127.0.0.1:8000/config`

## Checklist de éxito

- [ ] Ves “status ok” en `/health`.
- [ ] Se abre documentación de API.
- [ ] Se abre panel de configuración.

---

## 6) Fase 3: Primera operación guiada (sin perderte)

## Objetivo
Confirmar flujo end-to-end: evento → modelo → decisión.

## Caso demo

“Compré 10 unidades de tomate”.

## Opción A (fácil): desde la documentación `/docs`

1. Abre endpoint `POST /api/v1/tenants/{tenant_id}/events`.
2. Usa tenant: `demo-tenant`.
3. Envía este JSON:

```json
{
  "type": "purchase",
  "item": "tomate",
  "quantity": 10,
  "unit": "kg",
  "source": "chat",
  "note": "compra inicial"
}
```

4. Verifica respuesta: debe incluir `event`, `snapshot` y `decisions`.

## Opción B: desde terminal (copia y pega)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tenants/demo-tenant/events" \
  -H "Content-Type: application/json" \
  -d '{"type":"purchase","item":"tomate","quantity":10,"unit":"kg","source":"chat","note":"compra inicial"}'
```

## Checklist de éxito

- [ ] El evento se registra.
- [ ] El stock cambia en snapshot.
- [ ] Aparece una decisión/recomendación.

---

## 7) Fase 4: Configuración de políticas (gobernanza sencilla)

## Objetivo
Definir el nivel de autonomía del sistema.

### Modos de política (explicados fácil)

- `inform`: solo informa.
- `suggest`: sugiere y espera confirmación.
- `approval`: requiere aprobación formal.
- `auto`: ejecuta automáticamente.
- `auto_reversible`: ejecuta y permite reversión.

## Recomendación para empezar

Empieza con `suggest` en producción inicial.

## Paso a paso

1. Entra a `/config`.
2. En sección “Políticas y Gobernanza”:
   - Scope: `inventory_restock`.
   - Mode: `suggest`.
3. Guarda política.
4. Ejecuta un evento y revisa `/audit` y `/control-tower`.

## Checklist de éxito

- [ ] Política guardada.
- [ ] Las decisiones salen con `policy_mode` esperado.
- [ ] Ves trazabilidad en auditoría.

---

## 8) Fase 5: Operación diaria (runbook operativo)

Esta es la rutina recomendada para un operador no técnico.

## Inicio del día (10–15 min)

1. Revisar `/control-tower`.
2. Mirar riesgos críticos.
3. Revisar decisiones pendientes (`pending_confirmation`, `awaiting_approval`).

## Durante el día

1. Registrar eventos importantes (compras, mermas, ajustes).
2. Atender recomendaciones priorizadas.
3. Confirmar acciones tomadas para cerrar ciclo de decisión.

## Cierre del día

1. Revisar auditoría (`/audit`).
2. Confirmar que no hay incoherencias de stock.
3. Exportar/guardar resultados operativos del día.

---

## 9) Fase 6: Mantenimiento (sin drama)

## 9.1 Mantenimiento técnico básico (semanal)

1. Actualizar dependencias de manera controlada.
2. Ejecutar pruebas.
3. Revisar logs y errores recurrentes.

Comando de pruebas:

```bash
python -m unittest discover -s tests -v
```

## 9.2 Mantenimiento funcional (semanal)

1. Revisar políticas activas por tenant.
2. Ajustar umbrales (`low_stock_threshold`, `anomaly_spike_factor`).
3. Corregir entidades ambiguas detectadas en auditoría.

## 9.3 Mantenimiento de negocio (mensual)

1. Revisar KPIs de adopción.
2. Medir decisiones aceptadas vs rechazadas.
3. Ajustar estrategias por estacionalidad.

---

## 10) Fase 7: Escalada (de piloto a sistema serio)

Cuando ya funciona en piloto, sigue este orden para escalar de forma segura:

## Paso 1 — Multi-tenant real

- Separar datos por tenant con mayor robustez.
- Definir estándares de naming y onboarding.

## Paso 2 — Infraestructura

- Migrar de in-memory a base persistente (PostgreSQL + event store).
- Añadir cola/event bus productivo (Kafka, RabbitMQ o equivalente).

## Paso 3 — Observabilidad y seguridad

- Logs estructurados.
- Métricas por tenant.
- Alertas operativas.
- Gestión de secretos y rotación de credenciales.

## Paso 4 — Alta disponibilidad

- Despliegue en contenedores.
- Réplicas del servicio.
- Backups y plan de recuperación.

## Paso 5 — Verticalización

- Crear paquetes por industria (restaurante/hotel/retail).
- Definir ontologías y políticas por vertical.

---

## 11) Guía de errores comunes (y cómo salir rápido)

## Error 1: “No abre /docs ni /config”

Causa probable: servidor no levantado.

Solución:

- Ejecuta `uvicorn app.main:app --reload`.
- Verifica puerto 8000 libre.

## Error 2: “No cambia stock al enviar evento”

Causa probable: payload incompleto.

Solución:

- Incluye `item` y `quantity`.
- Revisa respuesta del endpoint.

## Error 3: “No veo decisiones”

Causa probable: configuración/política no definida.

Solución:

- Configura `low_stock_threshold`.
- Define política en `inventory_restock`.

## Error 4: “El sistema recomienda algo raro”

Causa probable: interpretación semántica con baja confianza.

Solución:

- Revisa `confidence_score` y `raw_payload` en auditoría.
- Estandariza el formato de entrada.

---

## 12) Plantilla de implementación para cliente real (copia y usa)

## Semana 1

- Instalación técnica.
- Pruebas internas.
- Configuración tenant demo.

## Semana 2

- Carga inicial de eventos reales.
- Ajuste de umbrales.
- Entrenamiento de usuarios operativos.

## Semana 3

- Activación de políticas en modo `suggest`.
- Rutina diaria con torre de control.
- Revisión de trazabilidad.

## Semana 4

- Ajustes finales.
- Evaluación de resultados.
- Plan de expansión a más sucursales/tenants.

---

## 13) Manual de roles (quién hace qué)

## Operador

- Registra eventos.
- Revisa recomendaciones.
- Ejecuta acciones operativas.

## Supervisor

- Aprueba decisiones críticas.
- Ajusta políticas.
- Revisa riesgos y control tower.

## Administrador técnico

- Mantiene infraestructura.
- Corre pruebas.
- Asegura seguridad, backups y disponibilidad.

## Dirección

- Define objetivos de negocio.
- Evalúa impacto económico.
- Decide expansión por vertical/tenant.

---

## 14) Criterios de “implementación exitosa”

Tu implementación está bien cuando:

- [ ] El equipo opera diariamente desde Ω JARBIS.
- [ ] Las decisiones quedan trazables en auditoría.
- [ ] Los riesgos se detectan antes de convertirse en crisis.
- [ ] Hay políticas claras de autonomía y aprobación.
- [ ] Existe rutina de mantenimiento y mejora continua.

---

## 15) Apéndice rápido de comandos

Activar entorno e instalar:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Levantar aplicación:

```bash
uvicorn app.main:app --reload
```

Pruebas:

```bash
python -m unittest discover -s tests -v
```

---

## Cierre

Si sigues este manual en orden, **una persona sin formación técnica puede implementar Ω JARBIS desde cero**, operarlo en el día a día, mantenerlo sin perder control y preparar una escalada sólida.

La clave no es correr más rápido, sino avanzar por fases con checklist y gobernanza.
