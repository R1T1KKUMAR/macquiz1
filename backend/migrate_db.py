"""
Database reset and migration script
Recreates the database with the updated schema including phone_number field
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import engine, Base
from app.models.models import User, Quiz, Question, QuizAttempt
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

def upgrade_database():
    """Create any missing tables/columns represented by current ORM metadata."""
    print("🔄 Applying safe schema upgrade (non-destructive)...")
    print("✨ Creating missing tables if needed...")
    Base.metadata.create_all(bind=engine)
    print("✅ Safe upgrade completed (existing data preserved)")


def reset_database():
    """Drop all tables and recreate them with updated schema."""
    print("🔄 Resetting database (DESTRUCTIVE)...")

    # Drop all tables
    print("📦 Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    # Create all tables with new schema
    print("✨ Creating tables with updated schema...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database schema reset successfully!")

def create_admin_user():
    """Create default admin user"""
    print("\n👤 Creating default admin user...")
    
    from app.db.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Check if admin exists
        existing_admin = db.query(User).filter(User.email == "admin@macquiz.com").first()
        if existing_admin:
            print("ℹ️  Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            email="admin@macquiz.com",
            hashed_password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
            phone_number=None  # Optional field
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created successfully!")
        print("📧 Email: admin@macquiz.com")
        print("🔑 Password: admin123")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MacQuiz database migration helper")
    parser.add_argument(
        "--force-reset",
        action="store_true",
        help="Drop and recreate all tables (DESTRUCTIVE)",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("  MacQuiz Database Migration")
    print("  Safe upgrade by default")
    print("=" * 50)
    print()
    
    try:
        if args.force_reset:
            print("⚠️  --force-reset enabled: this will delete all existing data")
            reset_database()
        else:
            upgrade_database()
        create_admin_user()
        
        print()
        print("=" * 50)
        print("✅ Migration completed successfully!")
        print("=" * 50)
        print()
        print("🚀 You can now start the backend server:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print()
        
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Migration failed: {e}")
        print("=" * 50)
        print()
        sys.exit(1)
