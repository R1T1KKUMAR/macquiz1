from app.db.database import SessionLocal
from app.models.models import QuizAttempt, User, Quiz
from collections import defaultdict

def main():
    db = SessionLocal()
    try:
        # Check duplicate attempts
        attempts = db.query(QuizAttempt).all()
        print(f"📊 Total quiz attempts: {len(attempts)}")

        duplicates = defaultdict(list)
        for attempt in attempts:
            key = (attempt.student_id, attempt.quiz_id)
            duplicates[key].append(attempt)

        print("\n🔍 Checking for duplicate attempts (same user + quiz):")
        has_duplicates = False
        for (student_id, quiz_id), attempt_list in duplicates.items():
            if len(attempt_list) > 1:
                has_duplicates = True
                user = db.query(User).filter(User.id == student_id).first()
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                print(f"\n⚠️  User: {user.email} ({user.role})")
                print(f"   Quiz: {quiz.title if quiz else 'Unknown'}")
                print(f"   Total attempts: {len(attempt_list)}")
                for attempt_item in attempt_list:
                    status = "✓ Completed" if attempt_item.is_completed else "⏳ Incomplete"
                    print(
                        f"   - Attempt #{attempt_item.id}: {status}, "
                        f"Score: {attempt_item.score}, Started: {attempt_item.started_at}"
                    )

        if not has_duplicates:
            print("✅ No duplicate attempts found!")

        # Check for incomplete teacher attempts
        print("\n\n🔍 Checking for teacher/admin incomplete attempts:")
        teacher_attempts = db.query(QuizAttempt).join(User).filter(
            User.role.in_(['teacher', 'admin']),
            QuizAttempt.is_completed == False
        ).all()

        if teacher_attempts:
            print(f"⚠️  Found {len(teacher_attempts)} incomplete teacher/admin attempts:")
            for attempt_item in teacher_attempts:
                user = db.query(User).filter(User.id == attempt_item.student_id).first()
                quiz = db.query(Quiz).filter(Quiz.id == attempt_item.quiz_id).first()
                print(
                    f"   - User: {user.email}, Quiz: {quiz.title if quiz else 'Unknown'}, "
                    f"Attempt ID: {attempt_item.id}"
                )
        else:
            print("✅ No incomplete teacher/admin attempts")
    finally:
        db.close()


if __name__ == "__main__":
    main()
