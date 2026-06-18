# AI Factory

## Upload to GitHub

1. Create a new GitHub repository
2. Upload all files from this folder
3. Done

## Deploy frontend (Vercel)

1. Connect your GitHub repo to vercel.com
2. Set root directory to `/` and framework to "Other"
3. Before deploying: edit `index.html` line 1 — add `data-api-url="https://your-backend-url"` to the `<html>` tag

## Deploy backend (Render)

1. Connect your GitHub repo to render.com → New Web Service
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `STORAGE_PROVIDER=memory`
5. Add environment variable: `ALLOWED_ORIGINS=https://your-frontend.vercel.app`
