# src/ranker/score.py

from typing import Dict, Any, Optional
from smart_filtering.ranker.features import extract_features
from smart_filtering.normalizer.skills_taxonomy import get_canonical_skill

def normalize_feature(value: float, min_val: float, max_val: float) -> float:
    """Min-max normalization to scale a feature to [0, 1]."""
    if max_val == min_val:
        return 0.0 if value <= min_val else 1.0 # Handle division by zero
    return (value - min_val) / (max_val - min_val)

def calculate_score(
    cv: Dict[str, Any],
    jd: Dict[str, Any],
    skill_weights: Optional[Dict[str, float]] = None,
    skill_weight_strength: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculates a weighted score for a CV against a JD, applying knock-out rules.
    Returns a dictionary with the score and a breakdown of features.
    """
    features = extract_features(cv, jd)

    # --- Knock-out rules (hard filters) ---
    ko_reasons = []
    if features.get("meets_must_have_skills") == 0:
        missing = [s for s in jd.get("must_have", []) if get_canonical_skill(s) not in cv.get("skills", {})]
        if missing:
            ko_reasons.append(f"Faltan must-have: {', '.join(missing)}")
        else:
            ko_reasons.append("No cumple habilidades must-have")

    if features.get("meets_min_total_years") == 0:
        ko_reasons.append(f"Experiencia total insuficiente ({features.get('total_experience_years', 0)} vs {jd.get('min_total_years', 0)})")

    if features.get("meets_min_skill_years") == 0:
        ko_reasons.append("No cumple mínima experiencia por skill")

    if features.get("location_match_score", 0.0) == 0.0 and jd.get("location_policy", {}).get("type") != "remote":
        ko_reasons.append("Ubicación fuera de rango para un puesto no remoto")

    if ko_reasons:
        return {
            "score": 0.0,
            "reason": "; ".join(ko_reasons),
            "features": features,
            "score_components": {},
        }

    # --- Calculate Weighted Score ---
    weights = jd["weights"]
    
    # Normalize experience years (assuming 0-15 years as a reasonable range for normalization)
    normalized_experience = normalize_feature(features["total_experience_years"], 0, 15)
    
    # Education bonus (simple binary for now)
    education_bonus = 1.0 if features["has_education"] else 0.0

    # Custom skill alignment (optional, weighted by recruiter input)
    skill_alignment = 0.0
    if skill_weights:
        normalized_skill_weights = {
            get_canonical_skill(k): v for k, v in skill_weights.items() if v and v > 0
        }
        total_skill_weight = sum(normalized_skill_weights.values())
        if total_skill_weight > 0:
            matched_weight = sum(
                weight for skill, weight in normalized_skill_weights.items() if skill in cv["skills"]
            )
            skill_alignment = matched_weight / total_skill_weight

    # Coverage factors to avoid hard knock-outs
    must_cov = features.get("must_have_coverage", 0.0)
    min_skill_cov = features.get("min_skill_years_coverage", 0.0)
    coverage_factor = 0.2 + 0.5 * must_cov + 0.3 * min_skill_cov
    coverage_factor = min(1.0, max(0.1, coverage_factor))

    # Experience factor to soften penalty for being slightly under the min
    exp_factor = 1.0
    if jd["min_total_years"]:
        exp_factor = min(1.0, (cv.get("experience_years_total", 0) or 0) / jd["min_total_years"])
        exp_factor = max(0.3, exp_factor)  # keep some signal even if below

    # Ensure all weights are present, default to 0 if not specified in JD
    w_skill_sem = weights.get("skill_semantic", 0.0)
    w_title_sem = weights.get("title_semantic", 0.0)
    w_experience = weights.get("experience", 0.0)
    w_location = weights.get("location", 0.0)
    w_education = weights.get("education", 0.0)

    # Calculate score components
    score_components = {
        "skill_semantic": features["skill_semantic_similarity"] * w_skill_sem,
        "title_semantic": features["title_semantic_similarity"] * w_title_sem,
        "experience": normalized_experience * w_experience * exp_factor,
        "location": features["location_match_score"] * w_location,
        "education": education_bonus * w_education,
        "must_have": must_cov * 0.1,  # small extra weight to reward coverage
        "skill_alignment": skill_alignment * skill_weight_strength,
    }
    
    total_score = sum(score_components.values())
    sum_of_weights = sum(weights.values()) + 0.1 + skill_weight_strength  # include must-have and custom skill bump
    if sum_of_weights > 0:
        total_score /= sum_of_weights

    total_score *= coverage_factor
    total_score = max(0.0, min(1.0, total_score))
    
    return {
        "score": round(total_score, 4),
        "reason": "Score calculated successfully",
        "features": features,
        "score_components": score_components
    }

if __name__ == "__main__":
    import json
    from smart_filtering.generator.cv_generator import generate_cv
    from smart_filtering.generator.jd_generator import generate_jd

    # Test Case 1: Good match
    print("--- Test Case 1: Good Match (Data Engineer) ---")
    de_jd = generate_jd("Data Engineer")
    de_cv_good = generate_cv(target_role="Data Engineer", relevance_hint=2)
    
    # Ensure CV has must-have skills for DE JD
    de_cv_good["skills"][get_canonical_skill("python")] = "advanced"
    de_cv_good["skills"][get_canonical_skill("pyspark")] = "intermediate"
    de_cv_good["skills"][get_canonical_skill("sql")] = "advanced"
    de_cv_good["experience_years_total"] = 5 # Meets min_total_years
    
    score_good = calculate_score(de_cv_good, de_jd)
    print(f"CV ID: {de_cv_good['id']}, JD ID: {de_jd['id']}")
    print(json.dumps(score_good, indent=2))

    # Test Case 2: Missing must-have skills (knock-out)
    print("\n--- Test Case 2: Missing Must-Have Skills (Knock-out) ---")
    de_cv_bad_skills = generate_cv(target_role="Project Manager", relevance_hint=0)
    de_cv_bad_skills["skills"] = {get_canonical_skill("excel"): "advanced"} # No DE skills
    score_bad_skills = calculate_score(de_cv_bad_skills, de_jd)
    print(f"CV ID: {de_cv_bad_skills['id']}, JD ID: {de_jd['id']}")
    print(json.dumps(score_bad_skills, indent=2))

    # Test Case 3: Not meeting min total experience years (knock-out)
    print("\n--- Test Case 3: Not Meeting Min Total Experience (Knock-out) ---")
    de_cv_low_exp = generate_cv(target_role="Data Engineer", relevance_hint=1)
    de_cv_low_exp["skills"][get_canonical_skill("python")] = "advanced"
    de_cv_low_exp["skills"][get_canonical_skill("pyspark")] = "intermediate"
    de_cv_low_exp["skills"][get_canonical_skill("sql")] = "advanced"
    de_cv_low_exp["experience_years_total"] = 1 # Lower than DE JD min (e.g., 3)
    score_low_exp = calculate_score(de_cv_low_exp, de_jd)
    print(f"CV ID: {de_cv_low_exp['id']}, JD ID: {de_jd['id']}")
    print(json.dumps(score_low_exp, indent=2))

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
    print(f"CV ID: {cv_barcelona_loc['id']}, JD ID: {de_jd_onsite['id']}")
    print(json.dumps(score_loc_mismatch, indent=2))
