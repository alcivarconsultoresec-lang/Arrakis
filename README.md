# Arrakis

Implementación **Ω JARBIS Next-Gen**: un plano de control cognitivo para operaciones empresariales.

## Qué incluye esta versión (2.1)

- Gateway de eventos con bus interno y DLQ en memoria para desacoplar ingestión/procesamiento.
- Motor mimético auditado con:
  - normalización semántica,
  - confianza por evento,
  - correlación/causalidad,
  - digital twin con estado actual + inferido + simulado.
- Motor de decisiones (descriptivo/diagnóstico/predictivo/prescriptivo).
- Motor de políticas para gobernanza de ejecución (`inform`, `suggest`, `approval`, `auto`, `auto_reversible`).
- Torre de control (`/control-tower`) para salud operativa y decisiones.
- Panel de configuración web para config + políticas + auditoría.
- Arranque rápido con Docker (`Dockerfile`, `docker-compose.yml`) y automatización de comandos con `Makefile`.

## Opción A — Ejecutar localmente (Python)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Opción B — Ejecutar con Docker

```bash
cp .env.example .env
docker compose up --build
```

Abrir:

- API docs: `http://127.0.0.1:8000/docs`
- Panel de configuración: `http://127.0.0.1:8000/config`

## Atajos con Makefile

```bash
make test
make lint
make docker-up
make docker-down
```

## Endpoints clave

- `POST /api/v1/tenants/{tenant_id}/events`
- `GET /api/v1/tenants/{tenant_id}/recommendations`
- `PUT /api/v1/tenants/{tenant_id}/config`
- `PUT /api/v1/tenants/{tenant_id}/policies`
- `GET /api/v1/tenants/{tenant_id}/control-tower`
- `POST /api/v1/tenants/{tenant_id}/simulate`
- `GET /api/v1/tenants/{tenant_id}/audit`

## Pruebas

```bash
python -m unittest discover -s tests -v
```

## Documentación

- [Ω JARBIS — Documento técnico de arquitectura y producto](docs/omega-jarbis-arquitectura-producto.md)
- [Manual Maestro de Implementación (desde cero a escalada)](docs/manual-implementacion-jarbis.md)
