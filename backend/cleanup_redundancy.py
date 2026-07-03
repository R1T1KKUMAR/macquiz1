from app.db.database import SessionLocal
from app.models.models import QuizAttempt, User, Quiz, Answer
from collections import defaultdict

def main():
    db = SessionLocal()
    try:
        print("🧹 Starting cleanup of redundant data...\n")

        # 1. Remove duplicate attempts - keep only the latest completed one per user+quiz
        print("1️⃣ Cleaning duplicate attempts...")
        attempts = db.query(QuizAttempt).all()
        duplicates = defaultdict(list)

        for attempt in attempts:
            key = (attempt.student_id, attempt.quiz_id)
            duplicates[key].append(attempt)

        removed_count = 0
        for (student_id, quiz_id), attempt_list in duplicates.items():
            if len(attempt_list) > 1:
                # Sort by: completed first, then by started_at (newest first)
                sorted_attempts = sorted(
                    attempt_list,
                    key=lambda x: (not x.is_completed, x.started_at),
                    reverse=True
                )

                # Keep the first one (completed and newest, or just newest)
                keep = sorted_attempts[0]
                to_remove = sorted_attempts[1:]

                user = db.query(User).filter(User.id == student_id).first()
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

                print(f"   User: {user.email}, Quiz: {quiz.title if quiz else 'Unknown'}")
                print(f"   ✓ Keeping: Attempt #{keep.id} ({'Completed' if keep.is_completed else 'Incomplete'})")

                for attempt_item in to_remove:
                    print(
                        f"   ✗ Removing: Attempt #{attempt_item.id} "
                        f"({'Completed' if attempt_item.is_completed else 'Incomplete'})"
                    )
                    db.query(Answer).filter(Answer.attempt_id == attempt_item.id).delete(synchronize_session=False)
                    db.delete(attempt_item)
                    removed_count += 1

        db.commit()
        print(f"   Removed {removed_count} duplicate attempts\n")

        # 2. Clean up incomplete teacher/admin attempts
        print("2️⃣ Cleaning incomplete teacher/admin preview attempts...")
        teacher_attempts = db.query(QuizAttempt).join(User).filter(
            User.role.in_(['teacher', 'admin']),
            QuizAttempt.is_completed == False
        ).all()

        teacher_removed = 0
        for attempt_item in teacher_attempts:
            user = db.query(User).filter(User.id == attempt_item.student_id).first()
            quiz = db.query(Quiz).filter(Quiz.id == attempt_item.quiz_id).first()
            print(
                f"   ✗ Removing incomplete preview: {user.email}, "
                f"Quiz: {quiz.title if quiz else 'Unknown'}, Attempt #{attempt_item.id}"
            )
            db.query(Answer).filter(Answer.attempt_id == attempt_item.id).delete(synchronize_session=False)
            db.delete(attempt_item)
            teacher_removed += 1

        db.commit()
        print(f"   Removed {teacher_removed} incomplete teacher/admin attempts\n")

        print("✅ Cleanup complete!")
        print(f"   Total removed: {removed_count + teacher_removed} redundant attempts")
    finally:
        db.close()


if __name__ == "__main__":
    main()
