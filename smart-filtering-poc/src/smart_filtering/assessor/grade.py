# src/assessor/grade.py

from typing import Dict, Any, List
import random
import re
import json

def grade_answer(question_data: Dict[str, Any], candidate_answer: str) -> float:
    """
    Simulates grading a candidate's answer against a predefined correct answer.
    Returns a score between 0 and 100.
    For POC, this uses a simplified keyword matching approach.
    """
    correct_answer = question_data["correct_answer"].lower()
    candidate_answer_lower = candidate_answer.lower()

    score = 0.0
    
    # Simple keyword matching: check if key terms from the correct answer are in the candidate's answer
    # This is a very basic simulation; a real system would use NLP techniques (e.g., semantic similarity)
    keywords = re.findall(r'\b\w+\b', correct_answer) # Extract words
    
    matched_keywords = 0
    for keyword in keywords:
        if len(keyword) > 3 and keyword in candidate_answer_lower: # Ignore very short words
            matched_keywords += 1
            
    if len(keywords) > 0:
        match_ratio = matched_keywords / len(keywords)
        score = match_ratio * 100
    
    # Add some randomness to simulate human grading or partial understanding
    score = max(0, min(100, score + random.uniform(-10, 10)))
    
    return round(score, 2)

def calculate_assessment_score(assessment_questions: List[Dict[str, Any]], candidate_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculates the overall assessment score for a candidate based on their answers.
    """
    total_score = 0.0
    graded_questions = []
    
    for q_data in assessment_questions:
        question_text = q_data["question"]
        skill = q_data["skill"]
        
        # Simulate candidate answer (for POC, just a random choice or partial match)
        # In a real scenario, candidate_answers would come from user input
        simulated_candidate_answer = candidate_answers.get(question_text, "")
        
        if not simulated_candidate_answer:
            # If no answer provided, simulate a poor answer
            simulated_candidate_answer = random.choice([
                "No estoy seguro de la respuesta.",
                "Es una pregunta interesante, pero no tengo la información exacta.",
                "Creo que se refiere a algo relacionado con " + skill + ".",
                q_data["correct_answer"][:len(q_data["correct_answer"]) // 2] # Partial answer
            ])
            if random.random() < 0.3: # 30% chance of a good simulated answer
                simulated_candidate_answer = q_data["correct_answer"]

        question_score = grade_answer(q_data, simulated_candidate_answer)
        total_score += question_score
        graded_questions.append({
            "skill": skill,
            "question": question_text,
            "correct_answer": q_data["correct_answer"],
            "candidate_answer": simulated_candidate_answer,
            "score": question_score
        })
        
    if assessment_questions:
        average_score = total_score / len(assessment_questions)
    else:
        average_score = 0.0
        
    return {
        "overall_assessment_score": round(average_score, 2),
        "graded_questions": graded_questions
    }

if __name__ == "__main__":
    from smart_filtering.assessor.questions import get_assessment_questions

    # Example usage
    skills_to_assess = ["python", "sql"]
    assessment_q = get_assessment_questions(skills_to_assess, num_questions_per_skill=1)

    # Simulate candidate answers
    mock_candidate_answers = {
        "¿Qué es un decorador en Python?": "Un decorador es una función que modifica el comportamiento de otra función.",
        "¿Qué es una JOIN en SQL y cuáles son sus tipos principales?": "Una JOIN combina tablas. Los tipos son INNER, LEFT, RIGHT y FULL."
    }

    assessment_results = calculate_assessment_score(assessment_q, mock_candidate_answers)
    print(json.dumps(assessment_results, indent=2))

    # Example with some missing answers (will be simulated)
    print("\n--- Assessment with some missing answers ---")
    mock_candidate_answers_partial = {
        "¿Qué es un decorador en Python?": "Un decorador es una función que modifica el comportamiento de otra función."
    }
    assessment_results_partial = calculate_assessment_score(assessment_q, mock_candidate_answers_partial)
    print(json.dumps(assessment_results_partial, indent=2))
