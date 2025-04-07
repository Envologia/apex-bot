#!/usr/bin/env python
import os
import sys
import threading
import subprocess
import logging
import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, ChatSettings, UserWarning, UserStats, BotStatus
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "apex_project_secret_key")

# Initialize database
db.init_app(app)

# Ensure DATABASE_URL is set
if not app.config['SQLALCHEMY_DATABASE_URI']:
    logger.warning("DATABASE_URL not set, using SQLite database")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apex_bot.db'

# Create scheduler for background tasks
scheduler = BackgroundScheduler()

# Bot process
bot_process = None

# Self-ping URL
self_url = None

def start_bot():
    """Start the Telegram bot in a subprocess"""
    global bot_process
    try:
        # Kill any existing bot process
        if bot_process and bot_process.poll() is None:
            bot_process.terminate()
            
        # Start the bot as a subprocess
        logger.info("Starting Telegram bot process...")
        bot_process = subprocess.Popen(
            ["python", "direct_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Log output from the bot process
        def log_output():
            for line in bot_process.stdout:
                logger.info(f"Bot: {line.strip()}")
        
        # Start thread to log output
        threading.Thread(target=log_output, daemon=True).start()
        
        logger.info("Bot process started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return False

@app.route('/')
def index():
    """Display bot status page"""
    from config import BOT_TOKEN, REQUIRED_CHANNEL, JOIN_REQUEST_TIMEOUT
    bot_running = bot_process and bot_process.poll() is None
    
    # Get bot username
    bot_username = "The_Apex_ProjectBot"
    
    return render_template(
        'index.html',
        bot_running=bot_running,
        bot_username=bot_username,
        required_channel=REQUIRED_CHANNEL,
        join_timeout=JOIN_REQUEST_TIMEOUT
    )

@app.route('/start_bot', methods=['POST'])
def start_bot_route():
    """API endpoint to start the bot"""
    success = start_bot()
    return jsonify({"success": success})

@app.route('/status')
def status():
    """API endpoint to check bot status"""
    bot_running = bot_process and bot_process.poll() is None
    return jsonify({"running": bot_running})

# Self-ping endpoint to keep the service alive
@app.route('/ping')
def ping():
    """Self-ping endpoint to keep the service alive"""
    # Update the bot status in the database
    with app.app_context():
        status = BotStatus.query.first()
        if status:
            status.last_ping = datetime.utcnow()
            status.is_running = bot_process and bot_process.poll() is None
            db.session.commit()
        else:
            # Create a new status record if it doesn't exist
            new_status = BotStatus(
                start_time=datetime.utcnow(),
                last_ping=datetime.utcnow(),
                is_running=bot_process and bot_process.poll() is None
            )
            db.session.add(new_status)
            db.session.commit()
    
    return jsonify({"status": "alive", "timestamp": datetime.utcnow().isoformat()})

def self_ping_task():
    """Task to self-ping the application to keep it alive"""
    global self_url
    if self_url:
        try:
            logger.info(f"Self-pinging at {self_url}/ping")
            response = requests.get(f"{self_url}/ping", timeout=10)
            if response.status_code == 200:
                logger.info("Self-ping successful")
            else:
                logger.warning(f"Self-ping failed with status code {response.status_code}")
        except Exception as e:
            logger.error(f"Self-ping failed: {e}")

def update_metrics_task():
    """Task to update bot metrics in the database"""
    with app.app_context():
        status = BotStatus.query.first()
        if status:
            status.is_running = bot_process and bot_process.poll() is None
            if not status.is_running and hasattr(app, '_bot_started'):
                # Attempt to restart the bot if it's not running
                logger.info("Bot appears to be down, attempting to restart")
                start_bot()
            db.session.commit()

# Initialize the database tables
with app.app_context():
    db.create_all()
    # Check if we have a BotStatus record, create one if not
    if not BotStatus.query.first():
        initial_status = BotStatus(
            start_time=datetime.utcnow(),
            last_ping=datetime.utcnow(),
            is_running=True
        )
        db.session.add(initial_status)
        db.session.commit()

# Start bot when server starts
start_bot()

# Register before_first_request handler using the latest Flask pattern
with app.app_context():
    @app.before_request
    def before_request():
        # Only run once on first request
        if not hasattr(app, '_bot_started'):
            app._bot_started = True
            # Restart the bot to ensure it's running
            start_bot()
            
            # Set up the self URL for pinging
            global self_url
            if 'REPLIT_CLUSTER' in os.environ:
                # We're on Replit, use the Replit URL
                replit_slug = os.environ.get('REPL_SLUG', 'apex-bot')
                replit_owner = os.environ.get('REPL_OWNER', 'user')
                self_url = f"https://{replit_slug}.{replit_owner}.repl.co"
            elif 'RENDER' in os.environ:
                # We're on Render, use the Render URL
                render_url = os.environ.get('RENDER_EXTERNAL_URL')
                if render_url:
                    self_url = render_url
                else:
                    # Fallback to localhost for testing
                    self_url = "http://localhost:5000"
            else:
                # Fallback to localhost for testing
                self_url = "http://localhost:5000"
            
            logger.info(f"Self-ping URL set to {self_url}")
            
            # Start the scheduler for self-pinging
            scheduler.add_job(self_ping_task, 'interval', minutes=10)
            scheduler.add_job(update_metrics_task, 'interval', minutes=5)
            scheduler.start()
            logger.info("Background tasks scheduler started")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
