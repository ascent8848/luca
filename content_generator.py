"""Local content generator used as a deterministic fallback when the AI service
is not available."""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

# Seed the random number generator to keep exercise order consistent between
# runs.  This makes behaviour more predictable for tests while still providing
# some variety when the module is expanded in the future.
random.seed(1234)


LOCAL_CONTENT: Dict[str, Dict[int, Dict[str, Dict[str, str]]]] = {
    "Mathematics": {
        3: {
            "Fractions": {
                "lesson": (
                    "Fractions represent equal parts of a whole. When we write "
                    "a fraction like 1/2, the number on top (the numerator) "
                    "tells us how many parts we have and the number on the bottom "
                    "(the denominator) tells us how many equal parts the whole is "
                    "divided into."
                ),
                "concept": "Understanding halves, thirds, and quarters of shapes and groups.",
            },
            "Multiplication": {
                "lesson": (
                    "Multiplication is repeated addition. To find 3 × 4, add 4 "
                    "three times (4 + 4 + 4 = 12). Arrays and equal groups help "
                    "us visualise multiplication problems."
                ),
                "concept": "Building fluency with times tables up to 5.",
            },
        },
        4: {
            "Decimals": {
                "lesson": (
                    "Decimals are another way to write fractions. 0.5 is the same "
                    "as 1/2 because it represents 5 tenths. Each place to the "
                    "right of the decimal point is worth ten times less than the "
                    "place before it."
                ),
                "concept": "Linking tenths and hundredths to place value charts.",
            }
        },
    },
    "Science": {
        3: {
            "Life Cycles": {
                "lesson": (
                    "Plants and animals go through life cycles. A butterfly starts "
                    "as an egg, becomes a caterpillar, forms a chrysalis, and "
                    "emerges as an adult butterfly. Each stage has a special job."
                ),
                "concept": "Recognising patterns in living things.",
            }
        },
        4: {
            "Energy": {
                "lesson": (
                    "Energy is the ability to do work. It can take many forms "
                    "such as light, heat, and movement. Energy can change from "
                    "one form to another, like when electricity powers a lamp."
                ),
                "concept": "Observing energy transfers in everyday situations.",
            }
        },
    },
}


def get_available_grades() -> List[int]:
    grades = set()
    for subject in LOCAL_CONTENT.values():
        grades.update(subject.keys())
    return sorted(grades)


def get_subjects_for_grade(grade: int) -> List[str]:
    return sorted(
        subject
        for subject, grade_data in LOCAL_CONTENT.items()
        if grade in grade_data
    )


def get_topics(subject: str, grade: int) -> List[str]:
    subject_data = LOCAL_CONTENT.get(subject, {})
    return sorted(subject_data.get(grade, {}).keys())


def _select_content(subject: str, grade: int, topic: str) -> Dict[str, str]:
    subject_data = LOCAL_CONTENT.get(subject, {})
    grade_data = subject_data.get(grade, {})
    content = grade_data.get(topic)
    if not content:
        raise KeyError(f"No local content for {subject} grade {grade} topic {topic}.")
    return content


def generate_local_lesson(subject: str, grade: int, topic: str) -> str:
    content = _select_content(subject, grade, topic)
    return (
        f"Lesson Topic: {topic}\n"
        f"Grade Level: {grade}\n"
        f"Subject: {subject}\n\n"
        f"Big Idea: {content['concept']}\n\n"
        f"Key Learning:\n{content['lesson']}\n\n"
        "Try sketching or acting out the idea to help it stick!"
    )


def generate_local_exercises(subject: str, grade: int, topic: str) -> List[Dict[str, str]]:
    content = _select_content(subject, grade, topic)
    concept = content["concept"]
    base_questions: List[Tuple[str, str]] = [
        (f"Explain the main idea of {topic.lower()} in your own words.", concept),
        (f"Give a real-life example related to {topic.lower()}.", concept),
    ]

    if subject == "Mathematics" and "fraction" in topic.lower():
        base_questions.append(("What fraction of a pizza is left if you eat 3 of 8 slices?", "5/8"))
    elif subject == "Mathematics" and "multiplication" in topic.lower():
        base_questions.append(("Solve 4 × 6.", "24"))
    elif subject == "Science" and "energy" in topic.lower():
        base_questions.append(("Name two forms of energy you use at school.", "light and sound"))

    random.shuffle(base_questions)
    return [
        {
            "question": question,
            "expected_answer": answer,
            "hint": f"Think about: {concept}",
        }
        for question, answer in base_questions
    ]


def answer_question_locally(question: str, context: str) -> str:
    question_lower = question.lower()
    if "fraction" in question_lower and "pizza" in question_lower:
        return "If 3 of 8 slices are eaten, 5/8 of the pizza remains."
    if "4 × 6" in question or "4 x 6" in question_lower:
        return "4 × 6 equals 24."
    if "energy" in question_lower:
        return "Common forms include light, sound, and heat energy."

    return (
        "Think back to the main idea of the lesson. Highlight key words in the "
        "question and match them to details from the lesson text."
    )
