# src/normalizer/skills_taxonomy.py

SKILL_TAXONOMY = {
    "python": {"category": "programming", "synonyms": ["py", "python3"]},
    "pyspark": {"category": "big_data", "synonyms": ["spark", "databricks"]},
    "sql": {"category": "databases", "synonyms": ["postgresql", "mysql", "oracle_sql"]},
    "airflow": {"category": "orchestration", "synonyms": ["apache_airflow"]},
    "azure": {"category": "cloud", "synonyms": ["microsoft_azure"]},
    "aws": {"category": "cloud", "synonyms": ["amazon_web_services"]},
    "gcp": {"category": "cloud", "synonyms": ["google_cloud_platform"]},
    "tableau": {"category": "bi", "synonyms": []},
    "powerbi": {"category": "bi", "synonyms": []},
    "excel": {"category": "data_analysis", "synonyms": ["microsoft_excel"]},
    "jira": {"category": "project_management", "synonyms": ["atlassian_jira"]},
    "scrum": {"category": "project_management", "synonyms": []},
    "stakeholder_management": {"category": "soft_skills", "synonyms": ["stakeholder_mgmt"]},
    "planning": {"category": "project_management", "synonyms": []},
    "risk_management": {"category": "project_management", "synonyms": ["risk_mgmt"]},
    "data_modeling": {"category": "data_engineering", "synonyms": []},
    "etl": {"category": "data_engineering", "synonyms": []},
    "machine_learning": {"category": "data_science", "synonyms": ["ml"]},
    "deep_learning": {"category": "data_science", "synonyms": ["dl"]},
    "r": {"category": "programming", "synonyms": []},
    "java": {"category": "programming", "synonyms": []},
    "javascript": {"category": "programming", "synonyms": ["js"]},
    "html": {"category": "web_dev", "synonyms": []},
    "css": {"category": "web_dev", "synonyms": []},
    "react": {"category": "web_dev", "synonyms": []},
    "angular": {"category": "web_dev", "synonyms": []},
    "node.js": {"category": "web_dev", "synonyms": ["nodejs"]},
    "docker": {"category": "devops", "synonyms": []},
    "kubernetes": {"category": "devops", "synonyms": ["k8s"]},
    "git": {"category": "devops", "synonyms": []},
    "ci/cd": {"category": "devops", "synonyms": ["cicd"]},
    "agile": {"category": "project_management", "synonyms": []},
    "prince2": {"category": "project_management", "synonyms": []},
    "qa_automation": {"category": "qa", "synonyms": ["test_automation"]},
    "selenium": {"category": "qa", "synonyms": []},
    "cypress": {"category": "qa", "synonyms": []},
    "marketing_strategy": {"category": "marketing", "synonyms": []},
    "seo": {"category": "marketing", "synonyms": []},
    "sem": {"category": "marketing", "synonyms": []},
    "content_creation": {"category": "marketing", "synonyms": []},
}

# Reverse map for quick lookup of canonical skill from synonym
SKILL_SYNONYM_MAP = {}
for skill, data in SKILL_TAXONOMY.items():
    SKILL_SYNONYM_MAP[skill] = skill # Add canonical skill itself
    for synonym in data["synonyms"]:
        SKILL_SYNONYM_MAP[synonym] = skill

def get_canonical_skill(skill_name: str) -> str:
    """Returns the canonical skill name for a given skill or synonym."""
    return SKILL_SYNONYM_MAP.get(skill_name.lower(), skill_name.lower())

def get_skill_category(skill_name: str) -> str | None:
    """Returns the category of a canonical skill."""
    canonical_skill = get_canonical_skill(skill_name)
    return SKILL_TAXONOMY.get(canonical_skill, {}).get("category")

if __name__ == "__main__":
    print("Canonical skill for 'py':", get_canonical_skill("py"))
    print("Canonical skill for 'pyspark':", get_canonical_skill("pyspark"))
    print("Canonical skill for 'non_existent_skill':", get_canonical_skill("non_existent_skill"))
    print("Category for 'python':", get_skill_category("python"))
    print("Category for 'spark':", get_skill_category("spark"))
    print("Category for 'non_existent_skill':", get_skill_category("non_existent_skill"))