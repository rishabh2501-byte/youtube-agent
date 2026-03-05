#!/bin/bash
# Setup script for cron job
# This will add a cron job that runs every 10 minutes

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
CRON_SCRIPT="$SCRIPT_DIR/cron_job.py"
LOG_FILE="$SCRIPT_DIR/output/cron.log"

# Create output directory if not exists
mkdir -p "$SCRIPT_DIR/output"

# Cron job entry (every 10 minutes)
CRON_ENTRY="*/10 * * * * cd $SCRIPT_DIR && $PYTHON_PATH $CRON_SCRIPT >> $LOG_FILE 2>&1"

echo "Setting up cron job..."
echo "Script: $CRON_SCRIPT"
echo "Log: $LOG_FILE"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cron_job.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l | grep -v "cron_job.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "Cron job added successfully!"
echo ""
echo "To verify, run: crontab -l"
echo "To remove, run: crontab -l | grep -v 'cron_job.py' | crontab -"
echo ""
echo "Videos will be created every 10 minutes about world locations."
echo "Check logs at: $LOG_FILE"
