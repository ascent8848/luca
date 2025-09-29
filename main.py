"""Entry point for the Luca learning assistant."""

from __future__ import annotations

import logging
import sys
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import ai_interface
import content_generator
from data_store import StudentProgress, load_progress, save_progress

try:  # Optional mini-game import
    from games.labyrinth_game import run_labyrinth_game
except Exception:  # pragma: no cover - pygame may be missing
    run_labyrinth_game = None


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class IntroPage(QWidget):
    started = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Welcome to Luca!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold;")

        subtitle = QLabel("An AI-assisted learning companion.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px;")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter student name")
        self.name_input.setFixedWidth(240)
        self.name_input.setMaxLength(32)

        start_button = QPushButton("Start Learning")
        start_button.clicked.connect(self._handle_start_clicked)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.name_input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _handle_start_clicked(self) -> None:
        student_name = self.name_input.text().strip() or "student"
        self.started.emit(student_name)


class LessonListPage(QWidget):
    lesson_selected = pyqtSignal(str, int, str)
    progress_requested = pyqtSignal()
    launch_game_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        header = QLabel("Choose what to explore")
        header.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(header)

        self.grade_combo = QComboBox()
        self.grade_combo.addItem("Select grade", userData=None)
        for grade in content_generator.get_available_grades():
            self.grade_combo.addItem(f"Grade {grade}", userData=grade)
        self.grade_combo.currentIndexChanged.connect(self._update_subjects)

        self.subject_combo = QComboBox()
        self.subject_combo.addItem("Select subject", userData=None)
        self.subject_combo.currentIndexChanged.connect(self._update_topics)

        self.topic_list = QListWidget()

        start_lesson_btn = QPushButton("Open Lesson")
        start_lesson_btn.clicked.connect(self._open_selected_lesson)

        progress_btn = QPushButton("View Progress")
        progress_btn.clicked.connect(self.progress_requested.emit)

        game_btn = QPushButton("Play Labyrinth Game")
        game_btn.clicked.connect(self.launch_game_requested.emit)
        game_btn.setEnabled(run_labyrinth_game is not None)

        layout.addWidget(self.grade_combo)
        layout.addWidget(self.subject_combo)
        layout.addWidget(QLabel("Topics"))
        layout.addWidget(self.topic_list)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(start_lesson_btn)
        buttons_row.addWidget(progress_btn)
        buttons_row.addWidget(game_btn)
        layout.addLayout(buttons_row)

    def _update_subjects(self) -> None:
        grade = self.grade_combo.currentData()
        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        self.subject_combo.addItem("Select subject", userData=None)
        if grade is not None:
            for subject in content_generator.get_subjects_for_grade(grade):
                self.subject_combo.addItem(subject, userData=subject)
        self.subject_combo.blockSignals(False)
        self._update_topics()

    def _update_topics(self) -> None:
        self.topic_list.clear()
        grade = self.grade_combo.currentData()
        subject = self.subject_combo.currentData()
        if grade is None or subject is None:
            return
        for topic in content_generator.get_topics(subject, grade):
            QListWidgetItem(topic, self.topic_list)

    def _open_selected_lesson(self) -> None:
        grade = self.grade_combo.currentData()
        subject = self.subject_combo.currentData()
        topic_item = self.topic_list.currentItem()
        if grade is None or subject is None or topic_item is None:
            QMessageBox.information(self, "Select a topic", "Please choose a grade, subject, and topic first.")
            return
        topic = topic_item.text()
        self.lesson_selected.emit(subject, grade, topic)


class LessonPage(QWidget):
    go_back = pyqtSignal()
    start_test = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.title_label = QLabel("Lesson")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.lesson_text = QTextEdit()
        self.lesson_text.setReadOnly(True)
        self.lesson_text.setStyleSheet("font-size: 16px;")

        button_row = QHBoxLayout()
        back_btn = QPushButton("Back to list")
        back_btn.clicked.connect(self.go_back.emit)
        test_btn = QPushButton("Try quick quiz")
        test_btn.clicked.connect(self.start_test.emit)

        button_row.addWidget(back_btn)
        button_row.addWidget(test_btn)

        layout.addWidget(self.title_label)
        layout.addWidget(self.lesson_text)
        layout.addLayout(button_row)

    def display_lesson(self, subject: str, topic: str, text: str) -> None:
        self.title_label.setText(f"{subject} – {topic}")
        self.lesson_text.setPlainText(text)


class TestPage(QWidget):
    back_requested = pyqtSignal()
    test_completed = pyqtSignal(int, int)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.header = QLabel("Quick quiz")
        self.header.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #666; font-style: italic;")

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Type your answer here")

        self.feedback_box = QTextEdit()
        self.feedback_box.setReadOnly(True)
        self.feedback_box.setFixedHeight(100)

        submit_btn = QPushButton("Submit answer")
        submit_btn.clicked.connect(self._handle_submit)

        next_btn = QPushButton("Next question")
        next_btn.clicked.connect(self._handle_next)

        back_btn = QPushButton("Back to lesson")
        back_btn.clicked.connect(self.back_requested.emit)

        button_row = QHBoxLayout()
        button_row.addWidget(submit_btn)
        button_row.addWidget(next_btn)
        button_row.addWidget(back_btn)

        layout.addWidget(self.header)
        layout.addWidget(self.question_label)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.feedback_box)
        layout.addLayout(button_row)

        self._exercises: List[Dict[str, str]] = []
        self._index = 0
        self._score = 0
        self._lesson_context = ""

    def load_exercises(self, exercises: List[Dict[str, str]], lesson_context: str) -> None:
        self._exercises = exercises
        self._index = 0
        self._score = 0
        self._lesson_context = lesson_context
        self.feedback_box.clear()
        self.answer_input.clear()
        self._display_current_question()

    def _display_current_question(self) -> None:
        if not self._exercises:
            self.question_label.setText("No exercises available.")
            self.hint_label.clear()
            return
        exercise = self._exercises[self._index]
        self.question_label.setText(exercise["question"])
        self.hint_label.setText(f"Hint: {exercise.get('hint', 'Consider the lesson content.')}")
        self.answer_input.clear()
        self.feedback_box.clear()

    def _handle_submit(self) -> None:
        if not self._exercises:
            return
        exercise = self._exercises[self._index]
        student_answer = self.answer_input.text().strip()
        expected = exercise.get("expected_answer", "").strip()
        correct = bool(expected) and student_answer.lower() == expected.lower()
        if correct:
            self.feedback_box.setPlainText("Great job! That's correct.")
            self._score += 1
        else:
            feedback = ai_interface.answer_question_sync(
                exercise["question"], self._lesson_context, student_answer
            )
            self.feedback_box.setPlainText(feedback)
        self.answer_input.clear()

    def _handle_next(self) -> None:
        if not self._exercises:
            self.back_requested.emit()
            return
        if self._index < len(self._exercises) - 1:
            self._index += 1
            self._display_current_question()
        else:
            total = len(self._exercises)
            self.test_completed.emit(self._score, total)


class ProgressPage(QWidget):
    back_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        header = QLabel("Progress tracker")
        header.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_requested.emit)

        layout.addWidget(header)
        layout.addWidget(self.summary_box)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def display_progress(self, progress: StudentProgress) -> None:
        lessons_lines = [
            f"• {item['subject']} grade {item['grade']} – {item['topic']}"
            for item in progress.completed_lessons
        ]
        tests_lines = [
            f"• {item['subject']} grade {item['grade']} – {item['topic']} (score {item['score']}/{item['total']})"
            for item in progress.completed_tests
        ]
        summary = [
            f"Student: {progress.student_id}",
            "",
            "Completed lessons:",
            *(lessons_lines or ["  No lessons completed yet."]),
            "",
            "Quiz history:",
            *(tests_lines or ["  No quizzes taken yet."]),
        ]
        self.summary_box.setPlainText("\n".join(summary))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Luca Learning Companion")
        self.resize(900, 600)

        self.student_id = "student"
        self.progress = StudentProgress(student_id=self.student_id, completed_lessons=[], completed_tests=[])
        self.current_subject: Optional[str] = None
        self.current_topic: Optional[str] = None
        self.current_grade: Optional[int] = None
        self.current_lesson_text = ""

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.intro_page = IntroPage()
        self.lesson_list_page = LessonListPage()
        self.lesson_page = LessonPage()
        self.test_page = TestPage()
        self.progress_page = ProgressPage()

        self.stacked_widget.addWidget(self.intro_page)
        self.stacked_widget.addWidget(self.lesson_list_page)
        self.stacked_widget.addWidget(self.lesson_page)
        self.stacked_widget.addWidget(self.test_page)
        self.stacked_widget.addWidget(self.progress_page)

        self.intro_page.started.connect(self._on_intro_started)
        self.lesson_list_page.lesson_selected.connect(self._open_lesson)
        self.lesson_list_page.progress_requested.connect(self._show_progress)
        self.lesson_list_page.launch_game_requested.connect(self._launch_game)
        self.lesson_page.go_back.connect(self._show_lesson_list)
        self.lesson_page.start_test.connect(self._start_test)
        self.test_page.back_requested.connect(self._show_lesson_list)
        self.test_page.test_completed.connect(self._record_test)
        self.progress_page.back_requested.connect(self._show_lesson_list)

    # Navigation helpers -------------------------------------------------

    def _on_intro_started(self, student_name: str) -> None:
        self.student_id = student_name
        self.progress = load_progress(student_name)
        self.lesson_list_page._update_subjects()  # Ensure combos refresh
        self._show_lesson_list()

    def _show_lesson_list(self) -> None:
        self.stacked_widget.setCurrentWidget(self.lesson_list_page)

    def _show_progress(self) -> None:
        self.progress_page.display_progress(self.progress)
        self.stacked_widget.setCurrentWidget(self.progress_page)

    def _open_lesson(self, subject: str, grade: int, topic: str) -> None:
        self.current_subject = subject
        self.current_grade = grade
        self.current_topic = topic

        lesson_text = ai_interface.generate_lesson_sync(subject, grade, topic)
        self.current_lesson_text = lesson_text

        self.lesson_page.display_lesson(subject, topic, lesson_text)
        self.stacked_widget.setCurrentWidget(self.lesson_page)

        # Update lesson progress if not already recorded
        lesson_entry = {
            "subject": subject,
            "grade": grade,
            "topic": topic,
        }
        if lesson_entry not in self.progress.completed_lessons:
            self.progress.completed_lessons.append(lesson_entry)
            self._persist_progress()

    def _start_test(self) -> None:
        if not (self.current_subject and self.current_grade and self.current_topic):
            QMessageBox.information(self, "Pick a lesson first", "Choose a lesson before attempting the quiz.")
            return
        exercises = ai_interface.generate_exercises_sync(
            self.current_subject, self.current_grade, self.current_topic
        )
        if not exercises:
            QMessageBox.warning(self, "No exercises", "We could not load a quiz for this topic right now.")
            return
        self.test_page.load_exercises(exercises, self.current_lesson_text)
        self.stacked_widget.setCurrentWidget(self.test_page)

    def _record_test(self, score: int, total: int) -> None:
        if not (self.current_subject and self.current_grade and self.current_topic):
            self._show_lesson_list()
            return
        QMessageBox.information(self, "Quiz complete", f"You scored {score} out of {total}.")
        test_entry = {
            "subject": self.current_subject,
            "grade": self.current_grade,
            "topic": self.current_topic,
            "score": score,
            "total": total,
        }
        self.progress.completed_tests.append(test_entry)
        self._persist_progress()
        self._show_lesson_list()

    def _persist_progress(self) -> None:
        try:
            save_progress(self.progress)
        except Exception as exc:  # pragma: no cover - disk issues
            LOGGER.error("Failed to save progress: %s", exc)

    def _launch_game(self) -> None:
        if run_labyrinth_game is None:
            QMessageBox.information(self, "Game unavailable", "The labyrinth game is not installed.")
            return
        try:
            run_labyrinth_game()
        except Exception as exc:  # pragma: no cover - runtime issues
            QMessageBox.warning(self, "Game error", str(exc))


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover - manual run helper
    sys.exit(main())
