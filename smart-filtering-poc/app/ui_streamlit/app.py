# smart-filtering-poc/app/ui_streamlit/app.py

import os
import sys
from pathlib import Path
import copy
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from smart_filtering.config import load_config, resolve_path
from smart_filtering.assessor.grade import calculate_assessment_score
from smart_filtering.assessor.questions import get_assessment_questions
from smart_filtering.explainer.explain import generate_explanation
from smart_filtering.normalizer.skills_taxonomy import get_canonical_skill
from smart_filtering.generator.run_generation import create_cvs_as_docx
from smart_filtering.generator.run_jd_generation import create_jds_as_docx, JD_ROLES
from smart_filtering.parser.docx_parser import parse_docx_cv, parse_docx_jd
from smart_filtering.ranker.score import calculate_score


st.set_page_config(layout="wide", page_title="Smart Candidate Filtering & Assessment")

st.markdown(
    """
    <style>
    .hero {
        padding: 12px 16px;
        border-radius: 12px;
        background: linear-gradient(90deg, #0f172a, #1e293b);
        color: #e2e8f0;
        margin-bottom: 12px;
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px 6px 2px 0;
        border-radius: 999px;
        background: #0ea5e9;
        color: #0b1220;
        font-size: 12px;
        font-weight: 600;
    }
    .section-card {
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(jd_dir: str, cv_dir: str):
    """Loads JDs and CVs from specified directories."""
    jds = []
    if not os.path.exists(jd_dir) or not any(f.endswith(".docx") for f in os.listdir(jd_dir) if not f.startswith("~")):
        # Autogenera JDs si no existen (útil en despliegues cloud/limpios)
        os.makedirs(jd_dir, exist_ok=True)
        create_jds_as_docx(jd_dir, JD_ROLES)

    for filename in os.listdir(jd_dir):
        if filename.endswith(".docx") and not filename.startswith("~"):
            file_path = os.path.join(jd_dir, filename)
            jd_data = parse_docx_jd(file_path)
            if jd_data and jd_data.get("id"):
                jds.append(jd_data)

    if not jds:
        st.warning("No JDs found. Por favor ejecuta el script de generación de JD.")

    cvs = []
    if not os.path.exists(cv_dir) or not any(f.endswith(".docx") for f in os.listdir(cv_dir) if not f.startswith("~")):
        os.makedirs(cv_dir, exist_ok=True)
        create_cvs_as_docx(cv_dir, num_cvs=15)

    for filename in os.listdir(cv_dir):
        if filename.endswith(".docx") and not filename.startswith("~"):
            file_path = os.path.join(cv_dir, filename)
            cv_data = parse_docx_cv(file_path)
            if cv_data and cv_data.get("id"):
                cvs.append(cv_data)

    if not cvs:
        st.warning("No CVs found. Por favor ejecuta el script de generación de CV.")

    return jds, cvs


def display_cv_details(cv_data: Dict[str, Any]):
    """Displays CV details in a formatted way."""
    loc = cv_data.get("location", {})
    cols = st.columns(3)
    cols[0].metric("Experiencia", f"{cv_data.get('experience_years_total', 0)} años")
    cols[1].metric("Ubicación", f"{loc.get('city', 'N/A')}, {loc.get('country', 'N/A')}")
    cols[2].metric("Preferencia", cv_data.get("remote_preference", "-").title())

    st.markdown("#### Experiencia")
    if cv_data.get("experiences"):
        for exp in cv_data["experiences"]:
            st.markdown(f"**{exp.get('role', 'N/A')}** · {exp.get('company', 'N/A')} | {exp.get('start_date', 'N/A')} → {exp.get('end_date', 'N/A')}")
            if exp.get("skills"):
                st.caption(", ".join(exp["skills"]))
    else:
        st.info("No se encontró experiencia profesional.")

    st.markdown("#### Skills")
    if cv_data.get("skills"):
        skill_strings = [f"{skill} ({level})" for skill, level in cv_data["skills"].items()]
        st.write(", ".join(skill_strings))
    else:
        st.info("No se encontraron habilidades.")

    st.markdown("#### Educación")
    if cv_data.get("education"):
        st.write(" · ".join(cv_data["education"]))
    else:
        st.info("No se encontró educación.")

    st.markdown("#### Idiomas y Certificaciones")
    languages = cv_data.get("languages", {})
    certs = cv_data.get("certs", [])
    if languages:
        lang_strings = [f"{lang}: {level}" for lang, level in languages.items()]
        st.write("Idiomas: " + ", ".join(lang_strings))
    if certs:
        st.write("Certificaciones: " + ", ".join(certs))
    if not languages and not certs:
        st.info("Sin idiomas o certificaciones reportadas.")


def render_score_components(score_details: Dict[str, Any]):
    components = score_details.get("score_components", {})
    if not components:
        st.write("No hay detalle de score disponible.")
        return

    for label, value in components.items():
        readable = label.replace("_", " ").title()
        try:
            safe_val = float(value)
        except (TypeError, ValueError):
            continue
        safe_val = max(0.0, min(1.0, safe_val))
        st.progress(safe_val, text=f"{readable}: {safe_val:.2f}")



# --- Streamlit App ---
CONFIG = load_config()
data_cfg = CONFIG.get("data", {})
ranking_cfg = CONFIG.get("ranking", {})

cv_input_directory = resolve_path(data_cfg.get("cvs_dir", "data/raw/cvs"), project_root=PROJECT_ROOT)
jd_input_directory = resolve_path(data_cfg.get("jds_dir", "data/raw/jds"), project_root=PROJECT_ROOT)

default_skill_weight_strength = float(ranking_cfg.get("default_skill_weight_strength", 0.25))

all_jds, all_cvs = load_data(str(jd_input_directory), str(cv_input_directory))

st.markdown(
    """
<div class="hero">
  <div style="font-size:18px; font-weight:700;">Smart Candidate Filtering & Assessment</div>
  <div style="color:#cbd5e1;">Filtrado inteligente de candidatos por skills, experiencia y ubicación.</div>
</div>
    """,
    unsafe_allow_html=True,
)

if not all_jds or not all_cvs:
    st.stop()

# Sidebar for JD selection and filters
with st.sidebar:
    st.header("JD & filtros")
    jd_options = {jd["role"]: jd for jd in all_jds}
    selected_jd_role = st.selectbox("Rol", options=list(jd_options.keys()))
    selected_jd_base = jd_options[selected_jd_role]
    selected_jd_eval = copy.deepcopy(selected_jd_base)

    st.caption("Must-have skills")
    for skill in selected_jd_base["must_have"]:
        st.markdown(f"<span class='pill'>{skill}</span>", unsafe_allow_html=True)
    min_years_override = st.slider(
        "Min años de experiencia (override)",
        min_value=0,
        max_value=20,
        value=int(selected_jd_base.get("min_total_years", 0)),
        step=1,
    )
    selected_jd_eval["min_total_years"] = min_years_override

    st.write(f"Min años exp usando: **{selected_jd_eval['min_total_years']}**")
    loc_policy = selected_jd_eval.get("location_policy", {})
    st.write(
        f"Ubicación: **{loc_policy.get('type', 'N/A')}** en {loc_policy.get('city', 'N/A')} (max {loc_policy.get('max_km', 0)} km)"
    )

    show_only_pass = st.toggle("Mostrar solo candidatos que pasan KO", value=False)

    st.divider()
    st.subheader("Ponderar skills/experiencia (opcional)")
    skill_alignment_weight = st.slider(
        "Peso adicional del bloque de skills (0 = sin efecto, 1 = máximo)",
        min_value=0.0,
        max_value=1.0,
        value=min(1.0, default_skill_weight_strength),
        step=0.05,
    )
    available_skills = list(
        dict.fromkeys(selected_jd_eval.get("must_have", []) + selected_jd_eval.get("nice_to_have", []))
    )
    default_selected = selected_jd_eval.get("must_have", [])
    selected_skills = st.multiselect(
        "Selecciona las skills que quieres ponderar",
        options=available_skills,
        default=default_selected,
    )
    user_skill_weights: Dict[str, float] = {}
    for skill in selected_skills:
        user_skill_weights[get_canonical_skill(skill)] = st.slider(
            f"Importancia de {skill}",
            min_value=0.0,
            max_value=10.0,
            value=8.0 if skill in default_selected else 5.0,
            step=1.0,
            key=f"skill_{skill}",
    )

    exp_weight_boost = st.slider(
        "Peso extra de experiencia (1 = usa el JD tal cual)",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.1,
    )

    st.divider()
    st.caption("Export")


# Ajusta pesos de experiencia según slider
selected_jd_eval["weights"] = dict(selected_jd_eval.get("weights", {}))
selected_jd_eval["weights"]["experience"] = selected_jd_eval["weights"].get("experience", 0.0) * exp_weight_boost

# Process CVs
scored_cvs: List[Dict[str, Any]] = []
for cv in all_cvs:
    score_result = calculate_score(
        cv,
        selected_jd_eval,
        skill_weights=user_skill_weights,
        skill_weight_strength=skill_alignment_weight,
    )
    scored_cvs.append(
        {
            "cv_id": cv["id"],
            "name": cv["name"],
            "score": score_result["score"],
            "ko_reason": score_result.get("ko_reason") or "OK",
            "experience_years_total": cv.get("experience_years_total", 0),
            "location_city": cv.get("location", {}).get("city", ""),
            "distance_km": score_result["features"].get("distance_to_jd_city_km"),
            "score_details": score_result,
            "original_cv": cv,
        }
    )

if show_only_pass:
    filtered_cvs = [cv for cv in scored_cvs if cv["ko_reason"] == "OK"]
else:
    filtered_cvs = scored_cvs

ranked_cvs = sorted(filtered_cvs, key=lambda x: x["score"], reverse=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Candidatos para {selected_jd_eval['role']}")
    if not ranked_cvs:
        st.warning("No hay candidatos que cumplan los knock-outs. Quita filtros o revisa las must-have.")
    else:
        df_ranked_cvs = pd.DataFrame(ranked_cvs)
        df_ranked_cvs["score_pct"] = (df_ranked_cvs["score"] * 100).round(1)
        table_cols = ["cv_id", "name", "score_pct", "experience_years_total", "location_city", "ko_reason"]
        st.dataframe(
            df_ranked_cvs[table_cols],
            hide_index=True,
            column_config={
                "cv_id": "ID",
                "score_pct": "Score",
                "experience_years_total": "Años exp",
                "location_city": "Ciudad",
                "ko_reason": "KO reason",
            },
            use_container_width=True,
        )

        selected_candidate_index = st.selectbox(
            "Selecciona un candidato",
            options=range(len(ranked_cvs)),
            format_func=lambda x: f"{ranked_cvs[x]['name']} ({ranked_cvs[x]['cv_id']})",
        )
        selected_candidate_data = ranked_cvs[selected_candidate_index]
        selected_cv = selected_candidate_data["original_cv"]

        st.markdown("---")
        st.subheader(f"{selected_candidate_data['name']} · Score {selected_candidate_data['score']*100:.1f}")
        st.caption(f"ID: {selected_candidate_data['cv_id']}")
        display_cv_details(selected_cv)

with col2:
    if ranked_cvs:
        st.subheader("Explicación del ranking")
        explanation = generate_explanation(selected_cv, selected_jd_eval, selected_candidate_data["score_details"])
        st.markdown(explanation)
        st.caption("Componentes de score")
        render_score_components(selected_candidate_data["score_details"])

        st.markdown("---")
        st.subheader("Mini-assessment simulado")
        if st.button("Lanzar ahora"):
            skills_for_assessment = [get_canonical_skill(s) for s in selected_jd["must_have"]]
            if not skills_for_assessment:
                st.info("No hay habilidades 'must-have' definidas en esta JD para el assessment.")
            else:
                assessment_questions = get_assessment_questions(skills_for_assessment, num_questions_per_skill=1)
                if not assessment_questions:
                    st.info("No se encontraron preguntas de assessment para las habilidades requeridas.")
                else:
                    simulated_candidate_answers = {}
                    for q_data in assessment_questions:
                        skill = q_data["skill"]
                        if skill in selected_cv["skills"]:
                            simulated_candidate_answers[q_data["question"]] = q_data["correct_answer"]
                        else:
                            simulated_candidate_answers[q_data["question"]] = "No estoy seguro de la respuesta."

                    assessment_results = calculate_assessment_score(
                        assessment_questions, simulated_candidate_answers
                    )

                    st.write(
                        f"**Puntuación General:** {assessment_results['overall_assessment_score']:.2f}/100"
                    )
                    with st.expander("Preguntas y respuestas"):
                        for q_result in assessment_results["graded_questions"]:
                            st.markdown(f"**{q_result['skill']}**")
                            st.markdown(f"Pregunta: {q_result['question']}")
                            st.markdown(f"Respuesta: {q_result['candidate_answer']}")
                            st.markdown(f"Respuesta correcta: {q_result['correct_answer']}")
                            st.markdown(f"Score: {q_result['score']:.2f}/100")
                            st.markdown("---")

        st.markdown("---")
        st.subheader("Exportar shortlist")
        csv_export = pd.DataFrame(ranked_cvs).to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv_export,
            file_name=f"shortlist_{selected_jd_role}.csv",
            mime="text/csv",
        )
