# MacQuiz Backend

FastAPI backend for the MacQuiz application.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **User Management**: Admin can create/manage teachers and students
- **Quiz Management**: Teachers can create quizzes with multiple question types
- **Quiz Attempts**: Students can attempt quizzes and get instant results
- **Dashboard Analytics**: Real-time statistics and activity tracking
- **RESTful API**: Clean and documented API endpoints

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the backend directory (already created):

```env
DATABASE_URL=sqlite:///./quizapp.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
ADMIN_EMAIL=admin@macquiz.com
ADMIN_PASSWORD=admin123
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### 5. Default Admin Credentials

- **Email**: admin@macquiz.com
- **Password**: admin123

**Important**: Change these credentials in production!

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login (OAuth2 form)
- `POST /api/v1/auth/login-json` - Login (JSON)

### Users
- `POST /api/v1/users/` - Create user (Admin only)
- `GET /api/v1/users/` - Get all users (Admin only)
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users/{user_id}` - Get user by ID (Admin only)
- `PUT /api/v1/users/{user_id}` - Update user (Admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (Admin only)
- `GET /api/v1/users/activity/teachers` - Get teacher activity (Admin only)
- `GET /api/v1/users/activity/students` - Get student activity (Admin only)

### Quizzes
- `POST /api/v1/quizzes/` - Create quiz (Admin/Teacher)
- `GET /api/v1/quizzes/` - Get all quizzes
- `GET /api/v1/quizzes/{quiz_id}` - Get quiz details
- `PUT /api/v1/quizzes/{quiz_id}` - Update quiz (Admin/Teacher)
- `DELETE /api/v1/quizzes/{quiz_id}` - Delete quiz (Admin/Teacher)

### Quiz Attempts
- `POST /api/v1/attempts/start` - Start quiz attempt
- `POST /api/v1/attempts/submit` - Submit quiz attempt
- `GET /api/v1/attempts/my-attempts` - Get user's attempts
- `GET /api/v1/attempts/quiz/{quiz_id}/attempts` - Get quiz attempts (Admin/Teacher)
- `GET /api/v1/attempts/stats/dashboard` - Get dashboard stats (Admin only)
- `GET /api/v1/attempts/stats/activity` - Get recent activity (Admin only)

## Database Schema

### Users Table
- Authentication and user profile information
- Roles: admin, teacher, student
- Student-specific fields: student_id, department, class_year

### Quizzes Table
- Quiz metadata and configuration
- Creator tracking
- Department and class year filters

### Questions Table
- Multiple question types: MCQ, True/False, Short Answer
- Options and correct answers
- Marks allocation

### Quiz Attempts Table
- Student attempts tracking
- Score calculation and percentage
- Attempt timing

### Answers Table
- Student responses
- Correctness evaluation
- Marks awarded

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py         # User management endpoints
│   │       ├── quizzes.py       # Quiz management endpoints
│   │       └── attempts.py      # Quiz attempt endpoints
│   ├── core/
│   │   ├── config.py           # Configuration settings
│   │   ├── security.py         # Security utilities
│   │   └── deps.py             # Dependencies (auth, permissions)
│   ├── db/
│   │   └── database.py         # Database connection
│   ├── models/
│   │   └── models.py           # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py          # Pydantic schemas
│   └── main.py                 # FastAPI application
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development

### Running Tests
```bash
# Add pytest later
pytest
```

### Database Migrations
```bash
# Using Alembic (setup later if needed)
alembic revision --autogenerate -m "migration message"
alembic upgrade head

# PostgreSQL safe constraint/index migration (duplicate pre-checks)
python migrate_postgres_constraints.py          # dry run (recommended first)
python migrate_postgres_constraints.py --apply  # apply only safe indexes
python migrate_postgres_constraints.py --apply --auto-fix --backup-file ./pre_dedupe.dump
```

### Code Quality
```bash
# Format code
black app/

# Lint code
flake8 app/
```

## Deployment

### Production Checklist
- [ ] Change SECRET_KEY in .env
- [ ] Change default admin credentials
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up logging
- [ ] Configure rate limiting
- [ ] Set up monitoring

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Support

For issues and questions, please create an issue in the repository.
