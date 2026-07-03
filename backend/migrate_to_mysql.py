"""
Migration script to transfer data from SQLite to MySQL
Run this after setting up your MySQL database
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import (
    Base,
    User,
    Subject,
    QuestionBank,
    Quiz,
    Question,
    QuizAttempt,
    Answer,
    QuizAssignment,
    RevokedToken,
    UserTokenBlock,
)


def copy_table(sqlite_db, mysql_db, model, build_payload):
    records = sqlite_db.query(model).all()
    migrated_count = 0

    for record in records:
        existing = mysql_db.query(model).filter(model.id == record.id).first()
        if existing:
            continue

        mysql_db.add(model(**build_payload(record)))
        migrated_count += 1

    mysql_db.commit()
    return len(records), migrated_count

def migrate_sqlite_to_mysql():
    """
    Migrate data from SQLite to MySQL
    """
    # SQLite connection
    sqlite_url = "sqlite:///./quizapp.db"
    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_db = SQLiteSession()
    
    # MySQL connection (read from .env or use direct string)
    mysql_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/macquiz_db")
    print(f"Connecting to MySQL: {mysql_url.split('@')[1] if '@' in mysql_url else mysql_url}")
    
    mysql_engine = create_engine(
        mysql_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=True
    )
    MySQLSession = sessionmaker(bind=mysql_engine)
    mysql_db = MySQLSession()
    
    try:
        # Create all tables in MySQL
        print("\n📋 Creating tables in MySQL...")
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ Tables created successfully!")

        summary = {}

        print("\n👥 Migrating users...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            User,
            lambda user: {
                "id": user.id,
                "email": user.email,
                "hashed_password": user.hashed_password,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_active": user.last_active,
                "student_id": user.student_id,
                "department": user.department,
                "class_year": user.class_year,
                "phone_number": user.phone_number,
            },
        )
        summary["users"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} users")

        print("\n📚 Migrating subjects...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            Subject,
            lambda subject: {
                "id": subject.id,
                "name": subject.name,
                "code": subject.code,
                "description": subject.description,
                "department": subject.department,
                "creator_id": subject.creator_id,
                "is_active": subject.is_active,
                "created_at": subject.created_at,
            },
        )
        summary["subjects"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} subjects")

        print("\n💡 Migrating question bank...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            QuestionBank,
            lambda question: {
                "id": question.id,
                "subject_id": question.subject_id,
                "creator_id": question.creator_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_answer": question.correct_answer,
                "topic": question.topic,
                "difficulty": question.difficulty,
                "marks": question.marks,
                "times_used": question.times_used,
                "is_active": question.is_active,
                "created_at": question.created_at,
                "updated_at": question.updated_at,
            },
        )
        summary["question_bank"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} question bank records")

        print("\n📝 Migrating quizzes...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            Quiz,
            lambda quiz: {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "creator_id": quiz.creator_id,
                "subject_id": quiz.subject_id,
                "department": quiz.department,
                "class_year": quiz.class_year,
                "scheduled_at": quiz.scheduled_at,
                "duration_minutes": quiz.duration_minutes,
                "grace_period_minutes": quiz.grace_period_minutes,
                "is_live_session": quiz.is_live_session,
                "live_start_time": quiz.live_start_time,
                "live_end_time": quiz.live_end_time,
                "total_marks": quiz.total_marks,
                "marks_per_correct": quiz.marks_per_correct,
                "negative_marking": quiz.negative_marking,
                "is_active": quiz.is_active,
                "created_at": quiz.created_at,
                "updated_at": quiz.updated_at,
            },
        )
        summary["quizzes"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} quizzes")

        print("\n❓ Migrating questions...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            Question,
            lambda question: {
                "id": question.id,
                "quiz_id": question.quiz_id,
                "question_bank_id": question.question_bank_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_answer": question.correct_answer,
                "marks": question.marks,
                "order": question.order,
            },
        )
        summary["questions"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} questions")

        print("\n🎯 Migrating quiz attempts...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            QuizAttempt,
            lambda attempt: {
                "id": attempt.id,
                "quiz_id": attempt.quiz_id,
                "student_id": attempt.student_id,
                "score": attempt.score,
                "total_marks": attempt.total_marks,
                "percentage": attempt.percentage,
                "started_at": attempt.started_at,
                "submitted_at": attempt.submitted_at,
                "time_taken_minutes": attempt.time_taken_minutes,
                "is_completed": attempt.is_completed,
                "is_graded": attempt.is_graded,
            },
        )
        summary["quiz_attempts"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} quiz attempts")

        print("\n✍️ Migrating answers...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            Answer,
            lambda answer: {
                "id": answer.id,
                "attempt_id": answer.attempt_id,
                "question_id": answer.question_id,
                "answer_text": answer.answer_text,
                "is_correct": answer.is_correct,
                "marks_awarded": answer.marks_awarded,
            },
        )
        summary["answers"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} answers")

        print("\n📌 Migrating quiz assignments...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            QuizAssignment,
            lambda assignment: {
                "id": assignment.id,
                "quiz_id": assignment.quiz_id,
                "student_id": assignment.student_id,
                "assigned_at": assignment.assigned_at,
            },
        )
        summary["quiz_assignments"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} quiz assignments")

        print("\n🔐 Migrating revoked tokens...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            RevokedToken,
            lambda token: {
                "id": token.id,
                "jti": token.jti,
                "subject": token.subject,
                "revoked_at": token.revoked_at,
                "expires_at": token.expires_at,
            },
        )
        summary["revoked_tokens"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} revoked tokens")

        print("\n🔒 Migrating user token blocks...")
        total, migrated = copy_table(
            sqlite_db,
            mysql_db,
            UserTokenBlock,
            lambda block: {
                "id": block.id,
                "user_id": block.user_id,
                "revoked_before": block.revoked_before,
            },
        )
        summary["user_token_blocks"] = (total, migrated)
        print(f"✅ Migrated {migrated}/{total} user token blocks")
        
        print("\n" + "="*50)
        print("🎉 Migration completed successfully!")
        print("="*50)
        print(f"\n📊 Summary:")
        for table_name, (total_count, migrated_count) in summary.items():
            print(f"  - {table_name}: {migrated_count}/{total_count} migrated")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        mysql_db.rollback()
        raise
    finally:
        sqlite_db.close()
        mysql_db.close()

if __name__ == "__main__":
    print("="*50)
    print("SQLite to MySQL Migration")
    print("="*50)
    print("\n⚠️  IMPORTANT: Before running this script:")
    print("1. Install MySQL Server (https://dev.mysql.com/downloads/)")
    print("2. Create database: CREATE DATABASE macquiz_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("3. Update .env file with your MySQL credentials")
    print("4. Install MySQL Python connector: pip install pymysql mysqlclient")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    migrate_sqlite_to_mysql()
