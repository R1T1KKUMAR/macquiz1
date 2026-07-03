"""
Fix incorrect attempt data (score and time_taken) for existing attempts
"""
from app.db.database import SessionLocal
from app.models.models import QuizAttempt, Quiz, Answer, Question

def fix_attempt_scores_and_time():
    db = SessionLocal()
    try:
        # Get all completed attempts
        attempts = db.query(QuizAttempt).filter(QuizAttempt.is_completed == True).all()
        
        print(f"Found {len(attempts)} completed attempts to check...")
        
        for attempt in attempts:
            quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
            if not quiz:
                continue
            
            # Recalculate score
            correct_count = 0
            total_score = 0
            
            answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
            for answer in answers:
                question = db.query(Question).filter(Question.id == answer.question_id).first()
                if question:
                    if answer.is_correct:
                        # Award full question marks (not marks_per_correct * marks)
                        total_score += question.marks
                        correct_count += 1
                    else:
                        # Apply negative marking
                        if quiz.negative_marking and quiz.negative_marking > 0:
                            total_score -= quiz.negative_marking
            
            # Fix score if different
            old_score = attempt.score
            new_score = max(0, total_score)
            
            if old_score != new_score:
                print(f"\nAttempt ID {attempt.id}:")
                print(f"  Old score: {old_score} -> New score: {new_score}")
                attempt.score = new_score
                attempt.percentage = (new_score / attempt.total_marks * 100) if attempt.total_marks > 0 else 0
                print(f"  New percentage: {attempt.percentage:.1f}%")
            
            # Fix time_taken if it exceeds quiz duration
            if attempt.time_taken_minutes and quiz.duration_minutes:
                if attempt.time_taken_minutes > quiz.duration_minutes:
                    print(f"\nAttempt ID {attempt.id}:")
                    print(f"  Time taken was {attempt.time_taken_minutes:.2f}m (exceeds quiz duration)")
                    print(f"  Capping at quiz duration: {quiz.duration_minutes}m")
                    attempt.time_taken_minutes = quiz.duration_minutes
        
        db.commit()
        print("\n✅ All attempts fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_attempt_scores_and_time()
