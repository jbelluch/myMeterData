#!/usr/bin/env python3
"""
Debug script to test statistics import locally and troubleshoot data issues.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from my_meter_data.scraper import UtilityDataScraper

# Load environment variables
load_dotenv()


def parse_datetime_string(datetime_str):
    """Parse the utility datetime string and return a datetime object."""
    try:
        # Format: "Thu, Jun 19, 2025 4:00 AM - 5:00 AM"
        start_time_str = datetime_str.split(" - ")[0]
        record_time = datetime.strptime(start_time_str, "%a, %b %d, %Y %I:%M %p")
        return record_time
    except ValueError as e:
        print(f"Error parsing datetime '{datetime_str}': {e}")
        return None


def analyze_statistics_data(data):
    """Analyze the data structure and simulate statistics import."""
    if not data or not data.get("all_records"):
        print("❌ No data or all_records found")
        return
    
    print(f"\n📊 Statistics Analysis")
    print(f"=" * 50)
    
    records = data["all_records"]
    print(f"Total records: {len(records)}")
    
    # Analyze the data
    cumulative_sum = 0
    statistics = []
    negative_count = 0
    
    print(f"\n🔍 Detailed Record Analysis:")
    print(f"{'Time':<25} {'Usage (gal)':<12} {'Cumulative':<12} {'Parsed DateTime'}")
    print("-" * 70)
    
    for i, record in enumerate(records):
        usage = record.get("usage_gallons", 0)
        datetime_str = record.get("datetime", "")
        
        # Parse datetime
        parsed_dt = parse_datetime_string(datetime_str)
        
        # Track negative values
        if usage < 0:
            negative_count += 1
        
        # Calculate cumulative
        cumulative_sum += usage
        
        # Store for analysis
        statistics.append({
            "index": i,
            "datetime_str": datetime_str,
            "parsed_dt": parsed_dt,
            "usage": usage,
            "cumulative": cumulative_sum
        })
        
        # Print first 10 and last 10 records
        if i < 10 or i >= len(records) - 10:
            dt_display = parsed_dt.strftime("%Y-%m-%d %H:%M") if parsed_dt else "PARSE ERROR"
            print(f"{datetime_str:<25} {usage:<12.1f} {cumulative_sum:<12.1f} {dt_display}")
        elif i == 10:
            print("... (middle records hidden) ...")
    
    print(f"\n📈 Summary:")
    print(f"Total usage: {cumulative_sum:.1f} gallons")
    print(f"Negative values: {negative_count}")
    print(f"Average hourly: {cumulative_sum / len(records):.2f} gallons")
    
    # Check for data issues
    print(f"\n⚠️  Potential Issues:")
    
    if negative_count > 0:
        print(f"- Found {negative_count} negative usage values")
        negatives = [s for s in statistics if s["usage"] < 0]
        for neg in negatives[:5]:  # Show first 5 negative values
            print(f"  - {neg['datetime_str']}: {neg['usage']} gal")
    
    # Check for datetime parsing errors
    parse_errors = [s for s in statistics if s["parsed_dt"] is None]
    if parse_errors:
        print(f"- Found {len(parse_errors)} datetime parsing errors")
        for error in parse_errors[:3]:  # Show first 3 errors
            print(f"  - {error['datetime_str']}")
    
    # Check for time order
    sorted_stats = [s for s in statistics if s["parsed_dt"] is not None]
    sorted_stats.sort(key=lambda x: x["parsed_dt"])
    
    if len(sorted_stats) != len(statistics):
        print(f"- Time sorting will lose {len(statistics) - len(sorted_stats)} records")
    
    # Check for time gaps
    if len(sorted_stats) > 1:
        time_gaps = []
        for i in range(1, len(sorted_stats)):
            prev_time = sorted_stats[i-1]["parsed_dt"]
            curr_time = sorted_stats[i]["parsed_dt"]
            gap = (curr_time - prev_time).total_seconds() / 3600  # Hours
            if gap != 1.0:  # Should be exactly 1 hour apart
                time_gaps.append((prev_time, curr_time, gap))
        
        if time_gaps:
            print(f"- Found {len(time_gaps)} time gaps (not exactly 1 hour)")
            for gap in time_gaps[:3]:  # Show first 3 gaps
                print(f"  - {gap[0]} to {gap[1]}: {gap[2]:.1f} hours")
    
    return statistics


def main():
    """Debug the statistics import process."""
    print("🔧 Utility Water Meter - Statistics Debug Tool")
    print("=" * 60)
    
    # Get credentials
    username = os.getenv('UTILITY_USERNAME')
    password = os.getenv('UTILITY_PASSWORD')
    
    if not username or not password:
        print("❌ Error: Please set UTILITY_USERNAME and UTILITY_PASSWORD in your .env file")
        return
    
    print(f"🔐 Testing with username: {username}")
    
    # Initialize scraper
    scraper = UtilityDataScraper()
    
    # Get data (this will handle login internally)
    print(f"\n📡 Fetching utility data...")
    data = scraper.get_latest_data(username, password)
    
    if not data:
        print("❌ Failed to fetch data!")
        return
    
    print("✅ Data fetch successful!")
    
    # Debug the raw data structure
    print(f"\n🔍 Raw Data Structure:")
    print(f"Keys: {list(data.keys())}")
    print(f"Latest record: {data.get('latest_record', {})}")
    print(f"Meter reading: {data.get('meter_reading', 0)}")
    print(f"Record count: {data.get('record_count', 0)}")
    
    # Analyze statistics import
    statistics = analyze_statistics_data(data)
    
    # Save debug data
    debug_file = "debug_statistics_output.json"
    with open(debug_file, 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        debug_data = {
            "raw_data": data,
            "parsed_statistics": [
                {
                    **stat,
                    "parsed_dt": stat["parsed_dt"].isoformat() if stat["parsed_dt"] else None
                }
                for stat in statistics
            ] if statistics else []
        }
        json.dump(debug_data, f, indent=2, default=str)
    
    print(f"\n💾 Debug data saved to: {debug_file}")
    print(f"\n🎯 Next Steps:")
    print(f"1. Check the debug output above for issues")
    print(f"2. Review the saved JSON file for detailed data")
    print(f"3. Compare online totals with the cumulative values shown")
    print(f"4. Look for negative values or parsing errors")


if __name__ == "__main__":
    main()