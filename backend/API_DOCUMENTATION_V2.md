# MacQuiz API v2.0 - Complete Documentation

## 🚀 Overview

MacQuiz v2.0 is a comprehensive quiz management system with advanced features including:
- JWT-based authentication with role-based access control
- Subject and question bank management
- Advanced quiz creation with scheduling and custom marking
- Automatic grading with positive and negative marking
- Comprehensive analytics and reporting

**Base URL:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`

---

## 🔐 Authentication

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

---

## 👥 User Management

### Create User (Admin Only)
```http
POST /api/v1/users/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "email": "student@rbmi.in",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "student",
  "student_id": "CS2024001",
  "department": "Computer Science Engg.",
  "class_year": "1st Year",
  "phone_number": "+1234567890"
}
```

### Bulk User Upload (Admin Only)
```http
POST /api/v1/users/bulk-upload
Authorization: Bearer {admin_token}
Content-Type: multipart/form-data

file: users.csv
```

**CSV Format:**
```csv
email,password,first_name,last_name,role,student_id,department,class_year,phone_number
student1@rbmi.in,Pass123,John,Doe,student,CS2024001,Computer Science,1st Year,1234567890
```

### Get All Users (Admin)
```http
GET /api/v1/users?role=student&department=Computer%20Science
Authorization: Bearer {admin_token}
```

### Update User
```http
PUT /api/v1/users/{user_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "first_name": "Updated Name",
  "phone_number": "+9876543210",
  "is_active": true,
  "password": "NewPassword123!"
}
```

---

## 📚 Subject Management

### Create Subject (Admin/Teacher)
```http
POST /api/v1/subjects/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Data Structures",
  "code": "CS201",
  "description": "Introduction to fundamental data structures",
  "department": "Computer Science Engg."
}
```

### Get All Subjects
```http
GET /api/v1/subjects?department=Computer%20Science&active_only=true
Authorization: Bearer {token}
```

### Get Subject Statistics
```http
GET /api/v1/subjects/{subject_id}/statistics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "subject_id": 1,
  "subject_name": "Data Structures",
  "subject_code": "CS201",
  "total_quizzes": 15,
  "active_quizzes": 10,
  "total_questions_in_bank": 250
}
```

---

## 💡 Question Bank

### Add Question to Bank (Admin/Teacher)
```http
POST /api/v1/question-bank/
Authorization: Bearer {token}
Content-Type: application/json

{
  "subject_id": 1,
  "question_text": "What is the time complexity of binary search?",
  "question_type": "mcq",
  "option_a": "O(n)",
  "option_b": "O(log n)",
  "option_c": "O(n^2)",
  "option_d": "O(1)",
  "correct_answer": "O(log n)",
  "topic": "Searching Algorithms",
  "difficulty": "easy",
  "marks": 1.0
}
```

### Get Questions with Filters
```http
GET /api/v1/question-bank?subject_id=1&difficulty=easy&topic=Algorithms
Authorization: Bearer {token}
```

### Get Question Statistics by Subject
```http
GET /api/v1/question-bank/subjects/{subject_id}/statistics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "subject_id": 1,
  "total_questions": 250,
  "by_difficulty": {
    "easy": 100,
    "medium": 100,
    "hard": 50
  },
  "by_type": {
    "mcq": 200,
    "true_false": 30,
    "short_answer": 20
  }
}
```

---

## 📝 Quiz Management

### Create Quiz (Admin/Teacher)
```http
POST /api/v1/quizzes/
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Data Structures Mid-Term",
  "description": "Covers arrays, linked lists, stacks, and queues",
  "subject_id": 1,
  "department": "Computer Science Engg.",
  "class_year": "2nd Year",
  "scheduled_at": "2025-10-30T10:00:00Z",
  "duration_minutes": 60,
  "grace_period_minutes": 10,
  "marks_per_correct": 1.0,
  "negative_marking": 0.25,
  "questions": [
    {
      "question_text": "What is a stack?",
      "question_type": "mcq",
      "option_a": "FIFO structure",
      "option_b": "LIFO structure",
      "option_c": "Tree structure",
      "option_d": "Graph structure",
      "correct_answer": "LIFO structure",
      "marks": 2.0,
      "question_bank_id": null,
      "order": 0
    }
  ]
}
```

### Get All Quizzes with Filters
```http
GET /api/v1/quizzes?subject_id=1&department=Computer%20Science&is_active=true
Authorization: Bearer {token}
```

### Check Quiz Eligibility
```http
GET /api/v1/quizzes/{quiz_id}/eligibility
Authorization: Bearer {student_token}
```

**Response:**
```json
{
  "eligible": true,
  "quiz_id": 1,
  "title": "Data Structures Mid-Term",
  "duration_minutes": 60,
  "total_marks": 50.0
}
```

### Get Quiz Statistics (Teacher/Admin)
```http
GET /api/v1/quizzes/{quiz_id}/statistics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "quiz_id": 1,
  "quiz_title": "Data Structures Mid-Term",
  "total_marks": 50.0,
  "total_attempts": 45,
  "completed_attempts": 42,
  "in_progress": 3,
  "average_score": 38.5,
  "average_percentage": 77.0,
  "highest_score": 50.0,
  "lowest_score": 15.0,
  "pass_rate": 93.33
}
```

---

## ✍️ Quiz Attempts

### Start Quiz Attempt
```http
POST /api/v1/attempts/start
Authorization: Bearer {student_token}
Content-Type: application/json

{
  "quiz_id": 1
}
```

**Response:**
```json
{
  "id": 100,
  "quiz_id": 1,
  "student_id": 5,
  "score": null,
  "total_marks": 50.0,
  "percentage": null,
  "started_at": "2025-10-25T10:05:00Z",
  "submitted_at": null,
  "time_taken_minutes": null,
  "is_completed": false,
  "is_graded": false
}
```

### Submit Quiz Attempt
```http
POST /api/v1/attempts/{attempt_id}/submit
Authorization: Bearer {student_token}
Content-Type: application/json

{
  "answers": [
    {
      "question_id": 1,
      "answer_text": "LIFO structure"
    },
    {
      "question_id": 2,
      "answer_text": "O(1)"
    }
  ]
}
```

**Response:**
```json
{
  "id": 100,
  "quiz_id": 1,
  "student_id": 5,
  "score": 47.5,
  "total_marks": 50.0,
  "percentage": 95.0,
  "started_at": "2025-10-25T10:05:00Z",
  "submitted_at": "2025-10-25T11:00:00Z",
  "time_taken_minutes": 55.0,
  "is_completed": true,
  "is_graded": true
}
```

### Get My Attempts
```http
GET /api/v1/attempts/my-attempts
Authorization: Bearer {student_token}
```

---

## 📊 Analytics & Reporting

### Dashboard Statistics (Admin)
```http
GET /api/v1/analytics/dashboard
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "total_quizzes": 150,
  "active_quizzes": 45,
  "total_students": 500,
  "active_students": 420,
  "total_teachers": 25,
  "active_teachers": 23,
  "total_subjects": 30,
  "total_questions_bank": 2500,
  "yesterday_assessments": 35,
  "total_attempts": 5000
}
```

### Teacher Statistics
```http
GET /api/v1/analytics/teacher/{teacher_id}/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_quizzes_created": 20,
  "total_questions_authored": 150,
  "students_attempted": 85,
  "average_quiz_score": 78.5,
  "last_quiz_created": "2025-10-20T15:30:00Z",
  "active_quizzes": 12,
  "subjects_taught": 3
}
```

### Student Statistics
```http
GET /api/v1/analytics/student/{student_id}/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_quizzes_attempted": 15,
  "quizzes_completed": 14,
  "average_score": 42.5,
  "average_percentage": 85.0,
  "highest_score": 50.0,
  "lowest_score": 30.0,
  "last_attempt": "2025-10-24T14:00:00Z",
  "pending_quizzes": 5
}
```

### Recent Activity (Admin)
```http
GET /api/v1/analytics/activity/recent?limit=20
Authorization: Bearer {admin_token}
```

### Subject Performance
```http
GET /api/v1/analytics/performance/subject/{subject_id}
Authorization: Bearer {token}
```

### Department Performance
```http
GET /api/v1/analytics/performance/department/{department_name}
Authorization: Bearer {token}
```

---

## 🎯 Advanced Features

### Time-Based Quiz Control
- **Scheduled Start:** Quizzes can be scheduled to start at a specific time
- **Grace Period:** Students can join late within the grace period
- **Auto-Lock:** Quiz automatically locks after grace period expires
- **Duration Control:** Enforced time limits with auto-submission

### Custom Marking Scheme
- **Positive Marking:** Configurable marks for correct answers
- **Negative Marking:** Optional penalty for incorrect answers
- **Per-Question Marks:** Individual question weightage
- **Flexible Scoring:** Custom scoring per quiz

### Question Bank Integration
- **Reusable Questions:** Pull questions from subject-wise banks
- **Difficulty Levels:** Easy, Medium, Hard classification
- **Topic Organization:** Group questions by topics
- **Usage Tracking:** Track how many times questions are used

### Role-Based Permissions
- **Admin:** Full system access, user management, all analytics
- **Teacher:** Create quizzes, manage subjects, view own analytics
- **Student:** Take quizzes, view own performance

---

## 🔧 Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## 📦 Data Models

### User Roles
- `admin` - Full system access
- `teacher` - Create and manage quizzes
- `student` - Take quizzes and view results

### Question Types
- `mcq` - Multiple Choice Questions
- `true_false` - True/False Questions
- `short_answer` - Short Answer Questions

### Difficulty Levels
- `easy` - Easy difficulty
- `medium` - Medium difficulty
- `hard` - Hard difficulty

---

## 🚀 Getting Started

1. **Start Backend:**
   ```bash
   cd backend
   python migrate_v2.py  # Run migration first
   uvicorn app.main:app --reload --port 8000
   ```

2. **Access API Docs:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Default Admin Credentials:**
   - Email: admin@macquiz.com
   - Password: admin123 (change in production)

4. **Test Endpoints:**
   - Use the interactive Swagger UI
   - Or use Postman/curl with Bearer tokens

---

## 📝 Notes

- All datetime fields use UTC timezone
- Tokens expire after 24 hours (configurable)
- File uploads limited to 10MB
- Bulk operations process up to 1000 records at once
- Passwords must be at least 8 characters with mixed case, numbers, and symbols

---

## 🆘 Support

For issues or questions:
- Check API documentation at `/docs`
- Review error messages in responses
- Verify authentication tokens are valid
- Ensure proper role permissions

---

**Version:** 2.0.0  
**Last Updated:** October 25, 2025
