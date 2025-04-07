import logging
import time
from config import BOT_TOKEN

# Check if we're in development mode
dev_mode = BOT_TOKEN == "dummy_token_for_development"

try:
    from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.ext import (
        ContextTypes,
        ChatJoinRequestHandler,
        CallbackQueryHandler,
    )
except ImportError:
    # In development mode, import from our mock module
    from mock_telegram import (
        Update, InlineKeyboardMarkup, InlineKeyboardButton,
        ContextTypes, ChatJoinRequestHandler, CallbackQueryHandler
    )
from config import REQUIRED_CHANNEL, JOIN_REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming chat join requests"""
    request = update.chat_join_request
    user = request.from_user
    chat = request.chat
    
    logger.info(f"Received join request from {user.id} ({user.username or user.first_name}) for chat {chat.id}")
    
    # Store the join request details with timestamp
    if "pending_join_requests" not in context.bot_data:
        context.bot_data["pending_join_requests"] = {}
        
    context.bot_data["pending_join_requests"][user.id] = {
        "chat_id": chat.id,
        "request_id": request.id,
        "timestamp": time.time()
    }
    
    # Create inline keyboard for user to join the required channel
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Execute Protocol 7-A", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
        [InlineKeyboardButton(text="Protocol 7-A Complete", callback_data=f"check_joined_{user.id}")]
    ])
    
    # Send message to the user
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "🔒 *ACCESS REQUEST RECEIVED* 🔒\n\n"
                f"Greetings, {user.first_name}. The Apex Project has logged your infiltration attempt.\n\n"
                "⚠️ *VERIFICATION PROTOCOLS ACTIVATED:* ⚠️\n"
                f"📡 *PROTOCOL 7-A*: Subscribe to {REQUIRED_CHANNEL}\n"
                f"⏳ *PROTOCOL 7-B*: Endure a {int(JOIN_REQUEST_TIMEOUT/60)}-minute verification period\n\n"
                "_Both protocols must be satisfied for clearance. Those who fail will be forgotten._\n\n"
                "The shadows are watching. Follow the instructions precisely."
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Schedule job to check after timeout period with error handling
        try:
            job_name = f"join_request_{user.id}"
            if hasattr(context, 'job_queue') and context.job_queue:
                context.job_queue.run_once(
                    check_join_request_timeout,
                    JOIN_REQUEST_TIMEOUT,
                    data={"user_id": user.id, "chat_id": chat.id},
                    name=job_name
                )
                logger.info(f"Scheduled timed join request check for user {user.id} in {JOIN_REQUEST_TIMEOUT} seconds")
            else:
                logger.error(f"No job queue available for scheduling join request for user {user.id}")
        except Exception as job_error:
            logger.error(f"Failed to schedule job for join request: {job_error}")
            # The join request will still work through the button callback, just without the automatic timeout check
        
    except Exception as e:
        logger.error(f"Failed to send message to user {user.id}: {e}")
        # If we can't message the user, we should not leave their request pending
        try:
            await request.decline()
        except Exception as decline_error:
            logger.error(f"Failed to decline request for user {user.id}: {decline_error}")

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback when user claims they've joined the channel"""
    query = update.callback_query
    
    if not query:
        logger.error("Callback received with no query object")
        return
        
    await query.answer()
    
    if not query.data:
        logger.error("Callback query missing data")
        return
        
    data_parts = query.data.split('_')
    if len(data_parts) < 3 or data_parts[0] != "check" or data_parts[1] != "joined":
        logger.error(f"Invalid callback data format: {query.data}")
        return
    
    try:
        user_id = int(data_parts[2])
    except ValueError:
        logger.error(f"Invalid user_id in callback data: {data_parts[2]}")
        return
    
    # Only allow the actual user to check their join status
    if query.from_user.id != user_id:
        await query.message.reply_text(
            "⚠️ *SECURITY BREACH DETECTED* ⚠️\n\n"
            "Unauthorized access attempt logged and reported.\n\n"
            "_The Apex Project does not tolerate interference with another's verification process._",
            parse_mode="Markdown"
        )
        return
    
    pending_requests = context.bot_data.get("pending_join_requests", {})
    if user_id not in pending_requests:
        await query.edit_message_text(
            "⛔ *ACCESS REQUEST NULLIFIED* ⛔\n\n"
            "Your application to The Apex Project has either expired or been purged from our systems.\n\n"
            "_The shadows wait for no one. Reapply if you seek enlightenment._",
            parse_mode="Markdown"
        )
        return
    
    # Check if user has joined the required channel
    try:
        user_in_channel = await check_user_in_channel(context, user_id)
        
        if user_in_channel:
            # Check if enough time has passed
            request_data = pending_requests[user_id]
            elapsed_time = time.time() - request_data["timestamp"]
            
            if elapsed_time >= JOIN_REQUEST_TIMEOUT:
                # Approve the request
                chat_id = request_data["chat_id"]
                try:
                    await context.bot.approve_chat_join_request(
                        chat_id=chat_id,
                        user_id=user_id
                    )
                    
                    # Remove from pending requests
                    del pending_requests[user_id]
                    
                    await query.edit_message_text(
                        "✅ *ACCESS GRANTED*\n\n"
                        "Your verification is complete. Welcome to The Apex Project.\n\n"
                        "_Remember to adhere to all protocols._",
                        parse_mode="Markdown"
                    )
                    
                    logger.info(f"Approved join request for user {user_id} to chat {chat_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to approve request for user {user_id}: {e}")
                    await query.edit_message_text(
                        "⚠️ *CRITICAL ERROR DETECTED* ⚠️\n\n"
                        "The Apex Project access mechanism encountered a critical malfunction.\n\n"
                        "_Report this code to the Inner Circle: ERROR-AP-7842_",
                        parse_mode="Markdown"
                    )
            else:
                remaining_time = int(JOIN_REQUEST_TIMEOUT - elapsed_time)
                await query.edit_message_text(
                    "⏳ *PROTOCOL 7-B IN PROGRESS* ⏳\n\n"
                    f"Protocol 7-A verification successful. Temporal alignment required before full access.\n\n"
                    f"Remaining synchronization time: {remaining_time} seconds.\n\n"
                    "_Patience is the first virtue of The Apex Project. The worthy know how to wait in the shadows._",
                    parse_mode="Markdown"
                )
        else:
            # User hasn't joined the channel
            await query.edit_message_text(
                "❌ *VERIFICATION FAILED* ❌\n\n"
                f"Access to The Apex Project requires subscription to {REQUIRED_CHANNEL}.\n\n"
                "_Those who seek knowledge must first demonstrate loyalty. Join our official channel to continue the initiation process._",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="Execute Protocol 7-A", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
                    [InlineKeyboardButton(text="Verify Protocol 7-A", callback_data=f"check_joined_{user_id}")]
                ]),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error checking if user {user_id} joined channel: {e}")
        await query.edit_message_text(
            "⚠️ *SYSTEM MALFUNCTION DETECTED* ⚠️\n\n"
            "Our surveillance systems encountered an anomaly while verifying your status.\n\n"
            "_Shadow protocols suggest you attempt verification again momentarily._",
            parse_mode="Markdown"
        )

async def check_join_request_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if a join request has timed out and can be approved"""
    try:
        # Extract data safely
        job_data = {}
        if hasattr(context, 'job') and context.job:
            if hasattr(context.job, 'data'):
                job_data = context.job.data
            elif hasattr(context, 'job_data'):
                job_data = context.job_data
        
        if not job_data:
            logger.error("Job context missing required data")
            return
            
        if not isinstance(job_data, dict) or "user_id" not in job_data or "chat_id" not in job_data:
            logger.error(f"Job data missing required fields: {job_data}")
            return
    except Exception as e:
        logger.error(f"Error extracting job data: {e}")
        return
        
    user_id = job_data["user_id"]
    chat_id = job_data["chat_id"]
    
    logger.info(f"Checking timed join request for user {user_id}")
    
    pending_requests = context.bot_data.get("pending_join_requests", {})
    if user_id not in pending_requests:
        logger.info(f"Join request for user {user_id} no longer pending")
        return
    
    # Check if user has joined the required channel
    try:
        user_in_channel = await check_user_in_channel(context, user_id)
        
        if user_in_channel:
            # Approve the request
            try:
                await context.bot.approve_chat_join_request(
                    chat_id=chat_id,
                    user_id=user_id
                )
                
                # Notify the user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "✅ *ACCESS GRANTED*\n\n"
                        "Your verification is complete. Welcome to The Apex Project.\n\n"
                        "_Remember to adhere to all protocols._"
                    ),
                    parse_mode="Markdown"
                )
                
                # Remove from pending requests
                del pending_requests[user_id]
                
                logger.info(f"Approved timed join request for user {user_id} to chat {chat_id}")
                
            except Exception as e:
                logger.error(f"Failed to approve timed request for user {user_id}: {e}")
        else:
            # User hasn't joined the channel - keep request pending but notify them
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "⚠️ *VERIFICATION REMINDER* ⚠️\n\n"
                        f"Your access request to The Apex Project requires subscription to {REQUIRED_CHANNEL}.\n\n"
                        "_The shadows cannot embrace those who remain unaligned. Your clearance remains suspended until commitment is proven._",
                    ),
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="Execute Protocol 7-A", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
                        [InlineKeyboardButton(text="Protocol 7-A Complete", callback_data=f"check_joined_{user_id}")]
                    ])
                )
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in timed check for user {user_id}: {e}")

async def check_user_in_channel(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if a user is a member of the required channel"""
    try:
        if not REQUIRED_CHANNEL:
            logger.error("REQUIRED_CHANNEL is not set")
            return True  # If no channel is required, consider it a success
            
        # Clean the channel name if needed
        channel_id = REQUIRED_CHANNEL
        if channel_id.startswith('@'):
            channel_id = channel_id[1:]  # Remove @ if present
            
        logger.info(f"Checking if user {user_id} is a member of channel {channel_id}")
            
        # Try to get the user's membership status
        member = await context.bot.get_chat_member(chat_id=f"@{channel_id}", user_id=user_id)
        
        # Check if the membership status is active
        is_member = member.status in ['member', 'administrator', 'creator']
        logger.info(f"User {user_id} channel membership status: {member.status}, is member: {is_member}")
        return is_member
    except Exception as e:
        logger.error(f"Error checking channel membership for user {user_id}: {e}")
        return False

def register_join_request_handlers(dp, pending_join_requests):
    """Register all handlers related to join requests"""
    dp.add_handler(ChatJoinRequestHandler(handle_join_request))
    dp.add_handler(CallbackQueryHandler(check_joined_callback, pattern=r"^check_joined_"))
    
    logger.info("Join request handlers registered")
