"""
PostgreSQL-safe constraint/index migration for MacQuiz.

Features:
- Duplicate pre-checks for target unique constraints
- Dry-run mode by default
- Optional auto-fix mode with deterministic keep/delete rules
- Optional pg_dump backup before destructive dedupe
"""

import argparse
import os
import subprocess
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.db.database import engine


@dataclass
class ConstraintCheck:
    name: str
    duplicate_count_sql: str
    create_sql: str
    description: str


UNIQUE_CHECKS = [
    ConstraintCheck(
        name="uq_answers_attempt_question",
        description="One answer per question in each attempt",
        duplicate_count_sql="""
            SELECT COUNT(*)
            FROM (
                SELECT attempt_id, question_id
                FROM public.answers
                GROUP BY attempt_id, question_id
                HAVING COUNT(*) > 1
            ) d
        """,
        create_sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_answers_attempt_question
            ON public.answers (attempt_id, question_id)
        """,
    ),
    ConstraintCheck(
        name="uq_quiz_assignments_quiz_student",
        description="One assignment per student per quiz",
        duplicate_count_sql="""
            SELECT COUNT(*)
            FROM (
                SELECT quiz_id, student_id
                FROM public.quiz_assignments
                GROUP BY quiz_id, student_id
                HAVING COUNT(*) > 1
            ) d
        """,
        create_sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_quiz_assignments_quiz_student
            ON public.quiz_assignments (quiz_id, student_id)
        """,
    ),
    ConstraintCheck(
        name="uq_revoked_tokens_jti",
        description="JWT jti must be globally unique",
        duplicate_count_sql="""
            SELECT COUNT(*)
            FROM (
                SELECT jti
                FROM public.revoked_tokens
                GROUP BY jti
                HAVING COUNT(*) > 1
            ) d
        """,
        create_sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_revoked_tokens_jti
            ON public.revoked_tokens (jti)
        """,
    ),
    ConstraintCheck(
        name="uq_user_token_blocks_user_id",
        description="Single token-block row per user",
        duplicate_count_sql="""
            SELECT COUNT(*)
            FROM (
                SELECT user_id
                FROM public.user_token_blocks
                GROUP BY user_id
                HAVING COUNT(*) > 1
            ) d
        """,
        create_sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_user_token_blocks_user_id
            ON public.user_token_blocks (user_id)
        """,
    ),
    ConstraintCheck(
        name="uq_users_email",
        description="Email must be unique",
        duplicate_count_sql="""
            SELECT COUNT(*)
            FROM (
                SELECT email
                FROM public.users
                GROUP BY email
                HAVING COUNT(*) > 1
            ) d
        """,
        create_sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email
            ON public.users (email)
        """,
    ),
    ConstraintCheck(
        name="uq_users_student_id",
        description="Student/teacher user ID must be unique when present",
        duplicate_count_sql="""
            SELECT COUNT(*)
            FROM (
                SELECT student_id
                FROM public.users
                WHERE student_id IS NOT NULL
                GROUP BY student_id
                HAVING COUNT(*) > 1
            ) d
        """,
        create_sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_users_student_id
            ON public.users (student_id)
            WHERE student_id IS NOT NULL
        """,
    ),
]

NON_UNIQUE_INDEXES = [
    (
        "ix_answers_attempt_id",
        "CREATE INDEX IF NOT EXISTS ix_answers_attempt_id ON public.answers (attempt_id)",
    ),
    (
        "ix_answers_question_id",
        "CREATE INDEX IF NOT EXISTS ix_answers_question_id ON public.answers (question_id)",
    ),
    (
        "ix_question_bank_subject_id",
        "CREATE INDEX IF NOT EXISTS ix_question_bank_subject_id ON public.question_bank (subject_id)",
    ),
    (
        "ix_question_bank_creator_id",
        "CREATE INDEX IF NOT EXISTS ix_question_bank_creator_id ON public.question_bank (creator_id)",
    ),
    (
        "ix_questions_quiz_id",
        "CREATE INDEX IF NOT EXISTS ix_questions_quiz_id ON public.questions (quiz_id)",
    ),
    (
        "ix_questions_question_bank_id",
        "CREATE INDEX IF NOT EXISTS ix_questions_question_bank_id ON public.questions (question_bank_id)",
    ),
    (
        "ix_quiz_attempts_quiz_id",
        "CREATE INDEX IF NOT EXISTS ix_quiz_attempts_quiz_id ON public.quiz_attempts (quiz_id)",
    ),
    (
        "ix_quiz_attempts_student_id",
        "CREATE INDEX IF NOT EXISTS ix_quiz_attempts_student_id ON public.quiz_attempts (student_id)",
    ),
    (
        "ix_quizzes_creator_id",
        "CREATE INDEX IF NOT EXISTS ix_quizzes_creator_id ON public.quizzes (creator_id)",
    ),
    (
        "ix_quizzes_subject_id",
        "CREATE INDEX IF NOT EXISTS ix_quizzes_subject_id ON public.quizzes (subject_id)",
    ),
    (
        "ix_subjects_creator_id",
        "CREATE INDEX IF NOT EXISTS ix_subjects_creator_id ON public.subjects (creator_id)",
    ),
]


def _scalar(connection, sql: str) -> int:
    result = connection.execute(text(sql)).scalar()
    return int(result or 0)


def _load_precheck(connection):
    blocked = []
    ready = []

    for check in UNIQUE_CHECKS:
        duplicate_groups = _scalar(connection, check.duplicate_count_sql)
        if duplicate_groups > 0:
            blocked.append((check, duplicate_groups))
        else:
            ready.append(check)

    return blocked, ready


def _merge_users_by_key(connection, key_column: str, include_not_null_filter: bool) -> int:
    where_clause = f"{key_column} IS NOT NULL" if include_not_null_filter else "TRUE"
    merge_cte = f"""
        WITH dup_map AS (
            SELECT id AS old_id,
                   MIN(id) OVER (PARTITION BY {key_column}) AS keep_id
            FROM public.users
            WHERE {where_clause}
        ),
        pairs AS (
            SELECT old_id, keep_id
            FROM dup_map
            WHERE old_id <> keep_id
        )
    """

    connection.execute(text(merge_cte + "UPDATE public.quizzes q SET creator_id = p.keep_id FROM pairs p WHERE q.creator_id = p.old_id"))
    connection.execute(text(merge_cte + "UPDATE public.subjects s SET creator_id = p.keep_id FROM pairs p WHERE s.creator_id = p.old_id"))
    connection.execute(text(merge_cte + "UPDATE public.question_bank qb SET creator_id = p.keep_id FROM pairs p WHERE qb.creator_id = p.old_id"))
    connection.execute(text(merge_cte + "UPDATE public.quiz_attempts qa SET student_id = p.keep_id FROM pairs p WHERE qa.student_id = p.old_id"))
    connection.execute(text(merge_cte + "UPDATE public.quiz_assignments qa SET student_id = p.keep_id FROM pairs p WHERE qa.student_id = p.old_id"))
    connection.execute(text(merge_cte + "UPDATE public.user_token_blocks ub SET user_id = p.keep_id FROM pairs p WHERE ub.user_id = p.old_id"))

    delete_sql = merge_cte + "DELETE FROM public.users u USING pairs p WHERE u.id = p.old_id"
    deleted = connection.execute(text(delete_sql))
    return int(deleted.rowcount or 0)


def _dedupe_answers(connection) -> int:
    sql = """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY attempt_id, question_id
                       ORDER BY id DESC
                   ) AS rn
            FROM public.answers
        )
        DELETE FROM public.answers a
        USING ranked r
        WHERE a.id = r.id
          AND r.rn > 1
    """
    result = connection.execute(text(sql))
    return int(result.rowcount or 0)


def _dedupe_quiz_assignments(connection) -> int:
    sql = """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY quiz_id, student_id
                       ORDER BY assigned_at DESC NULLS LAST, id DESC
                   ) AS rn
            FROM public.quiz_assignments
        )
        DELETE FROM public.quiz_assignments qa
        USING ranked r
        WHERE qa.id = r.id
          AND r.rn > 1
    """
    result = connection.execute(text(sql))
    return int(result.rowcount or 0)


def _dedupe_revoked_tokens(connection) -> int:
    sql = """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY jti
                       ORDER BY revoked_at DESC NULLS LAST, id DESC
                   ) AS rn
            FROM public.revoked_tokens
        )
        DELETE FROM public.revoked_tokens rt
        USING ranked r
        WHERE rt.id = r.id
          AND r.rn > 1
    """
    result = connection.execute(text(sql))
    return int(result.rowcount or 0)


def _dedupe_user_token_blocks(connection) -> int:
    sql = """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY user_id
                       ORDER BY revoked_before DESC NULLS LAST, id DESC
                   ) AS rn
            FROM public.user_token_blocks
        )
        DELETE FROM public.user_token_blocks ub
        USING ranked r
        WHERE ub.id = r.id
          AND r.rn > 1
    """
    result = connection.execute(text(sql))
    return int(result.rowcount or 0)


def _run_auto_fix(connection):
    print("\n🧹 Running deterministic auto-fix for duplicate rows...")
    deleted_email_users = _merge_users_by_key(connection, "email", include_not_null_filter=False)
    if deleted_email_users > 0:
        print(f"  ✅ Merged users by email: removed {deleted_email_users} duplicate user rows")

    deleted_student_users = _merge_users_by_key(connection, "student_id", include_not_null_filter=True)
    if deleted_student_users > 0:
        print(f"  ✅ Merged users by student_id: removed {deleted_student_users} duplicate user rows")

    deleted_answers = _dedupe_answers(connection)
    deleted_assignments = _dedupe_quiz_assignments(connection)
    deleted_tokens = _dedupe_revoked_tokens(connection)
    deleted_blocks = _dedupe_user_token_blocks(connection)

    print(f"  ✅ Deduped answers: removed {deleted_answers} rows")
    print(f"  ✅ Deduped quiz_assignments: removed {deleted_assignments} rows")
    print(f"  ✅ Deduped revoked_tokens: removed {deleted_tokens} rows")
    print(f"  ✅ Deduped user_token_blocks: removed {deleted_blocks} rows")


def _build_pg_dump_command(backup_file: str):
    url = make_url(str(engine.url))
    cmd = [
        "pg_dump",
        "-h",
        url.host or "localhost",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "postgres",
        "-d",
        (url.database or "postgres").lstrip("/"),
        "-Fc",
        "-f",
        backup_file,
    ]

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    return cmd, env


def _maybe_run_backup(backup_file: str) -> bool:
    print(f"\n💾 Creating backup via pg_dump: {backup_file}")
    cmd, env = _build_pg_dump_command(backup_file)
    try:
        subprocess.run(cmd, env=env, check=True)
        print("✅ Backup created successfully")
        return True
    except FileNotFoundError:
        print("❌ pg_dump not found in PATH. Install PostgreSQL client tools or run without --backup-file")
    except subprocess.CalledProcessError as error:
        print(f"❌ pg_dump failed with exit code {error.returncode}")
    return False


def run(apply_changes: bool, auto_fix: bool, backup_file: str | None) -> int:
    if engine.dialect.name != "postgresql":
        print(f"❌ This script is for PostgreSQL only. Current dialect: {engine.dialect.name}")
        return 2

    if auto_fix and not apply_changes:
        print("❌ --auto-fix requires --apply")
        return 2

    print("🔍 Running PostgreSQL constraint pre-checks...")

    with engine.begin() as connection:
        blocked, ready = _load_precheck(connection)

    if blocked:
        print("\n⚠️  Duplicate data detected. These unique indexes are blocked:")
        for check, count in blocked:
            print(f"  - {check.name}: {count} duplicate group(s) found ({check.description})")
    else:
        print("\n✅ No duplicate groups found for targeted unique constraints")

    print("\n📋 Planned unique indexes:")
    for check in UNIQUE_CHECKS:
        status = "BLOCKED" if any(item[0].name == check.name for item in blocked) else "READY"
        print(f"  - {check.name}: {status}")

    if not apply_changes:
        print("\nℹ️  Dry run only. Re-run with --apply to execute safe index creation.")
        return 1 if blocked else 0

    if auto_fix and blocked:
        if backup_file and not _maybe_run_backup(backup_file):
            return 2
        elif not backup_file:
            print("\n⚠️  Auto-fix is running without backup. Recommended: re-run with --backup-file <path>")

        with engine.begin() as connection:
            _run_auto_fix(connection)

        with engine.begin() as connection:
            blocked, ready = _load_precheck(connection)

        print("\n🔁 Re-check after auto-fix:")
        if blocked:
            for check, count in blocked:
                print(f"  - {check.name}: still blocked with {count} duplicate group(s)")
        else:
            print("  ✅ All target unique constraints are now clean")

    print("\n🚀 Applying safe indexes...")
    with engine.begin() as connection:
        for check in ready:
            connection.execute(text(check.create_sql))
            print(f"  ✅ Applied {check.name}")

        for index_name, create_sql in NON_UNIQUE_INDEXES:
            connection.execute(text(create_sql))
            print(f"  ✅ Ensured {index_name}")

    if blocked:
        print("\n⚠️  Migration applied partially. Resolve remaining duplicates, then re-run with --apply.")
        return 1

    print("\n🎉 All targeted PostgreSQL constraints/indexes are applied safely.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Safe PostgreSQL constraint/index migration")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply indexes that pass duplicate pre-checks",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically dedupe duplicate rows using deterministic keep/delete rules",
    )
    parser.add_argument(
        "--backup-file",
        type=str,
        default=None,
        help="Path for pg_dump backup file before auto-fix (recommended)",
    )
    args = parser.parse_args()
    raise SystemExit(run(apply_changes=args.apply, auto_fix=args.auto_fix, backup_file=args.backup_file))


if __name__ == "__main__":
    main()
