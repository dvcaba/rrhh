# POC: Smart Candidate Filtering & Assessment

This project aims to demonstrate a smart candidate filtering and assessment system using simulated data.

## Project Structure

```
smart-filtering-poc/
  app/
    ui_streamlit/           # UI Streamlit (lector de CV/JD ya parseados)
  data/
    raw/
      cvs/                  # CVs .docx generados
      jds/                  # JDs .docx generados
    processed/
    outputs/
  src/
    smart_filtering/
      generator/
      normalizer/
      embedder/
      ranker/
      explainer/
      assessor/
      parser/
  tests/
  PLAN.md
  README.md
```

Consulta `PLAN.md` para el plan de implementación detallado.

## Setup rápido (dev)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # instala en editable con extras dev

# Generar datos de ejemplo (CVs/JDs) en data/raw
python -m smart_filtering.generator.run_generation
python -m smart_filtering.generator.run_jd_generation

# Lanzar la UI
streamlit run app/ui_streamlit/app.py
```

## CLI

- Generar CVs: `smart-filtering generate-cv --n 20 --out data/raw/cvs`
- Generar JDs: `smart-filtering generate-jd --roles "Data Engineer,Project Manager" --out data/raw/jds`
- Rankear y exportar shortlist: `smart-filtering rank --jd-role "Data Engineer" --out data/outputs/shortlist.csv`

## Configuración

- Archivo por defecto: `config/default.yaml` (rutas de datos/outputs, modelo de embeddings, peso de skills).
- Puedes apuntar a otro YAML con `SMART_FILTERING_CONFIG=/ruta/a/otro.yaml`.
- Para entornos sin red, usa `SMART_FILTERING_EMBEDDER_MODE=offline` para evitar descargar el modelo; se usarán embeddings cero (válido para pruebas y smoke tests).

## Tests

```bash
pytest
```
