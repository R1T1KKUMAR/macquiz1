"""Test teacher preview functionality"""
from app.db.database import SessionLocal
from app.models.models import QuizAttempt, User, Quiz

db = SessionLocal()

# Find teacher
teacher = db.query(User).filter(User.email == 'prateek.a@rbmi.in').first()
if not teacher:
    print("❌ Teacher not found")
    db.close()
    exit(1)

print(f"✅ Found teacher: {teacher.email} (role: {teacher.role})")

# Find quiz
quiz = db.query(Quiz).filter(Quiz.id == 2).first()
if not quiz:
    print("❌ Quiz 2 not found")
    db.close()
    exit(1)

print(f"✅ Found quiz: {quiz.title}")

# Check for existing attempts
attempts = db.query(QuizAttempt).filter(
    QuizAttempt.student_id == teacher.id,
    QuizAttempt.quiz_id == 2
).all()

print(f"\n📊 Found {len(attempts)} existing attempts:")
for att in attempts:
    print(f"   - Attempt {att.id}: completed={att.is_completed}, score={att.score}")

# Delete all teacher attempts to allow fresh preview
if attempts:
    for att in attempts:
        db.delete(att)
    db.commit()
    print(f"\n🗑️  Deleted {len(attempts)} attempt(s) to allow fresh preview")

print("\n✅ Teacher can now preview quiz fresh!")
db.close()
