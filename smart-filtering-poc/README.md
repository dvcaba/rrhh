# POC: Smart Candidate Filtering & Assessment

This project aims to demonstrate a smart candidate filtering and assessment system using simulated data.

## Project Structure

```
smart-filtering-poc/
  app/
    ui_streamlit/           # UI Streamlit: ranking, filtros, explicación y export CSV
  data/
    raw/
      cvs/                  # CVs .docx generados por run_generation.py
      jds/                  # JDs .docx generados por run_jd_generation.py
    processed/              # Espacio para datos intermedios (ignorado en git)
    outputs/                # Shortlists u otros exports (ignorado en git)
  src/
    smart_filtering/
      generator/            # Creación de CVs/JDs sintéticos y scripts DOCX
      normalizer/           # Taxonomía de skills y helpers de canonicalización
      embedder/             # Wrapper de SentenceTransformer (modo offline disponible)
      ranker/               # Features y scoring (pesos, cobertura, ubicación)
      explainer/            # Texto explicativo/KO del score
      assessor/             # Banco de preguntas y grader simple para mini-assessment
      parser/               # Parsers DOCX → dict para CV/JD
    cli.py                  # CLI generate-cv/generate-jd/rank
    __main__.py             # Permite `python -m smart_filtering`
  tests/                    # Tests básicos de parser y scoring
  PLAN.md                   # Plan de implementación
  README.md                 # Este archivo (guía de uso)
```

Consulta `PLAN.md` para el plan de implementación detallado.

## Setup rápido (dev)

```bash
# Clonar repo (si no lo tienes ya)
# git clone git@github.com:dvcaba/rrhh.git && cd rrhh/smart-filtering-poc

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
- Para entornos sin red o despliegues ligeros, usa `SMART_FILTERING_EMBEDDER_MODE=offline` para evitar descargar el modelo; se usarán embeddings cero (válido para pruebas y smoke tests).
- La generación de CVs está balanceada: se crean perfiles alto/medio/bajo para cada rol (Data Engineer, Project Manager, QA) para que las listas no estén sesgadas por un mismo nombre o rol.

## Tests

```bash
pytest
```

## Cómo funciona (rápido)

- **Generación**: `generator/cv_generator.py` y `run_generation.py` fabrican CVs sintéticos con IDs únicos (`cv_xxxx`), skills, experiencia, educación y ubicación. `generator/jd_generator.py` y `run_jd_generation.py` crean JDs por rol con must-have/nice-to-have, pesos y políticas de ubicación. Se guardan como DOCX en `data/raw`.
- **Parsing**: `parser/docx_parser.py` reconstruye CVs/JDs desde DOCX al formato dict esperado por el motor.
- **Embeddings**: `embedder/embed.py` envuelve `SentenceTransformer`; con `SMART_FILTERING_EMBEDDER_MODE=offline` devuelve vectores cero.
- **Features y scoring**: `ranker/features.py` calcula similitudes semánticas, coberturas de must-have y distancia geográfica; `ranker/score.py` pondera todo según el JD, aplica factores de cobertura y un peso opcional de “skill alignment” definido por el usuario.
- **Explicaciones y assessment**: `explainer/explain.py` genera texto en castellano con razones de score/KO. `assessor/questions.py` y `assessor/grade.py` simulan un mini-assessment muy básico por keywords.
- **UI**: `app/ui_streamlit/app.py` permite elegir JD, ajustar pesos de skills, filtrar KOs, ver ranking con `cv_id`, detalle de CV, explicación y exportar CSV.
