#!/usr/bin/env python3
"""
Cron Job: Check Expired Voting Sessions
This script should be run periodically (e.g., every 5 minutes) to check for expired voting sessions
and send result notifications to all participants.

Usage:
    python3 cron_check_expired_voting.py

For production, set up a cron job:
    */5 * * * * cd /path/to/backend && python3 cron_check_expired_voting.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.voting_expiration_service import (
    check_and_process_expired_voting_sessions,
    create_voting_notifications_table
)
from datetime import datetime

def main():
    """Main function to run the expired voting session check"""
    print(f"🕐 Starting expired voting session check at {datetime.now()}")
    print("=" * 60)
    
    try:
        # Ensure the notifications table exists
        if not create_voting_notifications_table():
            print("❌ Failed to create/verify voting notifications table")
            return False
        
        # Check for expired sessions and send notifications
        check_and_process_expired_voting_sessions()
        
        print("✅ Expired voting session check completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in expired voting session check: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 