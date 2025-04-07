from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create an instance of SQLAlchemy
db = SQLAlchemy()

class ChatSettings(db.Model):
    """Settings for each chat where the bot is active"""
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger, unique=True, nullable=False)
    chat_title = db.Column(db.String(255), nullable=True)
    welcome_enabled = db.Column(db.Boolean, default=True)
    ai_responses_enabled = db.Column(db.Boolean, default=True)
    moderation_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChatSettings {self.chat_id} ({self.chat_title})>"

class UserWarning(db.Model):
    """Warnings issued to users"""
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    warned_at = db.Column(db.DateTime, default=datetime.utcnow)
    warned_by = db.Column(db.BigInteger, nullable=True)
    
    def __repr__(self):
        return f"<UserWarning {self.user_id} in {self.chat_id}>"

class UserStats(db.Model):
    """Statistics for each user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    chat_id = db.Column(db.BigInteger, nullable=False)
    message_count = db.Column(db.Integer, default=0)
    ai_requests = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'chat_id'),)
    
    def __repr__(self):
        return f"<UserStats {self.user_id} in {self.chat_id}>"

class BotStatus(db.Model):
    """Bot status and metrics"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_ping = db.Column(db.DateTime, default=datetime.utcnow)
    total_messages = db.Column(db.Integer, default=0)
    total_ai_requests = db.Column(db.Integer, default=0)
    errors_count = db.Column(db.Integer, default=0)
    is_running = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<BotStatus started at {self.start_time}>"