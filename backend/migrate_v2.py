"""
MacQuiz v2+ schema migration helper (safe, non-destructive).

This script uses SQLAlchemy metadata to create any missing tables for the
current model set. It intentionally does not drop tables or data.
"""

import os
import shutil
from datetime import datetime

from sqlalchemy import inspect, text

from app.db.database import engine, Base


DB_PATH = "quizapp.db"
BACKUP_PATH = f"quizapp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"


def backup_database():
    """Create a backup of SQLite database before migration."""
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Database backed up to: {BACKUP_PATH}")
        return True
    return False


def migrate_database():
    """Create missing tables using current SQLAlchemy metadata."""
    print("\n🔄 Starting safe schema migration...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("answers")}
    existing_indexes.update({idx["name"] for idx in inspector.get_indexes("quiz_assignments")})

    statements = []
    if "uq_answers_attempt_question" not in existing_indexes:
        statements.append(
            "CREATE UNIQUE INDEX uq_answers_attempt_question ON answers (attempt_id, question_id)"
        )
    if "ix_answers_attempt_question" not in existing_indexes:
        statements.append(
            "CREATE INDEX ix_answers_attempt_question ON answers (attempt_id, question_id)"
        )
    if "uq_quiz_assignments_quiz_student" not in existing_indexes:
        statements.append(
            "CREATE UNIQUE INDEX uq_quiz_assignments_quiz_student ON quiz_assignments (quiz_id, student_id)"
        )
    if "ix_quiz_assignments_quiz_student" not in existing_indexes:
        statements.append(
            "CREATE INDEX ix_quiz_assignments_quiz_student ON quiz_assignments (quiz_id, student_id)"
        )

    if statements:
        with engine.begin() as connection:
            for stmt in statements:
                try:
                    connection.execute(text(stmt))
                except Exception as error:
                    print(f"⚠️  Skipping index statement due to error: {error}")

    print("✅ Migration completed successfully!")


def verify_migration():
    """Verify presence of core tables for current backend features."""
    print("\n🔍 Verifying migration...")
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "users",
        "subjects",
        "question_bank",
        "quizzes",
        "questions",
        "quiz_attempts",
        "answers",
        "quiz_assignments",
        "revoked_tokens",
        "user_token_blocks",
    }

    missing_tables = sorted(expected_tables - table_names)

    if missing_tables:
        print("❌ Missing tables:")
        for table in missing_tables:
            print(f"   - {table}")
    else:
        print("✅ All expected tables are present")

    print(f"\n📊 Total tables in database: {len(table_names)}")
    for table in sorted(table_names):
        print(f"   - {table}")


if __name__ == "__main__":
    print("=" * 60)
    print("MacQuiz Safe Schema Migration")
    print("=" * 60)

    if backup_database():
        print("✅ Backup created successfully")
    else:
        print("ℹ️  No SQLite file found to backup (skipping backup)")

    migrate_database()
    verify_migration()

    print("\n" + "=" * 60)
    print("🎉 Migration process completed!")
    print("=" * 60)
