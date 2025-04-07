# Apex Bot Deployment Guide for Render

This guide will walk you through deploying your Apex Project Telegram bot on Render's free web service.

## Prerequisites

Before you start, make sure you have:

1. A [Render](https://render.com/) account
2. Your Telegram Bot Token from [@BotFather](https://t.me/botfather)
3. Your Gemini API Key from [Google AI Studio](https://ai.google.dev/)

## Deployment Steps

### 1. Download the Project

First, download your project from Replit as a ZIP file:

1. From your Replit project, click on the "three dots" menu in the upper right corner
2. Select "Download as ZIP"
3. Save the ZIP file to your computer and extract it

### 2. Create Required Files for Render

Create these two files in the root of your project:

**render.yaml**:
```yaml
services:
  - type: web
    name: apex-bot
    env: python
    buildCommand: pip install -r deployment_requirements.txt
    startCommand: gunicorn main:app --bind 0.0.0.0:$PORT --reuse-port --threads 2 --workers 2
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: GEMINI_API_KEY
        sync: false
```

**deployment_requirements.txt**:
```
apscheduler==3.10.4
email-validator==2.1.1
flask==3.0.3
flask-sqlalchemy==3.1.0
google-generativeai==0.4.0
gunicorn==23.0.0
psycopg2-binary==2.9.9
python-telegram-bot==20.8
telegram==0.0.1
```

### 3. Create a Git Repository (Optional but recommended)

```bash
# Initialize a new git repository
git init
git add .
git commit -m "Initial commit for deployment"
```

You can also push this to GitHub, GitLab, or BitBucket if you want.

### 4. Deploy to Render

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" and select "Web Service"
3. Connect your GitHub/GitLab/BitBucket repository, or use "Upload Files" to upload the ZIP
4. Fill in the deployment information:
   - Name: apex-bot (or any name you prefer)
   - Environment: Python
   - Build Command: `pip install -r deployment_requirements.txt`
   - Start Command: `gunicorn main:app --bind 0.0.0.0:$PORT --reuse-port --threads 2 --workers 2`

5. Add the environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `GEMINI_API_KEY`: Your Gemini API key

6. Click "Create Web Service"

### 5. Verify Deployment

1. Once deployed, Render will provide a URL like `https://apex-bot.onrender.com`
2. Visit this URL in your browser to see the bot's status page
3. Try interacting with your Telegram bot to ensure it's responding properly

## Troubleshooting

- If your bot doesn't respond, check the Render logs for any errors
- Ensure your environment variables are set correctly
- Make sure your bot token is valid and the bot hasn't been revoked

## Important Notes

- The free tier of Render may have some limitations on uptime and response time
- Your service will sleep after periods of inactivity
- To keep it always running, consider upgrading to a paid plan or implementing a ping service

## Maintenance

To update your bot in the future:
1. Make changes to your code locally
2. Update your git repository (if using)
3. Render will automatically redeploy when changes are pushed