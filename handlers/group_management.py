import logging
import time
import re
from config import BOT_TOKEN

# Check if we're in development mode
dev_mode = BOT_TOKEN == "dummy_token_for_development"

try:
    from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.ext import (
        ContextTypes,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        filters,
    )
except ImportError:
    # In development mode, import from our mock module
    from mock_telegram import (
        Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton,
        ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    )
from config import (
    MAX_FLOOD_MESSAGES,
    FLOOD_TIME_WINDOW,
    SLOW_MODE_INTERVAL,
    WARNING_EXPIRE_HOURS,
    MAX_WARNINGS,
    BANNED_CONTENT_TYPES,
    WELCOME_MESSAGE
)

logger = logging.getLogger(__name__)

# Helper functions
async def is_admin(chat_id, user_id, context):
    """Check if a user is an admin in the chat"""
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def check_flood_control(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle flood control for group messages"""
    message = update.message
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Don't apply flood control to admins
    if await is_admin(chat_id, user_id, context):
        return
    
    # Get or initialize flood control data for the chat
    flood_control = context.bot_data.setdefault("flood_control", {})
    chat_flood = flood_control.setdefault(chat_id, {})
    user_msgs = chat_flood.setdefault(user_id, [])
    
    # Add current message timestamp
    current_time = time.time()
    user_msgs.append(current_time)
    
    # Remove old messages from tracking
    user_msgs = [t for t in user_msgs if current_time - t <= FLOOD_TIME_WINDOW]
    chat_flood[user_id] = user_msgs
    
    # Check if user is flooding
    if len(user_msgs) > MAX_FLOOD_MESSAGES:
        try:
            # Mute the user for a short time
            until_date = current_time + 60  # 1 minute mute
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False
            )
            
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=permissions,
                until_date=until_date
            )
            
            # Generate AI-powered flood warning
            from utils.ai_helper import generate_banned_content_response
            flood_message = await generate_banned_content_response(
                message.from_user.first_name, 
                "message flooding"
            )
            
            # Fall back to default message if AI fails
            if not flood_message:
                flood_message = (
                    f"⚠️ *Excessive Communication Alert*\n\n"
                    f"{message.from_user.first_name} has triggered The Apex Project's flood protocols. "
                    f"Your voice has been temporarily revoked for 1 minute."
                )
            
            await message.reply_text(
                flood_message,
                parse_mode="Markdown"
            )
            
            # Issue a warning
            await issue_warning(chat_id, user_id, "message flooding", context)
            
            # Clear the user's message history after taking action
            chat_flood[user_id] = []
            
            logger.info(f"Muted user {user_id} in chat {chat_id} for flooding")
        except Exception as e:
            logger.error(f"Failed to apply flood control for user {user_id}: {e}")

async def check_banned_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle banned content in messages"""
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Don't apply to admins
    if await is_admin(chat_id, user_id, context):
        return
    
    # Check if we need to filter links
    settings = context.bot_data.setdefault("chat_settings", {})
    chat_settings = settings.setdefault(chat_id, {"banned_content": []})
    
    # Check for banned content types
    if "url" in chat_settings.get("banned_content", []) and message.entities:
        for entity in message.entities:
            if entity.type == "url" or entity.type == "text_link":
                try:
                    await message.delete()
                    
                    # Generate AI-powered roast for posting links
                    from utils.ai_helper import generate_banned_content_response
                    roast = await generate_banned_content_response(message.from_user.first_name, "links")
                    
                    # Fall back to default message if AI fails
                    if not roast:
                        roast = f"⚠️ Links are not allowed in this chat, {message.from_user.first_name}."
                    
                    await message.reply_text(
                        roast,
                        parse_mode="Markdown"
                    )
                    await issue_warning(chat_id, user_id, "posting links", context)
                    logger.info(f"Deleted link from user {user_id} in chat {chat_id}")
                    return
                except Exception as e:
                    logger.error(f"Failed to delete link message: {e}")
    
    # Banned phrases check has been disabled as requested
    # Users can now say whatever they want
    pass

async def issue_warning(chat_id, user_id, reason, context):
    """Issue a warning to a user"""
    warnings = context.bot_data.setdefault("user_warnings", {})
    chat_warnings = warnings.setdefault(chat_id, {})
    user_warnings = chat_warnings.setdefault(user_id, {"count": 0, "timestamps": []})
    
    # Update warnings count and add timestamp
    current_time = time.time()
    user_warnings["count"] += 1
    user_warnings["timestamps"].append(current_time)
    
    # Remove expired warnings
    expiry_time = current_time - (WARNING_EXPIRE_HOURS * 3600)
    user_warnings["timestamps"] = [t for t in user_warnings["timestamps"] if t > expiry_time]
    user_warnings["count"] = len(user_warnings["timestamps"])
    
    try:
        user = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        username = user.user.first_name
        
        if user_warnings["count"] >= MAX_WARNINGS:
            # Ban the user
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            
            # Generate AI ban message
            from utils.ai_helper import generate_banned_content_response
            ban_message = await generate_banned_content_response(username, "behavior after multiple warnings")
            
            # Fall back to default message if AI fails
            if not ban_message:
                ban_message = f"⛔️ {username} has been banned after receiving {MAX_WARNINGS} warnings."
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=ban_message,
                parse_mode="Markdown"
            )
            # Clear the user's warnings after banning
            chat_warnings[user_id] = {"count": 0, "timestamps": []}
            logger.info(f"Banned user {user_id} from chat {chat_id} after {MAX_WARNINGS} warnings")
        else:
            # Generate AI warning message
            from utils.ai_helper import generate_warning_message
            warning_message = await generate_warning_message(username, reason)
            
            # Fall back to default message if AI fails
            if not warning_message:
                warning_message = (
                    f"⚠️ {username} has been warned for {reason}.\n"
                    f"Warning: {user_warnings['count']}/{MAX_WARNINGS}"
                )
            else:
                # Add warning count to AI message if not present
                if f"{user_warnings['count']}/{MAX_WARNINGS}" not in warning_message:
                    warning_message += f"\nWarning: {user_warnings['count']}/{MAX_WARNINGS}"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=warning_message,
                parse_mode="Markdown"
            )
            logger.info(f"Issued warning to user {user_id} in chat {chat_id}, current count: {user_warnings['count']}")
    except Exception as e:
        logger.error(f"Failed to issue warning to user {user_id}: {e}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /ban command"""
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"Ban command triggered by user {user_id} in chat {chat_id}")
    
    # Check if user is admin
    if not await is_admin(chat_id, user_id, context):
        logger.info(f"User {user_id} is not an admin - ban command rejected")
        await message.reply_text("⚠️ You do not have permission to use this command.")
        return
    
    # Check if we're replying to a message and if there's a reason
    if not message.reply_to_message:
        await message.reply_text("⚠️ You must reply to a message to ban a user.")
        return
    
    target_user = message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    try:
        # Check if target user is also an admin
        if await is_admin(chat_id, target_user.id, context):
            await message.reply_text("⚠️ Cannot ban administrators.")
            return
        
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user.id)
        
        # Generate AI-powered ban message
        from utils.ai_helper import generate_banned_content_response
        ban_message = await generate_banned_content_response(target_user.first_name, f"being banned for {reason}")
        
        # Fall back to default message if AI fails
        if not ban_message:
            ban_message = (
                f"⛔️ {target_user.first_name} has been banned from The Apex Project.\n"
                f"Reason: {reason}"
            )
        
        await message.reply_text(
            ban_message,
            parse_mode="Markdown"
        )
        logger.info(f"Admin {user_id} banned user {target_user.id} from chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to ban user {target_user.id}: {e}")
        await message.reply_text("⚠️ Failed to ban user. Please check my permissions.")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /mute command"""
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    logger.info(f"Mute command triggered by user {user_id} in chat {chat_id}")
    
    # Check if user is admin
    if not await is_admin(chat_id, user_id, context):
        logger.info(f"User {user_id} is not an admin - mute command rejected")
        await message.reply_text("⚠️ You do not have permission to use this command.")
        return
    
    # Check if we're replying to a message
    if not message.reply_to_message:
        await message.reply_text("⚠️ You must reply to a message to mute a user.")
        return
    
    target_user = message.reply_to_message.from_user
    
    # Parse duration (default to 1 hour)
    duration = 3600  # 1 hour in seconds
    if context.args:
        time_arg = context.args[0].lower()
        try:
            match = re.match(r'^(\d+)', time_arg)
            if match:
                time_value = int(match.group(1))
                if "m" in time_arg:
                    duration = time_value * 60
                elif "h" in time_arg:
                    duration = time_value * 3600
                elif "d" in time_arg:
                    duration = time_value * 86400
                else:
                    duration = time_value * 60  # Default to minutes
        except (AttributeError, ValueError):
            duration = 3600  # Default to 1 hour if parsing fails
    
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    
    try:
        # Check if target user is also an admin
        if await is_admin(chat_id, target_user.id, context):
            await message.reply_text("⚠️ Cannot mute administrators.")
            return
        
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False
        )
        
        until_date = int(time.time() + duration)
        
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=permissions,
            until_date=until_date
        )
        
        # Format duration for display
        duration_text = ""
        if duration >= 86400:
            days = duration // 86400
            duration_text = f"{days} day{'s' if days > 1 else ''}"
        elif duration >= 3600:
            hours = duration // 3600
            duration_text = f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            minutes = max(1, duration // 60)
            duration_text = f"{minutes} minute{'s' if minutes > 1 else ''}"
        
        # Generate AI-powered mute message
        from utils.ai_helper import generate_banned_content_response
        mute_message = await generate_banned_content_response(
            target_user.first_name, 
            f"being muted for {duration_text} for {reason}"
        )
        
        # Fall back to default message if AI fails
        if not mute_message:
            mute_message = (
                f"🔇 {target_user.first_name} has been muted for {duration_text}.\n"
                f"Reason: {reason}"
            )
        
        await message.reply_text(
            mute_message,
            parse_mode="Markdown"
        )
        logger.info(f"Admin {user_id} muted user {target_user.id} in chat {chat_id} for {duration} seconds")
    except Exception as e:
        logger.error(f"Failed to mute user {target_user.id}: {e}")
        await message.reply_text("⚠️ Failed to mute user. Please check my permissions.")

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /warn command"""
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is admin
    if not await is_admin(chat_id, user_id, context):
        await message.reply_text("⚠️ You do not have permission to use this command.")
        return
    
    # Check if we're replying to a message
    if not message.reply_to_message:
        await message.reply_text("⚠️ You must reply to a message to warn a user.")
        return
    
    target_user = message.reply_to_message.from_user
    
    # Check if target user is also an admin
    if await is_admin(chat_id, target_user.id, context):
        await message.reply_text("⚠️ Cannot warn administrators.")
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    try:
        await issue_warning(chat_id, target_user.id, reason, context)
        logger.info(f"Admin {user_id} warned user {target_user.id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to warn user {target_user.id}: {e}")
        await message.reply_text("⚠️ Failed to issue warning.")

async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /pin command"""
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is admin
    if not await is_admin(chat_id, user_id, context):
        await message.reply_text("⚠️ You do not have permission to use this command.")
        return
    
    # Check if we're replying to a message
    if not message.reply_to_message:
        await message.reply_text("⚠️ You must reply to a message to pin it.")
        return
    
    # Check if we should notify members (default is no)
    disable_notification = True
    if context.args and context.args[0].lower() in ["notify", "loud"]:
        disable_notification = False
    
    try:
        await context.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message.reply_to_message.message_id,
            disable_notification=disable_notification
        )
        
        # Send a themed message about the pin
        pin_message = (
            f"📌 *Attention all Apex Project operatives*\n\n"
            f"A communication of strategic importance has been permanently archived by {message.from_user.first_name}.\n"
            f"_The shadows have eyes, and now they are watching this message._"
        )
        
        await message.reply_text(
            pin_message,
            parse_mode="Markdown"
        )
        
        logger.info(f"Admin {user_id} pinned message {message.reply_to_message.message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to pin message: {e}")
        await message.reply_text("⚠️ Failed to pin message. Please check my permissions.")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /settings command to configure group settings"""
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is admin
    if not await is_admin(chat_id, user_id, context):
        await message.reply_text("⚠️ You do not have permission to use this command.")
        return
    
    # Get current settings
    settings = context.bot_data.setdefault("chat_settings", {})
    chat_settings = settings.setdefault(chat_id, {"banned_content": []})
    
    # Create inline keyboard for settings
    keyboard = [
        [
            InlineKeyboardButton(
                "🔗 Links: " + ("❌ Blocked" if "url" in chat_settings.get("banned_content", []) else "✅ Allowed"),
                callback_data=f"toggle_setting_url_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⏱ Slow Mode: " + ("✅ On" if chat_settings.get("slow_mode", False) else "❌ Off"),
                callback_data=f"toggle_setting_slow_mode_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Welcome Messages: " + ("✅ On" if chat_settings.get("welcome_msg", True) else "❌ Off"),
                callback_data=f"toggle_setting_welcome_msg_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton("Close", callback_data="close_settings")
        ]
    ]
    
    await message.reply_text(
        "⚙️ *Apex Project Group Settings*\n\n"
        "Configure protection protocols below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def toggle_setting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callbacks for toggling settings"""
    query = update.callback_query
    
    if not query:
        logger.error("Callback received with no query object")
        return
        
    await query.answer()
    
    # Parse the callback data
    if not query.data:
        logger.error("Callback query missing data")
        return
        
    data_parts = query.data.split('_')
    if len(data_parts) < 4 or data_parts[0] != "toggle" or data_parts[1] != "setting":
        logger.error(f"Invalid callback data format: {query.data}")
        return
    
    setting_name = data_parts[2]
    
    try:
        chat_id = int(data_parts[3])
    except ValueError:
        logger.error(f"Invalid chat_id in callback data: {data_parts[3]}")
        return
    
    # Check if user is admin
    user_id = query.from_user.id
    if not await is_admin(chat_id, user_id, context):
        await query.edit_message_text("⚠️ You do not have permission to change settings.")
        return
    
    # Update the setting
    settings = context.bot_data.setdefault("chat_settings", {})
    chat_settings = settings.setdefault(chat_id, {"banned_content": []})
    
    if setting_name == "url":
        if "url" in chat_settings.get("banned_content", []):
            chat_settings["banned_content"].remove("url")
            setting_status = "✅ Allowed"
        else:
            chat_settings.setdefault("banned_content", []).append("url")
            setting_status = "❌ Blocked"
        
        logger.info(f"Admin {user_id} changed link setting to {setting_status} in chat {chat_id}")
    
    elif setting_name == "slow_mode":
        current_status = chat_settings.get("slow_mode", False)
        new_status = not current_status
        chat_settings["slow_mode"] = new_status
        
        # Apply slow mode to the chat
        try:
            if new_status:
                await context.bot.set_chat_slow_mode_delay(chat_id=chat_id, seconds=SLOW_MODE_INTERVAL)
                setting_status = "✅ On"
            else:
                await context.bot.set_chat_slow_mode_delay(chat_id=chat_id, seconds=0)
                setting_status = "❌ Off"
            
            logger.info(f"Admin {user_id} changed slow mode to {setting_status} in chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to set slow mode: {e}")
            await query.edit_message_text("⚠️ Failed to set slow mode. Please check my permissions.")
            return
    
    elif setting_name == "welcome_msg":
        current_status = chat_settings.get("welcome_msg", True)
        new_status = not current_status
        chat_settings["welcome_msg"] = new_status
        setting_status = "✅ On" if new_status else "❌ Off"
        
        logger.info(f"Admin {user_id} changed welcome messages to {setting_status} in chat {chat_id}")
    
    # Recreate the keyboard with updated settings
    keyboard = [
        [
            InlineKeyboardButton(
                "🔗 Links: " + ("❌ Blocked" if "url" in chat_settings.get("banned_content", []) else "✅ Allowed"),
                callback_data=f"toggle_setting_url_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⏱ Slow Mode: " + ("✅ On" if chat_settings.get("slow_mode", False) else "❌ Off"),
                callback_data=f"toggle_setting_slow_mode_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Welcome Messages: " + ("✅ On" if chat_settings.get("welcome_msg", True) else "❌ Off"),
                callback_data=f"toggle_setting_welcome_msg_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton("Close", callback_data="close_settings")
        ]
    ]
    
    try:
        await query.edit_message_text(
            "⚙️ *Apex Project Group Settings*\n\n"
            "Configure protection protocols below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to update settings message: {e}")

async def close_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the close settings button callback"""
    query = update.callback_query
    
    if not query:
        logger.error("Callback received with no query object")
        return
        
    await query.answer()
    
    try:
        await query.edit_message_text(
            "⚙️ *Protocol Configuration Complete*\n\n"
            "The Apex Project security parameters have been updated according to your specifications.\n\n"
            "_Our sentinels are vigilant. Our protocols are active._\n\n"
            "⚠️ *This control panel will self-destruct momentarily.* ⚠️",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to update close settings message: {e}")

async def delete_welcome_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a welcome message after the specified time"""
    try:
        # Extract data safely
        job_data = {}
        if hasattr(context, 'job') and context.job:
            if hasattr(context.job, 'data'):
                job_data = context.job.data
        
        if not job_data:
            logger.error("Job context missing required data for welcome message deletion")
            return
            
        if not isinstance(job_data, dict) or "chat_id" not in job_data or "message_id" not in job_data:
            logger.error(f"Job data missing required fields for welcome message deletion: {job_data}")
            return
            
        chat_id = job_data["chat_id"]
        message_id = job_data["message_id"]
        
        # Delete the welcome message
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted welcome message {message_id} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete welcome message: {e}")

async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new members joining the chat"""
    message = update.message
    chat_id = message.chat.id
    
    # Check if welcome messages are enabled
    settings = context.bot_data.setdefault("chat_settings", {})
    chat_settings = settings.setdefault(chat_id, {})
    
    if not chat_settings.get("welcome_msg", True):
        return
    
    for new_member in message.new_chat_members:
        # Skip if the new member is a bot
        if new_member.is_bot:
            continue
        
        try:
            # Generate AI welcome message
            from utils.ai_helper import generate_welcome_message
            welcome_text = await generate_welcome_message(new_member.first_name)
            
            # Fall back to default message if AI fails
            if not welcome_text:
                welcome_text = WELCOME_MESSAGE.format(user_name=new_member.first_name)
            
            # Send welcome message and get the message object
            welcome_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                parse_mode="Markdown"
            )
            logger.info(f"Sent welcome message to user {new_member.id} in chat {chat_id}")
            
            # Schedule deletion after 60 seconds (1 minute)
            try:
                job_name = f"delete_welcome_{welcome_msg.message_id}"
                if hasattr(context, 'job_queue') and context.job_queue:
                    context.job_queue.run_once(
                        delete_welcome_message,
                        60,  # 60 seconds = 1 minute
                        data={"chat_id": chat_id, "message_id": welcome_msg.message_id},
                        name=job_name
                    )
                    logger.info(f"Scheduled welcome message deletion for message {welcome_msg.message_id} in 60 seconds")
                else:
                    logger.error(f"No job queue available for scheduling welcome message deletion")
            except Exception as job_error:
                logger.error(f"Failed to schedule welcome message deletion: {job_error}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

def register_group_management_handlers(dp, user_warnings, flood_control, chat_settings):
    """Register all handlers related to group management"""
    # Command handlers - explicitly for group chats
    dp.add_handler(CommandHandler("ban", ban_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("mute", mute_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("warn", warn_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("pin", pin_command, filters=filters.ChatType.GROUPS))
    dp.add_handler(CommandHandler("settings", settings_command, filters=filters.ChatType.GROUPS))
    
    # Callback handlers
    dp.add_handler(CallbackQueryHandler(toggle_setting_callback, pattern=r"^toggle_setting_"))
    dp.add_handler(CallbackQueryHandler(close_settings_callback, pattern=r"^close_settings$"))
    
    # Message handlers - simplified approach for both development and production
    # This avoids filter operator issues in mock implementation
    dp.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, check_flood_control))
    dp.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, check_banned_content))
    dp.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members))
    
    logger.info("Group management handlers registered")
