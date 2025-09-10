#!/usr/bin/env python3
"""
Email Monitor Script
Monitors Gmail inbox for emails from specific senders and forwards them to Telegram.
"""

import imaplib
import email
import requests
import time
import logging
from email.header import decode_header
from datetime import datetime, timezone
import html2text
import sys
import os
import pickle

# Import keep-alive service for Render hosting
try:
    from keep_alive import start_keep_alive, stop_keep_alive
    KEEP_ALIVE_AVAILABLE = True
except ImportError:
    KEEP_ALIVE_AVAILABLE = False
    logger.warning("Keep-alive service not available")

# Try to import config, provide helpful error if missing
try:
    import config
except ImportError:
    print("ERROR: config.py file not found!")
    print("Please copy config_template.py to config.py and fill in your credentials.")
    print("See README.md for detailed setup instructions.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailMonitor:
    def __init__(self):
        # Validate configuration
        self._validate_config()

        self.imap_server = config.IMAP_SERVER
        self.email_user = config.EMAIL_USER
        self.email_password = config.EMAIL_PASSWORD
        self.telegram_bot_token = config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID
        self.monitored_senders = [sender.lower() for sender in config.MONITORED_SENDERS]
        self.telegram_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"

        # File to store processed email IDs
        self.processed_emails_file = "processed_emails.pkl"
        self.processed_emails = self._load_processed_emails()

        # Track when monitoring started
        self.start_time = datetime.now(timezone.utc)

    def _validate_config(self):
        """Validate that all required configuration is present"""
        required_fields = [
            'IMAP_SERVER', 'EMAIL_USER', 'EMAIL_PASSWORD',
            'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'MONITORED_SENDERS'
        ]

        missing_fields = []
        for field in required_fields:
            if not hasattr(config, field):
                missing_fields.append(field)
            elif not getattr(config, field):
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"Missing required configuration fields: {missing_fields}")
            print(f"ERROR: Missing configuration fields: {missing_fields}")
            print("Please check your config.py file and ensure all fields are filled in.")
            sys.exit(1)

        # Validate email format
        if '@' not in config.EMAIL_USER:
            logger.error("EMAIL_USER must be a valid email address")
            print("ERROR: EMAIL_USER must be a valid email address")
            sys.exit(1)

        # Validate monitored senders
        if not config.MONITORED_SENDERS or len(config.MONITORED_SENDERS) == 0:
            logger.error("MONITORED_SENDERS list cannot be empty")
            print("ERROR: MONITORED_SENDERS list cannot be empty")
            sys.exit(1)

    def _load_processed_emails(self):
        """Load the set of already processed email IDs"""
        try:
            if os.path.exists(self.processed_emails_file):
                with open(self.processed_emails_file, 'rb') as f:
                    return pickle.load(f)
            return set()
        except Exception as e:
            logger.warning(f"Could not load processed emails file: {e}")
            return set()

    def _save_processed_emails(self):
        """Save the set of processed email IDs"""
        try:
            with open(self.processed_emails_file, 'wb') as f:
                pickle.dump(self.processed_emails, f)
        except Exception as e:
            logger.error(f"Could not save processed emails file: {e}")

    def _get_email_date(self, msg):
        """Extract and parse email date"""
        try:
            date_str = msg.get('Date', '')
            if date_str:
                # Parse email date
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(date_str)
            return None
        except Exception as e:
            logger.warning(f"Could not parse email date: {e}")
            return None
        
    def connect_to_email(self):
        """Connect to Gmail IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_password)
            logger.info("Successfully connected to Gmail")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            return None
    
    def decode_mime_words(self, s):
        """Decode MIME encoded words in email headers"""
        if s is None:
            return ""
        decoded_parts = decode_header(s)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string
    
    def extract_text_content(self, msg):
        """Extract plain text content from email message"""
        text_content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        text_content += body
                    except Exception as e:
                        logger.warning(f"Error decoding plain text: {e}")
                
                elif content_type == "text/html" and not text_content:
                    # Only use HTML if no plain text is available
                    try:
                        html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        h = html2text.HTML2Text()
                        h.ignore_links = True
                        h.ignore_images = True
                        text_content = h.handle(html_body)
                    except Exception as e:
                        logger.warning(f"Error converting HTML to text: {e}")
        else:
            # Non-multipart message
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                try:
                    text_content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.warning(f"Error decoding message: {e}")
            elif content_type == "text/html":
                try:
                    html_body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    h.ignore_images = True
                    text_content = h.handle(html_body)
                except Exception as e:
                    logger.warning(f"Error converting HTML to text: {e}")
        
        return text_content.strip()
    
    def send_telegram_message(self, message):
        """Send message to Telegram with retry logic"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Telegram has a 4096 character limit per message
                if len(message) > 4000:
                    message = message[:4000] + "\n\n... (message truncated)"
                
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(self.telegram_url, data=payload, timeout=30)
                
                if response.status_code == 200:
                    logger.info("Message sent to Telegram successfully")
                    return True
                else:
                    logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    return False
                    
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error to Telegram API (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("All connection attempts to Telegram failed - network may be temporarily unavailable")
                    return False
                    
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout error sending Telegram message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("All attempts to send Telegram message timed out")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error sending Telegram message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return False
        
        return False
    
    def check_emails(self):
        """Check for new emails from monitored senders"""
        mail = self.connect_to_email()
        if not mail:
            return

        try:
            # Select inbox
            mail.select('inbox')

            # Search for unread emails from the last 1 day to focus on recent emails
            from datetime import timedelta
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            status, messages = mail.search(None, f'UNSEEN SINCE {since_date}')

            if status != 'OK':
                logger.error("Failed to search for emails")
                return

            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} unread emails")

            new_emails_processed = 0

            for email_id in email_ids:
                try:
                    # Skip if we've already processed this email
                    email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                    if email_id_str in self.processed_emails:
                        continue

                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parse email
                    msg = email.message_from_bytes(msg_data[0][1])

                    # Get email date and check if it's after we started monitoring
                    email_date = self._get_email_date(msg)
                    if email_date and email_date < self.start_time:
                        # This email is older than when we started monitoring, skip it
                        self.processed_emails.add(email_id_str)
                        continue

                    # Get sender
                    sender = self.decode_mime_words(msg.get('From', ''))
                    subject = self.decode_mime_words(msg.get('Subject', ''))

                    # Check if sender is in monitored list
                    sender_email = sender.split('<')[-1].split('>')[0].strip() if '<' in sender else sender.strip()
                    sender_email_lower = sender_email.lower()

                    if any(monitored in sender_email_lower for monitored in self.monitored_senders):
                        logger.info(f"Processing email from {sender_email}: {subject}")
                        
                        # Extract text content
                        text_content = self.extract_text_content(msg)
                        
                        # Prepare Telegram message (escape HTML characters)
                        import html
                        safe_sender = html.escape(sender)
                        safe_subject = html.escape(subject)
                        safe_content = html.escape(text_content[:3000])

                        telegram_message = f"<b>📧 New Email Alert</b>\n\n"
                        telegram_message += f"<b>From:</b> {safe_sender}\n"
                        telegram_message += f"<b>Subject:</b> {safe_subject}\n\n"
                        telegram_message += f"<b>Content:</b>\n{safe_content}"

                        if len(text_content) > 3000:
                            telegram_message += "\n\n... (content truncated)"
                        
                        # Send to Telegram
                        telegram_success = self.send_telegram_message(telegram_message)
                        
                        if telegram_success:
                            # Mark as read and add to processed list only if Telegram succeeded
                            mail.store(email_id, '+FLAGS', '\\Seen')
                            self.processed_emails.add(email_id_str)
                            new_emails_processed += 1
                            logger.info(f"Email processed and marked as read: {subject}")
                        else:
                            # If Telegram fails, still mark as processed to avoid infinite retries
                            # But don't mark as read in case we want to retry later
                            self.processed_emails.add(email_id_str)
                            logger.warning(f"Telegram delivery failed for email: {subject}")
                            logger.warning("Email marked as processed to prevent spam, but not marked as read")
                            
                            # Send a simplified retry notification if possible
                            simple_msg = f"⚠️ Email delivery failed\nFrom: {sender}\nSubject: {subject}\nCheck logs for details."
                            if self.send_telegram_message(simple_msg):
                                logger.info("Sent simplified failure notification")
                    else:
                        # Add to processed list even if not from monitored sender
                        self.processed_emails.add(email_id_str)

                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue

            # Save processed emails list
            self._save_processed_emails()

            if new_emails_processed > 0:
                logger.info(f"Processed {new_emails_processed} new emails from monitored senders")
            else:
                logger.info("No new emails from monitored senders found")
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
        
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
    
    def test_network_connectivity(self):
        """Test network connectivity to external services"""
        try:
            # Test connection to Telegram API
            response = requests.get('https://api.telegram.org', timeout=10)
            logger.info("✅ Network connectivity to Telegram API: OK")
            return True
        except requests.exceptions.ConnectionError:
            logger.error("❌ Network connectivity to Telegram API: FAILED")
            logger.error("This may be a temporary network issue on the hosting platform")
            return False
        except Exception as e:
            logger.error(f"Network connectivity test failed: {e}")
            return False
    def send_startup_notification(self):
        """Send startup notification to Telegram"""
        try:
            import html
            
            # Test network connectivity first
            if not self.test_network_connectivity():
                logger.warning("⚠️ Network connectivity issues detected - startup notification may fail")
            
            # Get current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare startup message
            startup_msg = "🚀 <b>Email Monitor Started!</b>\n\n"
            startup_msg += f"⏰ <b>Started at:</b> {current_time}\n"
            startup_msg += f"📧 <b>Monitoring Gmail:</b> {html.escape(self.email_user)}\n"
            startup_msg += f"🔍 <b>Check Interval:</b> {getattr(config, 'CHECK_INTERVAL_MINUTES', 3)} minutes\n\n"
            startup_msg += "<b>📋 Monitored Senders:</b>\n"
            
            for sender in config.MONITORED_SENDERS:
                safe_sender = html.escape(sender)
                startup_msg += f"• {safe_sender}\n"
            
            startup_msg += "\n✅ <b>Status:</b> Ready to monitor emails\n"
            startup_msg += "📱 You will receive notifications for new emails from the above senders."
            
            # Add keep-alive status if available
            if KEEP_ALIVE_AVAILABLE:
                startup_msg += "\n🔄 <b>Keep-Alive:</b> Active (Render hosting)"
            
            # Send startup notification
            if self.send_telegram_message(startup_msg):
                logger.info("✅ Startup notification sent to Telegram")
                return True
            else:
                logger.error("❌ Failed to send startup notification")
                return False
                
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")
            return False
        """Initialize monitoring by marking all current unread emails as processed"""
    def initialize_monitoring(self):
        """Initialize monitoring by marking all current unread emails as processed"""
        logger.info("Initializing email monitoring - marking existing emails as processed...")

        mail = self.connect_to_email()
        if not mail:
            return False

        try:
            mail.select('inbox')

            # Get all unread emails
            status, messages = mail.search(None, 'UNSEEN')
            if status == 'OK':
                email_ids = messages[0].split()
                for email_id in email_ids:
                    email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                    self.processed_emails.add(email_id_str)

                self._save_processed_emails()
                logger.info(f"Marked {len(email_ids)} existing unread emails as processed")
                logger.info("Email monitoring initialized - will now only process NEW emails")
                return True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

        return False

    def run_once(self):
        """Run email check once"""
        logger.info("Starting single email check...")
        self.check_emails()
        logger.info("Single email check completed")
    
    def run_continuous(self, interval_minutes=None):
        """Run email monitoring continuously"""
        # Use config interval if not provided
        if interval_minutes is None:
            interval_minutes = getattr(config, 'CHECK_INTERVAL_MINUTES', 3)
            
        # Start keep-alive service for Render hosting
        if KEEP_ALIVE_AVAILABLE:
            port = int(os.getenv('PORT', 10000))  # Render sets PORT environment variable
            if start_keep_alive(port):
                logger.info("🔄 Keep-alive service started for Render hosting")
            else:
                logger.warning("⚠️ Failed to start keep-alive service")
        
        # Check if this is the first run
        is_first_run = not os.path.exists(self.processed_emails_file)
        if is_first_run:
            logger.info("First time running - initializing monitoring...")
            if not self.initialize_monitoring():
                logger.error("Failed to initialize monitoring")
                return
        
        # Send startup notification ONCE when service starts
        logger.info("Testing network connectivity...")
        self.test_network_connectivity()
        
        logger.info("Sending startup notification...")
        if not self.send_startup_notification():
            logger.warning("Failed to send startup notification, but continuing...")

        logger.info(f"Starting continuous email monitoring (checking every {interval_minutes} minutes)")
        logger.info(f"Monitoring emails from: {', '.join(config.MONITORED_SENDERS)}")

        while True:
            try:
                self.run_once()
                logger.info(f"Waiting {interval_minutes} minutes before next check...")
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logger.info("Email monitoring stopped by user")
                
                # Send enhanced shutdown notification
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                shutdown_msg = "⏹️ <b>Email Monitor Stopped</b>\n\n"
                shutdown_msg += f"⏰ <b>Stopped at:</b> {current_time}\n"
                shutdown_msg += "🚫 <b>Status:</b> Email monitoring has been stopped by user\n\n"
                shutdown_msg += "📝 <b>Note:</b> No new email notifications will be sent until the service is restarted."
                
                self.send_telegram_message(shutdown_msg)
                
                # Stop keep-alive service
                if KEEP_ALIVE_AVAILABLE:
                    stop_keep_alive()
                    logger.info("🚫 Keep-alive service stopped")
                
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                
                # Send error notification
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_msg = "⚠️ <b>Email Monitor Error</b>\n\n"
                error_msg += f"⏰ <b>Time:</b> {error_time}\n"
                error_msg += f"🚫 <b>Error:</b> {str(e)[:200]}...\n\n"
                error_msg += "🔄 <b>Status:</b> Attempting to recover...\n"
                error_msg += "Service will retry in 1 minute."
                
                try:
                    self.send_telegram_message(error_msg)
                except:
                    # If we can't send error notification, just log it
                    logger.error("Failed to send error notification to Telegram")
                
                logger.info("Waiting 1 minute before retrying...")
                time.sleep(60)


def main():
    """Main function"""
    import sys

    monitor = EmailMonitor()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # Send a brief test notification for single run
            current_time = datetime.now().strftime("%H:%M:%S")
            test_msg = f"🧪 <b>Email Monitor Test Run</b>\n\n⏰ <b>Time:</b> {current_time}\n🔍 Running single email check..."
            monitor.send_telegram_message(test_msg)
            
            monitor.run_once()
        elif sys.argv[1] == '--test-notification':
            print("Testing Telegram notification...")
            if monitor.send_startup_notification():
                print("✅ Startup notification sent successfully!")
            else:
                print("❌ Failed to send startup notification.")
        elif sys.argv[1] == '--init':
            print("Initializing email monitoring...")
            if monitor.initialize_monitoring():
                print("✅ Email monitoring initialized successfully!")
                print("All existing unread emails have been marked as processed.")
                print("Run 'python email_monitor.py' to start continuous monitoring.")
            else:
                print("❌ Failed to initialize email monitoring.")
        elif sys.argv[1] == '--reset':
            # Reset processed emails
            if os.path.exists(monitor.processed_emails_file):
                os.remove(monitor.processed_emails_file)
                print("✅ Reset complete. All emails will be processed as new on next run.")
            else:
                print("No processed emails file found.")
        else:
            print("Usage:")
            print("  python email_monitor.py                  # Run continuously")
            print("  python email_monitor.py --once           # Run once")
            print("  python email_monitor.py --test-notification # Test startup notification")
            print("  python email_monitor.py --init           # Initialize (mark existing emails as processed)")
            print("  python email_monitor.py --reset          # Reset (clear processed emails list)")
    else:
        monitor.run_continuous()


if __name__ == "__main__":
    main()
