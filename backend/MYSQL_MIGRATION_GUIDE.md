# MySQL Migration Guide

## Step 1: Install MySQL Server

### Windows:
1. Download MySQL Installer from: https://dev.mysql.com/downloads/installer/
2. Run the installer and choose "Developer Default" or "Server only"
3. Follow the installation wizard:
   - Set root password (remember this!)
   - Keep default port 3306
   - Configure as Windows Service (auto-start)

### Verify Installation:
```bash
mysql --version
```

## Step 2: Create Database

1. Open MySQL Command Line Client or MySQL Workbench
2. Login with root user
3. Create the database:

```sql
CREATE DATABASE macquiz_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. (Optional) Create a dedicated user:

```sql
CREATE USER 'macquiz_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON macquiz_db.* TO 'macquiz_user'@'localhost';
FLUSH PRIVILEGES;
```

## Step 3: Update Configuration

Edit `backend/.env` file:

```env
# For root user:
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/macquiz_db

# Or for dedicated user:
DATABASE_URL=mysql+pymysql://macquiz_user:your_secure_password@localhost:3306/macquiz_db
```

**Replace:**
- `your_mysql_password` with your actual MySQL password
- `localhost` with your MySQL host (if remote)
- `3306` with your MySQL port (if different)

## Step 4: Install MySQL Python Packages

```bash
cd backend
.\venv\Scripts\activate
pip install pymysql mysqlclient
```

**Note:** If `mysqlclient` installation fails on Windows:
1. Download wheel file from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
2. Install: `pip install mysqlclient‑***.whl`

Or just use PyMySQL (already works):
```bash
pip install pymysql
```

## Step 5: Migrate Data from SQLite

```bash
cd backend
python migrate_to_mysql.py
```

This will:
- Create all tables in MySQL
- Copy all users, quizzes, questions, attempts, and answers
- Preserve all IDs and relationships

## Step 6: Restart Backend

```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 7: Verify Migration

1. Check backend startup logs - should show MySQL connection
2. Login to the application
3. Verify all data is visible:
   - Users list
   - Quizzes
   - Student attempt history
   - Quiz questions

## Troubleshooting

### Error: "Authentication plugin 'caching_sha2_password' cannot be loaded"

**Solution:** Use older authentication method:

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
```

### Error: "Access denied for user"

**Check:**
1. Username and password in `.env` are correct
2. User has proper privileges
3. MySQL service is running

### Error: "Can't connect to MySQL server"

**Check:**
1. MySQL service is running: `services.msc` (Windows) → MySQL
2. Port 3306 is not blocked by firewall
3. Host and port in `.env` are correct

### Error: "mysqlclient installation failed"

**Solution:** Use PyMySQL instead:
```bash
pip uninstall mysqlclient
# Update DATABASE_URL to use pymysql (already set)
```

## Performance Tuning (Optional)

For production, add these to MySQL configuration (`my.ini` or `my.cnf`):

```ini
[mysqld]
max_connections=200
innodb_buffer_pool_size=256M
innodb_log_file_size=64M
query_cache_size=32M
```

## Backup

### Backup MySQL Database:
```bash
mysqldump -u root -p macquiz_db > backup_$(date +%Y%m%d).sql
```

### Restore from Backup:
```bash
mysql -u root -p macquiz_db < backup_20241126.sql
```

## Rollback to SQLite

If you need to go back to SQLite:

1. Edit `.env`:
```env
DATABASE_URL=sqlite:///./quizapp.db
```

2. Restart backend

Your old SQLite database file (`quizapp.db`) is still there!
