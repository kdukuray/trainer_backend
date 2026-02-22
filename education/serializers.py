"""Serializers for quiz questions, flashcards, and quiz results."""

from rest_framework import serializers

from .models import FlashCard, QuizQuestion, UserQuizResult


class QuizQuestionSerializer(serializers.ModelSerializer):
    """
    Public serializer for quiz questions.
    Excludes ``correct_answer_index`` so the client cannot cheat.
    """

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_text", "options"]


class QuizQuestionWithAnswerSerializer(serializers.ModelSerializer):
    """Full serializer including the correct answer — used in result review."""

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_text", "options", "correct_answer_index", "explanation"]


class FlashCardSerializer(serializers.ModelSerializer):
    """Serializes flashcard content for the swipeable deck."""

    class Meta:
        model = FlashCard
        fields = ["id", "knowledge_level", "category", "front_text", "back_text"]


class UserQuizResultSerializer(serializers.ModelSerializer):
    """Read-only serializer for past quiz attempts."""

    class Meta:
        model = UserQuizResult
        fields = ["id", "score", "total_questions", "assigned_rank", "taken_at"]
        read_only_fields = fields
