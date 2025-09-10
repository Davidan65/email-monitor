"""
Configuration Template for Email Monitor
Copy this file to config.py and fill in your actual credentials.
"""

# Gmail IMAP Settings
IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = "your-email@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "your-app-password"  # Replace with your Gmail App Password

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"  # Replace with your bot token
TELEGRAM_CHAT_ID = "123456789"  # Replace with your chat ID

# Email Monitoring Settings
MONITORED_SENDERS = [
    "noreply@mysite.com",      # Replace with actual email addresses
    "notifications@example.com", # Add more as needed
]

# Optional: Advanced Settings
CHECK_INTERVAL_MINUTES = 3  # How often to check for new emails

"""
IMPORTANT: 
1. Copy this file to config.py
2. Replace all placeholder values with your actual credentials
3. Never commit config.py with real credentials to version control
4. Add config.py to your .gitignore file
"""
