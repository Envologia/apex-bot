#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackQueryHandler, ChatJoinRequestHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import configuration
from config import BOT_TOKEN, REQUIRED_CHANNEL, JOIN_REQUEST_TIMEOUT

# Import handler registrations
from handlers.ai_assistant import register_ai_assistant_handlers
from handlers.group_management import register_group_management_handlers
from handlers.join_request import register_join_request_handlers

async def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize data structures
    user_warnings = {}
    flood_control = {}
    chat_settings = {}
    pending_join_requests = {}
    
    # Add the data structures to application.bot_data
    application.bot_data["pending_join_requests"] = pending_join_requests
    application.bot_data["user_warnings"] = user_warnings
    application.bot_data["flood_control"] = flood_control
    application.bot_data["chat_settings"] = chat_settings
    
    # Register handlers
    register_ai_assistant_handlers(application)
    register_group_management_handlers(application, user_warnings, flood_control, chat_settings)
    register_join_request_handlers(application, pending_join_requests)
    
    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # Get bot info and print
    bot_info = await application.bot.get_me()
    print(f"Started bot @{bot_info.username}")
    print(f"Required channel: {REQUIRED_CHANNEL}")
    print(f"Join timeout: {JOIN_REQUEST_TIMEOUT} seconds")
    
    # Run until Ctrl+C
    print("Bot is running. Press Ctrl+C to stop.")
    
    # Keep the bot running until manually stopped
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        # Print banner
        print("\n░█▀█░█▀█░█▀▀░█░█░░░█▀█░█▀▄░█▀█░▀▀█░█▀▀░█▀▀░▀█▀")
        print("░█▀█░█▀▀░█▀▀░▄▀▄░░░█▀▀░█▀▄░█░█░░░█░█▀▀░█░░░░█░")
        print("░▀░▀░▀░░░▀▀▀░▀░▀░░░▀░░░▀░▀░▀▀▀░▀▀░░▀▀▀░▀▀▀░░▀░")
        print("\nInitializing Apex Project Telegram Bot...\n")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Unhandled exception")
        sys.exit(1)