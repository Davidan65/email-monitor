"""
Configuration file for Email Monitor
Credentials are loaded from .env file for security.
"""

import os
from dotenv import load_dotenv
import sys

# Load environment variables from .env file (for local development)
# On Render, environment variables are provided directly by the platform
if os.path.exists('.env'):
    load_dotenv()
    print("Loaded configuration from .env file")
else:
    print("No .env file found - using system environment variables (normal for cloud deployment)")

# Gmail IMAP Settings - Multiple Accounts Support
IMAP_SERVER = "imap.gmail.com"

# Multiple Gmail accounts (format: email:password,email:password)
GMAIL_ACCOUNTS = os.getenv("GMAIL_ACCOUNTS", "")

# Backward compatibility - single account support
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Parse multiple accounts or fall back to single account
if GMAIL_ACCOUNTS:
    # Parse multiple accounts format: email1:password1,email2:password2
    account_pairs = [pair.strip() for pair in GMAIL_ACCOUNTS.split(',') if pair.strip()]
    ACCOUNTS = {}
    for pair in account_pairs:
        if ':' in pair:
            email, password = pair.split(':', 1)
            ACCOUNTS[email.strip()] = password.strip()
else:
    # Single account mode (backward compatibility)
    ACCOUNTS = {EMAIL_USER: EMAIL_PASSWORD} if EMAIL_USER and EMAIL_PASSWORD else {}

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Email Monitoring Settings
MONITORED_SENDERS = [
    sender.strip() for sender in os.getenv("MONITORED_SENDERS", "").split(",")
    if sender.strip()
]

# Optional: Advanced Settings
CHECK_INTERVAL_MINUTES = float(os.getenv("CHECK_INTERVAL_MINUTES", "0.25"))  # 15 seconds by default

# Validate required environment variables
required_vars = {
    'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    'MONITORED_SENDERS': os.getenv("MONITORED_SENDERS")
}

# Check for accounts
if not ACCOUNTS:
    required_vars['EMAIL_USER'] = EMAIL_USER
    required_vars['EMAIL_PASSWORD'] = EMAIL_PASSWORD
    print("ERROR: No Gmail accounts configured.")
    print("Please set either:")
    print("  - GMAIL_ACCOUNTS=email1:password1,email2:password2")
    print("  - EMAIL_USER=email and EMAIL_PASSWORD=password (single account)")
    sys.exit(1)

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("")
    if os.path.exists('.env'):
        print("Local development: Please check your .env file and ensure all variables are set.")
    else:
        print("Cloud deployment: Please set environment variables in your hosting platform.")
        print("Required variables: EMAIL_USER, EMAIL_PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MONITORED_SENDERS")
    print("")
    print("See README.md for detailed setup instructions.")
    sys.exit(1)

if not MONITORED_SENDERS:
    print("ERROR: MONITORED_SENDERS is empty or not properly formatted.")
    print("Please provide a comma-separated list of email addresses to monitor.")
    print("Example: sender1@example.com,sender2@example.com")
    sys.exit(1)

"""
SETUP INSTRUCTIONS:

1. Environment File Setup:
   - Copy .env.template to .env
   - Fill in your actual credentials in the .env file
   - The .env file is automatically ignored by git for security

2. Gmail App Password:
   - Go to your Google Account settings
   - Enable 2-Factor Authentication if not already enabled
   - Go to Security > 2-Step Verification > App passwords
   - Generate an app password for "Mail"
   - Use this app password (NOT your regular Gmail password) in EMAIL_PASSWORD

3. Telegram Bot:
   - Message @BotFather on Telegram
   - Send /newbot and follow instructions to create a new bot
   - Copy the bot token and paste it in TELEGRAM_BOT_TOKEN in .env
   
4. Telegram Chat ID:
   - Message your bot first (send any message)
   - Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   - Look for "chat":{"id": YOUR_CHAT_ID} in the response
   - Copy the chat ID and paste it in TELEGRAM_CHAT_ID in .env

5. Monitored Senders:
   - Add the email addresses you want to monitor in MONITORED_SENDERS in .env
   - Use comma-separated format: sender1@example.com,sender2@example.com
   - The script will check if any of these addresses are contained in the sender's email

6. Advanced Settings:
   - CHECK_INTERVAL_MINUTES: How often to check for emails (0.25 = 15 seconds)
   - Keep above 0.25 (15 seconds) to avoid Gmail rate limiting
"""
