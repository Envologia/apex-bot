#!/usr/bin/env python
import os
import sys
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configure specialized loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.DEBUG)
logging.getLogger('telegram.ext').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Import configuration and handlers
from config import BOT_TOKEN
from handlers.ai_assistant import register_ai_assistant_handlers
from handlers.group_management import register_group_management_handlers

# Data structures for the bot's functionality
user_warnings = {}      # Track user warnings
flood_control = {}      # Track message frequency for flood control
chat_settings = {}      # Store chat settings

async def main():
    """Start the bot with direct Telegram API connection"""
    try:
        # Verify token
        if not BOT_TOKEN or BOT_TOKEN == "dummy_token_for_development":
            logger.error("TELEGRAM_BOT_TOKEN is not set or is using the dummy value")
            print("Error: Missing valid TELEGRAM_BOT_TOKEN environment variable. Bot cannot start.")
            sys.exit(1)
            
        # Create the Application and bot
        logger.info("Initializing application...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Register handlers with detailed error handling
        logger.info("Registering AI assistant handlers...")
        register_ai_assistant_handlers(application)
        
        logger.info("Registering group management handlers...")
        register_group_management_handlers(application, user_warnings, flood_control, chat_settings)
        
        # Print bot information (for verification)
        bot_info = await application.bot.get_me()
        logger.info(f"Bot initialized: @{bot_info.username} (ID: {bot_info.id})")
        print(f"✓ Bot successfully connected as @{bot_info.username}")
        print("✓ Telegram connection established")
        
        # Start polling with all update types
        logger.info("Starting bot in polling mode...")
        print("\nBot is now running. Press Ctrl+C to stop.")
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
        try:
            logger.info("Stopping bot...")
            await application.stop()
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")

if __name__ == '__main__':
    try:
        # Print banner
        print("\n░█▀█░█▀█░█▀▀░█░█░░░█▀█░█▀▄░█▀█░▀▀█░█▀▀░█▀▀░▀█▀")
        print("░█▀█░█▀▀░█▀▀░▄▀▄░░░█▀▀░█▀▄░█░█░░░█░█▀▀░█░░░░█░")
        print("░▀░▀░▀░░░▀▀▀░▀░▀░░░▀░░░▀░▀░▀▀▀░▀▀░░▀▀▀░▀▀▀░░▀░")
        print("\nStarting Apex Project Telegram Bot...\n")
        
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped manually.")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Bot crashed: {e}")
        sys.exit(1)