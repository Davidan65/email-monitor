#!/bin/bash
# Email Monitor Runner Script
# This script activates the virtual environment and runs the email monitor

# Check if virtual environment exists
if [ ! -d "email_monitor_env" ]; then
    echo "Virtual environment not found. Creating it..."
    python3 -m venv email_monitor_env
    source email_monitor_env/bin/activate
    pip install -r requirements.txt
else
    # Activate virtual environment
    source email_monitor_env/bin/activate
fi

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo "ERROR: config.py not found!"
    echo "Please copy config_template.py to config.py and fill in your credentials."
    echo "See README.md for setup instructions."
    exit 1
fi

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "🚀 Email Monitor - Choose an option:"
    echo ""
    echo "1. Start monitoring (continuous)     - ./run_monitor.sh start"
    echo "2. Test once                        - ./run_monitor.sh test"
    echo "3. Initialize (first time setup)    - ./run_monitor.sh init"
    echo "4. Reset processed emails           - ./run_monitor.sh reset"
    echo ""
    read -p "Enter your choice (1-4) or 'start' to begin: " choice

    case $choice in
        1|start) python email_monitor.py ;;
        2|test) python email_monitor.py --once ;;
        3|init) python email_monitor.py --init ;;
        4|reset) python email_monitor.py --reset ;;
        *) echo "Invalid choice. Use: start, test, init, or reset" ;;
    esac
else
    # Handle command line arguments
    case $1 in
        start) python email_monitor.py ;;
        test) python email_monitor.py --once ;;
        init) python email_monitor.py --init ;;
        reset) python email_monitor.py --reset ;;
        *) python email_monitor.py "$@" ;;
    esac
fi
