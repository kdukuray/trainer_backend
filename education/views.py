"""
Education endpoints: quiz delivery, submission, and flashcard retrieval.

The quiz is the same set of questions for every user. Submitting answers
calculates a score, assigns a knowledge rank, and persists the result.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import UserProfile

from .models import FlashCard, QuizQuestion, UserQuizResult
from .serializers import (
    FlashCardSerializer,
    QuizQuestionSerializer,
    QuizQuestionWithAnswerSerializer,
    UserQuizResultSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_quiz_questions(request):
    """
    Return all quiz questions without revealing correct answers.

    Returns:
        200: List of QuizQuestion objects (id, question_text, options).
    """
    questions = QuizQuestion.objects.all().order_by("id")
    serializer = QuizQuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_quiz(request):
    """
    Grade a completed quiz and assign a knowledge rank.

    Parameters:
        request.data.answers: List of integers — the user's chosen option
                              index for each question, in question-id order.

    Returns:
        200: { score, total, rank, questions } where questions includes
             correct answers and explanations for review.
    """
    answers = request.data.get("answers", [])
    questions = list(QuizQuestion.objects.all().order_by("id"))

    if len(answers) != len(questions):
        return Response(
            {"error": f"Expected {len(questions)} answers, got {len(answers)}."},
            status=400,
        )

    # Grade
    correct_count = sum(
        1
        for question, answer in zip(questions, answers)
        if int(answer) == question.correct_answer_index
    )
    total = len(questions)
    percentage = (correct_count / total * 100) if total > 0 else 0

    # Determine rank: Beginner 0-40%, Intermediate 41-70%, Advanced 71-100%
    if percentage <= 40:
        assigned_rank = 1
    elif percentage <= 70:
        assigned_rank = 2
    else:
        assigned_rank = 3

    # Persist result
    result = UserQuizResult.objects.create(
        user_id=request.user.id,
        score=correct_count,
        total_questions=total,
        assigned_rank=assigned_rank,
    )

    # Update the user profile rank
    profile, _ = UserProfile.objects.get_or_create(
        user_id=request.user.id,
        defaults={"email": request.user.email},
    )
    profile.knowledge_rank = assigned_rank
    profile.save(update_fields=["knowledge_rank"])

    # Return full questions with answers for review
    questions_serializer = QuizQuestionWithAnswerSerializer(questions, many=True)
    result_serializer = UserQuizResultSerializer(result)

    return Response(
        {
            "result": result_serializer.data,
            "questions": questions_serializer.data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_flashcards(request):
    """
    Return flashcards matching the user's current knowledge rank.

    Falls back to beginner cards if the user has no rank yet.

    Returns:
        200: List of FlashCard objects.
    """
    profile, _ = UserProfile.objects.get_or_create(
        user_id=request.user.id,
        defaults={"email": request.user.email},
    )

    # Users who haven't taken the quiz (rank=0) see beginner content
    rank = profile.knowledge_rank if profile.knowledge_rank > 0 else 1

    # Return cards up to and including the user's level so they also review basics
    cards = FlashCard.objects.filter(knowledge_level__lte=rank).order_by("?")
    serializer = FlashCardSerializer(cards, many=True)
    return Response(serializer.data)
