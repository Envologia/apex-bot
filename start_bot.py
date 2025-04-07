#!/usr/bin/env python
import os
import logging
import asyncio
import sys

# Add additional error handling and debugging
logging.basicConfig(level=logging.DEBUG,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                  stream=sys.stdout)

# Configure additional logging to see more details
logging.getLogger('httpx').setLevel(logging.DEBUG)
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('telegram.ext').setLevel(logging.DEBUG)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatJoinRequestHandler, filters
from handlers.ai_assistant import start_command, help_command, handle_private_message, handle_group_message
from handlers.group_management import (ban_command, mute_command, warn_command, pin_command, 
                                      settings_command, toggle_setting_callback, close_settings_callback,
                                      handle_new_chat_members, check_flood_control, check_banned_content)
from handlers.join_request import handle_join_request, check_joined_callback, check_join_request_timeout
from config import BOT_TOKEN

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data structures for the bot's functionality
user_warnings = {}  # Track user warnings
flood_control = {}  # Track message frequency for flood control
chat_settings = {}  # Store chat settings
pending_join_requests = {}  # Track pending join requests

def main():
    """Start the bot."""
    # Create the Application with built-in job queue
    builder = Application.builder().token(BOT_TOKEN)
    application = builder.build()
    
    # Register handlers from each module
    from handlers.join_request import register_join_request_handlers
    register_join_request_handlers(application, pending_join_requests)
    
    from handlers.ai_assistant import register_ai_assistant_handlers
    register_ai_assistant_handlers(application)
    
    from handlers.group_management import register_group_management_handlers
    register_group_management_handlers(application, user_warnings, flood_control, chat_settings)
    
    # Start the Bot in polling mode (connect directly to Telegram API)
    logger.info("Starting bot in polling mode...")
    
    # This is a more modern approach for python-telegram-bot v20+
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        # Debug print to check token
        token = BOT_TOKEN
        logger.info(f"Bot token set: {bool(token)}")
        if not token or token == "dummy_token_for_development":
            logger.error("TELEGRAM_BOT_TOKEN environment variable is not set or has dummy value")
            exit(1)
        
        # Run the bot
        main()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()