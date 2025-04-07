# The Apex Project Telegram Bot

A powerful Telegram bot with dark secret society theme and advanced group management features.

## Features

- **AI Assistant**: Built with Gemini 2.0 Flash API for natural conversational responses
- **Channel Subscription Enforcement**: Requires users to join a specific channel before being approved for the group
- **Join Request Timeout**: 5-minute waiting period for new join requests
- **Group Management Tools**: Ban, mute, warn, and pin commands for admins
- **Dark Theme**: All messages and interactions have a secret society aesthetic

## Setup

1. Set the following environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `GEMINI_API_KEY`: Your Gemini API key
   - `REQUIRED_CHANNEL`: The channel users must join (e.g., @my_channel)

2. Run the bot using one of the following methods:
   - `python direct_bot.py`: Runs the bot directly in the terminal
   - `./run_bot_workflow.sh`: Runs the bot using the workflow script

## Customization

The bot's behavior and personality can be customized in `config.py`:

- `AI_SYSTEM_PROMPT`: Change the bot's personality and behavior
- `JOIN_REQUEST_TIMEOUT`: Adjust the waiting period for join requests
- `WELCOME_MESSAGE`: Customize the welcome message for new users
- `HELP_MESSAGE`: Modify the help text displayed to users

## Commands

- `/start`: Displays welcome message
- `/help`: Shows available commands
- `/ban`: Bans a user (admin only)
- `/mute`: Mutes a user (admin only)
- `/warn`: Issues a warning to a user (admin only)
- `/pin`: Pins a message (admin only)
- `/settings`: Configure group settings (admin only)

## Development

The project is organized into the following structure:

```
├── handlers/             # Command and event handlers
│   ├── ai_assistant.py   # AI chat capabilities
│   ├── group_management.py  # Admin commands
│   └── join_request.py   # Join request processing
├── utils/                # Utility functions
│   ├── ai_helper.py      # Gemini API integration
│   └── telegram_helper.py  # Telegram-specific functions
├── config.py             # Configuration settings
└── direct_bot.py         # Main bot application
```
