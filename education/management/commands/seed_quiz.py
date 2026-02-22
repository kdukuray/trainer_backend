"""
Management command to populate the database with quiz questions.

Usage:
    uv run python manage.py seed_quiz
"""

from django.core.management.base import BaseCommand

from education.models import QuizQuestion

QUESTIONS = [
    {
        "question_text": "What is progressive overload?",
        "options": [
            "Doing the same workout every day",
            "Gradually increasing the stress placed on the body during training",
            "Lifting the heaviest weight possible on day one",
            "Switching exercises every session",
        ],
        "correct_answer_index": 1,
        "explanation": "Progressive overload means gradually increasing weight, reps, or intensity over time to continually challenge your muscles and drive adaptation.",
    },
    {
        "question_text": "Which of the following is a compound exercise?",
        "options": [
            "Bicep curl",
            "Leg extension",
            "Squat",
            "Calf raise",
        ],
        "correct_answer_index": 2,
        "explanation": "Squats engage multiple joints (hip, knee, ankle) and muscle groups simultaneously, making them a compound exercise.",
    },
    {
        "question_text": "What is the primary role of protein in fitness?",
        "options": [
            "Providing quick energy during workouts",
            "Building and repairing muscle tissue",
            "Storing body fat",
            "Improving flexibility",
        ],
        "correct_answer_index": 1,
        "explanation": "Protein provides amino acids that are essential for muscle protein synthesis — the process of building and repairing muscle fibers after training.",
    },
    {
        "question_text": "How should you breathe during a heavy lift?",
        "options": [
            "Hold your breath the entire time",
            "Inhale during the exertion phase",
            "Exhale during the exertion (concentric) phase",
            "Breathe as fast as possible",
        ],
        "correct_answer_index": 2,
        "explanation": "Exhaling during the concentric (lifting) phase helps maintain core stability and blood pressure regulation.",
    },
    {
        "question_text": "What rep range is generally best for muscle hypertrophy?",
        "options": [
            "1-3 reps",
            "6-12 reps",
            "15-20 reps",
            "25-30 reps",
        ],
        "correct_answer_index": 1,
        "explanation": "The 6-12 rep range is widely regarded as optimal for hypertrophy because it balances mechanical tension and metabolic stress.",
    },
    {
        "question_text": "Why is warming up before exercise important?",
        "options": [
            "It burns the most calories",
            "It increases blood flow to muscles and reduces injury risk",
            "It is only necessary for beginners",
            "It replaces stretching entirely",
        ],
        "correct_answer_index": 1,
        "explanation": "Warming up raises muscle temperature, increases blood flow, and prepares joints for the range of motion required, reducing the risk of strains and tears.",
    },
    {
        "question_text": "Which macronutrient is the body's preferred energy source during high-intensity exercise?",
        "options": [
            "Protein",
            "Fat",
            "Carbohydrates",
            "Fiber",
        ],
        "correct_answer_index": 2,
        "explanation": "Carbohydrates are stored as glycogen in muscles and the liver, providing rapid fuel for high-intensity activities.",
    },
    {
        "question_text": "How long should you typically rest between sets for strength training?",
        "options": [
            "10-15 seconds",
            "30-60 seconds",
            "2-5 minutes",
            "10+ minutes",
        ],
        "correct_answer_index": 2,
        "explanation": "For pure strength work (heavy loads, low reps), 2-5 minutes of rest allows the phosphagen energy system to recover for maximal effort.",
    },
    {
        "question_text": "What does DOMS stand for?",
        "options": [
            "Delayed Onset Muscle Soreness",
            "Direct Overload Muscle Syndrome",
            "Daily Optimal Movement Standard",
            "Dynamic Oxygen Muscle Supply",
        ],
        "correct_answer_index": 0,
        "explanation": "DOMS is the muscle soreness that appears 24-72 hours after intense or unfamiliar exercise, caused by micro-damage to muscle fibers.",
    },
    {
        "question_text": "Which muscle group does the bench press primarily target?",
        "options": [
            "Biceps",
            "Quadriceps",
            "Pectorals (chest)",
            "Trapezius",
        ],
        "correct_answer_index": 2,
        "explanation": "The bench press is a horizontal pushing movement that primarily works the pectoralis major, with secondary engagement of the anterior deltoids and triceps.",
    },
    {
        "question_text": "What is a good daily water intake guideline for active individuals?",
        "options": [
            "1-2 glasses",
            "At least 2-3 liters (8-12 cups)",
            "Only drink when thirsty",
            "5+ liters minimum",
        ],
        "correct_answer_index": 1,
        "explanation": "Active individuals should aim for 2-3 liters of water daily, adjusting upward based on exercise intensity, climate, and sweat rate.",
    },
    {
        "question_text": "What is the most common push-up form mistake?",
        "options": [
            "Hands too close together",
            "Elbows flaring out excessively",
            "Going too slow",
            "Breathing too loudly",
        ],
        "correct_answer_index": 1,
        "explanation": "Excessive elbow flare puts undue stress on the shoulder joint. Keeping elbows at roughly 45° to the body is generally safer.",
    },
    {
        "question_text": "What is a 'caloric surplus'?",
        "options": [
            "Eating fewer calories than you burn",
            "Eating exactly as many calories as you burn",
            "Eating more calories than you burn",
            "Skipping meals to save calories",
        ],
        "correct_answer_index": 2,
        "explanation": "A caloric surplus means consuming more energy than your body expends, which is necessary for gaining muscle mass (bulking).",
    },
    {
        "question_text": "Which type of exercise is best for improving cardiovascular endurance?",
        "options": [
            "Heavy deadlifts",
            "Aerobic activities like running or cycling",
            "Static stretching",
            "One-rep max attempts",
        ],
        "correct_answer_index": 1,
        "explanation": "Aerobic (cardio) exercises like running, cycling, or swimming train the heart and lungs to deliver oxygen more efficiently.",
    },
    {
        "question_text": "What is the benefit of tracking your workouts?",
        "options": [
            "It looks cool on social media",
            "It helps monitor progress and ensure progressive overload",
            "It is only useful for professional athletes",
            "There is no real benefit",
        ],
        "correct_answer_index": 1,
        "explanation": "Tracking workouts lets you monitor progress, identify plateaus, and systematically apply progressive overload to keep improving.",
    },
]


class Command(BaseCommand):
    help = "Seed the database with quiz questions for the knowledge assessment."

    def handle(self, *args, **options):
        """Insert or update all quiz questions."""
        created_count = 0
        for q_data in QUESTIONS:
            _, created = QuizQuestion.objects.update_or_create(
                question_text=q_data["question_text"],
                defaults={
                    "options": q_data["options"],
                    "correct_answer_index": q_data["correct_answer_index"],
                    "explanation": q_data["explanation"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(QUESTIONS)} quiz questions ({created_count} new)."
            )
        )
