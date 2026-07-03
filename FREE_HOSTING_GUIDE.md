# Free Hosting Guide (MacQuiz)

This guide gives you a **fully free starter deployment** using:
- **Frontend**: Vercel (free)
- **Backend (FastAPI)**: Vercel Serverless (free)
- **Database**: Supabase Postgres (free tier)

> Note: Free-tier limits can change over time. If any plan changes, keep the same architecture and swap to another free Postgres provider.

## 1) Create free Postgres database (Supabase)

1. Create a new project in Supabase.
2. Open **Project Settings → Database**.
3. Copy your connection string and use this SQLAlchemy format:

```env
DATABASE_URL=postgresql+psycopg://USER:ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require
```

Use the **Supabase Session Pooler** endpoint (IPv4). Do not use `db.<project-ref>.supabase.co` for Vercel.
Also URL-encode password special characters like `? / + & @ :`.

## 2) Deploy backend to Vercel

Your backend is already configured with [backend/vercel.json](backend/vercel.json).

1. Push this repo to GitHub.
2. In Vercel, **Add New Project** and import the repo.
3. Set **Root Directory** to `backend`.
4. Add these environment variables in Vercel (Project Settings → Environment Variables):

```env
DATABASE_URL=postgresql+psycopg://USER:ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require
SECRET_KEY=generate-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:5173
CORS_ORIGIN_REGEX=^https://.*\.vercel\.app$
CORS_ALLOW_CREDENTIALS=true
ADMIN_EMAIL=admin@macquiz.com
ADMIN_PASSWORD=change-this-password
```

5. Deploy.
6. Open backend URL once and verify:
   - `/docs` loads
   - login endpoint works

## 3) Deploy frontend to Vercel

Your frontend is already configured with [frontend/vercel.json](frontend/vercel.json).

1. In Vercel, create a second project from the same repo.
2. Set **Root Directory** to `frontend`.
3. Add environment variable:

```env
VITE_API_BASE_URL=https://your-backend-domain.vercel.app
```

4. Deploy.

## 4) Update CORS after frontend domain is final

After frontend deploy completes, copy the final frontend URL and update backend `CORS_ORIGINS` to include it.

Example:

```env
CORS_ORIGINS=https://macquiz-frontend.vercel.app,http://localhost:5173
```

Redeploy backend after updating env values.

## 5) First-login checklist

- Login with admin credentials.
- Create one teacher and one student.
- Create a test quiz and submit one attempt.
- Confirm data persists after redeploy.

## 6) If you prefer MySQL

Your backend also supports MySQL (`pymysql` already included). Use this format:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DB_NAME
```

But for easiest free setup today, Postgres (Supabase) is typically simpler.
