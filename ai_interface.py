"""Async wrapper around Google Gemini with graceful fallbacks."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Dict, List

import httpx

from content_generator import (
    answer_question_locally,
    generate_local_exercises,
    generate_local_lesson,
)

LOGGER = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_ENDPOINT = os.getenv(
    "GEMINI_API_ENDPOINT",
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
)
TIMEOUT = 30.0


async def _request_from_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            GEMINI_ENDPOINT,
            params={"key": GEMINI_API_KEY},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates") or []
    for candidate in candidates:
        parts = candidate.get("content", {}).get("parts", [])
        for part in parts:
            text = part.get("text")
            if text:
                return text
    raise RuntimeError("Gemini response did not include any text.")


async def generate_lesson(subject: str, grade: int, topic: str) -> str:
    prompt = (
        "You are a friendly elementary school teacher. "
        f"Create a concise lesson for grade {grade} {subject} learners about {topic}. "
        "Use inviting language, short paragraphs, and include one practical activity suggestion."
    )
    try:
        lesson_text = await _request_from_gemini(prompt)
        return lesson_text.strip()
    except Exception as exc:  # pragma: no cover - best effort logging
        LOGGER.warning("Falling back to local lesson for %s grade %s: %s", subject, grade, exc)
        return generate_local_lesson(subject, grade, topic)


async def generate_exercises(subject: str, grade: int, topic: str) -> List[Dict[str, str]]:
    prompt = (
        "Create three short practice questions for grade {grade} students in {subject} about {topic}. "
        "Respond with a JSON list where each item has keys 'question', 'expected_answer', and 'hint'."
    ).format(grade=grade, subject=subject, topic=topic)
    try:
        response_text = await _request_from_gemini(prompt)
        exercises = json.loads(response_text)
        if not isinstance(exercises, list):
            raise ValueError("Gemini exercise response must be a list")
        parsed: List[Dict[str, str]] = []
        for exercise in exercises:
            if not isinstance(exercise, dict):
                raise ValueError("Exercise entry must be a dict")
            question = str(exercise.get("question", "")).strip()
            answer = str(exercise.get("expected_answer", "")).strip()
            hint = str(exercise.get("hint", "Use clues from the lesson."))
            if question:
                parsed.append({"question": question, "expected_answer": answer, "hint": hint})
        if parsed:
            return parsed
        raise ValueError("No valid exercises returned")
    except Exception as exc:  # pragma: no cover - best effort logging
        LOGGER.warning("Falling back to local exercises for %s grade %s: %s", subject, grade, exc)
        return generate_local_exercises(subject, grade, topic)


async def answer_question(question: str, lesson_context: str, student_answer: str) -> str:
    prompt = (
        "You are an encouraging tutor. A student answered a question incorrectly. "
        "Provide gentle feedback using the lesson summary and student response.\n"
        f"Lesson summary: {lesson_context}\n"
        f"Question: {question}\n"
        f"Student answer: {student_answer}\n"
        "Respond with two short sentences offering guidance."
    )
    try:
        return (await _request_from_gemini(prompt)).strip()
    except Exception as exc:  # pragma: no cover - best effort logging
        LOGGER.warning("Falling back to local answer helper: %s", exc)
        return answer_question_locally(question, lesson_context)


def generate_lesson_sync(subject: str, grade: int, topic: str) -> str:
    return asyncio.run(generate_lesson(subject, grade, topic))


def generate_exercises_sync(subject: str, grade: int, topic: str) -> List[Dict[str, str]]:
    return asyncio.run(generate_exercises(subject, grade, topic))


def answer_question_sync(question: str, lesson_context: str, student_answer: str) -> str:
    return asyncio.run(answer_question(question, lesson_context, student_answer))
