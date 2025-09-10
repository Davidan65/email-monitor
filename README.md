# Email to Telegram Monitor

A Python script that monitors your Gmail inbox for emails from specific senders and automatically forwards them to your Telegram chat.

## Features

- ✅ Connects to Gmail via IMAP
- ✅ Monitors emails from specific sender addresses
- ✅ Extracts both plain text and HTML content (converts HTML to text)
- ✅ Sends formatted notifications to Telegram
- ✅ Marks processed emails as read to avoid duplicates
- ✅ Safe for repeated execution (every 3 minutes by default)
- ✅ Comprehensive logging
- ✅ Error handling and recovery

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment file:**
   ```bash
   # Copy the template
   copy .env.template .env
   ```
   Then edit `.env` with your actual credentials (see setup instructions below)

3. **Run the script:**
   ```bash
   # Test startup notification
   python email_monitor.py --test-notification
   
   # Run once
   python email_monitor.py --once
   
   # Run continuously (checks every 15 seconds by default)
   python email_monitor.py
   ```

### Cloud Deployment (Render)

For 24/7 monitoring on Render's free plan, see **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)** for complete deployment guide.

## Setup Instructions

### 1. Gmail App Password Setup

**Important:** You need to use a Gmail App Password, NOT your regular Gmail password.

1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification**
3. If not already enabled, enable 2-Factor Authentication
4. Scroll down to **App passwords**
5. Click **Select app** → **Mail**
6. Click **Select device** → **Other** → Enter "Email Monitor"
7. Click **Generate**
8. Copy the 16-character app password (it will look like: `abcd efgh ijkl mnop`)
9. Use this app password in the `EMAIL_PASSWORD` field in `config.py`

### 2. Telegram Bot Setup

1. **Create a bot:**
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot`
   - Follow the instructions to choose a name and username for your bot
   - Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
   - Paste this token in the `TELEGRAM_BOT_TOKEN` field in `config.py`

2. **Get your Chat ID:**
   - Send any message to your new bot first
   - Visit this URL in your browser (replace `YOUR_BOT_TOKEN` with your actual bot token):
     ```
     https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
     ```
   - Look for `"chat":{"id":YOUR_CHAT_ID}` in the response
   - Copy the chat ID number and paste it in the `TELEGRAM_CHAT_ID` field in `config.py`

### 3. Configure Environment File

Edit the `.env` file and update:

```bash
# Your Gmail credentials
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password

# Your Telegram settings
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Email addresses to monitor (comma-separated)
MONITORED_SENDERS=noreply@mysite.com,notifications@example.com

# Check interval (0.25 = 15 seconds)
CHECK_INTERVAL_MINUTES=0.25
```

## Usage

### Run Once (for testing)
```bash
python email_monitor.py --once
```

### Test Notifications
```bash
python email_monitor.py --test-notification
```

### Run Continuously
```bash
python email_monitor.py
```

The script will:
- Check for unread emails every 15 seconds (configurable)
- Process emails from monitored senders
- Send formatted notifications to Telegram
- Mark processed emails as read
- Log all activities to `email_monitor.log`

### Stop the Script
Press `Ctrl+C` to stop the continuous monitoring.

## Example Telegram Notification

```
📧 New Email Alert

From: noreply@mysite.com
Subject: New Order Received - #12345

Content:
Hello,

You have received a new order:
Order ID: #12345
Customer: John Doe
Total: $99.99

Please process this order as soon as possible.

Best regards,
Your Website
```

## Logging

The script creates detailed logs in `email_monitor.log` including:
- Connection status
- Emails processed
- Telegram messages sent
- Any errors encountered

## Troubleshooting

### Common Issues

1. **"Authentication failed" error:**
   - Make sure you're using a Gmail App Password, not your regular password
   - Verify 2-Factor Authentication is enabled on your Google account

2. **"Telegram message failed" error:**
   - Check your bot token is correct
   - Verify your chat ID is correct
   - Make sure you've sent at least one message to your bot first

3. **No emails being detected:**
   - Check that the sender email addresses in `MONITORED_SENDERS` are correct
   - Verify there are actually unread emails from those senders
   - Check the log file for any error messages

4. **Script stops unexpectedly:**
   - Check the log file for error details
   - Ensure your internet connection is stable
   - The script will automatically retry after errors

### Testing

To test your setup:
1. Run `python email_monitor.py --once`
2. Send yourself a test email from one of the monitored addresses
3. Check if you receive a Telegram notification

## Security Notes

- **NEVER commit your `.env` file to version control** - it contains sensitive credentials
- The `.env` file is automatically ignored by git (listed in `.gitignore`)
- Use Gmail App Passwords instead of your main password
- Keep your Telegram bot token secure
- The script only reads emails and marks them as read - it doesn't delete or modify email content

## Customization

You can modify the script to:
- Change the check interval (modify `CHECK_INTERVAL_MINUTES` in `.env` file)
- Customize the Telegram message format (edit the `telegram_message` in `check_emails()`)
- Add more filtering criteria (modify the sender matching logic)
- Process different email folders (change `'inbox'` in the `mail.select()` call)
