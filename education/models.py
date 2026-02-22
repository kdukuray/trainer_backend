"""
Education models for the knowledge quiz and flashcard system.

QuizQuestion and FlashCard are pre-populated via management commands.
UserQuizResult records each attempt so users can retake and improve.
"""

from django.db import models


class QuizQuestion(models.Model):
    """
    A single multiple-choice question shown to every user during the
    knowledge assessment. Pre-seeded by the ``seed_quiz`` command.
    """

    question_text = models.TextField()
    options = models.JSONField(
        help_text='Ordered list of four answer strings, e.g. ["A", "B", "C", "D"]'
    )
    correct_answer_index = models.IntegerField(
        help_text="Zero-based index into ``options`` for the correct answer"
    )
    explanation = models.TextField(
        blank=True,
        default="",
        help_text="Shown to the user after quiz completion",
    )

    def __str__(self) -> str:
        return self.question_text[:80]


class FlashCard(models.Model):
    """
    A flashcard tied to a specific knowledge level. The frontend shows
    cards whose ``knowledge_level`` matches the user's rank.
    """

    class Level(models.IntegerChoices):
        BEGINNER = 1, "Beginner"
        INTERMEDIATE = 2, "Intermediate"
        ADVANCED = 3, "Advanced"

    knowledge_level = models.IntegerField(choices=Level.choices)
    category = models.CharField(
        max_length=50,
        help_text='E.g. "Nutrition", "Training", "Recovery"',
    )
    front_text = models.TextField(help_text="The question or fact shown first")
    back_text = models.TextField(help_text="The detailed explanation revealed on flip")

    def __str__(self) -> str:
        return f"[L{self.knowledge_level}] {self.front_text[:60]}"


class UserQuizResult(models.Model):
    """
    Records one quiz attempt, including the score and the rank it yielded.
    Allows users to retake and track improvement over time.
    """

    user_id = models.CharField(max_length=255, db_index=True)
    score = models.IntegerField(help_text="Number of correct answers")
    total_questions = models.IntegerField()
    assigned_rank = models.IntegerField(
        help_text="1=Beginner, 2=Intermediate, 3=Advanced"
    )
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-taken_at"]

    def __str__(self) -> str:
        return f"{self.user_id} — {self.score}/{self.total_questions}"
