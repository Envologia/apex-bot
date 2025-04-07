#!/usr/bin/env python
import os
import sys
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatJoinRequestHandler, filters

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("telegram_bot.log")
    ]
)

# Configure specialized loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('telegram.ext').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Import configuration and handlers
from config import BOT_TOKEN, REQUIRED_CHANNEL, JOIN_REQUEST_TIMEOUT
from handlers.ai_assistant import register_ai_assistant_handlers
from handlers.group_management import register_group_management_handlers
from handlers.join_request import register_join_request_handlers

# Data structures for the bot's functionality
user_warnings = {}  # Track user warnings
flood_control = {}  # Track message frequency for flood control
chat_settings = {}  # Store chat settings

async def main():
    """Start the bot with detailed error handling and logging"""
    try:
        # Verify token
        if not BOT_TOKEN or BOT_TOKEN == "dummy_token_for_development":
            logger.error("TELEGRAM_BOT_TOKEN is not set or is using the dummy value")
            print("Error: Missing valid TELEGRAM_BOT_TOKEN environment variable. Bot cannot start.")
            sys.exit(1)
            
        # Verify required channel
        if not REQUIRED_CHANNEL or REQUIRED_CHANNEL == "@your_channel":
            logger.warning("REQUIRED_CHANNEL is not set or is using the default value")
            print(f"Warning: REQUIRED_CHANNEL is set to {REQUIRED_CHANNEL}. Join requests may not work properly.")
            
        # Create the Application and bot
        logger.info("Initializing application...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Setup pending join requests dict in bot_data
        application.bot_data["pending_join_requests"] = {}
        
        # Register handlers with detailed error handling
        logger.info("Registering AI assistant handlers...")
        register_ai_assistant_handlers(application)
        
        logger.info("Registering group management handlers...")
        register_group_management_handlers(application, user_warnings, flood_control, chat_settings)
        
        logger.info("Registering join request handlers...")
        register_join_request_handlers(application, application.bot_data["pending_join_requests"])
        
        # Print bot information (for verification)
        bot_info = await application.bot.get_me()
        logger.info(f"Bot initialized: @{bot_info.username} (ID: {bot_info.id})")
        print(f"✓ Bot successfully connected as @{bot_info.username}")
        print("✓ Telegram connection established")
        print(f"✓ Required channel set to {REQUIRED_CHANNEL}")
        print(f"✓ Join request timeout set to {JOIN_REQUEST_TIMEOUT} seconds")
        
        # Start polling with all update types
        logger.info("Starting bot in polling mode...")
        print("Bot is now running. Press Ctrl+C to stop.")
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep the bot running until stopped manually
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Critical error starting bot: {e}", exc_info=True)
        print(f"Error: Failed to start bot: {e}")
        sys.exit(1)
    finally:
        # Ensure proper cleanup
        logger.info("Stopping bot...")
        await application.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually.")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Bot crashed: {e}")
        sys.exit(1)