# src/generator/cv_generator.py

import uuid
import random
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from smart_filtering.normalizer.skills_taxonomy import SKILL_TAXONOMY, get_canonical_skill

# --- Helper Data ---
CITIES = [
    {"city": "Madrid", "country": "ES", "lat": 40.4168, "lon": -3.7038},
    {"city": "Barcelona", "country": "ES", "lat": 41.3851, "lon": 2.1734},
    {"city": "Valencia", "country": "ES", "lat": 39.4699, "lon": -0.3763},
    {"city": "Sevilla", "country": "ES", "lat": 37.3891, "lon": -5.9845},
    {"city": "Lisboa", "country": "PT", "lat": 38.7223, "lon": -9.1393},
    {"city": "Porto", "country": "PT", "lat": 41.1579, "lon": -8.6291},
]

NAMES = [
    "Alex Romero", "Maria Garcia", "Juan Perez", "Laura Fernandez", "Carlos Sanchez",
    "Ana Lopez", "David Rodriguez", "Sofia Martinez", "Pablo Gonzalez", "Elena Ruiz",
    "Luis Herrera", "Carmen Alvarez", "Raul Ortega", "Patricia Vega", "Jorge Navarro",
    "Lucia Ramos", "Sergio Prieto", "Marta Iglesias", "Hector Molina", "Beatriz Santos",
    "Daniela Castro", "Andres Molina", "Irene Gallardo", "Ruben Dominguez", "Natalia Pardo"
]

EDUCATION_DEGREES = [
    "BSc Computer Science", "MSc Data Science", "BSc Software Engineering",
    "MSc Artificial Intelligence", "BSc Business Administration", "MBA"
]

CERTS = [
    "AWS Certified Solutions Architect", "Azure Data Engineer Associate",
    "PMP", "Scrum Master Certified", "Google Cloud Professional Data Engineer"
]

# --- Skill Level Probabilities by Role ---
SKILL_LEVEL_PROBS = {
    "Data Engineer": {
        "basic": 0.2, "intermediate": 0.5, "advanced": 0.3
    },
    "Project Manager": {
        "basic": 0.3, "intermediate": 0.4, "advanced": 0.3
    },
    "QA Automation Engineer": {
        "basic": 0.25, "intermediate": 0.45, "advanced": 0.3
    },
    "Generic": {
        "basic": 0.4, "intermediate": 0.4, "advanced": 0.2
    }
}

# --- Core Skills by Role ---
CORE_SKILLS_BY_ROLE = {
    "Data Engineer": {
        "programming": ["python", "java", "r"],
        "big_data": ["pyspark"],
        "databases": ["sql"],
        "orchestration": ["airflow"],
        "cloud": ["azure", "aws", "gcp"],
        "data_engineering": ["etl", "data_modeling"]
    },
    "Project Manager": {
        "project_management": ["stakeholder_management", "planning", "jira", "agile", "scrum", "prince2", "risk_management"],
        "soft_skills": ["communication", "teamwork"]
    },
    "QA Automation Engineer": {
        "qa": ["qa_automation", "selenium", "cypress"],
        "programming": ["python", "javascript"],
        "devops": ["git", "ci/cd"]
    }
}

def generate_cv_id() -> str:
    """Generates a unique ID for a CV."""
    return f"cv_{uuid.uuid4().hex[:8]}"

def get_skill_level(role: str) -> str:
    """Randomly selects a skill level based on role probabilities."""
    probs = SKILL_LEVEL_PROBS.get(role, SKILL_LEVEL_PROBS["Generic"])
    return random.choices(list(probs.keys()), weights=list(probs.values()), k=1)[0]

def generate_experience(total_years: float, role: str) -> List[Dict[str, Any]]:
    """Generates a list of work experiences."""
    experiences = []
    remaining_years = total_years
    current_date = datetime.now()

    while remaining_years > 0.5: # Minimum 6 months per job
        job_years = round(random.uniform(0.5, min(remaining_years, 5.0)), 1)
        remaining_years -= job_years

        end_date = current_date
        start_date = current_date - timedelta(days=job_years * 365)
        current_date = start_date - timedelta(days=random.randint(30, 180)) # Gap between jobs

        company = f"Company{random.randint(1, 100)}"
        job_title = role if random.random() < 0.7 else f"{role} {random.choice(['Junior', 'Senior', 'Lead'])}"

        job_skills = {}
        # Add core skills for the role
        if role in CORE_SKILLS_BY_ROLE:
            for category, skills in CORE_SKILLS_BY_ROLE[role].items():
                if random.random() < 0.7: # Chance to include skills from core categories
                    skill = random.choice(skills)
                    job_skills[get_canonical_skill(skill)] = get_skill_level(role)
        
        # Add some random skills
        for _ in range(random.randint(0, 2)):
            random_skill = random.choice(list(SKILL_TAXONOMY.keys()))
            job_skills[get_canonical_skill(random_skill)] = get_skill_level(role)

        experiences.append({
            "role": job_title,
            "company": company,
            "years": job_years,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "skills": list(job_skills.keys()) # Only list skills for simplicity in experience object
        })
    return experiences[::-1] # Reverse to show chronologically

def generate_cv(target_role: str = "Generic", relevance_hint: int = 0) -> Dict[str, Any]:
    """Generates a simulated CV."""
    cv_id = generate_cv_id()
    name = random.choice(NAMES)
    location = random.choice(CITIES)
    total_years = round(random.uniform(0.5, 12), 1)

    # Determine primary role based on target_role or randomly
    primary_role = target_role if target_role != "Generic" else random.choice(list(CORE_SKILLS_BY_ROLE.keys()) + ["Generic"])
    if primary_role == "Generic":
        primary_role = random.choice(["Data Analyst", "Software Developer", "Marketing Specialist"])

    experiences = generate_experience(total_years, primary_role)
    
    # Aggregate skills from experiences and add some general ones
    all_skills = {}
    for exp in experiences:
        for skill in exp["skills"]:
            all_skills[get_canonical_skill(skill)] = get_skill_level(primary_role)
    
    # Add some extra skills based on role and total years
    if primary_role == "Data Engineer" and total_years > 4:
        if random.random() < 0.6: all_skills[get_canonical_skill("airflow")] = get_skill_level(primary_role)
        if random.random() < 0.6: all_skills[get_canonical_skill(random.choice(["azure", "aws", "gcp"]))] = get_skill_level(primary_role)
    
    # Languages
    languages = {"es": "native"}
    if random.random() < 0.4: # 40% chance for C1 English
        languages["en"] = "C1"

    # Certifications
    certs = []
    if random.random() < 0.25: # 25% chance for 1 relevant cert
        certs.append(random.choice(CERTS))

    education = [random.choice(EDUCATION_DEGREES)]
    if random.random() < 0.3: # Chance for a second degree
        education.append(random.choice(EDUCATION_DEGREES))

    cv = {
        "id": cv_id,
        "name": name,
        "location": location,
        "title": primary_role, # Simplified: use primary role as title
        "experience_years_total": total_years,
        "experiences": experiences,
        "skills": all_skills,
        "education": education,
        "languages": languages,
        "certs": certs,
        "remote_preference": random.choice(["hybrid", "remote", "on-site"]),
        "embeddings": {"skills_vec": [], "profile_vec": []}, # Placeholder
        "relevance_hint": relevance_hint # For ground truth generation
    }

    # Inject lower-quality profiles for low relevance to garantizar KOs en tests/ranking
    if relevance_hint <= 0:
        # Recorta experiencia total para aumentar probabilidad de KO por años
        cv["experience_years_total"] = round(random.uniform(0.2, 1.5), 1)

        # Quita sistemáticamente las must-have típicas del rol para forzar KO
        MUST_HAVE_BY_ROLE = {
            "Data Engineer": ["python", "pyspark", "sql"],
            "Project Manager": ["stakeholder_management", "planning", "jira", "agile"],
            "QA Automation Engineer": ["qa_automation", "python", "git"],
        }
        remove_list = MUST_HAVE_BY_ROLE.get(primary_role, [])
        for skill in remove_list:
            canonical = get_canonical_skill(skill)
            cv["skills"].pop(canonical, None)

    return cv

if __name__ == "__main__":
    print("Generating a CV for Data Engineer (high relevance):")
    de_cv = generate_cv(target_role="Data Engineer", relevance_hint=2)
    print(json.dumps(de_cv, indent=2))

    print("\nGenerating a CV for Project Manager (medium relevance):")
    pm_cv = generate_cv(target_role="Project Manager", relevance_hint=1)
    print(json.dumps(pm_cv, indent=2))

    print("\nGenerating a generic CV (low relevance):")
    generic_cv = generate_cv(relevance_hint=0)
    print(json.dumps(generic_cv, indent=2))
