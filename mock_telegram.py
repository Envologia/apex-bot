import logging

logger = logging.getLogger(__name__)
logger.info("Loading mock Telegram classes for development mode")

# Mock Telegram classes for development
class Update:
    def __init__(self):
        self.chat = Chat(id=123456789, type="private", title="Test Chat")
        self.from_user = User(id=987654321, first_name="Test", username="test_user")
        self.message = Message(message_id=1, text="Test message", chat=self.chat, from_user=self.from_user)
        self.effective_message = self.message
        self.effective_chat = self.chat
        self.effective_user = self.from_user
        self.callback_query = None
        self.chat_join_request = ChatJoinRequest(
            chat=Chat(id=123456789, type="supergroup", title="Test Group"),
            from_user=User(id=987654321, first_name="Test", username="test_user"),
            id="test_request_id"
        )

class Chat:
    def __init__(self, id=None, type=None, title=None):
        self.id = id
        self.type = type
        self.title = title

class User:
    def __init__(self, id=None, first_name=None, last_name=None, username=None, is_bot=False):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot

class Message:
    def __init__(self, message_id=None, text=None, chat=None, from_user=None):
        self.message_id = message_id
        self.text = text
        self.chat = chat or Chat()
        self.from_user = from_user or User()
        self.reply_to_message = None
        self.message_thread_id = None
        self.entities = []
        self.new_chat_members = []
        
    async def reply_text(self, text, parse_mode=None, reply_markup=None, reply_to_message_id=None):
        logger.info(f"[MOCK] Replying to message with text: {text[:50]}...")
        return Message(message_id=1, text=text, chat=self.chat)
        
    async def delete(self):
        logger.info(f"[MOCK] Deleting message {self.message_id}")
        return True

class Context:
    def __init__(self):
        self.bot = Bot(token="dummy_token_for_development")
        self.bot_data = {}
        self.user_data = {}
        self.chat_data = {}
        self.job_queue = JobQueue()
        self.args = []
        
    class job:
        def __init__(self, data=None):
            self.data = data or {}
        
class JobQueue:
    def __init__(self):
        pass
        
    def run_once(self, callback, when, data=None, name=None):
        logger.info(f"[MOCK] Scheduling one-time job named {name} to run after {when} seconds")
        return None

class ContextTypes:
    DEFAULT_TYPE = Context
    
class Application:
    def __init__(self):
        self.handlers = []
        
    def add_handler(self, handler):
        self.handlers.append(handler)
        logger.info(f"[MOCK] Added handler: {handler.__class__.__name__}")
        
    class Builder:
        def __init__(self):
            pass
            
        def bot(self, bot):
            return self
            
        def build(self):
            return Application()
            
    @classmethod
    def builder(cls):
        return cls.Builder()

class Bot:
    def __init__(self, token):
        self.token = token
        self.username = "ApexProjectBot"
        
    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None, reply_to_message_id=None, message_thread_id=None):
        logger.info(f"[MOCK] Sending message to {chat_id}: {text[:50]}...")
        return Message(message_id=1, text=text, chat=Chat(id=chat_id))
        
    async def delete_message(self, chat_id, message_id):
        logger.info(f"[MOCK] Deleting message {message_id} from chat {chat_id}")
        return True
    
    async def restrict_chat_member(self, chat_id, user_id, permissions, until_date=None):
        logger.info(f"[MOCK] Restricting user {user_id} in chat {chat_id}")
        return True
    
    async def pin_chat_message(self, chat_id, message_id, disable_notification=False):
        logger.info(f"[MOCK] Pinning message {message_id} in chat {chat_id}")
        return True
        
    async def approve_chat_join_request(self, chat_id, user_id):
        logger.info(f"[MOCK] Approving join request for user {user_id} in chat {chat_id}")
        return True
        
    async def decline_chat_join_request(self, chat_id, user_id):
        logger.info(f"[MOCK] Declining join request for user {user_id} in chat {chat_id}")
        return True
        
    async def get_chat_member(self, chat_id, user_id):
        logger.info(f"[MOCK] Getting chat member info for user {user_id} in chat {chat_id}")
        member = ChatMember(user=User(id=user_id), status="member")
        return member
        
    async def send_chat_action(self, chat_id, action):
        logger.info(f"[MOCK] Sending chat action {action} to chat {chat_id}")
        return True
        
    async def ban_chat_member(self, chat_id, user_id):
        logger.info(f"[MOCK] Banning user {user_id} from chat {chat_id}")
        return True
        
    async def set_chat_slow_mode_delay(self, chat_id, seconds):
        logger.info(f"[MOCK] Setting slow mode delay of {seconds} seconds for chat {chat_id}")
        return True

class InlineKeyboardButton:
    def __init__(self, text, url=None, callback_data=None):
        self.text = text
        self.url = url
        self.callback_data = callback_data

class InlineKeyboardMarkup:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard

class CallbackQuery:
    def __init__(self, id=None, from_user=None, message=None, data=None):
        self.id = id
        self.from_user = from_user or User()
        self.message = message or Message()
        self.data = data
        
    async def answer(self, text=None, show_alert=False):
        logger.info(f"[MOCK] Answering callback query: {text}")
        return True
        
    async def edit_message_text(self, text, parse_mode=None, reply_markup=None):
        logger.info(f"[MOCK] Editing message text: {text[:50]}...")
        return True

class ChatMember:
    def __init__(self, user=None, status=None):
        self.user = user or User()
        self.status = status

class ChatPermissions:
    def __init__(self, can_send_messages=None, can_send_media_messages=None, 
                can_send_polls=None, can_send_other_messages=None, 
                can_add_web_page_previews=None, can_change_info=None, 
                can_invite_users=None, can_pin_messages=None):
        self.can_send_messages = can_send_messages
        self.can_send_media_messages = can_send_media_messages
        self.can_send_polls = can_send_polls
        self.can_send_other_messages = can_send_other_messages
        self.can_add_web_page_previews = can_add_web_page_previews
        self.can_change_info = can_change_info
        self.can_invite_users = can_invite_users
        self.can_pin_messages = can_pin_messages

class ChatJoinRequest:
    def __init__(self, chat=None, from_user=None, id=None):
        self.chat = chat or Chat()
        self.from_user = from_user or User()
        self.id = id
        
    async def approve(self):
        logger.info(f"[MOCK] Approving join request for user {self.from_user.id} in chat {self.chat.id}")
        return True
        
    async def decline(self):
        logger.info(f"[MOCK] Declining join request for user {self.from_user.id} in chat {self.chat.id}")
        return True

# Mock handler classes
class CommandHandler:
    def __init__(self, command, callback, filters=None):
        self.command = command
        self.callback = callback
        self.filters = filters

class MessageHandler:
    def __init__(self, filters, callback):
        self.filters = filters
        self.callback = callback

class CallbackQueryHandler:
    def __init__(self, callback, pattern=None):
        self.callback = callback
        self.pattern = pattern

class ChatJoinRequestHandler:
    def __init__(self, callback):
        self.callback = callback

# Mock filters
class Filters:
    def __init__(self):
        self.ChatType = self.ChatTypeClass()
    
    @property
    def text(self):
        return self
        
    @property
    def TEXT(self):
        return self
    
    @property
    def command(self):
        return self
        
    @property
    def COMMAND(self):
        return self
    
    @property
    def chat_type(self):
        return self
        
    @property
    def StatusUpdate(self):
        return self
        
    @property
    def NEW_CHAT_MEMBERS(self):
        return self

    @property
    def GROUPS(self):
        return lambda msg: True
        
    @property
    def GROUP(self):
        return lambda msg: True
        
    @property
    def SUPERGROUP(self):
        return lambda msg: True
        
    @property
    def PRIVATE(self):
        return lambda msg: True
    
    def __call__(self, *args, **kwargs):
        return True
    
    def __invert__(self):
        return lambda msg: True
        
    def __and__(self, other):
        return lambda msg: True
        
    def __or__(self, other):
        return lambda msg: True
    
    @staticmethod
    def regex(pattern):
        return lambda msg: True
    
    @staticmethod
    def user(user_id):
        return lambda msg: True
    
    @staticmethod
    def chat(chat_id):
        return lambda msg: True
        
    class ChatTypeClass:
        def __init__(self):
            self.PRIVATE = lambda msg: True
            self.GROUP = lambda msg: True
            self.SUPERGROUP = lambda msg: True
            self.CHANNEL = lambda msg: True
            self.GROUPS = lambda msg: True
        
        def __or__(self, other):
            return lambda msg: True
        
        def __and__(self, other):
            return lambda msg: True

filters = Filters()