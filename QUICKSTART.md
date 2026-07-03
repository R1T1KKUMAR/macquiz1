# QuickStart Guide - MacQuiz Application

## Complete Setup in 5 Minutes

### Step 1: Start the Backend (1 minute)

```bash
cd backend
./run.sh
```

The backend will:
- Create virtual environment (if needed)
- Install all dependencies
- Create admin user automatically
- Start server on http://localhost:8000

**Backend is ready when you see:**
```
Admin user created: admin@macquiz.com
INFO: Application startup complete.
```

### Step 2: Start the Frontend (2 minutes)

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

**Frontend is ready when you see:**
```
Local: http://localhost:5173/
```

### Step 3: Login (30 seconds)

1. Open browser to http://localhost:5173
2. Login with:
   - **Username**: `admin@macquiz.com`
   - **Password**: `admin123`

### Step 4: Explore Features (1.5 minutes)

#### As Admin:
1. **Dashboard** - View system statistics
2. **Users** - Create teachers and students
3. **Teachers** - Monitor teacher activity
4. **Students** - Track student performance
5. **Detailed Reports** - AI-powered analytics

#### Create Your First Student:
1. Click "Dashboard" → "Add Teacher / Student" button
2. Fill in details:
   - Role: Student
   - First Name: John
   - Last Name: Doe
   - Email: john@example.com
   - Password: student123
   - Student ID: CS2024001
   - Department: Computer Science Engg.
   - Class/Year: 1st Year
3. Click "Create User"

#### Create Your First Teacher:
1. Click "Users" → "Add New User"
2. Fill in details:
   - Role: Teacher
   - First Name: Jane
   - Last Name: Smith
   - Email: jane@example.com
   - Password: teacher123
   - Department: Computer Science Engg.
3. Click "Create User"

### Step 5: Test the API (Optional)

#### Get API Documentation:
Visit http://localhost:8000/docs

#### Test Login via API:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login-json \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@macquiz.com","password":"admin123"}'
```

## API Endpoints Summary

### Authentication
- Login: `POST /api/v1/auth/login-json`

### User Management (Admin)
- Create User: `POST /api/v1/users/`
- List Users: `GET /api/v1/users/`
- Get User: `GET /api/v1/users/{id}`
- Update User: `PUT /api/v1/users/{id}`
- Delete User: `DELETE /api/v1/users/{id}`

### Quiz Management (Teacher/Admin)
- Create Quiz: `POST /api/v1/quizzes/`
- List Quizzes: `GET /api/v1/quizzes/`
- Get Quiz: `GET /api/v1/quizzes/{id}`
- Update Quiz: `PUT /api/v1/quizzes/{id}`
- Delete Quiz: `DELETE /api/v1/quizzes/{id}`

### Quiz Attempts (Students)
- Start Attempt: `POST /api/v1/attempts/start`
- Submit Answers: `POST /api/v1/attempts/submit`
- My Attempts: `GET /api/v1/attempts/my-attempts`

### Analytics (Admin)
- Dashboard Stats: `GET /api/v1/attempts/stats/dashboard`
- Recent Activity: `GET /api/v1/attempts/stats/activity`

## Troubleshooting

### Backend won't start:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
uvicorn app.main:app --reload
```

### Frontend won't start:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Can't login:
- Check backend is running on port 8000
- Default credentials: `admin@macquiz.com` / `admin123`
- Check browser console for errors

### CORS errors:
- Ensure backend CORS_ORIGINS includes frontend URL
- Default: `http://localhost:5173,http://localhost:3000`
- Edit `backend/.env` if needed

## Next Steps

1. **Create more users**: Add teachers and students
2. **Create quizzes**: Login as teacher and create assessments
3. **Take quizzes**: Login as student and attempt quizzes
4. **View analytics**: Check admin dashboard for insights
5. **Customize**: Update branding, colors, and features

## Production Deployment

### Backend:
1. Change SECRET_KEY in .env
2. Change admin password
3. Use PostgreSQL instead of SQLite
4. Set up proper CORS origins
5. Enable HTTPS

### Frontend:
1. Update API URL in environment variables
2. Build: `npm run build`
3. Deploy to hosting service (Vercel, Netlify, etc.)

## Support

- API Examples: `backend/API_EXAMPLES.md`
- Backend README: `backend/README.md`
- Main README: `README.md`

## Default Credentials

**Admin:**
- Email: `admin@macquiz.com`
- Password: `admin123`

⚠️ **Change these in production!**

---

**Happy Quizzing! 🎯**
