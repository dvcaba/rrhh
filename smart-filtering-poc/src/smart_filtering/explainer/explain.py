# src/explainer/explain.py

from typing import Dict, Any, List
from smart_filtering.ranker.score import calculate_score
from smart_filtering.ranker.features import calculate_haversine_distance
from smart_filtering.normalizer.skills_taxonomy import get_canonical_skill, SKILL_TAXONOMY

def generate_explanation(cv: Dict[str, Any], jd: Dict[str, Any], score_result: Dict[str, Any]) -> str:
    """
    Generates a human-readable explanation for a candidate's score against a job description.
    """
    explanation_parts = []
    
    # Start with overall score and reason
    explanation_parts.append(f"**Análisis de Candidato para '{jd['role']}'**")
    explanation_parts.append(f"Puntuación General: {score_result['score']:.2f}/1.00")
    explanation_parts.append(f"Razón Principal: {score_result['reason']}.")

    features = score_result['features']

    # --- Knock-out Reasons ---
    if score_result['score'] == 0.0:
        if features.get("meets_must_have_skills") == 0:
            missing_skills = [s for s in jd["must_have"] if get_canonical_skill(s) not in cv["skills"]]
            explanation_parts.append(f"❌ **Rechazo por Habilidades Obligatorias:** Faltan habilidades clave como: {', '.join(missing_skills)}.")
        if features.get("meets_min_total_years") == 0:
            explanation_parts.append(f"❌ **Rechazo por Experiencia:** El candidato tiene {features.get('total_experience_years', 0)} años de experiencia total, pero se requieren al menos {features.get('jd_min_total_years', 0)} años.")
        if features.get("meets_min_skill_years") == 0:
            missing_skill_exp = []
            for skill, min_years in jd["min_skill_years"].items():
                canonical_skill = get_canonical_skill(skill)
                if canonical_skill in cv["skills"]:
                    pass 
                else:
                    missing_skill_exp.append(f"{skill} (mín. {min_years} años)")
            if missing_skill_exp:
                explanation_parts.append(f"❌ **Rechazo por Experiencia Específica:** No cumple con la experiencia mínima requerida en: {', '.join(missing_skill_exp)}.")
        if features.get("location_match_score", 0.0) == 0.0 and jd.get("location_policy", {}).get("type") != "remote":
            explanation_parts.append(f"❌ **Rechazo por Ubicación:** El puesto es '{jd.get('location_policy', {}).get('type')}' en {jd.get('location_policy', {}).get('city')} (máx. {jd.get('location_policy', {}).get('max_km', 0)} km), y el candidato reside en {cv.get('location', {}).get('city')}.")
        return "\n".join(explanation_parts)

    # --- Positive Matches and Gaps ---
    explanation_parts.append("\n**Detalle de la Puntuación:**")
    
    # Skills Match
    matched_skills = [s for s in jd["must_have"] + jd["nice_to_have"] if get_canonical_skill(s) in cv["skills"]]
    if matched_skills:
        explanation_parts.append(f"✅ **Habilidades Clave Encontradas:** {', '.join(matched_skills)}.")
    
    missing_nice_to_have = [s for s in jd["nice_to_have"] if get_canonical_skill(s) not in cv["skills"]]
    if missing_nice_to_have:
        explanation_parts.append(f"⚠️ **Oportunidades de Mejora (Habilidades):** Podría mejorar en: {', '.join(missing_nice_to_have)}.")

    # Experience
    explanation_parts.append(f"✅ **Experiencia Total:** El candidato tiene {features['total_experience_years']} años de experiencia (requerido: {features['jd_min_total_years']}+).")

    # Location
    jd_loc_policy = jd["location_policy"]
    cv_loc = cv["location"]
    if jd_loc_policy["type"] == "remote":
        explanation_parts.append("✅ **Ubicación:** El puesto es remoto, por lo que la ubicación del candidato es compatible.")
    elif "distance_to_jd_city_km" in features:
        distance = features["distance_to_jd_city_km"]
        max_km = jd_loc_policy.get("max_km", 0)
        if distance <= max_km:
            explanation_parts.append(f"✅ **Ubicación:** El candidato reside en {cv_loc['city']}, a {distance:.1f} km de {jd_loc_policy['city']}, dentro del radio de {max_km} km.")
        else:
            explanation_parts.append(f"⚠️ **Ubicación:** El candidato reside en {cv_loc['city']}, a {distance:.1f} km de {jd_loc_policy['city']}, superando el radio de {max_km} km. Esto ha penalizado la puntuación.")
    else:
        explanation_parts.append(f"ℹ️ **Ubicación:** El puesto es '{jd_loc_policy['type']}' en {jd_loc_policy['city']}. La ubicación del candidato es {cv_loc['city']}.")

    # Score Components Breakdown
    if 'score_components' in score_result:
        explanation_parts.append("\n**Contribución de Componentes a la Puntuación:**")
        for component, value in score_result['score_components'].items():
            explanation_parts.append(f"- {component.replace('_', ' ').title()}: {value:.2f}")

    return "\n".join(explanation_parts)

if __name__ == "__main__":
    import json
    from smart_filtering.generator.cv_generator import generate_cv
    from smart_filtering.generator.jd_generator import generate_jd

    # Test Case 1: Good match
    print("--- Test Case 1: Good Match (Data Engineer) ---")
    de_jd = generate_jd("Data Engineer")
    de_cv_good = generate_cv(target_role="Data Engineer", relevance_hint=2)
    de_cv_good["skills"][get_canonical_skill("python")] = "advanced"
    de_cv_good["skills"][get_canonical_skill("pyspark")] = "intermediate"
    de_cv_good["skills"][get_canonical_skill("sql")] = "advanced"
    de_cv_good["experience_years_total"] = 5
    de_cv_good["location"] = {"city": "Madrid", "country": "ES", "lat": 40.4168, "lon": -3.7038}
    de_jd["location_policy"] = {"type": "hybrid", "city": "Madrid", "max_km": 50}
    
    score_good = calculate_score(de_cv_good, de_jd)
    explanation_good = generate_explanation(de_cv_good, de_jd, score_good)
    print(explanation_good)

    # Test Case 2: Missing must-have skills (knock-out)
    print("\n--- Test Case 2: Missing Must-Have Skills (Knock-out) ---")
    de_cv_bad_skills = generate_cv(target_role="Project Manager", relevance_hint=0)
    de_cv_bad_skills["skills"] = {get_canonical_skill("excel"): "advanced"} 
    score_bad_skills = calculate_score(de_cv_bad_skills, de_jd)
    explanation_bad_skills = generate_explanation(de_cv_bad_skills, de_jd, score_bad_skills)
    print(explanation_bad_skills)

    # Test Case 3: Not meeting min total experience years (knock-out)
    print("\n--- Test Case 3: Not Meeting Min Total Experience (Knock-out) ---")
    de_cv_low_exp = generate_cv(target_role="Data Engineer", relevance_hint=1)
    de_cv_low_exp["skills"][get_canonical_skill("python")] = "advanced"
    de_cv_low_exp["skills"][get_canonical_skill("pyspark")] = "intermediate"
    de_cv_low_exp["skills"][get_canonical_skill("sql")] = "advanced"
    de_cv_low_exp["experience_years_total"] = 1 
    de_cv_low_exp["location"] = {"city": "Madrid", "country": "ES", "lat": 40.4168, "lon": -3.7038}
    score_low_exp = calculate_score(de_cv_low_exp, de_jd)
    explanation_low_exp = generate_explanation(de_cv_low_exp, de_jd, score_low_exp)
    print(explanation_low_exp)

    # Test Case 4: Location mismatch (knock-out for on-site)
    print("\n--- Test Case 4: Location Mismatch (Knock-out for On-site) ---")
    de_jd_onsite = generate_jd("Data Engineer")
    de_jd_onsite["location_policy"] = {"type": "on-site", "city": "Madrid", "max_km": 20}
    
    cv_barcelona_loc = generate_cv(target_role="Data Engineer")
    cv_barcelona_loc["location"] = {"city": "Barcelona", "country": "ES", "lat": 41.3851, "lon": 2.1734}
    cv_barcelona_loc["skills"][get_canonical_skill("python")] = "advanced"
    cv_barcelona_loc["skills"][get_canonical_skill("pyspark")] = "intermediate"
    cv_barcelona_loc["skills"][get_canonical_skill("sql")] = "advanced"
    cv_barcelona_loc["experience_years_total"] = 5
    
    score_loc_mismatch = calculate_score(cv_barcelona_loc, de_jd_onsite)
    explanation_loc_mismatch = generate_explanation(cv_barcelona_loc, de_jd_onsite, score_loc_mismatch)
    print(explanation_loc_mismatch)
