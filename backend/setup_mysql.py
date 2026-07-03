"""
Quick MySQL setup and migration script
"""
import sys
import subprocess
import os

def check_mysql_installed():
    """Check if MySQL is installed and accessible"""
    try:
        result = subprocess.run(['mysql', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ MySQL is installed:", result.stdout.strip())
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def create_database():
    """Create the MacQuiz database in MySQL"""
    print("\n" + "="*60)
    print("MySQL Database Setup")
    print("="*60)
    
    print("\nEnter your MySQL root credentials:")
    mysql_host = input("MySQL Host [localhost]: ").strip() or "localhost"
    mysql_port = input("MySQL Port [3306]: ").strip() or "3306"
    mysql_user = input("MySQL Username [root]: ").strip() or "root"
    mysql_password = input("MySQL Password: ").strip()
    
    database_name = "macquiz_db"
    
    print(f"\n📋 Creating database '{database_name}'...")
    
    # Create database using mysql command
    create_db_sql = f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    
    cmd = [
        'mysql',
        f'-h{mysql_host}',
        f'-P{mysql_port}',
        f'-u{mysql_user}',
        f'-p{mysql_password}',
        '-e',
        create_db_sql
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Database '{database_name}' created successfully!")
            
            # Update .env file
            connection_string = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{database_name}"
            update_env_file(connection_string)
            
            return True
        else:
            print(f"❌ Error creating database: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ MySQL command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def update_env_file(connection_string):
    """Update .env file with MySQL connection string"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print("⚠️  .env file not found!")
        return
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update DATABASE_URL line
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('DATABASE_URL='):
                f.write(f'DATABASE_URL={connection_string}\n')
                print(f"✅ Updated .env with MySQL connection string")
            else:
                f.write(line)

def main():
    print("="*60)
    print("MacQuiz MySQL Setup Assistant")
    print("="*60)
    
    # Check if MySQL is installed
    if not check_mysql_installed():
        print("\n❌ MySQL is not installed or not in PATH")
        print("\n📥 Please install MySQL Server first:")
        print("   Download from: https://dev.mysql.com/downloads/installer/")
        print("\nAfter installation, add MySQL bin folder to PATH:")
        print("   C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin")
        sys.exit(1)
    
    # Create database
    if create_database():
        print("\n" + "="*60)
        print("🎉 Setup completed successfully!")
        print("="*60)
        print("\n📋 Next steps:")
        print("1. Run migration script: python migrate_to_mysql.py")
        print("2. Start backend: python -m uvicorn app.main:app --reload")
        print("\nFor detailed instructions, see: MYSQL_MIGRATION_GUIDE.md")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        print("For manual setup, see: MYSQL_MIGRATION_GUIDE.md")

if __name__ == "__main__":
    main()
