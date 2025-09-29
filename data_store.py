"""Utilities for persisting student progress to disk."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict


DEFAULT_DATA_DIR = "data"


@dataclass
class StudentProgress:
    """Simple structure describing the student's progress."""

    student_id: str
    completed_lessons: list
    completed_tests: list

    @classmethod
    def from_dict(cls, payload: Dict[str, Any], student_id: str) -> "StudentProgress":
        return cls(
            student_id=student_id,
            completed_lessons=payload.get("completed_lessons", []),
            completed_tests=payload.get("completed_tests", []),
        )


def _progress_path(student_id: str, data_dir: str = DEFAULT_DATA_DIR) -> str:
    os.makedirs(data_dir, exist_ok=True)
    safe_id = student_id.replace(os.sep, "_")
    return os.path.join(data_dir, f"{safe_id}.json")


def save_progress(progress: StudentProgress, data_dir: str = DEFAULT_DATA_DIR) -> None:
    """Persist ``progress`` to disk in a JSON file."""

    path = _progress_path(progress.student_id, data_dir=data_dir)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(asdict(progress), handle, indent=2, sort_keys=True)


def load_progress(student_id: str, data_dir: str = DEFAULT_DATA_DIR) -> StudentProgress:
    """Load progress for ``student_id`` from disk.

    If the student has no stored progress yet this will return an empty
    :class:`StudentProgress` instance.
    """

    path = _progress_path(student_id, data_dir=data_dir)
    if not os.path.exists(path):
        return StudentProgress(student_id=student_id, completed_lessons=[], completed_tests=[])

    with open(path, "r", encoding="utf-8") as handle:
        payload: Dict[str, Any] = json.load(handle)

    return StudentProgress.from_dict(payload, student_id=student_id)
