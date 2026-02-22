"""
Management command to populate the database with flashcards for 3 levels.

Usage:
    uv run python manage.py seed_flashcards
"""

from django.core.management.base import BaseCommand

from education.models import FlashCard

CARDS = [
    # ── Level 1: Beginner ──────────────────────────────────────────────
    {"knowledge_level": 1, "category": "Training", "front_text": "What is a 'rep'?", "back_text": "A rep (repetition) is one complete movement of an exercise — for example, one full push-up from down to up."},
    {"knowledge_level": 1, "category": "Training", "front_text": "What is a 'set'?", "back_text": "A set is a group of consecutive reps. For example, doing 10 push-ups without rest is 1 set of 10 reps."},
    {"knowledge_level": 1, "category": "Training", "front_text": "Why warm up before lifting?", "back_text": "Warming up increases blood flow to your muscles, raises body temperature, and prepares your joints — all of which reduce injury risk."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "What are macronutrients?", "back_text": "Macronutrients are the three main nutrient categories your body needs in large amounts: protein, carbohydrates, and fats."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "Why is protein important for fitness?", "back_text": "Protein provides amino acids that repair and build muscle fibers damaged during exercise. Aim for ~0.7-1g per pound of body weight daily."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "What is a calorie?", "back_text": "A calorie is a unit of energy. Your body burns calories for all functions — from breathing to sprinting. Eating more than you burn leads to weight gain, and vice versa."},
    {"knowledge_level": 1, "category": "Recovery", "front_text": "How much sleep should you aim for?", "back_text": "Most adults need 7-9 hours of sleep per night. Sleep is when your body releases growth hormone and repairs muscle tissue."},
    {"knowledge_level": 1, "category": "Recovery", "front_text": "What is DOMS?", "back_text": "Delayed Onset Muscle Soreness — the stiffness you feel 24-72 hours after a tough workout. It's caused by micro-tears in muscle fibers and is a normal part of adaptation."},
    {"knowledge_level": 1, "category": "Training", "front_text": "What is proper push-up form?", "back_text": "Hands shoulder-width apart, body in a straight line from head to heels, elbows at ~45° to your body, and controlled movement up and down."},
    {"knowledge_level": 1, "category": "Training", "front_text": "What is a compound exercise?", "back_text": "An exercise that works multiple joints and muscle groups at once — like squats (knees + hips), bench press (shoulders + elbows), and pull-ups (shoulders + elbows)."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "How much water should you drink daily?", "back_text": "Aim for 2-3 liters (8-12 cups) per day. Increase intake during exercise and in hot weather."},
    {"knowledge_level": 1, "category": "Training", "front_text": "What does 'form' mean in exercise?", "back_text": "Form refers to the correct technique and body positioning during an exercise. Good form maximizes effectiveness and minimizes injury risk."},
    {"knowledge_level": 1, "category": "Recovery", "front_text": "Should you stretch after a workout?", "back_text": "Yes! Post-workout stretching helps reduce muscle tension, improves flexibility, and can decrease soreness."},
    {"knowledge_level": 1, "category": "Training", "front_text": "What are isolation exercises?", "back_text": "Exercises targeting a single muscle group through a single joint — like bicep curls (elbow only) or leg extensions (knee only)."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "What role do carbohydrates play?", "back_text": "Carbs are your body's preferred quick-energy fuel. They're stored as glycogen in muscles and liver, powering everything from walking to sprinting."},
    {"knowledge_level": 1, "category": "Training", "front_text": "How many days a week should a beginner train?", "back_text": "3-4 days per week is ideal for beginners. This allows enough training stimulus while giving muscles time to recover and grow."},
    {"knowledge_level": 1, "category": "Recovery", "front_text": "Why are rest days important?", "back_text": "Muscles grow during rest, not during the workout itself. Rest days allow repair, reduce overtraining risk, and prevent burnout."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "What is a caloric deficit?", "back_text": "Eating fewer calories than your body burns. This forces the body to use stored energy (fat), which leads to weight loss over time."},
    {"knowledge_level": 1, "category": "Training", "front_text": "What is the difference between free weights and machines?", "back_text": "Free weights (dumbbells, barbells) require you to stabilize the weight, building more functional strength. Machines guide the movement, making them safer for beginners."},
    {"knowledge_level": 1, "category": "Nutrition", "front_text": "Is fat bad for you?", "back_text": "No! Dietary fat is essential for hormone production, vitamin absorption, and brain function. Focus on healthy fats like avocado, nuts, and olive oil."},

    # ── Level 2: Intermediate ──────────────────────────────────────────
    {"knowledge_level": 2, "category": "Training", "front_text": "What is progressive overload?", "back_text": "The principle of gradually increasing training stress (weight, reps, sets, or intensity) over time to force continued adaptation and growth."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is a PPL split?", "back_text": "Push/Pull/Legs — a training split where you dedicate sessions to pushing movements (chest, shoulders, triceps), pulling movements (back, biceps), and legs respectively."},
    {"knowledge_level": 2, "category": "Nutrition", "front_text": "How do you calculate your TDEE?", "back_text": "Total Daily Energy Expenditure = BMR × Activity Multiplier. BMR is calculated using equations like Mifflin-St Jeor. TDEE is how many calories you burn daily."},
    {"knowledge_level": 2, "category": "Training", "front_text": "When should you deload?", "back_text": "Every 4-8 weeks of intense training, take a deload week at 50-60% of normal volume/intensity. This allows accumulated fatigue to dissipate and prevents overtraining."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is mind-muscle connection?", "back_text": "Consciously focusing on the target muscle during an exercise to maximize its activation. Research shows this can improve muscle engagement, especially for hypertrophy."},
    {"knowledge_level": 2, "category": "Nutrition", "front_text": "What is nutrient timing?", "back_text": "Strategically consuming nutrients around training. A meal with protein and carbs within 1-2 hours post-workout supports recovery, though total daily intake matters more."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is training volume?", "back_text": "Total work done — typically sets × reps × weight. For hypertrophy, 10-20 sets per muscle group per week is a common target."},
    {"knowledge_level": 2, "category": "Recovery", "front_text": "What is active recovery?", "back_text": "Low-intensity movement on rest days (walking, yoga, light swimming) that promotes blood flow and recovery without adding significant fatigue."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is the difference between strength and hypertrophy training?", "back_text": "Strength training uses heavier loads (1-5 reps) to maximize force production. Hypertrophy training uses moderate loads (6-12 reps) to maximize muscle size."},
    {"knowledge_level": 2, "category": "Nutrition", "front_text": "How much protein should you eat for muscle gain?", "back_text": "Aim for 1.6-2.2g per kg of body weight daily. Spread intake across 3-5 meals for optimal muscle protein synthesis."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is time under tension (TUT)?", "back_text": "The total time a muscle is under load during a set. Slowing the eccentric (lowering) phase to 3-4 seconds can increase hypertrophy stimulus."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What are supersets?", "back_text": "Performing two exercises back-to-back with no rest. Antagonist supersets (e.g., biceps + triceps) are time-efficient without much performance loss."},
    {"knowledge_level": 2, "category": "Nutrition", "front_text": "What are BCAAs and are they necessary?", "back_text": "Branched-Chain Amino Acids (leucine, isoleucine, valine) are found in protein-rich foods. Supplements are unnecessary if you're hitting your daily protein target through whole foods or whey."},
    {"knowledge_level": 2, "category": "Recovery", "front_text": "How does stress affect gains?", "back_text": "Chronic stress elevates cortisol, which can impair recovery, promote muscle breakdown, and increase fat storage. Managing stress through sleep, meditation, and balanced training is crucial."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is proper barbell squat depth?", "back_text": "Ideally, your hip crease should go below the top of your knee ('below parallel'). This ensures full quad, glute, and hamstring activation."},
    {"knowledge_level": 2, "category": "Training", "front_text": "Why is the eccentric phase important?", "back_text": "The eccentric (lowering) phase causes more micro-damage to muscle fibers, which is a key stimulus for growth. Controlling the eccentric also reduces injury risk."},
    {"knowledge_level": 2, "category": "Nutrition", "front_text": "What is a 'refeed' day?", "back_text": "A planned day of higher calorie/carb intake during a cut. It restores glycogen, boosts leptin, and provides a psychological break from dieting."},
    {"knowledge_level": 2, "category": "Training", "front_text": "How do you prevent plateaus?", "back_text": "Vary your training stimulus: change rep ranges, exercise selection, rest periods, or use intensity techniques like drop sets, pauses, or tempos."},
    {"knowledge_level": 2, "category": "Recovery", "front_text": "What is foam rolling and does it help?", "back_text": "Self-myofascial release using a foam roller. It can temporarily increase range of motion and reduce soreness, making it a useful recovery tool."},
    {"knowledge_level": 2, "category": "Training", "front_text": "What is the Valsalva maneuver?", "back_text": "A breathing technique where you take a deep breath and brace your core before a heavy lift. It creates intra-abdominal pressure that stabilizes the spine."},

    # ── Level 3: Advanced ──────────────────────────────────────────────
    {"knowledge_level": 3, "category": "Training", "front_text": "What is linear vs. undulating periodization?", "back_text": "Linear periodization gradually increases intensity and decreases volume over weeks. Undulating periodization varies these within a single week (e.g., heavy Monday, light Wednesday, moderate Friday)."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is RPE and how is it used?", "back_text": "Rate of Perceived Exertion on a 1-10 scale. RPE 8 means you could do 2 more reps. It auto-regulates training intensity based on daily readiness rather than fixed percentages."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is the difference between RIR and RPE?", "back_text": "RIR (Reps in Reserve) counts how many reps you have left. RPE is 10 minus RIR. Both are auto-regulation tools. RPE 8 = RIR 2."},
    {"knowledge_level": 3, "category": "Nutrition", "front_text": "How does carb cycling work?", "back_text": "Alternating high-carb days (training days) and low-carb days (rest days) to optimize glycogen availability for performance while maintaining a caloric target."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is accommodating resistance?", "back_text": "Using bands or chains to modify the resistance curve of an exercise — making it harder at the top (lockout) where you're mechanically strongest."},
    {"knowledge_level": 3, "category": "Recovery", "front_text": "What is HRV and why does it matter?", "back_text": "Heart Rate Variability measures variation between heartbeats. Higher HRV indicates better recovery readiness. Low HRV may suggest accumulated fatigue and a need for lighter training."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is the SRA curve?", "back_text": "Stimulus-Recovery-Adaptation: after training (stimulus), performance dips during recovery, then supercompensates above baseline (adaptation). Training again at the peak of supercompensation is optimal."},
    {"knowledge_level": 3, "category": "Nutrition", "front_text": "What is the anabolic window myth?", "back_text": "The idea that you must eat protein within 30 minutes post-workout is largely debunked. Total daily protein intake matters far more than exact timing, though peri-workout nutrition can still help."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is conjugate training?", "back_text": "A system (popularized by Westside Barbell) that uses maximum effort days, dynamic effort days, and rotating exercise variations to develop both maximal strength and speed-strength."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What are cluster sets?", "back_text": "Breaking a set into mini-sets with short intra-set rest (10-30 seconds). This maintains rep quality and power output at higher loads compared to straight sets."},
    {"knowledge_level": 3, "category": "Nutrition", "front_text": "How does reverse dieting work?", "back_text": "After a prolonged cut, slowly increase calories (50-100 kcal/week) to rebuild metabolic rate while minimizing fat regain. This helps transition from a deficit to maintenance."},
    {"knowledge_level": 3, "category": "Recovery", "front_text": "What is the parasympathetic nervous system's role in recovery?", "back_text": "The 'rest and digest' branch. Post-training, shifting to parasympathetic dominance (via deep breathing, sleep, low stress) accelerates recovery and protein synthesis."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is mechanical tension vs. metabolic stress?", "back_text": "Mechanical tension (heavy loads) and metabolic stress (pump, high reps) are the two primary mechanisms of hypertrophy. An effective program includes both."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is velocity-based training (VBT)?", "back_text": "Using bar speed (measured by a device) to auto-regulate intensity. When bar speed drops below a threshold, the set ends — ensuring quality reps and managing fatigue objectively."},
    {"knowledge_level": 3, "category": "Nutrition", "front_text": "What role does creatine play?", "back_text": "Creatine monohydrate replenishes ATP in the phosphagen system, enabling 1-2 extra reps on heavy sets. It's the most researched and effective sports supplement. 3-5g daily is sufficient."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is a sticking point and how do you address it?", "back_text": "The weakest part of a lift's range of motion where you're most likely to fail. Address it with partial-range exercises (pin presses, board presses), paused reps, or accommodating resistance."},
    {"knowledge_level": 3, "category": "Recovery", "front_text": "What is the interference effect?", "back_text": "Concurrent training (heavy cardio + strength) can blunt hypertrophy signaling (AMPK vs. mTOR pathways). Separating sessions by 6+ hours or prioritizing one modality minimizes this."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is autoregulation in training?", "back_text": "Adjusting training load based on daily readiness using RPE, velocity, or HRV — rather than rigid percentages. This accounts for sleep, stress, nutrition, and accumulated fatigue."},
    {"knowledge_level": 3, "category": "Nutrition", "front_text": "How do you peak for a competition?", "back_text": "Taper training volume 1-2 weeks out while maintaining intensity. Carb-load in the final days to maximize glycogen. Manage weight cut if needed. Ensure peak strength on competition day."},
    {"knowledge_level": 3, "category": "Training", "front_text": "What is the repeated bout effect?", "back_text": "After the initial bout of an unfamiliar exercise, subsequent bouts produce less muscle damage and soreness. This is why beginners get more DOMS than experienced lifters doing the same exercise."},
]


class Command(BaseCommand):
    help = "Seed the database with flashcards for all knowledge levels."

    def handle(self, *args, **options):
        """Insert or update all flashcards."""
        created_count = 0
        for card_data in CARDS:
            _, created = FlashCard.objects.update_or_create(
                front_text=card_data["front_text"],
                defaults={
                    "knowledge_level": card_data["knowledge_level"],
                    "category": card_data["category"],
                    "back_text": card_data["back_text"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(CARDS)} flashcards ({created_count} new)."
            )
        )
