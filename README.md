# Arrakis

Implementación inicial de **Ω JARBIS**, plataforma de inteligencia ejecutiva operativa con enfoque conversacional.

## Componentes incluidos

- **API FastAPI** para ingestar eventos operativos por tenant.
- **Motor mimético** (`MimeticEngine`) como núcleo auditado:
  - normaliza eventos,
  - crea entidades dinámicas,
  - mantiene el digital twin,
  - expone trazabilidad completa de auditoría.
- **Motor de decisiones** para recomendaciones de reabastecimiento/anomalías.
- **Panel de configuración** web (`/config`) para ajustar parámetros críticos por tenant.

## Ejecutar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir:

- API docs: `http://127.0.0.1:8000/docs`
- Panel de configuración: `http://127.0.0.1:8000/config`

## Pruebas

```bash
python -m pytest -q
```

## Documentación

- [Ω JARBIS — Documento técnico de arquitectura y producto](docs/omega-jarbis-arquitectura-producto.md)
