"""Check quiz attempts in database"""
import sys
sys.path.insert(0, 'C:/Users/ritik/OneDrive/Desktop/MacQuiz/backend')

from app.db.database import SessionLocal
from app.models.models import QuizAttempt, User, Quiz

db = SessionLocal()

print("=== All Quiz Attempts ===")
attempts = db.query(QuizAttempt).all()
print(f"Total attempts: {len(attempts)}\n")

for attempt in attempts:
    student = db.query(User).filter(User.id == attempt.student_id).first()
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    
    print(f"Attempt ID: {attempt.id}")
    print(f"  Student: {student.first_name} {student.last_name} (ID: {student.id})")
    print(f"  Quiz: {quiz.title} (ID: {quiz.id})")
    print(f"  Score: {attempt.score}/{attempt.total_marks}")
    print(f"  Completed: {attempt.is_completed}")
    print(f"  Started: {attempt.started_at}")
    print(f"  Submitted: {attempt.submitted_at}")
    print()

db.close()
