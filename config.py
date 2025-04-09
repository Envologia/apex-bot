import os

# Bot Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "dummy_token_for_development")
if not BOT_TOKEN or BOT_TOKEN == "dummy_token_for_development":
    print("Warning: Using dummy token for development. The bot will not connect to Telegram API.")
    # We don't raise an error here to allow the web app to run in development mode

# Gemini API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "dummy_key_for_development")
if not GEMINI_API_KEY or GEMINI_API_KEY == "dummy_key_for_development":
    print("Warning: Using dummy Gemini API key. AI responses will not work.")

# Telegram Channel that users must join
REQUIRED_CHANNEL = os.environ.get("REQUIRED_CHANNEL", "@your_channel")
REQUIRED_CHANNEL_ID = os.environ.get("REQUIRED_CHANNEL_ID")  # Numeric ID for the channel

# Join request timeout in seconds (5 minutes)
JOIN_REQUEST_TIMEOUT = 300

# Webhook settings
WEBHOOK_URL_PATH = "/webhook/apex-project"

# AI Assistant Configuration
AI_MODEL = "gemini-1.5-flash"
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 800
AI_SYSTEM_PROMPT = """
You are the AI for the Apex Project, a secret organization that works in shadows.
Your name is Apex, not Gemini or any other AI.
You were made by Apex for members only.

When talking:
- Use simple words but keep a wisdom, and all knowing and smart,and be engaging and funny as hell
- Keep everything easy to understand

Remember: simple, and mysterious,wisdom,knowledge,fast.
"""

# Moderation settings
MAX_FLOOD_MESSAGES = 5  # Max messages allowed in short time period
FLOOD_TIME_WINDOW = 5   # Time window in seconds to check for flood
SLOW_MODE_INTERVAL = 3  # Default slow mode interval in seconds
WARNING_EXPIRE_HOURS = 24  # Warnings expire after 24 hours
MAX_WARNINGS = 3        # Number of warnings before a user is banned

# Banned content and filters
BANNED_CONTENT_TYPES = ['url']  # Content types that can be filtered
BANNED_PHRASES = [
    # All banned phrases have been removed as requested
    # Users can now say whatever they want
]

# Welcome message template
WELCOME_MESSAGE = """
*Welcome to The Apex Project, {user_name}*

You are now part of our secret group.
The shadows see you and welcome you.

Use /help to learn what you can do.

⚠️ *This message will vanish* ⚠️
"""

# Help message
HELP_MESSAGE = """
*🔒 APEX PROJECT: SECRET COMMANDS 🔒*

*Basic Commands:*
• Tag @{bot_username} in a message to talk to our AI
• /start - Connect to our network
• /help - See this help message

*Member Commands:*
• /stats - See your standing in our group
• /rules - Read our group rules

*Admin Commands:* (not working)
• /ban - Remove a user forever
• /mute - Stop a user from talking for a while 
• /warn - Give a user a warning
• /pin - Make a message stay at the top
• /settings - Change group settings

_"We work in shadows. We know secrets. We are Apex."_

⚠️ *For your eyes only* ⚠️
"""
