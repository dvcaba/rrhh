# src/assessor/questions.py

from typing import Dict, List, Any
import random

# A simple bank of questions and correct answers for various skills
# In a real system, this would be much more extensive or dynamically generated.
QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {"question": "¿Qué es un decorador en Python?", "answer": "Un decorador es una función que toma otra función como argumento, añade alguna funcionalidad y la devuelve sin modificar su estructura."}, 
        {"question": "¿Cuál es la diferencia entre una lista y una tupla?", "answer": "Las listas son mutables (se pueden modificar), mientras que las tuplas son inmutables (no se pueden modificar después de su creación)."},
        {"question": "¿Qué es un generador en Python?", "answer": "Un generador es una función que devuelve un iterador que produce una secuencia de resultados en lugar de un solo valor, usando la palabra clave `yield`."} 
    ],
    "pyspark": [
        {"question": "¿Qué es un DataFrame en PySpark?", "answer": "Un DataFrame en PySpark es una colección distribuida de datos organizada en columnas con nombre, similar a una tabla en una base de datos relacional."}, 
        {"question": "¿Cuál es la diferencia entre una transformación y una acción en Spark?", "answer": "Las transformaciones (ej. `filter`, `select`) crean un nuevo RDD/DataFrame a partir de uno existente de forma perezosa. Las acciones (ej. `count`, `show`) ejecutan el cómputo y devuelven un resultado o lo escriben en un sistema de almacenamiento."}, 
        {"question": "¿Qué es el 'lazy evaluation' en Spark?", "answer": "La evaluación perezosa significa que Spark no ejecuta las transformaciones inmediatamente. En su lugar, construye un DAG (Directed Acyclic Graph) de operaciones y solo las ejecuta cuando se invoca una acción."}
    ],
    "sql": [
        {"question": "¿Qué es una JOIN en SQL y cuáles son sus tipos principales?", "answer": "Una JOIN se usa para combinar filas de dos o más tablas basándose en una columna relacionada entre ellas. Los tipos principales son INNER JOIN, LEFT JOIN (o LEFT OUTER JOIN), RIGHT JOIN (o RIGHT OUTER JOIN) y FULL JOIN (o FULL OUTER JOIN)."},
        {"question": "¿Qué es la normalización de bases de datos?", "answer": "La normalización es un proceso de organización de las columnas y tablas de una base de datos relacional para minimizar la redundancia de datos y mejorar la integridad de los datos."}, 
        {"question": "¿Qué es un índice en una base de datos?", "answer": "Un índice es una estructura de datos que mejora la velocidad de las operaciones de recuperación de datos en una tabla de base de datos, aunque a costa de un mayor espacio de almacenamiento y un rendimiento más lento en las operaciones de escritura."}
    ],
    "agile": [
        {"question": "¿Qué es la metodología Scrum?", "answer": "Scrum es un marco de trabajo ágil para gestionar proyectos complejos, que se basa en ciclos de trabajo iterativos e incrementales llamados Sprints."}, 
        {"question": "¿Cuáles son los roles principales en Scrum?", "answer": "Los roles principales son Product Owner (responsable del qué), Scrum Master (responsable del cómo y de eliminar impedimentos) y el Equipo de Desarrollo (responsable de entregar el incremento)."},
        {"question": "¿Qué es un Sprint en Scrum?", "answer": "Un Sprint es un período de tiempo fijo y corto (generalmente de 1 a 4 semanas) durante el cual un equipo Scrum trabaja para completar un conjunto de trabajo definido y entregar un incremento de producto potencialmente liberable."}
    ],
}

def get_assessment_questions(skills: List[str], num_questions_per_skill: int = 1) -> List[Dict[str, Any]]:
    """
    Retrieves a list of assessment questions for given skills.
    """
    questions_for_assessment = []
    for skill in skills:
        if skill in QUESTION_BANK:
            available_questions = QUESTION_BANK[skill]
            selected_questions = random.sample(available_questions, min(num_questions_per_skill, len(available_questions)))
            for q in selected_questions:
                questions_for_assessment.append({"skill": skill, "question": q["question"], "correct_answer": q["answer"]})
    return questions_for_assessment

if __name__ == "__main__":
    print("Questions for Python and SQL:")
    python_sql_questions = get_assessment_questions(["python", "sql"], num_questions_per_skill=2)
    for q in python_sql_questions:
        print(f"Skill: {q['skill']}\nQuestion: {q['question']}\nCorrect Answer: {q['correct_answer']}\n---")

    print("\nQuestions for a non-existent skill:")
    non_existent_questions = get_assessment_questions(["non_skill"], num_questions_per_skill=1)
    print(non_existent_questions)