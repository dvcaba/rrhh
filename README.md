# RRHH - Smart Candidate Filtering POC

Proyecto de ejemplo para generación, parsing y ranking de CVs contra JDs con explicación y mini-assessment.

## Estructura

- `smart-filtering-poc/`: código principal, UI Streamlit, CLI y tests.
- `PLAN.md`: plan de trabajo.

## Cómo arrancar la app (local)

```bash
git clone git@github.com:dvcaba/rrhh.git
cd rrhh/smart-filtering-poc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m smart_filtering.generator.run_generation
python -m smart_filtering.generator.run_jd_generation
streamlit run app/ui_streamlit/app.py
```

Notas:
- Para entornos sin red o despliegues ligeros, exporta `SMART_FILTERING_EMBEDDER_MODE=offline` antes de lanzar Streamlit (usa embeddings cero y evita descargar el modelo).
- Los datos generados se guardan en `smart-filtering-poc/data/raw/` y se ignoran en git.

## Despliegue rápido (Streamlit Cloud)

1) Conecta el repo `dvcaba/rrhh` en https://share.streamlit.io.
2) App path: `smart-filtering-poc/app/ui_streamlit/app.py`.
3) Añade el secret/env `SMART_FILTERING_EMBEDDER_MODE=offline` si no quieres descargar el modelo.
4) Deploy y comparte la URL pública.

## Qué hace

- Genera CVs/JDs sintéticos (DOCX) y los parsea a diccionarios.
- Calcula features (skills, similitud semántica, experiencia, ubicación), los pondera y produce un score 0–1.
- Explica el score/KO en texto y permite un mini-assessment simulado.
- UI Streamlit para ajustar pesos de skills, filtrar KOs, ver ranking con `cv_id` y exportar CSV.
