# Deployment Guide

## Deploy to Render

This application is configured for easy deployment to Render.

### Quick Deploy

1. **Sign in to Render**: Go to https://render.com and sign in
2. **New Web Service**: Click "New +" → "Web Service"
3. **Connect Repository**:
   - Connect your GitHub account if not already connected
   - Select the `bearded-bytes/warhammer-cheatsheet` repository
4. **Configure Service**:
   - **Name**: `warhammer-cheatsheet` (or your preferred name)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or paid if you prefer)
5. **Deploy**: Click "Create Web Service"

Render will automatically:
- Install dependencies from `requirements.txt`
- Start the app with Gunicorn
- Assign a URL like `https://warhammer-cheatsheet.onrender.com`

### Using render.yaml (Alternative)

The included `render.yaml` file allows you to deploy with Infrastructure as Code:

1. In Render dashboard, go to "Blueprint" → "New Blueprint Instance"
2. Connect your repository
3. Render will automatically detect `render.yaml` and configure everything

### Environment Variables

The app automatically configures itself for production. No manual environment variables needed!

- `PORT` - Automatically set by Render
- `FLASK_ENV=production` - Set in render.yaml

### After Deployment

Once deployed, your app will be available at:
```
https://your-app-name.onrender.com
```

Users can paste their BattleScribe army lists and the app will:
- Auto-detect the faction
- Download catalogues from BSData GitHub
- Generate cheat sheets in-memory
- No disk usage for catalogues!

### Free Tier Limitations

Render's free tier:
- ✅ 750 hours/month
- ✅ 512MB RAM (enough for this app)
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Cold start takes ~30 seconds on first request

For production use, consider the $7/month paid tier for always-on service.

### Troubleshooting

**Build fails?**
- Check that `requirements.txt` is committed
- Verify Python version compatibility

**App crashes on start?**
- Check Render logs in the dashboard
- Ensure all dependencies are in `requirements.txt`

**Catalogues not downloading?**
- Verify outbound HTTPS is allowed (should be by default)
- Check BSData GitHub is accessible

### Local Testing

Test the production setup locally:
```bash
pip install -r requirements.txt
PORT=5000 FLASK_ENV=production gunicorn app:app
```

Visit http://localhost:8000

---

## Alternative Platforms

### Railway
1. Sign in to railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Select repository → Railway auto-detects Flask
4. Deploy!

### Heroku
1. Create `Procfile`: `web: gunicorn app:app`
2. Push to Heroku: `git push heroku main`

### Fly.io
1. Install flyctl: `fly auth signup`
2. Launch: `fly launch`
3. Deploy: `fly deploy`
