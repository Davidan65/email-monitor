#!/usr/bin/env python3
"""
Test script to verify Email Monitor setup
Run this script to test your configuration before running the main monitor.
"""

import sys
import imaplib
import requests

def test_config():
    """Test if config file exists and has required fields"""
    print("🔧 Testing configuration...")
    
    try:
        import config
        print("✅ config.py file found")
    except ImportError:
        print("❌ config.py file not found!")
        print("   Please copy config_template.py to config.py and fill in your credentials.")
        return False
    
    required_fields = [
        'IMAP_SERVER', 'EMAIL_USER', 'EMAIL_PASSWORD',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'MONITORED_SENDERS'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not hasattr(config, field) or not getattr(config, field):
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing configuration fields: {missing_fields}")
        return False
    
    print("✅ All required configuration fields present")
    return True

def test_gmail_connection():
    """Test Gmail IMAP connection"""
    print("\n📧 Testing Gmail connection...")
    
    try:
        import config
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
        mail.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
        mail.select('inbox')
        print("✅ Gmail connection successful")
        mail.close()
        mail.logout()
        return True
    except Exception as e:
        print(f"❌ Gmail connection failed: {e}")
        print("   Check your EMAIL_USER and EMAIL_PASSWORD in config.py")
        print("   Make sure you're using a Gmail App Password, not your regular password")
        return False

def test_telegram_bot():
    """Test Telegram bot connection"""
    print("\n📱 Testing Telegram bot...")
    
    try:
        import config
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result']['first_name']
                print(f"✅ Telegram bot connection successful: {bot_name}")
                return True
            else:
                print("❌ Telegram bot token invalid")
                return False
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram bot test failed: {e}")
        print("   Check your TELEGRAM_BOT_TOKEN in config.py")
        return False

def test_telegram_chat():
    """Test sending a message to Telegram chat"""
    print("\n💬 Testing Telegram message sending...")
    
    try:
        import config
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        test_message = "🧪 Email Monitor Test\n\nThis is a test message from your email monitor setup. If you see this, your Telegram integration is working correctly!"
        
        payload = {
            'chat_id': config.TELEGRAM_CHAT_ID,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Test message sent to Telegram successfully")
                print("   Check your Telegram chat for the test message")
                return True
            else:
                print(f"❌ Telegram message failed: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram message test failed: {e}")
        print("   Check your TELEGRAM_CHAT_ID in config.py")
        print("   Make sure you've sent at least one message to your bot first")
        return False

def main():
    """Run all tests"""
    print("🚀 Email Monitor Setup Test")
    print("=" * 40)
    
    tests = [
        ("Configuration", test_config),
        ("Gmail Connection", test_gmail_connection),
        ("Telegram Bot", test_telegram_bot),
        ("Telegram Message", test_telegram_chat),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 40)
    
    if all_passed:
        print("🎉 All tests passed! Your email monitor is ready to use.")
        print("\nNext steps:")
        print("1. Run: python email_monitor.py --once (to test once)")
        print("2. Run: python email_monitor.py (for continuous monitoring)")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before running the email monitor.")
        print("\nFor help, check:")
        print("1. README.md for detailed setup instructions")
        print("2. config_template.py for configuration examples")

if __name__ == "__main__":
    main()
