# API Usage Examples

This document provides examples of how to use the MacQuiz API endpoints.

## Authentication

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login-json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@macquiz.com",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## User Management

### Create a Student
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "student1@example.com",
    "password": "student123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "student_id": "CS2024001",
    "department": "Computer Science Engg.",
    "class_year": "1st Year"
  }'
```

### Create a Teacher
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "teacher1@example.com",
    "password": "teacher123",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "teacher",
    "department": "Computer Science Engg."
  }'
```

### Get All Users
```bash
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Current User Info
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Teacher Activity
```bash
curl -X GET http://localhost:8000/api/v1/users/activity/teachers \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Student Activity
```bash
curl -X GET http://localhost:8000/api/v1/users/activity/students \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Quiz Management

### Create a Quiz
```bash
curl -X POST http://localhost:8000/api/v1/quizzes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Python Basics Quiz",
    "description": "Test your knowledge of Python fundamentals",
    "department": "Computer Science Engg.",
    "class_year": "1st Year",
    "duration_minutes": 30,
    "questions": [
      {
        "question_text": "What is Python?",
        "question_type": "mcq",
        "option_a": "A snake",
        "option_b": "A programming language",
        "option_c": "A database",
        "option_d": "An operating system",
        "correct_answer": "B",
        "marks": 2.0
      },
      {
        "question_text": "Python is an interpreted language.",
        "question_type": "true_false",
        "correct_answer": "True",
        "marks": 1.0
      }
    ]
  }'
```

### Get All Quizzes
```bash
curl -X GET "http://localhost:8000/api/v1/quizzes/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Quiz Details
```bash
curl -X GET "http://localhost:8000/api/v1/quizzes/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Quiz
```bash
curl -X PUT http://localhost:8000/api/v1/quizzes/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Python Basics Quiz - Updated",
    "is_active": true
  }'
```

### Delete Quiz
```bash
curl -X DELETE http://localhost:8000/api/v1/quizzes/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Quiz Attempts

### Start Quiz Attempt
```bash
curl -X POST http://localhost:8000/api/v1/attempts/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "quiz_id": 1
  }'
```

Response:
```json
{
  "id": 1,
  "quiz_id": 1,
  "student_id": 2,
  "score": null,
  "total_marks": 3.0,
  "percentage": null,
  "started_at": "2024-01-15T10:30:00",
  "submitted_at": null
}
```

### Submit Quiz Attempt
```bash
curl -X POST http://localhost:8000/api/v1/attempts/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "attempt_id": 1,
    "answers": [
      {
        "question_id": 1,
        "answer_text": "B"
      },
      {
        "question_id": 2,
        "answer_text": "True"
      }
    ]
  }'
```

### Get My Attempts
```bash
curl -X GET http://localhost:8000/api/v1/attempts/my-attempts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Quiz Attempts (Admin/Teacher)
```bash
curl -X GET http://localhost:8000/api/v1/attempts/quiz/1/attempts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Dashboard Statistics

### Get Dashboard Stats (Admin)
```bash
curl -X GET http://localhost:8000/api/v1/attempts/stats/dashboard \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "total_quizzes": 5,
  "active_students": 15,
  "total_students": 20,
  "yesterday_assessments": 8,
  "yesterday_attendance": 12,
  "active_teachers_today": 3,
  "total_teachers": 5
}
```

### Get Recent Activity (Admin)
```bash
curl -X GET "http://localhost:8000/api/v1/attempts/stats/activity?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Using with JavaScript/Frontend

### Login Example
```javascript
const login = async () => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login-json', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: 'admin@macquiz.com',
      password: 'admin123'
    })
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
};
```

### Create User Example
```javascript
const createUser = async (userData) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/v1/users/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(userData)
  });
  
  return await response.json();
};
```

### Get Quizzes Example
```javascript
const getQuizzes = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/v1/quizzes/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

## Common Headers

All authenticated requests should include:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

## Rate Limiting

Currently no rate limiting is implemented. Consider adding it for production.

## CORS Configuration

Default allowed origins are configured in `.env`:
- http://localhost:5173 (Vite dev server)
- http://localhost:3000 (React dev server)

Add more origins as needed in the `CORS_ORIGINS` environment variable.
