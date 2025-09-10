#!/usr/bin/env python3
"""
Test script to verify Render deployment readiness
"""

import sys
import os

def test_imports():
    """Test all required imports"""
    try:
        import requests
        import html2text
        import dotenv
        from keep_alive import start_keep_alive, stop_keep_alive
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        import config
        
        required_vars = [
            'EMAIL_USER', 'EMAIL_PASSWORD', 'TELEGRAM_BOT_TOKEN', 
            'TELEGRAM_CHAT_ID', 'MONITORED_SENDERS'
        ]
        
        missing = []
        for var in required_vars:
            if not hasattr(config, var) or not getattr(config, var):
                missing.append(var)
        
        if missing:
            print(f"❌ Missing config variables: {missing}")
            return False
        
        print("✅ Configuration loaded successfully")
        return True
        
    except ImportError:
        print("❌ Config file not found or invalid")
        return False

def test_keep_alive():
    """Test keep-alive service"""
    try:
        from keep_alive import KeepAliveService
        service = KeepAliveService(port=8081)
        print("✅ Keep-alive service can be created")
        return True
    except Exception as e:
        print(f"❌ Keep-alive service error: {e}")
        return False

def test_notification():
    """Test startup notification functionality"""
    try:
        import config
        from email_monitor import EmailMonitor
        
        monitor = EmailMonitor()
        print("✅ Notification system can be created")
        
        # Note: We don't actually send the notification in the test
        # to avoid spamming during development
        print("📱 Startup notification feature is ready")
        print("🔄 Single startup notification on service start")
        return True
        
    except Exception as e:
        print(f"❌ Notification system error: {e}")
        return False

def test_render_readiness():
    files_needed = [
        'Procfile', 'runtime.txt', 'requirements.txt', 
        'email_monitor.py', 'keep_alive.py', '.env.template'
    ]
    
    missing_files = []
    for file in files_needed:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files for Render: {missing_files}")
        return False
    
    print("✅ All Render deployment files present")
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Email Monitor for Render deployment...\n")
    
    tests = [
        ("Import Dependencies", test_imports),
        ("Configuration", test_config),
        ("Keep-Alive Service", test_keep_alive),
        ("Notification System", test_notification),
        ("Render Readiness", test_render_readiness)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Ready for Render deployment!")
        print("\n📋 Next steps:")
        print("1. Push code to GitHub (make sure .env is in .gitignore)")
        print("2. Create Render Web Service")
        print("3. Set environment variables in Render dashboard")
        print("4. Deploy!")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())