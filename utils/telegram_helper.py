import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

async def check_user_membership(bot: Bot, channel_id: str, user_id: int) -> bool:
    """
    Check if a user is a member of a specific channel
    
    Args:
        bot: The Telegram bot instance
        channel_id: Channel ID or username (with @)
        user_id: User ID to check
        
    Returns:
        bool: True if user is a member, False otherwise
    """
    try:
        chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking membership status for user {user_id} in channel {channel_id}: {e}")
        return False

async def send_formatted_message(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """
    Send a message with proper error handling
    
    Args:
        bot: The Telegram bot instance
        chat_id: Target chat ID
        text: Message text
        **kwargs: Additional arguments for send_message
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return True
    except TelegramError as e:
        logger.error(f"Error sending message to chat {chat_id}: {e}")
        return False

async def delete_message_safe(bot: Bot, chat_id: int, message_id: int) -> bool:
    """
    Delete a message with proper error handling
    
    Args:
        bot: The Telegram bot instance
        chat_id: Chat ID
        message_id: Message ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except TelegramError as e:
        logger.error(f"Error deleting message {message_id} in chat {chat_id}: {e}")
        return False

async def restrict_chat_member_safe(bot: Bot, chat_id: int, user_id: int, permissions, until_date=None) -> bool:
    """
    Restrict a chat member with proper error handling
    
    Args:
        bot: The Telegram bot instance
        chat_id: Chat ID
        user_id: User ID to restrict
        permissions: ChatPermissions object
        until_date: Optional timestamp for restriction end
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id, 
            user_id=user_id, 
            permissions=permissions, 
            until_date=until_date
        )
        return True
    except TelegramError as e:
        logger.error(f"Error restricting user {user_id} in chat {chat_id}: {e}")
        return False
