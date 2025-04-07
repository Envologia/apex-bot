import logging
import re
from config import BOT_TOKEN

# Check if we're in development mode
dev_mode = BOT_TOKEN == "dummy_token_for_development"

try:
    from telegram import Update, Message
    from telegram.ext import (
        ContextTypes,
        CommandHandler,
        MessageHandler,
        filters,
    )
except ImportError:
    # In development mode, import from our mock module
    from mock_telegram import (
        Update, Message, ContextTypes, 
        CommandHandler, MessageHandler, filters
    )
from utils.ai_helper import generate_ai_response

logger = logging.getLogger(__name__)

# Rules message
RULES_MESSAGE = """
*🔒 APEX PROJECT: SACRED PROTOCOLS 🔒*

*Article I: Hierarchy Preservation*
• Respect the authority of Inner Circle members at all times
• Address Apex Intelligence Core with proper reverence
• Defer to seniority in matters of conflict

*Article II: Communication Security*
• All sensitive information must be encrypted
• External channels are considered compromised
• Observe silence protocol in the presence of non-members

*Article III: Knowledge Distribution*
• Classified information is distributed on a need-to-know basis
• Certain archives are accessible only to the Inner Circle
• Request proper clearance before accessing restricted data

*Article IV: Loyalty Requirements*
• Your allegiance to The Apex Project supersedes all others
• Betrayal results in immediate excommunication
• Report dissenters to the Inner Circle without delay

_"Through discipline, we maintain order. Through order, we achieve power."_

⚠️ *Failure to comply will result in severe consequences* ⚠️
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    user = update.effective_user
    bot_username = context.bot.username
    await update.message.reply_text(
        f"*Greetings, {user.first_name}*\n\n"
        "I am your interface to The Apex Project's advanced intelligence network.\n\n"
        f"You may ask me questions directly in this conversation, or tag me in groups with @{bot_username} or @apex.\n\n"
        "_Our knowledge spans across domains. Use it wisely._\n\n"
        "Type /help to learn more about my capabilities.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    from config import HELP_MESSAGE
    
    # Format the help message with the bot's username
    formatted_help = HELP_MESSAGE.format(bot_username=context.bot.username)
    
    await update.message.reply_text(
        formatted_help,
        parse_mode="Markdown"
    )

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /rules command to display the sacred protocols"""
    await update.message.reply_text(
        RULES_MESSAGE,
        parse_mode="Markdown"
    )
    
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /stats command to show user statistics"""
    user = update.effective_user
    
    # In a real implementation, these would be retrieved from a database
    # For now, we'll create sample data
    member_since = "2024-10-15"
    rank = "Initiate"
    contribution_level = "Level 2"
    activity_score = 78
    
    # Create a stats message
    stats_message = f"""
*🔒 CLASSIFIED PERSONNEL FILE: {user.first_name} 🔒*

*Designation:* {user.username or "Unknown"}
*Member ID:* {user.id}
*Clearance Level:* {rank}
*Registered:* {member_since}
*Contribution Status:* {contribution_level}
*Loyalty Metric:* {activity_score}/100

_"Your standing within The Apex Project hierarchy has been assessed."_

⚠️ *This report is for your eyes only* ⚠️
"""
    
    await update.message.reply_text(
        stats_message,
        parse_mode="Markdown"
    )

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages sent to the bot in private chat"""
    # Don't process messages without text
    if not update.message or not update.message.text:
        return
    
    # Don't process commands
    if update.message.text.startswith('/'):
        return
    
    user = update.effective_user
    message_text = update.message.text
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    logger.info(f"Processing private message from {user.id}: {message_text}")
    
    # Get AI response
    try:
        response = await generate_ai_response(message_text, is_private=True)
        
        await update.message.reply_text(
            response,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        await update.message.reply_text(
            "I apologize, but an error occurred while processing your request. Please try again later."
        )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages sent in groups that mention the bot"""
    # Don't process messages without text
    if not update.message or not update.message.text:
        return
    
    message = update.message
    bot_username = context.bot.username
    
    # Check if the bot is mentioned in the message by username or by "apex"
    bot_mention_pattern = fr'@{bot_username}\b'
    apex_mention_pattern = r'@apex\b'
    
    if (not re.search(bot_mention_pattern, str(message.text), re.IGNORECASE) and 
        not re.search(apex_mention_pattern, str(message.text), re.IGNORECASE)):
        return
    
    user = update.effective_user
    
    # Remove the bot mention from the message (with type safety)
    prompt = str(message.text)
    prompt = re.sub(bot_mention_pattern, '', prompt, flags=re.IGNORECASE).strip()
    prompt = re.sub(apex_mention_pattern, '', prompt, flags=re.IGNORECASE).strip()
    
    # If there's no actual question after the mention, don't respond
    if not prompt:
        return
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    logger.info(f"Processing group question from {user.id} in {message.chat.id}: {prompt}")
    
    # Get AI response
    try:
        response = await generate_ai_response(prompt, is_private=False)
        
        await message.reply_text(
            response,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error generating AI response for group message: {e}")
        await message.reply_text(
            "I apologize, but an error occurred while processing your request. Please try again later."
        )

def register_ai_assistant_handlers(dp):
    """Register all handlers related to AI assistant functionality"""
    # Command handlers for private chats
    dp.add_handler(CommandHandler("start", start_command, filters=filters.ChatType.PRIVATE))
    dp.add_handler(CommandHandler("help", help_command, filters=filters.ChatType.PRIVATE))
    dp.add_handler(CommandHandler("rules", rules_command, filters=filters.ChatType.PRIVATE))
    dp.add_handler(CommandHandler("stats", stats_command, filters=filters.ChatType.PRIVATE))
    
    # Command handlers for group chats
    dp.add_handler(CommandHandler("start", start_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("help", help_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("rules", rules_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("stats", stats_command, filters=filters.ChatType.GROUPS))
    
    # Message handlers with proper filtering
    # Group message handler for bot mentions (PRIORITY: higher to check before general private msgs)
    dp.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_message))
    
    # Private chat handler (only private chats, after group handler)
    dp.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private_message))
    
    logger.info("AI assistant handlers registered")
