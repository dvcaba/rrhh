# src/ranker/features.py

import numpy as np
from typing import Dict, Any, List
from scipy.spatial.distance import cosine
from smart_filtering.embedder.embed import get_embedder
from smart_filtering.normalizer.skills_taxonomy import get_canonical_skill
from smart_filtering.generator.cv_generator import CITIES # Import CITIES for location calculation

# Keep a cached embedder to avoid re-loading the model on every run
embedder = get_embedder()

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c
    return distance

def get_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculates cosine similarity between embeddings of two texts.
    Returns 1 - cosine_distance, so higher is better.
    """
    if not text1 or not text2:
        return 0.0 # Or handle as appropriate for missing text

    embedding1 = embedder.embed_text(text1)[0]
    embedding2 = embedder.embed_text(text2)[0]

    # Avoid invalid values when embeddings are zero vectors (e.g., offline mode)
    if not np.any(embedding1) or not np.any(embedding2):
        return 0.0
    
    # Cosine similarity is 1 - cosine distance
    return 1 - cosine(embedding1, embedding2)

def extract_features(cv: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and calculates various features for a given CV and JD pair.
    """
    features = {}

    # --- Semantic Features ---
    # Skill Semantic Similarity
    cv_skills_text = " ".join(cv["skills"].keys())
    jd_skills_text = " ".join(jd["must_have"] + jd["nice_to_have"])
    features["skill_semantic_similarity"] = get_semantic_similarity(cv_skills_text, jd_skills_text)

    # Title Semantic Similarity
    features["title_semantic_similarity"] = get_semantic_similarity(cv["title"], jd["role"])

    # --- Experience Features ---
    features["total_experience_years"] = cv["experience_years_total"]
    features["jd_min_total_years"] = jd["min_total_years"]

    # Check if CV meets min total years
    features["meets_min_total_years"] = 1 if cv["experience_years_total"] >= jd["min_total_years"] else 0

    # Min skill years (simplified: check if any skill in JD's min_skill_years is present in CV)
    features["meets_min_skill_years"] = 1
    for skill_req, min_years_req in jd["min_skill_years"].items():
        canonical_skill_req = get_canonical_skill(skill_req)
        if canonical_skill_req not in cv["skills"]:
            features["meets_min_skill_years"] = 0
            break

    # --- Location Features ---
    cv_loc = cv["location"]
    jd_loc_policy = jd["location_policy"]
    features["distance_to_jd_city_km"] = None

    features["location_match_score"] = 0.0
    if jd_loc_policy["type"] == "remote":
        features["location_match_score"] = 1.0
    elif jd_loc_policy["type"] in ["hybrid", "on-site"] and "city" in jd_loc_policy and "lat" in cv_loc and "lon" in cv_loc:
        jd_city_coords = next((c for c in CITIES if c["city"] == jd_loc_policy["city"]), None)
        if jd_city_coords:
            distance = calculate_haversine_distance(
                cv_loc["lat"], cv_loc["lon"],
                jd_city_coords["lat"], jd_city_coords["lon"]
            )
            features["distance_to_jd_city_km"] = distance
            if distance <= jd_loc_policy.get("max_km", 0):
                features["location_match_score"] = 1.0
            else:
                features["location_match_score"] = max(0.0, 1 - (distance / (jd_loc_policy.get("max_km", 1) * 2)))
        else:
            features["location_match_score"] = 0.0

    # --- Rule-based Features ---
    must_total = len(jd.get("must_have", []))
    must_matches = sum(
        1 for s in jd.get("must_have", []) if get_canonical_skill(s) in cv["skills"]
    )
    features["must_have_coverage"] = must_matches / must_total if must_total else 1.0

    min_skill_total = len(jd.get("min_skill_years", {}))
    min_skill_matches = sum(
        1 for s in jd.get("min_skill_years", {}) if get_canonical_skill(s) in cv["skills"]
    )
    features["min_skill_years_coverage"] = (
        min_skill_matches / min_skill_total if min_skill_total else 1.0
    )

    # Language match
    features["meets_language_requirements"] = 1

    # Education match
    features["has_education"] = 1 if cv["education"] else 0

    return features

if __name__ == "__main__":
    import json
    from smart_filtering.generator.cv_generator import generate_cv
    from smart_filtering.generator.jd_generator import generate_jd
    
    sample_de_jd = generate_jd("Data Engineer")
    sample_de_cv_good = generate_cv(target_role="Data Engineer", relevance_hint=2)
    sample_de_cv_bad = generate_cv(target_role="Project Manager", relevance_hint=0) # Mismatch role

    # Modify a bad CV to fail must-have
    sample_de_cv_bad["skills"] = {"excel": "advanced"} # Remove python/pyspark

    print("--- Features for good Data Engineer CV vs DE JD ---")
    features_good = extract_features(sample_de_cv_good, sample_de_jd)
    print(json.dumps(features_good, indent=2))

    print("\n--- Features for bad Data Engineer CV (missing must-have) vs DE JD ---")
    features_bad = extract_features(sample_de_cv_bad, sample_de_jd)
    print(json.dumps(features_bad, indent=2))

    # Test location
    sample_de_jd_onsite = generate_jd("Data Engineer")
    sample_de_jd_onsite["location_policy"] = {"type": "on-site", "city": "Madrid", "max_km": 20}
    
    cv_madrid = generate_cv(target_role="Data Engineer")
    cv_madrid["location"] = {"city": "Madrid", "country": "ES", "lat": 40.4168, "lon": -3.7038}
    
    cv_barcelona = generate_cv(target_role="Data Engineer")
    cv_barcelona["location"] = {"city": "Barcelona", "country": "ES", "lat": 41.3851, "lon": 2.1734}

    print("\n--- Features for CV in Madrid vs On-site Madrid JD ---")
    features_loc_madrid = extract_features(cv_madrid, sample_de_jd_onsite)
    print(json.dumps(features_loc_madrid, indent=2))

    print("\n--- Features for CV in Barcelona vs On-site Madrid JD ---")
    features_loc_barcelona = extract_features(cv_barcelona, sample_de_jd_onsite)
    print(json.dumps(features_loc_barcelona, indent=2))
