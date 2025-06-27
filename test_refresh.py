#!/usr/bin/env python3
"""
Simple test script to manually test the refresh functionality.
Run this to see if the login form issue persists.
"""

import os
import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "utility_water"))

from dotenv import load_dotenv
from scraper import UtilityDataScraper
import logging

# Set up logging to see what happens
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def test_refresh():
    """Test the refresh functionality with fresh session approach."""
    print("🔧 Testing Utility Water Refresh (Fresh Session)")
    print("=" * 50)
    
    username = os.getenv('UTILITY_USERNAME')
    password = os.getenv('UTILITY_PASSWORD')
    
    if not username or not password:
        print("❌ Missing credentials in .env file")
        return
    
    print(f"Testing with: {username}")
    
    # Test multiple fresh sessions (simulating multiple daily updates)
    for i in range(2):
        print(f"\n📡 Test {i+1}: Fresh session data fetch...")
        
        # Create fresh scraper instance each time (mimics HA coordinator behavior)
        scraper = UtilityDataScraper()
        
        data = scraper.get_latest_data(username, password)
        
        if data:
            print(f"✅ Test {i+1} successful!")
            print(f"  Records: {data.get('record_count', 0)}")
            print(f"  Total gallons: {data.get('meter_reading', 0)}")
            print(f"  Latest hourly: {data.get('latest_hourly', 0)}")
        else:
            print(f"❌ Test {i+1} failed!")
            print("  Check the logs above for details.")
            
        if i < 1:  # Don't sleep after last test
            print("  Waiting 3 seconds before next test...")
            time.sleep(3)

if __name__ == "__main__":
    test_refresh()