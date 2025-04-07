import os
import logging
from config import BOT_TOKEN

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if we're using a development token
dev_mode = BOT_TOKEN == "dummy_token_for_development"
if dev_mode:
    logger.warning("Running in development mode with dummy token. Telegram functionality will be limited.")

# Import the necessary modules based on mode
try:
    # Try to import from apscheduler
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    logger.error("Failed to import BackgroundScheduler from apscheduler")
    # Create a mock scheduler for development
    class MockScheduler:
        def __init__(self):
            pass
            
        def add_job(self, func, trigger, **kwargs):
            logger.info(f"[MOCK] Added job with trigger {trigger}")
            return None
            
        def start(self):
            logger.info("[MOCK] Started scheduler")
            
        def shutdown(self):
            logger.info("[MOCK] Shut down scheduler")
    
    BackgroundScheduler = MockScheduler

# Create bot and application instances
try:
    # Import from python-telegram-bot
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        CallbackQueryHandler,
        ChatJoinRequestHandler,
    )
    from telegram import Update, Bot
    logger.info("Successfully imported Telegram modules")
except ImportError:
    logger.error("Failed to import from python-telegram-bot package, using mock classes")
    
    # Import our mock classes
    from mock_telegram import (
        Update, Bot, Application, CommandHandler, MessageHandler, 
        CallbackQueryHandler, ChatJoinRequestHandler, filters
    )

# Create bot instance
bot = Bot(token=BOT_TOKEN)

# Create Application instance for handling updates
dp = Application.builder().bot(bot).build()

# Create scheduler for timed tasks
scheduler = BackgroundScheduler()

# Dictionary to store pending join requests
# Structure: {user_id: {"chat_id": chat_id, "request_id": request_id, "timestamp": timestamp}}
pending_join_requests = {}

# In-memory storage for user warnings and flood control
# Structure: {chat_id: {user_id: {"warnings": count, "last_warning": timestamp}}}
user_warnings = {}

# Structure: {chat_id: {user_id: [message_timestamps]}}
flood_control = {}

# Structure: {chat_id: {"enabled": bool, "banned_content": ["url", etc]}}
chat_settings = {}

# Register handlers
from handlers.join_request import register_join_request_handlers
from handlers.ai_assistant import register_ai_assistant_handlers
from handlers.group_management import register_group_management_handlers

# Register all handlers - simplified for now due to filter compatibility issues
try:
    # Register handlers
    register_join_request_handlers(dp, pending_join_requests)
    register_ai_assistant_handlers(dp)
    register_group_management_handlers(dp, user_warnings, flood_control, chat_settings)
    logger.info("All handlers registered successfully")
except Exception as e:
    logger.error(f"Error registering handlers: {e}")
    
    # Fallback for development mode when handler registration fails
    if dev_mode:
        logger.warning("Using simplified handlers for development mode")
        # Add basic command handlers directly
        from handlers.ai_assistant import start_command, help_command
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("help", help_command))

logger.info("Bot initialized successfully")
