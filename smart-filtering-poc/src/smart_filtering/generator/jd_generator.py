# src/generator/jd_generator.py

import uuid
import random
import json
from typing import List, Dict, Any
from smart_filtering.normalizer.skills_taxonomy import SKILL_TAXONOMY, get_canonical_skill

def generate_jd_id() -> str:
    """Generates a unique ID for a Job Description."""
    return f"jd_{uuid.uuid4().hex[:8]}"

def get_random_skills(category: str, count: int, exclude: List[str] = None) -> List[str]:
    """Returns a list of random skills from a given category."""
    if exclude is None:
        exclude = []
    available_skills = [
        skill for skill, data in SKILL_TAXONOMY.items()
        if data["category"] == category and skill not in exclude
    ]
    return random.sample(available_skills, min(count, len(available_skills)))

def generate_jd(role_type: str) -> Dict[str, Any]:
    """Generates a simulated Job Description based on role type."""
    jd = {
        "id": generate_jd_id(),
        "role": role_type,
        "location_policy": {},
        "must_have": [],
        "nice_to_have": [],
        "min_total_years": 0,
        "min_skill_years": {},
        "description": "",
        "weights": {},
        "embeddings": {"jd_vec": []} # Placeholder
    }

    if role_type == "Data Engineer":
        jd["location_policy"] = {"type": random.choice(["hybrid", "remote"]), "city": "Madrid", "max_km": 50}
        jd["must_have"] = [get_canonical_skill(s) for s in ["python", "pyspark", "sql"]]
        jd["nice_to_have"] = [get_canonical_skill(s) for s in ["airflow", random.choice(["azure", "aws", "gcp"]), "etl", "data_modeling"]]
        jd["min_total_years"] = random.randint(3, 7)
        jd["min_skill_years"] = {
            get_canonical_skill("python"): random.randint(2, 4),
            get_canonical_skill("pyspark"): random.randint(1, 3)
        }
        jd["description"] = (
            f"Buscamos un/a {role_type} con experiencia en la construcción de pipelines ETL "
            f"y procesamiento de datos a gran escala. Se requiere dominio de {', '.join(jd['must_have'])}. "
            f"Valorable experiencia en {', '.join(jd['nice_to_have'])}. "
            f"El puesto es {jd['location_policy']['type']} en {jd['location_policy']['city']}."
        )
        jd["weights"] = {
            "skill_semantic": 0.45,
            "title_semantic": 0.25,
            "experience": 0.15,
            "location": 0.10,
            "education": 0.05
        }
    elif role_type == "Project Manager":
        jd["location_policy"] = {"type": random.choice(["on-site", "hybrid"]), "city": "Barcelona", "max_km": 30}
        jd["must_have"] = [get_canonical_skill(s) for s in ["stakeholder_management", "planning", "jira", "agile"]]
        jd["nice_to_have"] = [get_canonical_skill(s) for s in ["scrum", "prince2", "risk_management"]]
        jd["min_total_years"] = random.randint(5, 10)
        jd["min_skill_years"] = {
            get_canonical_skill("agile"): random.randint(3, 5)
        }
        jd["description"] = (
            f"Necesitamos un/a {role_type} experimentado/a para liderar proyectos tecnológicos. "
            f"Imprescindible experiencia en {', '.join(jd['must_have'])}. "
            f"Se valorará conocimiento de {', '.join(jd['nice_to_have'])}. "
            f"El puesto es {jd['location_policy']['type']} en {jd['location_policy']['city']}."
        )
        jd["weights"] = {
            "skill_semantic": 0.30,
            "title_semantic": 0.30,
            "experience": 0.25,
            "location": 0.10,
            "education": 0.05
        }
    elif role_type == "QA Automation Engineer":
        jd["location_policy"] = {"type": random.choice(["remote", "hybrid"]), "city": "Valencia", "max_km": 70}
        jd["must_have"] = [get_canonical_skill(s) for s in ["qa_automation", "python", "git"]]
        jd["nice_to_have"] = [get_canonical_skill(s) for s in ["selenium", "cypress", "ci/cd"]]
        jd["min_total_years"] = random.randint(2, 6)
        jd["min_skill_years"] = {
            get_canonical_skill("qa_automation"): random.randint(1, 3)
        }
        jd["description"] = (
            f"Buscamos un/a {role_type} para automatizar pruebas de software. "
            f"Se requiere experiencia en {', '.join(jd['must_have'])}. "
            f"Conocimientos en {', '.join(jd['nice_to_have'])} serán un plus. "
            f"El puesto es {jd['location_policy']['type']} en {jd['location_policy']['city']}."
        )
        jd["weights"] = {
            "skill_semantic": 0.40,
            "title_semantic": 0.20,
            "experience": 0.20,
            "location": 0.10,
            "education": 0.10
        }
    else:
        # Default / Generic role
        jd["location_policy"] = {"type": "remote", "city": "Any", "max_km": 0}
        jd["must_have"] = [get_canonical_skill(s) for s in ["communication", "teamwork"]]
        jd["nice_to_have"] = [get_canonical_skill(s) for s in ["problem_solving"]]
        jd["min_total_years"] = random.randint(0, 2)
        jd["description"] = f"Buscamos un/a {role_type} con buenas habilidades de comunicación."
        jd["weights"] = {
            "skill_semantic": 0.30,
            "title_semantic": 0.30,
            "experience": 0.20,
            "location": 0.10,
            "education": 0.10
        }

    return jd

if __name__ == "__main__":
    print("Generating a Data Engineer JD:")
    de_jd = generate_jd("Data Engineer")
    print(json.dumps(de_jd, indent=2))

    print("\nGenerating a Project Manager JD:")
    pm_jd = generate_jd("Project Manager")
    print(json.dumps(pm_jd, indent=2))

    print("\nGenerating a QA Automation Engineer JD:")
    qa_jd = generate_jd("QA Automation Engineer")
    print(json.dumps(qa_jd, indent=2))
