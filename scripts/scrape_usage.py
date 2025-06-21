#!/usr/bin/env python3
"""
CLI script to scrape water usage data from city utility system.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from my_meter_data import UtilityDataScraper


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Scrape water usage data from city utility billing system"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to .env configuration file"
    )
    parser.add_argument(
        "--username", 
        type=str, 
        help="Username (email) for login"
    )
    parser.add_argument(
        "--password", 
        type=str, 
        help="Password for login"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        help="Output directory for CSV files"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize scraper
    scraper = UtilityDataScraper(config_file=args.config)
    
    # Override output directory if specified
    if args.output_dir:
        scraper.output_dir = args.output_dir
    
    # Get credentials
    username = args.username or os.getenv('UTILITY_USERNAME')
    password = args.password or os.getenv('UTILITY_PASSWORD')
    
    if not username or not password:
        print("Error: Please provide username and password via:")
        print("  1. Command line arguments (--username, --password)")
        print("  2. Environment variables (UTILITY_USERNAME, UTILITY_PASSWORD)")
        print("  3. .env file")
        sys.exit(1)
    
    # Scrape data
    result_file = scraper.scrape_usage_data(username, password)
    
    if result_file:
        print(f"✅ Success! Data saved to: {result_file}")
        sys.exit(0)
    else:
        print("❌ Failed to scrape usage data. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()